---
name: planning
description: Entry prompt for the Implementation Planning phase of the Agentic SDLC.
---

# Implementation Planning Prompt

## Invoke Agent

Read and follow `Agents/planning.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/planning/SKILL.md` for the task-breakdown methodology (decomposition with traceability and dependencies, dependency ordering, flagging under-specified architecture areas).

## Required Input

* `architecture.md`
* `design-review.md` — must show "Ready for Gate G2" with zero blocking findings.

## Expected Output

`impl-plan.md` at the repository root: an ordered, dependency-aware task list, each task showing its traceability to architecture/requirements and its expected test coverage.

## Human Approval / Gate

Gate G3: Implementation cannot start until `impl-plan.md` is explicitly reviewed and accepted by the human.

## Scope Boundary

Do this phase only. Do not write or edit application source code or tests in this pass, and do not begin implementation, review, verification, or PR work.

## Stop Condition

STOP once `impl-plan.md` is produced and reported to the human. Do not proceed to Implementation without explicit human approval of `impl-plan.md`.
