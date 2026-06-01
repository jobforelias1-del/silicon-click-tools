"""Tests for the error hierarchy."""

from __future__ import annotations

from sc_produce.errors import (
    AuditFailedError,
    ComposeError,
    MistralAPIError,
    SCError,
    SpecError,
)
from sc_produce.report import Report


def test_hierarchy():
    assert issubclass(SpecError, SCError)
    assert issubclass(ComposeError, SCError)
    assert issubclass(MistralAPIError, ComposeError)
    assert issubclass(AuditFailedError, SCError)


def test_audit_failed_carries_report():
    report = Report("Audit")
    report.error("boom")
    exc = AuditFailedError("audit failed", report=report)
    assert exc.report is report
    assert str(exc) == "audit failed"


def test_audit_failed_defaults_report_to_none():
    exc = AuditFailedError("nope")
    assert exc.report is None


def test_errors_are_catchable_as_scerror():
    for exc in (SpecError("a"), ComposeError("b"), MistralAPIError("c"), AuditFailedError("d")):
        try:
            raise exc
        except SCError as caught:
            assert caught is exc
