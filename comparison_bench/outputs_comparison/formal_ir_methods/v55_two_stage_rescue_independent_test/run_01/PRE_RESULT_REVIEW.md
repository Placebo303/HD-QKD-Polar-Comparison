# PRE_RESULT_REVIEW — V55 Two-Stage Rescue Independent TEST

Date: 2026-08-29
Cycle: V55P0 / formal-ir-v55-two-stage-rescue-independent-test
Result: QUALIFICATION_RESULT_ACCEPTED_FAIL / V55_INDEPENDENT_TEST_FAIL (independent cross-session, not qualification PASS; 0/90 fail evidence accepted)

## Binding
- accepted_plan_sha: 3d7c63eefe655c9f25d199af3f7f4ea311ac454b (short 3d7c63ee)
- implementation_sha: cf8b098047cf64aa1e0426e2ea2e62b680430bd6 (short cf8b0980)
- branch: origin/formal-ir-mainline
- HEAD at review: bb1cef45e69d7def78b31de8b9f7dbaec28cc890
- run_01: comparison_bench/outputs_comparison/formal_ir_methods/v55_two_stage_rescue_independent_test/run_01/ (v55_records.json/.csv, v55_summary.json — bytes frozen, 0/90)

## Accounting (360 calls)
- decoder_calls_completed: total 360 = L1 90 + L2 270 (base 90 + stage1 90 + stage2 90); hard_cap 360; 180-360 planned range satisfied.
- per-block: L1 90/90, base 90/90, stage1 90/90, stage2 90/90 (90/90/90/90).

## Re-check PASS
- Gate: overall 0/90 <70, per-source 0/30 <20 each → correctly FAIL; undetected==0 enforced. PASS (correctly judged FAIL).
- Leakage: per_source_avg = leak_base +40*N_stage1/30 +40*N_stage2/30; overall=(Σ leak_base[source(block)]+40*N1_total+40*N2_total)/90; avg 1167.33, disclosure 105060 bits. No JSON补字段. PASS.
- Undetected isolation: undetected_accepted_wrong 0, never merged into success/FER. PASS.
- Per-source breakdown: 1M/1p5M/2M each 0 exact, 30 blocks each, n_stage1/2 30 each. PASS.

## Non-blocking comments (3)
1. provenance — origins retained in summary; L1 detail provenance optional.
2. L1 90 footnote — disclosure_per_final_exact_block null when final_exact_full_count 0 (0/90); informative only.
3. wrong_codeword_l1 — present in records for audit, decode_failed already isolated; no success inflation.

## Verdict
PRE_RESULT_REVIEW PASS — 0/90 fail result solidified; bytes unchanged; no fields added to JSON.
