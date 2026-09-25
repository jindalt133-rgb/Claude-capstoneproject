"""Configuration Resolver: merges CLI-supplied values with defaults, validates
the source directory, resolves exclusions, and (see boundary_check below)
validates the output path against the docs/generated/ boundary.

Per architecture.md Section 4.2 / Section 13 (resolves DR-003): this module
performs ONLY the FR-016 output-path boundary check. It does NOT perform the
FR-009 ownership-marker check -- that check requires inspecting the actual
target file's current contents and is the Output Writer's exclusive
responsibility (writer.py), run immediately before the write.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath

DEFAULT_EXCLUSIONS = frozenset(
    {".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules"}
)

DEFAULT_OUTPUT_FILENAME = "code-documentation.md"
GENERATED_ROOT_NAME = "docs/generated"


class ConfigError(Exception):
    """Raised when configuration cannot be resolved (fatal, pre-scan)."""


@dataclass
class Config:
    source_dir: Path
    output_path: Path
    exclusions: frozenset[str] = field(default_factory=lambda: DEFAULT_EXCLUSIONS)


def _validate_source_dir(source: str) -> Path:
    source_path = Path(source)
    if not source_path.exists():
        raise ConfigError(f"configured source directory does not exist: {source}")
    if not source_path.is_dir():
        raise ConfigError(f"configured source path is not a directory: {source}")
    try:
        next(source_path.iterdir(), None)
    except OSError as exc:
        raise ConfigError(
            f"configured source directory is not readable: {source} ({exc})"
        ) from exc
    return source_path


def _resolve_exclusions(custom_excludes: list[str] | None) -> frozenset[str]:
    excludes = set(DEFAULT_EXCLUSIONS)
    if custom_excludes:
        excludes.update(custom_excludes)
    return frozenset(excludes)


def matches_exclusion(relative_path: str, exclusions: frozenset[str]) -> bool:
    """True if relative_path (posix-style, relative to source root) is excluded.

    Default exclusions match by directory/file NAME anywhere in the tree.
    Custom exclusions (FR-005) are glob-style patterns matched against the
    relative path.
    """
    parts = Path(relative_path).parts
    if any(part in DEFAULT_EXCLUSIONS for part in parts):
        return True
    custom = exclusions - DEFAULT_EXCLUSIONS
    for pattern in custom:
        if fnmatch.fnmatch(relative_path, pattern):
            return True
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    return False


def _reject(candidate: str, reason: str) -> None:
    raise ConfigError(
        f"configured output path resolves outside docs/generated/: {candidate!r} ({reason})"
    )


def boundary_check(candidate: str, generated_root: Path | None = None) -> Path:
    """Validate a user-supplied --output candidate against the docs/generated/
    boundary. Implements architecture.md Section 11.1 / ADR-0005 exactly --
    do not invent a different algorithm. Returns the validated, resolved path
    on success; raises ConfigError on any failed step.
    """
    # Step 1: reject empty/blank.
    if candidate is None or candidate.strip() == "":
        raise ConfigError("configured output path is empty or blank")

    # Step 2: reject absolute paths, both interpretations, regardless of host OS.
    if PureWindowsPath(candidate).is_absolute() or PurePosixPath(candidate).is_absolute():
        _reject(candidate, "absolute paths are not permitted")

    # Step 3: reject Windows drive-qualified/drive-relative forms and UNC paths.
    if PureWindowsPath(candidate).drive != "":
        _reject(
            candidate,
            "Windows drive-qualified, drive-relative, or UNC paths are not permitted",
        )
    if candidate.startswith("\\\\") or candidate.startswith("//"):
        _reject(candidate, "UNC-style paths are not permitted")

    # Step 4: reject traversal components, split on both separators.
    normalized_for_split = candidate.replace("\\", "/")
    components = normalized_for_split.split("/")
    if any(component == ".." for component in components):
        _reject(candidate, "path traversal ('..') is not permitted")

    # Step 5: compute the real root.
    root = generated_root if generated_root is not None else Path(GENERATED_ROOT_NAME)
    real_root = root.resolve()

    # Step 6: join the validated-relative remainder onto the real root.
    candidate_path = real_root / candidate

    # Step 7: resolve the candidate (follows symlinks; tolerates non-existent
    # trailing components).
    real_candidate = candidate_path.resolve()

    # Step 8: decisive path-aware containment check. The candidate must
    # denote a file strictly INSIDE docs/generated/ -- the root directory
    # itself is never a valid output target (writing there would replace
    # the docs/generated/ directory with a plain file).
    if real_root not in real_candidate.parents:
        _reject(candidate, "the output must be a file inside docs/generated/, not the directory itself")

    # Steps 9-10: case-sensitivity and symlink-escape handling fall out
    # naturally from resolving both sides identically above -- no separate
    # rule is introduced.

    # Step 11/12: only a path that passed step 8 is returned; any failure
    # above already raised.
    return real_candidate


def resolve_config(
    source: str,
    output: str | None = None,
    excludes: list[str] | None = None,
    generated_root: Path | None = None,
) -> Config:
    """Resolve CLI-supplied values into a validated Config.

    Note: this function performs ONLY the boundary check portion of output
    resolution (architecture.md Section 4.2). It does not perform the FR-009
    ownership-marker check.
    """
    source_path = _validate_source_dir(source)
    exclusions = _resolve_exclusions(excludes)
    candidate = output if output is not None else DEFAULT_OUTPUT_FILENAME
    output_path = boundary_check(candidate, generated_root=generated_root)
    return Config(source_dir=source_path, output_path=output_path, exclusions=exclusions)
