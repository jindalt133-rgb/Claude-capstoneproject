---
name: design
description: Entry prompt for the Design Review phase of the Agentic SDLC.
---

# Design Review Prompt

## Invoke Agent

Read and follow `Agents/design.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/design/SKILL.md` for the review-checklist methodology (requirement/component traceability both directions, decision justification, honest trade-offs, concrete NFR handling, hidden unapproved decisions, implementability).

## Required Input

* `architecture.md`
* `requirements.md`

## Expected Output

`design-review.md` at the repository root, with classified findings (blocking vs. non-blocking) and an explicit overall verdict.

## Human Approval / Gate

Gate G2 (shared with Architecture): Implementation Planning cannot start until this review shows "Ready for Gate G2" with zero unresolved blocking findings, explicitly accepted by the human.

## Scope Boundary

Do this phase only. Critically review the existing `architecture.md` — do not rewrite the architecture yourself, and do not begin planning, implementation, review, verification, or PR work.

## Stop Condition

STOP once `design-review.md` is produced and reported to the human. Do not proceed to Implementation Planning without explicit human acceptance of a zero-blocking-finding review.
