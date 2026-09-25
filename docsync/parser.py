"""Python Source Parser (architecture.md Section 8).

TASK-006: encoding-aware read/decode of a candidate source file.
TASK-007: AST parsing and structural extraction into the Documentation
Model.
"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

from docsync.model import (
    UNAVAILABLE,
    ClassDoc,
    FunctionDoc,
    ModuleDoc,
    NOT_APPLICABLE,
    ParameterDoc,
    ParseError,
)

# Exact set per architecture.md Section 8 point 2 (resolves DR-007) -- do
# not narrow to SyntaxError alone, and do not add types beyond this set.
_PARSE_EXCEPTIONS = (
    SyntaxError,
    RecursionError,
    ValueError,
    UnicodeDecodeError,
    LookupError,
    OSError,
)


class SourceReadError(Exception):
    """Raised when a candidate file cannot be read/decoded as text.

    Carries a ParseError so the caller can record a structured per-file
    diagnostic instead of crashing the run (FR-013).
    """

    def __init__(self, error: ParseError) -> None:
        super().__init__(error.message)
        self.error = error


def read_source(path: Path) -> str:
    """Read a Python source file as text, detecting its declared encoding
    the same way CPython's own tokenizer does (resolves DR-006): via
    tokenize.detect_encoding, which inspects the first two lines for a
    PEP 263 encoding cookie and defaults to UTF-8 when absent.

    Raises SourceReadError (wrapping a structured ParseError) on any
    decode failure -- never fabricates text, never crashes the run.
    """
    try:
        with open(path, "rb") as raw:
            encoding, _ = tokenize.detect_encoding(raw.readline)
    except SyntaxError as exc:
        # tokenize.detect_encoding raises SyntaxError for a malformed cookie.
        raise SourceReadError(
            ParseError(path=str(path), stage="encoding-detect", message=str(exc))
        ) from exc
    except OSError as exc:
        raise SourceReadError(
            ParseError(path=str(path), stage="read", message=str(exc))
        ) from exc

    try:
        with open(path, "rb") as raw:
            data = raw.read()
        return io.TextIOWrapper(io.BytesIO(data), encoding=encoding).read()
    except (UnicodeDecodeError, LookupError) as exc:
        raise SourceReadError(
            ParseError(path=str(path), stage="decode", message=str(exc))
        ) from exc
    except OSError as exc:
        raise SourceReadError(
            ParseError(path=str(path), stage="read", message=str(exc))
        ) from exc


def _docstring_or_unavailable(node: ast.AST) -> object:
    docstring = ast.get_docstring(node)
    return docstring if docstring is not None else UNAVAILABLE


def _annotation_or_unavailable(node: ast.expr | None) -> object:
    return ast.unparse(node) if node is not None else UNAVAILABLE


def _extract_parameters(args: ast.arguments) -> list[ParameterDoc]:
    """Extract parameters in source order: positional-only + positional,
    then *args, then keyword-only, then **kwargs. No type inference --
    annotations and defaults are unparsed source text only (Section 8
    point 4).
    """
    params: list[ParameterDoc] = []

    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    num_no_default = len(positional) - len(defaults)
    for i, arg in enumerate(positional):
        default = (
            ast.unparse(defaults[i - num_no_default])
            if i >= num_no_default
            else NOT_APPLICABLE
        )
        params.append(
            ParameterDoc(
                name=arg.arg,
                annotation=_annotation_or_unavailable(arg.annotation),
                default=default,
            )
        )

    if args.vararg is not None:
        params.append(
            ParameterDoc(
                name="*" + args.vararg.arg,
                annotation=_annotation_or_unavailable(args.vararg.annotation),
                default=NOT_APPLICABLE,
            )
        )

    for kwarg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
        default = ast.unparse(kw_default) if kw_default is not None else NOT_APPLICABLE
        params.append(
            ParameterDoc(
                name=kwarg.arg,
                annotation=_annotation_or_unavailable(kwarg.annotation),
                default=default,
            )
        )

    if args.kwarg is not None:
        params.append(
            ParameterDoc(
                name="**" + args.kwarg.arg,
                annotation=_annotation_or_unavailable(args.kwarg.annotation),
                default=NOT_APPLICABLE,
            )
        )

    return params


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionDoc:
    return FunctionDoc(
        name=node.name,
        docstring=_docstring_or_unavailable(node),
        decorators=[ast.unparse(d) for d in node.decorator_list],
        parameters=_extract_parameters(node.args),
        return_annotation=_annotation_or_unavailable(node.returns),
    )


def _extract_class(node: ast.ClassDef) -> ClassDoc:
    methods = [
        _extract_function(item)
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return ClassDoc(
        name=node.name,
        docstring=_docstring_or_unavailable(node),
        decorators=[ast.unparse(d) for d in node.decorator_list],
        methods=methods,
    )


def extract_module(path: str, source: str) -> ModuleDoc:
    """Parse `source` (already read/decoded by TASK-006's `read_source`)
    into a populated ModuleDoc. Any of the five exception types named by
    architecture.md Section 8 point 2 (resolves DR-007) is caught and
    converted into a structured per-file ParseError -- never fatal to the
    run (FR-013). Function/method body statements are never copied into
    the model: only `ast.get_docstring`, decorators, parameter/return
    annotations and defaults are read.
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except _PARSE_EXCEPTIONS as exc:
        return ModuleDoc(
            path=str(path),
            errors=[ParseError(path=str(path), stage="parse", message=str(exc))],
        )

    module_doc = ModuleDoc(path=str(path), docstring=_docstring_or_unavailable(tree))
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            module_doc.classes.append(_extract_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            module_doc.functions.append(_extract_function(node))
    return module_doc
