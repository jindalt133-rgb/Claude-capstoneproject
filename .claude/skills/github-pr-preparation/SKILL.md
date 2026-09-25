---
name: github-pr-preparation
description: Methodology for drafting a Pull Request title, description, and test plan from approved SDLC artifacts, and for the pre-PR secret/sanity checks. Use during the Pull Request phase, in the main conversation (not as a subagent), since opening a PR requires direct human confirmation.
---

# GitHub PR Preparation Skill

## Purpose

Provide a consistent methodology for preparing a Pull Request so it accurately reflects the approved requirements, architecture, and verification results — and for the final safety checks before anything is pushed or opened.

This is run in the main conversation, not delegated to an isolated subagent: opening a PR is a hard-to-reverse, externally visible action, and the human must confirm it directly rather than through a subagent's summary.

## Preconditions

* `docs/verification.md` shows a passing result (Gate G5 prerequisite).
* The human has explicitly authorized opening the PR — this skill drafts the PR; it does not open it.

## Steps

### 1. Summarize Approved Scope

Pull the summary of what was actually built from `docs/requirements.md` and `docs/impl-plan.md` — not from memory of the conversation. The PR description should describe what was approved and built, not aspirational scope.

### 2. Draft PR Title

Short (under ~70 characters), describing the change, not the process.

### 3. Draft PR Body

Include:

* **Summary** — 1-3 bullets on what changed and why, referencing requirement IDs where useful.
* **Test plan** — pulled from `docs/verification.md`: what was run, what passed, any known gaps explicitly called out (do not omit known gaps to make the PR look cleaner).

### 4. Pre-PR Safety Checks

Before proposing to push or open the PR:

* Confirm no secrets/credentials are present in the diff (this is also enforced mechanically by the pre-commit/pre-PR hook — treat that as a backstop, not a substitute for looking).
* Confirm the diff matches approved scope — no unrelated files, no leftover debug code.
* Confirm `git status` is clean of anything unexpected (stray untracked files, accidental large files).

### 5. Human Confirmation

Present the drafted title/body/test plan to the human explicitly and wait for confirmation before running any push or `gh pr create` command. Do not create the PR speculatively "to show what it would look like."

## Anti-patterns to avoid

* Writing a test plan that says more was verified than `docs/verification.md` actually shows.
* Bundling unrelated cleanup into the same PR without flagging it.
* Proceeding to `gh pr create` on an assumed approval.
