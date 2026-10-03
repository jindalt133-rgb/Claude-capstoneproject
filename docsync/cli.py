"""CLI entry point (architecture.md Section 17).

Single-command CLI: `docsync --source <path> [--output <path>] [--exclude <pattern> ...]`.
Maps args to a validated Config, invokes the Pipeline Orchestrator, and maps
the Result to a process exit code. Summary goes to stdout; errors/warnings
go to stderr. The generated Markdown itself is never printed to stdout.
"""

from __future__ import annotations

import argparse
import sys

from docsync.config import ConfigError, resolve_config
from docsync.core import run


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docsync",
        description="Generate Markdown documentation from Python source and keep it in sync.",
    )
    parser.add_argument("--source", required=True, help="path to the Python source directory")
    parser.add_argument(
        "--output",
        default=None,
        help="filename or sub-path relative to docs/generated/ (default: code-documentation.md)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="additional glob-style exclusion pattern (repeatable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = resolve_config(args.source, output=args.output, excludes=args.exclude)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = run(config)

    for message in result.diagnostics.format_all():
        print(message, file=sys.stderr)

    if result.written:
        print(f"documentation written: {config.output_path}")
    else:
        print("no changes detected; documentation is already up to date")

    return result.diagnostics.exit_code()


if __name__ == "__main__":
    sys.exit(main())
