## ADDED Requirements

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
