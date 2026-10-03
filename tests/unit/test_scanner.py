"""Unit tests for the Source Directory Scanner (TASK-005)."""

from __future__ import annotations

import os

import pytest

from docsync.config import DEFAULT_EXCLUSIONS
from docsync.scanner import scan


def test_scan_yields_only_py_files(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "readme.md").write_text("hello\n")
    (tmp_path / "data.json").write_text("{}\n")
    result = scan(tmp_path, DEFAULT_EXCLUSIONS)
    names = {p.name for p in result.files}
    assert names == {"a.py"}
    assert result.errors == []


def test_scan_prunes_default_exclusions_before_descent(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("x = 1\n")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "lib.py").write_text("y = 1\n")
    gitdir = tmp_path / ".git"
    gitdir.mkdir()
    (gitdir / "config.py").write_text("z = 1\n")
    result = scan(tmp_path, DEFAULT_EXCLUSIONS)
    names = {p.name for p in result.files}
    assert names == {"mod.py"}


def test_scan_applies_custom_exclude_glob_pattern(tmp_path):
    (tmp_path / "keep.py").write_text("x = 1\n")
    (tmp_path / "skip_generated.py").write_text("y = 1\n")
    exclusions = DEFAULT_EXCLUSIONS | {"skip_*.py"}
    result = scan(tmp_path, exclusions)
    names = {p.name for p in result.files}
    assert names == {"keep.py"}


def test_scan_unreadable_subtree_reported_not_fatal(tmp_path):
    (tmp_path / "good.py").write_text("x = 1\n")
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / "inner.py").write_text("y = 1\n")

    if os.name == "nt":
        pytest.skip("permission-based unreadable-directory simulation is unreliable on Windows")

    os.chmod(blocked, 0o000)
    try:
        result = scan(tmp_path, DEFAULT_EXCLUSIONS)
    finally:
        os.chmod(blocked, 0o755)

    names = {p.name for p in result.files}
    assert names == {"good.py"}
    assert len(result.errors) == 1
    assert "blocked" in result.errors[0].path


def test_scan_follows_symlinked_py_file_in_source_tree(tmp_path):
    """COR-03 regression: architecture Section 7 calls for an ordinary,
    unspecial-cased walk on the source side -- a symlinked .py file must
    be found, not silently skipped."""
    real_file = tmp_path / "real_target.py"
    real_file.write_text("x = 1\n")
    link = tmp_path / "linked.py"
    try:
        os.symlink(str(real_file), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted in this environment")

    result = scan(tmp_path, DEFAULT_EXCLUSIONS)
    names = {p.name for p in result.files}
    assert "linked.py" in names
    assert result.errors == []


def test_scan_per_entry_oserror_reported_not_fatal(tmp_path, monkeypatch):
    """ERR-02 regression: an OSError from a single entry's is_dir()/
    is_file() call (e.g. a broken symlink or a file removed mid-walk)
    must be recorded as a ScanError for that entry and the walk must
    continue for the remaining, healthy entries -- not abort the subtree."""
    (tmp_path / "good.py").write_text("x = 1\n")
    bad_path = tmp_path / "broken.py"

    class _RaisingEntry:
        path = str(bad_path)
        name = "broken.py"

        def is_dir(self, *args, **kwargs):
            raise OSError("simulated stat failure")

        def is_file(self, *args, **kwargs):
            raise OSError("simulated stat failure")

    import docsync.scanner as scanner_module

    real_entries = list(os.scandir(tmp_path))
    original_scandir = os.scandir

    def _fake_scandir(path):
        if str(path) == str(tmp_path):
            return real_entries + [_RaisingEntry()]
        return original_scandir(path)

    monkeypatch.setattr(scanner_module.os, "scandir", _fake_scandir)

    result = scan(tmp_path, DEFAULT_EXCLUSIONS)

    names = {p.name for p in result.files}
    assert names == {"good.py"}
    assert len(result.errors) == 1
    assert "broken.py" in result.errors[0].path


def test_scan_nested_directories_all_py_files_found(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "deep.py").write_text("x = 1\n")
    (tmp_path / "top.py").write_text("y = 1\n")
    result = scan(tmp_path, DEFAULT_EXCLUSIONS)
    names = {p.name for p in result.files}
    assert names == {"deep.py", "top.py"}
