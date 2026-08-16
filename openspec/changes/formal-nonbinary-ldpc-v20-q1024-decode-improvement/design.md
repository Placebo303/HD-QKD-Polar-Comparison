# Design: formal-nonbinary-ldpc-v20-q1024-decode-improvement

## Status
DRAFT — based on V19 primary-route evidence.

## Problem
- f≤1.3 leakage point is reachable: n=1024, m=73, R=0.929, f≈1.296.
- Current decoder returns `decode_failed` / `converged_no_syndrome` on all tested
  frames; simple postprocessing does not recover.
- The gap is finite-length decoding performance at very high rate.

## Proposed mechanisms

### M1: Bounded q-ary OSD
- Use BP posterior reliabilities to select an information set.
- For order 0: hard-decision from BP, solve for parity and check syndrome.
- For order 1: flip one symbol in the most-reliable information positions and
  re-solve; bounded by a small number of candidates.
- Use GF(q) tables from `nonbinary_field.GF2mField`.

### M2: Improved construction
- Use `find_two_degree_rho` / custom rho to keep exact socket consistency.
- Try QC-PEG with larger girth (if feasible) and multiple edge-label seeds.
- Pre-register a small construction search on development-only synthetic frames,
  not on confirmation frames.

### M3: Decoder retry / blind reconciliation
- Add bounded retries with randomized prior perturbations (seeded) and a public
  hash check after each retry.
- Keep exact syndrome/public-bit accounting.

### M4: Channel-aware DE gate
- Use `build_high_plane_w` and per-symbol-class puncture models to pre-register
  a DE gate only if capacity analysis shows a path to f≤1.3.

## V19 full-OSD breakthrough
- Full OSD-1 enumeration at q=1024, n=128, m=9, f≈1.279 recovered Alice on
  one frame (121738 candidates) but not on a second frame.
- At n=64, m=4, f≈1.136 full OSD-1 recovered 3/8 frames (FER=0.625);
  fast OSD-1..10 over 64 frames achieved 18/64 exact (FER=0.71875).
  With lambda {2:0.6,3:0.4}, n=64 fast OSD achieved 10/24 exact
  (FER=0.5833); at n=128 the same lambda gave 0/4.
- Broad OSD-2 did not recover any of the five n=64 non-full-OSD-1 frames.
- This proves exact q=1024 f≤1.3 decoding is possible with stronger OSD,
  but reliability/scale remains the open problem.
- V20 should focus on efficient full/partial OSD enumeration, better
  information-set selection, and/or smaller n with rate-compatible framing.

## V19 prototype evidence
- `nonbinary_v19_osd.py` implements OSD-0/1 plus bounded OSD-2 candidate search.
- R=0.89 q=1024: OSD improves to 2 exact / 2 exact_mismatch / 0 decode_failed.
- f=1.296 q=1024 n=1024: OSD-0/1/2 and wide OSD-2 still only exact_mismatch.
- This motivates V20 to go beyond bounded OSD-2 or improve code construction.

## Acceptance criteria (draft)
- T0: all V20 tests pass.
- E01: deterministic q=1024 synthetic run with at least one configuration
  achieving `exact_correct` at f≤1.3, or honest `best_f`/`FER` recorded.
- V01: read-only replay verifies byte-identical scientific outputs.
- C01: decision-log/memory/handoff updated.

## Outputs
- Additive evidence under
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v20_<date>/`.
- No overwrite of V19 or frozen outputs.
