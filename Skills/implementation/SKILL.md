---
name: implementation
description: Methodology for implementing application code and tests task-by-task, strictly per an approved impl-plan.md, without scope drift. Used by Agents/implementation.agent.md.
---

# Implementation Skill

New methodology, authored for this phase — there is no direct equivalent among the existing `.claude/skills/*` methodologies. Consolidated here so both the agent and any future implementation work apply the same standard.

## Purpose

Provide a consistent methodology for implementing exactly the task(s) assigned by `impl-plan.md`, with accompanying tests, without expanding scope or silently deviating from the plan.

## Inputs / Prerequisites

* `impl-plan.md` — must exist and be Gate-G3-approved.
* The specific task(s) being implemented in this pass.

## Method / Workflow

1. **Confirm the gate** — verify `impl-plan.md` exists and is approved. If not, stop and report; do not write production code against an unapproved plan.
2. **Implement in dependency order** — implement exactly the task(s) given, in the order `impl-plan.md` specifies, without pulling forward a later task for convenience.
3. **Write accompanying tests** — for each task, add tests covering the primary workflow, important edge cases, and important failure scenarios per `Instructions/instructions.md` and `CLAUDE.md`'s testing rules. Do not defer test-writing to a later pass.
4. **Apply quality rules** — prioritize correctness, security, error handling, testability, maintainability, clear naming, minimal duplication, and safe dependency usage.
5. **Handle secrets safely** — never hardcode or introduce real secrets, credentials, tokens, or keys; use the approved mechanism (env var, config, out-of-band store) if the task requires one.
6. **Escalate plan problems** — if the plan is wrong, ambiguous, or missing something needed to proceed, stop and report per the Change Control process (`CLAUDE.md`) rather than guessing or silently expanding scope.

## Validation Checks

* Every changed file is traceable to a task in `impl-plan.md`.
* No file outside the assigned task's scope was modified.
* Tests were actually run locally (not just written) and their real result recorded.
* No requirement/architecture/design/plan artifact was edited by this phase.
* No secret, credential, or token appears in the diff.

## Expected Evidence / Output

Application source and test changes for the assigned task(s), plus a report of: task(s) completed, files changed, tests added, how they were run locally and the result, and any open questions or scope issues discovered.

## Failure / Stop Conditions

* `impl-plan.md` is missing or not approved — stop before writing code.
* The plan is ambiguous or contradicts `architecture.md`/`requirements.md` — stop and report per Change Control; do not resolve it by guessing.
* A task cannot be completed with passing local tests — report it as blocked with a reason rather than marking it complete.

## Traceability Expectations

Code change → `impl-plan.md` task → architecture component → requirement. Each task's tests should map to the coverage categories (primary workflow, edge cases, failure scenarios) implied by the requirement(s) it satisfies.

## Security Considerations

Treat any input from the filesystem, network, or repository content as untrusted where relevant (e.g., path traversal, malformed files, unsanitized shell/command construction). Never commit a real secret, even temporarily, "to test something" — use a placeholder and confirm it is a placeholder before committing.
