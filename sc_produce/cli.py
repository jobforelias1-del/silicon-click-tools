"""The ``sc-produce`` command-line entry point.

Each subcommand lives in its own module and exposes the same small contract --
``NAME``, ``HELP``, ``configure_parser(parser)`` and ``run(args) -> int`` -- so this
file is just wiring: it builds the top-level parser, registers every command, and
dispatches to the selected handler.
"""

from __future__ import annotations

import argparse

from . import __version__, apply, audit, compose, pipeline, scaffold

#: The command modules, in the order they appear in ``--help``.
_COMMANDS = [scaffold, compose, audit, apply, pipeline]


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with every subcommand registered.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="sc-produce",
        description=(
            "Silicon Click production pipeline: scaffold, compose, audit and apply "
            "Ableton Live arrangements."
        ),
    )
    parser.add_argument("--version", action="version", version=f"sc-produce {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True
    for module in _COMMANDS:
        sub = subparsers.add_parser(module.NAME, help=module.HELP, description=module.HELP)
        module.configure_parser(sub)
        sub.set_defaults(_handler=module.run)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The process exit code returned by the selected command.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "_handler", None)
    if handler is None:  # pragma: no cover - argparse 'required' guards this
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
