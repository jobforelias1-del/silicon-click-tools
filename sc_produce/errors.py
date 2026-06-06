"""Typed exception hierarchy for the Silicon Click production tools.

Every error raised by ``sc_produce`` derives from :class:`SCError`, so a caller
(or the CLI) can catch the whole family with a single ``except SCError`` while
still distinguishing individual failure modes when it matters.

Errors raised by the underlying Ableton bridge (``AbletonBridgeError`` and its
subclasses, e.g. :class:`ableton_bridge.AudioTrackCannotHoldMidiError`) are *not*
re-parented onto :class:`SCError`; the apply/scaffold flows catch them explicitly
and translate them into per-cell report entries.
"""

from __future__ import annotations


class SCError(Exception):
    """Base class for all errors raised by ``sc_produce``."""


class SpecError(SCError):
    """Raised when a structure or arrangement spec cannot be loaded or parsed.

    This wraps YAML syntax errors and pydantic validation errors so the CLI can
    present a single, readable message rather than a raw traceback.
    """


class AuditFailedError(SCError):
    """Raised when an audit finds blocking (error-severity) problems.

    Carries the offending :class:`~sc_produce.report.Report` so a caller can
    render the findings.
    """

    def __init__(self, message: str, report=None) -> None:
        """Store the message and the originating report.

        Args:
            message: A human-readable summary of why the audit failed.
            report: The :class:`~sc_produce.report.Report` that failed, if any.
        """
        super().__init__(message)
        self.report = report


class ComposeError(SCError):
    """Raised when brief generation or Mistral response capture fails."""


class MistralAPIError(ComposeError):
    """Raised when a direct Mistral API call fails or returns an error."""
