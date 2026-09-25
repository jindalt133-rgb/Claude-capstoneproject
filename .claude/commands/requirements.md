---
description: Run the Requirements phase — analyze docs/user-story.md, clarify ambiguities with the human, and produce docs/requirements.md.
---

Run the Requirements phase of the Agentic SDLC defined in `CLAUDE.md`.

This phase runs in this conversation directly, not as a delegated subagent — requirements gathering requires a live clarification dialogue with the human.

1. Read `docs/user-story.md` as the primary source of truth. Apply the methodology in the `requirements-analysis` skill.
2. Produce the analysis: business objective, scope, actors/stakeholders, functional requirements (FR-xxx), non-functional requirements (NFR-xxx), constraints, dependencies, acceptance criteria, assumptions, ambiguities, missing information, conflicting/unclear statements.
3. Identify every unresolved question that must be answered before requirements can be finalized — grouped by category, each with a brief reason if not obvious.
4. Present the questions and stop. Do not write `docs/requirements.md` yet.
5. Once the human answers, and only once there are no remaining blocking questions, draft `docs/requirements.md` and present it for explicit approval (Gate G1).
6. Do not write `docs/requirements.md` to disk until the human has explicitly approved its content.
