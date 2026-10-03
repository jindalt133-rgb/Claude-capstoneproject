"""Unit tests for the Error & Diagnostics Reporter (TASK-012)."""

from __future__ import annotations

from docsync.diagnostics import DiagnosticsReport, DocSyncError


def test_report_aggregates_errors_from_multiple_sources():
    report = DiagnosticsReport()
    report.add(DocSyncError(path="pkg/a.py", stage="parse", message="invalid syntax"))
    report.extend(
        [
            DocSyncError(path="pkg/blocked", stage="scan", message="permission denied"),
            DocSyncError(path="docs/generated/x.md", stage="write", message="unmarked file"),
        ]
    )
    assert len(report.errors) == 3
    formatted = report.format_all()
    assert "[parse] pkg/a.py: invalid syntax" in formatted
    assert "[scan] pkg/blocked: permission denied" in formatted
    assert "[write] docs/generated/x.md: unmarked file" in formatted


def test_exit_code_zero_when_no_errors():
    report = DiagnosticsReport()
    assert report.has_errors is False
    assert report.exit_code() == 0


def test_exit_code_nonzero_when_any_error_present():
    report = DiagnosticsReport()
    report.add(DocSyncError(path="pkg/a.py", stage="parse", message="bad"))
    assert report.has_errors is True
    assert report.exit_code() != 0


def test_error_format_is_file_identified_and_human_readable():
    error = DocSyncError(path="pkg/a.py", stage="parse", message="invalid syntax")
    formatted = error.format()
    assert "pkg/a.py" in formatted
    assert "invalid syntax" in formatted
