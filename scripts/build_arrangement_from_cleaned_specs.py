#!/usr/bin/env python3
"""Fold cleaned_specs.json (Mistral delta ops) into a final-state arrangement.yml,
applying Mistral's 2026-05-31 disambiguation answers.

cleaned_specs.json is in the OLD manual-bridge format: per (R-index, cell) lists
of add / remove / modify operations against scaffolded placeholder clips. The
sc-produce ArrangementSpec wants the *desired final state* per (scene, track)
cell. This script replays the bridge's reconcile semantics (remove -> modify ->
add, blocks in R-index ascending order, later ops win on a (pitch, beat)
collision -- Mistral Q15=yes) to compute that state, then emits a schema-valid
arrangement via sc_produce's own dumper.

Mistral's disambiguation answers (canon) drive three things:

* **Q1=a:** A_server_hum is real MIDI -> authored as notes (structure re-typed to
  midi). Its ops stand.
* **Q2/Q3/Q4/Q5/Q6/Q7=b:** F_riser, F_impact, F_transition, D_clap, D_perc,
  D_drill_roll are AUDIO CUES, not MIDI. Their MIDI note-ops are translated to
  CueSpec entries: each surviving note's (beat) becomes a cue at that beat, using
  the Q25 sample hint and the note's duration as the cue length. Pitch/velocity
  are dropped (a sample trigger has neither).
* **Q8..Q14:** each drum pass maps to a section (or a span). Drum tracks that are
  still MIDI (D_kick, D_snare, D_hat) are placed per their pass's section
  assignment instead of all-into-INTRO.

Q26/Q27/Q28=silent: B_harmonics, A_data_air, A_archive_room get no cells.

One op is dropped: the known-unrecoverable D_hat modify stub at beat 32.5 (no
from/to), matching the bridge filter.
"""

from __future__ import annotations

import json
from pathlib import Path

from sc_produce.models import ArrangementSpec, ClipSpec, CueSpec, NoteSpec
from sc_produce.spec import dump_arrangement, load_structure

HERE = Path(__file__).resolve().parent.parent / "projects" / "pression_archivee"
CLEANED = HERE / "cleaned_specs.json"
STRUCTURE = HERE / "structure.yml"
OUT = HERE / "arrangement.yml"

DEFAULT_DUR = 0.25

# Mistral Q25 sample hints for the (b) audio-cue tracks.
SAMPLE_HINTS = {
    "F_riser": "fx_riser_01",
    "F_impact": "fx_impact_01",
    "F_transition": "fx_transition_01",
    "D_clap": "clap_sample_01",
    "D_perc": "perc_sample_01",
    "D_drill_roll": "drill_roll_sample_01",
}

# Mistral Q8..Q14: each drum pass -> the section(s) it targets. A span "A..B"
# places the pass into every section in that inclusive range.
DRUM_PASS_SECTION = {
    "R5:drums": ["INTRO"],
    "R6:drums": ["INTRO"],
    "R7:drums": ["INTRO"],
    "R8:drums": ["VERSE 1"],
    "R9:drums": ["CHORUS"],
    "R10:drums": ["PRE-CHORUS", "CHORUS"],
    "R11:drums": ["INTRO", "VERSE 1"],
}

DRUM_TRACKS = ["D_kick", "D_snare", "D_hat", "D_clap", "D_perc", "D_drill_roll"]

_skipped = 0  # malformed modify ops dropped (e.g. the known D_hat 32.5 stub)


def fold(blocks: list[dict]) -> list[dict]:
    """Replay remove->modify->add across blocks; return final notes (beat-sorted).

    Malformed ``modify`` ops (lacking ``from``/``to``) are skipped, mirroring the
    bridge transform's filter -- e.g. the known unrecoverable D_hat stub at 32.5.
    """
    global _skipped
    state: dict[tuple, dict] = {}
    for blk in blocks:
        for rm in blk.get("remove", []):
            state.pop((rm["pitch"], rm["beat"]), None)
        for mo in blk.get("modify", []):
            if "from" not in mo or "to" not in mo:
                _skipped += 1
                continue
            frm, to = mo["from"], mo["to"]
            state.pop((frm["pitch"], frm["beat"]), None)
            state[(to["pitch"], to["beat"])] = to
        for ad in blk.get("add", []):
            state[(ad["pitch"], ad["beat"])] = ad
    notes = list(state.values())
    notes.sort(key=lambda n: (n["beat"], str(n["pitch"])))
    return notes


def notes_to_clip(notes: list[dict]) -> ClipSpec:
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


def notes_to_cue_clip(notes: list[dict], sample: str) -> ClipSpec:
    """Translate surviving MIDI ops into audio cues (Q2-Q7=b).

    A sample trigger has no pitch/velocity; each note's beat becomes a cue start
    and its duration the cue length. Collapses duplicate beats (a chord of MIDI
    notes is one sample hit).
    """
    by_beat: dict[float, dict] = {}
    for n in notes:
        by_beat.setdefault(n["beat"], n)  # first wins; beats already sorted
    return ClipSpec(
        cues=[
            CueSpec(sample=sample, beat=beat, length=by_beat[beat].get("duration", DEFAULT_DUR))
            for beat in sorted(by_beat)
        ]
    )


def main() -> None:
    cs = json.loads(CLEANED.read_text())
    structure = load_structure(STRUCTURE)
    audio = set(structure.audio_track_names())

    scenes: dict[str, dict[str, ClipSpec]] = {}
    report: list[str] = []

    def place(scene: str, track: str, clip: ClipSpec) -> None:
        if not clip.notes and not clip.cues:
            return
        scenes.setdefault(scene, {})[track] = clip
        kind = f"{len(clip.notes)} notes" if clip.notes else f"{len(clip.cues)} cues"
        tag = " [audio-cue]" if track in audio else ""
        report.append(f"  {scene:12} / {track:14} : {kind}{tag}")

    # --- scene-keyed MIDI: K_piano, S_808_clean, A_server_hum (Q1=a) ----------
    for key in ["R3:K_piano", "R12:S_808_clean", "R13:A_server_hum"]:
        track = key.split(":", 1)[1]
        for blk in cs[key]:
            place(blk["header"], track, notes_to_clip(fold([blk])))

    # --- scene-keyed AUDIO CUES: F_riser, F_impact, F_transition (Q2-Q4=b) ----
    for key in ["R14:F_riser", "R15:F_impact", "R16:F_transition"]:
        track = key.split(":", 1)[1]
        for blk in cs[key]:
            place(blk["header"], track, notes_to_cue_clip(fold([blk]), SAMPLE_HINTS[track]))

    # --- drums: place each pass into its Q8..Q14 section(s) -------------------
    # MIDI drums (D_kick/D_snare/D_hat) -> notes; (b) drums -> cues. A pass that
    # SPANS sections (Q13/Q14) is STRETCHED across the absolute beat-range of the
    # combined sections and split at section boundaries (Elias 2026-06-01), not
    # copied into each. Per-section note fragments accumulate, then fold once.
    section_len = {s.name: (s.length or 0.0) for s in structure.scenes}
    # track -> section -> {(pitch, beat): note}. A dict keyed by (pitch, beat)
    # enforces Q15 (higher R-index wins): DRUM_PASS_SECTION is iterated R5..R11,
    # so a later pass's note overwrites an earlier one at the same (pitch, beat).
    drum_notes: dict[str, dict[str, dict[tuple, dict]]] = {t: {} for t in DRUM_TRACKS}

    for key, span in DRUM_PASS_SECTION.items():
        for track in DRUM_TRACKS:
            blocks = [b for b in cs.get(key, []) if b.get("header") == track]
            if not blocks:
                continue
            notes = fold(blocks)  # beats relative to the span start
            # boundaries of each section within the span (cumulative)
            starts = []
            acc = 0.0
            for sec in span:
                starts.append((sec, acc, acc + section_len.get(sec, 0.0)))
                acc += section_len.get(sec, 0.0)
            for n in notes:
                b = n["beat"]
                sec, lo = span[0], 0.0
                for s_name, s_lo, s_hi in starts:
                    if s_lo <= b < s_hi or (s_name == starts[-1][0] and b >= s_lo):
                        sec, lo = s_name, s_lo
                        break
                rebased = dict(n, beat=b - lo)
                drum_notes[track].setdefault(sec, {})[(rebased["pitch"], rebased["beat"])] = rebased

    for track in DRUM_TRACKS:
        for section, by_key in drum_notes[track].items():
            notes = sorted(by_key.values(), key=lambda n: (n["beat"], str(n["pitch"])))
            if track in audio:
                place(section, track, notes_to_cue_clip(notes, SAMPLE_HINTS[track]))
            else:
                place(section, track, notes_to_clip(notes))

    arrangement = ArrangementSpec(title="Pression Archivée", scenes=scenes)

    header = (
        "# Pression Archivée — ARRANGEMENT spec (final state)\n"
        "#\n"
        "# GENERATED by scripts/build_arrangement_from_cleaned_specs.py from\n"
        "# cleaned_specs.json, applying Mistral's 2026-05-31 disambiguation answers.\n"
        "# Do not hand-edit; re-run the script.\n"
        "#\n"
        "# Q1=a   A_server_hum authored as MIDI (structure re-typed audio->midi).\n"
        "# Q2-Q7=b F_riser/F_impact/F_transition/D_clap/D_perc/D_drill_roll authored\n"
        "#         as audio CUES (sample hints from Q25); these stay type: audio.\n"
        "# Q8-Q14 drum passes placed per section (no longer all-into-INTRO).\n"
        "# Q15=yes higher R-index wins on collision.\n"
        "# Q26-28 B_harmonics/A_data_air/A_archive_room silent (no cells).\n"
    )
    OUT.write_text(header + dump_arrangement(arrangement), encoding="utf-8")

    print("Wrote", OUT)
    print("Cells authored:", sum(len(t) for t in scenes.values()))
    print(f"Malformed modify ops skipped (bridge-filter parity): {_skipped}")
    print("\nPer-cell:")
    print("\n".join(report))


if __name__ == "__main__":
    main()
