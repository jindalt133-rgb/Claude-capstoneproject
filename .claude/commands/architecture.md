---
description: Run the Architecture phase — dispatch to the architect agent to produce docs/architecture.md from an approved docs/requirements.md.
---

Run the Architecture phase of the Agentic SDLC defined in `CLAUDE.md`.

1. Verify Gate G1: `docs/requirements.md` exists and has been explicitly approved by the human. If not, stop and tell the human which gate is unmet — do not proceed.
2. Dispatch to the `architect` agent to produce `docs/architecture.md` (and any ADRs) per the `architecture-analysis` skill.
3. Present the resulting architecture and any open questions the agent raised to the human.
4. Do not proceed to Design Review until the human has reviewed this output. Fixing open questions may require returning to Requirements — do not resolve them yourself.
