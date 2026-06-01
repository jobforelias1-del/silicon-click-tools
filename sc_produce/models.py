"""Pydantic models for Silicon Click track specs.

The pipeline uses **two** spec documents, kept deliberately separate:

* :class:`StructureSpec` -- the Live *skeleton*: tempo/key/idiom, the tracks (with
  their correct MIDI/audio type), return tracks, sends and the scene list. This is
  what ``sc-produce scaffold`` materialises and what ``compose`` briefs Mistral
  against.
* :class:`ArrangementSpec` -- the *content* authored by Mistral: for each
  ``scene -> track`` cell, the MIDI clip (its notes). This is what ``audit`` checks
  and ``apply`` writes into Live.

Splitting them mirrors the real workflow (the skeleton is designed up front; the
notes are authored later and iterated on) and means an arrangement can be
re-audited and re-applied against a stable structure.

Design notes:
    * Note ``velocity`` and ``pitch`` are intentionally **unconstrained** at the
      model level so a flawed Mistral output still *loads* and can be reported on
      by :mod:`sc_produce.audit` (rather than failing at parse time). Genuinely
      malformed documents -- unknown keys, wrong types -- are rejected via
      ``extra="forbid"`` and surface as "syntax errors", exactly the class of bug
      that bit the team on the first manual run.
    * Clip slot indices are *not* stored on the arrangement. A scene's clip slot
      index is its position in :attr:`StructureSpec.scenes`; that single source of
      truth keeps the scene/track grid unambiguous.
"""

from __future__ import annotations

from collections.abc import Iterator
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TrackType(str, Enum):
    """The kind of a track, which determines what it can hold."""

    MIDI = "midi"
    AUDIO = "audio"
    RETURN = "return"


class TrackSpec(BaseModel):
    """A single track in the Live skeleton.

    Attributes:
        name: The track's name; also its handle for routing arrangement cells.
        type: ``midi``, ``audio`` or ``return``. The headline bug this tool exists
            to prevent is creating a track as ``audio`` when MIDI was authored for
            it, so this field is load-bearing.
        instrument: Optional free-form hint (e.g. a drum-rack path) recorded for
            documentation; v0.1 does not load instruments over OSC.
        color: Optional Live colour index, recorded for documentation.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    type: TrackType = TrackType.MIDI
    instrument: str | None = None
    color: int | None = None


class SendSpec(BaseModel):
    """A send from a regular track to a return track.

    AbletonOSC addresses sends by *index* (0 == first return track), so the
    ``to`` name is resolved to a send index via the structure's return ordering
    (see :meth:`StructureSpec.send_index`).

    Attributes:
        from_: The source track name (YAML key ``from``).
        to: The destination return-track name.
        level: The send level, 0.0--1.0.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    level: float = 0.0


class StructureSpec(BaseModel):
    """The Live skeleton: tempo, tracks, returns, sends and scenes.

    Attributes:
        title: Optional human title for the project.
        bpm: Song tempo in beats per minute.
        key: Optional musical key (e.g. ``Am``), recorded and passed to the brief.
        idiom: Optional style hint (e.g. ``french_drill``) passed to the brief.
        time_signature: Song time signature as ``(numerator, denominator)``.
        tracks: Regular (MIDI/audio) tracks, in session order.
        returns: Return tracks, in order; their order defines send indices.
        sends: Send routings from tracks to returns.
        scenes: Scene names, in session order; a scene's index is its clip slot.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    bpm: float = 120.0
    key: str | None = None
    idiom: str | None = None
    time_signature: tuple[int, int] = (4, 4)
    tracks: list[TrackSpec] = Field(default_factory=list)
    returns: list[TrackSpec] = Field(default_factory=list)
    sends: list[SendSpec] = Field(default_factory=list)
    scenes: list[str] = Field(default_factory=list)

    def track(self, name: str) -> TrackSpec | None:
        """Return the regular track with ``name``, or ``None`` if absent."""
        for track in self.tracks:
            if track.name == name:
                return track
        return None

    def is_midi(self, name: str) -> bool:
        """Return whether ``name`` is a known MIDI track."""
        track = self.track(name)
        return track is not None and track.type is TrackType.MIDI

    def is_audio(self, name: str) -> bool:
        """Return whether ``name`` is a known audio track."""
        track = self.track(name)
        return track is not None and track.type is TrackType.AUDIO

    def midi_track_names(self) -> list[str]:
        """Return the names of all MIDI tracks, in order."""
        return [t.name for t in self.tracks if t.type is TrackType.MIDI]

    def audio_track_names(self) -> list[str]:
        """Return the names of all audio tracks, in order."""
        return [t.name for t in self.tracks if t.type is TrackType.AUDIO]

    def return_order(self) -> list[str]:
        """Return the return-track names whose order defines send indices.

        Uses the explicit :attr:`returns` list when present; otherwise falls back
        to the order in which return names first appear as send destinations, so a
        structure that only declares ``sends`` still resolves cleanly.
        """
        if self.returns:
            return [r.name for r in self.returns]
        seen: list[str] = []
        for send in self.sends:
            if send.to not in seen:
                seen.append(send.to)
        return seen

    def send_index(self, return_name: str) -> int | None:
        """Resolve a return-track name to its send index, or ``None``."""
        order = self.return_order()
        try:
            return order.index(return_name)
        except ValueError:
            return None

    def scene_index(self, scene_name: str) -> int | None:
        """Resolve a scene name to its clip slot index, or ``None``."""
        try:
            return self.scenes.index(scene_name)
        except ValueError:
            return None


class NoteSpec(BaseModel):
    """A single MIDI note in an arrangement cell.

    ``pitch`` and ``velocity`` are intentionally unvalidated here so that flawed
    values (e.g. ``velocity`` above 127 -- a real bug from the first run) load
    successfully and are reported by the auditor instead of crashing the parser.

    Attributes:
        pitch: MIDI note number (0--127) or a scientific name such as ``"C3"``.
        start: Start position in beats from the clip origin.
        duration: Note length in beats.
        velocity: MIDI velocity; nominally 0--127.
        mute: Whether the note is muted.
    """

    model_config = ConfigDict(extra="forbid")

    pitch: int | str
    start: float
    duration: float
    velocity: float = 100.0
    mute: bool = False


class CueSpec(BaseModel):
    """A single audio-clip trigger in an audio-track cell.

    Audio tracks cannot hold MIDI notes, but they can hold *clips* that reference
    a recorded sample. A cue is the audio counterpart of a :class:`NoteSpec`: it
    says "place this sample here, this long". The bridge has no sample-load API
    over OSC, so cues are authored and audited now and *materialised later* (by
    hand, or by a future loader); :mod:`sc_produce.apply` records but does not
    write them.

    Attributes:
        sample: Name or hint of the clip/sample to place (e.g. ``"fx_riser_01"``).
        beat: Start position in beats from the clip origin (mirrors a note start).
        length: Clip length in beats.
        gain_db: Optional level trim in dB.
    """

    model_config = ConfigDict(extra="forbid")

    sample: str
    beat: float
    length: float
    gain_db: float | None = None


class ClipSpec(BaseModel):
    """The contents of one ``scene -> track`` cell.

    A cell is either a **MIDI** cell (``notes``) or an **audio** cell (``cues``),
    never both -- the auditor rejects a cell that mixes them, and cross-checks each
    kind against the target track's declared type (notes belong on MIDI tracks,
    cues on audio tracks).

    Attributes:
        length: Optional clip length in beats; defaults applied at apply time.
        notes: The MIDI notes the clip should contain (the desired final state).
        cues: The audio-clip triggers for an audio-track cell.
    """

    model_config = ConfigDict(extra="forbid")

    length: float | None = None
    notes: list[NoteSpec] = Field(default_factory=list)
    cues: list[CueSpec] = Field(default_factory=list)


class ArrangementSpec(BaseModel):
    """The authored content: a ``scene -> track -> clip`` grid.

    Attributes:
        title: Optional title, useful for cross-checking against a structure.
        scenes: Mapping of scene name to a mapping of track name to its clip.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    scenes: dict[str, dict[str, ClipSpec]] = Field(default_factory=dict)

    def cell(self, scene: str, track: str) -> ClipSpec | None:
        """Return the clip for ``(scene, track)``, or ``None`` if absent."""
        return self.scenes.get(scene, {}).get(track)

    def iter_cells(self) -> Iterator[tuple[str, str, ClipSpec]]:
        """Yield ``(scene_name, track_name, clip)`` for every populated cell."""
        for scene_name, tracks in self.scenes.items():
            for track_name, clip in tracks.items():
                yield scene_name, track_name, clip

    def scene_names(self) -> list[str]:
        """Return the scene names present in the arrangement, in order."""
        return list(self.scenes.keys())
