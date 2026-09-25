# Code Review: Automated Documentation Sync (`docsync`) v1

**Reviewer:** code-review agent (independent, fresh-context review — no memory of authoring this code)
**Phase:** SDLC Phase 6 (Code Review), gating Phase 7 (Verification), per `CLAUDE.md`
**Scope:** all of `docsync/` and `tests/` (entire codebase is untracked/new — confirmed via `git status`; no prior commit history to diff against)
**Source of truth used:** `docs/requirements.md` (Gate G1), `docs/architecture.md` (post design-review remediation), `docs/impl-plan.md` (TASK-001–019), `pyproject.toml`

---

## Summary

| Severity | Count |
|---|---|
| BLOCKER | 1 |
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 6 |
| **Total** | **12** |

**Test-suite status:** Command run: `py -m pytest -q -rs` (from repo root, after `py -m pip install -e .`).
Observed result: **98 passed, 3 skipped, 0 failed.** The 3 skips are environment-conditional, not code defects:
- `tests/integration/test_path_security.py::test_ac015_symlink_escape_rejected_when_platform_supports_it` — skipped: symlink creation not permitted in this environment.
- `tests/unit/test_config.py::test_boundary_check_rejects_symlink_escape` — skipped: symlink creation not permitted in this environment.
- `tests/unit/test_scanner.py::test_scan_unreadable_subtree_reported_not_fatal` — skipped intentionally on Windows (permission-bit simulation is unreliable there).

**Security-review status (one line per sub-area):**

| Sub-area | Status |
|---|---|
| Output-path boundary check (`config.boundary_check`), steps 1–4 (empty/absolute/drive/UNC/traversal rejection) | PASS — verified step-by-step against architecture §11.1; matches exactly |
| Boundary check containment (step 8, path-object `is_relative_to`/`parents` check, sibling-prefix defense) | PASS — confirmed not string-prefix-based; `../generated-evil/x.md` correctly rejected |
| Boundary check symlink-escape handling (steps 7/10) | PASS by code inspection (relies on `Path.resolve()`); unit/integration tests for this exist but were skipped in this environment due to lack of symlink permission, not a code issue |
| Boundary check — root-directory edge case | **CONCERN — see COR-01/BLOCKER.** A candidate that resolves to `docs/generated` itself (e.g. `--output .`) is incorrectly accepted |
| Ownership-marker guard (`writer.py`) vs. boundary check — mechanism separation (DR-003) | PASS — confirmed the two checks are implemented in different modules, at different times, and `boundary_check` is called exactly once, only from `config.py` |
| Ownership-marker guard robustness | PASS for its stated (narrower, defense-in-depth) purpose; substring marker check is deliberately not a hard boundary per architecture, and this is by design, not a gap |
| Sensitive-value filter — named/vendor-format secrets (PEM keys, AKIA…, sk-live-…, ghp_…, URL credentials) | PASS — all confirmed redacted by direct testing |
| Sensitive-value filter — keyword-name heuristic for compound identifiers | **CONCERN — see SEC-01/HIGH.** `db_password`, `client_secret`, `admin_token`, etc. are not redacted at all |
| Secrets committed to the repository (source + test fixtures) | PASS — none found; all sensitive-looking strings in `sensitive.py`/`test_sensitive.py` are clearly fake example values used to test the redaction logic |
| Dependency safety (`pyproject.toml`) | PASS — zero runtime dependencies confirmed; `pytest` correctly dev-only |

**Are fixes required before Verification?** **Yes.** COR-01 (BLOCKER) must be fixed before Verification — it is a confirmed, reproducible defect that corrupts the `docs/generated/` boundary itself and then crashes the tool on every subsequent run with an unhandled traceback. SEC-01 and ERR-01 (both HIGH) should also be fixed before Verification, since they represent a real, easily-triggered security-filter gap and a systemic robustness gap respectively; shipping Verification against the current code would validate behavior that materially understates risk in both areas.

---

## 1. Correctness (FR-001–FR-016 vs. implementation and architecture.md)

Overall, the pipeline sequencing, model structure, sentinel handling, exception-boundary set (parser), hash-table format, and CLI surface all match `architecture.md` closely and faithfully implement `impl-plan.md`'s task breakdown. The findings below are the exceptions.

### COR-01 — BLOCKER
**File/location:** `docsync/config.py` (`boundary_check`, lines 78–139), `docsync/writer.py` (`write_output`, lines 33, 37–43), `docsync/core.py` (`run`, lines 79–83), `docsync/cli.py` (`main`, lines 42–58)
**Related:** FR-008, FR-014, FR-016, AC-015

**Problem:** `boundary_check` accepts any candidate whose resolved path is `docs/generated` itself, not just a file *within* it — e.g. `--output .`. Nothing in the 12-step algorithm (nor architecture §11.1 as written) rejects `real_candidate == real_root`; the containment check in step 8 explicitly treats equality as acceptable. Combined with `writer.py` having no "target is a directory" guard and no general exception handling in `core.run`/`cli.main` around the write step, this is independently reproducible and confirmed by direct execution:

```
$ docsync --source srcpkg --output .
documentation written: <cwd>/docs/generated      # docs/generated is now a FILE, not a directory
```

A second, ordinary run (no `--output` override) then crashes with an unhandled traceback:
```
FileExistsError: [WinError 183] Cannot create a file when that file already exists: '...\docs\generated'
  ... docsync/writer.py, line 33, in write_output
      target.parent.mkdir(parents=True, exist_ok=True)
```

**Impact:** A single plausible CLI invocation permanently corrupts the `docs/generated/` boundary (turns the directory into a plain file), directly violating FR-008 ("write generated documentation under `docs/generated/`" — there is no longer a directory there to write under). Every subsequent invocation of the tool (even with no `--output` at all) then crashes with a raw Python traceback instead of a clean, file-identified error, violating FR-014. This is not a narrow one-line edge case fix — it requires either rejecting the root-equals-candidate case in the boundary check, or hardening the writer/orchestrator against the target (or an ancestor of it) being an unexpected non-directory, or both, plus a general exception boundary around the write stage (see ERR-01, same root defect from a different angle).

**Recommended fix:** In `boundary_check`, reject `real_candidate == real_root` (a `--output` value must denote a file location *inside* `docs/generated/`, not the directory itself) as an explicit additional rule. Independently, in `core.run`/`cli.main`, add a general `except OSError` (or broader) boundary around the write stage that reports a clean FR-014 diagnostic and a non-zero exit code instead of propagating a raw traceback, so that any future filesystem anomaly at this stage (this one, or something unrelated like disk full or a permission error) degrades gracefully rather than crashing the whole process.

### COR-02 — MEDIUM
**File/location:** `docsync/render.py`, `_docstring_block` (lines 19–20); same pattern also present in `_format_parameter` (lines 25–27) and `_format_signature` (line 36) with lower practical risk
**Related:** FR-012, architecture §9 (two-sentinel distinction)

**Problem:** `_docstring_block` decides whether to show `_Not available_` purely by Python truthiness (`str(docstring) if docstring else NOT_AVAILABLE_MARKER`). `UNAVAILABLE`'s `__bool__` is `False` by design, which is correct for the "no docstring at all" case — but `ast.get_docstring()` can legitimately return an actual empty string `""` for a real (if degenerate) empty docstring (`""""""`), and `""` is also falsy in Python. Confirmed by direct reproduction: a module with docstring `""""""` renders `_Not available_` even though a docstring is genuinely present (just empty).

**Impact:** Conflates "cannot be determined" (`UNAVAILABLE`) with "determined to be an empty string" — exactly the distinction architecture §9 says the renderer "must render... distinguishably." Low real-world frequency (empty docstrings are rare), but it is a genuine, reproducible logic defect in the FR-012 guarantee, not merely a style nit.

**Recommended fix:** Use an explicit identity/type check (`if docstring is UNAVAILABLE: ... else: str(docstring)`) instead of bare truthiness, in `_docstring_block` and the analogous spots in `_format_parameter`/`_format_signature`.

### COR-03 — LOW
**File/location:** `docsync/scanner.py`, lines 52 and 56 (`entry.is_dir(follow_symlinks=False)`, `entry.is_file(follow_symlinks=False)`)
**Related:** FR-003, architecture §7

**Problem:** Architecture §7 states the scanner's source-side symlink handling should be "unspecial-cased, ordinary filesystem walk... no requirement drives it to be anything else" (explicitly contrasted with the *deliberately* symlink-following output-boundary check). The implementation instead explicitly passes `follow_symlinks=False` on both checks, so a symlinked `.py` file (or directory) inside the source tree is silently skipped entirely — neither yielded as a candidate file nor descended into. This is itself a special case, and a different one than "ordinary walk" (an ordinary `is_file()`/`rglob()` walk follows symlinks by default for files).

**Impact:** Low — symlinked source files are uncommon, and skipping them is arguably a defensible security-conscious default, but it is an undocumented deviation from what architecture actually specifies, and it means such files are silently excluded from documentation with no diagnostic reported (contrast with FR-013/FR-014's "report clearly" ethos for skipped content).

**Recommended fix:** Either change to the architecture's stated default (follow symlinks for file/type checks, matching plain `rglob`), or update architecture.md to record this as a deliberate, human-approved deviation (per Change Control) if the current behavior is actually preferred.

---

## 2. Security

See the Summary table above for the sub-area-by-sub-area status. Detailed findings:

### SEC-01 — HIGH
**File/location:** `docsync/sensitive.py`, lines 25 (`_SECRET_NAME_WORDS`), 43–45 (keyword=value content pattern), 48 (`_SECRET_PARAMETER_NAME`)
**Related:** FR-015, NFR-003, AC-008

**Problem:** Both the free-text `keyword=value` pattern and the parameter-name heuristic anchor the secret keyword at the *start* of an identifier (`\b` before the keyword, or `^` for the parameter-name regex). Because `_` is a word character in regex, there is no `\b` boundary between an identifier prefix and the keyword when they are joined by an underscore. Confirmed by direct testing:

```python
>>> redact('db_password = "hunter2"')      # NOT redacted
>>> redact('client_secret = "abc"')         # NOT redacted
>>> redact('admin_token = "xyz"')           # NOT redacted
>>> redact('my_api_key = "sk"')             # NOT redacted
```
And end-to-end through `filter_module`:
```python
extract + filter of: def connect(db_password="SuperSecret123", client_secret="abc-def-ghi"): ...
-> db_password -> 'SuperSecret123'      # leaks verbatim
-> client_secret -> 'abc-def-ghi'       # leaks verbatim
```

**Impact:** `db_*`, `client_*`, `admin_*`, `user_*`, `my_*`-prefixed secret names are an extremely common real-world convention (database clients, OAuth/API clients, config objects). A parameter or keyword argument named this way, with a hardcoded literal default, sails straight through both the content-based and name-based heuristics untouched, all the way into the generated Markdown — directly defeating the FR-015/NFR-003 protection for a very ordinary case, not an exotic one. (NFR-003 does accept that the filter is heuristic/non-exhaustive, so this is not rated BLOCKER, but the specific gap is common enough and easy enough to close that it should not ship as-is.)

**Recommended fix:** Replace the `\b`/`^` anchors with a substring/contains check on the secret-name words within a parameter or assignment target's identifier (e.g. `_SECRET_NAME_WORDS` search anywhere in the identifier, not just as a strict prefix), while keeping the current word-list scope.

### SEC-02 — see COR-01 (BLOCKER)
The `docs/generated` root-equals-candidate gap in `boundary_check` is, structurally, a defect in the FR-016 boundary algorithm itself (the single most security-sensitive function in this codebase per `impl-plan.md` TASK-004). Full detail, reproduction, and recommended fix are under COR-01 above to avoid duplicating the write-up; it is cross-referenced here because it is squarely a security-control gap, not just a general correctness bug.

### SEC-03 (informational) — LOW
**File/location:** `docsync/writer.py`, lines 25–43
**Related:** FR-009, ADR-0004

**Problem:** The target path handed to `write_output` is resolved once, at configuration time (before scanning/parsing run), and reused unchanged through the rest of the pipeline. There is a theoretical TOCTOU window between that resolution and the writer's `target.exists()`/marker check: if the filesystem at the target path changes during scanning/parsing (e.g., something else creates a symlink there), the writer's decision could be made against stale assumptions.

**Impact:** Low. This is consistent with, and only relevant outside of, the documented single-user/non-concurrent assumption in `docs/requirements.md` §8 and `docs/architecture.md` §1 ("no concurrency... no persistent process") — neither document asks the implementation to defend against concurrent filesystem mutation, so this is not a violation of any stated requirement, just a residual observation.

**Recommended fix:** None required given the stated single-user assumption; noting for completeness only.

---

## 3. Error Handling

### ERR-01 — HIGH
**File/location:** `docsync/core.py`, lines 76–85 (`run`, the `write_output` call is only wrapped for `WriteRefusedError`); `docsync/cli.py`, lines 42–58 (`main`, no `try/except` around `run(config)` at all)
**Related:** FR-013, FR-014

**Problem:** There is no general exception boundary around the write stage. `core.run` catches exactly one exception type (`WriteRefusedError`) around `write_output`; `cli.main` catches nothing around `run(config)`. Any *other* unexpected `OSError` at write time — not just the COR-01 scenario, but also e.g. a pre-existing non-directory obstruction anywhere along `docs/` or `docs/generated/`'s path, a disk-full condition, a permission error that appears mid-write, or an antivirus lock on Windows — propagates all the way out of `main()` as a raw, uncaught Python traceback.

**Impact:** Directly contradicts FR-014's "clearly communicate important errors" — a raw traceback is not a clear, file-identified, human-readable error message, and the process still exits with whatever exit code an uncaught exception produces (1, but via Python's default handler, not the tool's own diagnostics/exit-code logic), which happens to coincide with the "error occurred" convention but for the wrong reason and with no useful message for the user. This is a systemic gap, reproducibly triggered by COR-01 but not limited to it.

**Recommended fix:** Wrap the write stage (and arguably the whole `run()` body) in a broad `except OSError` (at minimum) that converts to a `DocSyncError`/diagnostic entry, consistent with how `read_source`/`extract_module`/the scanner already isolate per-file failures.

### ERR-02 — LOW
**File/location:** `docsync/scanner.py`, `_walk` (lines 42–61)
**Related:** FR-013, architecture §7

**Problem:** Only the initial `os.scandir(directory)` call is wrapped in `try/except OSError`. The subsequent per-entry calls (`entry.is_dir(follow_symlinks=False)`, `entry.is_file(follow_symlinks=False)`, `entry_path.relative_to(source_dir)`) are not — on some platforms/filesystems a broken symlink or a file removed mid-walk can cause `os.DirEntry.is_dir()`/`is_file()` to raise `OSError`, which would propagate up and abort the walk of that subtree without being recorded as a `ScanError`.

**Impact:** Low-probability edge case, but it would violate the "one bad location does not block valid ones" extension to directories that architecture §7 calls for.

**Recommended fix:** Move the per-entry `is_dir`/`is_file` calls inside a narrower `try/except OSError` that records a `ScanError` for that specific entry and continues, rather than only guarding the top-level `scandir` call.

---

## 4. Test Coverage

The suite is well-designed overall: assertions are on real, specific content (rendered text, hash equality/inequality, exact exit codes, filesystem snapshots), not tautological placeholders; `unittest.mock.patch` is used appropriately to inject each of the five parser exception types individually and to simulate a write interruption; the AC-015 integration suite (`tests/integration/test_path_security.py`) mirrors `docs/architecture.md` §19's negative-case list essentially one-for-one, including the sibling-prefix and symlink-escape cases, with a positive control. Every AC-001–AC-015 has at least one test that would actually fail if the corresponding logic regressed. Two coverage gaps, both directly related to findings above:

### TEST-01 — MEDIUM
**File/location:** `tests/unit/test_config.py` (boundary-check section, lines 86–183)
**Related:** FR-016, AC-015, COR-01

**Problem:** No test exercises a candidate that resolves to the `docs/generated` root itself (e.g. `boundary_check(".")`), nor an `--output` value that collides with a pre-existing directory at the target path. This is exactly the untested edge that COR-01 exploits.

**Recommended fix:** Add a unit test asserting `boundary_check(".")` (and similar root-resolving candidates) is rejected once COR-01 is fixed, plus a writer/integration test where the resolved target path already exists as a directory.

### TEST-02 — MEDIUM
**File/location:** `tests/unit/test_sensitive.py`
**Related:** FR-015, NFR-003, SEC-01

**Problem:** Every keyword-heuristic test case uses the secret word as the *entire* identifier (`password`, `api_key`) or a clearly vendor-prefixed literal (`AKIA...`, `sk_live_...`, `ghp_...`). No test uses a compound/prefixed identifier such as `db_password` or `client_secret`, so the SEC-01 gap was not caught by the existing test suite despite otherwise good coverage of the stated NFR-003 categories.

**Recommended fix:** Add test cases for compound secret-suggestive names once SEC-01 is fixed, to lock in the fix and prevent regression.

---

## 5. Code Clarity

Overall clarity is good: module-level docstrings consistently cross-reference the specific architecture section and DR-number they implement, naming is consistent (`ModuleDoc`/`ClassDoc`/`FunctionDoc`/`ParameterDoc` mirror architecture §9 exactly), and each module has a clear single responsibility matching architecture §3/§4. One minor finding:

### CLR-01 — LOW
**File/location:** `docsync/parser.py`, `extract_module(path: Path, source: str)` (line 174); called from `docsync/core.py` line 54 with a plain `str` (`relative`, from `.as_posix()`)
**Related:** none specific (maintainability only)

**Problem:** The type annotation says `path: Path`, but the only real caller (`core.run`) always passes a `str`. This works today only because `ModuleDoc(path=str(path), ...)` makes `str()` a no-op on an already-`str` value; it is misleading for a future maintainer reading the signature, and would silently break if `path`'s `Path`-specific methods were ever relied on inside `extract_module`.

**Recommended fix:** Change the annotation to `path: str` (matching actual usage), or have `core.run` pass an actual `Path` and have `extract_module` call `.as_posix()`/`str()` itself.

---

## 6. DRY

No unnecessary duplication was found beyond two very minor items:

### DRY-01 — LOW
**File/location:** `docsync/config.py`, line 23 (`GENERATED_ROOT_NAME = "docs/generated"`)

**Problem:** This constant is defined but never referenced anywhere in the codebase; `boundary_check`'s default root instead hardcodes the literal `Path("docs/generated")` at line 117. Two sources of truth for the same value exist only by coincidence of both currently being correct.

**Recommended fix:** Either use `GENERATED_ROOT_NAME` in `boundary_check`'s default, or remove the unused constant.

### DRY-02 — LOW
**File/location:** `docsync/config.py`, `boundary_check` (lines 90–131)

**Problem:** The error-message prefix `"configured output path resolves outside docs/generated/: {candidate!r} "` is repeated (with only the trailing clause differing) across the absolute-path, drive/UNC, and traversal rejection branches.

**Recommended fix:** Factor into a small helper (e.g. `_reject(candidate, reason)`) to reduce duplication and the risk of the copies drifting apart under future edits.

---

## 7. Dependency Safety

**No findings.** `pyproject.toml` declares `dependencies = []` — genuinely zero runtime dependencies, matching the architecture's stated claim (ADR-0001/ADR-0002) exactly. `pytest>=7.0` is correctly scoped under `[project.optional-dependencies].dev`, not a runtime dependency. `setuptools>=68` appears only in `[build-system]` (build-time only, standard for a `pyproject.toml`-based package). No unnecessary or risky packages are declared anywhere. This dimension is clean.

---

## Traceability of Findings to Requirements

| Finding | Severity | FR/NFR/AC |
|---|---|---|
| COR-01 | BLOCKER | FR-008, FR-014, FR-016, AC-015 |
| SEC-01 | HIGH | FR-015, NFR-003, AC-008 |
| ERR-01 | HIGH | FR-013, FR-014 |
| COR-02 | MEDIUM | FR-012 |
| TEST-01 | MEDIUM | FR-016, AC-015 (test gap for COR-01) |
| TEST-02 | MEDIUM | FR-015, NFR-003 (test gap for SEC-01) |
| COR-03 | LOW | FR-003 |
| SEC-03 | LOW | FR-009 (informational) |
| ERR-02 | LOW | FR-013 |
| CLR-01 | LOW | maintainability |
| DRY-01 | LOW | maintainability |
| DRY-02 | LOW | maintainability |

---

## Remediation

Performed per the human's remediation-approval instruction (priority: COR-01 → SEC-01 → ERR-01 → MEDIUM → LOW). All fixes are code-only; no approved requirement or architecture artifact was changed.

| Finding | Severity | Status | Evidence |
|---|---|---|---|
| COR-01 | BLOCKER | **RESOLVED** | `docsync/config.py`, `boundary_check` step 8: changed the containment check from `real_candidate == real_root or real_root in real_candidate.parents` to `real_root not in real_candidate.parents`, so a candidate resolving to the `docs/generated/` root itself (e.g. `--output .`) is now rejected, not accepted. New tests: `tests/unit/test_config.py::test_boundary_check_rejects_root_itself_via_dot`, `::test_boundary_check_rejects_candidate_resolving_exactly_to_root`, `::test_resolve_config_rejects_output_dot`; `tests/integration/test_path_security.py::test_ac015_output_dot_rejected_with_no_write_to_generated` (asserts a before/after filesystem snapshot equality — `docs/generated/` is provably untouched on rejection). All existing traversal/security cases in both files continue to pass unchanged. |
| SEC-01 | HIGH | **RESOLVED** | `docsync/sensitive.py`: replaced the `\b` word-boundary anchor (which never matches before a keyword joined by `_`, since `_` is a `\w` character) with `(?<![A-Za-z0-9])` in the keyword=value content pattern, and added an optional `(?:\w+_)?` prefix group to `_SECRET_PARAMETER_NAME`, so `db_password`, `client_secret`, `admin_token`, `my_api_key` are recognized as whole underscore-delimited segments. Did **not** broaden to a bare substring/contains check (the BLOCKER writeup's own suggested fix) specifically because that would flag unrelated words such as `mypasswordmanager`; the delimiter-aware fix avoids this. New positive tests: `test_redact_keyword_value_pair_for_compound_identifiers`, `test_filter_parameter_default_secret_by_compound_keyword_name` (all four required examples). New negative controls: `test_filter_parameter_default_not_redacted_for_unrelated_word` (`mypasswordmanager`, `username` left untouched), `test_redact_leaves_unrelated_word_in_free_text_untouched` (`password manager`/`passwordless` free text left untouched). All 16 tests in `tests/unit/test_sensitive.py` pass. |
| ERR-01 | HIGH | **RESOLVED** | `docsync/core.py`, `run`: added `except OSError as exc:` alongside the existing `except WriteRefusedError as exc:` around the `write_output(...)` call, converting any other filesystem failure at write time into a `DocSyncError(stage="write")` diagnostic instead of an uncaught traceback. New file `tests/unit/test_core.py`: `test_run_converts_unexpected_oserror_at_write_to_diagnostic` (simulated `OSError` is caught and reported, `written=False`, `exit_code()==1`), `test_run_still_reports_write_refused_error_as_diagnostic` (confirms the pre-existing `WriteRefusedError` path is unchanged), `test_run_writes_successfully_when_no_error` (happy-path baseline). All 3 pass. |
| COR-02 | MEDIUM | **RESOLVED** | `docsync/render.py`: `_docstring_block`, `_format_parameter`, `_format_signature` now use identity checks (`is UNAVAILABLE` / `is not UNAVAILABLE` / `is not NOT_APPLICABLE`) instead of Python truthiness, so a genuinely empty docstring (`""`) or a falsy-but-determined value (`0`, `""`) is never confused with the UNAVAILABLE/NOT_APPLICABLE sentinels. New tests: `tests/unit/test_render.py::test_render_genuinely_empty_docstring_not_confused_with_unavailable`, `::test_render_zero_default_and_empty_annotation_not_confused_with_sentinels`. All 7 tests in `test_render.py` pass. |
| TEST-01 | MEDIUM | **RESOLVED** | Directly closed as a side effect of the COR-01 fix above — the previously-missing root-resolving-candidate test cases (`boundary_check(".")` and equivalents) now exist in `test_config.py` and `test_path_security.py` (see COR-01 row). |
| TEST-02 | MEDIUM | **RESOLVED** | Directly closed as a side effect of the SEC-01 fix above — compound/prefixed secret-name test cases (`db_password`, `client_secret`, `admin_token`, `my_api_key`) now exist in `test_sensitive.py` (see SEC-01 row). |
| COR-03 | LOW | **RESOLVED** | `docsync/scanner.py`, `_walk`: removed `follow_symlinks=False` from both `entry.is_dir()`/`entry.is_file()` calls, restoring the default (symlink-following) behavior that `docs/architecture.md` §7/§18 explicitly specify for the source-side walk ("unspecial-cased, ordinary filesystem walk... no requirement drives it to be anything else") — confirmed by direct re-reading of that wording before making the change, so this aligns code to already-approved architecture rather than requiring an architecture change. New test: `test_scan_follows_symlinked_py_file_in_source_tree` (skipped in this Windows environment — symlink creation is not permitted here without elevated privilege, consistent with the pre-existing skip pattern for the other symlink-dependent tests in this suite; the code change itself was verified by direct reading, and the full suite shows no regression). |
| SEC-03 | LOW | **ACCEPTED** | No code change. Rationale (unchanged from the original review): the TOCTOU window between output-path resolution and the writer's existence/marker check is a real but out-of-scope concern under the documented single-user/non-concurrent assumption in `docs/requirements.md` §8 and `docs/architecture.md` §1 ("no concurrency... no persistent process"). Neither document asks the implementation to defend against concurrent filesystem mutation. Fixing this would require introducing new concurrency-defense requirements/architecture not currently approved — exactly the kind of change the human asked to be stopped and asked about, and the review's own recommended fix was "None required given the stated single-user assumption." |
| ERR-02 | LOW | **RESOLVED** | `docsync/scanner.py`, `_walk`: moved the per-entry `entry.is_dir()`/`entry.is_file()` calls (previously unguarded) inside the same `try/except OSError` scope as `relative_to`, recording a `ScanError` for that specific entry and continuing the walk, instead of only guarding the top-level `os.scandir()` call. New test: `test_scan_per_entry_oserror_reported_not_fatal` (a fake `DirEntry` that raises `OSError` from `is_dir()`/`is_file()` is recorded as one `ScanError` while a sibling healthy file is still found). Passes. |
| CLR-01 | LOW | **RESOLVED** | `docsync/parser.py`: changed `extract_module(path: Path, ...)` to `extract_module(path: str, ...)`, matching the only real caller (`core.run`, which always passes a `str`). New test: `test_extract_module_accepts_plain_str_path_as_actually_used_in_production`. All 15 tests in `test_parser.py` pass (existing tests that happen to pass a `Path` literal still pass too, since `str(Path)` is a no-op-equivalent conversion — no behavior change, annotation-only fix). |
| DRY-01 | LOW | **RESOLVED** | `docsync/config.py`: `boundary_check`'s default root now reads `Path(GENERATED_ROOT_NAME)` instead of a second hardcoded `"docs/generated"` literal, restoring a single source of truth. No dedicated new test added (a test exercising the true default, i.e. omitting `generated_root`, would touch the real repository's `docs/generated/` directory, which every existing test deliberately avoids by passing a `tmp_path`-scoped override) — covered instead by the full existing `boundary_check`/`resolve_config` test suite continuing to pass unchanged, confirming the refactor is behavior-preserving. |
| DRY-02 | LOW | **RESOLVED** | `docsync/config.py`: factored the repeated `"configured output path resolves outside docs/generated/: {candidate!r} (...)"` error-message prefix into a new `_reject(candidate, reason)` helper, used at all four rejection sites (absolute, drive/UNC, traversal, containment). Behavior-preserving; confirmed by the full existing boundary-check test suite (which asserts `ConfigError` is raised in each case) continuing to pass unchanged. |

### Full test-suite result after remediation

Command: `python -m pytest -q -rs` (repo root).

```
113 passed, 4 skipped, 0 failed
```

Skips (all environment-conditional, none are code defects — same three pre-existing skips as the original review, plus one new skip of the same kind for the new COR-03 symlink test):
- `tests/integration/test_path_security.py::test_ac015_symlink_escape_rejected_when_platform_supports_it` — symlink creation not permitted in this environment.
- `tests/unit/test_config.py::test_boundary_check_rejects_symlink_escape` — symlink creation not permitted in this environment.
- `tests/unit/test_scanner.py::test_scan_unreadable_subtree_reported_not_fatal` — permission-bit simulation unreliable on Windows.
- `tests/unit/test_scanner.py::test_scan_follows_symlinked_py_file_in_source_tree` (new, COR-03 regression test) — symlink creation not permitted in this environment.

### Remaining findings after remediation

| Severity | Remaining |
|---|---|
| BLOCKER | **0** |
| HIGH | **0** |
| MEDIUM | **0** |
| LOW | **0** (11 RESOLVED, 1 ACCEPTED — SEC-03, informational, no fix required) |

### Requirement / acceptance-criteria coverage after remediation

- **FR-001–FR-016: all remain satisfied.** No requirement's behavior was narrowed or removed; COR-01/SEC-01/ERR-01/COR-02/COR-03/ERR-02/CLR-01/DRY-01/DRY-02 were all defects or maintainability gaps *within* the approved requirements/architecture, not requirement changes. FR-016 (output boundary) and FR-015 (sensitive-value filter) are now *more* strictly enforced than before, in the direction the requirements already specified, not a new direction.
- **AC-001–AC-015: all remain covered**, and AC-015 (path-boundary security) and AC-008 (sensitive-value redaction) are now covered more precisely than in the original review (root-resolving `--output` candidates and compound secret identifiers are now exercised by name).
- No upstream artifact (`docs/requirements.md`, `docs/architecture.md`) required a change; every fix was contained to `docsync/` source and `tests/`.
