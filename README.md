# docsync — Automated Documentation Sync

Generates Markdown documentation from Python source and keeps it in sync with
code changes. `docsync` scans a source directory, extracts module/class/
function signatures and docstrings via static analysis (no code execution),
redacts sensitive-looking values, and writes a single Markdown file only when
the extracted content has actually changed.

## Installation

Requires Python 3.11+.

```bash
pip install -e .
```

This registers the `docsync` console script. You can also invoke the package
directly without installing an entry point:

```bash
python -m docsync --source <path>
```

## CLI usage

```bash
docsync --source <path> [--output <path>] [--exclude <pattern>]...
```

- `--source <path>` (required) — path to the Python source directory to scan.
- `--output <path>` (optional) — filename or sub-path for the generated file.
  Defaults to `code-documentation.md`. This value is always interpreted
  **relative to `docs/generated/`** — see Output boundary below.
- `--exclude <pattern>` (optional, repeatable) — additional glob-style
  exclusion pattern, matched against files/directories in the source tree.
  A built-in default exclusion set (`.git`, `.venv`, `venv`, `__pycache__`,
  `build`, `dist`, `node_modules`) always applies in addition to any
  `--exclude` patterns you provide.

Example:

```bash
docsync --source src/mypackage --output api/reference.md --exclude "*_test.py"
```

The command prints a one-line summary to stdout (whether documentation was
written or was already up to date) and prints any per-file errors or
warnings to stderr. The generated Markdown content itself is never printed to
stdout. The process exit code is `0` if no errors occurred, and non-zero if
any file could not be read/parsed or the output could not be written — even
when the run still produced output for the files that were valid (a single
broken file does not abort the run).

## Output boundary (`docs/generated/`)

All generated documentation is written under a fixed root, `docs/generated/`,
relative to the current working directory. `--output` only controls where
*inside* that root the file lands — it cannot be used to write outside of it.

Any `--output` value is rejected (non-zero exit, no file written) if it is:

- empty or blank
- an absolute path (POSIX or Windows form)
- a Windows drive-qualified or drive-relative path (e.g. `C:\evil.md`, `C:evil.md`)
- a UNC path (e.g. `\\server\share\evil.md`)
- a path containing `..` traversal components, including nested traversal
  and paths that merely resemble a sibling of `docs/generated/`
  (e.g. `../generated-evil/x.md`)
- a path that would resolve outside `docs/generated/` once symlinks are followed

A valid nested path, e.g. `--output api/nested/reference.md`, is accepted and
resolves to `docs/generated/api/nested/reference.md`.

If a file already exists at the resolved output path and was not previously
written by `docsync` (it lacks the tool's own header marker), the write is
refused rather than overwriting a hand-authored file — this is reported as an
error, and that pre-existing file is left untouched.

## Development

```bash
pip install -e ".[dev]"
python -m pytest
```
