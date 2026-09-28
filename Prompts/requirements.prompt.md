---
name: requirements
description: Entry prompt for the Requirements phase of the Agentic SDLC.
---

# Requirements Prompt

## Invoke Agent

Read and follow `Agents/requirements.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/requirements/SKILL.md` for the requirements-analysis methodology (business objective, scope, actors, FR/NFR extraction, constraints, dependencies, acceptance criteria, assumptions, ambiguities, missing information, conflicts, and the clarification process).

## Required Input

* `user_story.md`
* Direct human answers to any clarification questions raised while applying the skill.

## Expected Output

`requirements.md` at the repository root, containing every section the skill requires, with FR-xxx/NFR-xxx identifiers and assumptions/ambiguities visibly separated from confirmed requirements.

## Human Approval / Gate

Gate G1: `requirements.md` must be reviewed and explicitly accepted by the human before Architecture may begin. Do not proceed past this gate on silence.

## Scope Boundary

Do this phase only. Do not begin architecture, design, planning, implementation, review, verification, or PR work in this pass, even if the requirements seem obvious or the next step seems easy.

## Stop Condition

STOP once `requirements.md` is produced (or clarification questions are posed) and reported to the human. Do not proceed to Architecture without explicit human approval of `requirements.md`.
