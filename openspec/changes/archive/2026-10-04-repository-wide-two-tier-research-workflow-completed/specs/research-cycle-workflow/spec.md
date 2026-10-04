# Research-cycle two-tier workflow delta

> Supersession note: this delta supersedes the per-task review-frequency
> reading of `standardize-task-packet-review-loop` and
> `research-cycle-sop-single-user-simplification`. Their paired
> packet/prompt handoff surface and all safety-gate requirements remain
> in force.

## ADDED Requirements

### Requirement: Every packet declares exactly one track

Every task packet SHALL declare exactly one track, `EXPLORE` or
`DECIDE`, before execution. `EXPLORE_HEAVY` is a cost annotation on
`EXPLORE`, not a third lifecycle.

#### Scenario: Packet without a track

- **WHEN** a packet names no track or names both tracks
- **THEN** it SHALL NOT authorize execution until one track is declared

#### Scenario: Third track invented

- **WHEN** a packet proposes a track other than `EXPLORE` or `DECIDE`
- **THEN** the packet SHALL be revised to one of the two tracks, using
  `EXPLORE_HEAVY` only as a cost annotation where needed

### Requirement: Two-tier policy is the repository-wide default

The two-tier policy SHALL be the default for every future route, task,
packet, OpenSpec change, experiment, and result. Historical cycles
SHALL remain unchanged. Scope-by-name SHALL NOT reintroduce per-arm
paperwork that this policy removes.

#### Scenario: New route starts

- **WHEN** a new route (NB-LDPC, NB-Polar preparation, scan, security,
  or an unnamed future route) begins
- **THEN** its packets SHALL classify under this policy without a
  route-specific exemption document

#### Scenario: Old name reused to add ceremony

- **WHEN** an area proposes extra per-arm review files under a new
  cycle or method-family name
- **THEN** the proposal SHALL be rejected unless it adds a stricter
  scientific requirement rather than paperwork

### Requirement: Track eligibility follows concrete risk

`EXPLORE` SHALL require all five: (a) synthetic or already-approved
non-sensitive development input; (b) fresh additive `workspace/` root
or no-write probe; (c) bounded and reversible; (d) no
FER/SKR/qualification/promotion/publication claim; (e) no destructive
overwrite or new user-facing external action. `DECIDE` SHALL apply when
any one holds: frozen route/life-death gate; real/private/raw data;
expensive, formal, irreversible, or claim-bearing execution; or a
result intended for a report, publication, qualification, or promotion.
Real data, formal qualification, route-closing decisions, and
publication claims SHALL always be `DECIDE`.

#### Scenario: Synthetic diagnostic batch

- **WHEN** a bounded synthetic probe writes only to a fresh
  `workspace/` root and makes no claim
- **THEN** it SHALL classify as `EXPLORE`

#### Scenario: Real-data run labeled EXPLORE

- **WHEN** a task touches real/private/raw data or a route-closing
  gate
- **THEN** it SHALL be rejected as `EXPLORE` and re-filed as `DECIDE`

### Requirement: EXPLORE artifact contract

An exploratory batch SHALL consist of: one packet+prompt pair carrying
the preregistration and authorization boundary; one result root or
no-write transcript; and one append-only log carrying attempts, the
preregistered engineering correction, final evidence, and the batch-end
review. One authorization SHALL cover the frozen conditional arm
sequence. At most one preregistered repair+rerun SHALL be permitted,
with unchanged scientific inputs, seeds, thresholds, data roles, and
tested hypothesis, and the failed attempt retained in the same log. No
per-arm documentation set SHALL be required.

#### Scenario: Frozen conditional arms

- **WHEN** a batch preregisters arms X1–X3 with machine gates between
  them
- **THEN** the operator SHALL continue while each gate permits, under
  the single authorization, recording each arm in the one log

#### Scenario: Per-arm file demanded

- **WHEN** a reviewer asks for a separate authorization, return,
  failure-verification, repair-review, or rerun-review file per arm
- **THEN** the request SHALL be redirected into the single
  append-only log

### Requirement: DECIDE gate contract

`DECIDE` SHALL require: an accepted preregistration; a Pre-EXECUTE
review with exact command, budget, output absence, and explicit user
authorization; one execution/result record; an independent Pre-RESULT
review; and main-thread acceptance. The compact three-document option
(`PREREG_AND_AUTH.md`, `RESULT.md`, `INDEPENDENT_ACCEPTANCE.md`) plus
machine artifacts SHALL be permitted.

#### Scenario: Claim-bearing run without authorization

- **WHEN** a `DECIDE` run lacks explicit user authorization or its
  target output already exists
- **THEN** execution SHALL stop until the Pre-EXECUTE gate passes

#### Scenario: Result solidification without independent review

- **WHEN** a `DECIDE` result has no independent Pre-RESULT record
- **THEN** it SHALL NOT be published, committed as a result, or
  promoted

### Requirement: Escalation from EXPLORE to DECIDE

`EXPLORE` SHALL escalate to `DECIDE` before continuing on real data,
route-closing thresholds, publication claims, destructive output,
materially higher cost, or a change to scientific inputs/hypothesis.
Uncertainty SHALL default to `DECIDE` only when a concrete risk is
named.

#### Scenario: Exploratory probe reaches a route gate

- **WHEN** an `EXPLORE` batch produces a number intended as a
  route-closing or publication input
- **THEN** work SHALL stop and continue only under a `DECIDE` packet

#### Scenario: Decoder called on synthetic probe

- **WHEN** a bounded synthetic probe calls a decoder with no other
  `DECIDE` trigger
- **THEN** it SHALL remain `EXPLORE`

### Requirement: Review scoping follows the track

Pre-RESULT SHALL apply to `DECIDE` result publication. For `EXPLORE`,
one independent batch-end review SHALL replace per-arm review. A failed
engineering probe SHALL NOT count as an algorithm result. A failed
`DECIDE` gate SHALL remain immutable evidence.

#### Scenario: Seconds-scale probe fails then reruns

- **WHEN** an `EXPLORE` arm fails on an engineering cause and reruns
  under the preregistered repair clause
- **THEN** the failure and rerun SHALL live in the one log with a
  single batch-end review, not a per-arm review chain

#### Scenario: Failed DECIDE gate

- **WHEN** a `DECIDE` gate fails
- **THEN** the failure SHALL be retained as immutable evidence and
  SHALL NOT be overwritten by a rerun

### Requirement: Protected semantics are not weakened

Failure retention, no-overwrite, exact/syndrome/undetected separation,
reproducibility, real-data protection, and claim boundaries SHALL NOT
be weakened by track classification.

#### Scenario: Undetected outcomes in a report

- **WHEN** a result contains `undetected` outcomes
- **THEN** they SHALL remain isolated and SHALL NOT be merged into
  success/FER on either track

### Requirement: Commits stay scoped and provenance-only

Each exploratory batch or decision gate SHOULD produce one coherent
scoped milestone commit. Staging in dirty worktrees SHALL use an
explicit allowlist; `git add -A` SHALL NOT be used. Commit IDs SHALL be
provenance, not authorization locks.

#### Scenario: Dirty worktree commit

- **WHEN** unrelated changes are present
- **THEN** only the explicitly listed task files SHALL be staged

### Requirement: Machine terminal labels are scoped classifications

Machine terminal labels SHALL be scoped pre-registered classifications,
not immutable scientific facts, and citations SHALL carry their scope.

#### Scenario: D7-F label cited

- **WHEN** `D7_F_REVERSE_ORDER_REGRESSION` is cited
- **THEN** the citation SHALL carry its single-graph n=16 paired scope
  and SHALL NOT assert a general mechanism

### Requirement: Track classification is decidable from the matrix

Track classification SHALL be possible from the applicability matrix
alone — synthetic diagnostics; synthetic route gates; real-data
development; parameter scans; formal qualification;
publication/report numbers; security calculations;
implementation-only changes; documentation-only changes — without
inventing a third track.

#### Scenario: Arbitrary future task

- **WHEN** a reviewer classifies an unfamiliar task (scan, security,
  implementation-only, or documentation-only)
- **THEN** the matrix SHALL yield exactly one track or a named
  escalation to `DECIDE`
