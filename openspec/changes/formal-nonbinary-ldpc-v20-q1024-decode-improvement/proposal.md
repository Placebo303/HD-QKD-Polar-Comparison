# Proposal: formal-nonbinary-ldpc-v20-q1024-decode-improvement

> Status: DRAFT — prepared from V19 diagnostic evidence; production execution requires freeze review/acceptance.

## What
Improve q=1024 Nonbinary LDPC finite-length decoding so that the already-reachable
f≤1.3 leakage point (n=1024, m=73, R≈0.929, f≈1.296) becomes decodable with
acceptable FER, or honestly records the best achievable FER under a pre-registered
improved decoder/code construction.

## Why
V19 diagnostics established:
- q=1024 n=1024 m=73 achieves f≈1.296 (leakage target met).
- 4/4 frames decode_failed with current simple PEG/FFT-QSPA.
- Longer block n=2048 m=133 f≈1.181 also decode_failed.
- Literature-inspired Müller degree distribution and bounded single/two-symbol
  postprocessors did not recover frames.
- Therefore the missing piece is decoder/code-construction quality, not leakage
  accounting or channel modeling.

## Scope
- Add V20 modules under `comparison_bench/` only.
- Candidate improvements:
  1. Bounded q-ary OSD (order 0/1) using BP reliabilities and GF(q) linear algebra.
  2. Improved PEG/QC construction with larger girth or optimized edge-label profiles.
  3. Layered/relaxed FFT-QSPA scheduling and/or blind-reconciliation-style
     retry with public hashes.
  4. Pre-registered channel-aware DE gate (per-symbol-class puncture) if a
     mechanism survives capacity analysis.
- Execute-once deterministic synthetic q=1024 diagnostics; strict read-only
  verification.

## Out of scope
- Modifying frozen `src/`, `experiments/`, `tools/`, `results/`.
- Fresh/promotion/qualification claims.
- Real-data `.ttbin`/legacy execution unless separately authorized.
- Unbounded tuning/rerunning of V19 evidence.

## V19 blocker evidence
- q=1024 f≈1.296 / f≈1.279 / f≈1.119 configurations all produce
  `exact_mismatch` with BP + bounded OSD.
- Block lengths n=128/256/512/1024/2048 tested; none gave exact at f≤1.3.
- Comprehensive summary:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/n4_finite_q1024_f129_blocker_summary.json`
- V20 must therefore implement a decoder/construction that goes beyond
  bounded OSD-2 and the current PEG/FFT-QSPA.

## Claim boundary
`diagnostic_only` until a frozen gate review accepts the V20 protocol.
