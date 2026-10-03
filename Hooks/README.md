# Hooks/ — Project-Level Agentic SDLC Guardrails

This directory contains **project-local**, deterministic hook scripts for the
Automated Documentation Sync capstone. They enforce mechanical guardrails
around the four-layer Agentic SDLC structure (`Agents/` → `Skills/` →
`Prompts/` → `Hooks/`) and around the Approval Gates defined in `CLAUDE.md`.

None of these hooks call an LLM, invoke an agent, make a network call,
create a commit, push, create a Pull Request, or merge anything. They are
pure, fast, standard-library Python that read some local state and print a
pass/fail/warn report — plus, for the `PreToolUse` hooks, a permission
decision consumed by Claude Code itself.

They are registered in `.claude/settings.json` (see "Registration" below)
and can also be run by hand at any time (see "Manual usage" per hook).

## Files

| File | Role |
|---|---|
| `common.py` | Shared constants (required file lists, regex patterns) and a read-only `run_git()` helper. Not a hook itself — imported by the others. |
| `pre_pr_validation.py` | The **pre-PR validation** guardrail. Standalone script; also invoked automatically by `pr_gate_hook.py`. |
| `pr_gate_hook.py` | `PreToolUse` / `Bash` hook. Detects a PR-creation-shaped command and runs `pre_pr_validation.py` before allowing it through. |
| `lightweight_validation.py` | `PostToolUse` / `Write\|Edit` hook. Fast, single-file sanity check after an edit. |
| `phase_boundary_check.py` | `PreToolUse` / `Write\|Edit` hook. Mechanical Gate-G3-existence guard on `docsync/**` and `tests/**` edits. |
| `orchestrator_state_check.py` | Standalone, optional deterministic validator for `orchestrator-state.json`. Not registered in `.claude/settings.json` — run manually. |

## Registration (`.claude/settings.json`)

This file did not exist before this task and was created fresh:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",       "hooks": [{ "type": "command", "command": "python Hooks/pr_gate_hook.py", "timeout": 60 }] },
      { "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "python Hooks/phase_boundary_check.py", "timeout": 15 }] }
    ],
    "PostToolUse": [
      { "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "python Hooks/lightweight_validation.py", "timeout": 30 }] }
    ]
  }
}
```

No other keys were touched (there was nothing else in the file). This is a
project-level file — it is intended to be committed, unlike
`.claude/settings.local.json`, which is already gitignored.

## Hook-by-hook detail

### 1. `pre_pr_validation.py` — Pre-PR validation

- **Trigger/event:** Not bound directly to a Claude Code event (there is no
  "before PR" event in the supported hook vocabulary). Instead it is invoked
  automatically by `pr_gate_hook.py` (a real `PreToolUse`/`Bash` hook) when a
  PR-creation-shaped Bash command is detected, and it can always be run by
  hand.
- **What it validates (9 checks):**
  1. `Agents/`: all 9 required `*.agent.md` files exist and are non-empty (the eight phase agents plus `orchestrator.agent.md`).
  2. `Skills/`: all 9 required `Skills/<name>/SKILL.md` files exist and are non-empty (the eight phase skills plus `orchestrator`).
  3. `Prompts/`: all 9 required `*.prompt.md` files exist and are non-empty (the eight phase prompts plus `orchestrator.prompt.md`).
  4. `Instructions/instructions.md` exists.
  5. Required SDLC artifacts exist (`requirements.md`,
     `architecture.md`, `design-review.md`, `impl-plan.md`,
     `docs/code-review.md`, `docs/verification-report.md`) — **existence
     only**. This hook never parses or judges an artifact's verdict; per
     `CLAUDE.md`'s Hook Rules, accepting an artifact is always a human
     decision. `user_story.md` is intentionally not required here: the
     canonical Requirements workflow resolves its User Story input from
     Jira, Confluence, or a supplied Word document (see `CLAUDE.md`'s
     Requirements Rules) and does not depend on a local snapshot file.
  6. The test suite (`python -m pytest -q -rs`) is actually runnable and
     exits `0`. A non-zero exit (including a genuine test failure) is a
     blocking failure — this single check covers both "the test command can
     be executed" and "test failures produce a non-zero result."
  7. No generated/cache-shaped paths (`__pycache__/`, `*.pyc`, `.egg-info/`,
     `build/`, `dist/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`,
     `docs/generated/`) are tracked by git (`git ls-files`).
  8. No credential-shaped filenames (`.env*`, `*.pem`, `id_rsa`,
     `credentials.json`, etc.) appear in `git ls-files` or
     `git status --porcelain`.
  9. No secret-shaped content (AWS access key IDs, PEM private-key headers,
     `password/secret/token/api_key = "..."`-style literals) appears in
     `git diff` or `git diff --staged`.
- **Blocking vs non-blocking:** all 9 checks above are blocking (exit 1 on
  any failure). There are currently no non-blocking warnings emitted by this
  script, though the `check()` helper supports `blocking=False` for future
  use.
- **Run manually:**
  ```
  python Hooks/pre_pr_validation.py
  ```
- **Exit codes:** `0` = all checks passed; `1` = at least one blocking check
  failed.
- **Portability:** pure standard library (`subprocess`, `pathlib`, `re`);
  invokes the test suite via `sys.executable -m pytest`, not a hard-coded
  `python`/`python3` binary name; `REPO_ROOT` is derived from
  `Path(__file__).resolve().parent.parent`, never a hard-coded path.

### 2. `pr_gate_hook.py` — PR-creation gate

- **Trigger/event:** `PreToolUse`, matcher `Bash`.
- **What it validates:** whether the Bash command about to run matches
  `gh pr create`, `hub pull-request`, or `git request-pull` (case-insensitive,
  word-boundary matched). Any other Bash command is a fast no-op pass-through
  (returns immediately without running the validation suite). A match
  triggers a full run of `pre_pr_validation.py`.
- **Blocking vs non-blocking:** blocking. If `pre_pr_validation.py` exits
  non-zero, this hook prints a `hookSpecificOutput.permissionDecision: "deny"`
  JSON object, which Claude Code uses to deny the tool call. It never denies
  a non-PR-creation command.
- **Run manually (dry run):**
  ```
  echo '{"tool_input":{"command":"gh pr create --title x --body y"}}' | python Hooks/pr_gate_hook.py
  echo '{"tool_input":{"command":"ls"}}' | python Hooks/pr_gate_hook.py
  ```
- **Exit codes:** the script itself always exits `0` (the hook *ran*
  successfully) — the allow/deny decision is conveyed through the printed
  `permissionDecision` JSON field, per the documented Claude Code hook
  schema, not through the process exit code.
- **Portability:** stdlib only (`json`, `re`, `subprocess`, `pathlib`); if
  stdin is not parseable JSON it fails open (returns 0 / allow) rather than
  blocking on a plumbing error.

### 3. `lightweight_validation.py` — Post-edit sanity check

- **Trigger/event:** `PostToolUse`, matcher `Write|Edit`.
- **What it validates**, scoped to only the single file just written/edited:
  - `docsync/**/*.py` or `tests/**/*.py`: syntax-compiles via `py_compile`
    (**blocking** — a syntax error is an objective, mechanical defect).
  - `Agents/*.agent.md`: presence of the 10 required section headers
    (non-blocking WARN).
  - `Skills/*/SKILL.md`: presence of the 8 required section headers
    (non-blocking WARN).
  - `Prompts/*.prompt.md`: references both an `Agents/` path and a `Skills/`
    path (non-blocking WARN).
  - Any file: obvious secret-shaped content patterns (non-blocking WARN —
    the blocking secret check for what's actually staged/diffed lives in
    `pre_pr_validation.py`, which runs before a PR, not on every edit).
- **Blocking vs non-blocking:** only the Python syntax check is blocking.
  Everything else is an informational WARN so that this hook stays fast and
  never runs "the entire expensive SDLC pipeline" on every edit, per the
  task's explicit constraint.
- **Run manually:**
  ```
  python Hooks/lightweight_validation.py --file docsync/core.py
  python Hooks/lightweight_validation.py --file Agents/pr.agent.md
  ```
  (or pipe the standard `PostToolUse` stdin JSON shape).
- **Exit codes:** `0` = pass (WARNs, if any, are informational only);
  `1` = blocking (Python syntax error).
- **Portability:** stdlib only (`argparse`, `json`, `py_compile`, `tempfile`,
  `pathlib`); no dependency on external formatters/linters.

### 4. `phase_boundary_check.py` — Gate G3 existence guard

- **Trigger/event:** `PreToolUse`, matcher `Write|Edit`.
- **What it validates:** if the file about to be written/edited is under
  `docsync/` or `tests/` (application source/tests), checks whether
  `impl-plan.md` exists at the repository root. Any other path is a
  no-op pass-through.
- **Blocking vs non-blocking:** blocking for guarded paths. If
  `impl-plan.md` does not exist, prints a
  `hookSpecificOutput.permissionDecision: "deny"` JSON object. This is
  **existence-only** — per `CLAUDE.md`'s Hook Rules, a hook may check a gate
  artifact's mechanical state but must never infer or decide human approval,
  so this hook does not (and cannot) determine whether `impl-plan.md` was
  actually *approved*, only whether it exists.
- **Run manually (dry run):**
  ```
  echo '{"tool_input":{"file_path":"docsync/core.py"}}' | python Hooks/phase_boundary_check.py
  ```
- **Exit codes:** always exits `0` (like `pr_gate_hook.py`, the allow/deny
  decision is conveyed via the printed `permissionDecision` JSON, not the
  exit code).
- **Portability:** stdlib only (`json`, `pathlib`); fails open (no-op) on
  unparseable stdin or a path outside the repository.

### 5. `orchestrator_state_check.py` — `orchestrator-state.json` shape validator (optional, standalone)

- **Trigger/event:** none — not registered in `.claude/settings.json`. A standalone, manually-run deterministic check, the same way `pre_pr_validation.py` can be run by hand.
- **What it validates:** if `orchestrator-state.json` exists at the repository root — the durable gate-approval record used by the Orchestrator (`Agents/orchestrator.agent.md`, `Skills/orchestrator/SKILL.md`) to resume safely across sessions — it checks: the file is valid JSON; `schema_version` is present; every entry in `gates` has the required fields and a `gate` value in `G1`–`G5` and a `status` value in `APPROVED`/`UNKNOWN_LEGACY_UNRECORDED`/`PENDING`/`NOT_STARTED`; every `APPROVED` entry has `approval_recorded: true` and a non-null `approved_at` (and every non-`APPROVED` entry has `approval_recorded: false`); `resume` has its required fields; and no secret-shaped content appears in the file. If the file does not exist, the check is a no-op PASS (every gate is then implicitly `UNKNOWN_LEGACY_UNRECORDED`).
- **What it deliberately does NOT do:** it never judges *whether* a recorded approval was actually given by a human — only that the file's own internal consistency rules (e.g., `APPROVED` always paired with `approval_recorded: true`) hold. Deciding or inferring approval remains a human decision this script cannot observe.
- **Blocking vs non-blocking:** malformed JSON, missing required fields, an invalid `gate`/`status` value, or an `APPROVED`/`approval_recorded` inconsistency are blocking. A missing G1–G5 entry is a non-blocking WARN (a fresh or partially-initialized state file is valid).
- **Run manually:**
  ```
  python Hooks/orchestrator_state_check.py
  ```
- **Exit codes:** `0` = file absent, or all checks passed; `1` = at least one blocking check failed.
- **Portability:** stdlib only (`json`, `pathlib`); reuses `common.py`'s `SECRET_CONTENT_PATTERNS`.

## General notes

- **Windows/portability:** every hook is invoked as `python Hooks/<script>.py`
  (not a shebang-executed `.sh`/`.ps1` script), so the same registration
  works on the Windows environment this project was developed in and on any
  POSIX environment with `python` on `PATH`. No hook hard-codes a user path,
  and none reference the unrelated global `codemie` hook or its path.
- **No network calls.** Every check here operates on local files and local
  `git` state only.
- **No secrets in hooks.** Nothing in `Hooks/` contains or requires a PAT,
  token, password, or credential — the credential/secret checks are pure
  pattern matching against filenames and diff content, not authentication.
- **Fail-clear:** every blocking failure prints a specific `[FAIL]` line
  naming what failed and why; every hook that produces a permission decision
  includes a human-readable `permissionDecisionReason`.
