---
name: orchestrator
description: Reusable methodology for coordinating the eight existing Agentic SDLC phases from a single entry point — phase ordering, state determination from actual repository evidence, agent routing, HITL gate enforcement, changes-requested routing, downstream re-validation, resume behavior, and PR hand-off. Used by Agents/orchestrator.agent.md. Does not contain phase-specific methodology already owned by the other Skills.
---

# Orchestrator Skill

## Purpose

Provide a single, consistent methodology for running the full Agentic SDLC — or resuming an interrupted run — by sequencing the eight existing phases (requirements, architecture, design, planning, implementation, review, verify, pr) in the order and with the gates `CLAUDE.md` already defines, without re-implementing any phase's own analysis/design/implementation/review/verification/PR methodology.

This Skill is orchestration-only. It never substitutes for `Skills/requirements/SKILL.md`, `Skills/architecture/SKILL.md`, `Skills/design/SKILL.md`, `Skills/planning/SKILL.md`, `Skills/implementation/SKILL.md`, `Skills/review/SKILL.md`, `Skills/verify/SKILL.md`, or `Skills/pr/SKILL.md` — it only decides *when* to invoke each of them.

## Inputs / Prerequisites

* `CLAUDE.md` — the canonical Phase → Prompt → Agent → Skill → Artifact mapping and the Approval Gates (G1–G5) table.
* `Instructions/instructions.md` — cross-cutting rules (traceability, no silent requirement invention, test-evidence rules, phase-boundary rules, review-history preservation, stop-on-blocking-findings) that apply to orchestration exactly as they apply to any single phase.
* Actual repository state: which artifacts exist (`requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, application source/tests, `docs/code-review.md`, `docs/verification-report.md`, an existing GitHub PR) and their content/verdicts.
* The explicit human approval/changes-requested history recorded in the conversation.
* The selected User Story source for a fresh run (Jira, Confluence, or a supplied Word document) — resolved by `Prompts/requirements.prompt.md`, not by this Skill.

## Method / Workflow

### 1. Phase Ordering

Enforce this canonical order, matching `CLAUDE.md`'s Phase → Prompt → Agent → Skill → Artifact table exactly:

```
Selected User Story Source
    → Requirements Prompt/Agent/Skill → requirements.md → HITL GATE (G1)
    → Architecture Prompt/Agent/Skill → architecture.md → HITL GATE
    → Design Prompt/Agent/Skill → design-review.md → HITL GATE (G2)
    → Planning Prompt/Agent/Skill → impl-plan.md → MANDATORY IMPLEMENTATION APPROVAL GATE (G3)
    → Implementation Prompt/Agent/Skill → application source/tests
    → Review Prompt/Agent/Skill → docs/code-review.md
    → Verify Prompt/Agent/Skill → docs/verification-report.md → PR APPROVAL GATE (G5, with G4 resolved beforehand)
    → PR Prompt/Agent/Skill → project pre-PR validation → automatic GitHub PR workflow
```

Never reorder these, never run two phases concurrently, and never let a later phase begin before its stated gate is explicitly passed.

### 2. State Determination

At the start of every orchestration turn (fresh start or resume), determine state from evidence, not memory:

1. Check which of `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, application source/tests, `docs/code-review.md`, `docs/verification-report.md`, and an existing PR actually exist and what they say.
2. Separately check, from the conversation itself, which of those artifacts' gates have been *explicitly* approved by the human — never infer approval from existence alone.
3. The next eligible phase is the earliest phase in Phase Ordering whose own artifact is missing, OR whose artifact exists but whose gate has not been explicitly passed (in which case the next step is to stop at that gate, not to advance past it).

Examples:
* `requirements.md` exists and is approved; `architecture.md` missing → next eligible phase = Architecture.
* `architecture.md` exists but its design-review approval has not been established → stop at the Architecture/Design-Review gate; do not advance to Planning.
* `docs/verification-report.md` shows a passing result but PR approval has not been given → stop before invoking the PR Prompt/Agent.

Never skip a required gate merely because a downstream artifact happens to exist (e.g., never treat `impl-plan.md` as approved just because application code already exists).

### 3. Artifact Prerequisites

Before invoking any phase's canonical Prompt, confirm the specific upstream artifact(s)/gate(s) `CLAUDE.md` requires for that phase are met (see its Approval Gates table). If not met, stop and report the unmet gate instead of invoking the phase.

### 4. Agent Routing

Route exclusively through each phase's own canonical Prompt (which loads its own Agent and Skill):

| Need | Route to |
|---|---|
| Requirements work or changes | `Prompts/requirements.prompt.md` |
| Architecture work or changes | `Prompts/architecture.prompt.md` |
| Design Review work, or findings not implicating architecture | `Prompts/design.prompt.md` |
| Implementation Planning work or changes | `Prompts/planning.prompt.md` |
| Implementation work or defect fixes | `Prompts/implementation.prompt.md` |
| Code Review | `Prompts/review.prompt.md` |
| Verification | `Prompts/verify.prompt.md` |
| PR preparation/creation | `Prompts/pr.prompt.md` |

The Orchestrator Skill never performs the routed-to phase's work itself — it only selects and invokes the right Prompt.

### 5. HITL Gates and Approval Semantics

* On completing a phase that requires approval, stop and report: completed phase, artifact produced, validation result (mechanical existence/evidence only), next proposed phase, and that human approval is required.
* Resume only on an explicit affirmative reply (e.g., "Approved. Continue."). Silence, an unrelated message, or ambiguity is never approval.
* Gates G1–G5 are exactly `CLAUDE.md`'s existing gates; this Skill adds no new gate and removes none. Implementation cannot begin without Gate G3; PR creation cannot begin without Gate G5.

### 6. Changes-Requested Routing

If the human responds with changes requested instead of approval:

1. Identify which phase is actually responsible for the requested change (see Agent Routing above) — a Design Review finding that implicates architecture routes to Architecture, not to Design; an implementation review defect routes to Implementation, not to Review.
2. Re-invoke only that phase's canonical Prompt. The Orchestrator Skill itself must never author the fix.
3. Do not resume forward progress until the responsible phase has produced a revised artifact and the human has approved it.

### 7. Downstream Invalidation / Re-validation

After any upstream artifact changes (whether from a changes-requested cycle or a later Change Control update per `CLAUDE.md`):

* Never assume a downstream artifact is still valid merely because it still exists on disk.
* Recompute which downstream phases depend on the changed artifact and re-run their canonical Prompts: an architecture change invalidates `design-review.md` and requires re-running Design Review; an implementation change invalidates `docs/code-review.md` and `docs/verification-report.md` and requires re-running Review and Verification.
* Preserve prior review/verification artifacts rather than overwriting them (per `Instructions/instructions.md` Rule 9) — a re-run adds a new result alongside/below the prior one.

### 8. Resume Behavior

* Resuming is always driven by State Determination (Method step 2) against actual repository state, never by trusting a prior conversation's unverified claim that a phase "completed."
* A resumed run picks up at the next eligible phase or the next unmet gate, exactly as a fresh run would compute it.

### 9. PR Hand-off Rules

* Only after the PR Approval Gate (G5) is explicitly satisfied does this Skill invoke `Prompts/pr.prompt.md`.
* All pre-PR validation, git/GitHub state checks, secret/security checks, test execution, PR title/description generation, branch push, PR creation, and post-creation verification remain exclusively `Agents/pr.agent.md`'s and `Skills/pr/SKILL.md`'s responsibility — this Skill does not duplicate any of it.
* This Skill reports the PR Agent's outcome (real, verified PR URL, or its explicit stop) back to the human unmodified.
* This Skill never triggers or performs a merge, under any circumstance.

## Validation Checks

* The next-eligible-phase decision was computed from actual artifact existence/content and explicit recorded human approvals, not from assumption.
* Every invocation went through the phase's own canonical Prompt/Agent/Skill — no phase-specific business logic was performed by the Orchestrator itself.
* Every required gate (G1–G5) was stopped at and reported before being crossed; none were inferred from silence or from artifact existence alone.
* Changes-requested feedback was routed to the correct responsible phase, and all affected downstream phases were marked for re-validation rather than assumed valid.
* `user_story.md` was not recreated at any point in the flow.
* PR creation, if invoked, went only through `Prompts/pr.prompt.md` → `Agents/pr.agent.md`.

## Expected Evidence / Output

A reported sequence of phase hand-offs with their artifacts, each followed by either an `ORCHESTRATION PAUSED` gate report (awaiting explicit approval) or a routing decision (on changes requested) — ending in either a real, existence-verified Pull Request (reported by the PR Agent) or an explicit stop naming the exact unmet gate/precondition.

## Failure / Stop Conditions

* A phase's canonical Prompt itself stops with unresolved blocking questions/findings — the Orchestrator Skill reports that stop and does not proceed or soften it.
* A mechanical Hook denies an action (e.g., `phase_boundary_check.py` blocking an application-source edit before Gate G3, or `pr_gate_hook.py` blocking a PR-creation command before `pre_pr_validation.py` passes) — report the exact denial reason; do not retry by bypassing the hook.
* An unmet artifact precondition or unresolved gate — stop and name exactly which gate is unmet rather than guessing or proceeding.
* Ambiguity about whether a human reply constitutes approval — treat as not-approved and ask for an explicit confirmation.

## Traceability Expectations

Every phase hand-off this Skill makes must trace back to `CLAUDE.md`'s Phase → Prompt → Agent → Skill → Artifact mapping and Approval Gates table — never to an invented phase order or an invented gate. Routing decisions for changes-requested feedback must trace back to the specific finding/comment that triggered them.

## Security Considerations

* Never place a PAT/token or other credential in any orchestration state, report, or routing decision.
* Never bypass, soften, or reinterpret a Hook's deterministic denial — Hooks remain mechanical guardrails that this Skill obeys, not something it calls into to perform SDLC reasoning.
* Never duplicate the PR Agent's authentication or GitHub-mutating actions inside orchestration logic.
