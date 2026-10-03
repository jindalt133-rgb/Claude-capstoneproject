---
name: architecture
description: Methodology for producing architecture.md (and ADRs) from an approved requirements.md. Used by Agents/architecture.agent.md.
---

# Architecture Skill

Adapted from the "producing" half of the project's existing `architecture-analysis` methodology (`.claude/skills/architecture-analysis/SKILL.md`); the review-checklist half now lives in `Skills/design/SKILL.md`. Paths updated to the root-level artifact layout.

## Purpose

Provide a consistent methodology for turning approved requirements into an architecture design, without introducing requirements that were never approved.

## Inputs / Prerequisites

* `requirements.md` — must exist and be Gate-G1-approved by the human.
* Every architectural decision must be traceable to a specific requirement ID (`FR-xxx`/`NFR-xxx`). If a decision has no traceable requirement, flag it rather than inventing a justification.

## Method / Workflow

1. **Requirement Coverage** — list every FR/NFR from `requirements.md` and identify which architectural component addresses it. Flag any requirement with no covering component, and any component with no covering requirement (possible scope creep).
2. **Component Breakdown** — identify the major components/modules and the responsibility of each. Keep responsibilities single-purpose where the requirements allow it.
3. **Data and Control Flow** — describe how information moves through the system for the primary flows implied by the requirements. Do not invent flows the requirements don't imply.
4. **Key Decisions and Trade-offs** — for each decision with more than one reasonable option (e.g., storage approach, trigger mechanism, parsing strategy): state the options considered, state the decision and why (tied to specific requirements/constraints), and state the trade-off accepted. Record decisions with significant, hard-to-reverse trade-offs as a separate ADR under `docs/adr/`.
5. **Non-Functional Handling** — explicitly state how each NFR named in `requirements.md` is addressed. Do not invent NFR targets absent from requirements.
6. **Constraints and Dependencies Carried Forward** — re-state constraints/dependencies from `requirements.md` that shape the design, plus any new technical dependency introduced by the design itself.
7. **Open Questions** — list anything that could not be decided without a product decision beyond what `requirements.md` authorizes. These go to the human, not resolved by guessing.

## Validation Checks

* Every FR/NFR maps to a covering component, or is explicitly listed as an open question.
* Every component traces back to at least one requirement (no unexplained scope).
* Every significant, hard-to-reverse trade-off has a corresponding ADR under `docs/adr/`.
* No NFR target appears in the architecture that isn't grounded in `requirements.md`.

## Expected Evidence / Output

`architecture.md` at the repository root, plus any new ADR file(s) under `docs/adr/` for significant, hard-to-reverse decisions.

## Failure / Stop Conditions

* `requirements.md` does not exist or is not Gate-G1-approved — stop before starting this phase.
* A design decision requires an unauthorized product choice — list it under "Open Questions" instead of deciding it.

## Traceability Expectations

Requirement → Architecture component, in both directions: every requirement has a covering component, and every component cites the requirement(s) that justify it.

## Security Considerations

Address relevant NFRs concretely (e.g., input trust boundaries, path/output containment, secret handling) rather than mentioning security in the abstract; do not select a technology or approach that weakens a stated security NFR for convenience.
