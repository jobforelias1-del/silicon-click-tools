"""Tests for the LiveSession wrapper (creation ops + shared transport)."""

from __future__ import annotations

from _fakes import FakeLive, FakeScene, FakeTrack, make_session

from sc_produce.live_session import LiveSession


def test_session_shares_transport_with_bridge():
    fake = FakeLive(tracks=[FakeTrack("a")])
    session = make_session(fake)
    # The bridge must talk over the same transport instance.
    assert session.osc is fake
    assert session.bridge._osc is fake
    assert session.middle_c_octave == 3


def test_ping_via_bridge():
    session = make_session(FakeLive())
    assert session.bridge.ping() is True


def test_counts():
    fake = FakeLive(
        tracks=[FakeTrack("a"), FakeTrack("b")],
        scenes=[FakeScene("Intro")],
    )
    session = make_session(fake)
    assert session.get_num_tracks() == 2
    assert session.get_num_scenes() == 1


def test_create_tracks_send_correct_addresses():
    fake = FakeLive()
    session = make_session(fake)
    session.create_midi_track()
    session.create_audio_track()
    session.create_return_track()
    session.create_scene()
    addresses = [a for a, _ in fake.sent]
    assert addresses == [
        "/live/song/create_midi_track",
        "/live/song/create_audio_track",
        "/live/song/create_return_track",
        "/live/song/create_scene",
    ]
    # MIDI/audio/scene carry the append index; return takes no args.
    assert fake.sent[0] == ("/live/song/create_midi_track", (-1,))
    assert fake.sent[2] == ("/live/song/create_return_track", ())
    # state mutated
    assert len(fake.tracks) == 2
    assert fake.tracks[0].has_midi_input is True
    assert fake.tracks[1].has_midi_input is False
    assert len(fake.returns) == 1
    assert len(fake.scenes) == 1


def test_set_names():
    fake = FakeLive(tracks=[FakeTrack(""), FakeTrack("")], scenes=[FakeScene("")])
    session = make_session(fake)
    session.set_track_name(0, "D_kick")
    session.set_track_name(1, "A_hum")
    session.set_scene_name(0, "Intro")
    assert [t.name for t in fake.tracks] == ["D_kick", "A_hum"]
    assert fake.scenes[0].name == "Intro"


def test_create_return_extends_track_sends():
    fake = FakeLive(tracks=[FakeTrack("a"), FakeTrack("b")])
    session = make_session(fake)
    assert all(len(t.sends) == 0 for t in fake.tracks)
    session.create_return_track()
    assert all(len(t.sends) == 1 for t in fake.tracks)


def test_context_manager_closes_transport():
    fake = FakeLive()
    with make_session(fake) as session:
        assert session.bridge.ping()
    assert fake.closed is True


def test_explicit_close():
    fake = FakeLive()
    session = LiveSession(transport=fake)
    session.close()
    assert fake.closed is True
