# HANDOFF — HD-QKD Nonbinary LDPC route (V27 -> V28 -> V29)

## Current state (2026-08-20)
- **V27 finite-leakage-margin DE gate: PASS** (`pass_finite_budget_ready`, passing_block_len=1024).
  All 4 block_lens x 3 sources confirmed at the m1_ep offset-0 candidate.
- Evidence root: `comparison_bench/outputs_comparison/nonbinary_diagnostics/
  nbldpc_v27r_finite_leakage_margin/run_01/` (frozen_config + screen/confirm checkpoints+results
  + ranking + gate + RUN_MANIFEST + EXECUTION_WALLCLOCK_S=322.9s).
- Module: `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v27_gate.py` (budget planner
  + V26 MC-DE wrapper; 24h completed-call resource gate; four terminal states; read-only verifier).
- Tests: `comparison_bench/tests/test_nonbinary_v27_gate.py` (11 passed).
- V27R OpenSpec ACCEPTED (commit ed9bbf9e); candidate-delivery review ACCEPT
  (`tmp_v27r/v27_candidate_delivery_review.md`). V27 committed locally (9c3f0e70). No push.
- **V28 IMPLEMENTATION COMPLETE + acceptance ACCEPT** (`nonbinary_v28.py`, 11 tests, run_01 1.40s, verify ok; review `tmp_v28r/v28_acceptance_review.md`). Terminal `engineering_ready_for_retrospective_gate`. Honest limit: sparse-code uniform-QSC correction is limited (fail-closed); V29 measures real FER.

## Next (Phase C — V28)
- Create V28 OpenSpec (deterministic GF32xGF32 finite-code engineering); independent freeze review
  ACCEPT (in-conversation, authorized), then implement: two-layer deterministic GF32 parity-check
  MOTHER matrices from V27-selected (m1,m2,R1,R2) at the min passing block_len=1024; source only
  sets the public syndrome row prefix; claim only `engineering_ready_for_retrospective_gate` (no
  FER/qualification/promotion). Then V29 retrospective finite-code gate on frozen V25 holdout.
- **Next: V29 retrospective finite-code gate** — OpenSpec + freeze review ACCEPT, then implement on frozen V25 holdout (pre-registered grouping/source/matrix/decoder/iterations/failure-def/FER-threshold/run-root; Bob-only L1->L2 + tag verification; no Alice-oracle/top-K/frame-swap; one execution + read-only verifier; pass -> ready_for_fresh_qualification_change + V30 proposal only; fail -> finite-code failure analysis). Stop before fresh qualification; no V28/V29 raw .ttbin reads.

## Hard prohibitions (all phases)
- No push; no fresh/raw .ttbin; no qualification/promotion; no degree search/MET; no V26 rerun;
  no finite-matrix/FER inside V27 (only V28+). Preserve all failures; no re-tuning/re-runs.
