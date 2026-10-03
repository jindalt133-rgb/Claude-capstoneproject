#!/usr/bin/env python3
"""Deterministic validator for orchestrator-state.json (manual/optional).

Pure standard library, no network calls, no LLM invocation, read-only.
Not wired into .claude/settings.json -- this is a standalone check an
operator (or a future hook) can run on demand, the same way
Hooks/pre_pr_validation.py is run on demand, without changing when any
existing hook fires.

Validates only the deterministic, mechanical shape of the state file:
schema presence, gate enum values, and the APPROVED <-> approval_recorded/
approved_at consistency rule from Skills/orchestrator/SKILL.md Method
section 10. It does NOT and cannot judge whether a recorded approval was
actually given by a human -- that is a human decision this script never
makes or infers.

Run manually:
    python Hooks/orchestrator_state_check.py

Exit codes:
    0 - file absent (nothing to validate) or all checks passed
    1 - the file exists but fails a deterministic check
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT, SECRET_CONTENT_PATTERNS  # noqa: E402

STATE_FILE = "orchestrator-state.json"
ALLOWED_GATES = {"G1", "G2", "G3", "G4", "G5"}
ALLOWED_STATUSES = {"APPROVED", "UNKNOWN_LEGACY_UNRECORDED", "PENDING", "NOT_STARTED"}
REQUIRED_GATE_FIELDS = {
    "gate", "phase", "artifact", "status", "approval_recorded", "approved_at", "evidence",
}
REQUIRED_RESUME_FIELDS = {
    "last_completed_phase", "last_explicitly_approved_gate",
    "next_eligible_phase", "human_approval_currently_required",
}

FAIL: list[str] = []
WARN: list[str] = []


def check(label: str, ok: bool, detail: str = "", blocking: bool = True) -> bool:
    status = "PASS" if ok else ("FAIL" if blocking else "WARN")
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not ok:
        (FAIL if blocking else WARN).append(label)
    return ok


def main() -> int:
    path = REPO_ROOT / STATE_FILE
    print(f"=== orchestrator-state.json validation ({path}) ===\n")

    if not path.is_file():
        print(f"[SKIP] {STATE_FILE} does not exist -- nothing to validate "
              "(every gate is implicitly UNKNOWN_LEGACY_UNRECORDED).")
        return 0

    raw = path.read_text(encoding="utf-8", errors="replace")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        check(f"{STATE_FILE} is valid JSON", False, detail=str(exc))
        print("\nRESULT: BLOCKING -- fix the FAIL item(s) above before continuing.")
        return 1

    check("schema_version present (int)", isinstance(data.get("schema_version"), int))

    gates = data.get("gates")
    check("'gates' is a non-empty list", isinstance(gates, list) and len(gates) > 0)

    seen_gate_ids: set[str] = set()
    if isinstance(gates, list):
        for i, entry in enumerate(gates):
            label = f"gates[{i}]"
            if not isinstance(entry, dict):
                check(f"{label} is an object", False)
                continue
            missing = REQUIRED_GATE_FIELDS - entry.keys()
            check(f"{label} has required fields", not missing,
                  detail=("missing: " + ", ".join(sorted(missing))) if missing else "")

            gate_id = entry.get("gate")
            if gate_id in ALLOWED_GATES:
                seen_gate_ids.add(gate_id)
            check(f"{label}.gate is one of {sorted(ALLOWED_GATES)}", gate_id in ALLOWED_GATES,
                  detail=f"got {gate_id!r}")

            status = entry.get("status")
            check(f"{label}.status is one of {sorted(ALLOWED_STATUSES)}",
                  status in ALLOWED_STATUSES, detail=f"got {status!r}")

            approval_recorded = entry.get("approval_recorded")
            approved_at = entry.get("approved_at")
            if status == "APPROVED":
                ok = approval_recorded is True and approved_at is not None
                check(
                    f"{label}: status APPROVED implies approval_recorded=true and approved_at set",
                    ok,
                    detail=f"approval_recorded={approval_recorded!r}, approved_at={approved_at!r}",
                )
            else:
                ok = approval_recorded is False
                check(
                    f"{label}: non-APPROVED status implies approval_recorded=false",
                    ok,
                    detail=f"status={status!r}, approval_recorded={approval_recorded!r}",
                )

    missing_gates = ALLOWED_GATES - seen_gate_ids
    check(
        "all five gates (G1-G5) have an entry",
        not missing_gates,
        detail=("missing: " + ", ".join(sorted(missing_gates))) if missing_gates else "",
        blocking=False,
    )

    resume = data.get("resume")
    if isinstance(resume, dict):
        missing_resume = REQUIRED_RESUME_FIELDS - resume.keys()
        check("'resume' has required fields", not missing_resume,
              detail=("missing: " + ", ".join(sorted(missing_resume))) if missing_resume else "")
    else:
        check("'resume' is an object", False)

    hits = sorted({p.pattern for p in SECRET_CONTENT_PATTERNS if p.search(raw)})
    check(
        "No obvious secret-shaped literals in orchestrator-state.json",
        not hits,
        detail=("matched: " + "; ".join(hits)) if hits else "",
    )

    print()
    if FAIL:
        print(f"RESULT: BLOCKING FAILURE(S) ({len(FAIL)}): {', '.join(FAIL)}")
        return 1
    if WARN:
        print(f"RESULT: PASS with {len(WARN)} non-blocking warning(s).")
    else:
        print("RESULT: PASS -- orchestrator-state.json is deterministically well-formed.")
    print("This script never judges whether a recorded approval was actually given --")
    print("that remains a human decision this script cannot observe or infer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
