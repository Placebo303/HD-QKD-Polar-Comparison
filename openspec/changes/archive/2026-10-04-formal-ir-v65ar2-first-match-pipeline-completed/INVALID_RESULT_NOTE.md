# INVALID_RESULT_NOTE — V65AR2 Stage0 misapplication (SHA 3a6c4fa)

**Date**: 2026-08-31  
**Affected implementation SHA**: `3a6c4fa` (`251807f3` .. `3a6c4fa` pipeline)  
**Accepted plan SHA**: `70f9ed8ece53704374d37810a163a519e57be6e9`

## Summary
Stage0 in `3a6c4fa` violated the frozen plan: it executed `hierarchical_estimate` / `CE1/CE2` / `lambda` / `unseen` / `m1/m2` and `G2-G8` gates on the 8-frame (`4+4`) sample and used `m_req` to fail candidates.  
**Plan-frozen Stage0** is strictly materialization-only: `Phase R PASS` + real 8 frames ×256 pairs (4096 pairs materialized as 8 blocks), symbols `0..1023`, `mapping legacy_v1` / `frame_anchor period 204800`, provenance `sign(delay)==sign(peak)`, and `forbidden overlap` (`CAL∪VAL∪TEST_key ∩ forbidden ==∅`). No `estimate_stage` / `hierarchical` / `gate_stage` / `CE` / `lambda` / `unseen` / `m1/m2` shall be called in Stage0; `selected` is the first `Phase R PASS && materialization PASS` in frozen order `162148 → 2500K → 160254` (expected `162148` but not hard-coded). Stage1 alone runs the `256+64` estimator and stability gates.

## Consequence
Any `run_02` / `pipeline_result` produced by `3a6c4fa` that reports `STAGE0_NO_CANDIDATE` or candidate elimination due to `CE`/`m_req`/`lambda` is **misapplication and has no elimination effect** on `162148`. The result shall not be used to claim `162148` failed Stage0. Formal elimination requires a new run on the corrected Stage0.

## Remedy
- Fixed in next implementation SHA: `run_stage0` no longer calls `hierarchical_estimate` / `CE` / `lambda` / `m`; it only checks `Phase R PASS`, `8×256`, `0..1023`, `mapping/anchor`, and `forbidden overlap`.
- New tests monkey-patch `hierarchical_estimate` to throw and assert Stage0 still succeeds; inject extreme CE (still PASS); corrupt frame count (FAIL); verify first-match `UNREACHABLE`; verify Stage1 correctly runs `CE`/`λ`/`rate`.
- This note is the evidence that the old run's Stage0 failure is invalid.
