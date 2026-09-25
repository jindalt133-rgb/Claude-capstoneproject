"""Unit tests for docsync/parser.py.

TASK-006: encoding-aware read portion.
TASK-007: AST parsing and structural extraction portion.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from docsync.model import NOT_APPLICABLE, UNAVAILABLE
from docsync.parser import SourceReadError, extract_module, read_source


def test_read_source_utf8_no_cookie(tmp_path):
    f = tmp_path / "plain.py"
    f.write_bytes('x = "hello world"\n'.encode("utf-8"))
    text = read_source(f)
    assert text == 'x = "hello world"\n'


def test_read_source_pep263_cookie_non_utf8_encoding(tmp_path):
    f = tmp_path / "latin1.py"
    content = "# -*- coding: latin-1 -*-\nx = \"café\"\n"
    f.write_bytes(content.encode("latin-1"))
    text = read_source(f)
    assert text == content


def test_read_source_declared_encoding_mismatch_raises_structured_error(tmp_path):
    f = tmp_path / "bad.py"
    # Declares ascii but contains a byte (0xFF) that is not valid ascii.
    f.write_bytes(b"# -*- coding: ascii -*-\nx = 1  # \xff\n")
    try:
        read_source(f)
        assert False, "expected SourceReadError"
    except SourceReadError as exc:
        assert exc.error.path == str(f)
        assert exc.error.stage == "decode"
        assert exc.error.message


# ---------------------------------------------------------------------------
# TASK-007: AST parsing and structural extraction
# ---------------------------------------------------------------------------


def test_extract_module_docstring_and_top_level_function(tmp_path):
    source = '''"""Module docstring."""


def greet(name: str, greeting: str = "hello") -> str:
    """Greets someone."""
    return f"{greeting}, {name}"
'''
    m = extract_module(Path("mod.py"), source)
    assert m.docstring == "Module docstring."
    assert m.errors == []
    assert len(m.functions) == 1
    f = m.functions[0]
    assert f.name == "greet"
    assert f.docstring == "Greets someone."
    assert f.return_annotation == "str"
    assert f.parameters[0].name == "name"
    assert f.parameters[0].annotation == "str"
    assert f.parameters[0].default is NOT_APPLICABLE
    assert f.parameters[1].name == "greeting"
    assert f.parameters[1].default == "'hello'"


def test_extract_module_class_with_decorators_and_methods(tmp_path):
    source = '''class Foo:
    """A class."""

    @staticmethod
    def bar(x, *args, y=1, **kwargs):
        pass
'''
    m = extract_module(Path("mod.py"), source)
    assert len(m.classes) == 1
    c = m.classes[0]
    assert c.name == "Foo"
    assert c.docstring == "A class."
    assert len(c.methods) == 1
    method = c.methods[0]
    assert method.name == "bar"
    assert method.decorators == ["staticmethod"]
    names = [p.name for p in method.parameters]
    assert names == ["x", "*args", "y", "**kwargs"]


def test_extract_module_no_docstring_is_unavailable():
    m = extract_module(Path("mod.py"), "x = 1\n")
    assert m.docstring is UNAVAILABLE


def test_extract_module_no_return_annotation_is_unavailable():
    m = extract_module(Path("mod.py"), "def f():\n    return 1\n")
    assert m.functions[0].return_annotation is UNAVAILABLE


def test_extract_module_accepts_plain_str_path_as_actually_used_in_production():
    """CLR-01 regression: core.run passes a plain str (relative.as_posix()),
    not a Path -- lock in that extract_module's real, documented call
    contract (path: str) works correctly."""
    m = extract_module("pkg/mod.py", "def f():\n    return 1\n")
    assert m.path == "pkg/mod.py"
    assert m.functions[0].name == "f"


def test_extract_module_body_statements_never_copied_into_model():
    source = '''def f():
    """doc"""
    SECRET = "should-not-appear"
    return SECRET
'''
    m = extract_module(Path("mod.py"), source)
    f = m.functions[0]
    assert "SECRET" not in repr(f)
    assert "should-not-appear" not in repr(f)


@pytest.mark.parametrize(
    "exc",
    [
        SyntaxError("bad syntax"),
        RecursionError("too deep"),
        ValueError("bad value"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad byte"),
        LookupError("unknown encoding"),
        OSError("io failure"),
    ],
)
def test_extract_module_each_parse_exception_is_isolated_not_fatal(exc):
    with patch("docsync.parser.ast.parse", side_effect=exc):
        m = extract_module(Path("mod.py"), "irrelevant source")
    assert m.classes == []
    assert m.functions == []
    assert len(m.errors) == 1
    assert m.errors[0].stage == "parse"
    assert m.errors[0].path == "mod.py"
