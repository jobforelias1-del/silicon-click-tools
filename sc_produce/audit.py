"""Audit a Mistral arrangement for value, type and completeness problems.

This is the "Claude audits" stage of the Silicon Click pipeline. It inspects an
:class:`~sc_produce.models.ArrangementSpec` (optionally cross-checked against a
:class:`~sc_produce.models.StructureSpec`) and produces a
:class:`~sc_produce.report.Report` describing every problem it can find *without*
touching Live -- the function is pure: no I/O and no network.

Three classes of problem are detected:

* **Value** problems in the authored notes themselves (the headline bug from the
  first manual run was a velocity above the MIDI maximum of 127).
* **Type / structure** problems found by cross-checking against the skeleton --
  most importantly MIDI authored for a track that was built as *audio* (the
  "7 tracks as audio" bug).
* **Completeness** problems: cells the skeleton expects that the arrangement
  never authored.

The CLI surface (:data:`NAME`, :data:`HELP`, :func:`configure_parser`,
:func:`run`) wires this into the ``sc-produce audit`` subcommand.
"""

from __future__ import annotations

import argparse

from . import common, spec
from .errors import SpecError
from .midi import resolve_pitch
from .models import ArrangementSpec, ClipSpec, StructureSpec
from .report import Report

#: Inclusive MIDI maximum for a velocity value.
_MAX_VELOCITY = 127

NAME = "audit"
HELP = "Audit a Mistral arrangement for value, type and completeness problems"


def _audit_cell_values(
    report: Report,
    scene: str,
    track: str,
    clip: ClipSpec,
    *,
    middle_c_octave: int,
) -> bool:
    """Run the value-level checks for a single cell, appending findings.

    Checks every note's velocity, pitch, duration and start, flags duplicate
    resolved ``(pitch, start)`` keys and a non-positive clip length, then records
    a single "cell ok" finding when the cell produced no value-level errors.

    Args:
        report: The report to append findings to.
        scene: The scene name of the cell (for finding locations).
        track: The track name of the cell (for finding locations).
        clip: The clip whose notes are checked.
        middle_c_octave: Octave assigned to middle C when resolving note names.

    Returns:
        ``True`` if the cell produced no value-level errors, else ``False``.
    """
    cell_ok = True
    seen_keys: set[tuple[int, float]] = set()

    for i, note in enumerate(clip.notes):
        loc = {"scene": scene, "track": track, "index": i}

        velocity = note.velocity
        if velocity > _MAX_VELOCITY:
            report.error(f"velocity {velocity} exceeds MIDI max 127", **loc)
            cell_ok = False
        elif velocity < 0:
            report.error(f"velocity {velocity} is below 0", **loc)
            cell_ok = False
        elif velocity == 0:
            report.warn("velocity 0 (silent note)", **loc)

        resolved_pitch: int | None = None
        try:
            resolved_pitch = resolve_pitch(note.pitch, middle_c_octave)
        except ValueError as exc:
            report.error(f"invalid pitch {note.pitch!r}: {exc}", **loc)
            cell_ok = False

        if note.duration <= 0:
            report.error("duration must be > 0", **loc)
            cell_ok = False
        if note.start < 0:
            report.error("start must be >= 0", **loc)
            cell_ok = False

        if resolved_pitch is not None:
            key = (resolved_pitch, float(note.start))
            if key in seen_keys:
                report.warn(
                    "duplicate note key (pitch,start) is ambiguous for modify/remove",
                    **loc,
                )
            else:
                seen_keys.add(key)

    if clip.length is not None and clip.length <= 0:
        report.warn(
            f"clip length {clip.length} must be > 0",
            scene=scene,
            track=track,
        )

    if cell_ok:
        report.ok(f"cell ok ({len(clip.notes)} notes)", scene=scene, track=track)
    return cell_ok


def _audit_cell_types(
    report: Report,
    scene: str,
    track: str,
    structure: StructureSpec,
) -> None:
    """Cross-check a single cell's track and scene against the skeleton.

    Args:
        report: The report to append findings to.
        scene: The scene name of the cell.
        track: The track name of the cell.
        structure: The skeleton to validate the cell against.
    """
    if structure.track(track) is None:
        if track in structure.return_order():
            report.error("return track cannot hold clips", scene=scene, track=track)
        else:
            report.error(f"unknown track {track}", scene=scene, track=track)
    elif structure.is_audio(track):
        report.error(
            f"audio track {track} cannot hold MIDI (built as audio but MIDI was authored)",
            scene=scene,
            track=track,
        )

    if structure.scene_index(scene) is None:
        report.error(f"unknown scene {scene}", scene=scene, track=track)


def _audit_completeness(
    report: Report, arrangement: ArrangementSpec, structure: StructureSpec
) -> None:
    """Warn about MIDI cells the skeleton expects but the arrangement omits.

    Args:
        report: The report to append findings to.
        arrangement: The authored arrangement.
        structure: The skeleton whose ``scenes`` x MIDI-tracks grid is expected.
    """
    for scene in structure.scenes:
        for track in structure.midi_track_names():
            if arrangement.cell(scene, track) is None:
                report.warn(
                    f"no clip authored for {track} in {scene} (incomplete grid)",
                    scene=scene,
                    track=track,
                )


def audit_project(
    arrangement: ArrangementSpec,
    structure: StructureSpec | None = None,
    *,
    middle_c_octave: int = 3,
) -> Report:
    """Audit an arrangement, optionally cross-checked against a structure.

    Pure function: it performs no I/O and opens no network connections. Every
    populated cell is checked for value problems; when a ``structure`` is given,
    each cell is also checked for type/scene problems and the full
    scene x MIDI-track grid is checked for completeness.

    Args:
        arrangement: The authored arrangement to audit.
        structure: The skeleton to cross-check track types, scenes and grid
            completeness against. When ``None``, only value checks run.
        middle_c_octave: Octave assigned to middle C (MIDI 60) when resolving
            scientific note names; 3 is Ableton's convention.

    Returns:
        A :class:`~sc_produce.report.Report` titled ``"Audit"`` describing every
        problem found.
    """
    report = Report("Audit")

    if structure is None:
        report.info("no structure provided; skipping type and completeness checks")

    for scene, track, clip in arrangement.iter_cells():
        _audit_cell_values(
            report,
            scene,
            track,
            clip,
            middle_c_octave=middle_c_octave,
        )
        if structure is not None:
            _audit_cell_types(report, scene, track, structure)

    if structure is not None:
        _audit_completeness(report, arrangement, structure)

    return report


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the ``audit`` subparser.

    Args:
        parser: The subparser to populate with audit arguments.
    """
    parser.add_argument("arrangement", help="arrangement spec (YAML) to audit")
    parser.add_argument(
        "--structure",
        help="structure spec to cross-check track types & completeness",
    )
    parser.add_argument(
        "-o",
        "--out",
        help="write the validated arrangement here if it passes",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as failures",
    )
    parser.add_argument(
        "--middle-c-octave",
        type=int,
        default=3,
        help="octave number for middle C in note names (3 = Ableton, 4 = SPN)",
    )
    common.add_output_args(parser)


def run(args: argparse.Namespace) -> int:
    """Execute the ``audit`` subcommand.

    Loads the arrangement (and optional structure), audits it, emits the report,
    optionally writes the validated arrangement out, and returns an exit code.
    Spec-loading failures (YAML or validation problems) are surfaced as a
    single-finding report so ``--json`` still works on the error path.

    Args:
        args: Parsed arguments carrying ``arrangement``, ``structure``, ``out``,
            ``strict``, ``middle_c_octave`` and the output flags.

    Returns:
        ``0`` on success; ``1`` if the arrangement could not be loaded, if the
        audit found errors, or if ``--strict`` and any warnings were found.
    """
    try:
        arrangement = spec.load_arrangement(args.arrangement)
    except SpecError as exc:
        report = Report("Audit")
        report.error(f"syntax error: {exc}")
        common.emit_report(report, args)
        return 1

    structure: StructureSpec | None = None
    if args.structure:
        try:
            structure = spec.load_structure(args.structure)
        except SpecError as exc:
            report = Report("Audit")
            report.error(f"syntax error: {exc}")
            common.emit_report(report, args)
            return 1

    report = audit_project(arrangement, structure, middle_c_octave=args.middle_c_octave)
    common.emit_report(report, args)

    if args.out and report.passed:
        spec.save_arrangement(arrangement, args.out)

    if not report.passed:
        return 1
    if args.strict and report.warning_count > 0:
        return 1
    return 0
