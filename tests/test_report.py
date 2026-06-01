"""Tests for the reporting layer."""

from __future__ import annotations

from sc_produce.report import Finding, Report, Severity


def test_finding_location_variants():
    assert Finding(Severity.OK, "m").location() == ""
    assert Finding(Severity.OK, "m", scene="Intro").location() == "Intro"
    assert Finding(Severity.OK, "m", scene="Intro", track="D_kick").location() == "Intro/D_kick"
    assert (
        Finding(Severity.ERROR, "m", scene="Intro", track="D_kick", index=3).location()
        == "Intro/D_kick note 3"
    )
    assert Finding(Severity.ERROR, "m", index=2).location() == "note 2"


def test_finding_render_includes_location_and_glyph():
    rendered = Finding(Severity.ERROR, "bad", scene="Intro", track="D_kick").render()
    assert "bad" in rendered
    assert "[Intro/D_kick]" in rendered
    # no-location findings still render
    assert "ok thing" in Finding(Severity.OK, "ok thing").render()


def test_finding_to_dict():
    d = Finding(Severity.WARNING, "w", scene="S", track="T", index=1).to_dict()
    assert d == {
        "severity": "warning",
        "message": "w",
        "scene": "S",
        "track": "T",
        "index": 1,
    }


def test_report_add_helpers_and_counts():
    report = Report("Test")
    report.ok("good")
    report.info("fyi")
    report.warn("careful")
    report.error("nope")
    report.error("also nope")
    assert report.count(Severity.OK) == 1
    assert report.warning_count == 1
    assert report.error_count == 2
    assert report.passed is False


def test_report_passes_when_no_errors():
    report = Report("Test")
    report.ok("good")
    report.warn("careful")
    assert report.passed is True


def test_report_summary_and_render():
    report = Report("Audit")
    report.ok("cell ok")
    report.error("velocity 130 exceeds 127", scene="Intro", track="D_kick", index=0)
    text = report.render()
    assert "== Audit ==" in text
    assert "cell ok" in text
    assert "velocity 130" in text
    assert report.summary() in text
    # show_ok=False hides OK lines
    hidden = report.render(show_ok=False)
    assert "cell ok" not in hidden
    assert "velocity 130" in hidden


def test_report_extend():
    a = Report("A")
    a.ok("a1")
    b = Report("B")
    b.error("b1")
    a.extend(b)
    assert a.error_count == 1
    assert len(a.findings) == 2


def test_report_to_dict():
    report = Report("Apply")
    report.ok("done")
    report.error("boom")
    d = report.to_dict()
    assert d["title"] == "Apply"
    assert d["passed"] is False
    assert d["summary"] == {"ok": 1, "warnings": 0, "errors": 1}
    assert len(d["findings"]) == 2
