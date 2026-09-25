---
description: Run the Implementation Planning phase — dispatch to the implementation-planner agent to produce docs/impl-plan.md from an approved architecture and passed design review.
---

Run the Implementation Planning phase of the Agentic SDLC defined in `CLAUDE.md`.

1. Verify Gate G2: `docs/architecture.md` exists and `docs/design-review.md` shows zero blocking findings, explicitly accepted by the human. If not, stop and report.
2. Dispatch to the `implementation-planner` agent to produce `docs/impl-plan.md`: an ordered, dependency-aware task breakdown tracing to architecture components and requirement IDs.
3. Present the task list and order to the human, along with any gaps the planner flagged back to architecture.
4. Gate G3 is passed only once the human explicitly approves `docs/impl-plan.md`.
