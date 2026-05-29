"""Tests for the pydantic spec models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sc_produce.models import (
    ArrangementSpec,
    ClipSpec,
    NoteSpec,
    SendSpec,
    StructureSpec,
    TrackSpec,
    TrackType,
)


def test_track_defaults_to_midi():
    track = TrackSpec(name="D_kick")
    assert track.type is TrackType.MIDI
    assert track.instrument is None


def test_send_uses_from_alias_both_ways():
    send = SendSpec(**{"from": "K_piano", "to": "R_REVERB", "level": 0.1})
    assert send.from_ == "K_piano"
    # populate_by_name also allows the python field name
    send2 = SendSpec(from_="A", to="B", level=0.2)
    assert send2.from_ == "A"
    dumped = send.model_dump(by_alias=True)
    assert dumped["from"] == "K_piano"


def test_structure_track_lookups(structure: StructureSpec):
    assert structure.track("D_kick").type is TrackType.MIDI
    assert structure.track("missing") is None
    assert structure.is_midi("D_kick") is True
    assert structure.is_audio("A_server_hum") is True
    assert structure.is_midi("A_server_hum") is False
    assert structure.midi_track_names() == ["D_kick", "D_clap", "K_piano"]
    assert structure.audio_track_names() == ["A_server_hum"]


def test_return_order_prefers_explicit_returns(structure: StructureSpec):
    assert structure.return_order() == ["R_REVERB", "R_DELAY"]
    assert structure.send_index("R_REVERB") == 0
    assert structure.send_index("R_DELAY") == 1
    assert structure.send_index("R_UNKNOWN") is None


def test_return_order_falls_back_to_send_destinations():
    spec = StructureSpec(
        tracks=[TrackSpec(name="a"), TrackSpec(name="b")],
        sends=[
            SendSpec(from_="a", to="R_DELAY", level=0.1),
            SendSpec(from_="b", to="R_REVERB", level=0.2),
            SendSpec(from_="a", to="R_DELAY", level=0.3),
        ],
    )
    # No explicit returns -> order derived from first appearance in sends.
    assert spec.return_order() == ["R_DELAY", "R_REVERB"]
    assert spec.send_index("R_DELAY") == 0
    assert spec.send_index("R_REVERB") == 1


def test_scene_index(structure: StructureSpec):
    assert structure.scene_index("Intro") == 0
    assert structure.scene_index("Drop") == 2
    assert structure.scene_index("Nope") is None


def test_extra_keys_are_forbidden():
    with pytest.raises(ValidationError):
        TrackSpec(name="x", typ="midi")  # typo'd key
    with pytest.raises(ValidationError):
        NoteSpec(pitch="C3", start=0.0, duration=1.0, velociy=100)  # typo'd key


def test_note_velocity_loads_unconstrained():
    # The auditor reports >127; the model must still load it.
    note = NoteSpec(pitch=200, start=-1.0, duration=0.0, velocity=999)
    assert note.velocity == 999
    assert note.pitch == 200


def test_arrangement_cell_and_iteration():
    arr = ArrangementSpec(
        scenes={
            "Intro": {
                "D_kick": ClipSpec(notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25)]),
                "K_piano": ClipSpec(notes=[]),
            },
            "Verse": {"D_kick": ClipSpec(notes=[])},
        }
    )
    assert arr.cell("Intro", "D_kick") is not None
    assert arr.cell("Intro", "missing") is None
    assert arr.cell("Nope", "D_kick") is None
    cells = list(arr.iter_cells())
    assert len(cells) == 3
    assert cells[0][0] == "Intro" and cells[0][1] == "D_kick"
    assert arr.scene_names() == ["Intro", "Verse"]


def test_clip_defaults():
    clip = ClipSpec()
    assert clip.length is None
    assert clip.notes == []
