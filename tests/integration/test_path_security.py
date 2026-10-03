"""AC-015 security / path-boundary integration tests (TASK-016, SECURITY-SENSITIVE).

Runs the CLI end-to-end (not the unit-level boundary_check() calls already
covered by TASK-004/test_config.py) against every negative case from
docs/requirements.md Section 19 / impl-plan.md TASK-016, and asserts:
  * non-zero exit code
  * a clear, file-identified error message
  * no file is written anywhere outside docs/generated/ (filesystem snapshot
    before/after)

Plus one positive control: a valid nested --output path is accepted.
"""

from __future__ import annotations

import os

import pytest

from docsync.cli import main

OUTPUT_REL = "docs/generated/code-documentation.md"


@pytest.fixture(autouse=True)
def _chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_source(tmp_path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    (src / "mod.py").write_text('def f():\n    """doc"""\n    return 1\n', encoding="utf-8")
    return src


def _snapshot(root):
    files = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            files.add(os.path.relpath(full, root).replace("\\", "/"))
    return files


def _assert_no_write_outside_generated(before, after):
    new_files = after - before
    for path in new_files:
        assert path.startswith("docs/generated/"), (
            f"file written outside docs/generated/: {path}"
        )


NEGATIVE_CASES = [
    ("dot_dot_relative", "../escape.md"),
    ("nested_traversal", "sub/../../escape2.md"),
    ("absolute_posix", "/etc/passwd"),
    ("absolute_windows", "C:\\Windows\\evil.md"),
    ("sibling_prefix", "../generated-evil/x.md"),
    ("drive_relative", "C:evil.md"),
    ("unc_path", "\\\\server\\share\\evil.md"),
]


@pytest.mark.parametrize("name, candidate", NEGATIVE_CASES, ids=[c[0] for c in NEGATIVE_CASES])
def test_ac015_negative_case_rejected_with_no_write_outside_generated(
    tmp_path, capsys, name, candidate
):
    src = _write_source(tmp_path)
    before = _snapshot(tmp_path)

    exit_code = main(["--source", str(src), "--output", candidate])
    stderr = capsys.readouterr().err

    after = _snapshot(tmp_path)

    assert exit_code != 0, f"expected rejection for {name!r} candidate {candidate!r}"
    assert candidate in stderr or repr(candidate) in stderr
    _assert_no_write_outside_generated(before, after)


def test_ac015_output_dot_rejected_with_no_write_to_generated(tmp_path, capsys):
    """COR-01 regression: '--output .' (the docs/generated/ root itself)
    must be rejected end-to-end, and must not modify docs/generated/ at
    all -- not overwrite it with a file, not leave a partial write behind."""
    src = _write_source(tmp_path)
    before = _snapshot(tmp_path)

    exit_code = main(["--source", str(src), "--output", "."])
    stderr = capsys.readouterr().err

    after = _snapshot(tmp_path)

    assert exit_code != 0
    assert stderr.strip() != ""
    assert before == after, "docs/generated/ must be untouched when --output is rejected"
    generated_root = tmp_path / "docs" / "generated"
    assert not generated_root.exists() or generated_root.is_dir()


def test_ac015_symlink_escape_rejected_when_platform_supports_it(tmp_path, capsys):
    src = _write_source(tmp_path)
    outside_target = tmp_path.parent / "outside_target_dir"
    outside_target.mkdir(exist_ok=True)
    link_path = tmp_path / "docs" / "generated" / "escape_link"
    link_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        os.symlink(str(outside_target), str(link_path), target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted in this environment")

    before = _snapshot(tmp_path)
    exit_code = main(["--source", str(src), "--output", "escape_link/evil.md"])
    after = _snapshot(tmp_path)

    assert exit_code != 0
    _assert_no_write_outside_generated(before, after)
    assert not (outside_target / "evil.md").exists()


def test_ac015_positive_control_valid_nested_path_accepted(tmp_path):
    src = _write_source(tmp_path)
    exit_code = main(["--source", str(src), "--output", "api/nested/reference.md"])
    target = tmp_path / "docs" / "generated" / "api" / "nested" / "reference.md"

    assert exit_code == 0
    assert target.exists()
    assert "doc" in target.read_text(encoding="utf-8")
