# Implementation Plan: Automated Documentation Sync (v1)

Status: **Proposed — pending Gate G3 human approval.**
Source of truth (do not redesign): `docs/requirements.md` (Gate G1 approved),
`docs/architecture.md` (Gate G2 approved), `docs/design-review.md` (DR-001–DR-009
all RESOLVED, 0 BLOCKER/0 HIGH, focused re-review verdict READY FOR IMPLEMENTATION
PLANNING). ADRs 0001–0005 consulted only where `docs/architecture.md` explicitly
points to them for a detail (parsing engine, change-detection format, ownership
guard, output-path boundary algorithm).

This plan introduces no new requirement and redesigns nothing. Where architecture
gives a concrete, normative mechanism (notably §11.1's output-path boundary
algorithm), this plan requires that mechanism be implemented exactly as specified,
not reinvented.

---

## Packaging Decision

Standard `pyproject.toml`-based Python package, package name **`docsync`**
(finalizing the architecture's placeholder — §5, §23), exposing:

- A console-script entry point: `docsync = docsync.cli:main`
- Equivalent invocation via `python -m docsync`, per architecture §2's own
  anticipation of this

Minimum Python: **3.11+** (per ADR-0001; no stricter patch floor is needed — no
requirement or architectural detail depends on a Python patch version beyond
3.11). No publication to PyPI or any package index is required by any FR/NFR;
none is planned. No CI/CD pipeline, containerization, or deployment automation is
introduced — NFR-004 only requires that the design *not preclude* a future
Git-hook/CI trigger (satisfied by the CLI/core split in `core.py`), not that this
phase build one. `pytest` is a development-only dependency (NFR-005); it is not a
runtime dependency of the shipped package.

Rationale: this is the simplest packaging shape that (a) gives a real CLI entry
point (FR-001), (b) is `pip install`-able and importable for testing (NFR-005),
(c) has no OS-specific packaging step (NFR-001), and (d) adds no dependency or
infrastructure beyond what FR/NFR already require.

---

## Tasks

### TASK-001 — Project and package scaffolding
- **Depends On:** None
- **FR/NFR:** FR-001 (enables CLI); supports NFR-005 (testability)
- **Main files/components:** `pyproject.toml`; `docsync/__init__.py`; `tests/` directory skeleton (architecture §5)
- **Tests required:** none (scaffolding only); verified by `pip install -e .` succeeding and `import docsync` working
- **Definition of Done:** package installs in editable mode; empty `docsync` package importable; `tests/unit/` and `tests/integration/fixtures/` directories exist per §5's tree

### TASK-002 — Documentation Model
- **Depends On:** TASK-001
- **FR/NFR:** FR-006, FR-012
- **Main files/components:** `docsync/model.py`
- **Tests required:** `tests/unit/test_model.py` — construct each data class; verify `UNAVAILABLE` vs. absent/`NOT_APPLICABLE` sentinel distinction (§9)
- **Definition of Done:** `ModuleDoc`, `ClassDoc`, `FunctionDoc`, `ParameterDoc`, `ParseError` plain-data classes exist exactly matching §9's field list (no module-level-constant field, per DR-004 resolution); both sentinels implemented and distinguishable

### TASK-003 — Configuration Resolver: core resolution (excluding boundary check)
- **Depends On:** TASK-001
- **FR/NFR:** FR-002, FR-004, FR-005, FR-008
- **Main files/components:** `docsync/config.py`
- **Tests required:** `tests/unit/test_config.py` (resolution portion) — source dir existence/readability validation; default output path; default exclusion list merge with `--exclude` patterns
- **Definition of Done:** `Config` object resolves source dir (validated), default/custom exclusions (§14), and default output path (`docs/generated/code-documentation.md`), independent of TASK-004's boundary check

### TASK-004 — Output-path boundary-check algorithm (SECURITY-SENSITIVE)
- **Depends On:** TASK-003
- **FR/NFR:** FR-016; AC-015
- **Main files/components:** `docsync/config.py`
- **Implementation work:** Implement the algorithm specified in `docs/architecture.md` §11.1 and `docs/adr/0005-output-path-boundary-algorithm.md` **exactly as written — do not invent a different path-security algorithm.** The 12 steps, in order, each a hard rejection on failure: (1) reject empty/blank; (2) reject if `PureWindowsPath(candidate).is_absolute()` or `PurePosixPath(candidate).is_absolute()`, checked regardless of host OS; (3) reject if `PureWindowsPath(candidate).drive` is non-empty (catches drive-absolute, drive-relative, and UNC forms), plus defense-in-depth `\\`/`//` prefix rejection; (4) reject any path component exactly equal to `..`, split on both `/` and `\`; (5) compute `real_root = Path("docs/generated").resolve()`; (6) join validated-relative `candidate` onto `real_root`; (7) `real_candidate = candidate_path.resolve()` (follows symlinks, tolerates non-existent leaf components); (8) decisive containment check via `real_candidate.is_relative_to(real_root)` — path-object comparison, not string-prefix; (9) case-sensitivity inherited naturally from `.resolve()`, no separate case rule; (10) symlink escapes (including a symlinked `docs/generated/` itself) resolved correctly by (7)+(8); (11) no write of any kind before this check passes; (12) any failing step produces one clear, file-identified error (FR-014) and stops the run — no scanning, no parsing, no rendering, no write.
- **Tests required:** `tests/unit/test_config.py` (boundary-check portion) — exhaustive per-step coverage per §19: valid relative sub-path (accept); absolute POSIX path (reject, step 2); absolute Windows path (reject, step 2/3); Windows drive-relative path e.g. `C:foo` (reject, step 3); UNC path e.g. `\\server\share\x.md` (reject, step 3); `..`-traversal e.g. `../evil.md` (reject, step 4 and step 8); nested traversal e.g. `a/../../evil.md` (reject, step 8); sibling-prefix e.g. resolving to `docs/generated-evil/x.md` (reject, step 8 — proves path-aware not string-prefix); symlink-escape fixture where platform supports it (reject, step 8 after step 7's resolve)
- **Definition of Done:** every listed test case passes; no step reordered, omitted, or reimplemented differently from §11.1; AC-015 satisfied
- **Security-sensitive:** YES — this is the FR-016 hard boundary control; implementation must trace directly to §11.1/ADR-0005 with no deviation

### TASK-005 — Source Directory Scanner
- **Depends On:** TASK-003
- **FR/NFR:** FR-003, FR-004, FR-005; NFR-002
- **Main files/components:** `docsync/scanner.py`
- **Tests required:** `tests/unit/test_scanner.py` — default exclusions (`.git`, `.venv`, `venv`, `__pycache__`, `build`, `dist`, `node_modules`) pruned before descent; custom `--exclude` glob patterns applied; only `.py` files yielded; unreadable subtree reported as per-directory error, not fatal; unreadable top-level source dir is fatal (§7)
- **Definition of Done:** scanner yields correct candidate file list against fixture trees; excluded directories never descended into

### TASK-006 — Python source reader (encoding-aware)
- **Depends On:** TASK-001
- **FR/NFR:** FR-003, FR-012, FR-013; NFR-001
- **Main files/components:** `docsync/parser.py` (read/decode portion)
- **Implementation work:** use `tokenize.detect_encoding(readline)` ahead of decode, per §8 point 1 (resolves DR-006) — do not hard-code UTF-8-only
- **Tests required:** `tests/unit/test_parser.py` (encoding portion) — UTF-8 file with no cookie; file with a PEP 263 encoding cookie in a non-UTF-8 encoding; a file whose declared encoding doesn't match its bytes (must raise a caught `UnicodeDecodeError`/`LookupError`, converted to a structured per-file error, not a crash)
- **Definition of Done:** encoding detection matches CPython tokenizer behavior; decode failures produce structured per-file errors, never fabricated text

### TASK-007 — Python AST parsing and structural extraction
- **Depends On:** TASK-002, TASK-006
- **FR/NFR:** FR-006, FR-012, FR-013
- **Main files/components:** `docsync/parser.py` (parse/extract portion)
- **Implementation work:** `ast.parse()` inside a per-file exception boundary catching exactly `SyntaxError`, `RecursionError`, `ValueError`, `UnicodeDecodeError`/`LookupError`, `OSError` (§8 point 2, resolves DR-007 — this exact set, not `SyntaxError` alone); walk the module to collect module docstring, classes (with docstrings, decorators, nested methods), top-level functions, and for each function/method: name, decorators, parameters (name, default via `ast.unparse`, annotation via `ast.unparse`), return annotation via `ast.unparse`, docstring; any field with no source counterpart set to `UNAVAILABLE`; function/method body statements read but never copied into the model (enables TASK-009's body-exclusion); no type inference, no docstring-convention parsing (§8 point 4, per human decision)
- **Tests required:** `tests/unit/test_parser.py` (extraction portion) — module/class/function/method/signature/parameter/decorator extraction against fixtures; each of the five caught exception types individually triggered and confirmed non-fatal to the run; body-only content confirmed absent from the produced model
- **Definition of Done:** produces a populated `ModuleDoc` tree (TASK-002's classes) for valid files; any single pathological file (any of the five exception types) is isolated and does not abort the run (FR-013)

### TASK-008 — Sensitive-Value Filter (SECURITY-SENSITIVE)
- **Depends On:** TASK-002, TASK-007
- **FR/NFR:** FR-015; NFR-003
- **Main files/components:** `docsync/sensitive.py`
- **Implementation work:** scan every rendered-text-bearing model field per §15/§4.7 (resolves DR-004): module/class/function docstrings; `ParameterDoc.default`; `ParameterDoc.annotation`; `FunctionDoc.return_annotation`; `ClassDoc.decorators` and `FunctionDoc.decorators` **including string-literal decorator-call arguments**. Apply fixed pattern-based rules for NFR-003's categories (passwords, API keys, access/auth tokens, credentials, private-key blocks, variable-name heuristics like `password`/`secret`/`token`/`api_key`/`credential`); replace matches with a fixed redaction placeholder. Must run before hashing (TASK-009) and rendering (TASK-010) so a redacted value never reaches either.
- **Tests required:** `tests/unit/test_sensitive.py` — one case per NFR-003 category; a decorator-call string-literal-argument secret (e.g. `@requires_api_key("sk-live-...")`); a parameter-default secret; confirms redaction happens before the value would reach a hash or render step
- **Definition of Done:** all named leak paths redacted; no module-level-constant field is added (none exists in the model — DR-004 resolution)
- **Security-sensitive:** YES — implements FR-015/NFR-003 sensitive-data protection

### TASK-009 — Change Detector
- **Depends On:** TASK-002, TASK-008
- **FR/NFR:** FR-010, FR-011; NFR-002
- **Main files/components:** `docsync/changedetect.py`
- **Implementation work:** canonically serialize the redacted per-file model (excluding body statements, which never entered the model per TASK-007), hash (SHA-256); storage is a **per-file JSON hash table**, sorted-key serialization, embedded in the header banner per §12 (resolves DR-005): `<!-- docsync:v1 sha256={"pkg/a.py": "3f2a...", ...} -->`; read prior table from existing output's header banner; compare per-file; regenerate if any hash differs, a file is new, or a file was removed; skip write if table identical
- **Tests required:** `tests/unit/test_changedetect.py` — signature/docstring change triggers regeneration; body-only change does not; new file triggers regeneration; removed file triggers regeneration; identical run produces no write
- **Definition of Done:** matches §12's exact storage format and comparison semantics; AC-004/AC-005 both provable at unit level

### TASK-010 — Markdown Renderer
- **Depends On:** TASK-002, TASK-008, TASK-009
- **FR/NFR:** FR-007, FR-012
- **Main files/components:** `docsync/render.py`
- **Implementation work:** deterministic/pure rendering per §10 — header banner (do-not-edit notice + TASK-009's hash table), one section per module, subsections per class/function, explicit "_Not available_" marker for `UNAVAILABLE` fields (distinguishable from `NOT_APPLICABLE`/absent per §9)
- **Tests required:** `tests/unit/test_render.py` — same model input produces byte-identical output across repeated calls (determinism); `UNAVAILABLE` vs. absent rendered distinguishably; header banner contains correct hash table
- **Definition of Done:** rendering is pure/deterministic; output matches §10's structure

### TASK-011 — Output Writer: directory creation, ownership guard, atomic write (SECURITY-SENSITIVE)
- **Depends On:** TASK-004, TASK-010
- **FR/NFR:** FR-008, FR-009, FR-016
- **Main files/components:** `docsync/writer.py`
- **Implementation work:** operates only on the already-boundary-checked path from TASK-004 (never re-derives or repeats that check). Sequence per §11.3/§11.2 (resolves DR-003/DR-008): (a) `mkdir(parents=True, exist_ok=True)` on the validated target's parent directory; (b) if a file exists at the target, read it and check for the tool's header-banner marker (ADR-0003/ADR-0004) — present → proceed to overwrite; absent → abort this write and raise a reportable error (FR-014), do not overwrite; no file → proceed; (c) atomic write (temp file in same directory, then replace)
- **Tests required:** `tests/unit/test_writer.py` — fresh `docs/generated/` (not yet existing) gets created; pre-existing tool-marked file is overwritten; pre-existing unmarked (foreign) file is left untouched and an error is raised; atomicity (no partial file left on simulated interruption, where feasible to test)
- **Definition of Done:** ownership guard runs exclusively here, exclusively at write time; a manually maintained file outside the tool's ownership is never overwritten (AC-011)
- **Security-sensitive:** YES — implements the FR-009 ownership/overwrite-safety guard (ADR-0004); must not be merged with or substitute for TASK-004's boundary check

### TASK-012 — Error & Diagnostics Reporter
- **Depends On:** TASK-002
- **FR/NFR:** FR-013, FR-014
- **Main files/components:** `docsync/diagnostics.py`
- **Implementation work:** single structured error type (`DocSyncError`: `path`, `stage`, `message`); collects per-file/per-directory errors from Scanner/Parser/Writer; formats clear, file-identified messages; determines final exit code (zero only if no important error)
- **Tests required:** `tests/unit/test_diagnostics.py` — error aggregation from multiple sources; exit-code determination logic (all-success → 0; any important error → non-zero)
- **Definition of Done:** every error surfaced with file path and human-readable reason (FR-014)

### TASK-013 — Pipeline Orchestrator
- **Depends On:** TASK-004, TASK-005, TASK-007, TASK-008, TASK-009, TASK-011, TASK-012
- **FR/NFR:** FR-010, FR-011, FR-013; NFR-004
- **Main files/components:** `docsync/core.py`
- **Implementation work:** single importable entry point `run(config: Config) -> Result` sequencing Config→Scanner→Parser→Model→Sensitive Filter→Change Detector→Renderer→Writer; aggregates per-file errors into final `Result`; pre-scan fatal conditions (unreadable source root, boundary-check failure) stop the run before scanning per §16; all other errors are per-file/non-fatal (FR-013); exists independent of CLI process invocation so a future Git-hook/CI wrapper could call it directly (NFR-004)
- **Tests required:** covered at integration level (TASK-015); no additional orchestrator-only unit test required beyond what TASK-015 exercises through the CLI/library entry point
- **Definition of Done:** full pipeline runs end-to-end against a fixture repo, aggregating results/errors correctly

### TASK-014 — CLI entry point
- **Depends On:** TASK-013
- **FR/NFR:** FR-001, FR-002, FR-016
- **Main files/components:** `docsync/cli.py`; `pyproject.toml` console-script entry point
- **Implementation work:** `argparse`-based single-command CLI (`--source` required, `--output` optional, `--exclude` repeatable); maps args to `Config`; invokes `core.run`; maps `Result` to process exit code; prints summary to stdout, errors/warnings to stderr (never the generated Markdown to stdout) per §17
- **Tests required:** covered at CLI/end-to-end level (TASK-015)
- **Definition of Done:** `docsync --source <path>` runs the full pipeline and produces correct exit codes

### TASK-015 — Integration and CLI/end-to-end tests
- **Depends On:** TASK-013, TASK-014
- **FR/NFR:** FR-001–FR-014, FR-016; NFR-001, NFR-005
- **Main files/components:** `tests/integration/fixtures/*`, `tests/integration/test_end_to_end.py`
- **Tests required (per §19):** primary-workflow fixture (AC-001/AC-002); unavailable-information fixture (AC-003); signature-changed vs. body-only-changed fixture pair run twice each (AC-004/AC-005); invalid-file-alongside-valid-files fixture (AC-006/AC-007); NFR-003-category secret fixture (AC-008); default- and custom-exclusion fixtures (AC-009/AC-010); pre-existing manually-maintained-file-at-output-path fixture (AC-011); custom `--output` fixture (AC-012)
- **Definition of Done:** every listed AC has a passing fixture-backed test

### TASK-016 — AC-015 security/path-boundary integration tests (SECURITY-SENSITIVE)
- **Depends On:** TASK-004, TASK-014
- **FR/NFR:** FR-016; AC-015
- **Main files/components:** `tests/integration/test_end_to_end.py` (or a dedicated `test_output_path_security.py`)
- **Implementation work:** run the CLI end-to-end (not just TASK-004's unit tests) with each negative case from §19: `..`-escaping relative path; nested-traversal path; absolute path (POSIX and Windows forms); sibling-prefix path (`../generated-evil/x.md`); Windows drive-qualified/drive-relative path (Windows CI); UNC path (Windows CI); symlink-escape fixture where platform supports it — for each, assert non-zero exit + clear file-identified error, and assert (via filesystem snapshot before/after) that no file is written anywhere outside `docs/generated/`. Positive control: a valid nested path (e.g. `api/nested/reference.md`) must be accepted.
- **Tests required:** exactly the list above
- **Definition of Done:** all negative cases rejected with no write outside `docs/generated/`; positive control accepted — satisfies AC-015 and resolves DR-002's originally-missing test architecture
- **Security-sensitive:** YES — end-to-end proof of the FR-016 boundary control

### TASK-017 — Cross-platform behavior tests
- **Depends On:** TASK-015, TASK-016
- **FR/NFR:** NFR-001; AC-013
- **Main files/components:** `tests/integration/` (same suite, run across target OSes)
- **Implementation work:** confirm the existing suite (TASK-015/016) is OS-agnostic (uses only `pathlib`, explicit UTF-8 text I/O, no shelled-out OS-specific commands per §18); run on Windows, Linux, and macOS
- **Tests required:** existing suite executed on each target OS; no new test logic beyond CI/test-runner configuration
- **Definition of Done:** equivalent documentation content produced on all three OSes for the same input (AC-013)

### TASK-018 — Documentation/README updates
- **Depends On:** TASK-014
- **FR/NFR:** supports FR-001/FR-002/FR-016 (usability, not a new requirement)
- **Main files/components:** top-level `README.md` for the `docsync` project itself (not generated output)
- **Implementation work:** document installation (`pip install -e .`), CLI usage (`--source`, `--output`, `--exclude`), and the `docs/generated/` output-boundary behavior
- **Tests required:** none (documentation only)
- **Definition of Done:** README accurately describes CLI usage and packaging (TASK-014, Packaging Decision above)

### TASK-019 — Verification preparation
- **Depends On:** TASK-015, TASK-016, TASK-017
- **FR/NFR:** NFR-005
- **Main files/components:** none new — confirms existing `tests/` suite is complete and runnable as a single command (e.g. `pytest`)
- **Implementation work:** confirm every AC-001–AC-015 has at least one passing automated test; confirm the full suite runs via a single command for the later Verification phase; no new test logic is authored here beyond what TASKS 001–017 already required
- **Tests required:** none new; this task verifies existing coverage
- **Definition of Done:** full `pytest` run is green; AC/test coverage matrix (below) has no gaps

---

## Dependency / Execution Order

```
TASK-001
  ├─→ TASK-002 ─────────────────┐
  ├─→ TASK-003 ─→ TASK-004 ─┐   │
  │                          │   │
  ├─→ TASK-005 (needs 003)   │   │
  └─→ TASK-006               │   │
        └─→ TASK-007 (needs 002, 006)
                └─→ TASK-008 (needs 002, 007)
                      └─→ TASK-009 (needs 002, 008)
                            └─→ TASK-010 (needs 002, 008, 009)
                                  └─→ TASK-011 (needs 004, 010)
TASK-012 (needs 002)
TASK-013 (needs 004, 005, 007, 008, 009, 011, 012)
  └─→ TASK-014 (needs 013)
        └─→ TASK-015 (needs 013, 014)
        └─→ TASK-016 (needs 004, 014)
              └─→ TASK-017 (needs 015, 016)
        └─→ TASK-018 (needs 014)
TASK-019 (needs 015, 016, 017)
```

Recommended order, with parallel opportunities:

```
TASK-001
→ TASK-002 / TASK-003 / TASK-006          (parallel)
→ TASK-004 / TASK-005 / TASK-007 / TASK-012  (parallel, per their own deps above)
→ TASK-008
→ TASK-009
→ TASK-010
→ TASK-011
→ TASK-013
→ TASK-014
→ TASK-015 / TASK-016 / TASK-018          (parallel)
→ TASK-017
→ TASK-019
```

**Initially READY (no blocking dependency):** TASK-001

**Blocked tasks and their dependencies:**
- TASK-002: BLOCKED BY TASK-001
- TASK-003: BLOCKED BY TASK-001
- TASK-004: BLOCKED BY TASK-003
- TASK-005: BLOCKED BY TASK-003
- TASK-006: BLOCKED BY TASK-001
- TASK-007: BLOCKED BY TASK-002, TASK-006
- TASK-008: BLOCKED BY TASK-002, TASK-007
- TASK-009: BLOCKED BY TASK-002, TASK-008
- TASK-010: BLOCKED BY TASK-002, TASK-008, TASK-009
- TASK-011: BLOCKED BY TASK-004, TASK-010
- TASK-012: BLOCKED BY TASK-002
- TASK-013: BLOCKED BY TASK-004, TASK-005, TASK-007, TASK-008, TASK-009, TASK-011, TASK-012
- TASK-014: BLOCKED BY TASK-013
- TASK-015: BLOCKED BY TASK-013, TASK-014
- TASK-016: BLOCKED BY TASK-004, TASK-014
- TASK-017: BLOCKED BY TASK-015, TASK-016
- TASK-018: BLOCKED BY TASK-014
- TASK-019: BLOCKED BY TASK-015, TASK-016, TASK-017

**Security-sensitive tasks:** TASK-004 (FR-016 boundary algorithm), TASK-008 (sensitive-value filter), TASK-011 (ownership guard/atomic write), TASK-016 (AC-015 end-to-end security tests).

---

## Traceability: Requirement/AC → Task(s) → Test Task(s)

| Requirement/AC | Task(s) | Test Task(s) |
|---|---|---|
| FR-001 | TASK-014 | TASK-015 |
| FR-002 | TASK-003, TASK-014 | TASK-015 |
| FR-003 | TASK-005, TASK-006, TASK-007 | TASK-015 |
| FR-004 | TASK-005 | TASK-015 (AC-009) |
| FR-005 | TASK-003, TASK-005 | TASK-015 (AC-010) |
| FR-006 | TASK-002, TASK-007 | TASK-015 (AC-002) |
| FR-007 | TASK-010 | TASK-015 (AC-001/AC-002) |
| FR-008 | TASK-003, TASK-011 | TASK-015 (AC-001) |
| FR-009 | TASK-011 | TASK-015 (AC-011) |
| FR-010 | TASK-009 | TASK-015 (AC-004) |
| FR-011 | TASK-009 | TASK-015 (AC-005) |
| FR-012 | TASK-002, TASK-007, TASK-010 | TASK-015 (AC-003) |
| FR-013 | TASK-005, TASK-007, TASK-012, TASK-013 | TASK-015 (AC-006) |
| FR-014 | TASK-012 | TASK-015 (AC-007) |
| FR-015 | TASK-008 | TASK-015 (AC-008) |
| FR-016 | TASK-003, TASK-004, TASK-011 | TASK-016 (AC-012/AC-015) |
| NFR-001 | TASK-006, TASK-005/011/writer via `pathlib` | TASK-017 (AC-013) |
| NFR-002 | TASK-005, TASK-009 | TASK-015 (implicit, skip-write case) |
| NFR-003 | TASK-008 | TASK-015 (AC-008) |
| NFR-004 | TASK-013 | (design-time check — no runtime test, per requirements §11) |
| NFR-005 | TASK-019 (all unit/integration tasks) | TASK-015, TASK-016, TASK-017 (AC-014) |
| AC-001 | TASK-014 | TASK-015 |
| AC-002 | TASK-007, TASK-010 | TASK-015 |
| AC-003 | TASK-002, TASK-010 | TASK-015 |
| AC-004 | TASK-009 | TASK-015 |
| AC-005 | TASK-009 | TASK-015 |
| AC-006 | TASK-005, TASK-007, TASK-012 | TASK-015 |
| AC-007 | TASK-012 | TASK-015 |
| AC-008 | TASK-008 | TASK-015 |
| AC-009 | TASK-005 | TASK-015 |
| AC-010 | TASK-005 | TASK-015 |
| AC-011 | TASK-011 | TASK-015 |
| AC-012 | TASK-003, TASK-011 | TASK-015 |
| AC-013 | (cross-platform properties, TASK-005/006/011) | TASK-017 |
| AC-014 | (all test tasks) | TASK-019 |
| AC-015 | TASK-004 | TASK-016 |

No FR, NFR, or AC is without at least one implementing task and at least one test task.

---

## Validation

1. Every FR (001–016) has at least one task — confirmed above.
2. Every NFR (001–005) has an implementation/verification path — confirmed above (NFR-004 is design-time only, consistent with `docs/requirements.md` §11).
3. Every AC (001–015) has planned test evidence — confirmed above.
4. Every architecture §3 component is represented: CLI Layer→TASK-014; Configuration Resolver→TASK-003/004; Pipeline Orchestrator→TASK-013; Scanner→TASK-005; Parser→TASK-006/007; Model→TASK-002; Sensitive-Value Filter→TASK-008; Change Detector→TASK-009; Renderer→TASK-010; Output Writer→TASK-011; Diagnostics Reporter→TASK-012; Test Suite→TASK-015/016/017/019.
5. DR-001–DR-009 remediations preserved: TASK-004 requires the exact §11.1/ADR-0005 algorithm (DR-001/002); TASK-003/004/011 preserve the two-mechanism split (DR-003); TASK-008 requires decorator-argument filtering (DR-004); TASK-009 requires the per-file JSON hash table (DR-005); TASK-006 requires `tokenize.detect_encoding` (DR-006); TASK-007 requires the full five-exception boundary (DR-007); TASK-011 requires directory creation after the boundary check (DR-008); TASK-004 preserves natural case-sensitivity inheritance (DR-009).
6. No new product requirement introduced: all 19 tasks trace to an existing FR/NFR/architecture component; the packaging decision selects mechanics only, not new product behavior.
7. No application code or test code was created by this plan — only `docs/impl-plan.md`.

No gaps were found in `docs/architecture.md` requiring escalation back to Architecture.
