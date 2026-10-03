---
name: implementation
description: Entry prompt for the Implementation phase of the Agentic SDLC.
---

# Implementation Prompt

## Invoke Agent

Read and follow `Agents/implementation.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/implementation/SKILL.md` for the task-execution and testing methodology (implement in dependency order, write accompanying tests, apply quality rules, handle secrets safely, escalate plan problems).

## Required Input

* `impl-plan.md` — must exist and be Gate-G3-approved by the human.
* The specific task(s) being implemented in this pass.

## Expected Output

Application source and test changes for the assigned task(s), plus a report of: task(s) completed, files changed, tests added, how they were run locally and the result, and any open questions or scope issues discovered.

## Human Approval / Gate

No new gate is opened by this phase alone; its output feeds Gate G4 once the Review phase evaluates it. Any blocking open question or plan discrepancy must be raised to the human before continuing to the next task.

## Scope Boundary

Do this phase only, and only the task(s) assigned by `impl-plan.md`. Do not review your own work as the Review Agent would, and do not begin verification or PR work.

## Stop Condition

STOP once the assigned task(s) are implemented (or reported as blocked) and reported to the human. Do not proceed to Code Review without a separate invocation of that phase.
