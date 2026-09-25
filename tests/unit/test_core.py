"""Unit tests for the Pipeline Orchestrator (TASK-014), focused on the
ERR-01 write-stage error boundary.

Covers the general case (any OSError at write time, not just the
WriteRefusedError ownership-marker refusal) so an unexpected filesystem
failure -- disk full, permission error, or the docs/generated/ root being
occupied by a non-directory -- is reported as a clean diagnostic instead
of propagating as an uncontrolled traceback (FR-013/FR-014).
"""

from __future__ import annotations

import pytest

import docsync.core as core_module
from docsync.core import run


def _make_config(tmp_path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    (src / "mod.py").write_text('def f():\n    """doc"""\n    return 1\n', encoding="utf-8")
    from docsync.config import Config

    return Config(source_dir=src, output_path=tmp_path / "docs" / "generated" / "out.md")


def test_run_converts_unexpected_oserror_at_write_to_diagnostic(tmp_path, monkeypatch):
    """ERR-01 regression: an OSError raised by write_output (other than
    WriteRefusedError) must be caught and reported as a DocSyncError with
    stage='write', not propagate out of run()."""
    config = _make_config(tmp_path)

    def _boom(target, content):
        raise OSError("simulated disk-full failure")

    monkeypatch.setattr(core_module, "write_output", _boom)

    result = run(config)

    assert result.written is False
    write_errors = [e for e in result.diagnostics.errors if e.stage == "write"]
    assert len(write_errors) == 1
    assert "simulated disk-full failure" in write_errors[0].message
    assert result.diagnostics.exit_code() == 1


def test_run_still_reports_write_refused_error_as_diagnostic(tmp_path, monkeypatch):
    """Confirms the pre-existing WriteRefusedError handling still works
    unchanged alongside the new general OSError clause."""
    from docsync.writer import WriteRefusedError

    config = _make_config(tmp_path)

    def _refuse(target, content):
        raise WriteRefusedError(f"refusing to overwrite: {target}")

    monkeypatch.setattr(core_module, "write_output", _refuse)

    result = run(config)

    assert result.written is False
    write_errors = [e for e in result.diagnostics.errors if e.stage == "write"]
    assert len(write_errors) == 1
    assert "refusing to overwrite" in write_errors[0].message


def test_run_writes_successfully_when_no_error(tmp_path):
    config = _make_config(tmp_path)
    result = run(config)
    assert result.written is True
    assert not result.diagnostics.has_errors
    assert config.output_path.exists()
