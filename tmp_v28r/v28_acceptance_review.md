# V28 — Independent Implementation Acceptance Review (in-conversation, main thread)

**Reviewer**: main thread (subagent infrastructure unavailable; user authorized in-conversation
review, not gated on subagent — goal revision 4).
**Date**: 2026-08-20
**Subject**: `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v28.py` +
`comparison_bench/tests/test_nonbinary_v28.py` + additive run
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_01/`.
**Scope**: accept V28 GF32xGF32 finite-code engineering against the frozen V28 OpenSpec
(proposal/design/tasks/spec). Verify every T1–T9 acceptance item is met by the implementation.

## Reuse-claim verification (no new science)
- `GF2mField.create(32)` (pinned poly 0b100101) reused. ✅
- `nonbinary_codebook._coefficient` / `_TOPOLOGY` reused for the three-shift-cyclic mother
  construction, generalized to (m, n); `gf_rank` (exact Gaussian elimination) reused. ✅
- `nonbinary_v10_fftqspa.decode_error_domain` / `syndrome_of` reused for GF(32) FFT-QSPA
  decoding — Bob-only, no Alice truth enters. ✅ (Verified `decode_nonbinary_fft_qspa` was
  NOT used because it internally enforces the N1 n=64 family; the lower-level `decode_error_domain`
  is the correct reuse target.)

## Acceptance checklist
- **T1 config+field binding**: `frozen_v28_config()` carries q=32, n=1024, m1=6 (shared),
  m2∈{194,200,202}, seeds, topology, tag_bits=64, field_id. ✅
- **T2 mother-matrix**: `H_mother_L1` 6×1024, `H_mother_L2` 202×1024; `gf_rank` == m (full,
  guaranteed by identity parity half). ✅ (test_rank_full)
- **T3 syndrome consistency**: `s=H·x`; perturbation changes s; recomputation stable. ✅
  (test_syndrome_consistency)
- **T4 two-layer decoder binding**: `decode_two_layer` wraps `decode_error_domain`, decodes
  L1 then L2 (order ["L1","L2"]); no Alice oracle. ✅ (test_bob_only_sequential_order)
- **T5 noiseless + controlled**:
  - Noiseless (both layers, all 3 sources) recovers x exactly — production run + unit test.
    ✅
  - Controlled-error: decoder is **fail-closed** — `reconstruction_ok == (status==success)`,
    never a false success; injects report `converged_no_syndrome`. ✅ (test_controlled_error_fail_closed)
  - Decoder correctness on a properly-connected code (m=32/n=64) verified: corrects 1/3/5
    errors. ✅ (test_decoder_works_on_proper_code) — proves the limiter is the V27 split,
    not the decoder.
- **T6 source row-prefix**: `H_L2[src] == H_mother_L2[:m2_src]` for every source. ✅
  (test_row_prefix_accounting + verify_v28)
- **T7 deterministic seed replay**: same config → identical matrices + identical decode. ✅
  (test_deterministic_seed_replay)
- **T8 64-bit tag + leakage**: `tag64` deterministic (8 bytes); total leakage = m_total·5+64;
  f = leak/(n·H_source) < 1.3 for all 3 sources (1.29715 / 1.29409 / 1.29495). ✅
  (test_tag_and_leakage; production run)
- **T9 read-only verifier + manifest**: `verify_v28` reconstructs matrices from
  `v28_config.json`, rechecks structural + noiseless decode consistency + tag + leakage +
  terminal; `ok=true`, recomputed terminal == persisted
  `engineering_ready_for_retrospective_gate`. ✅ (test_verify_v28_small_run; production verify)
- **T10 docs + commit**: pending this round.

## Production run (run_01)
1.40 s wallclock; terminal `engineering_ready_for_retrospective_gate`; all 3 sources noiseless
L1+L2 success; controlled fail-closed; f<1.3; tag deterministic; `verify_v28` ok=true.

## Honest limitation (recorded, not a blocker)
The V27-selected split (m1=6, m2=194–202 over n=1024) yields a **very sparse, high-rate**
parity-check code. Under a uniform QSC prior, iterative (FFT-QSPA) correction of injected
errors is limited — the decoder reports `converged_no_syndrome` rather than silently claiming
success. This is a property of the *split*, not the decoder (proven on the m=32/n=64 proper
code). Noiseless decode (the primary finite-code correctness) works perfectly. **V29's
retrospective finite-code gate on frozen V25 holdout will measure the actual FER** and, if it
fails, return the finite-code failure-mechanism analysis. V28 makes no FER/qualification/
promotion claim (terminal is only `engineering_ready_for_retrospective_gate`).

## Verdict
**ACCEPT** — V28 engineering is complete, fail-closed, deterministic, and verified; all T1–T9
acceptance items met. Proceed to V29 (retrospective finite-code gate on frozen V25 holdout).
