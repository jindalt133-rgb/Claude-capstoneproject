"""Unit tests for the Output Writer (TASK-011, SECURITY-SENSITIVE)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from docsync.writer import WriteRefusedError, write_output


def test_write_creates_fresh_generated_directory(tmp_path):
    target = tmp_path / "docs" / "generated" / "code-documentation.md"
    assert not target.parent.exists()
    write_output(target, "<!-- docsync:v1 sha256={} -->\ncontent\n")
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "<!-- docsync:v1 sha256={} -->\ncontent\n"


def test_write_overwrites_preexisting_tool_marked_file(tmp_path):
    target = tmp_path / "docs" / "generated" / "code-documentation.md"
    target.parent.mkdir(parents=True)
    target.write_text("<!-- docsync:v1 sha256={} -->\nold content\n", encoding="utf-8")
    write_output(target, "<!-- docsync:v1 sha256={} -->\nnew content\n")
    assert "new content" in target.read_text(encoding="utf-8")


def test_write_refuses_preexisting_unmarked_foreign_file(tmp_path):
    target = tmp_path / "docs" / "generated" / "code-documentation.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Hand-written docs\nDo not touch.\n", encoding="utf-8")
    with pytest.raises(WriteRefusedError):
        write_output(target, "<!-- docsync:v1 sha256={} -->\nnew content\n")
    # Untouched.
    assert target.read_text(encoding="utf-8") == "# Hand-written docs\nDo not touch.\n"


def test_write_is_atomic_no_partial_file_on_simulated_interruption(tmp_path):
    target = tmp_path / "docs" / "generated" / "code-documentation.md"
    target.parent.mkdir(parents=True)
    target.write_text("<!-- docsync:v1 sha256={} -->\noriginal\n", encoding="utf-8")

    with patch("docsync.writer.os.replace", side_effect=OSError("simulated interruption")):
        with pytest.raises(OSError):
            write_output(target, "<!-- docsync:v1 sha256={} -->\nnew content\n")

    # The original file is untouched -- no partial write landed at `target`.
    assert target.read_text(encoding="utf-8") == "<!-- docsync:v1 sha256={} -->\noriginal\n"
    # No leftover temp file in the target directory.
    leftovers = [p for p in target.parent.iterdir() if p.name.startswith(".docsync-")]
    assert leftovers == []
