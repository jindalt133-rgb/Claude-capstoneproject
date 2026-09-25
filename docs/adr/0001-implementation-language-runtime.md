# ADR-0001: Implementation Language and Runtime for the Tool Itself

Status: Proposed (pending Design Review / Gate G2)
Date: 2026-09-24

## Context

`docs/requirements.md` Section 7/8 explicitly defers the choice of implementation
language/runtime for the Automated Documentation Sync tool to the Architecture
phase. The requirements fix only the *analyzed* language (Python, FR-003) and the
following constraints that any implementation choice must satisfy:

- FR-001: CLI is the sole means of invocation.
- FR-003/FR-006: must statically analyze Python source files and extract structural
  information (modules, classes, functions, signatures, parameters, docstrings).
- FR-007/FR-008: must produce Markdown output under `docs/generated/`.
- NFR-001: must run on Windows, Linux, and macOS without introducing unnecessary
  OS-specific behavior.
- NFR-002: no numeric performance SLA; must be "suitable for normal small-to-medium
  Python repositories" and avoid obviously unnecessary repeated work.
- NFR-005: must be covered by an automated test suite.
- CLAUDE.md Quality/Security Rules: safe dependency usage, maintainability,
  testability.

## Options Considered

1. **Python 3 (standard library first)** — implement the tool in Python, using the
   built-in `ast` module to parse the Python files it analyzes.
2. **A compiled language (Go or Rust)** — distribute as a single cross-platform
   binary with no runtime dependency, but parse Python source using either a
   third-party Python-grammar library in that language or a hand-rolled parser.
3. **Node.js/TypeScript** — cross-platform runtime, but no built-in understanding of
   Python syntax; would require a third-party Python parser package.
4. **Shell scripting (POSIX sh/PowerShell)** — rejected outright: no viable
   structured-parsing capability for Python source, poor testability, and would
   require OS-specific scripts, conflicting with NFR-001.

## Decision

Implement the tool in **Python 3, minimum supported version 3.11+**, using the
standard-library `ast` module as the parsing engine (see ADR-0002).

## Rationale

- **NFR-001 (cross-platform):** CPython runs unmodified on Windows, Linux, and
  macOS; no OS-specific branches are needed for core logic. Path handling uses
  `pathlib`, which normalizes cross-platform differences.
- **FR-003/FR-006 (Python analysis):** Python ships a first-party, always-in-sync
  parser for its own grammar (`ast`). No other language has an equivalently
  authoritative, zero-dependency Python parser. Using Python to parse Python
  eliminates an entire class of "parser drift" risk (the parser silently falling
  behind newer Python syntax).
- **NFR-002 (no strict performance SLA, small/medium repos):** CPython's AST parsing
  throughput is more than sufficient for the stated workload; a compiled language's
  raw speed advantage is not required by any approved requirement.
- **CLAUDE.md Security/Quality Rules (safe dependency usage):** Option 1 needs no
  third-party parsing dependency at all (stdlib `ast`), minimizing supply-chain
  exposure. Options 2 and 3 would require depending on a third-party Python-grammar
  package that is not the reference implementation.
- **NFR-005 (testability):** Python has a mature, widely-adopted test ecosystem
  (`pytest`), directly satisfying the testing-architecture requirement.
- **Version floor (3.11+):** chosen for current upstream support status (avoids
  targeting an end-of-life interpreter) and to allow use of stable stdlib AST
  helpers (e.g., `ast.unparse`, available since 3.9) without dependency risk. This
  is an engineering-hygiene choice, not a new product requirement.

## Trade-offs Accepted

- **Distribution:** Python is not a single self-contained binary; end users need a
  Python interpreter available (typically already true for a tool analyzing Python
  repositories) or must use a packaging step (e.g., `pipx`, a zipapp, or a future
  frozen binary) — deferred to Implementation Planning if desired, not required by
  any FR/NFR.
- **Raw performance:** A compiled implementation would likely be faster on very
  large codebases, but NFR-002 explicitly sets no numeric SLA and scopes v1 to
  small/medium repositories, so this is an acceptable trade-off.
- **Reversibility:** This decision is hard to reverse once implementation begins —
  the entire codebase, its parsing approach, and its test suite would need to be
  rewritten to change runtime. This is why it is recorded as an ADR rather than a
  routine implementation note.

## Consequences

- All subsequent architecture and implementation-planning decisions assume a Python
  3.11+ codebase.
- The CLI can be exposed either as an installable console-script entry point or via
  `python -m <package>`; exact packaging mechanics belong to Implementation
  Planning, not Architecture.
