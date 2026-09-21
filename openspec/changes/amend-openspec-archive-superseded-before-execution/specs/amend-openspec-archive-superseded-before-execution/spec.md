## ADDED Requirements

### Requirement: Every archived change carries a disposition record

Every change moved to `openspec/changes/archive/` SHALL carry an `archive.md` disposition
record at the archive root stating the archived date, exactly which of the two dispositions
(`completed` or `superseded-before-execution`) applies, and — for `completed` — what was
merged into `openspec/specs/`, or — for `superseded-before-execution` — that NOTHING was
merged, the grant/execution status, the reason for supersession, and the list of original
files retained verbatim.

#### Scenario: Archive without a disposition record

- **WHEN** a change is present under `openspec/changes/archive/` with no `archive.md`
  stating which disposition applies
- **THEN** it is refused as incompletely archived pending the disposition record.

#### Scenario: Archive with an ambiguous disposition

- **WHEN** `archive.md` names neither disposition exactly, or claims both
- **THEN** it is refused pending a single-disposition statement (partial execution states
  exactly what ran and what did not; any merge is limited to the executed scope).

### Requirement: Superseded-before-execution archives MUST NOT merge deltas

A change archived with disposition `superseded-before-execution` (frozen or drafted but
never granted and never executed) SHALL be moved to `openspec/changes/archive/` under the
`<date>-<name>-superseded` naming convention with its disposition record, and its spec
delta SHALL NOT be merged into `openspec/specs/`.

#### Scenario: Merge proposed for a never-executed change

- **WHEN** a merge into `openspec/specs/` is proposed for a change that was never granted
  and never executed
- **THEN** it is refused: the change archives as superseded-before-execution with no merge.

#### Scenario: SUPERSEDE banner cited as sufficient without a disposition record

- **WHEN** a SUPERSEDE banner on a cover file (e.g. `proposal.md` only) is cited as the
  archive action while effective SHALLs remain in `specs/*/spec.md` with no `archive.md`
- **THEN** it is refused pending the authoritative disposition record plus the `-superseded`
  archive placement.

### Requirement: Superseded frozen clauses are NOT citable as current

The frozen SHALLs of a disposition-2 (`superseded-before-execution`) archive are history /
provenance only. They SHALL NOT be cited as live specification, and no packet, result, or
successor change SHALL treat them as current authority by direct citation of the archived files.

#### Scenario: Packet cites an archived SHALL as live authority

- **WHEN** a packet or result cites a SHALL from a `-superseded` archive directory as if
  it were a live `openspec/specs/` requirement
- **THEN** it is refused pending citation of the live specification or of an explicit
  retained-clause index in the successor authority.

### Requirement: Survival only through a successor retained-clause index

If any clause of a superseded-before-execution change is to survive, the SUCCESSOR authority
SHALL carry an explicit retained-clause index naming each surviving clause (source file +
requirement). No clause survives by direct citation of the archived files.

#### Scenario: Surviving clause without an index entry

- **WHEN** a successor relies on a superseded clause that its own authority does not name
  in a retained-clause index
- **THEN** it is refused pending the index entry (source file + requirement quoted).

### Requirement: Archives preserve all original files verbatim

Archiving moves; it never rewrites. All original files (`proposal.md`, `design.md`,
`tasks.md`, `specs/*/spec.md`, plus any prompts/preregs in scope) SHALL be preserved
verbatim in the archive directory.

#### Scenario: Archive drops or rewrites an original file

- **WHEN** an archived change is missing one of its original files, or an original file's
  content was edited as part of the archive action rather than preserved
- **THEN** it is refused pending verbatim restoration (the disposition record is additive;
  it does not modify the originals).
