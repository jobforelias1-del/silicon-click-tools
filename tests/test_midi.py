"""Tests for pitch/note conversion helpers."""

from __future__ import annotations

import pytest

from sc_produce.midi import MAX_MIDI, note_spec_to_note, resolve_pitch
from sc_produce.models import NoteSpec


def test_resolve_pitch_int_passthrough():
    assert resolve_pitch(60) == 60
    assert resolve_pitch(0) == 0
    assert resolve_pitch(MAX_MIDI) == 127


def test_resolve_pitch_name_ableton_convention():
    # Middle C = C3 = 60 in Ableton convention (default octave 3).
    assert resolve_pitch("C3") == 60
    assert resolve_pitch("C1") == 36
    # In Ableton's convention A0 = 33 (MIDI 21 is labelled A-1, not A0).
    assert resolve_pitch("A0") == 33
    assert resolve_pitch("A-1") == 21


def test_resolve_pitch_name_spn_convention():
    # With middle C = C4, C4 maps to 60.
    assert resolve_pitch("C4", middle_c_octave=4) == 60


def test_resolve_pitch_out_of_range_int():
    with pytest.raises(ValueError):
        resolve_pitch(200)
    with pytest.raises(ValueError):
        resolve_pitch(-1)


def test_resolve_pitch_bad_name():
    with pytest.raises(ValueError):
        resolve_pitch("H9")
    with pytest.raises(ValueError):
        resolve_pitch("notanote")


def test_note_spec_to_note_conversion():
    spec = NoteSpec(pitch="C3", start=1.5, duration=0.25, velocity=90, mute=True)
    note = note_spec_to_note(spec)
    assert note.pitch == 60
    assert note.start == 1.5
    assert note.duration == 0.25
    assert note.velocity == 90.0
    assert note.mute is True


def test_note_spec_to_note_int_pitch():
    note = note_spec_to_note(NoteSpec(pitch=36, start=0.0, duration=1.0))
    assert note.pitch == 36
    assert note.velocity == 100.0  # default


def test_note_spec_to_note_propagates_bad_pitch():
    with pytest.raises(ValueError):
        note_spec_to_note(NoteSpec(pitch="ZZ", start=0.0, duration=1.0))
