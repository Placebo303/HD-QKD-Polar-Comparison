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
