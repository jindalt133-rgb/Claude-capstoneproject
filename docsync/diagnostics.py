"""Error & Diagnostics Reporter (architecture.md, FR-013/FR-014).

A single structured error type collects per-file/per-directory errors
from the Scanner, Parser, and Writer, formats them as clear,
file-identified messages, and determines the run's final exit code.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocSyncError:
    path: str
    stage: str
    message: str

    def format(self) -> str:
        return f"[{self.stage}] {self.path}: {self.message}"


@dataclass
class DiagnosticsReport:
    errors: list[DocSyncError] = field(default_factory=list)

    def add(self, error: DocSyncError) -> None:
        self.errors.append(error)

    def extend(self, errors: list[DocSyncError]) -> None:
        self.errors.extend(errors)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def exit_code(self) -> int:
        """FR-014: zero only if no important error was recorded; any
        recorded error is treated as important -- a per-file/per-directory
        error is still surfaced to the human even though it did not abort
        the run (FR-013)."""
        return 1 if self.has_errors else 0

    def format_all(self) -> list[str]:
        return [error.format() for error in self.errors]
