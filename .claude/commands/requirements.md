---
description: Run the Requirements phase — analyze the selected User Story source (Jira, Confluence, or a supplied Word document), clarify ambiguities with the human, and produce requirements.md.
---

Run the Requirements phase of the Agentic SDLC defined in `CLAUDE.md`.

This phase runs in this conversation directly, not as a delegated subagent — requirements gathering requires a live clarification dialogue with the human.

1. Resolve the User Story from the selected source — Jira or Confluence via the Atlassian MCP, or a supplied Word document via the supported file-reading mechanism — as the primary source of truth. A local `user_story.md` is not required. Apply the methodology in the `requirements-analysis` skill.
2. Produce the analysis: business objective, scope, actors/stakeholders, functional requirements (FR-xxx), non-functional requirements (NFR-xxx), constraints, dependencies, acceptance criteria, assumptions, ambiguities, missing information, conflicting/unclear statements.
3. Identify every unresolved question that must be answered before requirements can be finalized — grouped by category, each with a brief reason if not obvious.
4. Present the questions and stop. Do not write `requirements.md` yet.
5. Once the human answers, and only once there are no remaining blocking questions, draft `requirements.md` and present it for explicit approval (Gate G1).
6. Do not write `requirements.md` to disk until the human has explicitly approved its content.
