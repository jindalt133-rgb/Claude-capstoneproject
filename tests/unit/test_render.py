"""Unit tests for the Markdown Renderer (TASK-010)."""

from __future__ import annotations

from docsync.changedetect import HEADER_MARKER, build_hash_table
from docsync.model import UNAVAILABLE, ClassDoc, FunctionDoc, ModuleDoc, ParameterDoc
from docsync.render import NOT_AVAILABLE_MARKER, render


def _sample_modules():
    return [
        ModuleDoc(
            path="pkg/a.py",
            docstring="Module A.",
            classes=[
                ClassDoc(
                    name="Foo",
                    docstring="A class.",
                    methods=[
                        FunctionDoc(
                            name="bar",
                            docstring="Does a thing.",
                            parameters=[ParameterDoc(name="x", annotation="int")],
                            return_annotation="int",
                        )
                    ],
                )
            ],
            functions=[FunctionDoc(name="top_level")],
        )
    ]


def test_render_is_deterministic_across_repeated_calls():
    modules = _sample_modules()
    hash_table = build_hash_table(modules)
    first = render(modules, hash_table)
    second = render(modules, hash_table)
    assert first == second


def test_render_unavailable_field_shown_distinctly():
    modules = [ModuleDoc(path="pkg/a.py")]
    assert modules[0].docstring is UNAVAILABLE
    output = render(modules, build_hash_table(modules))
    assert NOT_AVAILABLE_MARKER in output


def test_render_genuinely_empty_docstring_not_confused_with_unavailable():
    """COR-02 regression: a real, empty docstring ("") is a determined
    value (architecture Section 9) and must not render as _Not available_,
    which is reserved for the UNAVAILABLE sentinel."""
    modules = [ModuleDoc(path="pkg/a.py", docstring="")]
    output = render(modules, build_hash_table(modules))
    assert NOT_AVAILABLE_MARKER not in output


def test_render_zero_default_and_empty_annotation_not_confused_with_sentinels():
    """COR-02 regression: falsy-but-determined values (0, "") for
    parameter default/annotation must still render, not be dropped as if
    unavailable/not-applicable."""
    modules = [
        ModuleDoc(
            path="pkg/a.py",
            functions=[
                FunctionDoc(
                    name="f",
                    parameters=[ParameterDoc(name="x", annotation="", default="0")],
                )
            ],
        )
    ]
    output = render(modules, build_hash_table(modules))
    assert "x: " in output
    assert "= 0" in output


def test_render_header_banner_contains_hash_table():
    modules = _sample_modules()
    hash_table = build_hash_table(modules)
    output = render(modules, hash_table)
    assert HEADER_MARKER in output
    assert '"pkg/a.py"' in output
    assert hash_table["pkg/a.py"] in output


def test_render_includes_module_class_and_function_content():
    modules = _sample_modules()
    output = render(modules, build_hash_table(modules))
    assert "pkg/a.py" in output
    assert "Module A." in output
    assert "Foo" in output
    assert "A class." in output
    assert "def bar(x: int) -> int:" in output
    assert "Does a thing." in output
    assert "def top_level():" in output


def test_render_do_not_edit_notice_present():
    modules = [ModuleDoc(path="pkg/a.py")]
    output = render(modules, build_hash_table(modules))
    assert "DO NOT EDIT" in output
