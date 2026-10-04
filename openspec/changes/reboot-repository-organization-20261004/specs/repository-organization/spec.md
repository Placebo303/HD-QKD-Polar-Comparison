## ADDED Requirements

### Requirement: Current archival lifecycle
Every archived change SHALL have an additive archive.md naming one evidenced disposition: completed (implemented, executed and reviewed, limited to that scope), superseded-before-execution (never granted and never executed, no delta merge), executed-exploration-closed (executed EXPLORE, no delta merge), or retired-history-no-delta (currently not advanced historical work with a stated individual reason, no delta merge). Originals SHALL remain verbatim via git mv; known facts and missing records SHALL remain distinct. Archive placement SHALL confer no scientific acceptance or execution grant. Clauses from the three no-delta dispositions require explicit adoption by a successor before becoming current.

#### Scenario: An older archive specification permits only two dispositions
- **WHEN** its two-disposition restriction conflicts with this explicitly approved extension
- **THEN** this four-disposition lifecycle governs; the old restriction is preserved as history and SHALL NOT be restored to live specifications.

Retained-clause index from `amend-openspec-archive-superseded-before-execution`: disposition records, no-delta for superseded-before-execution, historical clauses not directly current, explicit successor adoption, and verbatim preservation are adopted here. The old exclusive two-disposition restriction is superseded. Current user R1–R9 and AGENTS scientific gates take precedence over obsolete historical workflow clauses; filing and specification consolidation authorize no new experiment.

### Requirement: Project agent preferences
Ponytail SHALL be disabled for this project. Delegated subagents SHALL use luna_worker unless an explicit user or applicable named-role requirement overrides it. This preference SHALL NOT alter scientific acceptance or execution authorization.

#### Scenario: Organization work is delegated
- **WHEN** a delegated subtask has no explicitly required different role
- **THEN** it uses luna_worker and does not activate Ponytail.

### Requirement: History-preserving organization
The organization SHALL preserve all tracked files, use `git mv` for relocations, leave historical document bodies unchanged, and record old/new paths in PATH_MAP. Protected baseline and output roots SHALL remain untouched.

#### Scenario: Historical file is relocated
- **WHEN** a history file moves
- **THEN** its body remains unchanged and its relocation is indexed.

### Requirement: Archived test discovery
Default pytest discovery SHALL exclude the root `archive/` directory. Explicitly requested archived tests remain historical tools, not scientific execution authority.

#### Scenario: Root legacy tests move under archive
- **WHEN** default discovery runs after the move
- **THEN** archive is excluded and focused collection/import smoke records its actual scope.

### Requirement: Evidence-preserving closeout
Each S step SHALL have one scoped commit after actual status/diff checks. Unknown evidence status SHALL remain unknown; no archive action SHALL grant execution or scientific acceptance. Untracked clutter SHALL be isolated and listed without deletion.

#### Scenario: Disposition is unsupported by evidence
- **WHEN** available documents do not establish an applicable archive disposition
- **THEN** the ambiguity is recorded for a scoped decision before that archive action.

### Requirement: Executed exploration closure
An executed EXPLORE change retired from the current route MAY be archived as `executed-exploration-closed`. Its archive record SHALL state the execution and review status, the original evidence ceiling, any retained failure or incomplete stage, and all original files preserved verbatim. The archive SHALL merge no delta into live specifications and SHALL confer no scientific acceptance or execution grant. This disposition SHALL NOT reclassify DECIDE work as EXPLORE.

#### Scenario: A retired exploratory probe contains experiment-specific SHALLs
- **WHEN** the executed EXPLORE probe is closed and its evidenced disposition is recorded
- **THEN** its directory moves with `git mv`, an additive `archive.md` names `executed-exploration-closed`, and no probe delta is merged.

#### Scenario: An archived exploratory clause is cited as current
- **WHEN** a successor relies on a clause of an `executed-exploration-closed` archive
- **THEN** the successor SHALL explicitly adopt that clause in its own authority; direct historical citation does not make it live.

### Requirement: Historical work not currently advanced
A historical change whose available records do not establish another approved disposition MAY be archived as `retired-history-no-delta` under `<date>-<name>-history-no-delta`. This means the work is not currently advanced, not permanently rejected or scientifically killed. Its additive archive.md SHALL state this temporary prioritization, a change-specific reason supported by source records, known lifecycle facts and unresolved steps separately, and all original files preserved verbatim using git mv. Unknown review or authorization status SHALL remain unknown. No delta SHALL merge into live specifications; no retrospective acceptance or execution grant SHALL result. Current planning inputs remain current and exogenous changes remain excluded.

#### Scenario: Historical formal execution lacks an established reviewed scope
- **WHEN** the available records show execution but do not establish the independently reviewed scope required by completed
- **THEN** the archive states currently not advanced and its evidence-record gap, preserves the originals and outputs, and merges no delta.

#### Scenario: The historical work is reconsidered later
- **WHEN** a later scientific task proposes to advance the archived work
- **THEN** its successor explicitly adopts any retained clause and establishes its own applicable scientific evidence, review and user authorization; archival placement neither forbids reconsideration nor supplies those gates.

### Requirement: Closed probe source relocation and shared plumbing
The S7 frozen manifest SHALL govern mechanical relocation of closed CLI and corresponding test files with git mv. Current callers and directory anchors SHALL resolve the new paths without changing algorithms, defaults, units, data roles, schemas or scientific gates. Every move SHALL be immediately followed by a successful bounded .venv pytest smoke using cache disabled and a fresh task/UUID temporary directory; failure SHALL stop subsequent moves until its scoped cause is repaired. Historical scientific test bodies SHALL not execute during organization; collection/import smoke establishes only that limited engineering scope.

#### Scenario: A closed CLI or test moves
- **WHEN** one frozen CLI/test is moved
- **THEN** its module/file path is recorded in PATH_MAP and its lane-specific import or collection smoke is logged before the next move.

#### Scenario: Census callers share repeated plumbing
- **WHEN** common root validation, JSON/log and RSS/wall mechanics are extracted
- **THEN** a small stdlib helper is used by both census callers, preserving their converter, formatting, missing-RSS, clamping and threshold differences; fake-only checks cover these mechanics without decoder, DE, real data or historical result execution.
