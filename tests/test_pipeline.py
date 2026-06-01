"""Tests for the pipeline orchestration command."""

from __future__ import annotations

import argparse

from _fakes import empty_song, make_session
from ableton_bridge import OSCTimeoutError

from sc_produce import common
from sc_produce.models import (
    ArrangementSpec,
    ClipSpec,
    NoteSpec,
    StructureSpec,
    TrackSpec,
    TrackType,
)
from sc_produce.pipeline import run, run_pipeline
from sc_produce.spec import dump_arrangement, dump_structure


def _structure() -> StructureSpec:
    return StructureSpec(
        title="P",
        bpm=142.0,
        tracks=[
            TrackSpec(name="D_kick", type=TrackType.MIDI),
            TrackSpec(name="A_hum", type=TrackType.AUDIO),
        ],
        scenes=["Intro", "Verse"],
    )


def _clean_arrangement() -> ArrangementSpec:
    return ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                )
            }
        }
    )


def _bad_arrangement() -> ArrangementSpec:
    # velocity 200 -> audit error
    return ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=200)]
                )
            }
        }
    )


def _args(**overrides) -> argparse.Namespace:
    base = dict(
        structure="s.yml",
        arrangement="a.yml",
        launcher=None,
        dry_run=False,
        strict=False,
        force=False,
        host="127.0.0.1",
        send_port=11000,
        receive_port=11001,
        timeout=5.0,
        middle_c_octave=3,
        json=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


# -- run_pipeline ---------------------------------------------------------- #


def test_run_pipeline_happy_path_scaffolds_and_applies():
    live = empty_song()
    session = make_session(live)
    report = run_pipeline(_structure(), _clean_arrangement(), session)
    assert report.passed
    # scaffold created the tracks with correct types
    names = [t.name for t in live.tracks]
    assert "D_kick" in names and "A_hum" in names
    kick = next(t for t in live.tracks if t.name == "D_kick")
    assert kick.has_midi_input is True
    # apply wrote the note into clip slot 0 (Intro)
    assert len(kick.clip_slots[0].notes) == 1


def test_run_pipeline_blocks_on_audit_error_without_force():
    live = empty_song()
    report = run_pipeline(_structure(), _bad_arrangement(), make_session(live))
    assert not report.passed
    assert any("halted" in f.message for f in report.findings)
    # scaffold never ran -> no tracks created
    assert live.tracks == []


def test_run_pipeline_force_proceeds_despite_audit_error():
    live = empty_song()
    report = run_pipeline(_structure(), _bad_arrangement(), make_session(live), force=True)
    assert not report.passed  # the audit error is still recorded
    assert [t.name for t in live.tracks]  # but scaffold ran anyway


def test_run_pipeline_strict_blocks_on_warnings():
    live = empty_song()
    # clean arrangement still leaves Verse/D_kick uncovered -> completeness warning
    report = run_pipeline(_structure(), _clean_arrangement(), make_session(live), strict=True)
    assert any("halted" in f.message for f in report.findings)
    assert live.tracks == []


def test_run_pipeline_dry_run_makes_no_writes():
    live = empty_song()
    report = run_pipeline(_structure(), _clean_arrangement(), make_session(live), dry_run=True)
    addresses = [a for a, _ in live.sent]
    assert not any(a.startswith("/live/song/create") for a in addresses)
    assert "/live/clip/add/notes" not in addresses
    assert any(f.message.startswith("phase:") for f in report.findings)


# -- run() CLI ------------------------------------------------------------- #


def _write_specs(tmp_path, structure, arrangement):
    s = tmp_path / "s.yml"
    a = tmp_path / "a.yml"
    s.write_text(dump_structure(structure), encoding="utf-8")
    a.write_text(dump_arrangement(arrangement), encoding="utf-8")
    return str(s), str(a)


def test_run_launcher_path(tmp_path):
    s, a = _write_specs(tmp_path, _structure(), _clean_arrangement())
    out = tmp_path / "go.py"
    code = run(_args(structure=s, arrangement=a, launcher=str(out)))
    assert code == 0
    assert out.exists()
    source = out.read_text(encoding="utf-8")
    compile(source, str(out), "exec")
    assert "scaffold_project" in source and "apply_project" in source


def test_run_launcher_blocked_without_force(tmp_path):
    s, a = _write_specs(tmp_path, _structure(), _bad_arrangement())
    out = tmp_path / "go.py"
    code = run(_args(structure=s, arrangement=a, launcher=str(out)))
    assert code == 1
    assert not out.exists()


def test_run_apply_path(monkeypatch, tmp_path):
    s, a = _write_specs(tmp_path, _structure(), _clean_arrangement())
    live = empty_song()
    monkeypatch.setattr(common, "connect", lambda args: make_session(live))
    code = run(_args(structure=s, arrangement=a))
    assert code == 0
    assert [t.name for t in live.tracks]


def test_run_blocked_does_not_connect(monkeypatch, tmp_path):
    s, a = _write_specs(tmp_path, _structure(), _bad_arrangement())

    def explode(args):  # pragma: no cover - must never be called
        raise AssertionError("connect must not be called when blocked")

    monkeypatch.setattr(common, "connect", explode)
    assert run(_args(structure=s, arrangement=a)) == 1


def test_run_spec_error(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("- not a mapping\n", encoding="utf-8")
    a = tmp_path / "a.yml"
    a.write_text(dump_arrangement(_clean_arrangement()), encoding="utf-8")
    assert run(_args(structure=str(bad), arrangement=str(a))) == 1


def test_run_osc_timeout(monkeypatch, tmp_path):
    s, a = _write_specs(tmp_path, _structure(), _clean_arrangement())

    def timeout(args):
        raise OSCTimeoutError("no live")

    monkeypatch.setattr(common, "connect", timeout)
    assert run(_args(structure=s, arrangement=a)) == 1


def test_run_force_applies_and_returns_nonzero(monkeypatch, tmp_path):
    s, a = _write_specs(tmp_path, _structure(), _bad_arrangement())
    live = empty_song()
    monkeypatch.setattr(common, "connect", lambda args: make_session(live))
    # force proceeds, but the audit error keeps the exit code non-zero
    code = run(_args(structure=s, arrangement=a, force=True))
    assert code == 1
    assert [t.name for t in live.tracks]
