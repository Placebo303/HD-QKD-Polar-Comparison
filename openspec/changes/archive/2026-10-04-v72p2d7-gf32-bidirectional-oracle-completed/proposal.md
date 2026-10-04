# D7-C bidirectional cross-layer oracle — proposal (R1 + A1; freeze + implementation, no execution)

## What

Freeze and implement (without executing) a single-layer bidirectional oracle
diagnostic on the accepted n=64 GF32 operating point: for the same frozen
synthetic paired blocks, disclosures and historical row-layered decoder,
isolate whether either layer becomes recoverable only when given the other
layer's true symbol as a counterfactual diagnostic prior.

Four conditions per block and f:

1. `L1_MARGINAL`: `P(U1 | B)`
2. `L1_ORACLE_U2`: `P(U1 | B, U2_true)`
3. `L2_MARGINAL`: `P(U2 | B)`
4. `L2_ORACLE_U1`: `P(U2 | B, U1_true)`

Exact call matrix: 16 blocks × 2 f × 4 conditions = 128 single-layer decodes,
in a frozen order, each attempted once on normal completion. No D7-C
scientific execution in this task; stop at independent Pre-EXECUTE readiness.

## Why

D7-A (`D7_A_DECODER_CERTIFICATION_PASS`) certified the decoder; D7-B
hard-decision behavior was accepted only under the narrow scope
`HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`
with terminal `D7_B_RESOURCE_OVERRUN` (RSS telemetry unknown, not a measured
breach). The audited primary outcome `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`
established that a cold iteration-0 return is prior-only and must never be sold
as a syndrome-conditioned APP; the Phase-P correction proposal passed as
non-blocking for D7-C because D7-C builds all four priors directly from the
accepted joint model and never consumes cross-layer returned beliefs. The open
mainline question is where cross-layer dependence lies at this operating point.

## Scope

In scope: OpenSpec freeze, `D7_C_PREREG_R1.md`, `D7_C_EXECUTION_PACKET_R1.md`,
`cycle_state.yaml`, minimal module
(`v72p2d7_gf32_bidirectional_oracle.py`), focused tests
(`test_v72p2d7_gf32_bidirectional_oracle.py`), runner script
(`scripts/v72p2d7_gf32_bidirectional_oracle.py`), fake/unit qualification,
independent implementation review, independent Pre-EXECUTE review, scoped
local commits.

Out of scope: D7-C scientific execution, any real decoder call in this task,
R1d, G1/G2, CAL/VAL/parquet/raw/real/formal/VOID content reads, `--phase`,
production v35/D5/D6/D7-A/D7-B edits, the layer-interface rework
implementation, UUID generation, push.

## Decision question and claim ceiling

Question: at the accepted n=64 GF32 operating point, does either layer show a
strong oracle-only lift when handed the other layer's true symbols?

May establish: per-`(f, layer)` stratum classification from the frozen
thresholds; one run terminal from the frozen 11-entry priority; raw paired
counts and scalar decoder evidence.

May not establish: protocol recovery, FER, leakage, reconciliation efficiency,
key rate, disclosure accounting, CAL/real recoverability, cross-layer APP
viability, interface acceptance, R1d/G1/G2 readiness, qualification, promotion,
or any general GF32/NB-LDPC conclusion. The oracle conditions are
counterfactual diagnostics only, are not protocol recovery, and do not count
oracle truth as disclosure.

## Frozen scientific contract (full text in `D7_C_PREREG_R1.md`)

- **Input**: accepted Model-F root
  `workspace/v72p2d5_model_f_input/20260907_r1`; `n=64`; block seeds
  `2026091300..2026091315`; one generated block per seed reused across both f
  and all four conditions; no CAL/VAL/parquet/raw reads.
- **Estimator (H03, independently re-verified)**: unique accepted
  post-R2 concentration/backoff estimator
  `v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate(counts_ab, p_b)`
  (L2323–2350) → `build_f_model_concentration` (L274–305) with
  `LAMBDA_STAR = 137.3823795883264` (L46). Rejected alternative recorded:
  `prepare_model_f_prior` (L2292–2320) → `build_f_model` (L246–271) per-cell
  pseudocount, the identified `LAMBDA_APPLICATION_CONTRACT_DEFECT`, excluded by
  R1 §3.1.
- **Mother**: D6-frozen D5-native n=64 construction
  `build_dv3_nested_support(64, 64, k_min, seed)` +
  `assign_gf32_coefficients(sup, seed, None, 64)` with L1 k_min 49 / seed
  `2026090501`, L2 k_min 43 / seed `2026090502`; built in memory; VOID
  matrices/results never read. Disclosures f `[1.0, 1.2]`: L1 rows 49/59, L2
  rows 43/52.
- **Decoder**: historical certified `v35.decode_row_layered_fftqspa`, cold,
  `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None`; one single-layer
  decode per condition/block/f; no sequential L1→L2 APP, no feedback, no
  flooding/schedule/damping/clipping/restart/min-sum/graph-search/tuning.
- **Priors**: four direct constructions from `J[u1,u2,b]` (R1 §3.3), oracle
  slices normalized over their layer axis; transpose to `(position,q)` and a
  single `d5._floor_renorm(..., DECODER_FLOOR=1e-15)` application at the
  decoder boundary only.
- **Budgets**: `<= 128` calls (exactly 128 normally), 120 s/call watchdog,
  stored wall `<= 1500 s`, outer `timeout -k 30 1800`, RSS `< 2 GiB` via
  stdlib `resource` with explicit Linux KiB→bytes, fail-before-first-call on
  unavailable/nonpositive/nonfinite RSS; zero retry/rerun/resume; no psutil.
- **Evidence**: per-call and per-`(f,layer)` scalar records per R1 §3.6; no raw
  beliefs/symbols/priors/syndromes/block vectors persisted; current-belief
  confidence/entropy labeled diagnostics only.
- **Outcomes**: stratum thresholds and the 11 run terminals in exact priority
  order per R1 §4.
- **Provenance (A1 §A1.4/C14)**: iteration-0/current beliefs recorded only as
  `PRIOR_ONLY_CURRENT_BELIEF` (never posterior/APP); `beliefs_conditioned`
  derived from `iterations` and the reviewed audit semantics; no
  `final_beliefs -> other layer` data flow anywhere.

## Files, root, command

New module `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_bidirectional_oracle.py`,
new tests `comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py`,
new script `scripts/v72p2d7_gf32_bidirectional_oracle.py`. Future root
`workspace/d7_c_bidirectional_oracle_<uuid>/` fresh/no-overwrite/no-subdirs with
exactly `manifest.json, decoder_records.csv, paired_summary.csv, summary.json,
report.md, command_log.txt`. Frozen future WSL command (not run):

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_<uuid>
```

## R1/A1 binding and closeout

- R1 binds fully except where A1 amends it. H01 requires both
  `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS` and
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`. H02 cites
  the primary MIXED outcome and shows D7-C never consumes cross-layer returned
  beliefs.
- The implementation must not import or depend on the future interface-rework
  implementation. Pre-EXECUTE must verify direct four-prior construction and
  the absence of any `final_beliefs -> other layer` data flow.
- Closeout records two parallel states:
  `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` and
  `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP`. All
  authorization false; no attempts/results/completed fields; no push.

## Prohibitions

No D7-C scientific execution authorization; no R1d; no `--phase`; no
G1/G2/CAL/VAL/real/raw/VOID access; no production v35/D5/D6/D7-A/D7-B edits; no
UUID; no push; no Model-F binary content read in the freeze/implementation
task.
