# G1 L1 estimator discriminator R1 — evidence report

- repo: `HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`
- prereg: `G1_L1_ESTIMATOR_DISCRIMINATOR_PREREG_R1.md` (committed alone as
  `f0e4a1c` before any score or call); R2 acceptance `247f8adc` before it.
- evidence root:
  `workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/` (3 scripts, 3 scalar
  evidence JSONs, manifest, command log; no raw rows/symbols/beliefs).
- terminal class (exactly one): **`L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64`**
- final gate: **`D5_ROUTE_STOP_REVIEW`**

## 1. Prereg adherence

| Prereg item | Outcome |
|---|---|
| Primary endpoint held-out CAL L1 NLL, ≤3 estimators, zero VAL | done; E1/E2/E3 only; `val_touched=false`, 262144 CAL rows asserted |
| Decoder endpoints exact/syndrome/iters/nonfinite/wall/RSS, independent exact+syndrome recompute | done; 0 flag disagreements, 0 nonfinite in 75 calls |
| Useful-n64 rule (`m<64` only; `m=64` never counts) | applied; square partials recorded but never claimed |
| Paired seeds `2026090600..03`, square seed `2026090801`, 4 blocks/point | done; identical seeds across estimators |
| Sparse bracket disclosures, one axis per control | `{49,59,64}` / rate-matched `{98,118,128}` / `{196,236,256}`; matrix/decoder/max_iter fixed |
| Scaling only on n64-fail; stop at first nonzero-rate recovery | n64 0/4 everywhere → 128 → 256; no recovery; 256 arm completed, nothing further spent |
| Budgets ≤8h / ≤1500 calls / 120s watchdog / <2GiB | 75 calls, max call 2.41s, peak RSS 182894592 B, total wall ~78s |
| No decoder-outcome estimator selection | E2 frozen as winner from CAL before any new decoder call |
| One disclosed deviation (§2) | E2 blocks under E1 joint law (prior-only single axis; E2 defines no joint law) |

## 2. Estimator contracts and formulas

- E1: `P(a|b) = (counts + lam*·p_global)/(n_b + lam*)`, `lam* =
  137.3823795883264`, marginalized via `marginalize_f_to_p1`. No selection.
- E2: aggregated `counts_L1[B,U1]`, `P(u1|b) = (counts_L1 + kap·p1_global) /
  (n_b + kap)`, `kap* = 62.10169418915616` minimizing mean held-out L1 NLL
  over grid30 `logspace(-2,3)` (unanimous across all 4 folds).
- E3: same statistic as E2 at frozen `kap = lam*` (W4a-C3 P1 component).
- Mathematical identity found: E1 ≡ E3 to machine precision on every
  endpoint (held-out means bit-identical per fold). Proof: joint backoff is
  linear in counts, so marginalizing over U2 after smoothing equals
  aggregating over U2 before smoothing at equal strength. The
  sufficient-statistic axis (E1-vs-E3) collapses; the live contrast is
  selection strength only (E2 `kap*≈62` vs frozen `lam*≈137`).
- Deviation disclosed: decoder blocks for both estimators were sampled
  under the E1 joint law (the D4-family population both estimators
  describe); only the L1 prior fed to the decoder varied. E2 is L1-only
  and defines no joint law; same-population prior-only contrast is the
  single-axis design, coherent with the Phase C mass pairing.

## 3. CAL endpoint table (held-out L1 NLL, bits; lower wins)

| fold | E1 | E2 | E3 | E2 kap |
|---|---|---|---|---|
| F0 | 3.818215 | 3.775910 | 3.818215 | 62.10169418915616 |
| F1 | 3.819244 | 3.777093 | 3.819244 | 62.10169418915616 |
| F2 | 3.802897 | 3.757587 | 3.802897 | 62.10169418915616 |
| F3 | 3.818612 | 3.776014 | 3.818612 | 62.10169418915616 |
| mean ± SE | 3.814742 ± 0.00395 | **3.771651 ± 0.00470** | 3.814742 ± 0.00395 | unanimous |

Winner E2 (Δ = 0.043 bits ≈ 9 SE, outside the 0.01 tie band).
CAL-info check: `5.0 − 3.771651 = 1.228 ≫ 2·SE` → information present
(not `CAL_L1_INFORMATION_INSUFFICIENT`).

Full-counts diagnostics: E1/E3 CE_L1 4.2867 / MI 0.7089 / prior fraction
0.349 / truth mass (paired E1-law, floored) 0.0960; E2 CE_L1 4.0062 / MI
0.9896 / prior fraction 0.195 / truth mass 0.1110. Support identical
(column 198/256/325). E2 lifts mass by only +0.015, far below the R2 L2
pass-region mass (~0.28; fail region 0.22–0.24).

## 4. Paired decoder results (exact+syndrome recomputed; success = both)

- n64 (25 calls, S0 pass): E2 `{49: 0/4, 59: 0/4, sq: 0/4}`, E1 `{49: 0/4,
  59: 0/4, sq: 0/4}`. All saturate at 90 iters. No 2/4 ambiguity → no
  MIXED extension. Estimator axis changes no outcome (identical per block).
- n128 (25 calls, S0 pass): nonzero-rate 0/4 everywhere both estimators;
  square 1/4 (seed `2026090601`, both estimators identically).
- n256 (25 calls, S0 pass): nonzero-rate 0/4 everywhere both estimators;
  square 2/4 (seeds `2026090601/02`, both estimators identically).
- Isolated (never success): n256 m236 seed `2026090601` decoded
  syndrome-ok without exact recovery under both estimators (13 iters) —
  retained as a development-only undetected-type event, not counted.

## 5. Resources

75/1500 decoder calls; max per-call wall 2.41s (watchdog 120s, 0
violations); peak RSS 182894592 B (<2GiB); total experiment wall ~78s of
8h. Four-file D5 suite: **259 passed, 0 failed** (60.05s; includes both D4
30-test and D4R2 32-test audit files, removing the 227/229 ambiguity).

## 6. Terminal class and counterevidence

**`L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64`**: CAL holds real L1
information (E2 held-out 3.77 bits, MI 0.99), yet honest estimators fail
through square disclosure at n64 (0/4 at every point including square),
and development scaling to 128/256 restores only zero-rate square
partials (1/4, 2/4) with every nonzero-rate point at 0/4. The failure is
the decoder's BP threshold at these truth masses (~0.10–0.15, vs ~0.28
needed), not absent CAL information and not smoothing misapplication
(E1≡E3; E2 honestly selected).
Counterevidence recorded: square partials grow monotonically with width
(0/4 → 1/4 → 2/4), so signal strength is width-responsive but never
reaches a nonzero rate ≤256; S0 passes at every width (matrix/decoder
healthy with signal); the E2 mass lift is real but an order of magnitude
too small to matter.

## 7. Implementation and tests

No code justified (not recoverable → Phase E: no OpenSpec, no
layered-prior candidate, production wiring untouched, old R2 candidate
preserved as-is). No production file changed; the four-file suite result
above is milestone hygiene only.

## 8. One route recommendation

Route-stop: close the n64 two-layer L1-recovery line (estimator
refinement cannot cross this decoder's threshold: the honest optimum
`kap*≈62` is already selected and still 0/4 everywhere) and do not pursue
block scaling further (n256 fails at every nonzero rate; larger blocks are
out of D5 scope and show only zero-rate response). No G2 is opened or
authorized. Any successor is a new decoder/matrix proposal under a fresh
change — not estimator, disclosure, or scaling work.
