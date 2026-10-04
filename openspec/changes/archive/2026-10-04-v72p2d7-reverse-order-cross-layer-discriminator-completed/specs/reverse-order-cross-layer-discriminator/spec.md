## ADDED Requirements

### Requirement: D7-F frozen question and paired-order boundary

D7-F SHALL test only whether reverse order `L2→L1` recovers both layers
exactly on more seeds than forward order `L1→L2`, when each arm is a
complete two-pass sequence (source marginal, then one gated cold target
decode from the transfer prior), without oracle truth or feedback. It
SHALL NOT claim calibrated posterior, alternating convergence, leakage,
protocol recovery or Bob-only FER.

#### Scenario: Paired order mechanism

- **WHEN** a source marginal decode returns `CHECK_UPDATED`
- **THEN** at most one cold target decode consumes the transient transfer
  prior combined with the accepted joint Model-F conditional — never an
  alternating iteration, feedback loop, third stage, or joint factor
  graph.

### Requirement: D7-F frozen matrix and decoder contract

D7-F SHALL decode f in `[1.0, 1.2]`; seeds `2026091300..2026091315`
ascending (16/f); the same corrected per-Bob-column estimator, accepted
Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`, D7-C/D7-E
block identity, H/mother prefixes, rows, GF32 poly 37, cold row-layered
`max_iter=90` damping `1.0`; no oracle/flooding/CAL/VAL/real/raw/graph
changes. Per `(f,seed)` the arm order SHALL be exactly
`FORWARD_L1_TO_L2` (L1 marginal; gate → transient P(U2|B,s1) → cold L2)
then `REVERSE_L2_TO_L1` (L2 marginal; gate → transient P(U1|B,s2) →
cold L1). Maximum `32×4=128` calls (64 mandatory source marginals + up
to 64 gated transfers); a blocked second stage is a recorded
non-invocation, never replacement/retry/fake.

#### Scenario: Exact arm order

- **WHEN** the frozen identities are enumerated
- **THEN** f runs `[1.0, 1.2]`, seeds ascend `2026091300..2026091315`,
  and each `(f,seed)` yields `FORWARD_L1_TO_L2` then `REVERSE_L2_TO_L1`.

#### Scenario: Blocked second stage is a non-invocation

- **WHEN** a source return is not finite/non-crash/shape-valid with
  provenance exactly `CHECK_UPDATED`
- **THEN** the paired second stage records blocked with no decoder call,
  no replacement prior, no retry, and no fabricated result, and nothing
  transfers back to the source layer.

### Requirement: D7-F transfer formulas and estimator identity

D7-F SHALL compute `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`
(forward) and `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`
(reverse), where `q` is the transient normalized source belief from a
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

### Requirement: D7-F arm gate and source-exact exclusion

Eligibility SHALL require source status finite/non-crash, belief shape
valid and provenance exactly `CHECK_UPDATED`. Source exact SHALL NOT gate
eligibility.

#### Scenario: Source exact false stays eligible

- **WHEN** a source decode is inexact but finite/non-crash with valid
  shape and `CHECK_UPDATED`
- **THEN** the paired second stage is eligible.

#### Scenario: Refused provenance blocks before mixing

- **WHEN** the source token is `PRIOR_ONLY`, missing/`None`, unknown or
  `WARM_START_UNSPECIFIED`
- **THEN** no `q` is constructed, no mixer runs, and no target transfer
  decode is dispatched.

### Requirement: D7-F per-arm outcome accounting

For each arm D7-F SHALL persist scalar-only: first/second stage
eligibility and provenance; L1 exact/syndrome and L2 exact/syndrome
separately; `both_layers_exact = L1_exact AND L2_exact` only; calls,
blocked, crash/nonfinite, iterations/work, wall, RSS. Syndrome success
SHALL NEVER be merged into exact success.

#### Scenario: Both-layer exact truth table

- **WHEN** either layer is inexact
- **THEN** `both_layers_exact` is false regardless of syndrome fields.

### Requirement: D7-F evidence-use contract

Each target SHALL start cold from the transfer prior and consume its own
syndrome once. No target posterior SHALL be fed back, blended,
multiplied, or reused. Tests SHALL prove the first-stage syndrome is
consumed only by its source decoder and the second-stage syndrome only
by its target decoder. >2-stage alternating SHALL stay blocked pending a
cavity/extrinsic-message contract; D7-F SHALL document that no such
contract is encoded here.

#### Scenario: No syndrome return

- **WHEN** any target posterior exists
- **THEN** it feeds no further decoder input in this run.

### Requirement: D7-F paired labels

Across the same 16 seeds per f, D7-F SHALL compare reverse candidate C
with forward reference R (`candidate_only`: C both-exact and R not;
`reference_only`: R both-exact and C not; `both`; `neither`) and assign
the first matching label: `COVERAGE_BLOCKED` (either arm fewer than
12/16 complete eligible paired outcomes); `REVERSE_REGRESSION`
(`reference_only >= 2` and `candidate_only == 0`);
`STRONG_REVERSE_LIFT` (`candidate_only >= 4` and `reference_only == 0`);
`WEAK_REVERSE_LIFT` (`candidate_only > reference_only` but strong not
met); `NO_REVERSE_LIFT` otherwise. These are synthetic diagnostic
labels, not FER thresholds.

#### Scenario: First-match routing

- **WHEN** a stratum satisfies an earlier rule
- **THEN** it is not relabeled by a later rule.

### Requirement: D7-F run terminal priority

D7-F SHALL report the first applicable terminal:
`D7_F_PRE_EXECUTION_BLOCKED`, `D7_F_WATCHDOG_TIMEOUT_VOID`,
`D7_F_NONFINITE_OR_CRASH_BLOCKED`, `D7_F_RESOURCE_OVERRUN`,
`D7_F_INCOMPLETE_MATRIX_BLOCKED`, `D7_F_PROVENANCE_COVERAGE_BLOCKED`,
`D7_F_REVERSE_ORDER_STRONG_LIFT` (either f strong and the other does not
regress), `D7_F_REVERSE_ORDER_WEAK_LIFT` (either f weak and neither
regresses), `D7_F_REVERSE_ORDER_REGRESSION`,
`D7_F_NO_USEFUL_REVERSE_ORDER_LIFT`. No automatic successor SHALL be
encoded. All paired outcomes and blocked counts SHALL persist under a
higher-priority terminal.

#### Scenario: Outcomes persist under higher terminal

- **WHEN** a higher-priority stop applies
- **THEN** all paired outcome counts and blocked counts are still
  recorded, never dropped.

### Requirement: D7-F budgets, root contract, and frozen command

D7-F SHALL cap at 128 decoder calls with no concurrency/retry/rerun/
resume; per-call watchdog 120 s; stored scientific wall <=1500 s; outer
GNU timeout `1800` plus `-k 30`; `.venv/bin/python` only; on Linux/WSL
current-process peak RSS from `/proc/self/status` field `VmHWM` (unit
exactly `kB`, `bytes = value * 1024`), strict `< 2 GiB`, fail-closed
(missing/unparseable blocks before the first scientific call and at the
first affected call mid-run); sequential execution; one fresh identifier;
target a fresh direct child
`workspace/d7_f_reverse_order_discriminator_<uuid>/` with no
overwrite/subdirs and exactly seven scalar text files (`manifest.json`,
`decoder_records.csv`, `arm_pairs.csv`, `stratum_summary.csv`,
`summary.json`, `report.md`, `command_log.txt`); no
beliefs/priors/symbols/syndromes/vectors/digests persisted. The exact
future command SHALL be:

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_reverse_order_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_f_reverse_order_discriminator_<uuid>
```

with status `NOT_AUTHORIZED` (frozen but unauthorized and not executed;
no identifier generated here). An independent read-only verifier SHALL
recompute from record scalars only, never loading Model-F or binding/
calling a decoder.

#### Scenario: Budget and schema pins

- **WHEN** the runner or its outputs are inspected
- **THEN** call counts, walls, RSS bound, fresh-root/no-overwrite, the
  seven-file list, and scalar-only persistence all hold.

### Requirement: D7-F planned code paths and binding discipline

The implementer SHALL create exactly: module
`comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py`,
tests
`comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py`,
script `scripts/v72p2d7_gf32_reverse_order_discriminator.py`. D7-F SHALL
reuse D7-E loaders/estimator/transfer/provenance/RSS/scalar/verifier
conventions via narrow imports with no predecessor-module copies. Lazy
binding + DI SHALL be required: import/`--help`/`--dry-run`/
unauthorized/verifier/tests bind no real decoder, read no real Model-F,
and create no scientific root.
