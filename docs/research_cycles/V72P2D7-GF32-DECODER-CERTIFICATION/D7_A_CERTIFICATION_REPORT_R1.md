# D7-A certification report R1

- Baseline HEAD `dfab1ed8` (provenance); closeout HEAD per §8 return.
- Scope: historical `decode_row_layered_fftqspa` + GF32 tables + syndrome +
  FFT check update + `final_beliefs` + D5 bridge (`_run_layered_block`,
  `app_fed_l2_prior`). Zero production changes (no trace hook needed:
  `max_iter=1,2,3` beliefs sufficient, `iterations` matched `k` exactly).
- Calls: tiny synthetic in-memory correctness-unit calls only. No Model-F,
  CAL/VAL, real/raw, VOID contents, `--phase`, R1d, G1, G2.

## Findings

1. **Arithmetic**: oracle tables (bitwise poly-37 mult) elementwise-equal to
   production `_get_gf32_tables` (1024/1024 mul, 1024/1024 add, 31/31 inv).
   Spot identities (unit, inverse, commutativity, distributivity) hold.
2. **Check update** (production FFT vs independent direct-SP enumeration):
   max-abs per family — deg2/ordinary 2.1e-17, deg2/skewed 3.3e-16,
   deg3/ordinary 2.1e-17, deg3/skewed 3.3e-16. Full multiplier sweep
   (1,c)×{0,5,17,31}×{ordinary,skewed} + all-32 skewed peaks + deg-3 triples
   {(1,1,1),(1,2,3),(2,7,13),(1,13,29)}: all ≤ 1e-10, no failing tuple.
3. **Coefficient/syndrome direction**: negative controls discriminate
   (wrong-direction err and wrong-shift err both > 1e-6 on the (3,7)/syn-17
   skewed fixture), so the ≤3.3e-16 match is not vacuous.
4. **Tree posteriors** (softmaxed production beliefs vs exact enumeration):
   single-deg2 3.5e-17 / 6.7e-16, single-deg3 4.4e-16, two-check chain
   1.7e-16. All ≤ 1e-10. MAP equality held wherever compared (secondary).
5. **Loopy per-sweep** (matched same-schedule recurrence, never BP-vs-MAP):
   3-var cycle sweeps 1/2/3 → 1.2e-15 / 9.1e-14 / 7.1e-13;
   4-var/deg-3 loopy sweeps → 1.2e-16 / 2.4e-16 / 4.3e-16. All ≤ 1e-10.
   The cycle-3 growth across sweeps is floating-point path divergence
   (FWHT vs enumeration), not algorithmic; noted, non-blocking.
6. **Iteration convention**: production `iterations` == reference sweep count
   in every dynamics fixture; `iterations=0` early-return path verified
   (returns floored log-priors, documented convention, not a posterior).
7. **`final_beliefs` + L1→L2**: established log-domain from code (log-prior
   init + additive log updates; rows do not sum to 1). `_softmax_rows`
   therefore yields the normalized posterior — no double-exponentiation.
   `softmax(log p) == p` to 1.2e-12; `app_fed_l2_prior` matches explicit
   `q @ P` einsum to ≤1e-12 with positivity/normalization; `_run_layered_block`
   verified with fake decode_fn on both the softmax path (L2 prior exactly
   the softmaxed beliefs @ P) and the absent-belief uniform fallback.
   Cosmetic only: the `_softmax_rows(bel) if ... else _softmax_rows(bel)`
   ternary is redundant (both branches identical); behavior correct.

## Verdict

`D7_A_DECODER_CERTIFICATION_PASS`. No counterexample. No production patch.
Next route: `D7_B_EASY_REGIME_PACKET_FREEZE` readiness only — D7-B execution,
R1d, G1, G2 all unauthorized.

## Tests (literal)

- New: `test_v72p2d7_gf32_decoder_certification.py` — 14/14 pass.
- Related: `test_v35_algorithm_development.py` +
  `test_v72p2d5_gf32_rate_mother.py` — combined 204/204 pass with D7-A file.
- `test_v72p2d6_gf32_graph_mother.py` + `..._r1d.py` +
  `test_nonbinary_field.py` — 88 pass, 1 pre-existing failure:
  `test_qldpc_reference_source_is_not_mutated` (SHA pin vs CRLF-churned
  unrelated dirty file; both files uncommitted before D7-A, untouched by
  D7-A; non-blocking, no scope change).
