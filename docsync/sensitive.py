"""Sensitive-Value Filter (architecture.md Section 15, resolves DR-004).

Scans EVERY rendered-text-bearing field of the Documentation Model --
module/class/function docstrings; ParameterDoc.default; ParameterDoc.annotation
and FunctionDoc.return_annotation; ClassDoc.decorators and
FunctionDoc.decorators, including string-literal decorator-call arguments --
and redacts matches for NFR-003's named categories (passwords, API keys,
access/authentication tokens, credentials, private-key blocks, and a handful
of common cloud-provider key-format prefixes) plus a variable-name heuristic.

This is a deliberately heuristic, non-exhaustive rule set (NFR-003's own text:
"a full enterprise-grade secret-scanning solution is out of scope"). Must run
before the Change Detector's hashing (TASK-009) and the Renderer (TASK-010)
so a redacted value never reaches either.
"""

from __future__ import annotations

import re

from docsync.model import ClassDoc, FunctionDoc, ModuleDoc, ParameterDoc

REDACTED = "<redacted>"

_SECRET_NAME_WORDS = r"(?:password|secret|token|api_?key|credential)"

# A "word start" for secret-keyword matching purposes: the start of the
# string, or a non-alphanumeric character. Underscore counts as a valid
# separator here (unlike \b, which treats '_' as a word character and so
# would never find a boundary in compound_identifiers like `db_password`).
_WORD_START = r"(?<![A-Za-z0-9])"

# Fixed pattern-based rules covering NFR-003's named categories. Order
# matters only in that the private-key block must be matched (and removed)
# as a whole before any narrower pattern could partially match inside it.
_CONTENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # PEM private-key block markers.
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", re.DOTALL),
    # Common cloud-provider / vendor secret-key format prefixes.
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-live-[A-Za-z0-9_-]+"),
    re.compile(r"sk_live_[A-Za-z0-9_-]+"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    # Credentials embedded in a URL's userinfo component, e.g.
    # postgres://user:pw@host/db.
    re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:@'\"]+:[^\s/@'\"]+@[^\s/'\"]+"),
    # A secret-like keyword paired with a quoted literal value, anywhere in
    # text (covers decorator-call keyword arguments, free text, and
    # compound identifiers like `db_password=` alike).
    re.compile(
        rf"(?i){_WORD_START}{_SECRET_NAME_WORDS}\w*\s*=\s*(['\"])(?:(?!\1).)*\1"
    ),
)

# Matches when the secret keyword appears as a whole, underscore-delimited
# segment of the identifier -- e.g. `password`, `api_key`, `db_password`,
# `client_secret`, `my_api_key` -- without flagging an unrelated identifier
# that merely happens to end in similar characters.
_SECRET_PARAMETER_NAME = re.compile(
    rf"(?i)^(?:\w+_)?{_SECRET_NAME_WORDS}\w*$"
)


def redact(text: object) -> object:
    """Redact sensitive substrings in `text`. Non-string values (including
    the model's UNAVAILABLE/NOT_APPLICABLE sentinels) pass through unchanged.
    """
    if not isinstance(text, str):
        return text
    result = text
    for pattern in _CONTENT_PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


def _filter_parameter(p: ParameterDoc) -> ParameterDoc:
    default = redact(p.default)
    # Section 15's variable-name heuristic: the keyword lives in `p.name`,
    # separate from `p.default`'s literal text, so pairing is explicit here.
    if isinstance(p.default, str) and _SECRET_PARAMETER_NAME.match(p.name):
        default = REDACTED
    return ParameterDoc(name=p.name, annotation=redact(p.annotation), default=default)


def _filter_function(f: FunctionDoc) -> FunctionDoc:
    return FunctionDoc(
        name=f.name,
        docstring=redact(f.docstring),
        decorators=[redact(d) for d in f.decorators],
        parameters=[_filter_parameter(p) for p in f.parameters],
        return_annotation=redact(f.return_annotation),
    )


def _filter_class(c: ClassDoc) -> ClassDoc:
    return ClassDoc(
        name=c.name,
        docstring=redact(c.docstring),
        decorators=[redact(d) for d in c.decorators],
        methods=[_filter_function(m) for m in c.methods],
    )


def filter_module(m: ModuleDoc) -> ModuleDoc:
    """Return a new ModuleDoc with every sensitive-value leak path redacted.
    `errors` pass through unchanged -- diagnostic messages are not rendered
    documentation content.
    """
    return ModuleDoc(
        path=m.path,
        docstring=redact(m.docstring),
        classes=[_filter_class(c) for c in m.classes],
        functions=[_filter_function(f) for f in m.functions],
        errors=list(m.errors),
    )
