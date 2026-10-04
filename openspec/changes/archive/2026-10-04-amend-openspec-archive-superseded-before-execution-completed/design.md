# Amend OpenSpec Archive: Superseded-Before-Execution — Design

Sources: `AGENTS.md` §3/§6/§10.3; precedent
`openspec/changes/archive/2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded/archive.md`;
the four `openspec/changes/archive/2026-09-21-v80-*-superseded/` dirs; house style from
`openspec/changes/v80-prior-cost-accounting/` (`proposal.md` / `design.md` / `tasks.md` /
`specs/<change-name>/spec.md` with `## ADDED Requirements` + `#### Scenario:` blocks).

Condensation + governance promotion only; no new numbers, no code, no execution.

## 1. The two archive dispositions (exhaustive)

1. **completed** — the change was implemented, executed and reviewed. Archive merges its
   delta specs into `openspec/specs/` (the existing documented `/opsx-archive` behavior).
   The `archive.md` disposition record states this disposition and the merge that was performed.
2. **superseded-before-execution** — the change was frozen (or drafted) but never granted
   and never executed. Archive moves it to `openspec/changes/archive/` with a disposition
   record and **does NOT merge** its spec delta into `openspec/specs/`. Its frozen clauses
   retain force only through an explicit retained-clause index in the successor authority,
   never by direct citation of the archived files.

There is no third disposition. A change that was partially executed is NOT disposition 2;
its disposition record states exactly what ran and what did not, and any merge is limited
to the executed scope.

## 2. Naming convention

- Disposition 1 keeps the existing convention (`<name>` archived in place / per `/opsx-archive`).
- Disposition 2 uses `<date>-<name>-superseded` (e.g. `2026-09-21-v80-p3-real-hfull-census-superseded`,
   `2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded`), so the never-executed status
   is visible in the directory name itself.

## 3. The `archive.md` disposition record (required for both dispositions)

Every archived change carries `archive.md` at the archive root stating:

- archived date;
- which disposition applies (exactly one of the two above);
- for disposition 1: what was merged into `openspec/specs/`;
- for disposition 2: that NOTHING was merged; the grant/execution status
  (`NEVER_GRANTED / NEVER_EXECUTED`, or the partial-execution carve-out if applicable);
  the reason for supersession; and the list of original files retained verbatim;
- the standard non-implication sentence: archiving does not imply the former route passed
  any review, was implemented, produced evidence, or is impossible in general (per precedent).

## 4. Non-citability + retained-clause index

- The frozen SHALLs of a disposition-2 archive are NOT current authority and SHALL NOT be
  cited as live specification. They are history/provenance only.
- If any clause of a superseded change is to survive, the SUCCESSOR authority carries an
  explicit retained-clause index naming each surviving clause (source file + requirement);
  survival happens only through that index, never by direct citation of the archived files.
  (This mirrors the `v80-prior-cost-accounting` pattern: it did not retire the four V80
  SHALL sets and added its own contract for future packets to cite instead.)

## 5. Preservation

Archiving moves; it never rewrites. All original files (`proposal.md`, `design.md`,
`tasks.md`, `specs/*/spec.md`, plus any prompts/preregs in scope) are preserved verbatim
in the archive directory. SUPERSEDE banners on cover files alone are insufficient while
effective SHALLs remain unmarked — the disposition record, not the banner, is authoritative.

## Auth boundary

- Freeze consumes nothing; authorizes nothing. This change is planning/docs only.
