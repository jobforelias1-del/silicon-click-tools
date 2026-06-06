"""An in-memory AbletonOSC fake for the sc_produce test suite.

This extends the faithful transport used by the ableton-bridge tests to also
honour the *creation* surface that :class:`sc_produce.live_session.LiveSession`
adds: ``create_{midi,audio,return}_track``, ``create_scene``, ``set/name`` and
``get/num_{tracks,scenes}``. It models a Live song closely enough to exercise real
round-trip behaviour -- idempotent clip creation, audio-track refusal, narrow
note removal, send routing -- with no running Ableton.

Reply shapes mirror AbletonOSC: reads echo their leading indices then the
value(s); writes are fire-and-forget and mutate state with no reply. Return tracks
live in a separate list (as in Live), so they do **not** appear in
``track_names``/``num_tracks``; creating one extends every track's send list.
"""

from __future__ import annotations

from ableton_bridge.exceptions import OSCTimeoutError

from sc_produce.live_session import LiveSession


class FakeClip:
    """An in-memory MIDI clip."""

    def __init__(self, name: str = "", length: float = 4.0) -> None:
        self.name = name
        self.length = length
        # Each note is [pitch, start, duration, velocity, mute].
        self.notes: list[list] = []


class FakeDevice:
    """An in-memory device with named parameters."""

    def __init__(self, name: str, parameters: list[tuple] | None = None) -> None:
        self.name = name
        self.parameters: list[list] = [[n, v] for n, v in (parameters or [])]


class FakeTrack:
    """An in-memory regular track (MIDI or audio)."""

    def __init__(
        self,
        name: str,
        has_midi_input: bool = True,
        devices: list[FakeDevice] | None = None,
        num_sends: int = 0,
    ) -> None:
        self.name = name
        self.has_midi_input = has_midi_input
        self.devices = devices or []
        self.sends = [0.0] * num_sends
        self.clip_slots: dict[int, FakeClip] = {}


class FakeReturn:
    """An in-memory return track (lives outside ``song.tracks``)."""

    def __init__(self, name: str = "") -> None:
        self.name = name


class FakeScene:
    """An in-memory scene (essentially a name)."""

    def __init__(self, name: str = "") -> None:
        self.name = name


class FakeLive:
    """A faithful in-memory stand-in for an AbletonOSC server."""

    def __init__(
        self,
        tracks: list[FakeTrack] | None = None,
        returns: list[FakeReturn] | None = None,
        scenes: list[FakeScene] | None = None,
        tempo: float = 120.0,
        signature=(4, 4),
        is_playing: bool = False,
        version=(12, 1),
    ) -> None:
        self.tracks = tracks if tracks is not None else []
        self.returns = returns if returns is not None else []
        self.scenes = scenes if scenes is not None else []
        self.tempo = tempo
        self.signature = list(signature)
        self.is_playing = is_playing
        self.version = version
        self.create_clip_enabled = True
        # Recorded traffic, for assertions.
        self.sent: list[tuple] = []
        self.bundles: list[list[tuple]] = []
        self.messages: list[str] = []
        self.closed = False
        self._normalise_sends()

    def _normalise_sends(self) -> None:
        """Make every track's send list match the number of return tracks."""
        for track in self.tracks:
            while len(track.sends) < len(self.returns):
                track.sends.append(0.0)

    # -- transport interface ------------------------------------------- #
    def request(self, address: str, *args, match_leading=()) -> list:
        """Return the reply AbletonOSC would send for a read address."""
        handler = self._read_handlers().get(address)
        if handler is None:
            raise OSCTimeoutError(f"FakeLive has no read handler for {address}")
        return handler(list(args))

    def send(self, address: str, *args) -> None:
        """Apply a fire-and-forget write."""
        self.sent.append((address, tuple(args)))
        self._apply_write(address, list(args))

    def send_bundle(self, messages) -> None:
        """Apply a bundle of writes in order (as AbletonOSC processes them)."""
        materialised = [(address, tuple(args)) for address, args in messages]
        self.bundles.append(materialised)
        for address, args in materialised:
            self.sent.append((address, tuple(args)))
            self._apply_write(address, list(args))

    def close(self) -> None:
        """Mark the transport closed."""
        self.closed = True

    # -- reads ---------------------------------------------------------- #
    def _read_handlers(self):
        return {
            "/live/test": lambda a: ["ok"],
            "/live/application/get/version": lambda a: [self.version[0], self.version[1]],
            "/live/song/get/tempo": lambda a: [self.tempo],
            "/live/song/get/is_playing": lambda a: [self.is_playing],
            "/live/song/get/signature_numerator": lambda a: [self.signature[0]],
            "/live/song/get/signature_denominator": lambda a: [self.signature[1]],
            "/live/song/get/num_tracks": lambda a: [len(self.tracks)],
            "/live/song/get/num_scenes": lambda a: [len(self.scenes)],
            "/live/song/get/track_names": lambda a: [t.name for t in self.tracks],
            "/live/song/get/scenes/name": lambda a: [s.name for s in self.scenes],
            "/live/track/get/has_midi_input": self._get_has_midi_input,
            "/live/track/get/devices/name": self._get_device_names,
            "/live/track/get/send": self._get_send,
            "/live/clip_slot/get/has_clip": self._get_has_clip,
            "/live/clip/get/name": self._get_clip_name,
            "/live/clip/get/length": self._get_clip_length,
            "/live/clip/get/notes": self._get_notes,
            "/live/device/get/parameters/name": self._get_parameter_names,
            "/live/device/get/parameter/value": self._get_parameter_value,
        }

    def _get_has_midi_input(self, args):
        index = int(args[0])
        return [index, self.tracks[index].has_midi_input]

    def _get_device_names(self, args):
        index = int(args[0])
        return [index] + [d.name for d in self.tracks[index].devices]

    def _get_send(self, args):
        track_index, send_index = int(args[0]), int(args[1])
        return [track_index, send_index, self.tracks[track_index].sends[send_index]]

    def _get_has_clip(self, args):
        track_index, clip_index = int(args[0]), int(args[1])
        has = clip_index in self.tracks[track_index].clip_slots
        return [track_index, clip_index, has]

    def _clip(self, args) -> FakeClip:
        track_index, clip_index = int(args[0]), int(args[1])
        slots = self.tracks[track_index].clip_slots
        if clip_index not in slots:
            raise OSCTimeoutError(f"No clip at track {track_index} slot {clip_index}")
        return slots[clip_index]

    def _get_clip_name(self, args):
        return [int(args[0]), int(args[1]), self._clip(args).name]

    def _get_clip_length(self, args):
        return [int(args[0]), int(args[1]), self._clip(args).length]

    def _get_notes(self, args):
        track_index, clip_index = int(args[0]), int(args[1])
        clip = self._clip(args)
        flat: list = []
        for pitch, start, duration, velocity, mute in clip.notes:
            flat += [pitch, start, duration, velocity, mute]
        return [track_index, clip_index] + flat

    def _get_parameter_names(self, args):
        track_index, device_index = int(args[0]), int(args[1])
        device = self.tracks[track_index].devices[device_index]
        return [track_index, device_index] + [p[0] for p in device.parameters]

    def _get_parameter_value(self, args):
        track_index, device_index, parameter_index = (int(args[0]), int(args[1]), int(args[2]))
        device = self.tracks[track_index].devices[device_index]
        return [track_index, device_index, parameter_index, device.parameters[parameter_index][1]]

    # -- writes --------------------------------------------------------- #
    def _apply_write(self, address: str, args: list) -> None:
        handler = {
            "/live/song/set/tempo": self._set_tempo,
            "/live/song/start_playing": lambda a: setattr(self, "is_playing", True),
            "/live/song/stop_playing": lambda a: setattr(self, "is_playing", False),
            "/live/song/continue_playing": lambda a: setattr(self, "is_playing", True),
            "/live/song/set/signature_numerator": lambda a: self._set_sig(0, a),
            "/live/song/set/signature_denominator": lambda a: self._set_sig(1, a),
            "/live/api/show_message": lambda a: self.messages.append(a[0]),
            "/live/track/set/send": self._set_send,
            "/live/track/set/name": self._set_track_name,
            "/live/scene/set/name": self._set_scene_name,
            "/live/scene/fire": lambda a: None,
            "/live/song/create_midi_track": lambda a: self._create_track(a, True),
            "/live/song/create_audio_track": lambda a: self._create_track(a, False),
            "/live/song/create_return_track": self._create_return_track,
            "/live/song/create_scene": self._create_scene,
            "/live/clip_slot/create_clip": self._create_clip,
            "/live/clip_slot/delete_clip": self._delete_clip,
            "/live/clip/add/notes": self._add_notes,
            "/live/clip/remove/notes": self._remove_notes,
            "/live/device/set/parameter/value": self._set_parameter_value,
        }.get(address)
        if handler is not None:
            handler(args)
        # Any other write is accepted silently, like AbletonOSC.

    def _set_tempo(self, args):
        self.tempo = args[0]

    def _set_sig(self, idx, args):
        self.signature[idx] = args[0]

    def _set_send(self, args):
        track_index, send_index, value = int(args[0]), int(args[1]), args[2]
        self.tracks[track_index].sends[send_index] = value

    def _set_track_name(self, args):
        index, name = int(args[0]), args[1]
        self.tracks[index].name = name

    def _set_scene_name(self, args):
        index, name = int(args[0]), args[1]
        self.scenes[index].name = name

    def _create_track(self, args, has_midi_input: bool):
        index = int(args[0]) if args else -1
        track = FakeTrack("", has_midi_input=has_midi_input, num_sends=len(self.returns))
        if index < 0 or index >= len(self.tracks):
            self.tracks.append(track)
        else:
            self.tracks.insert(index, track)

    def _create_return_track(self, args):
        self.returns.append(FakeReturn(""))
        self._normalise_sends()

    def _create_scene(self, args):
        index = int(args[0]) if args else -1
        scene = FakeScene("")
        if index < 0 or index >= len(self.scenes):
            self.scenes.append(scene)
        else:
            self.scenes.insert(index, scene)

    def _create_clip(self, args):
        track_index, clip_index, length = int(args[0]), int(args[1]), args[2]
        track = self.tracks[track_index]
        if not self.create_clip_enabled or not track.has_midi_input:
            return
        if clip_index in track.clip_slots:
            return
        track.clip_slots[clip_index] = FakeClip(name="", length=length)

    def _delete_clip(self, args):
        self.tracks[int(args[0])].clip_slots.pop(int(args[1]), None)

    def _add_notes(self, args):
        track_index, clip_index = int(args[0]), int(args[1])
        clip = self.tracks[track_index].clip_slots[clip_index]
        rest = args[2:]
        for offset in range(0, len(rest), 5):
            pitch, start, duration, velocity, mute = rest[offset : offset + 5]
            clip.notes.append(
                [int(pitch), float(start), float(duration), float(velocity), bool(mute)]
            )

    def _remove_notes(self, args):
        track_index, clip_index = int(args[0]), int(args[1])
        pitch_start, pitch_span, time_start, time_span = args[2], args[3], args[4], args[5]
        clip = self.tracks[track_index].clip_slots[clip_index]
        kept = []
        for note in clip.notes:
            pitch, start = note[0], note[1]
            in_pitch = pitch_start <= pitch < pitch_start + pitch_span
            in_time = time_start <= start < time_start + time_span
            if not (in_pitch and in_time):
                kept.append(note)
        clip.notes = kept

    def _set_parameter_value(self, args):
        track_index, device_index, parameter_index, value = (
            int(args[0]),
            int(args[1]),
            int(args[2]),
            args[3],
        )
        self.tracks[track_index].devices[device_index].parameters[parameter_index][1] = value


class FailingTransport:
    """A transport whose every operation raises, for failure-mode tests."""

    def __init__(self, exc: Exception | None = None) -> None:
        self.exc = exc or OSCTimeoutError("simulated transport failure")

    def request(self, address, *args, match_leading=()):
        raise self.exc

    def send(self, address, *args):
        raise self.exc

    def send_bundle(self, messages):
        raise self.exc

    def close(self):
        pass


def make_session(fake: FakeLive, *, middle_c_octave: int = 3) -> LiveSession:
    """Build a :class:`LiveSession` wired to a :class:`FakeLive` transport."""
    return LiveSession(transport=fake, middle_c_octave=middle_c_octave)


def empty_song() -> FakeLive:
    """A blank song: no tracks, returns or scenes (the scaffold starting point)."""
    return FakeLive()


def populated_song() -> FakeLive:
    """A song already holding the Pression Archivée skeleton, for apply tests."""
    tracks = [
        FakeTrack("D_kick", has_midi_input=True),
        FakeTrack("D_clap", has_midi_input=True),
        FakeTrack("K_piano", has_midi_input=True),
        FakeTrack("A_server_hum", has_midi_input=False),  # audio
    ]
    returns = [FakeReturn("R_REVERB"), FakeReturn("R_DELAY")]
    scenes = [FakeScene("Intro"), FakeScene("Verse"), FakeScene("Drop")]
    return FakeLive(tracks=tracks, returns=returns, scenes=scenes, tempo=142.0)
