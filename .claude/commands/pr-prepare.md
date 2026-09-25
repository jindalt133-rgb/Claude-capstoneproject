---
description: Run the Pull Request phase — draft a PR title/body/test plan from approved artifacts in this conversation, and only open the PR after explicit human confirmation.
---

Run the Pull Request phase of the Agentic SDLC defined in `CLAUDE.md`.

This phase runs directly in this conversation, not as a delegated subagent — opening a PR is a hard-to-reverse, externally visible action that the human must confirm directly.

1. Verify Gate G5's prerequisite: `docs/verification.md` shows a passing result, explicitly accepted by the human. If not, stop and report.
2. Apply the `github-pr-preparation` skill: summarize approved scope from `docs/requirements.md`/`docs/impl-plan.md`, draft a PR title and body (summary + test plan pulled from `docs/verification.md`), and run the pre-PR safety checks (no secrets in diff, no unrelated files, clean `git status`).
3. Present the drafted title/body/test plan to the human and explicitly ask for confirmation before doing anything else.
4. Do not push, commit, or run `gh pr create` until the human has explicitly confirmed. Do not create a PR speculatively.
