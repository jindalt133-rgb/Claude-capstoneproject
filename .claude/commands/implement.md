---
description: Run the Implementation phase — dispatch to the developer agent to implement one or more tasks from an approved impl-plan.md.
argument-hint: [task id or description, optional]
---

Run the Implementation phase of the Agentic SDLC defined in `CLAUDE.md`.

1. Verify Gate G3: `impl-plan.md` exists and is explicitly approved by the human. If not, stop and report.
2. Determine which task(s) to implement next, in the dependency order `impl-plan.md` specifies (use `$ARGUMENTS` if a specific task was named; otherwise pick the next unblocked task).
3. Dispatch to the `developer` agent to implement that task, including tests, per `CLAUDE.md` Quality and Testing Rules.
4. Report back to the human what was implemented, what tests were added and run, and any open questions or scope issues the developer flagged.
5. Do not silently continue to the next task without the human's awareness if the developer reported a blocking open question or a plan discrepancy.
