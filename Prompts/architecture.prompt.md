---
name: architecture
description: Entry prompt for the Architecture phase of the Agentic SDLC.
---

# Architecture Prompt

## Invoke Agent

Read and follow `Agents/architecture.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/architecture/SKILL.md` for the architecture methodology (requirement coverage, component breakdown, data/control flow, key decisions and trade-offs with ADRs, non-functional handling, constraints/dependencies, open questions).

## Required Input

* `requirements.md` — must exist and be Gate-G1-approved by the human.

## Expected Output

`architecture.md` at the repository root, plus any new ADR file(s) under `docs/adr/` for significant, hard-to-reverse decisions.

## Human Approval / Gate

Gate G2 (shared with Design Review): Implementation Planning cannot start until `architecture.md` has passed `design-review.md` with no unresolved blocking findings, explicitly accepted by the human.

## Scope Boundary

Do this phase only. Do not perform the Design Review of your own architecture in this pass, and do not begin planning, implementation, review, verification, or PR work.

## Stop Condition

STOP once `architecture.md` (and any ADRs) are produced and reported to the human. Do not proceed to Design Review without a separate invocation of that phase.
