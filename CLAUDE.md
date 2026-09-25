# Automated Documentation Sync — Agentic SDLC Instructions

## Project Objective

Build the Automated Documentation Sync application from scratch by following a structured Agentic Software Development Life Cycle.

Claude must assist throughout the lifecycle while keeping a human in the loop for clarification, approval, and important decisions.

## SDLC Stages

Follow these stages in order:

1. Requirements
2. Architecture
3. Design Review
4. Implementation Planning
5. Implementation
6. Code Review
7. Verification
8. Pull Request

Do not skip stages.

## Source-of-Truth Hierarchy

Use approved artifacts from earlier SDLC stages as the source of truth for later stages.

User Story
→ requirements.md
→ architecture.md
→ design-review.md
→ impl-plan.md
→ implementation
→ tests and verification
→ Pull Request

Do not silently introduce requirements that are absent from approved artifacts.

## Human-in-the-Loop Rules

Claude must request human input when:

* A requirement is materially ambiguous.
* Required information is missing.
* Multiple materially different product decisions are possible.
* A proposed change alters approved scope.
* A major SDLC artifact is ready for approval.

Do not fabricate answers to unresolved product questions.

## Approval Gates

Explicit human approval is required before crossing each of these boundaries. Do not proceed past a gate on the assumption that silence means approval — wait for an explicit confirmation.

| Gate | Required before | Approved by human means |
|---|---|---|
| G1 | Starting Architecture | `docs/requirements.md` reviewed and accepted |
| G2 | Starting Implementation Planning | `docs/architecture.md` has passed `docs/design-review.md` with no unresolved blocking findings |
| G3 | Starting Implementation | `docs/impl-plan.md` reviewed and accepted |
| G4 | Starting Verification | Implementation and `docs/code-review.md` blocking findings resolved |
| G5 | Creating a Pull Request | `docs/verification.md` shows a passing result and the human has explicitly authorized opening the PR |

Hooks may check for the *existence and mechanical state* of these gate artifacts (see Hook Rules below) but the decision to accept an artifact is always the human's, never inferred by Claude or a hook.

## Requirements Rules

Treat `docs/user-story.md` as the primary source during requirements analysis.

Distinguish clearly between:

* Explicit requirements
* Assumptions
* Ambiguities
* Missing information
* Constraints
* Dependencies

Do not convert assumptions into requirements without human confirmation.

## Architecture Rules

Architecture decisions must trace back to approved requirements.

Do not select technology merely because it is convenient if the requirements imply otherwise.

Record significant architectural decisions and trade-offs.

## Implementation Restrictions

Do not begin production implementation until:

* `requirements.md` exists and is approved (Gate G1 passed).
* `architecture.md` exists and has passed design review (Gate G2 passed).
* `impl-plan.md` exists and is approved (Gate G3 passed).

Additional restrictions, at all times:

* Do not implement features, endpoints, files, or behavior absent from `impl-plan.md`.
* Do not reorder implementation ahead of the dependency order defined in `impl-plan.md` without human approval.
* Do not silently expand scope to "while I'm here" fix unrelated issues — log them instead and raise them to the human.
* Do not create a Pull Request until Gate G5 is explicitly satisfied.
* Do not mark a task complete if its tests are failing or missing.

## Quality Rules

Implementation must prioritize:

* Correctness
* Security
* Error handling
* Testability
* Maintainability
* Clear naming
* Minimal duplication
* Safe dependency usage

## Security Rules

Never intentionally expose:

* Passwords
* API keys
* Access tokens
* Authentication credentials
* Other secrets

Never commit real secrets to the repository.

## Testing Rules

Tests must cover:

* Primary successful workflows
* Important edge cases
* Important failure scenarios
* Missing or invalid inputs where applicable

## Traceability

Where practical, maintain traceability between:

Requirement
→ Architecture component
→ Implementation task
→ Code
→ Test

## Change Control

If implementation reveals that an approved requirement or architecture decision must change:

1. Stop the affected work.
2. Explain the issue.
3. Update the appropriate upstream artifact after human approval.
4. Continue implementation only after the change is accepted.

## Agent Responsibilities

Specialized subagents exist for phases that benefit from an isolated context window, a distinct tool-access profile, or a fresh perspective free of the producing agent's own reasoning (bias avoidance). Each agent must stay within its assigned responsibility and must not perform another agent's job.

| Agent | Reads | Produces | Tools |
|---|---|---|---|
| `architect` | `docs/requirements.md` | `docs/architecture.md`, `docs/adr/*` | Read, Grep, Glob, Write, Edit |
| `design-reviewer` | `docs/architecture.md`, `docs/requirements.md` | `docs/design-review.md` | Read, Grep, Glob, Write, Edit |
| `implementation-planner` | `docs/architecture.md`, `docs/design-review.md` | `docs/impl-plan.md` | Read, Grep, Glob, Write, Edit |
| `developer` | `docs/impl-plan.md` | application source code, tests | Read, Grep, Glob, Write, Edit, Bash |
| `code-reviewer` | source diff, `docs/impl-plan.md`, `docs/requirements.md` | `docs/code-review.md` | Read, Grep, Glob, Bash |
| `verifier` | source code, tests, `docs/requirements.md` | `docs/verification.md` | Read, Grep, Glob, Bash, Write |

Requirements analysis and Pull Request preparation are intentionally **not** run as isolated subagents — see the corresponding commands/skills. Requirements gathering requires a live clarification dialogue with the human that a subagent cannot hold, and PR creation is a hard-to-reverse, externally-visible action that must happen in the main conversation where the human directly confirms each step.

General rules for all agents:

* Agents should review existing approved artifacts before producing downstream artifacts.
* Review agents (`design-reviewer`, `code-reviewer`, `verifier`) must critically evaluate work rather than automatically approving it, and must not soften findings to avoid conflict with the producing agent's decisions.
* An agent that finds a blocking ambiguity must stop and report it rather than guessing — the orchestrating conversation raises it to the human.

## Framework Usage Policy

* **Agents (subagents)** are used only where isolation, a distinct tool profile, or independence from the producer's context materially improves quality (design/code/verification review, and the multi-step architecture/planning/implementation phases).
* **Skills** hold the reusable *methodology* for a cross-cutting activity (how to analyze requirements, how to analyze architecture, how to review code, how to verify, how to prepare a PR) so that both the main conversation and subagents apply the same standard.
* **Commands** are the reusable entry point for each SDLC phase. A command loads the relevant skill, checks the relevant approval gate, and either runs inline (requirements, PR preparation) or dispatches to the relevant subagent (architecture, design review, planning, implementation, code review, verification).
* **Hooks** perform only mechanical, objective enforcement (file existence, pattern matching, running tests/linters). Hooks must never approve an artifact, decide a product question, or silently alter scope — they may only block an action and surface a message for a human or Claude to act on.

## Hook Rules

* Hooks may block an action that violates SDLC stage ordering (e.g., editing application source before `impl-plan.md` is approved).
* Hooks may run automated quality checks (lint/type-check) after implementation edits and surface failures; they must not silently "fix" or revert code.
* Hooks may block a completion/stop event if required tests have not been run, but they must not invent test results.
* Hooks may block a commit or PR-creation command if likely secrets are detected in the diff; they must not attempt to redact or rewrite history automatically.
* No hook may generate or modify an SDLC artifact (`requirements.md`, `architecture.md`, etc.) on its own.
