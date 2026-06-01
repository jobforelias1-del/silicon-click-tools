"""Silicon Click production tools: the SC pipeline as a CLI package.

``sc_produce`` consolidates the multi-agent music-production workflow Silicon Click
runs by hand -- Mistral authors, Claude audits, the bridge executes -- into one
tool with five subcommands: ``scaffold``, ``compose``, ``audit``, ``apply`` and
``pipeline``. See ``docs/`` for the pipeline doctrine and ``README.md`` for usage.

The public surface re-exports the spec models, the live session, and the report
types so embedding code (and generated launchers) can ``from sc_produce import ...``.
"""

from __future__ import annotations

from .live_session import LiveSession
from .models import (
    ArrangementSpec,
    ClipSpec,
    NoteSpec,
    SendSpec,
    StructureSpec,
    TrackSpec,
    TrackType,
)
from .report import Finding, Report, Severity

__version__ = "0.1.0"

__all__ = [
    "ArrangementSpec",
    "ClipSpec",
    "Finding",
    "LiveSession",
    "NoteSpec",
    "Report",
    "SendSpec",
    "Severity",
    "StructureSpec",
    "TrackSpec",
    "TrackType",
    "__version__",
]
