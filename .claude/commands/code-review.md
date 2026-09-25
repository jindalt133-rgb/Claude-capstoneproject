---
description: Run the Code Review phase — dispatch to the code-reviewer agent to critically review implementation changes and produce docs/code-review.md.
---

Run the Code Review phase of the Agentic SDLC defined in `CLAUDE.md`.

1. Confirm there is implementation to review (changed/new files from the Implementation phase).
2. Dispatch to the `code-reviewer` agent to review the changes against `docs/impl-plan.md` and `docs/requirements.md`, per the `code-review` skill. It must produce `docs/code-review.md`.
3. Present the verdict and findings (blocking vs non-blocking) to the human.
4. If there are blocking findings, do not treat Gate G4 as passed. Route them back to the `developer` for the affected task(s) before re-running this phase.
5. Gate G4 is passed only once a code review with zero remaining blocking findings is explicitly accepted.
