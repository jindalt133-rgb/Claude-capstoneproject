"""Integration / CLI end-to-end tests (TASK-015).

Each test exercises the CLI entry point (`docsync.cli.main`) against a
fixture source tree built under `tmp_path`, with the process cwd
redirected there so the default `docs/generated/` root resolves inside
the fixture. One test (or pair) per Acceptance Criterion named by
impl-plan.md TASK-015.
"""

from __future__ import annotations

import pytest

from docsync.cli import main

OUTPUT_REL = "docs/generated/code-documentation.md"


@pytest.fixture(autouse=True)
def _chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write(tmp_path, relative, content):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_ac001_ac002_primary_workflow_produces_documentation(tmp_path):
    src = tmp_path / "srcpkg"
    _write(
        tmp_path,
        "srcpkg/mod.py",
        '''"""Module docstring."""


class Greeter:
    """Greets people."""

    def hello(self, name: str) -> str:
        """Say hello."""
        return f"hello {name}"


def top(x: int) -> int:
    """Doubles x."""
    return x * 2
''',
    )
    exit_code = main(["--source", str(src)])
    assert exit_code == 0
    output = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    assert "Module docstring." in output
    assert "Greeter" in output
    assert "Greets people." in output
    assert "def hello(self, name: str) -> str:" in output
    assert "Say hello." in output
    assert "def top(x: int) -> int:" in output
    assert "Doubles x." in output


def test_ac003_unavailable_information_marked_explicitly(tmp_path):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/mod.py", "def f(x):\n    return x\n")
    exit_code = main(["--source", str(src)])
    assert exit_code == 0
    output = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    assert "_Not available_" in output


def test_ac004_signature_change_triggers_regeneration(tmp_path):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/mod.py", "def f(x: int) -> int:\n    return x\n")
    main(["--source", str(src)])
    first = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")

    _write(tmp_path, "srcpkg/mod.py", "def f(x: int) -> str:\n    return x\n")
    exit_code = main(["--source", str(src)])
    second = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")

    assert exit_code == 0
    assert first != second
    assert "def f(x: int) -> str:" in second


def test_ac005_body_only_change_does_not_rewrite(tmp_path, capsys):
    src = tmp_path / "srcpkg"
    _write(
        tmp_path,
        "srcpkg/mod.py",
        'def f(x: int) -> int:\n    """doc"""\n    return x + 1\n',
    )
    main(["--source", str(src)])
    first = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    capsys.readouterr()

    _write(
        tmp_path,
        "srcpkg/mod.py",
        'def f(x: int) -> int:\n    """doc"""\n    return x + 999  # body-only change\n',
    )
    exit_code = main(["--source", str(src)])
    second = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert first == second
    assert "no changes detected" in stdout


def test_ac006_ac007_invalid_file_does_not_block_valid_files(tmp_path, capsys):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/good.py", 'def f():\n    """ok"""\n    return 1\n')
    _write(tmp_path, "srcpkg/bad.py", "def broken(:\n    pass\n")

    exit_code = main(["--source", str(src)])
    stderr = capsys.readouterr().err
    output = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")

    assert exit_code != 0
    assert "good.py" in output
    assert "bad.py" not in output
    assert "bad.py" in stderr


def test_ac008_sensitive_value_not_in_generated_documentation(tmp_path):
    src = tmp_path / "srcpkg"
    _write(
        tmp_path,
        "srcpkg/mod.py",
        "def login(password='hunter2-supersecret'):\n    pass\n",
    )
    exit_code = main(["--source", str(src)])
    output = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "hunter2-supersecret" not in output


def test_ac009_default_exclusions_not_analyzed(tmp_path):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/keep.py", "def keep():\n    pass\n")
    _write(tmp_path, "srcpkg/.venv/lib.py", "def excluded():\n    pass\n")
    exit_code = main(["--source", str(src)])
    output = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "keep" in output
    assert "excluded" not in output


def test_ac010_custom_exclusion_pattern_applied(tmp_path):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/keep.py", "def keep():\n    pass\n")
    _write(tmp_path, "srcpkg/skip_generated.py", "def excluded():\n    pass\n")
    exit_code = main(["--source", str(src), "--exclude", "skip_*.py"])
    output = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "keep" in output
    assert "excluded" not in output


def test_ac011_preexisting_manual_file_not_modified(tmp_path):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/mod.py", "def f():\n    pass\n")
    manual_content = "# Hand-written docs\nDo not overwrite.\n"
    _write(tmp_path, OUTPUT_REL, manual_content)

    exit_code = main(["--source", str(src)])
    output_after = (tmp_path / OUTPUT_REL).read_text(encoding="utf-8")

    assert exit_code != 0
    assert output_after == manual_content


def test_ac012_custom_output_subpath_within_generated(tmp_path):
    src = tmp_path / "srcpkg"
    _write(tmp_path, "srcpkg/mod.py", 'def f():\n    """doc"""\n    pass\n')
    exit_code = main(["--source", str(src), "--output", "api/reference.md"])
    custom_output = tmp_path / "docs" / "generated" / "api" / "reference.md"
    default_output = tmp_path / OUTPUT_REL

    assert exit_code == 0
    assert custom_output.exists()
    assert "doc" in custom_output.read_text(encoding="utf-8")
    assert not default_output.exists()
