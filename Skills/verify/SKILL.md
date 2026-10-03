---
name: verify
description: Methodology for independently confirming an implementation meets requirements.md by actually executing tests and checking acceptance criteria, producing docs/verification-report.md. Used by Agents/verify.agent.md.
---

# Verification Skill

Adapted from the project's existing `testing-verification` methodology (`.claude/skills/testing-verification/SKILL.md`); output path corrected to `docs/verification-report.md` (the actual artifact filename — `docs/verification.md` referenced in the older `.claude/` methodology was never the real filename) and updated to the root-level artifact layout.

## Purpose

Provide a consistent methodology for independently confirming an implementation actually works and meets approved requirements, rather than trusting the implementation or code-review agent's self-report.

## Inputs / Prerequisites

* `docs/code-review.md` — must show "Ready for Gate G4" with zero unresolved blocking findings.
* `requirements.md`.
* Application source code and tests.

## Method / Workflow

1. **Requirement Traceability Check** — for each FR/NFR in `requirements.md`, identify the test(s) that exercise it. A requirement with no corresponding test is a gap, not a pass.
2. **Coverage Categories** — confirm tests exist for: primary successful workflow(s); important edge cases (boundary conditions, empty/large inputs, etc.); important failure scenarios (invalid input, missing dependency, unexpected repository state); missing or invalid inputs where applicable.
3. **Execution** — actually run the test suite and any build/lint checks; do not infer results from reading code. Record the exact command(s) run, the pass/fail outcome, and any skipped or flaky tests with a reason.
4. **Acceptance Criteria Check** — walk every acceptance criterion in `requirements.md` and state, with evidence, whether it is met, not met, or not objectively testable as written.
5. **Reporting** — produce `docs/verification-report.md` with the traceability table, execution results, acceptance-criteria results, and an overall verdict.

## Validation Checks

* Every acceptance criterion has a stated, evidenced result (met / not met / not objectively testable).
* Test execution commands and outcomes are recorded verbatim, not inferred from static reading.
* High code-coverage percentage was not treated as a substitute for checking the specific required scenarios.
* Any gap or failure is classified blocking (must fix before Gate G5) or non-blocking.

## Expected Evidence / Output

`docs/verification-report.md`, containing the requirement-to-test traceability table, test execution results, acceptance-criteria results, and an overall verdict (PASS, PASS WITH DOCUMENTED LIMITATIONS, or FAIL).

## Failure / Stop Conditions

* `docs/code-review.md` does not show "Ready for Gate G4" — stop before starting verification.
* A required test was not actually executed in this pass — do not report its result as observed.
* An acceptance criterion is ambiguous as written — flag it as not objectively testable rather than marking it "met."

## Traceability Expectations

Requirement → Test(s) → executed result, so a blocking gap can be routed back to a specific missing or inadequate test rather than a vague "coverage is low."

## Security Considerations

Verify that security-relevant NFRs and acceptance criteria are checked with real evidence (e.g., an actual malformed-input test run), not asserted from reading the implementation; do not report a security-relevant test as passing without having executed it.
