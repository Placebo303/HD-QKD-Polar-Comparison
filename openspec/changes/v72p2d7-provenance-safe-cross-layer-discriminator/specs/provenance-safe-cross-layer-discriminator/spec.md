## ADDED Requirements

### Requirement: D7-E frozen question and single-pass boundary

D7-E SHALL test only whether one provenance-valid single-pass source-layer
BP belief improves target-layer exact recovery over the target marginal
control, in either direction, without oracle truth or feedback. It SHALL NOT
claim calibrated posterior, alternating convergence, leakage, protocol
recovery or Bob-only FER.

#### Scenario: Single-pass mechanism

- **WHEN** a source marginal decode returns `CHECK_UPDATED`
- **THEN** at most one cold target decode consumes
  `softmax(current log belief)` combined with the accepted joint Model-F
  conditional — never an alternating iteration, feedback loop, or joint
  factor graph.

### Requirement: D7-E frozen matrix and decoder contract

D7-E SHALL decode f in `[1.0, 1.2]`; seeds `2026091300..2026091315`
ascending (16/f); the same blocks/graph seeds/rows/mothers/estimator as
accepted D7-C/D7-D; row-layered only GF(32) poly 37 cold `max_iter=90`
damping `1.0`; directions `[L1_TO_L2, L2_TO_L1]`; no flooding; no oracle
decoder calls. Per `(f,seed)` the slot order SHALL be exactly
`L1_TO_L2_SOURCE_L1_MARGINAL`, `L1_TO_L2_TARGET_L2_CONTROL_MARGINAL`,
`L1_TO_L2_TARGET_L2_TRANSFER` (only if source CHECK_UPDATED),
`L2_TO_L1_SOURCE_L2_MARGINAL`, `L2_TO_L1_TARGET_L1_CONTROL_MARGINAL`,
`L2_TO_L1_TARGET_L1_TRANSFER` (only if source CHECK_UPDATED). 192 slots =
128 mandatory + at most 64 eligible transfers; a blocked transfer slot is a
recorded non-invocation, never replacement/retry/fake.

#### Scenario: Exact slot order

- **WHEN** the frozen identities are enumerated
- **THEN** f runs `[1.0, 1.2]`, seeds ascend `2026091300..2026091315`,
  and each `(f,seed)` yields the six slots above in order.

#### Scenario: Blocked transfer is a non-invocation

- **WHEN** a source return is not `CHECK_UPDATED`
- **THEN** the paired transfer slot records blocked with no decoder call,
  no replacement prior, no retry, and no fabricated result.

### Requirement: D7-E transfer formulas and estimator identity

D7-E SHALL compute `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`
(L1 to L2) and `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`
(L2 to L1), where `q` is the transient normalized source belief from a
`CHECK_UPDATED` return. The joint SHALL come only from
`prepare_model_f_prior_candidate` / `build_f_model_concentration` with
per-Bob-column smoothing `(counts[:,b] + lambda*p_global)/(n_b[b] +
lambda)`; the legacy per-cell `build_f_model(counts + lambda)` SHALL NOT
be referenced. Floor/renorm SHALL follow the accepted D5 helper contract;
source q SHALL be transient and never persisted; no source truth SHALL
enter either formula.

#### Scenario: Estimator identity

- **WHEN** the joint is built
- **THEN** it equals the per-column concentration rule above, and a tiny
  asymmetric fixture distinguishes it numerically from the legacy
  per-cell rule, which static and behavioral tests forbid.

### Requirement: D7-E pair and eligibility semantics

For each direction the target control and transfer SHALL share
f/seed/block/target H/syndrome/decoder configuration with only the target
prior differing. Source exactness SHALL NOT gate eligibility. Eligibility
SHALL require source status finite/non-crash, belief shape valid and
provenance exactly `CHECK_UPDATED`. Per `(f,direction)` stratum fewer than
12/16 eligible slots SHALL yield `PROVENANCE_COVERAGE_BLOCKED` with no
substitution.

#### Scenario: Source exact false stays eligible

- **WHEN** a source decode is inexact but finite/non-crash with valid
  shape and `CHECK_UPDATED`
- **THEN** the paired transfer is eligible.

#### Scenario: Refused provenance blocks before mixing

- **WHEN** the source token is `PRIOR_ONLY`, missing/`None`, unknown or
  `WARM_START_UNSPECIFIED`
- **THEN** no `q` is constructed, no mixer runs, and no target transfer
  decode is dispatched.

### Requirement: D7-E stratum labels

On eligible control/transfer pairs D7-E SHALL assign the first matching
label: `STRONG_TRANSFER_LIFT` (eligible >=12, transfer-only >=4,
control-only <=1, transfer exact >=4, zero crash/nonfinite);
`TRANSFER_REGRESSION` (eligible >=12, control-only >=4, transfer-only
<=1); `NO_TRANSFER_RECOVERY` (eligible >=12, transfer exact <=1 and
control exact <=1); `CONTROL_ALREADY_RECOVERS` (eligible >=12 and control
exact >=12); `AMBIGUOUS_TRANSFER_EFFECT` (every other complete finite
eligible case); empty label when eligible <12 with the coverage status
carrying the reason.

#### Scenario: First-match routing

- **WHEN** a stratum satisfies an earlier rule
- **THEN** it is not relabeled by a later rule.

### Requirement: D7-E run terminal priority

D7-E SHALL report the first applicable terminal:
`D7_E_PRE_EXECUTION_BLOCKED`, `D7_E_WATCHDOG_TIMEOUT_VOID`,
`D7_E_NONFINITE_OR_CRASH_BLOCKED`, `D7_E_RESOURCE_OVERRUN`,
`D7_E_INCOMPLETE_CORE_CALL_MATRIX`, `D7_E_PROVENANCE_COVERAGE_BLOCKED`,
`D7_E_BIDIRECTIONAL_TRANSFER_LIFT` (same f strong both directions),
`D7_E_L1_TO_L2_TRANSFER_LIFT`, `D7_E_L2_TO_L1_TRANSFER_LIFT`,
`D7_E_TRANSFER_REGRESSION` (any regression, no strong lift),
`D7_E_NO_USEFUL_TRANSFER_RECOVERY` (all four strata no recovery),
`D7_E_MIXED_TRANSFER_DIAGNOSTIC`. All four strata and blocked-slot counts
SHALL persist under higher-priority terminal.

#### Scenario: Strata persist under higher terminal

- **WHEN** a higher-priority stop applies
- **THEN** all four stratum labels/counts and blocked counts are still
  recorded, never dropped.

### Requirement: D7-E budgets and root contract

D7-E SHALL cap at 192 decoder calls with no concurrency/retry/rerun/
resume; per-call watchdog 120 s; stored scientific wall <=1500 s; outer
GNU timeout `1800` plus `-k 30`; WSL stdlib `resource` RSS finite positive
and `<2GiB` before the first call and recorded maximum; target a fresh
direct child `workspace/d7_e_cross_layer_discriminator_<uuid>/` with no
overwrite/subdirs and exactly seven scalar text files (`manifest.json`,
`decoder_records.csv`, `transfer_pairs.csv`, `stratum_summary.csv`,
`summary.json`, `report.md`, `command_log.txt`); no
beliefs/priors/symbols/syndromes/vectors/digests persisted.

#### Scenario: Budget and schema pins

- **WHEN** the runner or its outputs are inspected
- **THEN** call counts, walls, RSS bound, fresh-root/no-overwrite, the
  seven-file list, and scalar-only persistence all hold.

### Requirement: D7-E RSS source is VmHWM-only on Linux/WSL (A2 telemetry delta)

On Linux/WSL, D7-E SHALL read current-process peak RSS from
`/proc/self/status`, field `VmHWM` with unit exactly `kB`, converting with
`bytes = value * 1024`. `VmHWM` SHALL be authoritative: no comparison
against and no fallback to `ru_maxrss` when `/proc/self/status` is present.
Missing file/field, duplicate field, malformed/non-integer/non-positive
value, wrong unit, read error, or overflow SHALL return `None` and block
before scientific execution or at the first affected call under the existing
resource terminal. D7-E SHALL NOT silently substitute `VmRSS`,
`/proc/<pid>/statm`, psutil, shell commands, or another process. The limit
SHALL remain strict `< 2 GiB` (equality or greater blocked); the stored
scalar key SHALL remain `rss_bytes`. `resource.ru_maxrss` MAY remain only
for non-Linux legacy code if already necessary, but the frozen WSL path
SHALL NOT call it. A single fresh E09 probe after implementation is
evidence; repeating probes until one passes is forbidden.

#### Scenario: Strict VmHWM parsing

- **WHEN** the status text holds exactly one ASCII
  `VmHWM: <positive integer> kB` line with a digit string of at most 18 digits
- **THEN** the probe yields `value * 1024` bytes.
- **WHEN** the field is missing, duplicated, malformed, decimal, signed,
  zero, negative, wrong-unit, non-ASCII-confusable, longer than 18 digits,
  or the file is unreadable
- **THEN** the probe yields `None` and the run blocks under the existing
  resource terminal.

#### Scenario: No ru_maxrss on the WSL path

- **WHEN** `/proc/self/status` is present on Linux/WSL, even with a
  conflicting bogus `ru_maxrss`
- **THEN** the WSL result equals the `VmHWM` parse and `_read_ru_maxrss`
  is not called.
