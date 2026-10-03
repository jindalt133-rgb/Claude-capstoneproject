---
name: orchestrator
description: Single entry point to run the full Agentic SDLC — or resume an interrupted run — by coordinating the eight existing phase Prompts/Agents/Skills in canonical order and stopping at every required HITL gate.
---

# Orchestrator Prompt

## Invoke Agent

Read and follow `Agents/orchestrator.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, Phase State Model, Agent Routing Rules, Artifact Preconditions, Human Approval/Gate Behavior, and Failure/Retry Behavior govern this phase.

## Load Skill

Load and apply `Skills/orchestrator/SKILL.md` for the orchestration methodology (phase ordering, state determination, artifact prerequisites, agent routing, HITL gate enforcement, changes-requested routing, downstream re-validation, resume behavior, PR hand-off).

## Load Instructions

Load `Instructions/instructions.md` and `CLAUDE.md` — every cross-cutting rule, Approval Gate (G1–G5), and the canonical Phase → Prompt → Agent → Skill → Artifact mapping apply to this orchestration run exactly as they apply to any single phase invoked directly.

## Trigger

This Prompt is the canonical full-pipeline entry point. A user instruction such as "Run the Agentic SDLC using the User Story from Confluence" (or Jira, or a supplied Word document) invokes it.

## Required Input

* The selected User Story source for a fresh run — Confluence, Jira, or a supplied Word document. This Prompt passes the selected source straight through to `Prompts/requirements.prompt.md`, which remains solely responsible for resolving it (via the Atlassian MCP for Confluence/Jira, or the supported file-reading mechanism for Word). This Prompt does not resolve the source itself and does not recreate `user_story.md`.
* For a resumed run: no new input is required beyond the human's reply to the last gate/question this orchestration run raised.
* Actual repository state (inspected per the Orchestrator Skill's State Determination method) rather than any unverified claim from earlier in the conversation.

## Orchestration Steps

Executing this Prompt means, in order:

1. Load `Instructions/instructions.md`, `Agents/orchestrator.agent.md`, and `Skills/orchestrator/SKILL.md`.
2. Determine actual workflow state: which SDLC artifacts exist, what they contain, and which of their gates have been explicitly approved by the human in this conversation — never inferred from artifact existence alone.
3. Identify the next eligible phase (or the next unmet gate to stop at) per the Orchestrator Skill's Phase Ordering and State Determination method.
4. If a fresh Requirements run is needed, pass the selected User Story source through to `Prompts/requirements.prompt.md` unchanged; otherwise route to the next eligible phase's own canonical Prompt (`Prompts/architecture.prompt.md`, `Prompts/design.prompt.md`, `Prompts/planning.prompt.md`, `Prompts/implementation.prompt.md`, `Prompts/review.prompt.md`, `Prompts/verify.prompt.md`, or `Prompts/pr.prompt.md`).
5. Let that phase's own Prompt/Agent/Skill perform the actual work — do not perform or duplicate any phase-specific analysis, design, implementation, review, verification, or PR logic inside this Prompt.
6. After the phase produces its artifact/evidence, confirm only its mechanical existence — not its substantive correctness, which remains that phase's and the human's judgment.
7. Stop at the phase's Human Approval Gate (or the Mandatory Implementation Approval Gate before Implementation, or the PR Approval Gate before the PR Prompt) and report using the `ORCHESTRATION PAUSED` shape defined in `Agents/orchestrator.agent.md`. Never silently approve a gate.
8. Resume only on the human's explicit approval (e.g., "Approved. Continue."). On changes-requested feedback instead, route it to the responsible phase per the Orchestrator Skill's Agent Routing table, and recompute which downstream phases now require re-validation rather than assuming they remain valid.
9. Repeat steps 2–8 through Verification.
10. Stop for explicit PR approval before invoking `Prompts/pr.prompt.md`.
11. On explicit PR approval, hand off fully to `Prompts/pr.prompt.md` → `Agents/pr.agent.md` → `Skills/pr/SKILL.md` and report its outcome (the real, verified PR URL, or its explicit stop) unmodified.
12. Never merge a Pull Request, under any circumstance, at any point in this flow.

## Expected Output

A sequence of phase hand-offs to the correct existing canonical Prompt/Agent/Skill for each eligible phase, each followed by either an `ORCHESTRATION PAUSED` gate report or a changes-requested routing decision — ending in either a real, existence-verified Pull Request (as reported by the PR Agent) or an explicit stop naming the exact unmet gate/precondition.

## Human Approval / Gate

Every Approval Gate already defined in `CLAUDE.md` (G1–G5) applies unchanged. This Prompt adds no new gate and removes none. Implementation cannot begin without Gate G3 explicitly passed; PR creation cannot begin without Gate G5 explicitly passed.

## Scope Boundary

This Prompt coordinates; it does not do. It must never perform requirements analysis, architecture design, design review, implementation planning, application implementation, code review, verification, or PR preparation/creation itself, and it must never duplicate the PR Agent's pre-PR validation, git/GitHub actions, or PR content generation. It only decides which existing phase to invoke next and reports the required gate stop.

## Stop Condition

STOP at every Human Approval Gate (including the Mandatory Implementation Approval Gate and the PR Approval Gate) and report per `Agents/orchestrator.agent.md`'s Human Approval / Gate Behavior. Resume only after explicit human approval of that specific gate. Do not proceed past any gate on silence, and do not continue past the point where `Prompts/pr.prompt.md` hands back its outcome — merging remains a separate, human-only action outside this Prompt's scope entirely.
