"""Change Detector (architecture.md Section 12, resolves DR-005).

Per-file hash table, keyed by source-relative path, embedded as a
single-line JSON object inside the header banner's HTML comment:

    <!-- docsync:v1 sha256={"pkg/a.py": "3f2a...", "pkg/sub/b.py": "9c11..."} -->

Hashes are computed from each file's already-redacted (TASK-008)
extracted model (Section 9), which by construction never contains
function/method body statements -- so a body-only source change never
changes the hash, and a signature/docstring change always does.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict

from docsync.model import ModuleDoc

BANNER_PATTERN = re.compile(r"<!-- docsync:v1 sha256=(\{.*?\}) -->")

# The ownership-marker guard (ADR-0004, FR-009) checks only for this
# prefix's presence -- it does not need to parse the hash table.
HEADER_MARKER = "<!-- docsync:v1"


def compute_file_hash(module: ModuleDoc) -> str:
    """SHA-256 over a sorted-key JSON serialization of the model's
    documentation-relevant fields (docstring, classes, functions).
    `path` and `errors` are excluded: `path` is the hash table's own key,
    and `errors` are run diagnostics, not documentation content.
    """
    payload = {
        "docstring": module.docstring,
        "classes": [asdict(c) for c in module.classes],
        "functions": [asdict(f) for f in module.functions],
    }
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_hash_table(modules: list[ModuleDoc]) -> dict[str, str]:
    return {module.path: compute_file_hash(module) for module in modules}


def serialize_hash_table(table: dict[str, str]) -> str:
    return json.dumps(table, sort_keys=True)


def parse_previous_hash_table(existing_output_text: str | None) -> dict[str, str]:
    """Read the prior run's hash table from an existing output file's
    header banner. An absent file, absent marker, or malformed JSON is all
    treated the same as "no prior state" -- full regeneration.
    """
    if not existing_output_text:
        return {}
    match = BANNER_PATTERN.search(existing_output_text)
    if not match:
        return {}
    try:
        table = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    if not isinstance(table, dict):
        return {}
    return table


def has_changed(previous: dict[str, str], current: dict[str, str]) -> bool:
    """True if any file's hash differs, a file is new, or a previously
    included file was removed -- i.e. the two tables are not identical."""
    return previous != current
