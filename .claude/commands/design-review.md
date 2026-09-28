---
description: Run the Design Review phase — dispatch to the design-reviewer agent to critically review architecture.md and produce design-review.md.
---

Run the Design Review phase of the Agentic SDLC defined in `CLAUDE.md`.

1. Verify `architecture.md` exists. If not, stop and report.
2. Dispatch to the `design-reviewer` agent to critically evaluate the architecture against `requirements.md`, per the `architecture-analysis` skill's review checklist. It must produce `design-review.md`.
3. Present the verdict and findings (blocking vs non-blocking) to the human.
4. If there are blocking findings, do not treat Gate G2 as passed. Route blocking findings back to the `architect` (or to the human, if they require a product decision) before re-running this phase.
5. Gate G2 is passed only once the human explicitly accepts a design-review with zero remaining blocking findings.
