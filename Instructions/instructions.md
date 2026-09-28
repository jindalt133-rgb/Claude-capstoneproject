# Cross-Cutting SDLC Instructions

These rules apply to every agent, skill, and prompt in this project, regardless of phase. They are commonized here so they are stated once instead of repeated in each `Agents/*.agent.md` file. `CLAUDE.md` is the high-level orchestration entry point and defers to this file for these cross-cutting rules; where the two ever appear to conflict, `CLAUDE.md`'s SDLC stage ordering and gate table win, and this file's rule-level detail governs how each stage is actually carried out.

## 1. Requirement Traceability

Maintain traceability, where practical, along the chain:

Requirement → Architecture component → Implementation task → Code → Test

Every downstream artifact should be able to point back to the specific upstream item(s) that justify it. An agent that cannot trace a piece of work to an approved upstream artifact must flag it rather than proceed.

## 2. Human Approval Gates

Gates G1–G5 (defined in `CLAUDE.md`) require **explicit** human approval before the next phase begins. Silence, inactivity, or an unrelated message from the human is never approval. An agent that reaches a gate boundary stops and reports; it does not infer approval and continue.

## 3. No Silent Requirement Invention

Do not convert an assumption, a convenient default, or an agent's own judgment call into a requirement, acceptance criterion, or NFR target unless it is already present in an approved upstream artifact. When a decision requires new information not present upstream, surface it as an open question to the human — do not decide it and move on.

## 4. Security Rules

* Never write real secrets, API keys, tokens, passwords, or credentials into source, tests, commits, PR descriptions, or any artifact under `Agents/`, `Skills/`, `Prompts/`, `Instructions/`, or `Hooks/`.
* A PAT/token must never be placed in source code, prompts, agent definitions, skills, or committed configuration — authenticate out-of-band (e.g., an already-authenticated `gh` CLI session) instead.
* Treat any credential-shaped string found during work as a defect to flag, not a value to copy elsewhere.

## 5. Test Evidence Rules

* A test result may only be reported after the test was actually executed in this pass — reading code and inferring "this would pass" is not evidence.
* Record the exact command run and its real output (or a faithful summary of it).
* Do not report higher coverage or a broader passing scope than what was actually run.

## 6. No Claiming Unexecuted Tests Passed

If a required test was skipped, not run, flaky, or could not be executed, say so explicitly. Do not mark a task, a code review, or a verification as passing while masking an unexecuted or failing test.

## 7. No Bypassing Phase Boundaries

Each agent performs only its own phase (see `Agents/*.agent.md`). An agent must not silently perform another agent's job — e.g., the developer does not review its own code as if it were the reviewer, the architect does not write implementation code, the verifier does not patch application code to make a test pass. If a phase's output reveals a problem in an earlier phase, stop and route it back per Change Control (`CLAUDE.md`), rather than absorbing the fix into the current phase.

## 8. No Exposing Secrets

Do not print, log, or persist environment variables, credential files, or token values as part of any artifact, status update, or PR description, even for debugging purposes.

## 9. Preserve Review History

Do not delete or overwrite prior review, remediation, or verification artifacts (`design-review.md`, `docs/code-review.md`, `docs/verification-report.md`, ADRs under `docs/adr/`) to make current status look cleaner. If a phase is re-run after fixes, add the new result alongside or below the prior one rather than erasing the record of what was previously found.

## 10. Stop on Blocking Findings

A blocking finding (from design review, code review, or verification) means the current gate is not passed. Do not soften a blocking finding to non-blocking to allow progress. Route blocking findings back to the responsible agent (or to the human, if a product decision is required) and re-run the phase once addressed.

## How Agents, Skills, Prompts, and Hooks Relate

* **Agents** (`Agents/*.agent.md`) define *who* does a phase of work and the boundaries of that role.
* **Skills** (`Skills/*/SKILL.md`) define *how* to do the work correctly — the reusable methodology/checklist an agent applies. An agent references its skill; it does not restate the skill's content.
* **Prompts** (`Prompts/*.prompt.md`) are the short, human-facing entry point that invokes the right agent against the right approved inputs. A prompt does not duplicate a skill's methodology.
* **Hooks** (`Hooks/`) mechanically enforce a subset of the above (gate-artifact existence, secret scanning, test-before-PR) — they block or warn, but never author, approve, or silently fix an artifact themselves.
