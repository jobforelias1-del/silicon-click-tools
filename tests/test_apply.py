"""Tests for :mod:`sc_produce.apply`.

These exercise ``apply_project`` and the ``apply`` CLI surface against the
in-memory :class:`_fakes.FakeLive`, which faithfully models AbletonOSC's clip and
note surface (idempotent clip creation, audio-track refusal, narrow-window note
removal). The behaviours under test mirror the two properties the module exists to
guarantee:

* **Correct track type** -- MIDI is never written to an audio (or return) track,
  whether rejected up front from the structure or surfaced from inside the bridge.
* **Convergence to the desired state** -- a re-applied cell is reconciled (remove
  -> modify -> add) until the clip matches the spec exactly, then read back to
  confirm.

A single bad cell (unknown scene/track, wrong type, invalid pitch) is recorded as
a finding and never aborts the rest of the apply.
"""

from __future__ import annotations

import argparse

import pytest
from _fakes import FakeLive, make_session, populated_song
from ableton_bridge import ClipNotFoundError, Note, OSCTimeoutError

from sc_produce import apply as apply_mod
from sc_produce import common
from sc_produce.apply import apply_project
from sc_produce.launcher import generate_launcher
from sc_produce.models import (
    ArrangementSpec,
    ClipSpec,
    CueSpec,
    NoteSpec,
    StructureSpec,
    TrackSpec,
    TrackType,
)
from sc_produce.report import Severity
from sc_produce.spec import dump_arrangement, dump_structure

# Track indices within the populated skeleton song (see _fakes.populated_song).
D_KICK = 0
D_CLAP = 1
K_PIANO = 2
A_SERVER_HUM = 3


def _messages(report) -> str:
    """Join all finding messages into a single searchable string."""
    return "\n".join(f.message for f in report.findings)


def _errors(report) -> list:
    """Return the error-severity findings of ``report``."""
    return [f for f in report.findings if f.severity is Severity.ERROR]


def _sent_addresses(live: FakeLive) -> list[str]:
    """Return every OSC address ``live`` recorded as written."""
    return [address for address, _ in live.sent]


# --------------------------------------------------------------------------- #
# Happy path: the arrangement fixture is written into the song
# --------------------------------------------------------------------------- #
def test_apply_writes_notes_into_clip_slots(
    populated_live: FakeLive,
    session,
    structure: StructureSpec,
    arrangement: ArrangementSpec,
) -> None:
    """Applying the fixture writes each cell's notes into the right clip slot.

    A scene's clip slot index is its position in the structure (``Intro`` -> 0,
    ``Verse`` -> 1), so the two ``Intro`` cells land in slot 0 and the ``Verse``
    cell in slot 1.
    """
    report = apply_project(structure, arrangement, session)

    assert report.passed
    # Intro/D_kick (slot 0) has both kick notes; assert via the song and the bridge.
    assert len(populated_live.tracks[D_KICK].clip_slots[0].notes) == 2
    assert len(session.bridge.get_notes("D_kick", 0)) == 2
    # Intro/K_piano (slot 0) has its single note.
    assert len(populated_live.tracks[K_PIANO].clip_slots[0].notes) == 1
    # Verse/D_kick (slot 1) has its single note.
    assert len(populated_live.tracks[D_KICK].clip_slots[1].notes) == 1
    # Every cell reports a clean apply with no modifications or removals.
    assert all(f.severity is Severity.OK for f in report.findings)
    assert "cell applied (+2 ~0 -0)" in _messages(report)


def test_apply_is_idempotent(
    session,
    structure: StructureSpec,
    arrangement: ArrangementSpec,
) -> None:
    """Re-applying an already-applied arrangement is a no-op (+0 ~0 -0) and passes."""
    apply_project(structure, arrangement, session)

    second = apply_project(structure, arrangement, session)

    assert second.passed
    # On the second pass nothing changes: every cell is +0 ~0 -0.
    for finding in second.findings:
        assert finding.severity is Severity.OK
        assert "(+0 ~0 -0)" in finding.message


# --------------------------------------------------------------------------- #
# Reconciliation: remove + modify + add converge to the desired state
# --------------------------------------------------------------------------- #
def test_reconcile_removes_modifies_and_adds(
    populated_live: FakeLive,
    session,
) -> None:
    """A pre-populated clip is reconciled to the desired set exactly.

    The slot starts with three notes: one that is absent from the spec (removed),
    one that shares a ``(pitch, start)`` key but a different velocity (modified),
    and the spec additionally introduces a brand-new note (added). After apply the
    final note set must equal the desired set by key *and* velocity, and the OK
    message must report ``+1 ~1 -1``.
    """
    structure = StructureSpec(
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )
    # Pre-create the clip and seed three existing notes (slot 0 == "Intro").
    session.bridge.create_clip("D_kick", 0, 4.0)
    session.bridge.add_notes(
        "D_kick",
        0,
        [
            Note(pitch=60, start=0.0, duration=0.5, velocity=100),  # to be modified
            Note(pitch=62, start=1.0, duration=0.5, velocity=90),  # to be removed
        ],
    )

    # Desired: keep+modify (60,0.0)->vel120, drop (62,1.0), add (64,2.0).
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    length=4.0,
                    notes=[
                        NoteSpec(pitch=60, start=0.0, duration=0.5, velocity=120),
                        NoteSpec(pitch=64, start=2.0, duration=0.5, velocity=80),
                    ],
                )
            }
        }
    )

    report = apply_project(structure, arrangement, session)

    assert report.passed
    final = session.bridge.get_notes("D_kick", 0)
    # Keys converge exactly to the desired set.
    assert {n.key() for n in final} == {(60, 0.0), (64, 2.0)}
    # And the velocities match the desired set (the modify took effect).
    vel_by_key = {n.key(): n.velocity for n in final}
    assert vel_by_key == {(60, 0.0): 120.0, (64, 2.0): 80.0}
    # The removed note is gone from the underlying song.
    song_keys = {(n[0], n[1]) for n in populated_live.tracks[D_KICK].clip_slots[0].notes}
    assert (62, 1.0) not in song_keys
    # The OK message reports the correct +added ~modified -removed counts.
    assert "cell applied (+1 ~1 -1)" in _messages(report)


def test_reconcile_remove_modify_add_ordering(
    populated_live: FakeLive,
    session,
) -> None:
    """Writes are issued in the required order: remove, then modify, then add."""
    structure = StructureSpec(
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )
    session.bridge.create_clip("D_kick", 0, 4.0)
    session.bridge.add_notes(
        "D_kick",
        0,
        [
            Note(pitch=60, start=0.0, duration=0.5, velocity=100),  # modified
            Note(pitch=62, start=1.0, duration=0.5, velocity=90),  # removed
        ],
    )
    populated_live.sent.clear()  # only look at writes the reconcile issues

    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[
                        NoteSpec(pitch=60, start=0.0, duration=0.5, velocity=120),
                        NoteSpec(pitch=64, start=2.0, duration=0.5, velocity=80),
                    ]
                )
            }
        }
    )

    apply_project(structure, arrangement, session)

    addresses = _sent_addresses(populated_live)
    remove_at = addresses.index("/live/clip/remove/notes")
    # The modify is a remove+add bundle; the *standalone* add for new notes is last.
    last_add = max(i for i, a in enumerate(addresses) if a == "/live/clip/add/notes")
    # The lone remove (the -1) precedes the final add (the +1).
    assert remove_at < last_add


def test_post_apply_mismatch_is_a_warning(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the read-back set differs from the desired set, a WARNING is recorded.

    The reconcile completes its writes but the confirmation read returns a
    different note set (simulating a write that silently failed in Live), so the
    cell must be flagged with a non-error ``post-apply mismatch`` warning.
    """
    structure = StructureSpec(
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            }
        }
    )
    real_get_notes = session.bridge.get_notes
    calls = {"n": 0}

    def _flaky_get_notes(track, clip_index):
        # First call returns the true (empty) existing set; the read-back lies.
        calls["n"] += 1
        if calls["n"] == 1:
            return real_get_notes(track, clip_index)
        return []  # read-back reports nothing was written

    monkeypatch.setattr(session.bridge, "get_notes", _flaky_get_notes)

    report = apply_project(structure, arrangement, session)

    # A mismatch is non-fatal: it is a warning, not an error, so the report passes.
    assert report.passed
    warnings = [f for f in report.findings if f.severity is Severity.WARNING]
    assert warnings and "post-apply mismatch" in warnings[0].message
    assert "expected 1 got 0" in warnings[0].message


def test_generic_bridge_error_is_reported_per_cell(
    session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-audio bridge failure becomes a ``bridge error`` finding, not a crash."""
    structure = StructureSpec(
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            }
        }
    )

    def _boom(*args, **kwargs):
        raise ClipNotFoundError("simulated clip vanished")

    monkeypatch.setattr(session.bridge, "add_notes", _boom)

    report = apply_project(structure, arrangement, session)

    assert report.passed is False
    bridge_errors = [f for f in _errors(report) if "bridge error" in f.message]
    assert bridge_errors and bridge_errors[0].track == "D_kick"


# --------------------------------------------------------------------------- #
# Audio / return / unknown cells: clean per-cell errors, rest still applies
# --------------------------------------------------------------------------- #
def test_audio_track_cell_is_error_but_rest_applies(
    populated_live: FakeLive,
    session,
    structure: StructureSpec,
) -> None:
    """A cell targeting an audio track errors, while a valid sibling cell applies."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "A_server_hum": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                ),
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                ),
            }
        }
    )

    report = apply_project(structure, arrangement, session)

    assert report.passed is False
    audio_errors = [
        f for f in _errors(report) if f.track == "A_server_hum" and "cannot hold MIDI" in f.message
    ]
    assert audio_errors, "expected an 'audio track cannot hold MIDI' error"
    # No clip was created on the audio track.
    assert populated_live.tracks[A_SERVER_HUM].clip_slots == {}
    # The valid D_kick cell still applied.
    assert len(session.bridge.get_notes("D_kick", 0)) == 1
    assert any(f.severity is Severity.OK and f.track == "D_kick" for f in report.findings)


def test_audio_track_cues_are_recorded_not_written(
    populated_live: FakeLive,
    session,
    structure: StructureSpec,
) -> None:
    """Audio cues on an audio track are recorded as info and write nothing.

    The bridge has no OSC sample-load API, so cues are noted for the later
    by-hand materialisation step rather than applied -- and must NOT be treated
    as the audio-holds-MIDI error.
    """
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "A_server_hum": ClipSpec(cues=[CueSpec(sample="hum_01", beat=0.0, length=8.0)]),
            }
        }
    )

    report = apply_project(structure, arrangement, session)

    # Not an error -- cues are legitimate on an audio track.
    assert not _errors(report)
    assert any(
        f.severity is Severity.INFO and f.track == "A_server_hum" and "audio cue" in f.message
        for f in report.findings
    )
    # Nothing was written to the audio track.
    assert populated_live.tracks[A_SERVER_HUM].clip_slots == {}


def test_audio_refusal_surfaced_from_bridge_is_reported(session) -> None:
    """If the structure mislabels an audio track as MIDI, the bridge refusal is caught.

    The structure declares ``A_server_hum`` as MIDI (a spec mistake), so the cell
    passes the up-front type guard but the bridge -- the real authority -- raises
    :class:`AudioTrackCannotHoldMidiError`, which must become a clean per-cell error
    rather than aborting the apply.
    """
    structure = StructureSpec(
        tracks=[TrackSpec(name="A_server_hum", type=TrackType.MIDI)],  # wrong on purpose
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "A_server_hum": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            }
        }
    )

    report = apply_project(structure, arrangement, session)

    assert report.passed is False
    caught = [f for f in _errors(report) if "caught from bridge" in f.message]
    assert caught and caught[0].track == "A_server_hum"


def test_return_track_cell_is_error(session) -> None:
    """A cell targeting a RETURN-typed track is rejected up front."""
    structure = StructureSpec(
        tracks=[TrackSpec(name="R_REVERB", type=TrackType.RETURN)],
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "R_REVERB": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            }
        }
    )

    report = apply_project(structure, arrangement, session)

    assert report.passed is False
    assert any(
        f.track == "R_REVERB" and "return track cannot hold clips" in f.message
        for f in _errors(report)
    )


def test_unknown_scene_and_unknown_track_are_errors(
    session,
    structure: StructureSpec,
) -> None:
    """Cells naming a scene or track absent from the structure are errors."""
    arrangement = ArrangementSpec(
        scenes={
            "Outro": {  # not a scene in the structure
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            },
            "Intro": {
                "D_ghost": ClipSpec(  # not a track in the structure
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            },
        }
    )

    report = apply_project(structure, arrangement, session)

    assert report.passed is False
    messages = _messages(report)
    assert "unknown scene Outro" in messages
    assert "unknown track D_ghost" in messages


# --------------------------------------------------------------------------- #
# Dry run: plan only, no writes
# --------------------------------------------------------------------------- #
def test_dry_run_performs_no_writes(
    populated_live: FakeLive,
    session,
    structure: StructureSpec,
    arrangement: ArrangementSpec,
) -> None:
    """``dry_run=True`` records an info plan and sends nothing to Live."""
    report = apply_project(structure, arrangement, session, dry_run=True)

    # No writes of any kind, and specifically no note adds.
    assert populated_live.sent == []
    assert "/live/clip/add/notes" not in _sent_addresses(populated_live)
    # No clips were created.
    assert all(t.clip_slots == {} for t in populated_live.tracks)
    # The plan is recorded as info findings naming each cell and its slot.
    assert report.count(Severity.INFO) == 3
    messages = _messages(report)
    assert "would write 2 note(s) to D_kick/Intro (clip 0)" in messages
    assert "would write 1 note(s) to K_piano/Intro (clip 0)" in messages
    assert "would write 1 note(s) to D_kick/Verse (clip 1)" in messages


# --------------------------------------------------------------------------- #
# Robustness: an invalid pitch is reported; other notes still applied
# --------------------------------------------------------------------------- #
def test_invalid_pitch_is_reported_other_notes_applied(session) -> None:
    """A note with an out-of-range pitch errors (by index); valid notes still apply."""
    structure = StructureSpec(
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[
                        NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110),
                        NoteSpec(pitch=999, start=1.0, duration=0.25, velocity=110),  # bad
                        NoteSpec(pitch="C1", start=2.0, duration=0.25, velocity=110),
                    ]
                )
            }
        }
    )

    report = apply_project(structure, arrangement, session)

    pitch_errors = [f for f in _errors(report) if "invalid pitch" in f.message]
    assert pitch_errors, "expected an invalid-pitch error"
    assert pitch_errors[0].index == 1  # keyed to the offending note's index
    assert pitch_errors[0].track == "D_kick"
    # The two valid notes were still written (the bad one skipped).
    assert len(session.bridge.get_notes("D_kick", 0)) == 2


def test_dry_run_reports_invalid_pitch_without_writing(
    populated_live: FakeLive,
    session,
) -> None:
    """Even in dry-run the bad pitch is flagged, and still nothing is written."""
    structure = StructureSpec(
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[
                        NoteSpec(pitch=999, start=0.0, duration=0.25, velocity=110),
                        NoteSpec(pitch="C1", start=1.0, duration=0.25, velocity=110),
                    ]
                )
            }
        }
    )

    report = apply_project(structure, arrangement, session, dry_run=True)

    assert any("invalid pitch" in f.message for f in _errors(report))
    # Dry-run still writes nothing, and the info plan counts only the valid note.
    assert populated_live.sent == []
    assert "would write 1 note(s) to D_kick/Intro (clip 0)" in _messages(report)


# --------------------------------------------------------------------------- #
# Launcher generation
# --------------------------------------------------------------------------- #
def test_generate_launcher_compiles_and_embeds_data(
    structure: StructureSpec,
    arrangement: ArrangementSpec,
) -> None:
    """A generated apply-only launcher compiles and embeds apply_project + data."""
    src = generate_launcher(structure, arrangement, do_scaffold=False)

    # It is valid Python.
    compile(src, "launcher.py", "exec")
    # It calls the apply entry point and embeds the structure/arrangement data.
    assert "apply_project" in src
    assert "from sc_produce.apply import apply_project" in src
    assert "D_kick" in src  # a track name from the embedded structure
    assert "A2" in src  # a note pitch from the embedded arrangement
    # do_scaffold=False means it must not also scaffold.
    assert "scaffold_project" not in src


# --------------------------------------------------------------------------- #
# CLI: run() launcher path, apply path, and the SpecError path
# --------------------------------------------------------------------------- #
def _run_args(arrangement_path, structure_path, **overrides) -> argparse.Namespace:
    """Build a parsed-args namespace for ``apply.run`` via its own parser."""
    parser = argparse.ArgumentParser()
    apply_mod.configure_parser(parser)
    argv = [str(arrangement_path), "--structure", str(structure_path)]
    for flag, value in overrides.items():
        if value is True:
            argv.append(f"--{flag.replace('_', '-')}")
        elif value is not None and value is not False:
            argv.extend([f"--{flag.replace('_', '-')}", str(value)])
    return parser.parse_args(argv)


def test_run_launcher_path_writes_compilable_file_without_connecting(
    tmp_path,
    structure: StructureSpec,
    arrangement: ArrangementSpec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--launcher`` writes a compilable script, returns 0 and never connects."""
    structure_file = tmp_path / "structure.yaml"
    arrangement_file = tmp_path / "arrangement.yaml"
    launcher_file = tmp_path / "go.py"
    structure_file.write_text(dump_structure(structure), encoding="utf-8")
    arrangement_file.write_text(dump_arrangement(arrangement), encoding="utf-8")

    # connect must never be reached on the launcher path.
    def _boom(args: argparse.Namespace):
        raise AssertionError("connect should not be called when writing a launcher")

    monkeypatch.setattr(common, "connect", _boom)

    args = _run_args(arrangement_file, structure_file, launcher=launcher_file)
    code = apply_mod.run(args)

    assert code == 0
    assert launcher_file.exists()
    compile(launcher_file.read_text(encoding="utf-8"), str(launcher_file), "exec")


def test_run_apply_path_returns_zero(
    tmp_path,
    structure: StructureSpec,
    arrangement: ArrangementSpec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``run`` loads real YAML, connects (monkeypatched) and applies OK."""
    structure_file = tmp_path / "structure.yaml"
    arrangement_file = tmp_path / "arrangement.yaml"
    structure_file.write_text(dump_structure(structure), encoding="utf-8")
    arrangement_file.write_text(dump_arrangement(arrangement), encoding="utf-8")

    live = populated_song()
    monkeypatch.setattr(common, "connect", lambda args: make_session(live))

    args = _run_args(arrangement_file, structure_file)
    code = apply_mod.run(args)

    assert code == 0
    # The arrangement was actually written and the session closed (context manager).
    assert len(live.tracks[D_KICK].clip_slots[0].notes) == 2
    assert live.closed


def test_run_apply_path_returns_one_on_errors(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the apply records errors, ``run`` returns 1."""
    # A structure with only an audio track, and an arrangement that writes MIDI to it.
    structure = StructureSpec(
        tracks=[TrackSpec(name="A_server_hum", type=TrackType.AUDIO)],
        scenes=["Intro"],
    )
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "A_server_hum": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            }
        }
    )
    structure_file = tmp_path / "structure.yaml"
    arrangement_file = tmp_path / "arrangement.yaml"
    structure_file.write_text(dump_structure(structure), encoding="utf-8")
    arrangement_file.write_text(dump_arrangement(arrangement), encoding="utf-8")

    monkeypatch.setattr(common, "connect", lambda args: make_session(populated_song()))

    args = _run_args(arrangement_file, structure_file)
    assert apply_mod.run(args) == 1


def test_run_surfaces_spec_error(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A spec that fails to load makes ``run`` fail fast with exit code 1."""
    good_structure = tmp_path / "structure.yaml"
    good_structure.write_text(
        dump_structure(StructureSpec(tracks=[], scenes=["Intro"])), encoding="utf-8"
    )
    bad_arrangement = tmp_path / "bad.yaml"
    bad_arrangement.write_text("scenes: [not, a, mapping]\n", encoding="utf-8")

    # connect must never be reached on a load failure.
    def _boom(args: argparse.Namespace):
        raise AssertionError("connect should not be called on a load failure")

    monkeypatch.setattr(common, "connect", _boom)

    args = _run_args(bad_arrangement, good_structure)
    assert apply_mod.run(args) == 1


def test_run_returns_one_when_live_unreachable(
    tmp_path,
    structure: StructureSpec,
    arrangement: ArrangementSpec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A connect that times out is surfaced as exit code 1, not a traceback."""
    structure_file = tmp_path / "structure.yaml"
    arrangement_file = tmp_path / "arrangement.yaml"
    structure_file.write_text(dump_structure(structure), encoding="utf-8")
    arrangement_file.write_text(dump_arrangement(arrangement), encoding="utf-8")

    def _timeout(args: argparse.Namespace):
        raise OSCTimeoutError("Live is not reachable")

    monkeypatch.setattr(common, "connect", _timeout)

    args = _run_args(arrangement_file, structure_file)
    assert apply_mod.run(args) == 1


# --------------------------------------------------------------------------- #
# CLI metadata smoke check
# --------------------------------------------------------------------------- #
def test_cli_metadata() -> None:
    """The module exposes the expected CLI name/help and parser arguments."""
    assert apply_mod.NAME == "apply"
    assert apply_mod.HELP == "Apply an audited arrangement into the open Live set, cell by cell"

    parser = argparse.ArgumentParser()
    apply_mod.configure_parser(parser)
    ns = parser.parse_args(["arr.yaml", "--structure", "struct.yaml"])
    assert ns.arrangement == "arr.yaml"
    assert ns.structure == "struct.yaml"
    assert ns.dry_run is False
    assert ns.launcher is None

    # --structure is required.
    with pytest.raises(SystemExit):
        parser.parse_args(["arr.yaml"])
