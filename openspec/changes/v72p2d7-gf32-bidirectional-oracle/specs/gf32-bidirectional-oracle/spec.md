## ADDED Requirements

### Requirement: Four single-layer conditions and diagnostic boundary
The D7-C harness SHALL decode exactly four single-layer conditions per block and f — `L1_MARGINAL` (`P(U1|B)`), `L1_ORACLE_U2` (`P(U1|B,U2_true)`), `L2_MARGINAL` (`P(U2|B)`), `L2_ORACLE_U1` (`P(U2|B,U1_true)`) — each as one cold single-layer decode. Oracle conditions SHALL be counterfactual diagnostics only, SHALL NOT be described as protocol recovery, SHALL NOT count oracle truth as disclosure, and SHALL support no FER, leakage or key-rate claim.

#### Scenario: Condition set is closed
- **WHEN** the run matrix is built
- **THEN** exactly these four condition tokens are dispatched, each exactly once per (f, seed)
- **AND** no additional condition, layer or oracle mode is introduced.

#### Scenario: Oracle truth stays diagnostic
- **WHEN** an oracle condition prior is constructed from the true other-layer symbol
- **THEN** the truth value is used only to select the prior slice
- **AND** it is never persisted, never enters a marginal condition and never feeds another layer.

### Requirement: Frozen input identity and accepted estimator
The harness SHALL use only the accepted Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`, `n=64`, and block seeds `2026091300..2026091315`, sampled once per seed and reused across both f values and all four conditions. The prior estimator SHALL be the unique accepted post-R2 concentration/backoff estimator `v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate` (calling `build_f_model_concentration`) with `LAMBDA_STAR = 137.3823795883264` (total concentration per Bob column); `prepare_model_f_prior`/`build_f_model` (per-cell pseudocount, `LAMBDA_APPLICATION_CONTRACT_DEFECT`) SHALL never be called. No CAL/VAL/parquet/raw rows SHALL be read.

#### Scenario: Model-F root is fixed
- **WHEN** the runner receives any `--model-f-root` other than the accepted root
- **THEN** it refuses before any decoder bind, Model-F read or root creation.

#### Scenario: Rejected estimator is absent
- **WHEN** source or a run trace is inspected
- **THEN** `build_f_model` / `prepare_model_f_prior` appear nowhere in the D7-C call path.

### Requirement: Frozen mother geometry and disclosures
The n=64 mothers SHALL be built in memory exactly as `build_dv3_nested_support(64, 64, k_min, seed)` plus `assign_gf32_coefficients(sup, seed, None, 64)`, with L1 `k_min=49`, seed `2026090501`, and L2 `k_min=43`, seed `2026090502` (equivalently `build_dv3_nested_mother(64, 64, k_min, seed, None)`). Disclosures SHALL be `{f=1.0: L1 49, L2 43; f=1.2: L1 59, L2 52}` as row prefixes. VOID G1 matrices/results and any other VOID root SHALL never be read.

#### Scenario: Mother identity matches the frozen D6-native construction
- **WHEN** the mother call expressions are re-derived from source
- **THEN** they equal the D6-frozen `B0_D5_DV3_NATIVE` construction with D5 graph seeds
- **AND** the D5 formal G1 geometry `(64,59,59)`/`(64,52,52)` is not used.

#### Scenario: Disclosure uses prefixes only
- **WHEN** a call is dispatched at f
- **THEN** the decoder receives `H1[:rows]` or `H2[:rows]` for the frozen row count and no other rows.

### Requirement: Frozen prior formulas and single boundary floor
The four priors SHALL be computed directly from `J[u1,u2,b] = P_F(32*u1+u2|b)` as: `L1_MARGINAL = sum_u2 J[:,u2,b]`; `L1_ORACLE_U2 = J[:,u2_true,b]` normalized over u1; `L2_MARGINAL = sum_u1 J[u1,:,b]`; `L2_ORACLE_U1 = J[u1_true,:,b]` normalized over u2. A zero-mass oracle slice SHALL fall back to uniform `1/32`. The prior SHALL be transposed to the decoder `(position, q)` shape only at the decoder boundary, and `DECODER_FLOOR = 1e-15` floor/renormalization SHALL be applied exactly once there.

#### Scenario: Literal tensor recomputation
- **WHEN** each formula is recomputed by an independent literal joint-tensor calculation on a small fixture
- **THEN** all four results match
- **AND** swapped U1/U2/B axis negative controls fail.

#### Scenario: Prior boundary is applied once
- **WHEN** any of the four priors is dispatched
- **THEN** it is positive and normalized over q after one floor application
- **AND** no second D7-C-side floor, clip or renormalization occurs.

### Requirement: Frozen call matrix and order
Normal completion SHALL perform exactly 128 scientific calls in the order `for f in [1.0, 1.2]: for seed in 2026091300..2026091315: L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1`, with every call attempted exactly once unless a higher-priority run stop occurs, no early-success stop and no replacement cell. The marginal/oracle pair SHALL share H prefix, syndrome target, block and decoder configuration.

#### Scenario: Identity freeze precedes the first call
- **WHEN** the runner starts decoding
- **THEN** the accepted Model-F has loaded and all 128 identities are frozen in memory
- **AND** each identity is `(f, seed, condition, layer, rows, n=64)`.

#### Scenario: No substitution
- **WHEN** a call fails or returns an unexpected outcome
- **THEN** no replacement call, rerun, resume or retry is performed.

### Requirement: Budgets and resource guards
The run SHALL enforce `<= 128` scientific calls (exactly 128 on normal completion), a 120 s per-call watchdog, stored scientific wall `<= 1500 s`, an outer `timeout -k 30 1800`, and current-process RSS `< 2 GiB` measured via stdlib `resource.getrusage(RUSAGE_SELF).ru_maxrss` with explicit Linux KiB→bytes conversion. A missing, nonpositive or nonfinite RSS measurement SHALL block before the first scientific call. `psutil` SHALL NOT be used. Zero retry/rerun/resume.

#### Scenario: RSS preflight
- **WHEN** the RSS probe is unavailable, nonpositive or nonfinite
- **THEN** the run stops as `D7_C_PRE_EXECUTION_BLOCKED` with zero scientific calls.

#### Scenario: Watchdog fires
- **WHEN** a single call exceeds 120 s
- **THEN** the run stops as `D7_C_WATCHDOG_TIMEOUT_VOID` and no further call is attempted.

### Requirement: Scalar evidence schema and six-file root
The writer SHALL create exactly six compact scalar files in a fresh
`workspace/d7_c_bidirectional_oracle_<uuid>/` root with no subdirectories:
`manifest.json`, `decoder_records.csv`, `paired_summary.csv`, `summary.json`,
`report.md`, `command_log.txt`. Per-call records SHALL contain the frozen
scalar fields of the prereg §9; per-`(f,layer)` paired rows SHALL contain the
frozen marginal/oracle counts, paired syndrome, nonfinite/crash and
median/max iteration/wall fields. No raw beliefs, symbols, priors, syndromes or
block vectors SHALL be persisted.

#### Scenario: Root is fresh and closed
- **WHEN** the target exists, is outside `workspace/`, does not match the frozen name pattern or contains a subdirectory
- **THEN** the writer refuses before any call or overwrite.

#### Scenario: Exact and syndrome stay isolated
- **WHEN** a call returns `syndrome_ok` without exact recovery
- **THEN** the record keeps `exact=false` and the event is never counted as recovery or merged into an exact rate.

### Requirement: Frozen stratum classification and run terminals
Each `(f, layer)` stratum SHALL be classified by the frozen thresholds
(`STRONG_ORACLE_LIFT`, `NO_ORACLE_RECOVERY`, `MARGINAL_ALREADY_RECOVERS`,
`AMBIGUOUS_ORACLE_EFFECT`) and the run SHALL select exactly one terminal from
the 11-entry priority list `D7_C_PRE_EXECUTION_BLOCKED`,
`D7_C_WATCHDOG_TIMEOUT_VOID`, `D7_C_NONFINITE_OR_CRASH_BLOCKED`,
`D7_C_RESOURCE_OVERRUN`, `D7_C_INCOMPLETE_CALL_MATRIX`,
`D7_C_BIDIRECTIONAL_DEPENDENCE`, `D7_C_L1_DEPENDS_ON_U2`,
`D7_C_L2_DEPENDS_ON_U1`, `D7_C_MARGINAL_REGION_EXISTS`,
`D7_C_ORACLE_NO_USEFUL_RECOVERY`, `D7_C_MIXED_DIAGNOSTIC`. All stratum labels
SHALL be recorded even when a higher-priority run terminal applies. An
incomplete stratum SHALL record partial counts with an empty label, never a
fabricated one.

#### Scenario: Terminal priority is exact
- **WHEN** several terminal conditions are simultaneously true
- **THEN** the first applicable terminal in the frozen order is selected.

#### Scenario: Labels survive a higher terminal
- **WHEN** a resource or watchdog stop occurs after some strata completed
- **THEN** completed strata still carry their frozen labels and incomplete strata carry empty labels.

### Requirement: Current-belief provenance labeling (A1)
Iteration-0 and current-belief diagnostics SHALL be labeled only
`PRIOR_ONLY_CURRENT_BELIEF` when `iterations == 0` and
`CHECK_UPDATED_CURRENT_BELIEF` when `iterations > 0`; they SHALL never be
labeled posterior or APP. `beliefs_conditioned` SHALL be derived from
`iterations` and the reviewed audit semantics. No decoder-returned belief SHALL
flow to another layer or be used as a prior.

#### Scenario: Iteration-0 diagnostic
- **WHEN** a call returns with zero completed check sweeps
- **THEN** its current-belief fields are labeled `PRIOR_ONLY_CURRENT_BELIEF`
- **AND** no conditioned-posterior tolerance or APP language is applied.

#### Scenario: No cross-layer belief flow
- **WHEN** the source or run trace is inspected
- **THEN** no `final_beliefs -> other layer` path exists.

### Requirement: Implementation isolation and authorization gating
Import, `--help`, `--dry-run` and unauthorized runs SHALL bind no decoder, read
no Model-F and create no root. The implementation SHALL use lazy local-source
package import (works from the WSL repo and an external cwd), dependency
injection for joint tensor, blocks, matrices, decoder, clock and RSS, and a
single sequential loop with no retry/resume/concurrency framework. The runner
SHALL read the D7-C `cycle_state.yaml` and refuse while
`d7c_execution_authorized` is false; authorization SHALL be consumed on the
first decoder attempt. The implementation SHALL NOT import or depend on the
future layer-interface rework.

#### Scenario: Unauthorized refusal
- **WHEN** the key is false
- **THEN** the runner refuses before any Model-F read, decoder bind or root creation.

#### Scenario: External-cwd bind
- **WHEN** the module/runner is imported from outside the repository with a fake decoder sentinel
- **THEN** the local-source package bind reaches the first decoder call with zero real Model-F read and zero root creation.

### Requirement: Verify mode independence
Verify mode SHALL recompute schema, 128-identity uniqueness, pair matching,
counts/outcomes, stratum labels and run terminal from the six files alone. It
SHALL never call the decoder and never load Model-F.

#### Scenario: Tampered records are detected
- **WHEN** a record is duplicated, deleted, unpaired or its scalar values are altered
- **THEN** verify fails with the affected identity or field.

#### Scenario: Verifier isolation
- **WHEN** verify mode runs
- **THEN** no decoder binding and no Model-F read occur.
