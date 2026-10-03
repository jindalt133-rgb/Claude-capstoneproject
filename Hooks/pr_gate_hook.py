#!/usr/bin/env python3
"""PreToolUse/Bash hook: gates PR-creation commands behind pre_pr_validation.py.

Reads the standard Claude Code PreToolUse hook JSON from stdin. If the Bash
command about to run looks like a PR-creation command (`gh pr create`,
`hub pull-request`, `git request-pull`, or an equivalent), this hook runs
the full pre-PR validation suite first and denies the tool call if any
blocking check fails. Any other Bash command is allowed through immediately
without paying the cost of the validation suite.

This hook does not create, push, or merge a Pull Request itself, and it
does not call an LLM or invoke any agent -- it only runs the deterministic
checks in pre_pr_validation.py and reports a permission decision.

Dry-run manually:
    echo '{"tool_input":{"command":"gh pr create --title x --body y"}}' \
        | python Hooks/pr_gate_hook.py
    echo '{"tool_input":{"command":"ls"}}' | python Hooks/pr_gate_hook.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

PR_CREATE_PATTERN = re.compile(
    r"(?i)\bgh\s+pr\s+create\b|\bhub\s+pull-request\b|\bgit\s+request-pull\b"
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # No parseable stdin -- never block on a hook-plumbing problem.
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not PR_CREATE_PATTERN.search(command):
        return 0  # not a PR-creation command; nothing to gate

    print(f"[pr_gate_hook] Detected PR-creation command: {command!r}")
    print("[pr_gate_hook] Running Hooks/pre_pr_validation.py before allowing it through...\n")

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "pre_pr_validation.py")],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Pre-PR validation failed (Hooks/pre_pr_validation.py "
                    f"exit code {result.returncode}). See output above. "
                    "Resolve the blocking failure(s) before running a "
                    "PR-creation command."
                ),
            }
        }
        print(json.dumps(decision))
    else:
        print("[pr_gate_hook] Pre-PR validation passed; allowing the command through.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
