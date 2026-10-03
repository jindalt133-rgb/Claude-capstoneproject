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
* `orchestrator-state.json` at the repository root, if present — the durable record of which gates have an explicitly recorded human approval. Read before trusting any approval claim; see Method §10 below.
* Actual repository state: which artifacts exist (`requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, application source/tests, `docs/code-review.md`, `docs/verification-report.md`, an existing GitHub PR) and their content/verdicts.
* The explicit human approval/changes-requested history recorded in the conversation — useful for the *current* turn's own gate, but never a substitute for what `orchestrator-state.json` durably records across sessions.
* The selected User Story source for a fresh run (Jira, Confluence, or a supplied Word document) — resolved by `Prompts/requirements.prompt.md`, not by this Skill.

## Method / Workflow

### 1. Phase Ordering

Enforce this canonical order, matching `CLAUDE.md`'s Phase → Prompt → Agent → Skill → Artifact table exactly. **There are exactly five stops (G1, G2, G3, conditional-G4, G5) — Architecture's own completion is never a sixth, separate stop:**

```
Selected User Story Source
    → Requirements Prompt/Agent/Skill → requirements.md → HITL GATE (G1)
    → Architecture Prompt/Agent/Skill → architecture.md
        (runs automatically immediately after G1 — Architecture has NO gate of its own)
    → Design Prompt/Agent/Skill → design-review.md → HITL GATE (G2)
        (the ONLY stop between Requirements and Planning; judges architecture.md
        and design-review.md together — never two separate stops here)
    → Planning Prompt/Agent/Skill → impl-plan.md → MANDATORY IMPLEMENTATION APPROVAL GATE (G3)
    → Implementation Prompt/Agent/Skill → application source/tests
        (runs automatically immediately after G3)
    → Review Prompt/Agent/Skill → docs/code-review.md → GATE G4 (conditional):
        - 0 BLOCKER/HIGH findings  → proceed automatically to Verification
        - any BLOCKER/HIGH finding → STOP; obtain explicit human approval
          BEFORE remediation; after approved remediation, re-run Review and
          re-evaluate G4 against the new result before proceeding
    → Verify Prompt/Agent/Skill → docs/verification-report.md → PR APPROVAL GATE (G5)
    → PR Prompt/Agent/Skill → project pre-PR validation → automatic GitHub PR workflow
```

Never reorder these, never run two phases concurrently, and never let a later phase begin before its stated gate is explicitly passed. Do not read the absence of an explicit gate label after a phase (Architecture, Implementation) as an oversight — it is intentional: that phase has no human stop of its own.

### 2. State Determination

At the start of every orchestration turn (fresh start or resume), determine state from evidence, not memory:

1. Check which of `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, application source/tests, `docs/code-review.md`, `docs/verification-report.md`, and an existing PR actually exist and what they say.
2. Separately check, from the conversation itself, which of those artifacts' gates have been *explicitly* approved by the human — never infer approval from existence alone.
3. The next eligible phase is the earliest phase in Phase Ordering whose own artifact is missing, OR whose artifact exists but whose gate has not been explicitly passed (in which case the next step is to stop at that gate, not to advance past it).

Examples:
* `requirements.md` exists and is approved; `architecture.md` missing → next eligible phase = Architecture.
* `architecture.md` exists; `design-review.md` missing or not yet approved → next eligible phase = Design Review (Architecture itself is never re-stopped at — it already ran); do not advance to Planning until G2 is recorded.
* `docs/code-review.md` exists with 1 BLOCKER finding and `orchestrator-state.json` shows no recorded G4 approval → stop at Gate G4 for remediation approval; do not route to Implementation for the fix without it.
* `docs/verification-report.md` shows a passing result but PR approval has not been given → stop before invoking the PR Prompt/Agent.

Never skip a required gate merely because a downstream artifact happens to exist (e.g., never treat `impl-plan.md` as approved just because application code already exists), and never treat `orchestrator-state.json`'s absence of a recorded approval as proof that approval never happened — absence of a durable record means the gate's status is `UNKNOWN_LEGACY_UNRECORDED`, not `APPROVED` and not `DENIED`.

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
* Immediately after receiving that explicit approval, record it in `orchestrator-state.json` (gate, `APPROVED`, timestamp, short evidence note) before invoking the next phase — the conversation reply is the trigger, but the durable record is what future turns and future sessions actually rely on.
* Gates G1–G5 are exactly `CLAUDE.md`'s existing gates; this Skill adds no new gate and removes none. Implementation cannot begin without Gate G3; PR creation cannot begin without Gate G5. Architecture has no gate of its own (folded into G2); Gate G4 is conditional (see §1 and §9b below) rather than always being a hard stop.

### 6. Changes-Requested Routing

If the human responds with changes requested instead of approval:

1. Identify which phase is actually responsible for the requested change (see Agent Routing above) — a Design Review finding that implicates architecture routes to Architecture, not to Design; an implementation review defect routes to Implementation, not to Review.
2. Re-invoke only that phase's canonical Prompt. The Orchestrator Skill itself must never author the fix.
3. Do not resume forward progress until the responsible phase has produced a revised artifact and the human has approved it.

### 6a. Gate G4 — Code Review Remediation Approval (Conditional Gate)

Gate G4 is **not** a uniform hard stop the way G1/G2/G3/G5 are — it is conditional on what Code Review actually finds:

1. After `Prompts/review.prompt.md` produces `docs/code-review.md`, inspect its findings summary.
2. **Zero BLOCKER/HIGH findings:** Gate G4 is satisfied by that result alone. Proceed automatically to `Prompts/verify.prompt.md` — no additional stop-and-wait is required beyond what Code Review itself already reports.
3. **Any BLOCKER/HIGH finding:** STOP. Report the finding(s) and that explicit human approval is required *before remediation begins* (not merely before Verification) — remediating a defect is itself a change this Skill must not authorize on its own. Use the same `ORCHESTRATION PAUSED` shape as any other gate.
4. On explicit approval, route to `Prompts/implementation.prompt.md` for remediation (per Agent Routing), then re-run `Prompts/review.prompt.md` and re-evaluate from step 1 against the new result — a single approval to remediate does not carry forward as approval of the remediation's outcome.
5. Record the eventual G4 outcome in `orchestrator-state.json` only once a result with zero remaining BLOCKER/HIGH findings is reached (whether immediately or after one or more remediation rounds).

### 7. Downstream Invalidation / Re-validation

After any upstream artifact changes (whether from a changes-requested cycle or a later Change Control update per `CLAUDE.md`):

* Never assume a downstream artifact is still valid merely because it still exists on disk.
* Recompute which downstream phases depend on the changed artifact and re-run their canonical Prompts: an architecture change invalidates `design-review.md` and requires re-running Design Review; an implementation change invalidates `docs/code-review.md` and `docs/verification-report.md` and requires re-running Review and Verification.
* Preserve prior review/verification artifacts rather than overwriting them (per `Instructions/instructions.md` Rule 9) — a re-run adds a new result alongside/below the prior one.

### 8. Resume Behavior

* Resuming is always driven by State Determination (Method step 2) against actual repository state, never by trusting a prior conversation's unverified claim that a phase "completed."
* Read `orchestrator-state.json` first: it is the durable, cross-session record of which gates actually have an explicitly recorded human approval. Conversation memory is never required to resume a previously-recorded gate — that is precisely what the state file is for (see §10).
* A resumed run picks up at the next eligible phase or the next unmet gate, exactly as a fresh run would compute it — combining `orchestrator-state.json`'s recorded gate statuses with the artifacts' own existence/content.
* If `orchestrator-state.json` is missing entirely (e.g., a repository predating this mechanism), treat every gate as `UNKNOWN_LEGACY_UNRECORDED` and surface that explicitly rather than assuming either approval or denial.

### 9. PR Hand-off Rules

* Only after the PR Approval Gate (G5) is explicitly satisfied does this Skill invoke `Prompts/pr.prompt.md`.
* All pre-PR validation, git/GitHub state checks, secret/security checks, test execution, PR title/description generation, branch push, PR creation, and post-creation verification remain exclusively `Agents/pr.agent.md`'s and `Skills/pr/SKILL.md`'s responsibility — this Skill does not duplicate any of it.
* This Skill reports the PR Agent's outcome (real, verified PR URL, or its explicit stop) back to the human unmodified.
* This Skill never triggers or performs a merge, under any circumstance.

### 10. Durable Approval-State Persistence

A minimal, repository-owned JSON file, `orchestrator-state.json` at the repository root, is the durable record of which gates have an explicitly recorded human approval. It exists so that resuming after a Claude/CodeMie session restart never has to rely on conversation memory for a gate that was already approved in an earlier session.

**Schema (minimal, no secrets, no conversation transcripts):**

* `schema_version` — integer.
* `source` — `{type, identifier, space}` for the run's User Story source (e.g. `{"type": "Confluence", "identifier": "page:14745601", "space": "Agentic SDLC"}`); omit or leave null fields for a source type where a field doesn't apply. Never store credentials, tokens, or page content here — an identifier only.
* `gates` — an array of one entry per gate (`G1`–`G5`), each with: `gate`, `phase`, `artifact`, `status`, `approval_recorded` (boolean), `approved_at` (ISO date or `null`), `evidence` (a short human-readable note).
* `resume` — derived summary: `last_completed_phase`, `last_explicitly_approved_gate`, `next_eligible_phase`, `human_approval_currently_required`.
* `meta` — `created_at` and a free-text `note`.

**Allowed `status` values:** `APPROVED`, `UNKNOWN_LEGACY_UNRECORDED`, `PENDING` (produced, awaiting a decision), `NOT_STARTED`.

**The write rule, strictly enforced:**

* A gate may be written as `APPROVED` **only** in the same turn an explicit human approval for that specific gate is given. `approval_recorded` must be `true` and `approved_at` must be set whenever `status` is `APPROVED` — the two are never inconsistent.
* Artifact existence, downstream files, commits, or an existing Pull Request must **never** by themselves cause a gate to be written as `APPROVED`. If the only evidence available is of that kind, the status is `UNKNOWN_LEGACY_UNRECORDED`, with the circumstantial evidence recorded in the `evidence` field as context, not as proof.
* A gate already recorded as `UNKNOWN_LEGACY_UNRECORDED` is never silently upgraded to `APPROVED` — upgrading it requires the same explicit, contemporaneous human approval as any other gate.
* Before orchestrating a **new** run, re-initialize `gates`/`resume` for that run rather than reusing a prior run's recorded approvals — a durable record belongs to the run whose artifacts it describes.

**Resume read rule:** on every orchestration turn, read `orchestrator-state.json` before anything else; combine its recorded gate statuses with current artifact existence/content (Method §2) to compute the next eligible phase. Never treat a missing or `UNKNOWN_LEGACY_UNRECORDED` entry as approval, and never treat it as denial either — it simply means no durable record exists, and (for a gate still relevant to forward progress) a fresh explicit human approval must be obtained before proceeding.

## Validation Checks

* The next-eligible-phase decision was computed from `orchestrator-state.json` plus actual artifact existence/content, not from assumption or conversation memory alone.
* Every invocation went through the phase's own canonical Prompt/Agent/Skill — no phase-specific business logic was performed by the Orchestrator itself.
* Every required gate (G1, G2, G3, conditional-G4, G5) was stopped at and reported before being crossed; none were inferred from silence or from artifact existence alone. Architecture's completion was never treated as a sixth gate.
* Every `APPROVED` entry in `orchestrator-state.json` corresponds to an explicit, contemporaneous human approval; no entry was upgraded from `UNKNOWN_LEGACY_UNRECORDED` without one.
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
* `orchestrator-state.json` is missing, unreadable, or fails its deterministic validation (`Hooks/orchestrator_state_check.py`, if run) — treat every gate as `UNKNOWN_LEGACY_UNRECORDED` and surface this explicitly rather than guessing at prior approvals.

## Traceability Expectations

Every phase hand-off this Skill makes must trace back to `CLAUDE.md`'s Phase → Prompt → Agent → Skill → Artifact mapping and Approval Gates table — never to an invented phase order or an invented gate. Routing decisions for changes-requested feedback must trace back to the specific finding/comment that triggered them.

## Security Considerations

* Never place a PAT/token or other credential in any orchestration state, report, or routing decision — including `orchestrator-state.json`, which must contain only workflow facts (gate, status, artifact path, non-sensitive source identifier, timestamps, short evidence notes), never credentials, tokens, user identity data, or conversation transcripts.
* Never bypass, soften, or reinterpret a Hook's deterministic denial — Hooks remain mechanical guardrails that this Skill obeys, not something it calls into to perform SDLC reasoning.
* Never duplicate the PR Agent's authentication or GitHub-mutating actions inside orchestration logic.
