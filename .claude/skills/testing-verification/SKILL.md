---
name: testing-verification
description: Methodology for independently verifying that an implementation meets requirements.md and impl-plan.md — running tests, checking coverage of edge/failure cases, and producing verification.md. Use during the Verification phase.
---

# Testing & Verification Skill

## Purpose

Provide a consistent methodology for independently confirming an implementation actually works and meets approved requirements, rather than trusting the developer's or code-reviewer's self-report.

Used by the `verifier` agent.

## Preconditions

* Implementation exists for the task(s) being verified.
* `docs/code-review.md` blocking findings are resolved.

## Verification Framework

### 1. Requirement Traceability Check

For each FR/NFR in `docs/requirements.md` that this implementation claims to satisfy, identify the test(s) that exercise it. A requirement with no corresponding test is a gap, not a pass.

### 2. Coverage Categories

Confirm tests exist for, per the `CLAUDE.md` testing rules:

* Primary successful workflow(s).
* Important edge cases (boundary conditions, empty/large inputs, etc., as implied by requirements).
* Important failure scenarios (invalid input, missing dependency, unexpected repository state).
* Missing or invalid inputs where applicable.

### 3. Execution

Actually run the test suite and any build/lint checks — do not infer results from reading code. Record:

* Command(s) run.
* Pass/fail outcome.
* Any skipped or flaky tests, and why.

### 4. Acceptance Criteria Check

Walk through the acceptance criteria in `docs/requirements.md` one by one and state, with evidence, whether each is met, not met, or not testable as currently specified.

### 5. Reporting

Produce `docs/verification.md` containing:

* Requirement-to-test traceability table.
* Test execution results.
* Acceptance criteria results.
* Any gap or failure, classified as blocking (must fix before Gate G5) or non-blocking.

## Anti-patterns to avoid

* Reporting "tests pass" without having actually executed them in this pass.
* Treating high code coverage percentage as a substitute for checking the specific scenarios above.
* Marking an acceptance criterion "met" when it was never actually stated as objectively testable — flag it as ambiguous instead.
