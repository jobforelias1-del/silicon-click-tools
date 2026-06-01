"""Shared pytest fixtures for the sc_produce test suite."""

from __future__ import annotations

import pytest
from _fakes import FakeLive, empty_song, make_session, populated_song

from sc_produce.models import (
    ArrangementSpec,
    ClipSpec,
    NoteSpec,
    SendSpec,
    StructureSpec,
    TrackSpec,
    TrackType,
)


@pytest.fixture
def empty_live() -> FakeLive:
    """A blank Live song (no tracks/returns/scenes)."""
    return empty_song()


@pytest.fixture
def populated_live() -> FakeLive:
    """A Live song already holding the Pression Archivée skeleton."""
    return populated_song()


@pytest.fixture
def empty_session(empty_live: FakeLive):
    """A :class:`LiveSession` over a blank song."""
    return make_session(empty_live)


@pytest.fixture
def session(populated_live: FakeLive):
    """A :class:`LiveSession` over the populated skeleton song."""
    return make_session(populated_live)


@pytest.fixture
def structure() -> StructureSpec:
    """A small but representative structure: MIDI + audio tracks, returns, sends."""
    return StructureSpec(
        title="Pression Archivée",
        bpm=142.0,
        key="Am",
        idiom="french_drill",
        time_signature=(4, 4),
        tracks=[
            TrackSpec(name="D_kick", type=TrackType.MIDI, instrument="drum_rack:808"),
            TrackSpec(name="D_clap", type=TrackType.MIDI),
            TrackSpec(name="K_piano", type=TrackType.MIDI),
            TrackSpec(name="A_server_hum", type=TrackType.AUDIO),
        ],
        returns=[TrackSpec(name="R_REVERB"), TrackSpec(name="R_DELAY")],
        sends=[SendSpec(from_="K_piano", to="R_REVERB", level=0.10)],
        scenes=["Intro", "Verse", "Drop"],
    )


@pytest.fixture
def arrangement() -> ArrangementSpec:
    """A small arrangement with a couple of populated cells."""
    return ArrangementSpec(
        title="Pression Archivée",
        scenes={
            "Intro": {
                "D_kick": ClipSpec(
                    length=4.0,
                    notes=[
                        NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110),
                        NoteSpec(pitch="C1", start=1.0, duration=0.25, velocity=110),
                    ],
                ),
                "K_piano": ClipSpec(
                    notes=[NoteSpec(pitch="A2", start=0.0, duration=2.0, velocity=80)]
                ),
            },
            "Verse": {
                "D_kick": ClipSpec(
                    notes=[NoteSpec(pitch="C1", start=0.0, duration=0.25, velocity=110)]
                ),
            },
        },
    )
