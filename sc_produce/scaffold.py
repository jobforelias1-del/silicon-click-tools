"""Build the Live skeleton (tracks, scenes, sends) from a :class:`StructureSpec`.

``sc-produce scaffold`` materialises the *structure* document into a running
Ableton Live set: it sets tempo and time signature, creates the regular tracks
**with their correct MIDI/audio type**, creates return tracks and scenes, and
wires sends. It is deliberately *idempotent* -- running it against a set that
already holds (some of) the skeleton skips what exists and only fills the gaps.

The single most important guarantee of this whole tool is **correct track
type**. The team's first manual run created a track as *audio* when MIDI clips
were authored for it; AbletonOSC then dropped every note silently (audio tracks
have no MIDI input and writes are unacknowledged -- see
``KNOWN_LIMITATIONS.md``). So:

* missing tracks are created with :meth:`LiveSession.create_midi_track` /
  :meth:`LiveSession.create_audio_track` strictly according to
  :attr:`TrackSpec.type`; and
* an *existing* track whose actual MIDI-input capability disagrees with the spec
  is reported as a hard **error** (the headline "built as the wrong type" bug),
  because re-typing a track is not something this tool will silently paper over.

Because AbletonOSC writes are fire-and-forget, creations are issued first, then
(after an optional ``settle`` pause to let Live catch up) names are set and the
result is **verified** by reading the names back -- never assumed.

Return tracks cannot be resolved by name over OSC (``/live/track/*`` operate on
``song.tracks`` only; see ``KNOWN_LIMITATIONS.md``), so for v0.1 returns are only
created when the session started out blank; otherwise they are left untouched
with a warning. Sends therefore address returns by *index*, resolved from the
structure's return ordering.
"""

from __future__ import annotations

import argparse
import time

import ableton_bridge

from . import common, spec
from .live_session import LiveSession
from .models import StructureSpec, TrackSpec, TrackType
from .report import Report

#: The subcommand name, as it appears on the ``sc-produce`` CLI.
NAME = "scaffold"

#: One-line help shown in the ``sc-produce`` subcommand listing.
HELP = "Build the Live skeleton (tracks/scenes/sends) from a structure spec"


def scaffold_project(
    structure: StructureSpec,
    session: LiveSession,
    *,
    settle: float = 0.0,
    dry_run: bool = False,
) -> Report:
    """Materialise ``structure`` into ``session`` idempotently and report on it.

    Sets tempo/time signature, creates any missing tracks (with the correct
    MIDI/audio type), return tracks and scenes, and wires sends. Existing tracks
    and scenes are skipped; an existing track whose type disagrees with the spec
    is flagged as an error. Per-item failures (e.g. an unknown return, a
    missing source track for a send) are recorded as findings rather than
    raised, so a single bad row never aborts the whole scaffold.

    Args:
        structure: The Live skeleton to build.
        session: A connected (or faked) :class:`LiveSession` to build it in.
        settle: Seconds to pause after issuing create operations before naming
            and verifying, giving Live time to apply the (unacknowledged)
            writes. ``0`` (the default) skips the pauses.
        dry_run: If ``True``, no write is sent to Live; instead each intended
            action is recorded as an ``info`` "would ..." finding so the plan
            can be inspected safely.

    Returns:
        A :class:`Report` describing every action taken (or planned) and any
        problems found. ``report.passed`` is ``False`` if any error was recorded.
    """
    report = Report("Scaffold")
    _scaffold_transport(structure, session, report, dry_run=dry_run)
    created = _scaffold_tracks(structure, session, report, settle=settle, dry_run=dry_run)
    _scaffold_returns(structure, session, report, blank=created.blank, dry_run=dry_run)
    _scaffold_scenes(structure, session, report, settle=settle, dry_run=dry_run)
    _scaffold_sends(structure, session, report, dry_run=dry_run)
    return report


class _TrackOutcome:
    """Internal carrier for the result of the track-creation phase.

    Attributes:
        blank: Whether the session held zero regular tracks before scaffolding;
            used to decide whether return tracks may be created safely.
    """

    def __init__(self, *, blank: bool) -> None:
        self.blank = blank


def _scaffold_transport(
    structure: StructureSpec,
    session: LiveSession,
    report: Report,
    *,
    dry_run: bool,
) -> None:
    """Set the song tempo and time signature (or plan to, when ``dry_run``)."""
    num, den = structure.time_signature
    if dry_run:
        report.info(f"would set tempo to {structure.bpm:g} BPM")
        report.info(f"would set time signature to {num}/{den}")
        return
    session.bridge.set_tempo(structure.bpm)
    report.ok(f"tempo set to {structure.bpm:g} BPM")
    session.bridge.set_time_signature(num, den)
    report.ok(f"time signature set to {num}/{den}")


def _expected_midi_input(track: TrackSpec) -> bool:
    """Return whether ``track`` should report MIDI input (MIDI tracks do)."""
    return track.type is TrackType.MIDI


def _scaffold_tracks(
    structure: StructureSpec,
    session: LiveSession,
    report: Report,
    *,
    settle: float,
    dry_run: bool,
) -> _TrackOutcome:
    """Create any missing regular tracks with the correct type, then verify.

    Existing tracks are skipped (and type-checked against the spec); missing
    tracks are created with :meth:`LiveSession.create_midi_track` or
    ``create_audio_track`` per :attr:`TrackSpec.type`. A ``return`` track listed
    in :attr:`StructureSpec.tracks` is a spec mistake and is warned-and-skipped.

    Args:
        structure: The structure being scaffolded.
        session: The session to build in.
        report: The report to append findings to.
        settle: Seconds to pause after creating and after naming.
        dry_run: If ``True``, plan only -- issue no writes.

    Returns:
        A :class:`_TrackOutcome` recording whether the session was blank.
    """
    existing = session.bridge.get_track_names()
    blank = len(existing) == 0
    # (target_index, name) for each track we (would) create, in creation order.
    planned: list[tuple[int, str]] = []
    creates_so_far = 0

    for track in structure.tracks:
        if track.type is TrackType.RETURN:
            report.warn(
                "return track declared under 'tracks'; skipped "
                "(declare it under 'returns' instead)",
                track=track.name,
            )
            continue

        if track.name in existing:
            report.ok("track exists, skipped", track=track.name)
            _check_existing_track_type(session, report, track)
            continue

        index = len(existing) + creates_so_far
        creates_so_far += 1
        planned.append((index, track.name))
        kind = "MIDI" if track.type is TrackType.MIDI else "audio"
        if dry_run:
            report.info(f"would create {kind} track at index {index}", track=track.name)
            continue
        if track.type is TrackType.MIDI:
            session.create_midi_track()
        else:
            session.create_audio_track()
        report.info(f"created {kind} track at index {index}", track=track.name)

    if dry_run or not planned:
        return _TrackOutcome(blank=blank)

    # Writes are fire-and-forget: let Live settle, then name, settle, verify.
    _sleep(settle)
    for index, name in planned:
        session.set_track_name(index, name)
    _sleep(settle)

    names = session.bridge.get_track_names()
    for index, name in planned:
        actual = names[index] if 0 <= index < len(names) else None
        if actual == name:
            report.ok("track created", track=name, index=index)
        else:
            report.error(
                f"track create not verified at index {index} "
                f"(found {actual!r}, expected {name!r})",
                track=name,
                index=index,
            )
    return _TrackOutcome(blank=blank)


def _check_existing_track_type(
    session: LiveSession,
    report: Report,
    track: TrackSpec,
) -> None:
    """Error if an existing track's actual type disagrees with the spec.

    This is the headline check: a track authored for MIDI that exists in the set
    as audio (or vice versa) means clips would land silently in the wrong place.
    The track's index is resolved by name so its ``has_midi_input`` flag can be
    read back.

    Args:
        session: The session holding the track.
        report: The report to append the error to.
        track: The spec for the track being checked.
    """
    try:
        index = session.bridge.get_track_index(track.name)
        actual_midi = session.bridge.track_has_midi_input(index)
    except ableton_bridge.TrackNotFoundError:  # pragma: no cover - guarded by membership check
        return
    expected_midi = _expected_midi_input(track)
    if actual_midi != expected_midi:
        spec_kind = "MIDI" if expected_midi else "audio"
        actual_kind = "MIDI" if actual_midi else "audio"
        report.error(
            f"track built as the wrong type: spec says {spec_kind} but the existing "
            f"track is {actual_kind}",
            track=track.name,
            index=index,
        )


def _scaffold_returns(
    structure: StructureSpec,
    session: LiveSession,
    report: Report,
    *,
    blank: bool,
    dry_run: bool,
) -> None:
    """Create return tracks, but only when the session started out blank.

    Return tracks are not name-resolvable over OSC, so they cannot be matched to
    spec entries on a populated set. v0.1 therefore only creates them on a fresh
    session; on a populated one it leaves them untouched and warns that they
    could not be verified. Sends address returns by index, so the created
    returns need no names.

    Args:
        structure: The structure whose returns to create.
        session: The session to create them in.
        report: The report to append findings to.
        blank: Whether the session held zero regular tracks before scaffolding.
        dry_run: If ``True``, plan only -- issue no writes.
    """
    if not structure.returns:
        return
    count = len(structure.returns)
    names = [r.name for r in structure.returns]

    if not blank:
        report.warn(
            f"{count} return(s) in the spec left untouched: returns are not "
            "name-resolvable over OSC, so they cannot be verified on a non-blank "
            f"session ({', '.join(names)})"
        )
        return

    if dry_run:
        report.info(f"would create {count} return track(s): {', '.join(names)}")
        return

    for name in names:
        session.create_return_track()
        report.ok(f"return track created (addressed by send index): {name}", track=name)


def _scaffold_scenes(
    structure: StructureSpec,
    session: LiveSession,
    report: Report,
    *,
    settle: float,
    dry_run: bool,
) -> None:
    """Create any missing scenes by name, then verify by reading names back.

    Args:
        structure: The structure whose scenes to create.
        session: The session to create them in.
        report: The report to append findings to.
        settle: Seconds to pause after creating and after naming.
        dry_run: If ``True``, plan only -- issue no writes.
    """
    existing = session.bridge.get_scene_names()
    planned: list[tuple[int, str]] = []
    creates_so_far = 0

    for scene_spec in structure.scenes:
        name = scene_spec.name
        if name in existing:
            report.ok("scene exists, skipped", scene=name)
            continue
        index = len(existing) + creates_so_far
        creates_so_far += 1
        planned.append((index, name))
        if dry_run:
            report.info(f"would create scene at index {index}", scene=name)
            continue
        session.create_scene()
        report.info(f"created scene at index {index}", scene=name)

    if dry_run or not planned:
        return

    _sleep(settle)
    for index, name in planned:
        session.set_scene_name(index, name)
    _sleep(settle)

    names = session.bridge.get_scene_names()
    for index, name in planned:
        actual = names[index] if 0 <= index < len(names) else None
        if actual == name:
            report.ok("scene created", scene=name, index=index)
        else:
            report.error(
                f"scene create not verified at index {index} "
                f"(found {actual!r}, expected {name!r})",
                scene=name,
                index=index,
            )


def _scaffold_sends(
    structure: StructureSpec,
    session: LiveSession,
    report: Report,
    *,
    dry_run: bool,
) -> None:
    """Wire each send from its source track to a return, addressed by index.

    The source track is resolved by name (an unknown source is an error); the
    destination return is resolved to a send index via
    :meth:`StructureSpec.send_index` (an unknown return is an error). On success
    the level is written and read back, warning if the read-back differs.

    Args:
        structure: The structure whose sends to wire.
        session: The session to wire them in.
        report: The report to append findings to.
        dry_run: If ``True``, plan only -- issue no writes.
    """
    for send in structure.sends:
        send_index = structure.send_index(send.to)
        if send_index is None:
            report.error(
                f"send references unknown return {send.to!r}",
                track=send.from_,
            )
            continue

        if dry_run:
            report.info(
                f"would set send {send_index} ({send.to}) to {send.level:g}",
                track=send.from_,
            )
            continue

        try:
            track_index = session.bridge.get_track_index(send.from_)
        except ableton_bridge.TrackNotFoundError:
            report.error(
                f"send source track {send.from_!r} not found",
                track=send.from_,
            )
            continue

        session.bridge.set_send(track_index, send_index, send.level)
        actual = session.bridge.get_send(track_index, send_index)
        message = f"send {send_index} ({send.to}) set to {actual:g}"
        if abs(actual - send.level) > 1e-6:
            report.warn(
                f"send {send_index} ({send.to}) read back {actual:g}, expected {send.level:g}",
                track=send.from_,
            )
        else:
            report.ok(message, track=send.from_)


def _sleep(settle: float) -> None:
    """Pause for ``settle`` seconds when positive (a no-op otherwise)."""
    if settle > 0:
        time.sleep(settle)


# ---------------------------------------------------------------------------- #
# CLI wiring
# ---------------------------------------------------------------------------- #
def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the ``scaffold`` subcommand's argument parser.

    Args:
        parser: The subparser to populate.
    """
    parser.add_argument("structure", help="path to the structure spec YAML")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="plan the scaffold without sending any writes to Live",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.2,
        help="seconds to wait after create ops for Live to settle",
    )
    common.add_connection_args(parser)
    common.add_output_args(parser)


def run(args: argparse.Namespace) -> int:
    """Execute the ``scaffold`` subcommand.

    Loads and validates the structure spec, connects to Live, scaffolds the
    project, prints the report and returns a process exit code.

    Args:
        args: Parsed CLI arguments (as configured by :func:`configure_parser`).

    Returns:
        ``0`` if the scaffold reported no errors, ``1`` otherwise (or on a load
        or connection failure).
    """
    try:
        structure = spec.load_structure(args.structure)
    except spec.SpecError as exc:
        return common.fail(str(exc))

    # The timeout may surface during connect() or on the first read inside
    # scaffold_project(), so the whole exchange is guarded, not just connect().
    try:
        with common.connect(args) as session:
            report = scaffold_project(structure, session, settle=args.settle, dry_run=args.dry_run)
    except ableton_bridge.OSCTimeoutError:
        return common.fail("could not reach Ableton Live (is it running with AbletonOSC enabled?)")

    common.emit_report(report, args)
    return 0 if report.passed else 1
