# ADR-0005: Output-Path Boundary-Check Algorithm

Status: Proposed (pending follow-up Design Review / Gate G2)
Date: 2026-09-24 (added under Change Control, remediating `docs/design-review.md` DR-001)

## Context

`docs/requirements.md` FR-016 (as amended, see its Section 12 Change Log) requires
that a user-configured `--output` value be restricted to a filename/sub-path within
`docs/generated/`, and that the tool must reject, with a clear error, any resolved
`--output` value that would fall outside `docs/generated/` (AC-015). ADR-0004
originally treated the marker-based ownership guard as the sole safety net for a
then-ambiguous FR-016; once FR-016 was clarified to require a hard boundary, the
architecture (`docs/architecture.md`, prior draft, Sections 11/13/17/21) asserted
that a "boundary check" existed but described only the desired outcome ("normalizes
... and verifies the normalized path lies inside the subtree"), not a concrete
mechanism.

`docs/design-review.md` DR-001 (BLOCKER) found this insufficient: several
superficially reasonable implementations of "join, normalize, verify" fail on real
edge cases — absolute-path join semantics (`pathlib`/`os.path.join` discard the base
when the right-hand operand is absolute), Windows drive-relative forms (`C:foo`,
not reported as absolute by `pathlib`, yet resolves against that drive's own cwd),
UNC paths (`\\server\share\...`), sibling-prefix confusion from a string-prefix
comparison (`docs/generated-evil/` vs `docs/generated/`), and symlinked or
not-yet-existing path components. A concrete algorithm was required before this
control could be considered implementable as specified, per the
`architecture-analysis` skill's Review Checklist ("is the design implementable as
described, or does it hand-wave a hard part?").

## Options Considered

1. **String-prefix comparison** (`str(candidate).startswith(str(base))`), with a
   pre-join rejection of absolute paths. Simple, but demonstrably unsound: it
   incorrectly accepts a sibling directory that merely shares a string prefix
   (e.g., `docs/generated-evil/x.md` shares the prefix `docs/generated` with
   `docs/generated/x.md`) unless a separator is manually appended and even then does
   not account for symlinks or `..` segments that a subsequent `resolve()` would
   reveal.
2. **Lexical normalization only** (e.g., `os.path.normpath`/`PurePath` operations,
   collapsing `..`/`.` segments without touching the filesystem), then a
   string/path-component comparison. Does not require the filesystem to exist, but
   cannot detect a symlink that points outside the boundary — a `docs/generated/api`
   symlink to `/etc` would lexically normalize to an in-bounds-looking path while
   physically pointing outside it.
3. **OS-level sandboxing (e.g., `chroot`, containers, restricted filesystem
   namespaces).** Would provide a strong guarantee but is not available
   cross-platform (no direct Windows equivalent), requires elevated privileges on
   POSIX systems, and is wildly disproportionate to a single-user, single-run CLI
   tool — directly conflicting with NFR-001 (cross-platform, no unnecessary
   OS-specific behavior) and the general scope-discipline principle of not adding
   infrastructure no requirement asks for.
4. **Reject-then-join-then-resolve-then-path-aware-containment-check** (the option
   detailed in `docs/architecture.md` Section 11.1): explicitly reject absolute,
   drive-qualified, UNC, and `..`-containing candidates before any join; join the
   validated-relative remainder onto the *resolved* real path of `docs/generated/`;
   resolve the joined result (following symlinks, tolerating non-existent leaf
   components); and perform the decisive containment check using
   `Path.is_relative_to()` — a path-object, separator-aware comparison — rather than
   a string operation.

## Decision

Option 4. The full, numbered algorithm is specified in `docs/architecture.md`
Section 11.1 and is treated as normative — a developer implementing FR-016 output
handling must follow it exactly, not invent an equivalent.

## Rationale

- **Correctness against every DR-001 edge case:** `Path.resolve()` on both the
  candidate and the `docs/generated/` root, followed by `is_relative_to()`, is
  correct for absolute-path confusion (rejected pre-join at step 2), Windows
  drive-relative/UNC forms (rejected pre-join at step 3, via `.drive` inspection —
  the specific gap `pathlib`'s `.is_absolute()` alone does not close), sibling-prefix
  confusion (path-component comparison in step 8 cannot be fooled by a shared string
  prefix), symlink escapes (step 7's `resolve()` follows symlinks to their real
  target before step 8 compares), and non-existent leaf paths (`resolve()`'s
  documented behavior of lexically normalizing the non-existent suffix while
  resolving the existing prefix against the real filesystem).
- **Defense-in-depth without relying on it for correctness:** the early rejection
  rules (steps 2–4) are not strictly necessary for correctness — step 8 alone would
  catch any escape — but they are kept because they produce clearer, more specific
  error messages and because layered checks reduce the blast radius of any single
  future implementation mistake in one layer.
- **No additional dependency:** every primitive used (`PureWindowsPath`,
  `PurePosixPath`, `Path.resolve()`, `Path.is_relative_to()`) is standard-library
  `pathlib`, consistent with CLAUDE.md's safe-dependency-usage rule and this
  project's existing stdlib-only stance (ADR-0001, ADR-0002).
- **Cross-platform correctness (NFR-001):** both `PureWindowsPath` and
  `PurePosixPath` interpretations of the candidate string are checked regardless of
  host OS, so the same malicious/misconfigured value is rejected identically whether
  the tool runs on Windows, Linux, or macOS — directly serving NFR-001's "equivalent
  behavior" intent, which DR-001 specifically flagged as under-addressed for this
  control.
- **Case-sensitivity (DR-009) falls out naturally:** because the containment check
  compares two paths that both went through the same `.resolve()` call against the
  same host filesystem, the comparison inherits that filesystem's actual
  case-sensitivity behavior without needing a separate, independently-specified
  case-handling rule that could disagree with the OS.

## Trade-offs Accepted

- **`resolve()` performs filesystem I/O** (it must stat existing path components to
  follow symlinks and determine the real path). This is a negligible cost for a
  single CLI invocation's single output-path validation and is not a concern under
  NFR-002 (no numeric performance SLA; small/medium repositories).
- **A deliberately symlinked `docs/generated/` directory is treated as
  authoritative** — if a developer has intentionally made `docs/generated` itself a
  symlink elsewhere, output is validated against wherever it actually resolves to,
  not against the symlink's apparent location. This is accepted as the correct,
  security-honest behavior (resolving consistently, not special-casing the root)
  rather than a limitation to work around.
- **This algorithm is hard to reverse once implemented and tested against it:**
  changing the comparison primitive later (e.g., swapping `is_relative_to()` for
  something else) would require re-validating every edge case above again. This is
  exactly the kind of significant, security-relevant, hard-to-reverse decision
  CLAUDE.md's Architecture Rules ask to be recorded as an ADR rather than left as an
  inline implementation note.

## Consequences

- `docs/architecture.md` Section 11.1 specifies this algorithm as the sole,
  normative implementation of the FR-016 boundary check; Sections 4.2, 13, 16, 21,
  and 22 all reference it rather than restating or re-deriving it.
- The Configuration Resolver (`config.py`) is the only component that runs this
  algorithm; it runs before any scanning begins (Section 11.4's restated processing
  order).
- `test_config.py` (added to the Section 5 package/test-tree structure and to
  Section 19's unit-test description under this remediation) unit-tests every step
  of this algorithm directly, independent of the Section 19 integration-level
  AC-015 fixtures that exercise the algorithm end-to-end through the CLI.
- This ADR does not reopen or contradict ADR-0004: ADR-0004's marker-based
  ownership guard remains a separate, later, defense-in-depth mechanism (see
  `docs/architecture.md` Section 11.2) operating only on paths this ADR's algorithm
  has already validated.
