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

### N2b — Channel-aware diagnostic bound: LSB-public two-step

- Evidence: `n2b_channel_aware_bounds/lsb_public_capacity.json`
- Capacity-ideal bound for 0..10 public LSB planes.
- Publicly disclosing LSBs does **not** lower ideal full f: the added public
  bits exceed the entropy removed from the protected high-bit alphabet.
  - l=0 (full q=1024 coding): ideal f≈1.00.
  - l=1: ideal f≈2.40.
- Conclusion: the route to f≤1.3 must target **full q=1024 DE/code
  construction**, not simple LSB-public disclosure; per-symbol-class puncture
  remains the more promising channel-aware mechanism.

## N2b — High-plane effective channels for LSB-public DE prep

- Evidence: `n2b_channel_aware_bounds/high_plane_channels.json`
- Added `build_high_plane_w(public_lsb_planes)` to construct the residual
  high-bit Gray symbol-difference channel after publicly disclosing L LSB
  planes.
- Entropies: l=0 q=1024 H=0.549955; l=1 q=512 H=0.319217; l=4 q=64
  H=0.056943; l=6 q=16 H=0.017841.
- This gives the DE input for a Pacher-style LSB-public two-step if a future
  change decides to evaluate that mechanism.
- Initial tiny DE probe on l=1 high-plane q=512 at target R=0.92:
  non-converged (`n2b_channel_aware_bounds/lsb_public_de_probe_q512.json`).

## N2c — Extended-degree probe

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

## N3/N4 — q=1024 finite code construction and synthetic execute

- Evidence: `n4_finite_q1024_simple/finite_execute.json` (+ outcomes.csv)
  and `n4_finite_q1024_n128_simple/finite_execute.json` (+ outcomes.csv).
- q=1024 (full V17 structured channel via `build_real_w_q1024`),
  simple degree distribution `{2:0.5, 3:0.5}`.
  - n=64, m=24, rate=0.625: 2/2 exact_correct, FER=0, f_plain≈6.819.
  - n=128, m=51, rate≈0.602: 4/4 exact_correct (2-frame and 4-frame runs),
    FER=0, f_plain≈7.245.
- syndrome bits/frame = 240 (n=64) / 510 (n=128).
- This shows the full q=1024 V19 pipeline (PEG + FFT-QSPA + structured
  channel prior) is executable at two small block lengths, while the leakage
  is still far above 1.3.

## N2c — q=1024 extended-degree DE probe

- Evidence: `n2_extended_probe_q1024/extended_degree_probe.json`
- q=1024, rate=0.6, simple lambda `{2:0.5, 3:0.5}`,
  n_samples=100, max_iter=3: non-converged (final base-q entropy ≈0.0477).
- This is a tiny diagnostic probe, not a production DE search.

## N3/N4 — q=1024 high-rate finite attempts (R≈0.84 / R≈0.89)

- Evidence:
  - `n4_finite_q1024_r084_simple_16f/finite_execute.json`: q=1024, n=256,
    m=41, R≈0.840, f≈2.912, **8/16 exact_correct, 8/16 decode_failed
    (corrected), FER=0.5**.
  - `n4_finite_q1024_r089_simple/finite_execute.json`: q=1024, n=256,
    m=28, R≈0.891, f≈1.989, **3/16 exact_correct, 13/16 decode_failed
    (corrected), FER=0.8125**.
- Under the corrected status rule, these are mostly `decode_failed`
  (non-success, non-exact); only a true syndrome-consistent wrong word is
  `exact_mismatch`.
- This gives an honest q=1024 best-f/FER tradeoff: lower leakage is possible
  (f≈1.99) but current simple PEG/FFT-QSPA is not reliable at those rates.

## N3/N4 — q=1024 f≤1.3 leakage-point attempt (n=1024, m=73)

- Evidence: `n4_finite_q1024_f129_n1024_4f/finite_execute.json`
- q=1024, n=1024, m=73, rate≈0.9287, f_plain≈**1.296** (within f≤1.3 leakage target).
- 4/4 frames ended as **decode_failed** (`max_iter_reached`; corrected status;
  no syndrome-consistent wrong word was returned).
- This honestly records that the leakage target is numerically reachable, but
  the current simple PEG/FFT-QSPA construction does **not** produce reliable
  decoding at this rate.
- Additional one-frame probes with degree distributions `{2:0.7,3:0.3}` and
  `{2:0.8,3:0.2}` also ended `decode_failed` at max_iter=10
  (`n4_finite_q1024_f129_c_lambda_1f/`, `n4_finite_q1024_f129_d_lambda_1f/`).
- A custom exact-socket rho attempt with the V18-B2 optimized lambda at
  n=512, m=64, R=0.875 also ended 4/4 `decode_failed`
  (`n4_finite_q1024_optrho_n512_m64/`). This extends `construct_codebook` /
  `execute_synthetic_frames` with an optional `rho_edge` (additive feature).
- Tested a longer q=1024 block at n=2048, m=133, R≈0.935, f≈1.181
  (`n4_finite_q1024_f118_n2048_1f/`): 1/1 decode_failed at max_iter=3.
  Longer block length alone did not unlock reliable f≤1.3 decoding with the
  current simple PEG/FFT-QSPA.
- Added `find_two_degree_rho` to build exact-socket integer two-degree check
  distributions for arbitrary lambda (useful for literature distributions).
- Tested normalized Müller-et-al q=4 degree distribution on q=1024:
  - `n4_finite_q1024_f129_muller_2deg_1f/` (n=1024, m=73, f≈1.296):
    1/1 decode_failed.
  - `n4_finite_q1024_r089_muller_4f/` (n=256, m=28, f≈1.989):
    0/4 exact, 4/4 decode_failed.
  The literature-inspired irregular distribution also does not decode
  reliably at these high rates with the current FFT-QSPA decoder.
- Implemented bounded q-ary OSD-0/1 (`nonbinary_v19_osd.py`) and integrated it
  into the finite executor.
  - `n4_finite_q1024_r089_simple_pp_osd/`: R=0.89 q=1024, 4 frames,
    **2/4 exact_correct, 2/4 exact_mismatch, 0 decode_failed**, FER=0.5.
  - `n4_finite_q1024_f129_simple_pp_osd_1f/`: f≈1.296 n=1024,
    0/1 exact_correct, 1/1 exact_mismatch (OSD-0 finds a valid codeword but
    not Alice's word).
  - `n4_finite_q1024_f129_simple_pp_osd1_1f/`: same point with OSD-1
    top_info=1, still 0/1 exact_correct / 1/1 exact_mismatch.
  - `n4_finite_q1024_f129_simple_pp_osd1_top2_1f/`: OSD-1 top_info=2,
    still 0/1 exact_correct / 1/1 exact_mismatch.
  - `n4_finite_q1024_f129_simple_pp_osd1_top4_1f/`: OSD-1 top_info=4,
    still 0/1 exact_correct / 1/1 exact_mismatch.
  - `n4_finite_q1024_f129_retry_osd_probe.json`: prior-perturbation retries
    combined with OSD-1 top4 also did not recover Alice's codeword.
  - Added `osd_decode_candidates` and checked all OSD-1 single-flip candidate
    codewords (`n4_finite_q1024_f129_simple_pp_osdcand1_1f/`); still no exact
    match at f≈1.296.
  - Added bounded OSD-2 candidate search (`osd_decode_candidates_order2`) and
    tested at f≈1.296 (`n4_finite_q1024_f129_simple_pp_osd2_1f/`): still
    exact_mismatch.
  - Wider OSD-2 probe (`n4_finite_q1024_f129_osd2_wide_probe.json`,
    top_info=4, top_symbols=16, 1531 candidates): still no exact match.
  - PEG seed sweep (`n4_finite_q1024_f129_seed_sweep_summary.json`):
    seeds 2026082028/33/36/37/38 all exact_mismatch; construction seed alone
    does not unlock exact decoding.
  - `n4_finite_q1024_f129_iter50_osd_1f/`: max_iter=50 + OSD still
    exact_mismatch; the failure is not iteration-limited.
  - `n4_finite_q1024_f112_n2048_1f/`: n=2048, m=126, f≈1.119, OSD still
    exact_mismatch; longer block with lower f also does not unlock exact.
  - Improved OSD reliability ordering (max posterior minus second max) and
    retested f≈1.296:
    `n4_finite_q1024_f129_rel_osdcand1_1f/` and
    `n4_finite_q1024_f129_rel_osd2_1f/` still exact_mismatch.
  - `n4_finite_q1024_f129_opt_osd_1f/`: V18-B2 optimized lambda + exact
    two-degree rho at f=1.296, OSD still exact_mismatch.
  - `n4_finite_q1024_f129_osd_4f/`: 4-frame OSD run at f=1.296, 4/4
    exact_mismatch, 0 exact, FER=1.0.
  - Consolidated blocker summary:
    `n4_finite_q1024_f129_blocker_summary.json`.
  - `n4_finite_q1024_r084_osd_8f/`: R=0.84 q=1024 with OSD, 3 exact /
    5 exact_mismatch / 0 decode_failed, FER=0.625.
  - `n4_finite_q1024_f1279_n512_1f/`: n=512, m=36, f≈1.279, OSD still
    exact_mismatch.
  - `n4_finite_q1024_f1279_n128_1f/`: n=128, m=9, f≈1.279, OSD still
    exact_mismatch.
  - Full OSD-1 aggregate summary:
    `n4_full_osd1_summary.json`.
  - **Full OSD-1 exact recovery**:
    `n4_finite_q1024_f1279_full_osd1_n128_probe.json`
    n=128, m=9, f≈1.279; enumerating all single free-variable flips
    (121738 candidates) found Alice's codeword. This is the first exact
    q=1024 f≤1.3 recovery evidence. A second frame
    (`..._full_osd1_n128_probe_seed2050.json`) was not recovered, and two
    additional frames (seeds 2051/2052) were also not recovered. Across four
    n=128 frames, full OSD-1 recovered 1/4 exact (FER=0.75), proving exact
    recovery is possible but not yet reliable. A non-recovered frame
    (seed2050) also failed full OSD-1 + bounded OSD-2
    (`..._full_osd1_plus_osd2_seed2050.json`), and broad OSD-2 probes
    (top20/top4 and top20/top16) also failed
    (`..._osd2_broad_seed2050.json`, `..._osd2_broad16_seed2050.json`).
  - Full OSD-1 at n=64, m=4, f≈1.136 recovered 3/8 frames
    (`..._full_osd1_n64_probe*.json`; seeds 2054/2057/2058 true,
    2055/2056/2059/2062/2063 false), FER=0.625. Prior-retry + full OSD-1
    and broad
    OSD-2 on a
    non-recovered frame also failed
    (`..._retry_full_osd1_n64_seed2055.json`,
    `..._osd2_n64_seed2055.json`). Two n=64 frames with lambda
    `{2:0.7,3:0.3}` both failed full OSD-1
    (`..._full_osd1_n64_lamc_seed2060/61.json`). Broad OSD-2 also failed on
    non-recovered seeds 2056/2059 (`..._osd2_n64_seed2056/59.json`) and
    2062/2063 (`..._osd2_n64_seed2062/63.json`).
    max_iter=50 + full OSD-1 also failed on seed2055
    (`..._full_osd1_iter50_n64_seed2055.json`). Fixed-frame alternate code
    seeds 3001/3002 also failed on seed2055
    (`..._n64_frame2055_codeseed3001/02.json`), as did 3003/3004
    (`..._codeseed3003/04.json`).
- Added a prior-perturbation retry probe (`n4_finite_q1024_r089_retry_probe.json`):
  4 frames x 5 retries at R=0.89 q=1024, 0 successes.
- Added bounded single-symbol and two-symbol OSD-like post-processors to the
  finite executor.
  - `n4_finite_q1024_r089_simple_pp/`: single-symbol post-processor; run
    remained 1/4 exact_correct / 3/4 decode_failed.
  - `n4_finite_q1024_r089_simple_pp2/`: two-symbol bounded OSD-like
    post-processor; a fresh 4-frame R=0.89 run remained 0/4 exact_correct /
    4/4 decode_failed.

## Status correction

- V19 finite executor has been corrected: `exact_mismatch` is reserved for a
  success (syndrome-consistent) but wrong codeword; non-success non-exact
  outcomes are `decode_failed`.  Corrected per-run aggregates are in
  `n6_comparison_v4_corrected_statuses/status_correction.json` and the v4
  comparison table.

## N6 — Three-way comparison

- Evidence: `n6_comparison/comparison_table.csv` and `comparison_summary.json`
  (v1: q=16 proxy); `n6_comparison_v2_q1024/comparison_table.csv` and
  `comparison_summary.json` (v2: includes q=1024 primary);
  `n6_comparison_v3_q1024_rates/comparison_table.csv` + `comparison_summary.json`
  (v3: q=1024 rate tradeoff rows);
  `n6_comparison_v4_corrected_statuses/comparison_table.csv` +
  `comparison_summary.json` + `status_correction.json`
  (v4: corrected statuses; f≤1.3-point f≈1.296 with FER=1.0).
- Leakage decomposition: `n6_comparison_v2_q1024/leakage_decomposition.json`
  - q=16 folded honest full-channel f≈3.016
    (syndrome 1.602 + uncovered 6-MSB public cost 0.057 / H_full 0.550).
  - q=1024 n=128 full-syndrome f≈7.245.
- Binary LDPC MLC baseline imported from existing
  `v19_binary_mlc_prototype_20260816`: f≈4.169, FER=0.
- Nonbinary LDPC q=16 diagnostic row: f≈4.183, FER=0.25.
- Nonbinary LDPC q=1024 diagnostic rows: f≈7.245 (n=128, FER=0); f≈2.912
  (n=256 R≈0.84, FER=0.5 corrected to decode_failed); f≈1.989
  (n=256 R≈0.89); f≈1.296 (n=1024 R≈0.929, FER=1.0 decode_failed).
- Binary Polar MLC is available in the separate release repo
  `D:\Code\HD-QKD_Polar_Release`; this package marks it `not_available` until a
  clean evidence JSON is supplied.

## Constraints honored

- Frozen `src/`, `experiments/`, `tools/`, `results/` untouched.
- New code under `comparison_bench/` only.
- Outputs are additive; no existing evidence overwritten.
- No push.
