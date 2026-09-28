---
name: design
description: Review-checklist methodology for critically evaluating architecture.md against requirements.md and producing design-review.md. Used by Agents/design.agent.md.
---

# Design Review Skill

Adapted from the "review checklist" half of the project's existing `architecture-analysis` methodology (`.claude/skills/architecture-analysis/SKILL.md`); the design-production half now lives in `Skills/architecture/SKILL.md`. Paths updated to the root-level artifact layout.

## Purpose

Provide a consistent methodology for critically reviewing an architecture design against approved requirements — not a rubber-stamp pass.

## Inputs / Prerequisites

* `requirements.md`
* `architecture.md`

## Method / Workflow

Independently re-derive expected requirement coverage rather than accepting `architecture.md`'s own coverage claims, then walk this checklist:

1. Does every requirement have a covering component? Does every component trace to a requirement?
2. Are decisions justified by requirements/constraints rather than convenience or familiarity?
3. Are trade-offs honestly stated, including downsides?
4. Are NFRs concretely addressed, not just mentioned?
5. Is anything in the design a hidden, unapproved product decision?
6. Is the design implementable as described, or does it hand-wave a hard part?

## Validation Checks

* Every finding is classified as **blocking** (must be resolved before Gate G2) or **non-blocking** (recommendation).
* The overall verdict is explicit: "Ready for Gate G2" only if there are zero blocking findings.
* No finding was softened to avoid conflict with the architecture agent's decisions.

## Expected Evidence / Output

`design-review.md` at the repository root, with the classified findings list and the explicit overall verdict.

## Failure / Stop Conditions

* `requirements.md` or `architecture.md` is missing — stop and report.
* A blocking finding exists — do not mark the review as passed; route it back to the architecture agent (or the human, if a product decision is required).

## Traceability Expectations

Each finding should cite the specific requirement/component it concerns, so a blocking finding can be routed back to a concrete, actionable spot in `architecture.md`.

## Security Considerations

Specifically check whether stated security-relevant NFRs are concretely addressed (not just asserted), and flag any design element that would weaken a security boundary described in `requirements.md`.
