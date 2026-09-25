"""Unit tests for the Configuration Resolver.

Split into two portions per impl-plan.md:
  - TASK-003: core resolution (source dir validation, exclusions, default output)
  - TASK-004: the Section 11.1 / ADR-0005 output-path boundary-check algorithm
"""

from __future__ import annotations

import os
import sys

import pytest

from docsync.config import (
    DEFAULT_EXCLUSIONS,
    ConfigError,
    boundary_check,
    matches_exclusion,
    resolve_config,
)

# ---------------------------------------------------------------------------
# TASK-003: core resolution (excluding boundary check)
# ---------------------------------------------------------------------------


def test_resolve_config_valid_source_dir(tmp_path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    (src / "a.py").write_text("x = 1\n")
    generated_root = tmp_path / "docs" / "generated"
    cfg = resolve_config(str(src), generated_root=generated_root)
    assert cfg.source_dir == src
    assert cfg.output_path == (generated_root.resolve() / "code-documentation.md")


def test_resolve_config_nonexistent_source_dir_raises(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(ConfigError):
        resolve_config(str(missing), generated_root=tmp_path / "docs" / "generated")


def test_resolve_config_source_dir_is_a_file_raises(tmp_path):
    f = tmp_path / "not_a_dir.py"
    f.write_text("x = 1\n")
    with pytest.raises(ConfigError):
        resolve_config(str(f), generated_root=tmp_path / "docs" / "generated")


def test_resolve_config_default_exclusions_present(tmp_path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    generated_root = tmp_path / "docs" / "generated"
    cfg = resolve_config(str(src), generated_root=generated_root)
    assert DEFAULT_EXCLUSIONS <= cfg.exclusions


def test_resolve_config_custom_exclusions_merged(tmp_path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    generated_root = tmp_path / "docs" / "generated"
    cfg = resolve_config(str(src), excludes=["*_generated.py"], generated_root=generated_root)
    assert "*_generated.py" in cfg.exclusions
    assert DEFAULT_EXCLUSIONS <= cfg.exclusions


def test_matches_exclusion_default_directory_name():
    assert matches_exclusion("pkg/.git/config", DEFAULT_EXCLUSIONS)
    assert matches_exclusion("pkg/__pycache__/mod.pyc", DEFAULT_EXCLUSIONS)
    assert not matches_exclusion("pkg/module.py", DEFAULT_EXCLUSIONS)


def test_matches_exclusion_custom_glob_pattern():
    exclusions = DEFAULT_EXCLUSIONS | {"*_test.py"}
    assert matches_exclusion("pkg/foo_test.py", exclusions)
    assert not matches_exclusion("pkg/foo.py", exclusions)


# ---------------------------------------------------------------------------
# TASK-004: output-path boundary-check algorithm (Section 11.1 / ADR-0005)
# Security-sensitive: exact algorithm, no deviation.
# ---------------------------------------------------------------------------


def test_boundary_check_valid_relative_subpath_accepted(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    result = boundary_check("api/reference.md", generated_root=generated_root)
    assert result == (generated_root.resolve() / "api" / "reference.md")


def test_boundary_check_valid_nested_path_accepted_positive_control(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    result = boundary_check("api/nested/reference.md", generated_root=generated_root)
    assert result.is_relative_to(generated_root.resolve())


def test_boundary_check_rejects_empty():
    with pytest.raises(ConfigError):
        boundary_check("")
    with pytest.raises(ConfigError):
        boundary_check("   ")


def test_boundary_check_rejects_absolute_posix_path(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check("/etc/passwd", generated_root=generated_root)


def test_boundary_check_rejects_absolute_windows_path(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check(r"C:\evil.md", generated_root=generated_root)


def test_boundary_check_rejects_windows_drive_relative_path(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check("C:foo.md", generated_root=generated_root)


def test_boundary_check_rejects_unc_path(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check(r"\\server\share\x.md", generated_root=generated_root)


def test_boundary_check_rejects_dotdot_traversal(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check("../evil.md", generated_root=generated_root)


def test_boundary_check_rejects_nested_traversal(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check("a/../../evil.md", generated_root=generated_root)


def test_boundary_check_rejects_sibling_prefix_escape(tmp_path):
    """docs/generated-evil/ must NOT be accepted merely because it shares a
    string prefix with docs/generated/ -- proves path-aware containment,
    not string-prefix comparison."""
    generated_root = tmp_path / "docs" / "generated"
    generated_root.parent.mkdir(parents=True, exist_ok=True)
    (generated_root.parent / "generated-evil").mkdir()
    with pytest.raises(ConfigError):
        boundary_check("../generated-evil/x.md", generated_root=generated_root)


def test_boundary_check_rejects_root_itself_via_dot(tmp_path):
    """COR-01 regression: '.' resolves to the docs/generated/ root itself,
    which must never be an accepted output target (writing there would
    replace the directory with a plain file)."""
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check(".", generated_root=generated_root)


def test_boundary_check_rejects_candidate_resolving_exactly_to_root(tmp_path):
    """COR-01 regression: any relative candidate that resolves exactly to
    the docs/generated/ root (not a file inside it) must be rejected, not
    just the literal '.' spelling."""
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check("./.", generated_root=generated_root)


def test_resolve_config_rejects_output_dot(tmp_path):
    """COR-01 regression: '--output .' must fail safely through the full
    resolve_config flow, not just at the boundary_check unit level."""
    src = tmp_path / "srcpkg"
    src.mkdir()
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        resolve_config(str(src), output=".", generated_root=generated_root)


def test_boundary_check_case_insensitivity_no_escape(tmp_path):
    """Case handling falls out of .resolve() naturally -- not tested for a
    specific case-sensitivity outcome (host-dependent), only that no valid
    escape occurs."""
    generated_root = tmp_path / "docs" / "generated"
    result = boundary_check("Reference.md", generated_root=generated_root)
    assert result.is_relative_to(generated_root.resolve())


@pytest.mark.skipif(sys.platform != "win32", reason="drive-relative semantics are Windows-specific")
def test_boundary_check_rejects_windows_drive_relative_on_windows(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    with pytest.raises(ConfigError):
        boundary_check("C:foo.md", generated_root=generated_root)


@pytest.mark.skipif(
    not hasattr(os, "symlink"), reason="symlink support required for this test"
)
def test_boundary_check_rejects_symlink_escape(tmp_path):
    generated_root = tmp_path / "docs" / "generated"
    generated_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    symlinked_dir = generated_root / "escape"
    try:
        symlinked_dir.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")
    with pytest.raises(ConfigError):
        boundary_check("escape/evil.md", generated_root=generated_root)
