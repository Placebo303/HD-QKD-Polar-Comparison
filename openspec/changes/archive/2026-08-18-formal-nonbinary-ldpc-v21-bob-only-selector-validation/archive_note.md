# Archive Note — formal-nonbinary-ldpc-v21-bob-only-selector-validation

Status: ARCHIVED (closeout accepted, user-authorized archive 2026-08-18)

## Why archived
- V21 evaluated Bob-executable q=1024 short-block strategies S0 BP-only, S1
  bounded4-only, S2 BP-first-fallback-bounded4 on 64 fresh n=64 frames.
- Observed stop gate triggered: S0=24/64 FER=0.625, S1=28/64 FER=0.5625,
  S2=28/64 FER=0.5625; all >= 0.45, so the short-block OSD/top-K branch is
  frozen.
- Retained as diagnostic_only. P0/P1 were not pre-frozen; runtime
  Alice-injection verifier and V01 independent semantic verification were
  NOT_RUN/UNVERIFIED. These limitations are preserved and do not reopen the
  stopped branch.

## Preserved
- Code: `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v21_bob_only.py`,
  CLI `comparison_bench/src/comparison_bench/cli/run_v21_bob_only.py`.
- Tests: focused S0/S1/S2 tests.
- Evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v21_20260816/`.
- Claim boundary: diagnostic_only, stop gate met.

## Closeout review
- Independent read-only closeout review ACCEPT on 2026-08-17.
- Archive movement authorized by current objective on 2026-08-18.
