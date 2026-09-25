---
name: architecture-analysis
description: Methodology for producing and reviewing architecture.md from an approved requirements.md, and for structuring ADRs. Use during the Architecture and Design Review phases.
---

# Architecture Analysis Skill

## Purpose

Provide a consistent methodology for turning approved requirements into an architecture design, and for critically reviewing that design, without introducing requirements that were never approved.

Used by both the `architect` agent (producing) and the `design-reviewer` agent (reviewing), so both sides apply the same standard.

## Preconditions

* `docs/requirements.md` exists and has been approved by the human (Gate G1).
* Every architectural decision must be traceable to a specific requirement ID (FR-xxx / NFR-xxx). If a decision has no traceable requirement, flag it rather than inventing a justification.

## Analysis Framework

### 1. Requirement Coverage

List every FR/NFR from `requirements.md` and identify which architectural component addresses it. Flag any requirement with no covering component, and any component with no covering requirement (possible scope creep).

### 2. Component Breakdown

Identify the major components/modules and the responsibility of each. Keep responsibilities single-purpose where the requirements allow it.

### 3. Data and Control Flow

Describe how information moves through the system for the primary flows implied by the requirements. Do not invent flows the requirements don't imply.

### 4. Key Decisions and Trade-offs

For each decision with more than one reasonable option (e.g., storage approach, trigger mechanism, parsing strategy):

* State the options considered.
* State the decision and why, tied to specific requirements/constraints.
* State the trade-off accepted.

Record decisions with significant, hard-to-reverse trade-offs as a separate ADR in `docs/adr/`.

### 5. Non-Functional Handling

Explicitly state how each NFR (security, reliability, performance, maintainability, etc.) named in `requirements.md` is addressed. Do not invent NFR targets absent from requirements.

### 6. Constraints and Dependencies Carried Forward

Re-state constraints/dependencies from `requirements.md` that shape the design, plus any new technical dependency introduced by the design itself (e.g., a specific library or runtime).

### 7. Open Questions

List anything that could not be decided without a product decision beyond what requirements.md authorizes. These must go to the human, not be resolved by guessing.

## Review Checklist (for design-reviewer)

Critically evaluate — do not rubber-stamp:

* Does every requirement have a covering component? Does every component trace to a requirement?
* Are decisions justified by requirements/constraints rather than convenience or familiarity?
* Are trade-offs honestly stated, including downsides?
* Are NFRs concretely addressed, not just mentioned?
* Is anything in the design a hidden, unapproved product decision?
* Is the design implementable as described, or does it hand-wave a hard part?

Findings must be classified as **blocking** (must be resolved before Gate G2) or **non-blocking** (recommendation). Do not mark the review as passed while blocking findings remain open.
