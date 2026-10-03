# ADR-0002: Python Source Parsing Approach

Status: Proposed (pending Design Review / Gate G2)
Date: 2026-09-24

## Context

Given ADR-0001 (implementation in Python), the tool still needs a concrete strategy
to turn Python source text into the structured information required by FR-006
(module/file name, module docstring, classes, class docstrings, functions, methods,
signatures, parameters, return information when determinable, docstrings) while
satisfying FR-012 (report undeterminable information rather than fabricating it)
and FR-013 (one invalid/unsupported file must not block the others).

## Options Considered

1. **Standard-library `ast` module.** Parses Python source into an abstract syntax
   tree using CPython's own grammar; raises `SyntaxError` on invalid source, which
   can be caught per file.
2. **Third-party concrete-syntax-tree library (e.g., `libcst`).** Preserves
   formatting/comments and supports source-to-source transforms.
3. **`tree-sitter` grammar for Python.** Language-agnostic incremental parser used
   by editors; robust to partially-invalid source.
4. **Regular-expression / text-based scanning.** Pattern-match `def`/`class` lines
   directly.

## Decision

Use the standard-library **`ast` module** (plus `ast.unparse` for rendering
annotation/default-value expressions back to source-like text) as the sole parsing
engine for v1.

## Rationale

- **FR-006 (structural extraction):** `ast` exposes exactly the structural elements
  FR-006 requires — module docstrings (`ast.get_docstring`), class/function
  definitions, argument lists (`ast.arguments`), return annotations, and decorator
  lists — without needing a second library.
- **FR-012 (report unavailable, don't fabricate):** `ast` surfaces exactly what is
  statically present. It does not infer or guess types/values it cannot see,
  matching FR-012's intent — anything not explicitly present in source (e.g., an
  un-annotated return type) is naturally represented as absent, not guessed.
- **FR-013 (partial-failure isolation):** `ast.parse()` raises a catchable
  `SyntaxError`/`ValueError` per file; wrapping the per-file parse call in an
  exception boundary directly implements "one invalid file does not block others."
- **Safe dependency usage (CLAUDE.md):** `ast` requires no third-party dependency,
  is maintained in lock-step with the CPython release that ships it, and cannot
  drift out of sync with the language version it targets. `libcst` and
  `tree-sitter`-based options would add a dependency whose own Python-grammar
  support could lag behind new syntax.
- **Scope discipline:** v1 does not need to preserve formatting, comments, or
  perform source-to-source rewriting (there is no requirement to modify analyzed
  source), so the extra capabilities of `libcst`/`tree-sitter` are not needed and
  would only add unused surface area and dependency risk.

## Trade-offs Accepted

- `ast` discards comments and exact formatting of the analyzed source. This is
  acceptable because no FR/NFR requires preserving or reproducing the *analyzed*
  file's formatting — only extracting the FR-006 list of structural facts from it.
- `ast.parse` requires source that is syntactically valid Python for the running
  interpreter's grammar version; a file written for a much newer Python syntax
  than the running interpreter supports will fail to parse. This is treated as an
  "unsupported file" case under FR-013/FR-014 (reported and skipped, not fatal to
  the run), not a defect — no requirement guarantees support for arbitrary future
  syntax.
- Regular-expression scanning (option 4) was rejected outright: it cannot reliably
  determine nested scope, multi-line signatures, or decorators, and would risk
  silently fabricating or omitting information — a direct conflict with FR-012.

## Consequences

- The Python Source Parser component (Section 8 of `docs/architecture.md`) is built
  directly on `ast`, with one `try/except` boundary per file.
- Signature text for documentation is reconstructed with `ast.unparse()` on
  annotation/default-value sub-expressions, avoiding a hand-written unparser.

## Resolution (2026-09-24, remediation update — resolves design-review DR-006 and DR-007)

This ADR's original scope covered only the choice of parsing engine (`ast` itself).
`docs/design-review.md` raised two related gaps in how that engine's *inputs* and
*failure modes* were specified, not in the choice of `ast` itself, which the review
did not challenge:

- **DR-006 (source encoding):** the prior `docs/architecture.md` Section 8 wording
  hard-coded UTF-8 as the only recognized source encoding, which would mis-decode or
  reject a legitimately PEP-263-encoded (non-UTF-8) Python source file. Per explicit
  human decision, `docs/architecture.md` Section 8 point 1 now specifies use of the
  standard-library `tokenize.detect_encoding` function ahead of the read — the same
  mechanism CPython's own tokenizer uses — so PEP-263 encoding cookies are honored
  without adding a third-party dependency or material complexity. This is an
  addition to *how the source text is obtained* before `ast.parse()` is called; it
  does not change the decision to use `ast` as the parsing engine.
- **DR-007 (exception boundary too narrow):** the prior wording named only
  `SyntaxError` as the caught exception for the per-file parse boundary, which does
  not cover `RecursionError` (deeply nested but syntactically valid expressions) or
  `ValueError` (e.g., embedded null bytes), both of which `ast.parse()` can raise.
  `docs/architecture.md` Section 8 point 2 now names the full exception set
  (`SyntaxError`, `RecursionError`, `ValueError`, `UnicodeDecodeError`/`LookupError`,
  `OSError`) that the per-file boundary must catch, so FR-013's per-file isolation
  guarantee holds for any single-file failure mode, not only syntax errors.

Neither change reopens the Options/Decision in this ADR; `ast` remains the sole
parsing engine, and no alternative library is introduced.
