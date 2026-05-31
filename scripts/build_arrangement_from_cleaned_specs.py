#!/usr/bin/env python3
"""Fold cleaned_specs.json (Mistral delta ops) into a final-state arrangement.yml.

cleaned_specs.json is in the OLD manual-bridge format: per (R-index, cell) lists
of add / remove / modify operations applied against scaffolded placeholder clips.
The sc-produce ArrangementSpec wants the *desired final note state* per
(scene, track) cell. This script replays the bridge's reconcile semantics
(remove -> modify -> add, blocks in R-index ascending order, later ops win on a
(pitch, beat) collision) to compute that final state, then emits a schema-valid
arrangement via sc_produce's own dumper.

R-index map (from Dispatch's implementation doc):
  R3  K_piano        scene-keyed  (VERSE 1..OUTRO; no INTRO)
  R5..R11  drums     TRACK-keyed passes that LAYER onto one clip per drum track,
                     applied R-index ascending; R10 supersedes R6 for kick/snare.
  R12 S_808_clean    scene-keyed  (INTRO..OUTRO; no BRIDGE)
  R13 A_server_hum   scene-keyed  (all 7)   [AUDIO track -> audit will flag]
  R14 F_riser        scene-keyed            [AUDIO track -> audit will flag]
  R15 F_impact       scene-keyed            [AUDIO track -> audit will flag]
  R16 F_transition   scene-keyed            [AUDIO track -> audit will flag]

ASSUMPTION (needs Elias sign-off): the drum passes carry no scene label. Per
Dispatch's note the placeholder drum patterns lived in "clip slot 0", so the
folded per-track drum clips are placed in scenes[0] == INTRO. If drums should be
distributed across scenes, this script needs the per-pass -> scene mapping.

Intentionally empty (NOT fabricated): B_harmonics, A_data_air, A_archive_room.
"""

from __future__ import annotations

import json
from pathlib import Path

from sc_produce.models import ArrangementSpec, ClipSpec, NoteSpec
from sc_produce.spec import dump_arrangement, load_structure

HERE = Path(__file__).resolve().parent.parent / "projects" / "pression_archivee"
CLEANED = HERE / "cleaned_specs.json"
STRUCTURE = HERE / "structure.yml"
OUT = HERE / "arrangement.yml"

DRUM_KEYS = ["R5:drums", "R6:drums", "R7:drums", "R8:drums", "R9:drums", "R10:drums", "R11:drums"]
DRUM_TRACKS = ["D_kick", "D_snare", "D_hat", "D_clap", "D_perc", "D_drill_roll"]
DRUM_SCENE = "INTRO"  # scenes[0] / "clip slot 0" -- ASSUMPTION, see module docstring
DEFAULT_DUR = 0.25

_skipped = 0  # malformed modify ops dropped (e.g. the known D_hat 32.5 stub)


def fold(blocks: list[dict]) -> tuple[list[dict], int]:
    """Replay remove->modify->add across blocks; return (final notes, missing-dur count).

    Malformed ``modify`` ops (lacking ``from``/``to``) are skipped, mirroring the
    bridge transform's filter -- e.g. the known unrecoverable D_hat stub at 32.5.
    """
    state: dict[tuple, dict] = {}
    missing = 0
    for blk in blocks:
        for rm in blk.get("remove", []):
            state.pop((rm["pitch"], rm["beat"]), None)
        for mo in blk.get("modify", []):
            if "from" not in mo or "to" not in mo:
                global _skipped
                _skipped += 1
                continue
            frm, to = mo["from"], mo["to"]
            state.pop((frm["pitch"], frm["beat"]), None)
            state[(to["pitch"], to["beat"])] = to
        for ad in blk.get("add", []):
            state[(ad["pitch"], ad["beat"])] = ad
    notes = []
    for n in state.values():
        if "duration" not in n:
            missing += 1
        notes.append(n)
    # stable order: by beat then pitch-string
    notes.sort(key=lambda n: (n["beat"], str(n["pitch"])))
    return notes, missing


def to_clip(notes: list[dict]) -> ClipSpec:
    return ClipSpec(
        notes=[
            NoteSpec(
                pitch=n["pitch"],
                start=n["beat"],
                duration=n.get("duration", DEFAULT_DUR),
                velocity=n.get("velocity", 100.0),
            )
            for n in notes
        ]
    )


def main() -> None:
    cs = json.loads(CLEANED.read_text())
    structure = load_structure(STRUCTURE)
    audio = set(structure.audio_track_names())

    scenes: dict[str, dict[str, ClipSpec]] = {}
    report: list[str] = []
    total_missing = 0

    def place(scene: str, track: str, notes: list[dict]) -> None:
        if not notes:
            return
        scenes.setdefault(scene, {})[track] = to_clip(notes)
        flag = "  <-- AUDIO (audit will flag)" if track in audio else ""
        report.append(f"  {scene:12} / {track:14} : {len(notes):3} notes{flag}")

    # --- scene-keyed keys: K_piano, S_808_clean, A_server_hum, F_* -----------
    for key in [
        "R3:K_piano",
        "R12:S_808_clean",
        "R13:A_server_hum",
        "R14:F_riser",
        "R15:F_impact",
        "R16:F_transition",
    ]:
        track = key.split(":", 1)[1]
        for blk in cs[key]:
            notes, miss = fold([blk])
            total_missing += miss
            place(blk["header"], track, notes)

    # --- drums: fold all passes per track, place in DRUM_SCENE ----------------
    for track in DRUM_TRACKS:
        blocks = [blk for key in DRUM_KEYS for blk in cs.get(key, []) if blk.get("header") == track]
        notes, miss = fold(blocks)
        total_missing += miss
        place(DRUM_SCENE, track, notes)

    arrangement = ArrangementSpec(title="Pression Archivée", scenes=scenes)

    header = (
        "# Pression Archivée — ARRANGEMENT spec (final note state)\n"
        "#\n"
        "# GENERATED by scripts/build_arrangement_from_cleaned_specs.py from\n"
        "# cleaned_specs.json (Mistral delta ops). Do not hand-edit; re-run the\n"
        "# script. See that file's docstring for the R-index map and assumptions.\n"
        "#\n"
        "# ASSUMPTION (needs sign-off): drum clips placed in INTRO (clip slot 0).\n"
        "# UNRESOLVED: cells on audio tracks (A_server_hum, F_riser, F_impact,\n"
        "#   F_transition, D_clap, D_perc, D_drill_roll) are authored as MIDI here\n"
        "#   so `sc-produce audit` surfaces the audio-vs-MIDI verdict. Elias decides\n"
        "#   per-track: change type to midi, or re-encode as audio cues.\n"
        "# Intentionally empty (not fabricated): B_harmonics, A_data_air, A_archive_room.\n"
    )
    OUT.write_text(header + dump_arrangement(arrangement), encoding="utf-8")

    print("Wrote", OUT)
    print("Cells authored:", sum(len(t) for t in scenes.values()))
    print(f"Notes missing explicit duration (defaulted to {DEFAULT_DUR:.2f}): {total_missing}")
    print(f"Malformed modify ops skipped (bridge-filter parity): {_skipped}")
    print("\nPer-cell fold:")
    print("\n".join(report))


if __name__ == "__main__":
    main()
