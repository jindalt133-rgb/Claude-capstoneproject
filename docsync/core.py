"""Pipeline Orchestrator (architecture.md Section 16).

A single importable entry point, `run(config) -> Result`, independent of
CLI process invocation (NFR-004) so a future Git-hook/CI wrapper could
call it directly. Sequences Config -> Scanner -> Parser -> Model ->
Sensitive-Value Filter -> Change Detector -> Renderer -> Writer.

Pre-scan fatal conditions (unreadable source root, boundary-check failure)
are the Configuration Resolver's responsibility (`config.resolve_config`,
which raises ConfigError) and are handled by the caller BEFORE `run` is
invoked -- `run` assumes it has already received a validated `Config`.
Everything within `run` itself is per-file/non-fatal (FR-013): one bad
file or directory is recorded as a diagnostic and does not abort the run.
"""

from __future__ import annotations

from dataclasses import dataclass

from docsync.changedetect import build_hash_table, has_changed, parse_previous_hash_table
from docsync.config import Config
from docsync.diagnostics import DiagnosticsReport, DocSyncError
from docsync.parser import SourceReadError, extract_module, read_source
from docsync.render import render
from docsync.scanner import scan
from docsync.sensitive import filter_module
from docsync.writer import WriteRefusedError, write_output


@dataclass
class Result:
    diagnostics: DiagnosticsReport
    written: bool


def run(config: Config) -> Result:
    diagnostics = DiagnosticsReport()

    scan_result = scan(config.source_dir, config.exclusions)
    for scan_error in scan_result.errors:
        diagnostics.add(DocSyncError(path=scan_error.path, stage="scan", message=scan_error.message))

    modules = []
    for file_path in scan_result.files:
        relative = file_path.relative_to(config.source_dir).as_posix()
        try:
            source = read_source(file_path)
        except SourceReadError as exc:
            diagnostics.add(
                DocSyncError(path=relative, stage=exc.error.stage, message=exc.error.message)
            )
            continue

        module = extract_module(relative, source)
        if module.errors:
            for parse_error in module.errors:
                diagnostics.add(
                    DocSyncError(path=relative, stage=parse_error.stage, message=parse_error.message)
                )
            continue

        modules.append(filter_module(module))

    hash_table = build_hash_table(modules)

    previous_text = None
    if config.output_path.exists():
        try:
            previous_text = config.output_path.read_text(encoding="utf-8")
        except OSError as exc:
            diagnostics.add(
                DocSyncError(path=str(config.output_path), stage="read-previous", message=str(exc))
            )
    previous_table = parse_previous_hash_table(previous_text)

    written = False
    if has_changed(previous_table, hash_table):
        content = render(modules, hash_table)
        try:
            write_output(config.output_path, content)
            written = True
        except WriteRefusedError as exc:
            diagnostics.add(DocSyncError(path=str(config.output_path), stage="write", message=str(exc)))
        except OSError as exc:
            diagnostics.add(DocSyncError(path=str(config.output_path), stage="write", message=str(exc)))

    return Result(diagnostics=diagnostics, written=written)
