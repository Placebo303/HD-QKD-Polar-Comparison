# V39P0 Review Entrypoint

**Cycle**: `V39P0`
**Change ID**: `formal-ir-v39-lanec-robustness-laneb-control`
**Repository**: `Placebo303/HD-QKD-Polar-pipeline`
**Branch**: `formal-ir-mainline`
**Lifecycle state**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Predecessor cycle**: `V38R1` (terminal `V38_MULTIPLE_ROUTE_SIGNALS`)
**Accepted predecessor result SHA**: `2416486f724f4fb7cbf1058d9dc1bb1fc5ded5ed`
**Independent acceptance commit**: `c8c5cd2e`
**Accepted predecessor implementation SHA**: `8f7bc7d8d7366772ff425528cd1080fa67ef7509`
**Plan target SHA**: recorded in the plan-candidate commit message of this
repository; reviewers must verify it via `git rev-parse` before treating any
verdict as ACCEPT (otherwise advisory only).

## What to review

Primary documents, in reading order:

1. `openspec/changes/formal-ir-v39-lanec-robustness-laneb-control/proposal.md`
2. `openspec/changes/formal-ir-v39-lanec-robustness-laneb-control/design.md`
3. `openspec/changes/formal-ir-v39-lanec-robustness-laneb-control/specs/formal-ir-v39-lanec-robustness-laneb-control/spec.md`
4. `openspec/changes/formal-ir-v39-lanec-robustness-laneb-control/tasks.md`
5. `docs/research_cycles/V39P0/EXECUTION_PACKET.md`

## Scope of the frozen plan

- Main route Lane C and control route Lane B on ALL nine pre-registered
  construction seeds each (18 matrices deterministically reconstructed and
  strictly checked against the committed V38P0 27-record structural JSON).
- 15 NEW development block seeds (390101-390105 / 390201-390205 /
  390301-390305) sampled from the same source-specific V25 TRAIN empirical
  counts with oracle-L1 conditioning.
- Same-block frozen V31 baseline recomputed exactly once per block (15 calls).
- Exactly 105 real decoder calls in one authorized run: 45 + 45 + 15.
- Frozen gates C1 / B1 / CB / BASE; six-state terminal machine with
  integrity-first precedence (`V39_EVIDENCE_INVALID` overrides all).
- Success criterion is `exact_l2` everywhere; `syndrome_ok` and
  `wrong_codeword` are reported separately and never counted as exact.

## Specific reviewer questions

1. Are revisions R39-01..R39-12 correctly and completely incorporated:
   CB-b `d_CB - d_BC >= 3` over the complete 45 pairs; CB-d as the MEAN
   comparison; per-(source, construction_seed) >= 4/5 cell condition in
   C1/B1; per-ordinal BASE evaluation against the single 15-record
   baseline; renamed state 2 `V39_C_ROBUST_NO_COMPLETE_ADVANTAGE` with
   `terminal_reason`; NPZ carve-out preserving the legal read-only V25
   counts input; explicit posterior-preflight sentinels; exact-equality
   execution SHA binding?
2. Is the exhaustive terminal truth table (design Section 12) total and
   disjoint over all (C1, CB, BASE-C, B1) combinations, with correct
   `terminal_reason` selection for state 2?
3. Confirm BASE-B remains report-only and that the
   `V39_B_ONLY_ROBUST` no-auto-superiority caveats are correctly stated.
4. Confirm the posterior preflight sentinel set (six conditions) and the
   plan-review-only probe-replacement policy.
5. Confirm the baseline dedup rule (one record per block; ordinal-level
   joins of 15-vs-15; never replicated into new observations).

## Claim boundary for reviewers

No execution is authorized by this plan. Even after an authorized run,
results are bounded development evidence on empirical-count samples with
oracle-L1 conditioning — never FER, threshold, SKR, security,
qualification, promotion, or real-frame claims. Lane A is excluded from V39.
The 45 lane records per lane are 15 unique sampled blocks x 3 construction
matrices and must not be described as independent block draws; record-level
Wilson intervals and the 45-pair McNemar test are naive descriptive
summaries uncorrected for clustering.

## Verification hints

- Structural authority:
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
  (27 records; lane_b/lane_c subset = 18; lane_c records include
  `position_permutations`).
- Accepted V38R1 result evidence:
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_02/v38r1_triage_summary.json`
  and `v38r1_development_block_records.json`.
- Memory boundary: `AGENT_PROJECT_MEMORY.md` entries dated 2026-08-25.
