---
name: pr
description: Entry prompt for the automated Pull Request phase of the Agentic SDLC.
---

# Pull Request Prompt

## Invoke Agent

Read and follow `Agents/pr.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Read and use `Skills/pr/SKILL.md` and apply its full automated PR workflow.

## Required Input

* `docs/verification-report.md` — must show PASS or PASS WITH DOCUMENTED LIMITATIONS, explicitly accepted by the human.
* `requirements.md`, `impl-plan.md` (for summarizing approved scope)
* Current repository/git state
* An authorized, already-authenticated GitHub PR-creation mechanism
* Explicit human authorization to open the PR

## Required Automated Workflow

Executing this prompt means carrying out the full automated PR workflow, in order:

1. Read the approved `docs/verification-report.md` and confirm its verdict.
2. Inspect repository/git state (`git status`, `git diff`, `git diff --staged`, `git log`).
3. Perform the required secret/artifact checks (generated/cache files against `.gitignore`; obvious secrets/credentials in the diff and history).
4. Verify final test evidence — run or verify the already-recorded results of the approved test command.
5. Prepare the PR title and the PR description (Summary, Changes Made, Test Evidence, Known Limitations, Reviewer Checklist).
6. Commit approved outstanding changes if appropriate.
7. Push the feature branch.
8. Create the GitHub Pull Request **automatically**, using an authenticated GitHub mechanism (preferred: `gh pr create`).
9. Verify the PR actually exists.
10. Return the actual PR URL.

**Manual copy/paste of the PR description into GitHub is NOT the normal workflow.** Instructing the human to do this is only acceptable as an explicit fallback after this prompt has stopped and reported a missing prerequisite — never presented as the default path.

**Do not automatically merge the Pull Request**, under any circumstance.

**If authenticated GitHub PR tooling is unavailable** (e.g., `gh` CLI not installed, or installed but not authenticated), STOP and report exactly that missing prerequisite. Do not claim success, do not fabricate a URL, and do not silently fall back to a manual flow as if it were expected.

## Expected Output

A pushed feature branch with only approved commits, an actually-created GitHub Pull Request with the generated title/description, and the real returned PR URL reported to the human — OR an explicit stop naming the exact missing prerequisite, with no PR falsely claimed.

## Human Approval / Gate

Gate G5: requires both a passing, human-accepted `docs/verification-report.md` and explicit human authorization to open the PR. Runs inline in the main conversation so the human directly confirms each step before the hard-to-reverse action of opening a real PR.

## Scope Boundary

Do this phase only. This is the final SDLC phase — there is no next phase to silently perform. Do not merge the PR, and do not modify any prior SDLC artifact as part of this pass.

## Stop Condition

STOP once the real PR URL is returned and reported, or once an explicit missing-prerequisite stop has been reported. Take no further action either way.
