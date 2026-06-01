"""A small, shared reporting layer for audit / scaffold / apply.

Every command that inspects or mutates a project produces a :class:`Report`: an
ordered list of :class:`Finding` objects, each with a severity and an optional
``scene``/``track``/``index`` location. Reports render to readable text (for the
terminal) or to a plain dict (for ``--json``), and they know whether they
"passed" (no error-severity findings).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """The severity of a single finding."""

    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


#: Glyphs used when rendering findings to the terminal.
_GLYPHS = {
    Severity.OK: "✓",  # check mark
    Severity.INFO: "•",  # bullet
    Severity.WARNING: "!",
    Severity.ERROR: "✗",  # ballot x
}


@dataclass
class Finding:
    """A single observation about a project.

    Attributes:
        severity: How serious the finding is.
        message: A human-readable description.
        scene: Optional scene name the finding relates to.
        track: Optional track name the finding relates to.
        index: Optional note index within a cell.
    """

    severity: Severity
    message: str
    scene: str | None = None
    track: str | None = None
    index: int | None = None

    def location(self) -> str:
        """Return a compact ``scene/track[note N]`` location string (or empty)."""
        parts: list[str] = []
        if self.scene is not None:
            parts.append(self.scene)
        if self.track is not None:
            parts.append(self.track)
        loc = "/".join(parts)
        if self.index is not None:
            loc = f"{loc} note {self.index}" if loc else f"note {self.index}"
        return loc

    def render(self) -> str:
        """Render the finding as a single ``glyph [location] message`` line."""
        glyph = _GLYPHS[self.severity]
        loc = self.location()
        prefix = f"{glyph} "
        if loc:
            return f"{prefix}[{loc}] {self.message}"
        return f"{prefix}{self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable mapping for this finding."""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "scene": self.scene,
            "track": self.track,
            "index": self.index,
        }


@dataclass
class Report:
    """An ordered collection of findings for one command run.

    Attributes:
        title: A short label for the report (e.g. ``"Audit"``).
        findings: The findings, in the order they were recorded.
    """

    title: str
    findings: list[Finding] = field(default_factory=list)

    def add(
        self,
        severity: Severity,
        message: str,
        *,
        scene: str | None = None,
        track: str | None = None,
        index: int | None = None,
    ) -> Finding:
        """Append a finding and return it.

        Args:
            severity: The finding's severity.
            message: The finding message.
            scene: Optional scene name.
            track: Optional track name.
            index: Optional note index.

        Returns:
            The created :class:`Finding`.
        """
        finding = Finding(severity, message, scene=scene, track=track, index=index)
        self.findings.append(finding)
        return finding

    def ok(self, message: str, **loc: Any) -> Finding:
        """Add an OK-severity finding."""
        return self.add(Severity.OK, message, **loc)

    def info(self, message: str, **loc: Any) -> Finding:
        """Add an INFO-severity finding."""
        return self.add(Severity.INFO, message, **loc)

    def warn(self, message: str, **loc: Any) -> Finding:
        """Add a WARNING-severity finding."""
        return self.add(Severity.WARNING, message, **loc)

    def error(self, message: str, **loc: Any) -> Finding:
        """Add an ERROR-severity finding."""
        return self.add(Severity.ERROR, message, **loc)

    def extend(self, other: Report) -> None:
        """Append all findings from ``other`` into this report."""
        self.findings.extend(other.findings)

    def count(self, severity: Severity) -> int:
        """Return the number of findings of a given severity."""
        return sum(1 for f in self.findings if f.severity is severity)

    @property
    def error_count(self) -> int:
        """The number of error-severity findings."""
        return self.count(Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """The number of warning-severity findings."""
        return self.count(Severity.WARNING)

    @property
    def passed(self) -> bool:
        """Whether the report is free of error-severity findings."""
        return self.error_count == 0

    def summary(self) -> str:
        """Return a one-line ``N ok, N warnings, N errors`` summary."""
        return (
            f"{self.count(Severity.OK)} ok, "
            f"{self.warning_count} warning(s), "
            f"{self.error_count} error(s)"
        )

    def render(self, *, show_ok: bool = True) -> str:
        """Render the full report as text.

        Args:
            show_ok: If ``False``, OK-severity lines are omitted (useful for
                large applies where only problems matter).

        Returns:
            The rendered report.
        """
        lines = [f"== {self.title} =="]
        for finding in self.findings:
            if not show_ok and finding.severity is Severity.OK:
                continue
            lines.append(finding.render())
        lines.append(self.summary())
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable mapping for the whole report."""
        return {
            "title": self.title,
            "passed": self.passed,
            "summary": {
                "ok": self.count(Severity.OK),
                "warnings": self.warning_count,
                "errors": self.error_count,
            },
            "findings": [f.to_dict() for f in self.findings],
        }
