"""Tests for :mod:`sc_produce.scaffold`.

These exercise the scaffold against the in-memory :class:`_fakes.FakeLive`, which
faithfully models AbletonOSC's creation surface (append-on-create, name writes,
return/send normalisation). The headline behaviour under test is **correct track
type**: a MIDI track must be created with ``create_midi_track`` and an audio track
with ``create_audio_track``, and an existing track whose type disagrees with the
spec must surface as a hard error.
"""

from __future__ import annotations

import argparse

import pytest
from _fakes import FakeLive, FakeReturn, FakeScene, FakeTrack, make_session

from sc_produce import common, scaffold, spec
from sc_produce.models import SendSpec, StructureSpec, TrackSpec, TrackType
from sc_produce.report import Severity
from sc_produce.spec import dump_structure


def _has_create(live: FakeLive, address: str) -> bool:
    """Return whether ``live`` recorded a write to ``address``."""
    return any(sent_address == address for sent_address, _ in live.sent)


def _track_index(live: FakeLive, name: str) -> int:
    """Return the index of the track named ``name`` in ``live``."""
    return [t.name for t in live.tracks].index(name)


def _messages(report) -> str:
    """Join all finding messages into a single searchable string."""
    return "\n".join(f.message for f in report.findings)


# --------------------------------------------------------------------------- #
# Blank-session scaffold: tracks created in order, with correct types
# --------------------------------------------------------------------------- #
def test_blank_scaffold_creates_tracks_in_order_with_correct_types(
    empty_live: FakeLive,
    structure: StructureSpec,
) -> None:
    """A blank session gets every track, in order, with the right MIDI/audio type."""
    session = make_session(empty_live)

    report = scaffold.scaffold_project(structure, session, settle=0.0)

    assert [t.name for t in empty_live.tracks] == [
        "D_kick",
        "D_clap",
        "K_piano",
        "A_server_hum",
    ]
    # MIDI-input flag matches the spec: the three MIDI tracks True, the audio False.
    midi_by_name = {t.name: t.has_midi_input for t in empty_live.tracks}
    assert midi_by_name == {
        "D_kick": True,
        "D_clap": True,
        "K_piano": True,
        "A_server_hum": False,
    }
    # The headline behaviour: the correct create address was used for each type.
    assert _has_create(empty_live, "/live/song/create_midi_track")
    assert _has_create(empty_live, "/live/song/create_audio_track")
    assert report.passed


def test_blank_scaffold_creates_returns_scenes_and_sets_tempo(
    empty_live: FakeLive,
    structure: StructureSpec,
) -> None:
    """Returns and scenes are created and tempo is set on a fresh session."""
    session = make_session(empty_live)

    scaffold.scaffold_project(structure, session, settle=0.0)

    assert len(empty_live.returns) == 2
    assert [s.name for s in empty_live.scenes] == ["Intro", "Verse", "Drop"]
    assert empty_live.tempo == 142.0
    assert list(empty_live.signature) == [4, 4]


def test_blank_scaffold_applies_send(
    empty_live: FakeLive,
    structure: StructureSpec,
) -> None:
    """The K_piano -> R_REVERB send (index 0) is written at level 0.10."""
    session = make_session(empty_live)

    report = scaffold.scaffold_project(structure, session, settle=0.0)

    k_piano = _track_index(empty_live, "K_piano")
    assert empty_live.tracks[k_piano].sends[0] == pytest.approx(0.10)
    assert report.passed


# --------------------------------------------------------------------------- #
# Idempotency
# --------------------------------------------------------------------------- #
def test_scaffold_is_idempotent(
    empty_live: FakeLive,
    structure: StructureSpec,
) -> None:
    """Running scaffold twice does not duplicate tracks or scenes."""
    session = make_session(empty_live)

    scaffold.scaffold_project(structure, session, settle=0.0)
    track_names_after_first = [t.name for t in empty_live.tracks]
    scene_names_after_first = [s.name for s in empty_live.scenes]
    returns_after_first = len(empty_live.returns)

    second = scaffold.scaffold_project(structure, session, settle=0.0)

    assert [t.name for t in empty_live.tracks] == track_names_after_first
    assert [s.name for s in empty_live.scenes] == scene_names_after_first
    # Returns are name-unresolvable: on the (now non-blank) second run they are
    # left untouched rather than duplicated.
    assert len(empty_live.returns) == returns_after_first
    # The second run reports the existing tracks/scenes as skipped.
    messages = _messages(second)
    assert "track exists, skipped" in messages
    assert "scene exists, skipped" in messages
    assert second.passed


# --------------------------------------------------------------------------- #
# Wrong-type detection (the headline bug)
# --------------------------------------------------------------------------- #
def test_wrong_type_existing_track_is_an_error() -> None:
    """An existing audio track where the spec declares MIDI is a hard error.

    The session is pre-populated with explicit returns and scenes (so the
    scaffold takes its non-blank/idempotent paths) and a ``D_kick`` track that was
    built as *audio* while the spec declares it MIDI -- the headline bug.
    """
    live = FakeLive(
        tracks=[FakeTrack("D_kick", has_midi_input=False)],  # built as audio
        returns=[FakeReturn("R_REVERB")],
        scenes=[FakeScene("Intro")],
    )
    session = make_session(live)
    structure = StructureSpec(
        bpm=120.0,
        tracks=[TrackSpec(name="D_kick", type=TrackType.MIDI)],
        scenes=["Intro"],
    )

    report = scaffold.scaffold_project(structure, session, settle=0.0)

    assert not report.passed
    wrong_type = [
        f for f in report.findings if f.severity is Severity.ERROR and "wrong type" in f.message
    ]
    assert wrong_type, "expected a 'wrong type' error finding"
    assert wrong_type[0].track == "D_kick"


# --------------------------------------------------------------------------- #
# Send to an unknown return
# --------------------------------------------------------------------------- #
def test_send_to_unknown_return_is_an_error(empty_live: FakeLive) -> None:
    """A send whose destination return is not in the structure is an error."""
    session = make_session(empty_live)
    structure = StructureSpec(
        bpm=120.0,
        tracks=[TrackSpec(name="K_piano", type=TrackType.MIDI)],
        returns=[TrackSpec(name="R_REVERB")],
        sends=[SendSpec(from_="K_piano", to="R_NONEXISTENT", level=0.5)],
    )

    report = scaffold.scaffold_project(structure, session, settle=0.0)

    assert not report.passed
    unknown = [
        f for f in report.findings if f.severity is Severity.ERROR and "unknown return" in f.message
    ]
    assert unknown, "expected an 'unknown return' error finding"


# --------------------------------------------------------------------------- #
# Dry run: no writes, plan findings only
# --------------------------------------------------------------------------- #
def test_dry_run_performs_no_creation_writes(
    empty_live: FakeLive,
    structure: StructureSpec,
) -> None:
    """``dry_run=True`` issues no create/name/tempo writes but records a plan."""
    session = make_session(empty_live)

    report = scaffold.scaffold_project(structure, session, settle=0.0, dry_run=True)

    # No state mutated, no writes recorded.
    assert empty_live.sent == []
    assert empty_live.tracks == []
    assert empty_live.returns == []
    assert empty_live.scenes == []
    assert not _has_create(empty_live, "/live/song/create_midi_track")
    assert not _has_create(empty_live, "/live/song/create_audio_track")
    # The plan is recorded as info findings.
    assert report.count(Severity.INFO) > 0
    messages = _messages(report)
    assert "would set tempo" in messages
    assert "would create" in messages


# --------------------------------------------------------------------------- #
# run(): exercise the CLI entry point without a real socket
# --------------------------------------------------------------------------- #
def _run_args(structure_path: str) -> argparse.Namespace:
    """Build a parsed-args namespace for ``scaffold.run`` via its own parser."""
    parser = argparse.ArgumentParser()
    scaffold.configure_parser(parser)
    return parser.parse_args([str(structure_path)])


def test_run_scaffolds_and_returns_zero(
    tmp_path,
    structure: StructureSpec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``run`` loads a real YAML, connects (monkeypatched) and scaffolds OK."""
    structure_file = tmp_path / "structure.yaml"
    structure_file.write_text(dump_structure(structure), encoding="utf-8")

    live = FakeLive()
    monkeypatch.setattr(common, "connect", lambda args: make_session(live))

    args = _run_args(structure_file)
    code = scaffold.run(args)

    assert code == 0
    assert [t.name for t in live.tracks] == ["D_kick", "D_clap", "K_piano", "A_server_hum"]
    assert live.closed  # used as a context manager


def test_run_with_bad_yaml_returns_one(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A spec that fails to load makes ``run`` fail fast with exit code 1."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("tracks: [name: oops, extra_unknown_key: 1]\n", encoding="utf-8")

    # connect must never be reached; fail loudly if it is.
    def _boom(args: argparse.Namespace):
        raise AssertionError("connect should not be called on a load failure")

    monkeypatch.setattr(common, "connect", _boom)

    args = _run_args(bad)
    code = scaffold.run(args)

    assert code == 1


def test_run_surfaces_spec_error_for_missing_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing structure file is a :class:`SpecError` and ``run`` returns 1."""

    def _boom(args: argparse.Namespace):
        raise AssertionError("connect should not be called on a load failure")

    monkeypatch.setattr(common, "connect", _boom)

    missing = tmp_path / "nope.yaml"
    with pytest.raises(spec.SpecError):
        spec.load_structure(missing)  # sanity-check the load path itself

    args = _run_args(missing)
    assert scaffold.run(args) == 1


# --------------------------------------------------------------------------- #
# Populated session: returns left untouched with a warning
# --------------------------------------------------------------------------- #
def test_populated_session_warns_returns_untouched(
    populated_live: FakeLive,
    structure: StructureSpec,
) -> None:
    """On a non-blank session, returns are left untouched and a warning is added."""
    before = len(populated_live.returns)
    session = make_session(populated_live)

    report = scaffold.scaffold_project(structure, session, settle=0.0)

    assert len(populated_live.returns) == before  # not re-created
    warnings = [f for f in report.findings if f.severity is Severity.WARNING]
    assert any("return" in f.message.lower() for f in warnings)


def test_return_track_under_tracks_is_warned(empty_live: FakeLive) -> None:
    """A RETURN-typed entry in ``tracks`` is a spec mistake: warned and skipped."""
    session = make_session(empty_live)
    structure = StructureSpec(
        bpm=120.0,
        tracks=[
            TrackSpec(name="D_kick", type=TrackType.MIDI),
            TrackSpec(name="R_OOPS", type=TrackType.RETURN),
        ],
    )

    report = scaffold.scaffold_project(structure, session, settle=0.0)

    assert [t.name for t in empty_live.tracks] == ["D_kick"]  # the return was skipped
    assert any(f.severity is Severity.WARNING and f.track == "R_OOPS" for f in report.findings)


# A module-level smoke check that the CLI metadata is wired as the contract states.
def test_cli_metadata() -> None:
    """The module exposes the expected CLI name/help and parser arguments."""
    assert scaffold.NAME == "scaffold"
    assert scaffold.HELP == "Build the Live skeleton (tracks/scenes/sends) from a structure spec"
    parser = argparse.ArgumentParser()
    scaffold.configure_parser(parser)
    ns = parser.parse_args(["some/path.yaml"])
    assert ns.structure == "some/path.yaml"
    assert ns.dry_run is False
    assert ns.settle == pytest.approx(0.2)
