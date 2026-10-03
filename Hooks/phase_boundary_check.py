#!/usr/bin/env python3
"""Phase-boundary guard (PreToolUse: Write|Edit).

Blocks Claude from writing/editing application source or tests
(docsync/**, tests/**) before Gate G3 has mechanically been reached --
i.e. before impl-plan.md exists at the repository root.

This is a purely mechanical existence check. Per CLAUDE.md's Hook Rules,
a hook may check a gate artifact's existence/mechanical state but must
never decide whether it is *approved* -- that stays a human decision made
in the conversation, which this hook cannot observe and does not attempt to.

Reads the standard Claude Code PreToolUse hook JSON from stdin.

Dry-run manually:
    echo '{"tool_input":{"file_path":"docsync/core.py"}}' \
        | python Hooks/phase_boundary_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT  # noqa: E402

GUARDED_PREFIXES = ("docsync/", "tests/")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0

    try:
        rel_str = str(Path(file_path).resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return 0

    if not rel_str.startswith(GUARDED_PREFIXES):
        return 0  # not application source/tests; nothing to guard

    if (REPO_ROOT / "impl-plan.md").is_file():
        return 0  # Gate G3 artifact mechanically exists; allow

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Gate G3 not mechanically reached: impl-plan.md does not exist "
                f"at the repository root, so application source/test edits "
                f"({rel_str}) are blocked. This checks existence only, not "
                f"human approval -- produce impl-plan.md and get it explicitly "
                f"approved before implementing."
            ),
        }
    }
    print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
