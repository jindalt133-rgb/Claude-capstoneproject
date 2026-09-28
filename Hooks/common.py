"""Shared constants and helpers for the project-level Agentic SDLC hooks.

Pure standard library, no network calls, no LLM invocation. Every helper
here is read-only unless a docstring says otherwise. REPO_ROOT is derived
from this file's own location so nothing in Hooks/ hard-codes a machine-
specific path.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_AGENTS = [
    "requirements.agent.md",
    "architecture.agent.md",
    "design.agent.md",
    "planning.agent.md",
    "implementation.agent.md",
    "review.agent.md",
    "verify.agent.md",
    "pr.agent.md",
]

REQUIRED_SKILLS = [
    "requirements",
    "architecture",
    "design",
    "planning",
    "implementation",
    "review",
    "verify",
    "pr",
]

REQUIRED_PROMPTS = [
    "requirements.prompt.md",
    "architecture.prompt.md",
    "design.prompt.md",
    "planning.prompt.md",
    "implementation.prompt.md",
    "review.prompt.md",
    "verify.prompt.md",
    "pr.prompt.md",
]

REQUIRED_SDLC_ARTIFACTS = [
    "user_story.md",
    "requirements.md",
    "architecture.md",
    "design-review.md",
    "impl-plan.md",
    "docs/code-review.md",
    "docs/verification-report.md",
]

INSTRUCTIONS_FILE = "Instructions/instructions.md"

# Cache/generated artifact shapes that must never be *tracked* by git, even
# though .gitignore already keeps them out of new commits (a stray `git add
# -f` or an artifact created before .gitignore covered it could still slip
# through).
GENERATED_ARTIFACT_PATTERNS = [
    re.compile(r"__pycache__/"),
    re.compile(r"\.pyc$"),
    re.compile(r"\.pyo$"),
    re.compile(r"\.egg-info/"),
    re.compile(r"(^|/)build/"),
    re.compile(r"(^|/)dist/"),
    re.compile(r"\.pytest_cache/"),
    re.compile(r"\.mypy_cache/"),
    re.compile(r"\.ruff_cache/"),
    re.compile(r"^docs/generated/"),
]

# Filenames that are almost never legitimate to commit.
CREDENTIAL_FILENAME_PATTERNS = [
    re.compile(r"(^|/)\.env(\..+)?$"),
    re.compile(r"\.pem$"),
    re.compile(r"\.pfx$"),
    re.compile(r"\.p12$"),
    re.compile(r"(^|/)id_rsa$"),
    re.compile(r"(^|/)id_dsa$"),
    re.compile(r"(^|/)id_ecdsa$"),
    re.compile(r"(^|/)id_ed25519$"),
    re.compile(r"credentials\.json$"),
    re.compile(r"service[-_]?account.*\.json$"),
    re.compile(r"(^|/)secrets?\.(ya?ml|json|env)$"),
]

# Content shapes that suggest a hardcoded secret/credential literal.
# Intentionally simple and self-contained: this is an independent,
# fast repository-hygiene guardrail, not a replacement for docsync's own
# NFR-003 redaction logic (docsync/sensitive.py), which implements the
# application's functional requirement and is scoped to generated docs,
# not to this repository's own commits/diffs.
SECRET_CONTENT_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key ID
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(
        r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*"
        r"['\"][^'\"\s]{6,}['\"]"
    ),
]


def run_git(*args: str) -> subprocess.CompletedProcess:
    """Run a read-only git command rooted at REPO_ROOT. Never mutates state."""
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
