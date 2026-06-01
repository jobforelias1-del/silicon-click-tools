"""Helpers bridging :class:`~sc_produce.models.NoteSpec` and the Ableton bridge.

A :class:`NoteSpec` may carry its pitch as a MIDI integer or as a scientific name
(``"C3"``). These helpers resolve a pitch to a MIDI integer and convert a
``NoteSpec`` into the bridge's :class:`ableton_bridge.Note`, honouring the chosen
``middle_c_octave`` convention (3 == Ableton's labelling, 4 == strict SPN).
"""

from __future__ import annotations

from ableton_bridge import DEFAULT_MIDDLE_C_OCTAVE, Note, name_to_pitch

from .models import NoteSpec

#: Inclusive bounds for a valid MIDI value (pitch or velocity).
MIN_MIDI = 0
MAX_MIDI = 127


def resolve_pitch(pitch: int | str, middle_c_octave: int = DEFAULT_MIDDLE_C_OCTAVE) -> int:
    """Resolve a pitch (MIDI int or scientific name) to a MIDI integer.

    Args:
        pitch: A MIDI note number or a name such as ``"C3"`` / ``"F#5"``.
        middle_c_octave: Octave assigned to middle C (MIDI 60). Defaults to 3
            (Ableton's convention).

    Returns:
        The MIDI note number.

    Raises:
        ValueError: If a name cannot be parsed or an int is out of 0--127.
    """
    if isinstance(pitch, str):
        return name_to_pitch(pitch, middle_c_octave)
    value = int(pitch)
    if not MIN_MIDI <= value <= MAX_MIDI:
        raise ValueError(f"MIDI pitch must be in {MIN_MIDI}-{MAX_MIDI}, got {value}")
    return value


def note_spec_to_note(note: NoteSpec, middle_c_octave: int = DEFAULT_MIDDLE_C_OCTAVE) -> Note:
    """Convert a :class:`NoteSpec` into a bridge :class:`ableton_bridge.Note`.

    Args:
        note: The note spec to convert.
        middle_c_octave: Octave assigned to middle C (MIDI 60).

    Returns:
        An :class:`ableton_bridge.Note` with the pitch resolved to a MIDI int.

    Raises:
        ValueError: If the pitch cannot be resolved.
    """
    return Note(
        pitch=resolve_pitch(note.pitch, middle_c_octave),
        start=float(note.start),
        duration=float(note.duration),
        velocity=float(note.velocity),
        mute=bool(note.mute),
    )
