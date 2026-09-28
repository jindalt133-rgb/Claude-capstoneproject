#!/usr/bin/env python3
"""Pre-PR validation hook for the Automated Documentation Sync Agentic SDLC.

Deterministic, fast, fully offline. Does NOT call an LLM, does NOT recurse
into any agent, and does NOT create, push, or merge a Pull Request -- it
only validates that the prerequisites the PR Agent (Agents/pr.agent.md /
Skills/pr/SKILL.md) depends on are mechanically in place.

Run manually:
    python Hooks/pre_pr_validation.py

Exit codes:
    0 - all blocking checks passed (non-blocking warnings may still exist)
    1 - at least one blocking check failed
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    CREDENTIAL_FILENAME_PATTERNS,
    GENERATED_ARTIFACT_PATTERNS,
    INSTRUCTIONS_FILE,
    REPO_ROOT,
    REQUIRED_AGENTS,
    REQUIRED_PROMPTS,
    REQUIRED_SDLC_ARTIFACTS,
    REQUIRED_SKILLS,
    SECRET_CONTENT_PATTERNS,
    run_git,
)

BLOCKING: list[str] = []
WARNINGS: list[str] = []


def check(label: str, ok: bool, detail: str = "", blocking: bool = True) -> bool:
    status = "PASS" if ok else ("FAIL" if blocking else "WARN")
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not ok:
        (BLOCKING if blocking else WARNINGS).append(label)
    return ok


def check_required_files(section: str, base: Path, names: list[str], is_skill_dir: bool = False) -> None:
    missing = []
    for name in names:
        path = (base / name / "SKILL.md") if is_skill_dir else (base / name)
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(name)
    check(
        f"{section}: {len(names) - len(missing)}/{len(names)} present",
        not missing,
        detail=("missing: " + ", ".join(missing)) if missing else "",
    )


def check_sdlc_artifacts() -> None:
    missing = [a for a in REQUIRED_SDLC_ARTIFACTS if not (REPO_ROOT / a).is_file()]
    check(
        f"Required SDLC artifacts: {len(REQUIRED_SDLC_ARTIFACTS) - len(missing)}/{len(REQUIRED_SDLC_ARTIFACTS)} present",
        not missing,
        detail=("missing: " + ", ".join(missing)) if missing else "",
    )
    print(
        "      (existence only -- this hook never judges whether an artifact's "
        "verdict is approved; that decision stays with the human.)"
    )


def check_instructions() -> None:
    check(f"{INSTRUCTIONS_FILE} exists", (REPO_ROOT / INSTRUCTIONS_FILE).is_file())


def check_test_suite() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rs"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    tail = result.stdout.strip().splitlines()[-5:]
    for line in tail:
        print(f"      {line}")
    if result.stderr.strip():
        print(f"      stderr: {result.stderr.strip()[-500:]}")
    check(
        "Test suite exits zero (python -m pytest -q -rs)",
        result.returncode == 0,
        detail=f"exit code {result.returncode}",
    )


def check_tracked_generated_artifacts() -> None:
    result = run_git("ls-files")
    if result.returncode != 0:
        check("git ls-files available", False, detail=result.stderr.strip())
        return
    tracked = result.stdout.splitlines()
    hits = [f for f in tracked if any(p.search(f) for p in GENERATED_ARTIFACT_PATTERNS)]
    check(
        "No generated/cache artifacts tracked by git",
        not hits,
        detail=("tracked: " + ", ".join(hits)) if hits else "",
    )


def check_credential_filenames() -> None:
    tracked_result = run_git("ls-files")
    tracked = tracked_result.stdout.splitlines() if tracked_result.returncode == 0 else []
    status_result = run_git("status", "--porcelain")
    pending = (
        [line[3:] for line in status_result.stdout.splitlines() if len(line) > 3]
        if status_result.returncode == 0
        else []
    )
    candidates = sorted(set(tracked) | set(pending))
    hits = [f for f in candidates if any(p.search(f) for p in CREDENTIAL_FILENAME_PATTERNS)]
    check(
        "No obvious credential-shaped filenames staged/tracked",
        not hits,
        detail=("found: " + ", ".join(hits)) if hits else "",
    )


def check_secret_content_in_diff() -> None:
    diffs = []
    for args in (("diff",), ("diff", "--staged")):
        result = run_git(*args)
        if result.returncode == 0:
            diffs.append(result.stdout)
    combined = "\n".join(diffs)
    hits = sorted({p.pattern for p in SECRET_CONTENT_PATTERNS if p.search(combined)})
    check(
        "No obvious secret-shaped literals in git diff",
        not hits,
        detail=("matched pattern(s): " + "; ".join(hits)) if hits else "",
    )


def main() -> int:
    print("=== Pre-PR Validation (Hooks/pre_pr_validation.py) ===")
    print(f"Repo root: {REPO_ROOT}\n")

    check_required_files("Agents/", REPO_ROOT / "Agents", REQUIRED_AGENTS)
    check_required_files("Skills/", REPO_ROOT / "Skills", REQUIRED_SKILLS, is_skill_dir=True)
    check_required_files("Prompts/", REPO_ROOT / "Prompts", REQUIRED_PROMPTS)
    check_instructions()
    check_sdlc_artifacts()
    check_test_suite()
    check_tracked_generated_artifacts()
    check_credential_filenames()
    check_secret_content_in_diff()

    print()
    if BLOCKING:
        print(f"RESULT: BLOCKING FAILURE(S) ({len(BLOCKING)}): {', '.join(BLOCKING)}")
        print("The PR Agent must NOT proceed until these are resolved.")
        return 1
    if WARNINGS:
        print(f"RESULT: PASS with {len(WARNINGS)} non-blocking warning(s).")
    else:
        print("RESULT: PASS -- all pre-PR prerequisites mechanically satisfied.")
    print("This hook does not create, push, or merge a Pull Request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
