"""A session wrapper that adds track/scene creation on top of the bridge.

``ableton_bridge.AbletonBridge`` deliberately covers clips, notes, name
resolution, sends and device parameters -- but **not** creating or renaming
tracks and scenes. Scaffolding a brand-new set needs exactly those operations, so
:class:`LiveSession` adds them.

The important constraint: AbletonOSC replies to a single fixed UDP port (11001),
so only one client socket may exist per Live instance. :class:`LiveSession`
therefore creates **one** transport and shares it between the bridge (for
everything it already does well) and its own creation calls (sent as raw OSC on
the same socket). The creation addresses were read from the AbletonOSC source:

* ``/live/song/create_midi_track`` ``[index]`` (``-1`` appends)
* ``/live/song/create_audio_track`` ``[index]``
* ``/live/song/create_return_track`` (no args)
* ``/live/song/create_scene`` ``[index]``
* ``/live/track/set/name`` ``[track_index, name]``
* ``/live/scene/set/name`` ``[scene_index, name]``
* ``/live/song/get/num_tracks`` / ``/live/song/get/num_scenes`` -> ``(count,)``

Like all AbletonOSC writes, the creation calls are fire-and-forget: there is no
acknowledgement, so callers should compute target indices arithmetically and then
verify by reading back names (see :mod:`sc_produce.scaffold`).
"""

from __future__ import annotations

from ableton_bridge import DEFAULT_MIDDLE_C_OCTAVE, AbletonBridge
from ableton_bridge.osc_client import (
    DEFAULT_HOST,
    DEFAULT_RECEIVE_PORT,
    DEFAULT_SEND_PORT,
    DEFAULT_TIMEOUT,
    OSCClient,
)


class LiveSession:
    """A live Ableton session: an :class:`AbletonBridge` plus creation ops.

    May be used as a context manager, which closes the shared transport on exit::

        with LiveSession() as session:
            session.bridge.ping()
            session.create_midi_track()
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        send_port: int = DEFAULT_SEND_PORT,
        receive_port: int = DEFAULT_RECEIVE_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        *,
        transport=None,
        middle_c_octave: int = DEFAULT_MIDDLE_C_OCTAVE,
    ) -> None:
        """Open a session against a running AbletonOSC instance.

        Args:
            host: Host where AbletonOSC listens. Defaults to ``127.0.0.1``.
            send_port: UDP port AbletonOSC listens on. Defaults to 11000.
            receive_port: UDP port AbletonOSC replies to. Defaults to 11001.
            timeout: Seconds to wait for a reply before raising
                :class:`ableton_bridge.OSCTimeoutError`.
            transport: An optional pre-built transport (``send``/``send_bundle``/
                ``request``/``close``). Mainly for testing; when omitted a real
                :class:`ableton_bridge.osc_client.OSCClient` is created and shared.
            middle_c_octave: Octave for middle C in note names (3 == Ableton).
        """
        self._osc = (
            transport
            if transport is not None
            else OSCClient(host, send_port, receive_port, timeout)
        )
        self.bridge = AbletonBridge(transport=self._osc, middle_c_octave=middle_c_octave)

    @property
    def osc(self):
        """The shared OSC transport (used by both the bridge and creation calls)."""
        return self._osc

    @property
    def middle_c_octave(self) -> int:
        """The octave assigned to middle C, mirrored from the bridge."""
        return self.bridge.middle_c_octave

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        """Close the shared transport."""
        self._osc.close()

    def __enter__(self) -> LiveSession:
        """Enter the context manager.

        Returns:
            This session.
        """
        return self

    def __exit__(self, *exc) -> None:
        """Close the transport on context-manager exit."""
        self.close()

    # ------------------------------------------------------------------ #
    # Counts (used to compute where appended tracks/scenes will land)
    # ------------------------------------------------------------------ #
    def get_num_tracks(self) -> int:
        """Return the number of regular tracks in the song.

        Returns:
            The track count.

        Raises:
            OSCTimeoutError: If AbletonOSC does not reply.
        """
        params = self._osc.request("/live/song/get/num_tracks")
        return int(params[0])

    def get_num_scenes(self) -> int:
        """Return the number of scenes in the song.

        Returns:
            The scene count.

        Raises:
            OSCTimeoutError: If AbletonOSC does not reply.
        """
        params = self._osc.request("/live/song/get/num_scenes")
        return int(params[0])

    # ------------------------------------------------------------------ #
    # Creation (fire-and-forget, like all AbletonOSC writes)
    # ------------------------------------------------------------------ #
    def create_midi_track(self, index: int = -1) -> None:
        """Create a MIDI track.

        Args:
            index: Position to insert at; ``-1`` (default) appends at the end.
        """
        self._osc.send("/live/song/create_midi_track", int(index))

    def create_audio_track(self, index: int = -1) -> None:
        """Create an audio track.

        Args:
            index: Position to insert at; ``-1`` (default) appends at the end.
        """
        self._osc.send("/live/song/create_audio_track", int(index))

    def create_return_track(self) -> None:
        """Create a return track (always appended; Live takes no index)."""
        self._osc.send("/live/song/create_return_track")

    def create_scene(self, index: int = -1) -> None:
        """Create a scene.

        Args:
            index: Position to insert at; ``-1`` (default) appends at the end.
        """
        self._osc.send("/live/song/create_scene", int(index))

    def set_track_name(self, track_index: int, name: str) -> None:
        """Rename a track by index.

        Args:
            track_index: The zero-based track index.
            name: The new name.
        """
        self._osc.send("/live/track/set/name", int(track_index), str(name))

    def set_scene_name(self, scene_index: int, name: str) -> None:
        """Rename a scene by index.

        Args:
            scene_index: The zero-based scene index.
            name: The new name.
        """
        self._osc.send("/live/scene/set/name", int(scene_index), str(name))
