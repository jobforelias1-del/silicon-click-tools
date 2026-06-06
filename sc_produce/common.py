"""Shared CLI plumbing: connection arguments, connecting, and output.

Subcommand modules use these helpers so flags stay consistent across the whole
``sc-produce`` surface (``--host``, ``--json``, and so on) and so there is one
place that turns parsed args into a :class:`~sc_produce.live_session.LiveSession`.
"""

from __future__ import annotations

import argparse
import json
import sys

from ableton_bridge import DEFAULT_MIDDLE_C_OCTAVE
from ableton_bridge.osc_client import (
    DEFAULT_HOST,
    DEFAULT_RECEIVE_PORT,
    DEFAULT_SEND_PORT,
    DEFAULT_TIMEOUT,
)

from .live_session import LiveSession
from .report import Report


def add_connection_args(parser: argparse.ArgumentParser) -> None:
    """Add the AbletonOSC connection flags to a subparser.

    Args:
        parser: The subparser to extend.
    """
    group = parser.add_argument_group("connection")
    group.add_argument("--host", default=DEFAULT_HOST, help="AbletonOSC host (default 127.0.0.1)")
    group.add_argument(
        "--send-port",
        type=int,
        default=DEFAULT_SEND_PORT,
        help="UDP port AbletonOSC listens on (default 11000)",
    )
    group.add_argument(
        "--receive-port",
        type=int,
        default=DEFAULT_RECEIVE_PORT,
        help="UDP port AbletonOSC replies to (default 11001)",
    )
    group.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Seconds to wait for an OSC reply (default 5.0)",
    )
    group.add_argument(
        "--middle-c-octave",
        type=int,
        default=DEFAULT_MIDDLE_C_OCTAVE,
        help="Octave number for middle C in note names (3 = Ableton, 4 = SPN)",
    )


def add_output_args(parser: argparse.ArgumentParser) -> None:
    """Add output-format flags (``--json``) to a subparser.

    Args:
        parser: The subparser to extend.
    """
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON instead of text"
    )


def connect(args: argparse.Namespace) -> LiveSession:
    """Build a :class:`LiveSession` from parsed connection args.

    Args:
        args: A namespace carrying ``host``/``send_port``/``receive_port``/
            ``timeout``/``middle_c_octave`` (as added by
            :func:`add_connection_args`).

    Returns:
        A connected (socket-bound) live session.
    """
    return LiveSession(
        host=args.host,
        send_port=args.send_port,
        receive_port=args.receive_port,
        timeout=args.timeout,
        middle_c_octave=args.middle_c_octave,
    )


def emit_report(report: Report, args: argparse.Namespace, *, show_ok: bool = True) -> None:
    """Print a report as JSON or text, honouring ``args.json``.

    Args:
        report: The report to print.
        args: Parsed args; ``json`` selects the format when present and truthy.
        show_ok: Whether to include OK lines in text output.
    """
    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.render(show_ok=show_ok))


def fail(message: str) -> int:
    """Print an error to stderr and return the standard failure exit code.

    Args:
        message: The error message.

    Returns:
        ``1``, for convenient ``return fail(...)`` use in command handlers.
    """
    print(f"error: {message}", file=sys.stderr)
    return 1
