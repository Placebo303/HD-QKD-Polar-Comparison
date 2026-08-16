# NBLDPC Primary Route V19 — Diagnostic Progress (2026-08-16)

Status: diagnostic_only / additive evidence.  This document records the first
V19 run on the Nonbinary LDPC primary route (Route N0–N6).  It does not claim
fresh/promotion/qualification.

## N0 — Contract freeze

- Execution contract: `docs/nbldpc-focus-plan-20260816.md`.
- Reused read-only: V18-B2 structured DE, V10 DE/PEG/FFT-QSPA, V14 MC-DE.
- Output root:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/`
- Scratch: `workspace/`.

## N1 — Channel model

- Evidence: `n1_channel/channel.json`
- Reuses V17 per-plane error vector and V18 folded q=16 channel.
- Folded q=16 entropy: `0.382911` bits/symbol; full q=1024 `0.549955`.
- QSC equal-entropy control p=0.038: `0.381508`.

## N2 — DE search

### N2a — Warm-started rate ladder

- Evidence: `n2_rate_ladder/rate_ladder.json`
- Warm-started from V18-B2 rate-0.60 best lambda.
- With a small local budget (pop=4, gen=1, n_samples=500, max_iter=30),
  the first higher rate 0.65 did **not** converge.
- This is consistent with the prior V18-B2 plain structured-channel ceiling:
  R≈0.60 / f≈4.18.

### N2c — Extended-degree probe

- Evidence: `n2_extended_probe/extended_degree_probe.json`
- Two candidates with degrees up to 48 and 60 at rate 0.65 both failed to
  converge on the folded structured channel.
- The probe path accepts degrees above the frozen V10 40-degree encoding
  without modifying V10/V14.

## N3/N4 — Finite code construction and synthetic execute

- Evidence: `n4_finite_q16_r060_simple/finite_execute.json` (+ outcomes.csv)
- q=16, n=512, m=205, rate=0.5996, simple degree distribution `{2:0.5, 3:0.5}`.
- 4 deterministic synthetic frames: 3 `exact_correct`, 1 `exact_mismatch`,
  0 `decode_failed`; FER=0.25.
- syndrome bits/frame = 820; f_plain_qary = 4.183.
- The `exact_mismatch` is retained, not converted to ok.

## N6 — Three-way comparison

- Evidence: `n6_comparison/comparison_table.csv` and `comparison_summary.json`
- Binary LDPC MLC baseline imported from existing
  `v19_binary_mlc_prototype_20260816`: f≈4.169, FER=0.
- Nonbinary LDPC diagnostic row: f≈4.183, FER=0.25.
- Binary Polar MLC is available in the separate release repo
  `D:\Code\HD-QKD_Polar_Release`; this package marks it `not_available` until a
  clean evidence JSON is supplied.

## Constraints honored

- Frozen `src/`, `experiments/`, `tools/`, `results/` untouched.
- New code under `comparison_bench/` only.
- Outputs are additive; no existing evidence overwritten.
- No push.
