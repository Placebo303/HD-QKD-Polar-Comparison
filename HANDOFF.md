# HANDOFF — HD-QKD Nonbinary LDPC route (V30R archived)

## Current state (2026-08-20)

- V30R change `formal-nonbinary-ldpc-v30-projective-safe-finite-graph-gate/`
  is archived with terminal `finite_graph_fail` (P103 ACCEPTED 2026-08-20).
- Original V30 `P102 ACCEPTED` is superseded. Canonical `run_01` implementation,
  pre-registered execution, and independent read-only verification are complete;
  verifier `ok=true`, `problems=[]`, with no DE/decoder rerun. No push occurred.
- Frozen inputs: V25
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
  and
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`;
  V26 canonical
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
  (manifest/M0/verify); V28R canonical
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
  (config/evidence/manifest/verify).
  Source mapping is `type2_1M_20260121_184040/-50 ps/1M`,
  `type2_1p5M_20260121_183806/+50 ps/1p5M`, and
  `type2_2M_20260121_183657/+50 ps/2M`, with matching
  `v13r3fresh_pairs_20260816/<source_id>/pairs.parquet` paths.
- Field binding is `GF2mField.create(32)`, primitive polynomial `0b100101`,
  V28R field_id
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, and
  zero-based `ratio_index` into `nonzero_cycle`.
- Packet cap: at most one balanced and one PEG-projective-cycle-cancelled per
  selected allocation, at most two allocations/four packets globally. M1 is
  exactly 72 screen calls and at most 60 confirmation calls; M3 screen is
  `0..19`, only top-ranked confirmation is `20..69`, and its failure is global
  `finite_graph_fail` with no fallback.

## V30R closeout

- Evidence root:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01/`.
- M0=`15/69/303/922/1107`; M1=72 screen+60 confirmation, eligible
  `m1=9,12,16`, selected/confirmed `m1_9,m1_12` both 30/30.
- M2 retained balanced `m1=9,12`; PEG packets were deterministic rejects due
  to no projectively unique ratio for support `(0,1)`.
- M3 stopped after blocks `0..5` on source 1M for both valid packets (`0/6`
  exact/tag, `0` false accepts), so no other source or confirmation ran.
  Resource meters: 74.828s DE and 719.876s decoder.
- Scope: only the tested `n=1024` F03 fixed-allocation/family finite conversion
  is negative. V25 empirical channel and V26 DE remain valid within their own
  boundaries; this is not an all-NBLDPC impossibility result.

---

## Historical V27–V29 state (superseded by V30R)
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

## Next (requires new authorization)

No automatic fallback remains. A future V31 finite-graph redesign may consider
`m1=16`, projective-capacity-aware PEG, L2 girth/expander/QC/SC structure, and
`n=2048/4096`, but it requires a new OpenSpec, independent review, and explicit
user authorization. Do not expand or rerun the V30R packet.

## Hard prohibitions (all phases)
- No push; no fresh/raw .ttbin; no qualification/promotion; no degree search/MET; no V26 rerun;
  no finite-matrix/FER inside V27 (only V28+). Preserve all failures; no re-tuning/re-runs.
