# ADR-0004: Generated-Output Ownership and Overwrite Safety

Status: Proposed (pending Design Review / Gate G2)
Date: 2026-09-24

## Context

FR-009 requires that the tool never create, modify, or overwrite manually
maintained documentation located outside its designated generated-output location.
FR-016 additionally requires that the output location be user-configurable "where
appropriate." These two requirements are in tension unless the mechanism for
honoring FR-016 is designed carefully: an unrestricted "write anywhere" output-path
option could let a misconfigured run point at an existing manually maintained file
(e.g., a hand-written `README.md`) and destroy it, directly violating FR-009.

## Options Considered

1. **Fixed root, no override:** ignore FR-016; always write to
   `docs/generated/code-documentation.md`.
2. **Unrestricted override:** let `--output` point at any path; overwrite whatever
   is there.
3. **Guarded override:** let `--output` point at any path, but before writing,
   require the target file to either not exist yet, or already contain the tool's
   own generated-file marker (the header banner from ADR-0003). If the target
   exists and does **not** contain that marker, refuse to write and report an error
   (FR-014) instead of overwriting.

## Decision

Option 3 — **guarded override**. The default output path is
`docs/generated/code-documentation.md` (FR-008). FR-016's configurability is
implemented by allowing `--output <path>` to redirect the write target, but the
Output Writer will only ever write to a path that is either new or already
recognizably a prior generated-output file of this tool. Any other existing file at
the target path is left untouched and reported as a configuration error.

## Rationale

- **FR-009 (never touch manual docs) is the hard constraint;** it must hold
  regardless of how a user configures FR-016. A purely fixed root (option 1) would
  satisfy FR-009 trivially but would not implement FR-016 at all. An unrestricted
  override (option 2) implements FR-016 but creates a direct, high-severity path to
  violating FR-009 by misconfiguration (e.g., accidentally pointing `--output` at
  `README.md`).
- **The marker-based guard (option 3)** lets FR-016 be honestly satisfied — the
  user can redirect output — while making an accidental overwrite of a manually
  maintained file structurally difficult: the tool only ever overwrites files that
  are empty/new, or that it can recognize as its own prior output via the ADR-0003
  header banner.
- **FR-014 (communicate important errors clearly):** a refused write due to an
  unrecognized existing file at the target path is exactly the kind of "important
  error" FR-014 requires surfacing, with the specific path named.

## Trade-offs Accepted

- If a user deletes the header banner from a previously generated file by hand and
  then re-runs the tool with the same output path, the guard cannot recognize the
  file as its own and will refuse to overwrite it, requiring the user to delete or
  rename the file first. This is treated as an acceptable, safe-by-default
  inconvenience rather than a defect, since silently overwriting an unrecognized
  file is exactly the risk FR-009 exists to prevent.
- This mechanism only detects "is this recognizably our own prior output," not "is
  this file manually maintained" in general — it cannot prevent a user from
  pointing `--output` at a location and then, on a *first* run, overwriting a
  pre-existing non-generated file that happens not to exist yet at the moment of
  the check race (accepted as an inherent limitation of a single-process CLI tool
  with no locking guarantees; no concurrency behavior is required per requirements
  Section 8 assumptions).
- Because changing the ownership-guard mechanism later would change what existing
  files are considered "safe to overwrite" for every existing adopter, this is
  treated as hard to reverse and recorded as an ADR rather than a routine
  implementation note.

## Consequences

- The Output Writer component must read (not just write) the target path before
  writing, to check for the marker.
- The generated-file header banner introduced in ADR-0003 now serves a second
  purpose: ownership marking for FR-009, in addition to change-detection storage.

## Resolution (2026-09-24, post-decision update)

This ADR's original Decision anticipated Option 3 ("guarded override") as a
mitigation for a *broader, unrestricted* `--output` path — at the time this ADR
was written, FR-016 was ambiguous about whether `--output` could target any
filesystem path, and the marker-based ownership guard was framed as the sole
safety net against that possibility.

The human has since resolved FR-016's ambiguity in `docs/requirements.md`,
under the `CLAUDE.md` change-control process (see `docs/requirements.md`
Section 12, Change Log, and `docs/architecture.md` Section 24): **FR-016's
configurability is restricted to the filename/sub-path within `docs/generated/`
only.** Arbitrary paths outside `docs/generated/` are now rejected **by
construction** — a path-boundary check in the Configuration Resolver
(`docs/architecture.md` Sections 11 and 13) normalizes the resolved `--output`
path and refuses any value that does not resolve inside the `docs/generated/`
subtree, before this ADR's guard ever runs.

This changes the guard's role but does not eliminate it:

- The original Options/Decision/Rationale/Trade-offs above are kept as the
  historical record of the reasoning at the time and are **not** rewritten.
- The marker-based ownership guard (Option 3, as decided) is **retained**, but
  now operates only on paths that have already passed the boundary check — i.e.,
  paths known to be within `docs/generated/`. Its remaining purpose is
  defense-in-depth: protecting against the narrower case where a user-specified
  sub-path *within* `docs/generated/` happens to collide with a pre-existing,
  non-tool-owned file at that location (e.g., a stray hand-placed file under
  `docs/generated/`).
- The guard is **no longer the sole safety net** against arbitrary-path
  misconfiguration. That risk (e.g., `--output ../../etc/something` or
  `--output /etc/passwd`) is now prevented structurally by the boundary check,
  which rejects such values before the Output Writer or its marker check is ever
  reached.

No option previously considered is re-opened; this is a scoping clarification of
Option 3's applicability, made necessary by the human's FR-016 decision, not a
reversal of the guarded-override decision itself.

## Further Resolution (2026-09-24, remediation update — resolves design-review DR-001, DR-003, DR-008)

The Resolution note above correctly established that the marker-based ownership
guard now operates only on paths that have already passed a boundary check, but
`docs/architecture.md`'s prior draft still gave **two contradictory accounts** of
*which component* runs this guard and *when* — Sections 4.2/13/16 said the
Configuration Resolver validates "against the ownership guard rules... before any
scanning begins," while Sections 4.10/11 (point 2) said the Output Writer checks the
marker immediately before writing. `docs/design-review.md` DR-003 correctly flagged
this as a genuine internal contradiction, not a wording nit: only one of the two can
be true, and only one is consistent with this ADR's own Consequences section
("Output Writer component must read... the target path before writing").

**This is now resolved, in favor of what this ADR's Consequences section already
said:** the ownership-marker check is performed **exclusively by the Output Writer**
(`writer.py`), **exclusively at write time**, immediately before writing/replacing
the target file — never by the Configuration Resolver, and never pre-scan. This is
because the check requires inspecting the *actual current contents* of whatever file
exists (or doesn't) at the target path, and that fact does not exist to inspect
until the Output Writer is about to act on it. `docs/architecture.md` Sections 4.2,
4.10, 11.2, 13, 16, 21, and 22 have been corrected to state this consistently; none
of them now claim the ownership guard runs pre-scan.

This further resolution also incorporates two related, smaller clarifications raised
alongside DR-003:

- **DR-001 relationship:** the FR-016 *boundary check* (a distinct mechanism from
  this ADR's ownership guard) is now specified as a concrete algorithm in
  `docs/architecture.md` Section 11.1 / ADR-0005, and *is* performed pre-scan, by the
  Configuration Resolver. The boundary check and the ownership guard are two
  different mechanisms, in two different components, at two different pipeline
  stages — conflating them was the root cause of the DR-003 contradiction.
- **DR-008 (directory creation):** the Output Writer is also the component
  responsible for creating `docs/generated/` and any needed sub-directories if they
  do not already exist, applying only to a path that has already passed the Section
  11.1 boundary check. This happens immediately before the ownership-marker check
  described above (`docs/architecture.md` Section 11.3).

No option previously considered in this ADR is re-opened by this note; this is a
pipeline-sequencing correction, not a reversal of the guarded-override decision.
