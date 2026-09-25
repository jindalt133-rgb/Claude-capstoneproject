"""Output Writer (architecture.md Sections 11.2/11.3, resolves DR-003/DR-008).

Operates ONLY on a path that has already passed TASK-004's boundary check
(`config.boundary_check`) -- this module never re-derives or repeats that
check. Sequence: (a) create the target's parent directory; (b) the FR-009
ownership-marker guard, exclusively here, exclusively at write time,
immediately before writing; (c) an atomic write (temp file in the same
directory, then replace).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from docsync.changedetect import HEADER_MARKER


class WriteRefusedError(Exception):
    """Raised when the ownership-marker guard refuses to overwrite an
    existing, unrecognized (non-tool-owned) file (FR-009/ADR-0004)."""


def write_output(target: Path, content: str) -> None:
    """Write `content` to `target`, a path already validated by
    `config.boundary_check`. Raises WriteRefusedError if a file already
    exists at `target` and does not carry this tool's own header-banner
    marker -- such a file is left untouched (FR-009).
    """
    # (a) Directory creation (resolves DR-008): only for an already
    # boundary-checked path.
    target.parent.mkdir(parents=True, exist_ok=True)

    # (b) Ownership-marker guard (FR-009/ADR-0004): exclusively here,
    # exclusively at write time, immediately before the write.
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if HEADER_MARKER not in existing:
            raise WriteRefusedError(
                f"refusing to overwrite existing file not recognized as "
                f"this tool's own generated output: {target}"
            )

    # (c) Atomic write: temp file in the same directory, then replace.
    fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".docsync-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
