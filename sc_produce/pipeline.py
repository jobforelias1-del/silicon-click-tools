"""The ``pipeline`` command: audit -> scaffold -> apply in one shot.

This is the one-command path for materialising a track: it audits the arrangement
(and *gates* on the result), scaffolds the skeleton with correct track types, then
applies the MIDI cell by cell. Like ``apply`` it can instead emit a self-contained
launcher when Live is not reachable.
"""

from __future__ import annotations

import argparse
import os

from ableton_bridge import OSCTimeoutError

from . import common
from .apply import apply_project
from .audit import audit_project
from .errors import SpecError
from .launcher import generate_launcher, write_launcher
from .live_session import LiveSession
from .models import ArrangementSpec, StructureSpec
from .report import Report
from .scaffold import scaffold_project
from .spec import load_arrangement, load_structure

NAME = "pipeline"
HELP = "One command end-to-end: audit, then scaffold (correct types), then apply"


def _audit_blocks(report: Report, *, strict: bool) -> bool:
    """Return whether an audit report should block scaffold/apply."""
    return (not report.passed) or (strict and report.warning_count > 0)


def run_pipeline(
    structure: StructureSpec,
    arrangement: ArrangementSpec,
    session: LiveSession,
    *,
    strict: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> Report:
    """Audit, scaffold and apply a project against a live session.

    The arrangement is audited first. If the audit finds blocking problems
    (errors, or -- under ``strict`` -- warnings) and ``force`` is not set, the
    pipeline halts before touching Live. Otherwise it scaffolds the skeleton and
    applies the arrangement.

    Args:
        structure: The structure spec to scaffold.
        arrangement: The arrangement spec to audit and apply.
        session: The live session to drive.
        strict: Treat audit warnings as blocking.
        force: Proceed even when the audit is blocking.
        dry_run: Plan scaffold/apply without writing to Live.

    Returns:
        A combined :class:`~sc_produce.report.Report` across all phases.
    """
    report = Report("Pipeline")

    report.info("phase: audit")
    audit_report = audit_project(arrangement, structure, middle_c_octave=session.middle_c_octave)
    report.extend(audit_report)

    if _audit_blocks(audit_report, strict=strict) and not force:
        report.error(
            "halted before scaffold/apply: audit found blocking problems "
            "(pass --force to proceed anyway)"
        )
        return report

    report.info("phase: scaffold")
    report.extend(scaffold_project(structure, session, dry_run=dry_run))

    report.info("phase: apply")
    report.extend(apply_project(structure, arrangement, session, dry_run=dry_run))

    return report


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the ``pipeline`` arguments to a subparser.

    Args:
        parser: The subparser to configure.
    """
    parser.add_argument("structure", help="Path to the structure spec YAML")
    parser.add_argument("arrangement", help="Path to the arrangement spec YAML")
    parser.add_argument(
        "--launcher",
        help="Instead of applying, write a self-contained launcher script to this path",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan without writing to Live")
    parser.add_argument("--strict", action="store_true", help="Treat audit warnings as blocking")
    parser.add_argument(
        "--force", action="store_true", help="Scaffold/apply even if the audit is blocking"
    )
    common.add_connection_args(parser)
    common.add_output_args(parser)


def run(args: argparse.Namespace) -> int:
    """Execute the ``pipeline`` command.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Process exit code (0 on success).
    """
    try:
        structure = load_structure(args.structure)
        arrangement = load_arrangement(args.arrangement)
    except SpecError as exc:
        return common.fail(str(exc))

    audit_report = audit_project(arrangement, structure, middle_c_octave=args.middle_c_octave)
    blocked = _audit_blocks(audit_report, strict=args.strict) and not args.force

    if args.launcher:
        common.emit_report(audit_report, args)
        if blocked:
            return common.fail("audit found blocking problems; pass --force to emit anyway")
        source = generate_launcher(
            structure,
            arrangement,
            do_scaffold=True,
            do_apply=True,
            middle_c_octave=args.middle_c_octave,
            filename=os.path.basename(args.launcher),
        )
        write_launcher(args.launcher, source)
        print(f"Wrote launcher to {args.launcher} (run it against your open Live set).")
        return 0

    if blocked:
        common.emit_report(audit_report, args)
        return common.fail("audit found blocking problems; pass --force to proceed anyway")

    try:
        with common.connect(args) as session:
            report = run_pipeline(
                structure,
                arrangement,
                session,
                strict=args.strict,
                force=args.force,
                dry_run=args.dry_run,
            )
    except OSCTimeoutError as exc:
        return common.fail(f"could not reach Ableton Live: {exc}")

    common.emit_report(report, args, show_ok=False)
    return 0 if report.passed else 1
