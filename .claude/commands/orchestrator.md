---
description: Single entry point to run the full Agentic SDLC — or resume an interrupted run — by delegating to the canonical Prompts/orchestrator.prompt.md.
---

Read and follow `Prompts/orchestrator.prompt.md` in full. That canonical Prompt (via `Agents/orchestrator.agent.md` and `Skills/orchestrator/SKILL.md`) determines actual workflow state, routes to the next eligible phase's own existing Prompt/Agent/Skill, and stops at every required Human-in-the-Loop gate defined in `CLAUDE.md`.

This runtime command is a delegation only — it must not reimplement orchestration logic. Do not use this file as a second, competing orchestrator implementation.
