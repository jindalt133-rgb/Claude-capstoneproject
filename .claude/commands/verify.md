---
description: Run the Verification phase — dispatch to the verifier agent to independently run tests and check acceptance criteria, producing docs/verification.md.
---

Run the Verification phase of the Agentic SDLC defined in `CLAUDE.md`.

1. Verify Gate G4: `docs/code-review.md` shows zero blocking findings, explicitly accepted by the human. If not, stop and report.
2. Dispatch to the `verifier` agent to independently execute tests/build/lint and check every acceptance criterion in `docs/requirements.md`, per the `testing-verification` skill. It must produce `docs/verification.md`.
3. Present the verdict, traceability results, and any gaps to the human.
4. If there are blocking gaps, do not treat this as a passing verification. Route them back to the `developer`.
5. Gate G5's verification prerequisite is satisfied only once `docs/verification.md` shows a passing result explicitly accepted by the human.
