---
name: requirements
description: Entry prompt for the Requirements phase of the Agentic SDLC.
---

# Requirements Prompt

## Invoke Agent

Read and follow `Agents/requirements.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/requirements/SKILL.md` for the requirements-analysis methodology (business objective, scope, actors, FR/NFR extraction, constraints, dependencies, acceptance criteria, assumptions, ambiguities, missing information, conflicts, and the clarification process).

## Source Selection

This Prompt is responsible for resolving the User Story input. Before invoking the Agent, determine which source applies and retrieve the content directly — never by writing an intermediate `user_story.md`:

* **Jira** — retrieve the selected issue through the Atlassian MCP (e.g. `getJiraIssue`, or `searchJiraIssuesUsingJql` to locate it first). Consume the issue's relevant User Story content directly.
* **Confluence** — locate/read the User Story page through the Atlassian MCP (e.g. `searchConfluence` to locate it, `getConfluenceContent` to read it). Consume the retrieved content directly.
* **Word document** — consume the user-supplied document through whatever file-reading mechanism is actually supported for that file. Do not claim native `.docx` support unless it has been verified; if unverified, ask the human to confirm the file is readable or supply a plain-text/markdown export.

Record the resolved source's non-secret metadata (see `Skills/requirements/SKILL.md` traceability expectations) for inclusion in `requirements.md`. Never retrieve or persist OAuth tokens, PATs, passwords, or other credentials as part of this step.

## Required Input

* The selected User Story content, resolved per Source Selection above (from Jira, Confluence, or a supplied Word document).
* Direct human answers to any clarification questions raised while applying the skill.

## Expected Output

`requirements.md` at the repository root, containing every section the skill requires, with FR-xxx/NFR-xxx identifiers and assumptions/ambiguities visibly separated from confirmed requirements.

## Human Approval / Gate

Gate G1: `requirements.md` must be reviewed and explicitly accepted by the human before Architecture may begin. Do not proceed past this gate on silence.

## Scope Boundary

Do this phase only. Do not begin architecture, design, planning, implementation, review, verification, or PR work in this pass, even if the requirements seem obvious or the next step seems easy.

## Stop Condition

STOP once `requirements.md` is produced (or clarification questions are posed) and reported to the human. Do not proceed to Architecture without explicit human approval of `requirements.md`.
