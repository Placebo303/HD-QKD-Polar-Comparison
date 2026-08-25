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

1. Do the gates C1/B1/CB/BASE and their thresholds match the intended
   protocol? Gate CB sub-items b/d were transcribed from a partially
   corrupted task packet; see design Section 19 OQ-1/OQ-2 and confirm or
   correct the strict-inequality discordance form and the median choice.
2. Is the terminal-state precedence in design Section 12 (resolution of the
   literal overlap between states 2 and 3 via B1 status, and the C1+CB PASS
   with BASE-C FAIL fall-through) acceptable? OQ-3/OQ-4.
3. Confirm BASE-B is report-only and drives no terminal state (OQ-5).
4. Confirm the posterior-binding preflight contract (design Section 5)
   fully guards against a recurrence of the V38P0 `u2_bob` defect.
5. Confirm the baseline dedup rule (one record per block; join-based
   comparisons; never 45 replicated baseline observations).

## Claim boundary for reviewers

No execution is authorized by this plan. Even after an authorized run,
results are bounded development evidence on empirical-count samples with
oracle-L1 conditioning — never FER, threshold, SKR, security,
qualification, promotion, or real-frame claims. Lane A is excluded from V39.

## Verification hints

- Structural authority:
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
  (27 records; lane_b/lane_c subset = 18; lane_c records include
  `position_permutations`).
- Accepted V38R1 result evidence:
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_02/v38r1_triage_summary.json`
  and `v38r1_development_block_records.json`.
- Memory boundary: `AGENT_PROJECT_MEMORY.md` entries dated 2026-08-25.
