"""Tests for :mod:`sc_produce.audit`.

These exercise the pure :func:`~sc_produce.audit.audit_project` function across
every class of finding (value, type/structure and completeness) and then drive
the ``run`` CLI handler end to end on temporary spec files. The auditor never
touches Live or the network, so no fakes or sockets are needed here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from sc_produce import spec
from sc_produce.audit import audit_project, configure_parser, run
from sc_produce.models import (
    ArrangementSpec,
    ClipSpec,
    NoteSpec,
    StructureSpec,
)
from sc_produce.report import Report, Severity


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _errors(report: Report) -> list[str]:
    """Return the messages of all error-severity findings."""
    return [f.message for f in report.findings if f.severity is Severity.ERROR]


def _warnings(report: Report) -> list[str]:
    """Return the messages of all warning-severity findings."""
    return [f.message for f in report.findings if f.severity is Severity.WARNING]


def _severities(report: Report) -> set[Severity]:
    """Return the set of severities present in a report."""
    return {f.severity for f in report.findings}


# --------------------------------------------------------------------------- #
# Value checks
# --------------------------------------------------------------------------- #
def test_velocity_over_127_is_error() -> None:
    """A velocity above the MIDI maximum is the headline error and fails the audit."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=130)]
                )
            }
        }
    )

    report = audit_project(arrangement)

    assert report.passed is False
    assert any("velocity" in msg and "exceeds MIDI max 127" in msg for msg in _errors(report))


def test_velocity_below_zero_is_error() -> None:
    """A negative velocity is an error."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=-5)]
                )
            }
        }
    )

    report = audit_project(arrangement)

    assert report.passed is False
    assert any("velocity" in msg for msg in _errors(report))


def test_velocity_zero_is_warning_not_error() -> None:
    """A zero velocity is a (non-blocking) silent-note warning."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=0)]
                )
            }
        }
    )

    report = audit_project(arrangement)

    assert report.passed is True
    assert any("silent note" in msg for msg in _warnings(report))


@pytest.mark.parametrize("bad_pitch", ["H9", 200])
def test_invalid_pitch_is_error(bad_pitch: str | int) -> None:
    """An unparseable name or out-of-range int pitch is an error."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch=bad_pitch, start=0.0, duration=0.25, velocity=100)]
                )
            }
        }
    )

    report = audit_project(arrangement)

    assert report.passed is False
    assert any("invalid pitch" in msg for msg in _errors(report))


def test_non_positive_duration_and_negative_start_are_errors() -> None:
    """A zero duration and a negative start both produce errors."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=-1.0, duration=0.0, velocity=100)]
                )
            }
        }
    )

    report = audit_project(arrangement)

    errors = _errors(report)
    assert report.passed is False
    assert any("duration must be > 0" in msg for msg in errors)
    assert any("start must be >= 0" in msg for msg in errors)


def test_non_positive_clip_length_is_warning() -> None:
    """A clip length of zero (when set) is a warning, not a hard error."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    length=0.0,
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=100)],
                )
            }
        }
    )

    report = audit_project(arrangement)

    assert report.passed is True
    assert any("length" in msg for msg in _warnings(report))


def test_duplicate_pitch_start_is_warning() -> None:
    """Two notes with the same resolved (pitch, start) flag an ambiguity warning."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[
                        NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=100),
                        # Same pitch (C1 == MIDI 36) via integer spelling, same start.
                        NoteSpec(pitch=36, start=0.0, duration=0.5, velocity=90),
                    ]
                )
            }
        }
    )

    report = audit_project(arrangement)

    assert any("duplicate note key" in msg for msg in _warnings(report))


def test_clean_cell_gets_single_ok() -> None:
    """A cell with no value-level errors records exactly one OK finding."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[
                        NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110),
                        NoteSpec(pitch="C1", start=1.0, duration=0.25, velocity=110),
                    ]
                )
            }
        }
    )

    report = audit_project(arrangement)

    ok_findings = [f for f in report.findings if f.severity is Severity.OK]
    assert len(ok_findings) == 1
    assert "cell ok (2 notes)" in ok_findings[0].message


# --------------------------------------------------------------------------- #
# Type / structure checks
# --------------------------------------------------------------------------- #
def test_audio_track_with_midi_is_error(structure: StructureSpec) -> None:
    """Authoring notes on an audio track is the '7-tracks-as-audio' error."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "A_server_hum": ClipSpec(
                    notes=[NoteSpec(pitch="C3", start=0.0, duration=1.0, velocity=100)]
                )
            }
        }
    )

    report = audit_project(arrangement, structure)

    assert report.passed is False
    assert any("audio track A_server_hum cannot hold MIDI" in msg for msg in _errors(report))


def test_unknown_track_is_error(structure: StructureSpec) -> None:
    """A track absent from the structure (and not a return) is an error."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "Z_ghost": ClipSpec(
                    notes=[NoteSpec(pitch="C3", start=0.0, duration=1.0, velocity=100)]
                )
            }
        }
    )

    report = audit_project(arrangement, structure)

    assert report.passed is False
    assert any("unknown track Z_ghost" in msg for msg in _errors(report))


def test_return_track_cannot_hold_clips(structure: StructureSpec) -> None:
    """A clip on a return track is an error."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "R_REVERB": ClipSpec(
                    notes=[NoteSpec(pitch="C3", start=0.0, duration=1.0, velocity=100)]
                )
            }
        }
    )

    report = audit_project(arrangement, structure)

    assert report.passed is False
    assert any("return track cannot hold clips" in msg for msg in _errors(report))


def test_unknown_scene_is_error(structure: StructureSpec) -> None:
    """A scene absent from the structure's scene list is an error."""
    arrangement = ArrangementSpec(
        scenes={
            "Outro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=100)]
                )
            }
        }
    )

    report = audit_project(arrangement, structure)

    assert report.passed is False
    assert any("unknown scene Outro" in msg for msg in _errors(report))


def test_clean_arrangement_against_structure_passes(structure: StructureSpec) -> None:
    """A full, valid MIDI grid against the structure has no error findings."""
    note = NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=100)
    scenes: dict[str, dict[str, ClipSpec]] = {}
    for scene in structure.scenes:
        scenes[scene] = {track: ClipSpec(notes=[note]) for track in structure.midi_track_names()}
    arrangement = ArrangementSpec(scenes=scenes)

    report = audit_project(arrangement, structure)

    assert report.passed is True
    assert _errors(report) == []
    # A complete grid leaves no completeness warnings either.
    assert _warnings(report) == []


# --------------------------------------------------------------------------- #
# Completeness checks
# --------------------------------------------------------------------------- #
def test_incomplete_grid_warns_for_missing_cells(
    structure: StructureSpec, arrangement: ArrangementSpec
) -> None:
    """MIDI cells the structure expects but the arrangement omits are warnings."""
    report = audit_project(arrangement, structure)

    warnings = _warnings(report)
    # The fixture arrangement omits, e.g., D_clap entirely and several others.
    assert any("no clip authored for D_clap in Intro (incomplete grid)" in msg for msg in warnings)
    # The completeness check is over MIDI tracks only -- never the audio track.
    assert not any("A_server_hum" in msg for msg in warnings)


# --------------------------------------------------------------------------- #
# structure=None behaviour
# --------------------------------------------------------------------------- #
def test_no_structure_emits_info_and_still_runs_value_checks() -> None:
    """Without a structure an INFO is added and only value checks run."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=130)]
                )
            }
        }
    )

    report = audit_project(arrangement, None)

    info_msgs = [f.message for f in report.findings if f.severity is Severity.INFO]
    assert any("no structure provided" in msg for msg in info_msgs)
    # Value checks still run: the bad velocity is caught.
    assert report.passed is False
    assert any("exceeds MIDI max 127" in msg for msg in _errors(report))
    # No type/completeness findings without a structure.
    assert not any("incomplete grid" in msg for msg in _warnings(report))


# --------------------------------------------------------------------------- #
# CLI: run()
# --------------------------------------------------------------------------- #
def _namespace(**overrides: object) -> argparse.Namespace:
    """Build a Namespace with audit's default flag values, plus overrides."""
    defaults: dict[str, object] = {
        "arrangement": None,
        "structure": None,
        "out": None,
        "strict": False,
        "middle_c_octave": 3,
        "json": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _write(path: Path, text: str) -> str:
    """Write ``text`` to ``path`` and return the path as a string."""
    path.write_text(text, encoding="utf-8")
    return str(path)


@pytest.fixture
def clean_arrangement(structure: StructureSpec) -> ArrangementSpec:
    """A complete, valid MIDI grid for ``structure`` (no errors, no warnings)."""
    note = NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=100)
    scenes = {
        scene: {track: ClipSpec(notes=[note]) for track in structure.midi_track_names()}
        for scene in structure.scenes
    }
    return ArrangementSpec(title="clean", scenes=scenes)


def test_run_clean_returns_zero(
    tmp_path: Path, structure: StructureSpec, clean_arrangement: ArrangementSpec
) -> None:
    """A clean arrangement audited against its structure exits 0."""
    arr_path = _write(tmp_path / "arr.yaml", spec.dump_arrangement(clean_arrangement))
    struct_path = _write(tmp_path / "struct.yaml", spec.dump_structure(structure))

    code = run(_namespace(arrangement=arr_path, structure=struct_path))

    assert code == 0


def test_run_with_errors_returns_one(tmp_path: Path) -> None:
    """An arrangement with a value error exits 1."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=130)]
                )
            }
        }
    )
    arr_path = _write(tmp_path / "arr.yaml", spec.dump_arrangement(arrangement))

    code = run(_namespace(arrangement=arr_path))

    assert code == 1


def test_run_strict_fails_on_warnings_only(
    tmp_path: Path, structure: StructureSpec, arrangement: ArrangementSpec
) -> None:
    """Under --strict, a warnings-only (no-error) audit exits 1; without it, 0."""
    arr_path = _write(tmp_path / "arr.yaml", spec.dump_arrangement(arrangement))
    struct_path = _write(tmp_path / "struct.yaml", spec.dump_structure(structure))

    # The fixture arrangement is error-free but has completeness warnings.
    lenient = run(_namespace(arrangement=arr_path, structure=struct_path, strict=False))
    strict = run(_namespace(arrangement=arr_path, structure=struct_path, strict=True))

    assert lenient == 0
    assert strict == 1


def test_run_writes_out_when_passed(
    tmp_path: Path, structure: StructureSpec, clean_arrangement: ArrangementSpec
) -> None:
    """When the audit passes, ``-o/--out`` writes the validated arrangement."""
    arr_path = _write(tmp_path / "arr.yaml", spec.dump_arrangement(clean_arrangement))
    struct_path = _write(tmp_path / "struct.yaml", spec.dump_structure(structure))
    out_path = tmp_path / "validated.yaml"

    code = run(_namespace(arrangement=arr_path, structure=struct_path, out=str(out_path)))

    assert code == 0
    assert out_path.exists()
    # The written file is itself a loadable arrangement.
    reloaded = spec.load_arrangement(out_path)
    assert reloaded.title == clean_arrangement.title


def test_run_does_not_write_out_when_failed(tmp_path: Path) -> None:
    """A failing audit must not write the ``--out`` file."""
    arrangement = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=130)]
                )
            }
        }
    )
    arr_path = _write(tmp_path / "arr.yaml", spec.dump_arrangement(arrangement))
    out_path = tmp_path / "validated.yaml"

    code = run(_namespace(arrangement=arr_path, out=str(out_path)))

    assert code == 1
    assert not out_path.exists()


def test_run_syntax_error_returns_one(tmp_path: Path) -> None:
    """A malformed YAML arrangement surfaces as a syntax error and exits 1."""
    arr_path = _write(tmp_path / "broken.yaml", "scenes: [unclosed")

    code = run(_namespace(arrangement=arr_path))

    assert code == 1


def test_run_structure_syntax_error_returns_one(
    tmp_path: Path, clean_arrangement: ArrangementSpec
) -> None:
    """A malformed structure spec also surfaces as a syntax error and exits 1."""
    arr_path = _write(tmp_path / "arr.yaml", spec.dump_arrangement(clean_arrangement))
    struct_path = _write(tmp_path / "struct.yaml", "tracks: [unclosed")

    code = run(_namespace(arrangement=arr_path, structure=struct_path))

    assert code == 1


# --------------------------------------------------------------------------- #
# CLI: configure_parser
# --------------------------------------------------------------------------- #
def test_configure_parser_defaults() -> None:
    """The parser wires the expected flags with their documented defaults."""
    parser = argparse.ArgumentParser(prog="audit")
    configure_parser(parser)

    args = parser.parse_args(["song.yaml"])

    assert args.arrangement == "song.yaml"
    assert args.structure is None
    assert args.out is None
    assert args.strict is False
    assert args.middle_c_octave == 3
    assert args.json is False


def test_configure_parser_accepts_all_flags() -> None:
    """All optional flags parse into the expected attributes."""
    parser = argparse.ArgumentParser(prog="audit")
    configure_parser(parser)

    args = parser.parse_args(
        [
            "song.yaml",
            "--structure",
            "skeleton.yaml",
            "-o",
            "out.yaml",
            "--strict",
            "--middle-c-octave",
            "4",
            "--json",
        ]
    )

    assert args.structure == "skeleton.yaml"
    assert args.out == "out.yaml"
    assert args.strict is True
    assert args.middle_c_octave == 4
    assert args.json is True


def test_run_json_path_on_syntax_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """The syntax-error path still emits JSON when --json is set."""
    arr_path = _write(tmp_path / "broken.yaml", "scenes: [unclosed")

    code = run(_namespace(arrangement=arr_path, json=True))
    captured = capsys.readouterr()

    assert code == 1
    # Output is JSON (a report dict), not the plain-text rendering.
    assert '"passed": false' in captured.out
    assert "syntax error" in captured.out
