# Proposal: formal-nonbinary-ldpc-v20-q1024-decode-improvement

> Status: APPROVED — user approved direct V20 planning/execution after V19 review (2026-08-16).

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
  5. Bounded-support exhaustive list decoding (small n, small weight) as a
     BP/OSD-independent decoder for q=1024 high-rate short blocks.
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

## Updated V19 blocker evidence (Round 83-84)
- Best finite-length point remains n=64,m=4,lambda {2:0.6,3:0.4},f≈1.136:
  **28/64 exact_correct, FER=0.5625** (64-frame honest sample; 32-frame was 15/32).
- Same-f block lengths n=80,m=5 and n=96,m=6 are worse (2/8 and 1/8 exact).
- Reliability-sorted MRB-OSD was implemented (`osd_decode_candidates_mrb`) and
  integrated as MRB OSD-1 full + MRB OSD-2 broad; on seed 2252/2276 it did not
  change outcomes, and on hard frame seed 2055 it still did not recover.
- Direct MRB probes on frame 2055 (OSD-2 all-free/symbols 4-8, OSD-3/4 bounded,
  OSD-3 all-free/symbols 2) also did not find Alice's codeword.
- Code-seed sweep on the same hard frame (code seeds 3001-3005, frame fixed 2055)
  all yielded `exact_mismatch`; rho variants {35,39}, {33,41}, {30,44} also failed.
- BP random-prior retry probes (blind-reconciliation style) on hard frame 2055 and
  seed 2252 mismatch frames also failed to recover Alice.
- Conclusion: the V19 PEG/FFT-QSPA + OSD/BP-retry family is exhausted at q=1024 f≤1.3;
  V20 must select a strictly stronger code construction/decoder or a pre-registered
  different mechanism (e.g. blind reconciliation, SC/MET, better information-set
  decoding with larger n).

## Claim boundary
`diagnostic_only` until a frozen gate review accepts the V20 protocol.
