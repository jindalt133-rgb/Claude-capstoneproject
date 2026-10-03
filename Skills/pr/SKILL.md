---
name: pr
description: Methodology for the fully automated Pull Request workflow — from confirming a passing verification result through to an actually-created GitHub Pull Request with a real returned URL. Used by Agents/pr.agent.md.
---

# Pull Request Skill

Adapted and substantially extended from the project's existing `github-pr-preparation` methodology (`.claude/skills/github-pr-preparation/SKILL.md`), which covered only manual drafting. This skill supersedes that draft-only scope: it defines the full automated preparation-through-creation workflow, ending in an actually-created Pull Request rather than a draft handed to the human to paste in manually.

This is run in the main conversation, not delegated to an isolated subagent: opening a PR is a hard-to-reverse, externally visible action, and the human must confirm it directly rather than through a subagent's summary.

## Purpose

Provide a consistent, automated methodology for turning an approved, passing verification result into an actual, existing GitHub Pull Request — accurate title and description, no secrets, no unwanted files, and a real returned PR URL — under the normal (prerequisites-met) path, without requiring the human to manually open GitHub, copy/paste the description, or click "Create Pull Request" themselves.

**Manual GitHub copy/paste is NOT the normal workflow.** It is only ever a fallback the human chooses after this skill has explicitly stopped and reported a missing prerequisite — never a silent default.

## Inputs / Prerequisites

* `docs/verification-report.md` — must show **PASS** or **PASS WITH DOCUMENTED LIMITATIONS**, explicitly accepted by the human.
* `requirements.md`, `impl-plan.md` — for summarizing approved scope accurately (not from memory of the conversation).
* Current repository state: `git status`, `git diff`, `git log`.
* An authorized, already-authenticated GitHub PR-creation mechanism (preferred: the `gh` CLI, already logged in via `gh auth login` run by the human beforehand).
* Explicit human authorization to open the PR.

## Method / Workflow

Execute in this order:

1. Read `docs/verification-report.md` and confirm its verdict is **PASS** or **PASS WITH DOCUMENTED LIMITATIONS**, explicitly accepted by the human. Any other verdict (FAIL, missing file, or no human acceptance) is a hard stop.
2. Inspect `git status` to see the full current working-tree state (staged, unstaged, untracked).
3. Inspect `git diff` (and `git diff --staged`) and `git log` to see the actual content changes and commit history that would go into the PR, and confirm they match the approved scope.
4. Detect accidental generated/cache files (e.g., `__pycache__/`, `*.pyc`, `.pytest_cache/`, generated-output directories, build artifacts) by cross-checking against `.gitignore`.
5. Check the diff and commit history for obvious secrets/credentials (API keys, tokens, passwords, connection strings).
6. Run, or verify the already-recorded results of, the approved final test command (e.g., `python -m pytest -q -rs`) — never fabricate test or CI evidence; do not claim a passing suite without this.
7. Generate the PR title from the approved scope: short, descriptive, not process-oriented.
8. Generate the complete PR description containing exactly these sections: **Summary**, **Changes Made**, **Test Evidence**, **Known Limitations**, **Reviewer Checklist**. Known limitations from `docs/verification-report.md` must not be omitted to make the change look cleaner.
9. If there are approved outstanding changes not yet committed, commit them (using the project's standard commit-message/attribution convention) — never commit anything not already approved for this PR's scope.
10. Push the approved feature branch to the remote.
11. Use an authenticated GitHub mechanism to create the Pull Request **automatically** (preferred: `gh pr create`) — do not ask the human to perform this step manually when the mechanism is available and prerequisites are met.
12. Verify the Pull Request actually exists (e.g., re-query it via the same mechanism) before reporting success.
13. Return the actual PR URL produced by the PR-creation call — never a fabricated, guessed, or templated URL.

## Validation Checks

* The verification verdict was actually read from `docs/verification-report.md` in this pass, not assumed.
* The diff matches approved scope — no unrelated files, no leftover debug code, no generated/cache artifacts.
* No secret or credential is present anywhere in the diff or commit history.
* The PR description contains all five required sections, and Known Limitations is not empty when `docs/verification-report.md` documented any.
* A real PR URL was returned by the GitHub mechanism before success is reported.

## Expected Evidence / Output

A pushed feature branch with only approved commits; an actually-created GitHub Pull Request with the generated title and a description containing Summary, Changes Made, Test Evidence, Known Limitations, and Reviewer Checklist; the real, returned PR URL reported to the human. OR, if a prerequisite is unmet: an explicit stop naming exactly which prerequisite is missing.

## Failure / Stop Conditions

* `docs/verification-report.md` is missing, shows FAIL, or has not been explicitly accepted by the human — stop before any git/GitHub action.
* No authorized, authenticated GitHub PR-creation mechanism is available (e.g., `gh` CLI not installed, or installed but not authenticated) — **stop immediately and report exactly that missing prerequisite.** Do not fall back to pretending the PR was created, and do not silently degrade to "please open GitHub yourself" as if that were the normal path.
* A secret/credential or an accidental generated/cache file is detected in the diff — stop and report it; do not push or create the PR until resolved.
* The PR-creation call does not return a real, verifiable PR — never report success from an assumed, simulated, or partially-completed action.

## Traceability Expectations

The PR description's Summary and Changes Made must trace back to `requirements.md` and `impl-plan.md` — describing what was approved and built, not aspirational or remembered scope. Test Evidence must trace back to the actual `docs/verification-report.md` results, not be restated from memory.

## Security Considerations

* Never place a PAT/token (or any other credential) in source code, prompts, agent definitions, skills, or committed configuration. Authentication must come from an already-authenticated out-of-band session (e.g., `gh auth login` run by the human beforehand), never from a token embedded in this project.
* Never automatically merge the Pull Request, under any circumstance — merging is a separate, human-only decision.
* Never close, modify, or replace any pre-existing manually-created PR.
* Never push to `main`/`master`, force-push, or rewrite history.
