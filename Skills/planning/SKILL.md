---
name: planning
description: Methodology for breaking an approved architecture.md (with a passed design-review.md) into an ordered, dependency-aware task breakdown in impl-plan.md. Used by Agents/planning.agent.md.
---

# Implementation Planning Skill

New methodology, authored for this phase — there is no direct equivalent among the existing `.claude/skills/*` methodologies. Consolidated here so both the agent and any future planning work apply the same standard.

## Purpose

Provide a consistent methodology for turning an approved architecture into an ordered, dependency-aware set of implementation tasks, without inventing functionality absent from `architecture.md` or `requirements.md`.

## Inputs / Prerequisites

* `architecture.md` — must exist.
* `design-review.md` — must show "Ready for Gate G2" with zero blocking findings.

## Method / Workflow

1. **Confirm prerequisites** — verify `architecture.md` exists and `design-review.md` shows zero unresolved blocking findings. If either condition fails, stop and report rather than planning around an unresolved blocking finding.
2. **Decompose into tasks** — break the architecture into discrete, individually completable tasks. For each task, record: what it covers, which architecture component(s) and requirement ID(s) (`FR-xxx`/`NFR-xxx`) it traces to, its dependencies on other tasks, and the tests expected to accompany it.
3. **Order by dependency** — sequence tasks by actual technical dependency (what must exist before what), not by convenience or familiarity.
4. **Flag under-specified areas** — where `architecture.md` is too vague to plan a concrete task, report the gap rather than inventing design detail to fill it.

## Validation Checks

* Every task cites at least one architecture component and, through it, at least one requirement.
* Task ordering respects every real dependency (no task depends on a task that comes later).
* No task exists for functionality absent from `architecture.md`/`requirements.md`.
* Expected test coverage is stated per task, not deferred to "implementation will figure it out."

## Expected Evidence / Output

`impl-plan.md` at the repository root: an ordered, dependency-aware task list, each task showing its traceability and expected test coverage.

## Failure / Stop Conditions

* `architecture.md` does not exist — stop before starting this phase.
* `design-review.md` shows any unresolved blocking finding — stop and report; do not plan around it.
* An architecture area is too vague to decompose into a concrete task — list it as a flagged gap, not a guessed task.

## Traceability Expectations

Requirement → Architecture component → Implementation task, so that Gate G4 review and Gate G5 verification can later walk the same chain back to a specific requirement.

## Security Considerations

Do not schedule a task that would require introducing a hardcoded secret, credential, or token to "make progress" — if the architecture implies credential handling, the task should reference the approved mechanism (e.g., environment variable, out-of-band secret store), never a literal value.
