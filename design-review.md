# Design Review: Automated Documentation Sync Architecture (v1)

Reviewer: `design-reviewer` agent
Reviewed artifacts: `docs/architecture.md`, `docs/adr/0001-implementation-language-runtime.md`,
`docs/adr/0002-python-parsing-approach.md`, `docs/adr/0003-change-detection-strategy.md`,
`docs/adr/0004-generated-output-ownership.md`, against `docs/requirements.md` (Gate G1,
amended once for FR-016) and `docs/user-story.md`.
Methodology: `.claude/skills/architecture-analysis/SKILL.md` Analysis Framework and
Review Checklist.

Gate under evaluation: **G2** (`docs/architecture.md` must pass this review with no
unresolved blocking findings before Implementation Planning may start).

This review does not modify `requirements.md`, `architecture.md`, or any ADR. Findings
are advisory to the human and to the `architect` agent for a follow-up revision.

---

## Summary of Findings

| Severity | Count |
|---|---|
| BLOCKER | 1 |
| HIGH | 3 |
| MEDIUM | 3 |
| LOW | 2 |
| **Total** | **9** |

---

## Findings

### DR-001 — BLOCKER
**Area:** Generated-output ownership protection / Security risks / Cross-platform behavior
**Affected:** `docs/architecture.md` §11, §13, §17, §21; `docs/adr/0004-generated-output-ownership.md` (Resolution note)
**Related requirements:** FR-016, FR-009, AC-015, NFR-001

**Problem.** The task instructions specifically call for scrutinizing the FR-016
output-path boundary check rather than accepting it because it was "recently
resolved." On that scrutiny, the check is asserted, not specified. Four places
in the architecture (§11 twice, §13, §17, §21) all use the same phrasing —
"normalizes ... and verifies the normalized path still lies inside the
`docs/generated/` subtree" — without ever committing to *how* that verification
is performed. This matters because several superficially reasonable
implementations of "join, normalize, verify" fail on real edge cases:

- **Absolute-path join semantics.** §13 says the resolver "joins [`--output`]
  onto `docs/generated/`." In `pathlib` (and `os.path.join`), joining a base
  path with an absolute right-hand operand *discards the base entirely* —
  `Path("docs/generated") / "/etc/passwd"` yields `/etc/passwd`, not
  `docs/generated/etc/passwd`. The architecture never states whether an
  absolute `--output` value is rejected *before* the join (which would be
  correct and simple) or is allowed to reach the join and rely on the
  *subsequent* "lies inside" check to catch it. The document's prose ("not an
  arbitrary absolute path") describes the desired outcome but not the
  mechanism that guarantees it.
- **Windows drive-relative and UNC forms.** NFR-001 requires Windows support,
  and this is exactly the kind of check where Windows path semantics differ
  from POSIX in security-relevant ways: `pathlib.PureWindowsPath("C:foo")` is
  *not* considered absolute, yet resolves relative to that drive's own current
  directory (which need not be anywhere near the process cwd or the project
  root); UNC paths (`\\server\share\...`) and multiple drive letters are also
  unaddressed. None of these Windows-specific absolute/relative forms are
  discussed anywhere in §11/13/17/18/21, despite NFR-001 explicitly scoping
  Windows in.
- **Unspecified comparison primitive.** "Verifies the normalized path still
  lies inside the subtree" could be implemented safely (e.g.
  `resolved_output.is_relative_to(resolved_generated_root)` after
  `Path.resolve()` on both sides) or unsafely (e.g. a string
  `startswith(str(base))` check, which incorrectly accepts a sibling like
  `docs/generated-evil/x.md` because it shares a string prefix without a path
  separator boundary). The architecture does not commit to one, so
  "implementable as described" cannot be confirmed — this is exactly the kind
  of hand-waved hard part the review checklist calls out.
- **Symlinked intermediate directories / non-existent leaf path.** §11 claims
  the check resolves "symlink-style traversal," which correctly implies
  intent to follow symlinks (e.g. via `Path.resolve()`). But the *target*
  output file typically does not exist yet at check time (it is about to be
  created), and `docs/generated/` itself — or an intermediate sub-path
  component supplied via FR-016's sub-path configurability — could itself be
  a symlink pointing outside the project tree. Python's `resolve()` behavior
  on a path whose leaf doesn't exist but whose parents do (some of which may
  be symlinks) needs to be explicitly designed for, not assumed to "just
  work."

**Impact.** This is the single hard security control introduced under change
control specifically to convert FR-016 from a soft, ambiguous requirement into
a hard boundary (AC-015: "the system does not write generated documentation
[outside `docs/generated/`]... generated output never appears outside
`docs/generated/`"). If the eventual implementation picks any of the unsafe
variants above, a misconfigured or adversarially-crafted `--output` value
could write outside `docs/generated/`, which is precisely the outcome AC-015
exists to prevent, and would also defeat FR-009 (never touch manually
maintained files) for the reason ADR-0004 originally raised.

**Recommended resolution.** Before this can pass Gate G2, the architecture (or,
if the human treats this as implementation-level detail, the impl-plan) must
state a concrete algorithm, not a description of the desired property, e.g.:
(1) reject any `--output` value that `PurePath.is_absolute()` reports true for,
*and* any value containing a drive specifier, *before* joining; (2) join the
remainder onto the resolved-real-path of `docs/generated/`; (3) resolve the
result with symlinks followed; (4) compare using a separator-aware
"is-relative-to" check against the resolved-real-path of `docs/generated/`,
not a string-prefix check; (5) explicitly define behavior when `docs/generated/`
itself does not yet exist (resolve as far as it can and validate the
non-existent remainder lexically) and when it is, or contains, a symlink.

## Resolution

**Disposition: RESOLVED.**

`docs/architecture.md` Section 11.1 now specifies a concrete, 12-step algorithm
for the FR-016 boundary check, matching (and slightly extending) the recommended
resolution above: it explicitly rejects absolute paths via both
`PureWindowsPath`/`PurePosixPath` interpretations (step 2, checked regardless of
host OS for NFR-001 consistency), rejects Windows drive-qualified/drive-relative
forms and UNC paths via `.drive` inspection plus a `\\`/`//` prefix check (step
3 — this specifically closes the `C:foo` drive-relative gap this finding named),
rejects `..` components pre-join as defense-in-depth (step 4), computes the real
root and joins onto it (steps 5–6), resolves with symlinks followed and
non-existent leaf components tolerated (step 7), and performs the decisive
containment check via `Path.is_relative_to()` — a path-object, separator-aware
comparison, never a string-prefix check (step 8). Symlink and non-existent-path
behavior are explicitly defined (steps 7, 10). A new ADR, `docs/adr/0005-output-path-boundary-algorithm.md`,
records this as a significant, hard-to-reverse security decision with options
considered (including the rejected string-prefix and lexical-only alternatives
this finding warned against) and trade-offs accepted.

**What changed:** `docs/architecture.md` Section 11 was restructured into
Section 11.1 (this algorithm), 11.2 (ownership guard, see DR-003), 11.3
(directory creation, see DR-008), and 11.4 (summary/default-path behavior);
Sections 4.2, 13, 17, and 21 were updated to reference the concrete algorithm
instead of restating the prior vague "normalizes and verifies" language. New
file: `docs/adr/0005-output-path-boundary-algorithm.md`.

**Rationale for disposition:** the algorithm is now specified precisely enough
that a developer does not need to invent security behavior — every edge case
this finding named (absolute-path join semantics, Windows drive-relative/UNC
forms, string-prefix vs. path-aware comparison, symlinked/non-existent paths)
has an explicit, numbered step addressing it.

---

### DR-002 — HIGH
**Area:** Testability
**Affected:** `docs/architecture.md` §19 (Testing Architecture)
**Related requirements:** AC-015 (FR-016)

**Problem.** §19 enumerates integration-test fixtures for every acceptance
criterion introduced or amended in `requirements.md` **except** AC-015 — the
negative case added specifically for the FR-016 change-control amendment
("given a user-specified output path that resolves outside `docs/generated/`,
the system does not write ... and rejects the configuration with a clear
error"). The bullet list covers AC-001–002, AC-003, AC-004/005, AC-006/007,
AC-008, AC-009/010, AC-011, AC-012, and separately AC-013/AC-014, but there is
no fixture or assertion described for AC-015 anywhere in §19.

**Impact.** AC-015 is the acceptance criterion for the exact control flagged as
unsound in DR-001. Its absence from the test architecture means the one
requirement that most needs an explicit escape-attempt regression test (e.g.
`--output ../../etc/passwd`, `--output /etc/passwd`, a Windows drive-letter
path, a symlink-escape fixture) currently has no committed test coverage plan,
which also violates NFR-005's intent ("automated test suite shall cover ...
the important failure scenarios") for this specific, newly hardened control.

**Recommended resolution.** Add an explicit AC-015 fixture/test bullet to §19,
covering at minimum: an absolute path, a `..`-escaping relative path, and (if
DR-001's Windows/symlink edge cases are adopted) a drive-letter/UNC path and a
symlink-escape case.

## Resolution

**Disposition: RESOLVED.**

`docs/architecture.md` Section 19 now includes an explicit AC-015 bullet
covering, at minimum: a `..`-escaping relative path, a nested-traversal path, an
absolute path (POSIX and Windows forms), a sibling-prefix path
(`docs/generated-evil/`, explicitly called out as a check on path-aware vs.
string-prefix containment), a Windows drive-qualified/drive-relative path, a
UNC path, and — where the test platform supports it — a symlink-escape
fixture. A positive-control valid nested path is also specified so the negative
tests are not vacuously passing. In addition, Section 5's package structure and
Section 19's unit-test description now include a new `tests/unit/test_config.py`
module that unit-tests the Section 11.1 algorithm's individual steps directly
(this was not requested verbatim by the finding but follows directly from
having a concrete algorithm to unit-test, per NFR-005).

**What changed:** `docs/architecture.md` Section 19 (Testing Architecture),
Section 5 (package/test-tree structure).

**Rationale for disposition:** every category the finding named is now present
in the test architecture, traced explicitly to FR-016/AC-015.

---

### DR-003 — HIGH
**Area:** Component responsibilities and boundaries / Conflicts between requirements, architecture, and ADRs
**Affected:** `docs/architecture.md` §4.2, §4.10, §11, §13, §16
**Related requirements:** FR-009, FR-016

**Problem.** The architecture gives two different, mutually inconsistent
accounts of *which component* enforces the ADR-0004 ownership-marker guard and
*when* in the pipeline it runs:

- §4.2 (Configuration Resolver): "validates the requested output path against
  the ownership guard rules ... **before any scanning begins**."
- §13: "Only after the boundary check passes is the path additionally
  validated against the ownership guard (Section 11, ADR-0004). This
  fail-fast ordering — boundary check, then ownership guard, **then
  scanning** — means a misconfigured `--output` value never results in
  scanning the source tree..."
- §16: lists "the resolved output path fails the FR-016 output-path boundary
  check or the ownership guard" together as one of the two run-level,
  pre-scan-equivalent fatal conditions.

versus

- §4.10 (Output Writer): "enforces FR-009's ownership guard (ADR-0004):
  **before writing**, checks whether the target path is new or already
  carries this tool's header banner; if an unrecognized file already exists
  at that path, aborts the write."
- §11, point 2: "the Output Writer only writes to a target path that is
  either new, or already carries this tool's own header banner ... from a
  prior run."

These describe two different pipeline stages: the ownership-marker check
either happens once, up front, before the Scanner runs at all (§4.2/§13/§16),
or it happens at the very end of the pipeline, immediately before the actual
file write, after scanning/parsing/rendering have already completed (§4.10/§11
pt. 2). The document never reconciles these, and it matters beyond
terminology: if checked early, the check result can go stale by the time the
write actually happens (the file at that path could be created or deleted in
the interim by something else on the filesystem — a TOCTOU window ADR-0004
itself already accepts for a *different* reason but does not mention here);
if checked only at write time, then §13's claim that a misconfigured output
value "never results in scanning the source tree" is false for the
ownership-guard half of that sentence (only the boundary check half would be
pre-scan).

**Impact.** An implementation planner or developer following §4.2/§13 literally
would build the ownership check into the Configuration Resolver; one following
§4.10/§11 literally would build it into the Output Writer. Only one of these
is consistent with the "fail-fast, nothing scanned on misconfiguration"
guarantee the document repeatedly claims. This is a genuine internal
contradiction, not a stylistic nit — it affects both correctness of the
fail-fast claim and where test doubles/unit tests should be targeted.

**Recommended resolution.** Pick one: either (a) the ownership-marker check is
purely mechanical file-existence/marker inspection performed once by the
Configuration Resolver before scanning (in which case §4.10/§11 pt. 2 must be
reworded to say the Output Writer trusts the Resolver's prior validation and
only re-verifies defensively/atomically at write time to close the TOCTOU
window), or (b) the check genuinely belongs to the Output Writer at write
time (in which case §4.2/§13/§16's "before any scanning begins" / "never
results in scanning" claims must be corrected to say the boundary check alone
is pre-scan, while the ownership guard is applied at write time after a
render that may turn out to be discarded).

## Resolution

**Disposition: RESOLVED**, via option (b) named in the recommended resolution.

Per the human's explicit remediation instruction, the split is: the FR-016
**boundary check** runs in the Configuration Resolver, pre-scan (Section 11.1);
the FR-009 **ownership-marker check** runs in the Output Writer, immediately
before the write (Section 11.2), because it depends on inspecting the actual
target file's contents, which are not available to inspect any earlier.
`docs/architecture.md` Section 4.2 now explicitly states the Configuration
Resolver performs *only* the boundary check and does not perform the
ownership-marker check. Section 4.10 now states the Output Writer performs the
ownership-marker check, sequenced after directory creation (Section 11.3) and
immediately before the atomic write. Section 13's "fail-fast ordering" prose
was corrected to state that only the boundary check is pre-scan; the ownership
guard is evaluated later and can reject a configuration only after
scanning/rendering have already run. Section 16 now lists the two fatal
conditions at their correct pipeline stages (pre-scan vs. at write time) instead
of lumping them together. Section 21 and the Section 22 traceability table were
updated to match. `docs/adr/0004-generated-output-ownership.md` gained a
"Further Resolution" dated note stating the same split and correcting the
contradiction, without altering its original Decision/Rationale/Trade-offs or
its earlier (2026-09-24) Resolution note.

**What changed:** `docs/architecture.md` Sections 4.2, 4.10, 11 (restructured
into 11.1/11.2/11.3/11.4), 13, 16, 21, 22; `docs/adr/0004-generated-output-ownership.md`
("Further Resolution" section).

**Rationale for disposition:** the contradiction identified by this finding is
real and is now removed — every section that discusses the ownership guard's
timing agrees it runs in the Output Writer, at write time, and every section
that discusses the boundary check's timing agrees it runs in the Configuration
Resolver, pre-scan.

---

### DR-004 — HIGH
**Area:** Sensitive-information protection
**Affected:** `docs/architecture.md` §4.7, §9, §15
**Related requirements:** FR-015, NFR-003

**Problem.** §4.7 (Sensitive-Value Filter) states it inspects "string-valued
literals captured in the model (e.g., default parameter values, module-level
constant values if captured, docstring text)." Two problems:

1. **Decorators are not listed as inspected content, but are rendered
   output.** The Documentation Model (§9) explicitly includes
   `ClassDoc.decorators` and `FunctionDoc.decorators` as `str[]` fields, and
   §10 (Markdown Generation) renders "a fenced code block showing the
   reconstructed signature of each method" — decorators are part of a
   function/method's reconstructed signature and therefore part of the
   rendered output. A hardcoded secret passed as a decorator argument (e.g.
   `@requires_api_key("sk-live-abc123...")`, `@cache(dsn="postgres://user:pw@host/db")`)
   would be captured into the model via `ast.unparse` (per §8 pt. 3, decorator
   lists are collected) and rendered into the final Markdown, but §4.7/§15
   never name decorators as a category the filter scans. This is a concrete,
   plausible leak path directly contradicting FR-015 ("shall avoid
   intentionally including detected sensitive values ... in generated
   documentation").
2. **"Module-level constant values if captured" refers to a field that does
   not exist.** §9's `ModuleDoc` has exactly four fields: `path`, `docstring`,
   `classes`, `functions`, `errors`. There is no module-level-constants field
   anywhere in the model, and FR-006 itself does not ask for module-level
   constant extraction. §4.7's own text is therefore internally inconsistent
   with §9 — it describes filtering something the model was never designed to
   capture.

**Impact.** (1) is a real, requirement-violating gap in the filter's coverage
as specified — not merely an omission of detail, since decorators are
demonstrably part of the rendered surface. (2) is a smaller internal
consistency defect but suggests the sensitive-value coverage list in §4.7/§15
was not cross-checked against the actual model shape in §9.

**Recommended resolution.** Either extend §4.7/§15 to explicitly include
decorator argument text as filtered content (and confirm the filter runs on
the already-`ast.unparse`'d decorator strings before they reach the Renderer,
consistent with the "runs before hashing/rendering" ordering already
described), or explain why decorator arguments are considered out of scope
(no such rationale currently exists). Remove or correct the "module-level
constant values if captured" reference to match §9's actual model, or add a
constants field to §9 if module-level constants are meant to be captured
after all — as written, the two sections disagree.

## Resolution

**Disposition: RESOLVED.**

Per explicit human decision (signature scope includes decorators as part of
generated documentation), decorators are confirmed in-scope for rendering, and
therefore in-scope for the Sensitive-Value Filter. `docs/architecture.md`
Sections 4.7 and 15 now explicitly name decorator text — including
string-literal arguments passed to a decorator call — as filtered content,
scanned identically to parameter defaults/annotations/docstrings, since all of
these reach the filter as `ast.unparse`'d text. The "module-level constant
values if captured" phrase has been removed from §4.7/§15 (not replaced with a
new field): `docs/architecture.md` Section 9's `ModuleDoc` has no
module-level-constant field, `docs/requirements.md` FR-006 does not request
module-level constant extraction, and no field was added, per the explicit
instruction not to introduce unnecessary scope.

**What changed:** `docs/architecture.md` Sections 4.7, 15.

**Rationale for disposition:** the concrete leak path this finding identified
(a secret passed as a decorator-call argument) is now covered by the filter's
stated scope, and the internal inconsistency between §4.7's prose and §9's
actual model fields has been removed by correcting the prose rather than
inventing a new model field.

---

### DR-005 — MEDIUM
**Area:** Change-detection strategy / Missing architecture decisions
**Affected:** `docs/architecture.md` §12; `docs/adr/0003-change-detection-strategy.md`
**Related requirements:** FR-010, FR-011, NFR-002

**Problem.** §12 describes change detection at *per-file* granularity: "If
hashes match for **all** files that contributed to the previous output, skips
... If any file's hash differs, or a file is new, or a previously-included
file was deleted/excluded, triggers a full re-render" — this wording requires
tracking a *set* of (file identity → hash) pairs from the previous run, so
that additions, deletions, and per-file changes can each be individually
detected. But ADR-0003's Decision and Consequences describe storage as **a
single** embedded hash (plus banner) in one HTML comment at the top of the one
generated Markdown file: "embed the resulting hash ... as an HTML comment,"
"the Change Detector reads that header back." No data structure is specified
for representing N per-file hashes (and their associated file identities) inside
what is described throughout as a single scalar hash value in a single
comment block.

A single combined hash (e.g., over the concatenation of all per-file
canonical serializations in a stable order) *can* still correctly detect "did
anything relevant change" in aggregate — including additions/removals if the
serialization includes file identity — but that is a different, coarser
design than the per-file comparison §12 describes, and the document does not
say which of the two it actually means. This is exactly the kind of
"comparison unit vs. storage format" gap the review checklist flags as
hand-waving a hard part when a design claims per-item granularity without
specifying the storage shape that would make that granularity possible.

**Impact.** Low-to-moderate implementability risk: whoever writes the
impl-plan/code has to invent a header-comment micro-format (e.g., a JSON
blob mapping file path → hash, embedded in the HTML comment) that isn't
specified anywhere, and different reasonable choices here have different
correctness properties (e.g., a single aggregate hash cannot report *which*
file changed for diagnostic purposes, though the requirements don't actually
ask for that — only for correct skip/regenerate behavior, which either
approach can satisfy).

**Recommended resolution.** State explicitly whether change detection is (a)
one aggregate hash over an ordered, file-identity-inclusive serialization of
all contributing files, or (b) a per-file hash table, and if (b), specify the
embedded format (e.g., `<!-- docsync:v1 sha256={"a/b.py": "...", ...} -->`).

## Resolution

**Disposition: RESOLVED**, via option (b) as the finding's own suggested
example format.

`docs/architecture.md` Section 12 now explicitly states storage is a per-file
hash table (not a single aggregate hash), embedded as a single-line JSON object
in the header comment, keyed by each file's path relative to the source root,
with sorted-key serialization for determinism — matching almost exactly the
finding's own suggested format. `docs/adr/0003-change-detection-strategy.md`
gained a dated "Resolution" section making this concrete, without altering its
original Decision (per-source-file model hash as the comparison unit; embedded
header-comment storage) or Rationale/Trade-offs.

**What changed:** `docs/architecture.md` Section 12; `docs/adr/0003-change-detection-strategy.md`
("Resolution" section); Section 10's header-banner description updated to say
"per-file change-detection hash table" instead of "the ... hash."

**Rationale for disposition:** the storage shape is now specified precisely
enough that a developer does not need to invent the header-comment
micro-format, closing the "comparison unit vs. storage format" gap this finding
identified.

---

### DR-006 — MEDIUM
**Area:** Python AST parsing approach / Incorrect or unsupported assumptions
**Affected:** `docs/architecture.md` §8, point 1
**Related requirements:** FR-003, FR-012, FR-013

**Problem.** §8 point 1 states the Parser "reads the file as text (UTF-8,
replacing/reporting on decode errors rather than crashing the whole run)."
This hard-codes UTF-8 as the only recognized source encoding. Real Python
source files may declare a different encoding via a PEP 263 encoding cookie
(`# -*- coding: <name> -*-` on line 1 or 2), and such a file is fully valid,
parseable Python source under CPython's own rules — CPython's own tokenizer
uses `tokenize.detect_encoding` (or equivalent) rather than assuming UTF-8. A
file that is legitimately encoded (e.g. `latin-1`) with a correct coding
cookie would, under the architecture's stated approach, either be mis-decoded
(producing corrupted docstring/text content silently, which risks fabricating
"decoded" text FR-012 says must instead be reported as unavailable) or
reported as a decode error / unsupported file — despite being a perfectly
valid, analyzable Python file with respect to FR-003.

**Impact.** Moderate correctness risk against FR-003 ("analyze Python source
files") for the (admittedly less common today, but still legal) non-UTF-8
source case; more importantly it's an unstated, not-obviously-correct
assumption baked into a numbered design step, which the review checklist
flags as needing to be explicit rather than silently assumed.

**Recommended resolution.** Either explicitly scope v1 to UTF-8-only source
files as an accepted limitation (a genuine, defensible product decision, but
one that should be stated as a decision/constraint rather than embedded as an
implementation detail), or specify use of `tokenize.detect_encoding`/PEP
263-aware decoding before falling back to a decode-error report.

## Resolution

**Disposition: RESOLVED**, via the finding's second option.

Per explicit human decision — do not arbitrarily restrict v1 to UTF-8-only if a
standard, low-complexity mechanism exists — `docs/architecture.md` Section 8
point 1 now specifies use of the standard-library `tokenize.detect_encoding`
function ahead of the file read, honoring PEP 263 encoding cookies the same way
CPython's own tokenizer does, with UTF-8 remaining the default when no cookie
is present. This adds no third-party dependency (confirmed low-complexity,
stdlib-only) and is added to Section 2's technology-stack table.
`docs/adr/0002-python-parsing-approach.md` gained a dated "Resolution" section
recording this, without reopening its original engine choice (`ast`).

**What changed:** `docs/architecture.md` Sections 2, 8 (point 1), 23 (assumptions
list updated to state this as a confirmed decision rather than a silent
assumption); `docs/adr/0002-python-parsing-approach.md` ("Resolution" section).

**Rationale for disposition:** the finding's own stated preference (given the
human's decision criteria) — respecting PEP 263 via the standard mechanism
rather than silently assuming UTF-8 — was determined to be low-complexity and
was incorporated, closing the correctness risk against FR-003/FR-012 the finding
identified.

---

### DR-007 — MEDIUM
**Area:** Error handling and partial-failure isolation
**Affected:** `docs/architecture.md` §8 point 2, §16
**Related requirements:** FR-013, FR-014

**Problem.** The per-file exception boundary is described narrowly: "A
`SyntaxError` here is caught and converted into a structured per-file error
... then the loop continues with the next file" (§8 pt. 2), and §16's
structured-error discussion likewise frames per-file failure as "a single
file that fails to parse, decode, or otherwise be analyzed," without naming
which exception types the try/except boundary actually spans. `ast.parse()`
can also raise `RecursionError` on pathologically deeply-nested (but
syntactically valid) expressions, and `ValueError` on certain malformed input
(e.g. embedded null bytes) — neither of which is a `SyntaxError`. If the
implementation follows the letter of §8 pt. 2 and catches only `SyntaxError`
(the only exception type named anywhere in the document for this boundary), a
single pathological-but-technically-present file could raise an uncaught
exception that propagates out of the per-file loop and aborts the entire run
— directly violating FR-013's "one invalid file does not block processing of
other valid files."

**Impact.** Moderate — this is a plausible, not merely theoretical, failure
mode (deeply nested list/dict literals or expressions are a known way to
trigger `RecursionError` in `ast.parse`), and it undermines the specific
guarantee (FR-013) that this component exists to satisfy.

**Recommended resolution.** Broaden the documented exception boundary to name
the actual set of exceptions the per-file try/except must catch (at minimum
`SyntaxError`, `RecursionError`, `ValueError`, `UnicodeDecodeError`, and OS-level
errors), or wrap in a broader `except Exception` boundary at the per-file
level with justification, so FR-013's guarantee holds for any single-file
failure mode, not only syntax errors.

## Resolution

**Disposition: RESOLVED**, via the finding's first option (named exception set,
not a blanket `except Exception`).

`docs/architecture.md` §8 point 2 now names the full exception boundary
explicitly: `SyntaxError`, `RecursionError`, `ValueError`,
`UnicodeDecodeError`/`LookupError` (the latter covering an unrecognized/unsupported
codec name reported by a PEP 263 cookie once DR-006's `tokenize.detect_encoding`
step is in play), and `OSError` (unreadable file at read time). §16's structured
per-file error description now cross-references §8 point 2 as the authoritative
statement of this set rather than re-describing it loosely. `docs/adr/0002-python-parsing-approach.md`
gained a dated "Resolution" section recording the same broadened set, without
reopening the ADR's original engine choice.

**What changed:** `docs/architecture.md` §8 (point 2), §16;
`docs/adr/0002-python-parsing-approach.md` ("Resolution" section).

**Rationale for disposition:** naming the exact exception set (rather than a
catch-all) keeps the boundary auditable — a developer can verify each named
exception is handled deliberately — while still closing the FR-013 gap the
finding identified (an uncaught `RecursionError`/`ValueError` aborting the whole
run).

---

### DR-008 — LOW
**Area:** Missing architecture decisions
**Affected:** `docs/architecture.md` §11, §13 (Output Writer / Configuration Resolver)
**Related requirements:** FR-008, FR-016

**Problem.** No section states whether the tool creates `docs/generated/`
(and any FR-016 sub-path parent directories) when it does not already exist,
versus treating a missing directory as an error. FR-008 implies writing under
`docs/generated/` by default, which in a fresh repository will very commonly
not exist yet on a first run.

**Impact.** Low — this is a small, easily-decided implementation detail, but
its absence means a developer could reasonably implement either behavior, and
"first run in a fresh repository" is explicitly called out elsewhere (§11) as
an important, common case ("always safe on a first run in a fresh
repository"), so the directory-creation behavior deserves at least one
sentence.

**Recommended resolution.** State that the Output Writer creates
`docs/generated/` and any needed sub-directories under it if missing (this is
consistent with FR-016 sub-path configurability already implying nested
paths may need to exist), while still applying the DR-001 boundary check
first.

## Resolution

**Disposition: RESOLVED**, exactly as recommended.

`docs/architecture.md` new §11.3 ("Directory Creation") states the Output
Writer creates `docs/generated/` and any needed sub-directories via
`mkdir(parents=True, exist_ok=True)`, applied only to a target path that has
already passed the §11.1 boundary check — never to a raw, unvalidated path —
and that this happens after §11.1 and before the §11.2 ownership-marker check.
`docs/adr/0004-generated-output-ownership.md`'s new "Further Resolution"
section cross-references this same ordering.

**What changed:** `docs/architecture.md` §11.3, §22 (FR-008/FR-016
traceability rows); `docs/adr/0004-generated-output-ownership.md` ("Further
Resolution" section).

**Rationale for disposition:** this closes the gap with a single, explicit
sentence-level decision (create if missing, only post-validation) rather than
leaving the behavior to individual developer judgment, and it is fully
consistent with — not in tension with — the DR-001 algorithm's own handling of
non-existent `docs/generated/` during `resolve()`.

---

### DR-009 — LOW
**Area:** Cross-platform behavior
**Affected:** `docs/architecture.md` §11, §13, §18
**Related requirements:** NFR-001, FR-016

**Problem.** §18 discusses case-sensitivity only for FR-004's default
directory-name exclusion matching ("should match names case-sensitively for
portability of behavior"). It does not address whether the FR-016
boundary-check comparison ("lies inside the `docs/generated/` subtree") is
case-sensitive or case-insensitive, which matters because the answer differs
by platform filesystem behavior (case-sensitive on Linux, typically
case-insensitive on Windows/macOS by default).

**Impact.** Low — a case mismatch cannot itself be used to escape
`docs/generated/` (it would at most cause an equivalent, in-bounds path to be
spuriously accepted or rejected), so this does not compound DR-001's severity,
but it is a real gap in "equivalent behavior across Windows/Linux/macOS"
consistency (NFR-001's intent) that §18 addresses for exclusions but not for
this comparison.

**Recommended resolution.** State that the boundary-check comparison should be
performed in a platform-appropriate case-sensitivity mode (e.g., matching the
resolved filesystem's actual case-sensitivity, or simply normalizing to a
single case for the comparison consistently on all platforms) so behavior is
predictable rather than incidental.

## Resolution

**Disposition: RESOLVED**, via the finding's first option (match the resolved
filesystem's actual case-sensitivity, not a separate normalization rule).

`docs/architecture.md` §11.1 step 9 now states explicitly that the boundary
check's containment comparison (`is_relative_to()` on two `.resolve()`d paths)
inherits whatever case-sensitivity the host filesystem itself exhibits,
because both the candidate and the `docs/generated/` root are resolved through
the identical OS-level call before comparison — there is no independent,
hand-rolled case-folding step that could disagree with the OS. §18 gained a
new bullet explicitly distinguishing this FR-016 boundary-check
case-sensitivity question from the pre-existing FR-004 exclusion-matching
case-sensitivity discussion, so the two are not conflated.
`docs/adr/0005-output-path-boundary-algorithm.md`'s Rationale section records
this as a natural consequence of the algorithm choice, not a separate design
decision requiring its own trade-off analysis.

**What changed:** `docs/architecture.md` §11.1 (step 9), §18;
`docs/adr/0005-output-path-boundary-algorithm.md` (Rationale).

**Rationale for disposition:** as the finding itself notes, a case mismatch
cannot be used to escape the boundary — it can only cause a spurious accept/reject
of an otherwise in-bounds path — so inheriting OS-native behavior (rather than
introducing an independent cross-platform normalization rule no requirement
asks for) is the simplest resolution consistent with NFR-001's "equivalent
behavior" intent and with not inventing behavior beyond what §11.1's
algorithm already does.

---

## Areas Reviewed With No Findings

The following review areas were examined and no issues were identified beyond
what is already captured above:

- **Coverage of all FRs and NFRs** — §22's forward coverage table and reverse
  (scope-creep) check both hold up; every FR-001–016 and NFR-001–005 has at
  least one covering component, and every component in §3 traces to at least
  one requirement.
- **Requirement-to-component traceability** — traceability entries in §22 are
  accurate against the component responsibilities described in §4, aside from
  the DR-003 timing/ownership conflict already noted.
- **Technology/runtime decision** — ADR-0001's options, decision, and
  trade-offs are honestly stated (distribution and raw-performance downsides
  are explicitly named, not glossed over) and are traceable to specific
  requirement IDs rather than convenience.
- **CLI boundaries** — FR-001's "sole means of invocation" is respected; the
  Pipeline Orchestrator's internal reuse as a library function is reasonably
  distinguished from a second public interface.
- **Configuration/exclusion design** — FR-004/FR-005 handling is sound, and
  the gitignore-style-glob assumption is properly flagged in §23 for Design
  Review confirmation rather than silently treated as settled.
- **Dependency safety** — stdlib-only runtime footprint plus dev-only pytest
  is well justified and consistent with CLAUDE.md's safe-dependency-usage
  rule; no unnecessary or risky dependency is introduced.
- **Unnecessary complexity** — the two-layer defense (boundary check +
  ownership guard) is justified as intentional defense-in-depth rather than
  redundant complexity, and the full-re-render-on-any-change decision (§12) is
  honestly justified against NFR-002's actual wording rather than
  over-engineered into partial patching that no requirement asked for.
- **Maintainability** — component decomposition is otherwise single-purpose
  and testable in isolation, aside from the Configuration Resolver's
  overloaded responsibility implicated in DR-003.

---

## Required Architecture Changes Before This Can Pass

Gate G2 requires no unresolved **blocking** findings. At minimum, before this
architecture can proceed to Implementation Planning:

1. **DR-001 (BLOCKER)** must be resolved: the architecture must specify a
   concrete, escape-proof algorithm for the FR-016 output-path boundary check,
   addressing absolute-path join semantics, Windows drive-relative/UNC forms,
   a safe (separator-aware, post-resolve) containment comparison, and
   symlinked/non-existent-path handling.
2. **DR-002, DR-003, DR-004 (HIGH)** should be resolved or explicitly
   accepted with rationale by the human before Implementation Planning, since
   they affect test coverage of the newly hardened FR-016 control, a genuine
   internal contradiction about pipeline ordering/ownership, and a concrete
   sensitive-data leak path (decorators), respectively.
3. MEDIUM/LOW findings (DR-005 through DR-009) do not need to block G2 by
   themselves, but should be tracked and addressed no later than
   Implementation Planning so they don't silently reappear as undocumented
   assumptions in the impl-plan.

## Assumptions Requiring Human Confirmation

These are pre-existing architecture-level assumptions (§23) that this review
did not find to be *incorrect*, but which remain product decisions the human
should explicitly confirm rather than have carried forward by default, per
CLAUDE.md's human-in-the-loop rules:

- Whether "signature" for change-detection purposes should include decorators,
  parameter defaults, and annotations (not just parameter names) — already
  self-flagged by the architect in §8/§23 for Design Review confirmation.
- Whether structured docstring-convention parsing (Google/NumPy/Sphinx-style
  `Args:`/`:param:` sections) should ever be in scope — already correctly
  raised as Open Question #2 in §24 and not decided here; this review does not
  attempt to decide it either.
- Whether v1 explicitly excludes non-UTF-8-encoded (but validly PEP
  263-declared) Python source files as an accepted limitation (raised newly by
  this review as DR-006) — this is a product-scope decision, not something
  this review can resolve unilaterally.

## Verdict

**Not ready for Implementation Planning.** One BLOCKER (DR-001) and three HIGH
findings (DR-002, DR-003, DR-004) remain unresolved. Per CLAUDE.md's Gate G2
definition, `docs/architecture.md` has not passed design review while a
blocking finding is open. The most consequential gap is DR-001: the one
control introduced specifically to convert FR-016 from a soft into a hard
boundary (AC-015) is described only at the level of intent ("verifies the path
lies inside the subtree"), not at the level of a concrete, edge-case-proof
mechanism — which is precisely the distinction this review was asked to
verify rather than assume. The `architect` agent should address DR-001 through
DR-004 and resubmit for a follow-up design review before Gate G2 can be
considered passed.

## Remediation Status (2026-09-24, added under Change Control)

This section is appended after the Verdict above without altering it — the
Verdict text is preserved as the historical record of this review's original
judgment at the time it was written.

The `architect` agent has since applied a remediation pass to
`docs/architecture.md` and to `docs/adr/0002-0005` in response to all nine
findings above. Each finding (DR-001 through DR-009) now carries its own
"## Resolution" subsection, added directly under that finding without deleting
or editing the finding's original Problem/Impact/Recommended-resolution text,
recording a disposition of RESOLVED for every finding in this review — no
finding was silently dropped or left unaddressed. In summary:

- **DR-001 (BLOCKER):** RESOLVED — a concrete, numbered, escape-proof algorithm
  is now specified in `docs/architecture.md` §11.1 and recorded in new
  `docs/adr/0005-output-path-boundary-algorithm.md`.
- **DR-002 (HIGH):** RESOLVED — explicit AC-015 negative/positive test
  fixtures added to §19's testing architecture, plus a new `test_config.py`
  unit-test target.
- **DR-003 (HIGH):** RESOLVED — the FR-016 boundary check (Configuration
  Resolver, pre-scan) and the FR-009 ownership-marker guard (Output Writer,
  at write time) are now consistently described as two distinct mechanisms in
  two distinct components across every affected section.
- **DR-004 (HIGH):** RESOLVED — decorator text (including string-literal
  decorator-call arguments) is now explicitly in the Sensitive-Value Filter's
  scope; the unsupported "module-level constants" reference has been removed
  from §4.7 without adding any new, unrequested model field.
- **DR-005 (MEDIUM):** RESOLVED — storage specified concretely as a per-file
  JSON hash table embedded in the header banner.
- **DR-006 (MEDIUM):** RESOLVED — `tokenize.detect_encoding` adopted per
  explicit human decision, honoring PEP 263 without a new dependency.
- **DR-007 (MEDIUM):** RESOLVED — the per-file exception boundary is now named
  explicitly (`SyntaxError`, `RecursionError`, `ValueError`,
  `UnicodeDecodeError`/`LookupError`, `OSError`).
- **DR-008 (LOW):** RESOLVED — Output Writer creates `docs/generated/` and
  sub-directories if missing, only after the §11.1 boundary check passes.
- **DR-009 (LOW):** RESOLVED — the boundary check's containment comparison
  inherits host-filesystem case-sensitivity naturally via `.resolve()`, rather
  than introducing an independent case-handling rule.

**This section does not itself declare Gate G2 passed.** Whether the
remediated `docs/architecture.md` now satisfies Gate G2 is a determination for
a follow-up, independent Design Review pass to make — consistent with
CLAUDE.md's rule that review agents must critically evaluate work rather than
have it self-certified by the producing agent, and that the decision to accept
an artifact is always the human's. This status section records only that every
finding has been addressed with a documented disposition, not that the
architecture has been re-approved.

---

## Focused Re-review (2026-09-24)

Reviewer: `design-reviewer` agent, independent second pass. This re-review does
not accept the "Resolution"/"Remediation Status" text above as fact — each
disposition below reflects independent verification against the current text
of `docs/architecture.md` and the affected ADRs. Scope is limited to
re-verifying DR-001 through DR-009 and the cross-cutting conditions listed in
the task brief; it is not a new full architecture review.

Inputs read: `docs/requirements.md`, `docs/architecture.md` (full text, current
revision), `docs/design-review.md` (this file, prior content), and
`docs/adr/0002-python-parsing-approach.md`, `docs/adr/0003-change-detection-strategy.md`,
`docs/adr/0004-generated-output-ownership.md`, `docs/adr/0005-output-path-boundary-algorithm.md`.

### DR-001 — previously BLOCKER

**Remediation claimed:** a concrete, 12-step algorithm now specifies the
FR-016 boundary check (`docs/architecture.md` §11.1), covering absolute
paths, Windows drive-qualified/drive-relative/UNC forms, `..` traversal,
path-aware containment, sibling-prefix, symlink escapes, non-existent
components, and case-sensitivity, with the decision recorded in new
`docs/adr/0005-output-path-boundary-algorithm.md`.

**Evidence checked:**
- §11.1 step 2: rejects `candidate` if either `PureWindowsPath(candidate).is_absolute()` or `PurePosixPath(candidate).is_absolute()` is `True`, checked regardless of host OS — covers absolute POSIX and Windows syntax on any host.
- §11.1 step 3: rejects if `PureWindowsPath(candidate).drive` is non-empty (verified this single check independently: for `ntpath.splitdrive`-style parsing, `.drive` is non-empty for drive-absolute `C:\foo`, drive-relative `C:foo`, and UNC `\\server\share\...`, since UNC prefixes are also reported as the `.drive` value by `PureWindowsPath`), plus a defense-in-depth `\\`/`//` prefix check.
- §11.1 step 4: rejects literal `..` path components, split on both `/` and `\`, independent of host OS — covers single-level traversal pre-join.
- §11.1 steps 5–7: `real_root`/`real_candidate` computed via `Path.resolve()` on both sides; verified `Path.resolve()` (non-strict, default since Python 3.6) lexically normalizes `..` components even in a not-yet-existing suffix while resolving symlinks in whatever prefix does exist — this correctly handles nested traversal (e.g. `a/../../evil.md`) and non-existent intermediate/leaf components without special-casing.
- §11.1 step 8: containment via `Path.is_relative_to()` — a path-object comparison, explicitly contrasted in the text against a naive `str.startswith` check, and confirmed component-aware (so `docs/generated-evil/` is correctly excluded — verified this is not merely asserted but is actually true of `is_relative_to` semantics).
- §11.1 step 10: explicitly addresses both a symlinked subdirectory under `docs/generated/` pointing outside the tree, and `docs/generated/` itself being a symlink (in which case its real target becomes `real_root`).
- §11.1 step 11: "No write of any kind occurs before this check passes"; corroborated by §6's data-flow diagram, which places the boundary check as the first pipeline step, before scanning.
- `docs/adr/0005-output-path-boundary-algorithm.md`: records the same algorithm as Option 4, with three rejected alternatives (string-prefix, lexical-only, OS sandboxing) and explicit trade-offs (resolve() does filesystem I/O; a symlinked `docs/generated/` is treated as authoritative).

**Status: RESOLVED.** Every sub-element named in the task's DR-001 checklist has a concrete, independently-verified mechanism, not merely an asserted property. No gap found.

### DR-002 — previously HIGH

**Remediation claimed:** §19 now has an explicit AC-015 bullet with concrete negative path-escape test cases, plus a new `test_config.py` unit-test target.

**Evidence checked:** §19's bullet list (Testing Architecture) enumerates, specifically for AC-015: a `..`-escaping relative path, a nested-traversal path, an absolute path (both POSIX and Windows forms), a sibling-prefix path (`../generated-evil/x.md`, explicitly framed as a check on path-aware vs. string-prefix containment), a Windows drive-qualified/drive-relative path, a UNC path, a symlink-escape fixture (platform-permitting), and a positive-control valid nested path so the negative tests aren't vacuously passing. §5's package tree lists `tests/unit/test_config.py`, and §19's unit-test bullet states it "unit-tests the Section 11.1 boundary-check algorithm directly and exhaustively... covering at minimum every step of the algorithm," naming the same case list.

**Status: RESOLVED.** This is concrete, itemized negative-case coverage, not a generic mention.

### DR-003 — previously HIGH

**Remediation claimed:** the FR-016 boundary check (Configuration Resolver, pre-scan) and the FR-009 ownership-marker check (Output Writer, at write time) are now consistently described as two distinct mechanisms across every affected section.

**Evidence checked, section by section:**
- §4.2 (Configuration Resolver): explicit "Remediation note (resolves DR-003)" stating the Resolver performs *only* the boundary check and "does not perform, and must not be implemented to perform, the FR-009 ownership-marker check."
- §4.10 (Output Writer): states the Output Writer is "the sole component responsible for the FR-009 ownership-marker check... executed immediately before writing/replacing the target file," and that it does not re-derive or repeat the boundary check.
- §6 (data-flow diagram): shows the boundary check gating entry into scanning (`B -->|boundary check passes| C[Scan...]`), and shows the ownership-marker check occurring later, inside node `P`, after rendering (`P["Output Writer: create dirs...OWNERSHIP-MARKER CHECK (11.2, FR-009); atomic write..."]`) — consistent with the two-stage split, not contradictory.
- §11.2: "Owner: Output Writer... When: immediately before writing/replacing the target file"; explicitly states prior drafts of §4.2/§13/§16 were corrected.
- §13: "Corrected fail-fast ordering (resolves DR-003)" — states only the boundary check is pre-scan; the ownership guard is evaluated later, "after scanning/rendering have already run."
- §16: lists the two conditions under separate headings ("Pre-scan..." vs. "At write time... only if a write was determined to be necessary"), at their correct respective stages.
- §21: "the ownership guard, performed by the Output Writer immediately before the write (resolves DR-003's ordering ambiguity)."
- §22: FR-009 row says "Output Writer (ownership-marker check, at write time only)"; FR-016 row's Notes column explicitly states "the two checks are distinct components and distinct pipeline stages (resolves DR-003)."
- `docs/adr/0004-generated-output-ownership.md`'s "Further Resolution" section states the same split and does not contradict the architecture text.

**Status: RESOLVED.** No section retains the earlier contradictory claim; all eight cited locations agree on both the component and the timing for each of the two checks.

### DR-004 — previously HIGH

**Remediation claimed:** decorator text (including string-literal decorator-call arguments) is now explicitly filtered; the "module-level constants" inconsistency is corrected by removal (no such field exists), not by adding a new field.

**Evidence checked:**
- §4.7: names "decorator text, including any string-literal arguments passed to a decorator call (e.g., `@requires_api_key("sk-live-...")`)" as filtered content, and explains decorators are rendered as part of the reconstructed signature, so they are a real leak path.
- §15: repeats the same coverage list — module/class/function docstrings, parameter default-value text, parameter/return annotation text, and `ClassDoc.decorators`/`FunctionDoc.decorators` text including decorator-call string arguments.
- §9 (`ModuleDoc`): confirmed fields are exactly `path`, `docstring`, `classes`, `functions`, `errors` — no module-level-constant field. §4.7 and §15 both explicitly state this and state the prior "module-level constants if captured" phrase has been removed, not replaced. Cross-checked: FR-006 in `docs/requirements.md` does not request module-level constant extraction, so removal (rather than adding a field) is the correct-scope choice.
- Both `ClassDoc.decorators` and `FunctionDoc.decorators` exist in §9's model, so class-level and function/method-level decorators are both structurally covered by the filter's stated scope (§15 names both).

**Status: RESOLVED.** The concrete leak path (decorator-argument secrets) is closed, and §4.7/§9/§15 are now mutually consistent — verified, not merely asserted.

### DR-005 — previously MEDIUM

**Remediation claimed:** storage is specified concretely as a per-file JSON hash table embedded in the header banner, resolving the "comparison unit vs. storage format" ambiguity.

**Evidence checked:** §12 states explicitly: "the storage format is explicitly a per-file hash table, not a single aggregate hash... embedded as a single-line, machine-parseable JSON object inside the header banner's HTML comment, keyed by the file's path relative to the configured source root, with a stable (sorted-by-key) serialization," and gives a concrete example: `<!-- docsync:v1 sha256={"pkg/a.py": "3f2a...", "pkg/sub/b.py": "9c11..."} -->`. `docs/adr/0003-change-detection-strategy.md`'s "Resolution" section states the identical format and explicitly frames it as a clarification of Option B3, not a reversal. §10 (Markdown Generation) also refers to "the ADR-0003 per-file change-detection hash table," consistent with §12.

**Status: RESOLVED.** The format is concrete and consistent between §12, §10, and the ADR.

### DR-006 — previously MEDIUM

**Remediation claimed:** `tokenize.detect_encoding` adopted per human decision, resolving the UTF-8-only assumption.

**Evidence checked:** §8 point 1 specifies the Parser calls `tokenize.detect_encoding(readline)` before reading, honoring PEP 263 cookies, defaulting to UTF-8 when no cookie is present, with decode failures converted to a structured per-file error rather than fabricated text. §2's technology-stack table has a matching row. §23 records this as a human-confirmed decision. `docs/adr/0002-python-parsing-approach.md`'s "Resolution" section states the same change and explicitly notes it does not reopen the `ast`-engine decision.

**Status: RESOLVED.**

### DR-007 — previously MEDIUM

**Remediation claimed:** the per-file exception boundary now names the full exception set (`SyntaxError`, `RecursionError`, `ValueError`, `UnicodeDecodeError`/`LookupError`, `OSError`).

**Evidence checked:** §8 point 2 names exactly this set and explicitly states it "resolves DR-007." §4.5 (Parser responsibilities) independently repeats the same set. §16 cross-references §8 point 2 as "the authoritative statement of this set" rather than re-describing it loosely (closing the exact duplication risk the original finding worried about). `docs/adr/0002-python-parsing-approach.md`'s "Resolution" section states the same set.

**Status: RESOLVED.**

### DR-008 — previously LOW

**Remediation claimed:** the Output Writer creates `docs/generated/` and needed sub-directories if missing, only on an already-validated path.

**Evidence checked:** §11.3 states the Output Writer creates directories via `mkdir(parents=True, exist_ok=True)` "applied only to a target path that has already passed the §11.1 boundary check... never to a raw, unvalidated `--output` value." §11.4's restated processing order places this between the boundary check and the ownership-marker check. `docs/adr/0004-generated-output-ownership.md`'s "Further Resolution" section cross-references the same ordering.

**Status: RESOLVED.**

### DR-009 — previously LOW

**Remediation claimed:** the boundary check's containment comparison inherits host-filesystem case-sensitivity naturally via `.resolve()`, rather than a separately specified case rule.

**Evidence checked:** §11.1 step 9 states the comparison is performed on two `.resolve()`d paths on the same host, so it "inherits whatever case-sensitivity semantics that filesystem actually has... automatically and consistently," and explicitly declines to layer an independent case-folding rule on top. §18 has a new bullet distinguishing this FR-016 boundary-check case-sensitivity question from the pre-existing FR-004 exclusion-matching case-sensitivity discussion, so the two are not conflated. `docs/adr/0005-output-path-boundary-algorithm.md`'s Rationale section states the same point as a natural consequence of the algorithm, not a separate decision.

**Status: RESOLVED.**

### Cross-cutting conditions

1. **No approved requirement contradicted by the remediation — PASS.** Checked FR-016's wording and the Section 6 Constraint in `docs/requirements.md` against `docs/architecture.md` §11.1/§13/§17; the architecture's restriction of `--output` to a sub-path within `docs/generated/` matches the requirement text exactly (both use the same "filename/sub-path within `docs/generated/`" framing). No other requirement text is contradicted by any remediated section.

2. **No new product requirement silently introduced — PASS.** §3's component list (CLI Layer, Configuration Resolver, Pipeline Orchestrator, Scanner, Parser, Model, Sensitive-Value Filter, Change Detector, Renderer, Writer, Diagnostics Reporter, Test Suite) is unchanged in membership from before remediation; the remediation only added specificity (a concrete algorithm, a named exception set, a concrete storage format, a corrected ownership-check split) to existing components' already-authorized responsibilities. §22's traceability table still maps every FR/NFR to existing components; the new `test_config.py` file and new ADR-0005 are test/documentation artifacts, not new product capabilities. Decorators (`ClassDoc.decorators`, `FunctionDoc.decorators`) already existed in §9's model before this remediation (per DR-004's own problem statement, which describes them as already present but unfiltered) — filtering them is a fix, not new scope.

3. **FR-001 through FR-016 remain architecturally covered — PASS.** Verified against §22's table; every FR-001–016 row is present and points to an existing component/section.

4. **NFR-001 through NFR-005 remain architecturally covered — PASS.** Verified against §22's table; every NFR-001–005 row is present.

5. **The three human decisions are represented correctly and consistently — PASS.**
   - Signature scope (decorators/defaults/annotations, no source execution): stated in §23 ("Confirmed by explicit human decision during this remediation (signature scope)") and consistently reflected in §8's decision-scope paragraph, §4.7/§15's filter coverage, and §9's model fields.
   - Structured docstring-convention parsing out of scope for v1: stated in §23 and in §24 ("Resolved during this remediation (formerly Open Question #2)"), consistent with §8 point 4's "no docstring-convention parsing" statement.
   - `tokenize.detect_encoding` for source encoding: stated in §23, §8 point 1, and §2's tech-stack table, all consistent with each other and with ADR-0002's Resolution section.

### Verdict

```
DR-001: RESOLVED
DR-002: RESOLVED
DR-003: RESOLVED
DR-004: RESOLVED
DR-005: RESOLVED
DR-006: RESOLVED
DR-007: RESOLVED
DR-008: RESOLVED
DR-009: RESOLVED

BLOCKER findings remaining: 0
HIGH findings remaining: 0

Requirement coverage:
FR-001-FR-016: COVERED
NFR-001-NFR-005: COVERED

New conflicts introduced: NO
Unapproved scope introduced: NO

Final Design Review verdict:
READY FOR IMPLEMENTATION PLANNING
```

This verdict is this re-review's independent determination; per CLAUDE.md, the
decision to accept `docs/architecture.md` and formally pass Gate G2 remains
the human's to make.
