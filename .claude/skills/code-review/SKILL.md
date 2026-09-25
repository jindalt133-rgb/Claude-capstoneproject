---
name: code-review
description: Methodology for reviewing implementation code against impl-plan.md and requirements.md for correctness, security, and unapproved scope. Use during the Code Review phase.
---

# Code Review Skill

## Purpose

Provide a consistent methodology for critically reviewing implementation changes against the approved plan and requirements — not a generic style pass.

Used by the `code-reviewer` agent.

## Preconditions

* `docs/impl-plan.md` is approved (Gate G3).
* A concrete diff or set of changed files exists to review.

## Review Dimensions

### 1. Requirement and Plan Conformance

* Does the change implement what `impl-plan.md` assigned to this task — no more, no less?
* Does any change trace back to a requirement that is not in `impl-plan.md`? If so, flag as unapproved scope, not a free bonus.

### 2. Correctness

* Logic errors, incorrect edge-case handling, off-by-one/boundary issues.
* Concurrency or ordering issues if applicable.
* Error handling: are failures surfaced clearly, per `CLAUDE.md` quality rules, rather than swallowed?

### 3. Security

* No hardcoded secrets, credentials, or tokens.
* Input from the repository/filesystem is treated as untrusted where relevant (e.g., path traversal, malformed files).
* No unsafe use of dynamic execution, unsanitized shell commands, or unchecked deserialization.

### 4. Testability and Test Coverage

* Are the primary workflow, important edge cases, and important failure scenarios (per `CLAUDE.md` testing rules) actually covered by tests, not just claimed?
* Are tests meaningful (would they fail if the logic were wrong), not tautological?

### 5. Simplification and Duplication

* Is there unnecessary complexity, dead code, or duplicated logic that the plan didn't call for?
* Is naming clear and consistent with the rest of the codebase?

### 6. Traceability

* Can this change be traced back to a specific `impl-plan.md` task and, through it, to a requirement?

## Severity Classification

Classify every finding as:

* **Blocking** — correctness, security, or unapproved-scope issue; must be resolved before Gate G4.
* **Non-blocking** — style/maintainability suggestion; can be deferred with human agreement.

Do not silently fix blocking issues yourself as part of "reviewing" — report them. Fixing is the `developer` agent's job, after the human/orchestrator has seen the finding.

## Anti-patterns to avoid

* Approving because "it looks fine" without checking against `impl-plan.md`/`requirements.md`.
* Treating unrelated refactors introduced in the same diff as acceptable by default — flag scope creep explicitly.
