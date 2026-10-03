#!/usr/bin/env python3
"""Post-edit lightweight validation hook (PostToolUse: Write|Edit).

Fast, deterministic, single-file checks meant to run after every Write/Edit
-- this is explicitly NOT the full SDLC validation pipeline (see
pre_pr_validation.py for that). Reads the standard Claude Code PostToolUse
hook JSON from stdin and validates only the one file that was just
written/edited.

Checks performed on the edited file, where applicable:
  * Python files under docsync/ or tests/: syntax-compile check (py_compile)
    -- BLOCKING, since a syntax error is an objective, mechanical defect.
  * Agents/*.agent.md, Skills/*/SKILL.md, Prompts/*.prompt.md: minimal
    required-section presence check -- informational WARN only.
  * Any file: obvious secret-shaped content patterns -- informational WARN
    only (the blocking secret check for git-tracked changes lives in
    pre_pr_validation.py, which runs before a PR, not on every keystroke).

Can also be run manually against an explicit file:
    python Hooks/lightweight_validation.py --file docsync/core.py
    python Hooks/lightweight_validation.py --file Agents/pr.agent.md
"""
from __future__ import annotations

import argparse
import json
import py_compile
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT, SECRET_CONTENT_PATTERNS  # noqa: E402

REQUIRED_AGENT_SECTIONS = [
    "## Role", "## Objective", "## Inputs", "## Required Skill",
    "## Responsibilities", "## Allowed Actions", "## Forbidden Actions",
    "## Expected Output", "## Human Approval", "## Completion Criteria",
]
REQUIRED_SKILL_SECTIONS = [
    "## Purpose", "## Inputs", "## Method", "## Validation Checks",
    "## Expected Evidence", "## Failure", "## Traceability",
    "## Security Considerations",
]


def get_edited_path() -> Path | None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file")
    args, _ = parser.parse_known_args()
    if args.file:
        return (REPO_ROOT / args.file).resolve()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    file_path = tool_input.get("file_path") or tool_response.get("filePath")
    return Path(file_path).resolve() if file_path else None


def check_python_syntax(path: Path) -> tuple[bool, str]:
    try:
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(path), cfile=str(Path(tmp) / "out.pyc"), doraise=True)
        return True, ""
    except py_compile.PyCompileError as exc:
        return False, str(exc)
    except OSError as exc:
        return False, str(exc)


def missing_sections(text: str, required: list[str]) -> list[str]:
    return [s for s in required if s not in text]


def main() -> int:
    path = get_edited_path()
    if path is None or not path.is_file():
        print("[SKIP] No editable file identified from hook input; nothing to check.")
        return 0

    try:
        rel_str = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        rel_str = str(path).replace("\\", "/")

    print(f"=== Lightweight Post-Edit Validation: {rel_str} ===")
    blocking = False

    if rel_str.endswith(".py") and (rel_str.startswith("docsync/") or rel_str.startswith("tests/")):
        ok, detail = check_python_syntax(path)
        print(f"[{'PASS' if ok else 'FAIL'}] Python syntax compiles" + (f" -- {detail}" if detail else ""))
        blocking = blocking or not ok

    text = path.read_text(encoding="utf-8", errors="replace")

    if rel_str.startswith("Agents/") and rel_str.endswith(".agent.md"):
        missing = missing_sections(text, REQUIRED_AGENT_SECTIONS)
        print(f"[{'PASS' if not missing else 'WARN'}] Agent required sections present" + (f" -- missing: {', '.join(missing)}" if missing else ""))
    elif rel_str.startswith("Skills/") and rel_str.endswith("SKILL.md"):
        missing = missing_sections(text, REQUIRED_SKILL_SECTIONS)
        print(f"[{'PASS' if not missing else 'WARN'}] Skill required sections present" + (f" -- missing: {', '.join(missing)}" if missing else ""))
    elif rel_str.startswith("Prompts/") and rel_str.endswith(".prompt.md"):
        ok = "Agents/" in text and "Skills/" in text
        print(f"[{'PASS' if ok else 'WARN'}] Prompt references an Agent path and a Skill path")

    hits = sorted({p.pattern for p in SECRET_CONTENT_PATTERNS if p.search(text)})
    print(
        f"[{'PASS' if not hits else 'WARN'}] No obvious secret-shaped literals in file content"
        + (f" -- matched: {'; '.join(hits)}" if hits else "")
    )

    print()
    if blocking:
        print("RESULT: BLOCKING -- fix the FAIL item(s) above before continuing.")
        return 1
    print("RESULT: PASS (any WARNs above are informational only).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
