"""Source Directory Scanner (architecture.md Section 7).

Walks the configured source directory, pruning excluded directories
BEFORE descending into them (supports NFR-002), and yields only `.py`
candidate files (FR-003). An unreadable subtree is reported as a
per-directory error and skipped, never fatal to the whole scan
(FR-013 extended to directories). The top-level source directory's
own readability is validated earlier, by the Configuration Resolver
(config.py's `_validate_source_dir`) -- that fatal case is not this
module's responsibility.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from docsync.config import matches_exclusion


@dataclass
class ScanError:
    path: str
    message: str


@dataclass
class ScanResult:
    files: list[Path]
    errors: list[ScanError]


def scan(source_dir: Path, exclusions: frozenset[str]) -> ScanResult:
    """Recursively walk source_dir, pruning excluded directories before
    descending into them, and return every `.py` file found plus any
    per-directory errors encountered along the way.
    """
    files: list[Path] = []
    errors: list[ScanError] = []

    def _walk(directory: Path) -> None:
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            errors.append(ScanError(path=str(directory), message=str(exc)))
            return

        for entry in entries:
            entry_path = Path(entry.path)
            try:
                relative = entry_path.relative_to(source_dir).as_posix()
                # No follow_symlinks=False here: the source-side walk is an
                # unspecial-cased, ordinary filesystem walk per architecture
                # Section 7 -- deliberately distinct from the FR-016
                # boundary check's symlink-following behavior.
                is_dir = entry.is_dir()
                is_file = entry.is_file()
            except OSError as exc:
                errors.append(ScanError(path=str(entry_path), message=str(exc)))
                continue

            if is_dir:
                if matches_exclusion(relative, exclusions):
                    continue
                _walk(entry_path)
            elif is_file:
                if matches_exclusion(relative, exclusions):
                    continue
                if entry_path.suffix == ".py":
                    files.append(entry_path)

    _walk(source_dir)
    return ScanResult(files=files, errors=errors)
