"""Apply an audited arrangement into a running Ableton Live set, cell by cell.

``sc-produce apply`` is the final executor of the pipeline: it takes a
:class:`~sc_produce.models.StructureSpec` (the skeleton, the single source of
truth for scene and track positions) and an
:class:`~sc_produce.models.ArrangementSpec` (the authored MIDI content) and writes
each populated ``scene -> track`` cell into Live.

The clip slot index of a ``(scene, track)`` cell is the scene's index in the
structure -- the arrangement deliberately does not carry slot indices (see
:mod:`sc_produce.models`).

Two properties matter most and shape this module:

* **Correct track type.** MIDI must never be written to an audio track. Audio and
  return cells are rejected up front with a clear error, and -- because the bridge
  is the real authority on a track's MIDI capability -- every bridge call is also
  wrapped so a :class:`~ableton_bridge.AudioTrackCannotHoldMidiError` surfaced
  from inside Live becomes a clean per-cell error rather than an abort.
* **Convergence to the desired state.** Re-applying must be safe and must make the
  clip match the spec exactly, not merely append. Each cell is therefore
  *reconciled*: notes absent from the spec are removed, notes whose key matches
  but whose attributes differ are modified, and genuinely new notes are added --
  in the order remove -> modify -> add -- and the result is read back and
  compared.

A single bad cell (unknown scene/track, wrong type, bridge error, invalid pitch)
is recorded as a finding and never aborts the rest of the apply.
"""

from __future__ import annotations

import argparse
import os

from ableton_bridge import (
    AbletonBridgeError,
    AudioTrackCannotHoldMidiError,
    Note,
    OSCTimeoutError,
)

from . import common, spec
from .launcher import generate_launcher, write_launcher
from .live_session import LiveSession
from .midi import note_spec_to_note
from .models import ArrangementSpec, ClipSpec, StructureSpec, TrackType
from .report import Report

#: The subcommand name, as it appears on the ``sc-produce`` CLI.
NAME = "apply"

#: One-line help shown in the ``sc-produce`` subcommand listing.
HELP = "Apply an audited arrangement into the open Live set, cell by cell"

#: Default clip length in beats, used when a cell does not specify one.
DEFAULT_CLIP_LENGTH = 4.0


def apply_project(
    structure: StructureSpec,
    arrangement: ArrangementSpec,
    session: LiveSession,
    *,
    dry_run: bool = False,
) -> Report:
    """Apply ``arrangement`` into ``session`` cell by cell, against ``structure``.

    For every populated ``(scene, track)`` cell in ``arrangement``, resolves the
    clip slot index from the scene's position in ``structure``, validates that the
    target track is a MIDI track, builds the desired notes, and reconciles the
    clip to that desired final state (remove -> modify -> add) before reading it
    back to confirm. Each step that can fail is reported as a finding rather than
    raised, so one bad cell never aborts the whole apply.

    Args:
        structure: The Live skeleton, used to resolve scene and track positions
            and types. This is the authority for clip slot indices.
        arrangement: The authored MIDI content to write.
        session: A connected (or faked) :class:`LiveSession` to write into.
        dry_run: If ``True``, no write is sent to Live; instead each cell records
            an ``info`` "would write ..." finding so the plan can be inspected.

    Returns:
        A :class:`Report` titled ``"Apply"`` describing every cell. ``passed`` is
        ``False`` if any error-severity finding was recorded.
    """
    report = Report("Apply")
    octave = session.middle_c_octave
    for scene, track, clip in arrangement.iter_cells():
        _apply_cell(structure, session, report, scene, track, clip, octave, dry_run=dry_run)
    return report


def _apply_cell(
    structure: StructureSpec,
    session: LiveSession,
    report: Report,
    scene: str,
    track: str,
    clip: ClipSpec,
    middle_c_octave: int,
    *,
    dry_run: bool,
) -> None:
    """Resolve, validate, and reconcile a single ``(scene, track)`` cell.

    Args:
        structure: The structure used to resolve the scene index and track type.
        session: The session to write into.
        report: The report to append findings to.
        scene: The scene name of the cell.
        track: The track name of the cell.
        clip: The desired clip contents.
        middle_c_octave: Octave convention for resolving note names.
        dry_run: If ``True``, plan only -- issue no reads or writes.
    """
    scene_idx = structure.scene_index(scene)
    if scene_idx is None:
        report.error(f"unknown scene {scene}", scene=scene, track=track)
        return

    ts = structure.track(track)
    if ts is None:
        report.error(f"unknown track {track}", scene=scene, track=track)
        return
    if ts.type is TrackType.AUDIO:
        # An audio cell carries cues, not MIDI. The bridge has no sample-load API
        # over OSC, so cues are recorded for the by-hand/later materialisation step
        # rather than written. MIDI authored onto an audio track is still an error.
        if clip.notes:
            report.error(f"audio track {track} cannot hold MIDI", scene=scene, track=track)
        else:
            report.info(
                f"{len(clip.cues)} audio cue(s) for {track}/{scene} "
                f"(clip {scene_idx}) -- not written (no OSC sample-load); "
                f"materialise by hand",
                scene=scene,
                track=track,
            )
        return
    if ts.type is TrackType.RETURN:
        report.error("return track cannot hold clips", scene=scene, track=track)
        return

    desired = _build_desired_notes(report, scene, track, clip, middle_c_octave)

    if dry_run:
        report.info(
            f"would write {len(desired)} note(s) to {track}/{scene} (clip {scene_idx})",
            scene=scene,
            track=track,
        )
        return

    _reconcile_cell(session, report, scene, track, scene_idx, clip, desired)


def _build_desired_notes(
    report: Report,
    scene: str,
    track: str,
    clip: ClipSpec,
    middle_c_octave: int,
) -> list[Note]:
    """Convert a cell's :class:`NoteSpec` list to bridge notes, robustly.

    A note whose pitch cannot be resolved (e.g. out of the 0--127 MIDI range, or
    an unparseable name) is reported as an error keyed to its index and skipped;
    the remaining notes are still returned so the rest of the cell applies.

    Args:
        report: The report to append per-note errors to.
        scene: The cell's scene name (for finding location).
        track: The cell's track name (for finding location).
        clip: The clip whose notes to convert.
        middle_c_octave: Octave convention for resolving note names.

    Returns:
        The successfully converted notes, in spec order.
    """
    desired: list[Note] = []
    for i, note_spec in enumerate(clip.notes):
        try:
            desired.append(note_spec_to_note(note_spec, middle_c_octave))
        except ValueError as exc:
            report.error(f"invalid pitch: {exc}", scene=scene, track=track, index=i)
    return desired


def _reconcile_cell(
    session: LiveSession,
    report: Report,
    scene: str,
    track: str,
    scene_idx: int,
    clip: ClipSpec,
    desired: list[Note],
) -> None:
    """Make the clip at ``(track, scene_idx)`` match ``desired`` exactly.

    Creates the clip idempotently, diffs the existing notes against the desired
    set by their ``(pitch, start)`` key, then applies removals, modifications and
    additions -- in that order, each only when non-empty -- and reads the clip
    back to confirm convergence. Bridge failures (including an audio-track refusal
    surfaced from inside Live) are translated into per-cell error findings.

    Args:
        session: The session whose bridge performs the writes.
        report: The report to append findings to.
        scene: The cell's scene name (for finding location).
        track: The cell's track name (for finding location).
        scene_idx: The clip slot index (the scene's position in the structure).
        clip: The desired clip contents (used for its length).
        desired: The desired notes, already converted to bridge notes.
    """
    bridge = session.bridge
    length = clip.length if clip.length is not None else DEFAULT_CLIP_LENGTH
    try:
        bridge.create_clip(track, scene_idx, length)

        existing = bridge.get_notes(track, scene_idx)
        existing_by_key = {n.key(): n for n in existing}
        desired_by_key = {n.key(): n for n in desired}

        to_remove = [k for k in existing_by_key if k not in desired_by_key]
        to_modify = [
            (k, desired_by_key[k])
            for k in desired_by_key
            if k in existing_by_key and desired_by_key[k] != existing_by_key[k]
        ]
        to_add = [desired_by_key[k] for k in desired_by_key if k not in existing_by_key]

        if to_remove:
            bridge.remove_notes(track, scene_idx, to_remove)
        if to_modify:
            bridge.modify_notes(track, scene_idx, to_modify)
        if to_add:
            bridge.add_notes(track, scene_idx, to_add)

        final = bridge.get_notes(track, scene_idx)
        final_keys = {n.key() for n in final}
        desired_keys = set(desired_by_key)
        if final_keys == desired_keys:
            report.ok(
                f"cell applied (+{len(to_add)} ~{len(to_modify)} -{len(to_remove)})",
                scene=scene,
                track=track,
            )
        else:
            report.warn(
                f"post-apply mismatch (expected {len(desired_keys)} got {len(final_keys)})",
                scene=scene,
                track=track,
            )
    except AudioTrackCannotHoldMidiError:
        report.error(
            f"audio track {track} cannot hold MIDI (caught from bridge)",
            scene=scene,
            track=track,
        )
    except AbletonBridgeError as exc:
        report.error(f"bridge error: {exc}", scene=scene, track=track)


# ---------------------------------------------------------------------------- #
# CLI wiring
# ---------------------------------------------------------------------------- #
def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the ``apply`` subcommand's argument parser.

    Args:
        parser: The subparser to populate.
    """
    parser.add_argument("arrangement", help="path to the arrangement spec YAML")
    parser.add_argument(
        "--structure",
        required=True,
        help="path to the structure spec YAML (the authority for scene/track positions)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="plan the apply without sending any writes to Live",
    )
    parser.add_argument(
        "--launcher",
        help="instead of applying, write a self-contained launcher script here",
    )
    common.add_connection_args(parser)
    common.add_output_args(parser)


def run(args: argparse.Namespace) -> int:
    """Execute the ``apply`` subcommand.

    Loads and validates both specs. With ``--launcher`` it writes a self-contained
    launcher script (which embeds the specs and applies them locally) and returns
    without connecting to Live. Otherwise it connects, applies the arrangement,
    prints the report and returns a process exit code.

    Args:
        args: Parsed CLI arguments (as configured by :func:`configure_parser`).

    Returns:
        ``0`` on success (or after writing a launcher), ``1`` if the apply
        reported errors or a load/connection failure occurred.
    """
    try:
        arrangement = spec.load_arrangement(args.arrangement)
        structure = spec.load_structure(args.structure)
    except spec.SpecError as exc:
        return common.fail(str(exc))

    if args.launcher:
        src = generate_launcher(
            structure,
            arrangement,
            do_scaffold=False,
            do_apply=True,
            middle_c_octave=args.middle_c_octave,
            filename=os.path.basename(args.launcher),
        )
        write_launcher(args.launcher, src)
        print(f"wrote launcher to {args.launcher}")
        return 0

    # The timeout may surface during connect() or on the first read inside
    # apply_project(), so the whole exchange is guarded, not just connect().
    try:
        with common.connect(args) as session:
            report = apply_project(structure, arrangement, session, dry_run=args.dry_run)
    except OSCTimeoutError:
        return common.fail("could not reach Ableton Live (is it running with AbletonOSC enabled?)")

    common.emit_report(report, args)
    return 0 if report.passed else 1
