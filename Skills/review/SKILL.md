---
name: review
description: Methodology for critically reviewing implementation changes against impl-plan.md and requirements.md, classifying findings, and producing docs/code-review.md. Used by Agents/review.agent.md.
---

# Code Review Skill

Adapted from the project's existing `code-review` methodology (`.claude/skills/code-review/SKILL.md`); paths updated to the root-level artifact layout.

## Purpose

Provide a consistent methodology for critically reviewing implementation changes against the approved plan and requirements — not a generic style pass, and not a rubber stamp.

## Inputs / Prerequisites

* `impl-plan.md` — approved (Gate G3).
* `requirements.md`.
* A concrete diff or set of changed files from the Implementation phase (`git status`/`git diff`, read-only).

## Method / Workflow

Review the diff against these six dimensions:

1. **Requirement and Plan Conformance** — does the change implement what `impl-plan.md` assigned to this task, no more and no less? Anything traceable to a requirement absent from `impl-plan.md` is unapproved scope, not a free bonus.
2. **Correctness** — logic errors, incorrect edge-case handling, boundary issues, concurrency/ordering issues if applicable, and whether failures are surfaced clearly rather than swallowed.
3. **Security** — no hardcoded secrets/credentials/tokens; untrusted input (filesystem/repository content) is handled defensively; no unsafe dynamic execution, unsanitized shell commands, or unchecked deserialization.
4. **Testability and Test Coverage** — are the primary workflow, important edge cases, and important failure scenarios actually covered by tests (not just claimed), and are those tests meaningful (would fail if the logic were wrong)?
5. **Simplification and Duplication** — unnecessary complexity, dead code, or duplicated logic the plan didn't call for; naming clarity and consistency.
6. **Traceability** — can the change be traced back to a specific `impl-plan.md` task and, through it, to a requirement?

## Validation Checks

* Every finding is classified as **blocking** (must be resolved before Gate G4) or **non-blocking** (recommendation, may be deferred with human agreement).
* The overall verdict is explicit: "Ready for Gate G4" only if there are zero blocking findings.
* Unrelated changes bundled into the same diff are flagged as scope creep explicitly, not accepted by default because they "look harmless."
* No finding was softened to allow progress.

## Expected Evidence / Output

`docs/code-review.md`, containing the classified findings list (blocking vs. non-blocking) and an explicit overall verdict.

## Failure / Stop Conditions

* No concrete diff/changed-file set is available to review — stop and report.
* A blocking finding exists — do not mark the review "Ready for Gate G4"; route it back to the implementation agent (or the human, if a product decision is required).

## Traceability Expectations

Each finding should cite the specific task/file/requirement it concerns, so a blocking finding can be routed back to a concrete, actionable spot rather than a vague "needs work."

## Security Considerations

Specifically check for hardcoded secrets/credentials, unsafe handling of untrusted input, and unsafe use of dynamic execution or shell commands; do not treat a passing test suite as evidence that a security concern is resolved.
