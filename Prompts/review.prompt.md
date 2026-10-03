---
name: review
description: Entry prompt for the Code Review phase of the Agentic SDLC.
---

# Code Review Prompt

## Invoke Agent

Read and follow `Agents/review.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/review/SKILL.md` for the review methodology (plan/requirement conformance, correctness, security, testability/coverage, simplification/duplication, traceability; severity classification).

## Required Input

* `impl-plan.md`
* `requirements.md`
* `architecture.md`
* The actual source diff / changed files from the Implementation phase

## Expected Output

`docs/code-review.md`, with classified findings (blocking vs. non-blocking) and an explicit overall verdict ("Ready for Gate G4" only if zero blocking findings).

## Human Approval / Gate

Gate G4: Verification cannot start until `docs/code-review.md` shows zero unresolved blocking findings, explicitly accepted by the human.

## Scope Boundary

Do this phase only, read-only against the code. Do not edit or "fix" application code yourself, and do not begin verification or PR work.

## Stop Condition

STOP once `docs/code-review.md` is produced and reported to the human. Do not proceed to Verification without explicit human acceptance of a zero-blocking-finding review.
