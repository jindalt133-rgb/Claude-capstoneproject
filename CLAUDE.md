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

## Agentic SDLC Structure (Canonical)

The canonical implementation of this Agentic SDLC lives in five explicit, portable layers at the repository root:

* **`Instructions/instructions.md`** — cross-cutting rules shared by every phase (traceability, gate approval, no silent requirement invention, security, test-evidence rules, phase-boundary rules, secret handling, review-history preservation, stop-on-blocking-findings). `CLAUDE.md` is the high-level orchestration entry point and defers to `Instructions/instructions.md` for this rule-level detail; where the two ever appear to conflict, this file's SDLC stage ordering and gate table win.
* **`Agents/*.agent.md`** — define *who* does a phase of work and the boundaries of that role.
* **`Skills/*/SKILL.md`** — define *how* to do the work correctly: the reusable methodology/checklist the corresponding Agent applies.
* **`Prompts/*.prompt.md`** — the canonical, human-facing entry point that invokes the right Agent (and its Skill) against the right approved inputs.
* **`Hooks/`** — mechanical, deterministic enforcement (gate-artifact existence, secret scanning, test-before-PR). Hooks block or warn; they never author, approve, or silently fix an artifact.

This structure — `Instructions/`, `Agents/`, `Skills/`, `Prompts/`, `Hooks/` — is the authoritative capstone workflow. The pre-existing `.claude/agents/`, `.claude/skills/`, and `.claude/commands/` files are legacy/runtime material from an earlier iteration of this project's tooling; they are retained for reference (see "Legacy Runtime Subagents" below) but are not the source of truth for how a phase is invoked or what methodology it applies.

Every phase follows the same pipeline:

Prompt → Agent → Skill → SDLC phase work → Artifact → Human Gate

The eight phases, in order, are: **requirements, architecture, design, planning, implementation, review, verify, pr.**

## Phase → Prompt → Agent → Skill → Artifact Mapping

| Phase | Prompt | Agent | Skill | Artifact |
|---|---|---|---|---|
| Requirements | `Prompts/requirements.prompt.md` | `Agents/requirements.agent.md` | `Skills/requirements/SKILL.md` | `requirements.md` |
| Architecture | `Prompts/architecture.prompt.md` | `Agents/architecture.agent.md` | `Skills/architecture/SKILL.md` | `architecture.md` |
| Design Review | `Prompts/design.prompt.md` | `Agents/design.agent.md` | `Skills/design/SKILL.md` | `design-review.md` |
| Implementation Planning | `Prompts/planning.prompt.md` | `Agents/planning.agent.md` | `Skills/planning/SKILL.md` | `impl-plan.md` |
| Implementation | `Prompts/implementation.prompt.md` | `Agents/implementation.agent.md` | `Skills/implementation/SKILL.md` | application source code, tests |
| Code Review | `Prompts/review.prompt.md` | `Agents/review.agent.md` | `Skills/review/SKILL.md` | `docs/code-review.md` |
| Verification | `Prompts/verify.prompt.md` | `Agents/verify.agent.md` | `Skills/verify/SKILL.md` | `docs/verification-report.md` |
| Pull Request | `Prompts/pr.prompt.md` | `Agents/pr.agent.md` | `Skills/pr/SKILL.md` | an actual, created GitHub Pull Request |

This table is the canonical description of how each SDLC phase is invoked and what it produces. It supersedes the "Legacy Runtime Subagents" table below wherever the two would otherwise disagree.

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
| G1 | Starting Architecture | `requirements.md` reviewed and accepted |
| G2 | Starting Implementation Planning | `architecture.md` has passed `design-review.md` with no unresolved blocking findings |
| G3 | Starting Implementation | `impl-plan.md` reviewed and accepted |
| G4 | Starting Verification | Implementation and `docs/code-review.md` blocking findings resolved |
| G5 | Creating a Pull Request | `docs/verification-report.md` shows a passing result and the human has explicitly authorized opening the PR |

Hooks may check for the *existence and mechanical state* of these gate artifacts (see Hook Rules below) but the decision to accept an artifact is always the human's, never inferred by Claude or a hook.

## Requirements Rules

Treat `user_story.md` as the primary source during requirements analysis.

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

## Pull Request Automation

The Pull Request phase (`Prompts/pr.prompt.md` → `Agents/pr.agent.md` → `Skills/pr/SKILL.md`) is responsible for automatically creating the GitHub Pull Request once Gate G5 is satisfied. In order, it must:

1. Validate that `docs/verification-report.md` shows a passing result explicitly accepted by the human (Gate G5).
2. Validate repository state (`git status`, `git diff`, commit history).
3. Validate tests, security (no secrets/credentials), and required artifacts.
4. Prepare the PR title and description.
5. Push the approved feature branch.
6. Create the Pull Request automatically, using an authenticated GitHub mechanism (e.g. `gh pr create`).
7. Verify the Pull Request actually exists.
8. Return the actual PR URL.

Manual copy/paste of the PR title/description into GitHub is **not** the normal workflow — it exists only as a fallback after this phase has explicitly stopped. If no authenticated GitHub PR-creation mechanism is available, the PR phase must STOP and report the missing prerequisite rather than claim success, fabricate a URL, or fall back to manual instructions silently. Creating the Pull Request is as far as this phase goes: merging remains a separate, human-only decision and is never automatic.

## Legacy Runtime Subagents (`.claude/agents/`)

Before the `Instructions/` / `Agents/` / `Skills/` / `Prompts/` / `Hooks/` structure existed, this project used a set of Claude Code runtime subagents defined under `.claude/agents/*.md`, invoked via `.claude/commands/*.md`, and following the skills under `.claude/skills/`. Those files still exist and are left in place as legacy/runtime material, but they are **not** the canonical description of this project's workflow — see "Phase → Prompt → Agent → Skill → Artifact Mapping" above for the current, authoritative mapping. The table below documents what those legacy files do, for historical reference only:

| Legacy agent | Reads | Produces | Tools |
|---|---|---|---|
| `architect` | `requirements.md` | `architecture.md`, `docs/adr/*` | Read, Grep, Glob, Write, Edit |
| `design-reviewer` | `architecture.md`, `requirements.md` | `design-review.md` | Read, Grep, Glob, Write, Edit |
| `implementation-planner` | `architecture.md`, `design-review.md` | `impl-plan.md` | Read, Grep, Glob, Write, Edit |
| `developer` | `impl-plan.md` | application source code, tests | Read, Grep, Glob, Write, Edit, Bash |
| `code-reviewer` | source diff, `impl-plan.md`, `requirements.md` | `docs/code-review.md` | Read, Grep, Glob, Bash |
| `verifier` | source code, tests, `requirements.md` | `docs/verification-report.md` | Read, Grep, Glob, Bash, Write |

General rules that still apply to any agent, legacy or current:

* Agents should review existing approved artifacts before producing downstream artifacts.
* Review agents (design review, code review, verification) must critically evaluate work rather than automatically approving it, and must not soften findings to avoid conflict with the producing agent's decisions.
* An agent that finds a blocking ambiguity must stop and report it rather than guessing — the orchestrating conversation raises it to the human.

## Framework Usage Policy

The canonical capstone structure is `Instructions/`, `Agents/`, `Skills/`, `Prompts/`, and `Hooks/` at the repository root (see "Agentic SDLC Structure (Canonical)" above). The pre-existing `.claude/agents/`, `.claude/skills/`, and `.claude/commands/` files described in "Legacy Runtime Subagents" above are retained for reference only and are not the authoritative source for how a phase is invoked or what methodology it applies.

* **`Agents/*.agent.md`** are used where isolation, a distinct tool profile, or independence from the producer's context materially improves quality (design/code/verification review, and the multi-step architecture/planning/implementation phases).
* **`Skills/*/SKILL.md`** hold the reusable *methodology* for a cross-cutting activity (how to analyze requirements, how to analyze architecture, how to review code, how to verify, how to prepare and create a PR) so that every phase applies the same standard.
* **`Prompts/*.prompt.md`** are the canonical reusable entry point for each SDLC phase. A prompt identifies its Agent and Skill, checks the relevant approval gate, and either runs inline (requirements, PR) or dispatches to the relevant Agent — see the "Phase → Prompt → Agent → Skill → Artifact Mapping" table above.
* **`Hooks/`** perform only mechanical, objective enforcement (file existence, pattern matching, running tests/linters). Hooks must never approve an artifact, decide a product question, or silently alter scope — they may only block an action and surface a message for a human or Claude to act on.

## Hook Rules

* Hooks may block an action that violates SDLC stage ordering (e.g., editing application source before `impl-plan.md` is approved).
* Hooks may run automated quality checks (lint/type-check) after implementation edits and surface failures; they must not silently "fix" or revert code.
* Hooks may block a completion/stop event if required tests have not been run, but they must not invent test results.
* Hooks may block a commit or PR-creation command if likely secrets are detected in the diff; they must not attempt to redact or rewrite history automatically.
* No hook may generate or modify an SDLC artifact (`requirements.md`, `architecture.md`, etc.) on its own.
