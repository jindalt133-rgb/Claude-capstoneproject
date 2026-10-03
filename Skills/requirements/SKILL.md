---
name: requirements
description: Methodology for converting the selected User Story (from Jira, Confluence, or a supplied Word document, as resolved by Prompts/requirements.prompt.md) into clear, testable requirements.md without fabricating missing information. Used by Agents/requirements.agent.md.
---

# Requirements Skill

Adapted from the project's existing `requirements-analysis` methodology (`.claude/skills/requirements-analysis/SKILL.md`); paths updated to the root-level artifact layout.

## Purpose

Provide a consistent methodology for converting a User Story into clear, testable software requirements without fabricating missing information.

## Inputs / Prerequisites

* The selected User Story — the primary source of truth for this phase, resolved by `Prompts/requirements.prompt.md` from Jira, Confluence, or a supplied Word document. This methodology is source-agnostic; it does not perform or duplicate the MCP/file retrieval itself.
* Direct human answers to any clarification questions raised while applying this methodology.

## Method / Workflow

Analyze the User Story for the following areas, in order:

1. **Business Objective** — the business problem and intended outcome.
2. **Scope** — functionality explicitly inside the proposed solution's scope, and explicitly outside scope when stated.
3. **Actors and Stakeholders** — users, systems, teams, or other parties that interact with or are affected by the solution.
4. **Functional Requirements** — extract observable system behaviors; assign identifiers `FR-001`, `FR-002`, ... Each requirement should be clear and independently understandable.
5. **Non-Functional Requirements** — performance, security, reliability, maintainability, compatibility, usability; assign identifiers `NFR-001`, `NFR-002`, ... Do not invent numeric targets absent from the User Story.
6. **Constraints** — restrictions that limit implementation or operation.
7. **Dependencies** — external systems, tools, services, files, workflows, or upstream decisions required by the solution.
8. **Acceptance Criteria** — extract existing acceptance criteria and identify where additional criteria require clarification; criteria should eventually be objectively verifiable.
9. **Assumptions** — record separately; never silently treat an assumption as an approved requirement.
10. **Ambiguities** — statements with multiple reasonable interpretations.
11. **Missing Information** — information necessary for architecture, implementation, testing, or acceptance that has not been provided.
12. **Conflicting or Unclear Statements** — requirements that contradict each other or whose relationship is unclear.

### Clarification Process

For each unresolved issue: explain what is unclear, explain why the answer matters, ask a concise question, present reasonable options where useful, and do not choose an option on behalf of the human. Prioritize blocking questions over minor ones. Do not generate a final requirements specification while blocking questions remain unanswered.

## Validation Checks

Before finalizing `requirements.md`, verify that:

* Requirements are testable.
* Requirements do not contradict one another.
* Functional and non-functional requirements are separated.
* Assumptions are explicit and distinguished from firm requirements.
* Acceptance criteria can be verified.
* Important unresolved issues are visible, not buried.
* No requirement has been fabricated.

## Expected Evidence / Output

`requirements.md` at the repository root, containing every section above with FR-xxx/NFR-xxx identifiers, and assumptions/ambiguities visibly separated from confirmed requirements.

## Failure / Stop Conditions

* A blocking question is unresolved — stop and ask; do not guess.
* An assumption has not been explicitly confirmed by the human — keep it labeled as an assumption, do not promote it silently.

## Traceability Expectations

Every FR/NFR should be traceable to a specific statement in the selected User Story or an explicitly confirmed human answer recorded during clarification — never to an unstated inference.

When the User Story was retrieved from Jira or Confluence, `requirements.md` should record the source's non-secret metadata (e.g. Source Type, Source Page/Issue, Content ID/Issue Key, Space/Project, Source Version) for traceability. When it was supplied as a Word document, record equivalent safe document metadata (e.g. file name, supplied date). Never record OAuth tokens, PATs, passwords, authorization headers, or other credentials.

## Security Considerations

Do not record real credentials, tokens, or other secrets that may appear in a user story example into `requirements.md` — redact or generalize such values if the user story itself contains sample secrets.
