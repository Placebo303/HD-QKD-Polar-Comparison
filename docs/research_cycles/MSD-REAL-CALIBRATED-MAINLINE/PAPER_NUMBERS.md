# PAPER_NUMBERS.md — G0=(B) paper numbers freeze (H-2, DECIDE, documentation-only)

> Track: DECIDE (publication/report numbers, user-authorized). Documentation-only
> verification: artifacts read, numbers recomputed in an independent Python
> process, ONE new file written, nothing else modified, no decoders run.
> Branch: `formal-ir-v72p1-addendum-clean`. Date: 2026-10-08.

## Recomputation method (applies to every number below)

- **f formula**: `f = (E_L + 64 + (N*H_A − E_L)*FER) / (N*H_AB)`, TAG = 64 bits,
  `FER = failures/blocks` (point), `undetected` always isolated (never merged).
- **`f_up`** (Wilson-upper f): same formula with `FER` replaced by the Wilson
  upper95 of that row. It is a sensitivity bound, not an estimate.
- **Wilson upper95**: standard Wilson score upper bound, z = 1.96:
  `(p + z²/2n + z·sqrt(p(1−p)/n + z²/4n²)) / (1 + z²/n)`, `p = k/n`.
- **P1 scalars used** (T2-1M, GRAY): `H_A = 9.9976919099`,
  `H_AB = 0.7981344445`.
  Verified against `docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P1_NUMBERS.json`
  (`analysis_rows`, T2-1M GRAY LSB_FIRST: `H_A_bits_per_symbol = 9.997691909893772`,
  `H_A_given_B_bits_per_symbol = 0.798134444535838`; Δ vs task scalars 6.2e-12 /
  3.6e-11 — display rounding only) and consistent with
  `docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P1_TABLE.md`
  (entropy-summary row T2-1M GRAY `H(A|B) = 0.7981344445`).
  Rows carrying their own embedded `H_A`/`H_AB` (S-5, E-1, M5, S-1) were
  recomputed with those embedded full-precision values; T2-1M rows agree with the
  task scalars to display precision.
- **Rounding policy**: recompute-vs-logged Δ ≤ ~1e-10 (10dp scalar rounding) or
  4th-decimal display rounding is recorded as `None (rounding-level)`.
  Anything larger would be a finding (see §10).

## 1. G-5 best row — RA-q5-gap0.08 / margin 3.0 / N=32768

- Artifact: `workspace/g5_bakeoff/g5_20261008/g5_summary.json`, row index 8
  (keys `A_method`, `margin_B`, `N`, `blocks`, `failures`, `undetected`, `E_L`,
  `FER_exact`, `FER_wilson_upper95`, `f_expected`).
- Values: `f = 1.1397810137829194`, `FER = 0/300 = 0.0`, `und = 0`,
  `E_L = 29745.0`, `FER_wilson_upper95 = 0.012643429997735661`, `n = 300`.
- Recompute: `f(29745.0, 32768, 0.0) = 1.1397810138340985` (Δ 5.1e-11);
  `Wilson(0,300) = 0.012643429997735661` (exact); **`f_up = 1.2837769328951099`**.
- Block-level cross-check (`workspace/g5_bakeoff/g5_20261008/blocks_g5.jsonl`,
  keys `A`, `margin`, `n`, `L_A`, `L_B`, `a_ok`, `exact_full`, `undetected`):
  300/300 matching records, `mean L_A = 28542.0`, `mean L_B = 1203.0`
  (deterministic — every block identical), sum `29745.0` ✓, 0 fails, 0 und.
- Evidence type: **synthetic** (bakeoff, B=300/row).
- Discrepancy vs logged: **None** (rounding-level only).

## 2. Polar control — polar-SCL8-0.88 / margin 3.0 / N=32768 + tie arithmetic

- Artifact: same file `workspace/g5_bakeoff/g5_20261008/g5_summary.json`, row
  index 7 (same keys as §1).
- Values: `E_L = 30039.0`, `f = 1.1510224381196021`, `FER = 0/300`, `und = 0`,
  `FER_wilson_upper95 = 0.012643429997735661`, `n = 300`.
- Recompute: `f(30039.0, 32768, 0.0) = 1.151022438171286` (Δ 5.2e-11);
  Wilson exact; **`f_up = 1.2948762270706156`**.
- Block-level: 300/300 records, `mean L_A = 28836.0`, `mean L_B = 1203.0`,
  sum `30039.0` ✓. Level-B disclosure identical to RA (1203.0); the entire gap
  sits in level A: `28836 − 28542 = 294` bits, and
  `294 / (32768 × 0.7981344445) = 0.0112414` ✓ closes the tie arithmetic below.
- Tie arithmetic: `1.1510224381196021 − 1.1397810137829194 =
  0.011241424336682737`; at 3dp `1.151 − 1.140 = 0.011`.
- Evidence type: **synthetic**.
- Discrepancy: **FINDING D1** — the full-precision gap `0.01124` exceeds `0.01`
  (by `0.00124`); the "within 0.01 tie" phrasing is not strictly true at full
  precision (at 2dp both round to a `0.01` gap). Paper must state the gap as
  `0.011` (or `≈0.01` with the exact value) rather than claiming `≤ 0.01`.
  Artifacts themselves are self-consistent; nothing to fix.

## 3. G-6 — two-level chain, real-consistency (35/35, nominal-zero disclaimer)

- Artifact: `workspace/g6_real/g6_20261008/g6_summary.json` (keys `seg`, `N`,
  `m_A`, `m_B`, `blocks`, `failures`, `undetected`, `E_L`, `FER_exact`,
  `FER_wilson_upper95`, `f_expected`); block cross-check
  `workspace/g6_real/g6_20261008/blocks_g6.jsonl` (35 records total ✓).

| seg | N | blocks | E_L (= m_A+m_B) | FER | und | f (logged / recomputed) | Wilson upper95 (logged / recomputed) |
|---|---|---|---|---|---|---|---|
| 4dB | 32768 | 3 | 29745.0 = 28542+1203 | 0/3 | 0 | 1.1397810137829194 / 1.1397810138 | 0.5615060804490177 exact |
| 4dB | 16384 | 7 | 14873.0 = 14271+602 | 0/7 | 0 | 1.1422663627008935 / 1.1422663628 | 0.35433884297520657 exact |
| 10dB | 16384 | 1 | 14873.0 | 0/1 | 0 | 1.1422663627008935 / 1.1422663628 | 0.7934567085261071 exact |
| 0dB | 32768 | 8 | 29745.0 | 0/8 | 0 | 1.1397810137829194 / 1.1397810138 | 0.3244156195108769 exact |
| 0dB | 16384 | 16 | 14873.0 | 0/16 | 0 | 1.1422663627008935 / 1.1422663628 | 0.19361341827271994 exact |

- Skipped row logged as-is: 10dB/N=32768 `skipped: true` (`pairs: 30907`,
  insufficient for one block) — not a measurement.
- Totals recomputed: `3+7+1+8+16 = 35` blocks, `0` failures, `0` undetected.
- `E_L` exact-consistency with synthetic best row: `29745.0`/`14873.0` match the
  §1 block means exactly (including the `m_A`/`m_B` split).
- Block spot-check: 4dB/N=32768 (3 records): mean `L_A+L_B = 29745.0`, 0 fails.
- **Nominal-zero disclaimer (must accompany any citation)**: logged `f` uses the
  `FER = 0` point estimate on tiny per-row `n` (1–16); Wilson uppers span
  `0.19–0.79` and must NOT be used as FER estimates. The FER tail for the paper
  comes from synthetic (G-5 `0/300`, upper `0.0126`).
- Cross-check vs `G6_RESULT.md`: table rows (3/7/1/8/16, `E_L`, `0/n`, `f`
  1.140/1.142) match ✓.
- Evidence type: **real-consistency** (real frames; consistency demo only).
- Discrepancy vs logged: **None**.

## 4. NB F-1 — 4dB-diff main row (f = 1.376, 0/112 + Wilson)

- Artifact: `workspace/f1_oos/f1_20261007/f1_summary.json` (keys `seg`, `arm`,
  `N`, `blocks`, `failures`, `undetected`, `E_u2`, `E_u1`, `E_L`, `FER_exact`,
  `FER_wilson_upper95`, `f_expected`); T2-1M scalars apply to all four rows
  (verified by recompute).
- Main row (4dB/diff): `N = 1024`, `n = 112`, `E_L = 1060.7142857142858`
  (`E_u2 = 1010.7142857142857 + E_u1 = 50.0` ✓ arithmetically),
  `FER = 0/112 = 0.0`, `und = 0`, `f = 1.3761513516455415`,
  recomputed `1.376151351707334` (Δ 6.2e-11);
  `Wilson(0,112) = 0.03316252537948371` (exact);
  **`f_up = 1.7485161656707533`**.
- Block-level (`workspace/f1_oos/f1_20261007/blocks_f1.jsonl`, keys `seg`,
  `arm`, `L_u2`, `L_u1`, `u2_ok`, `exact_full`, `undetected`): 112/112
  4dB-diff records, mean `L_u2+L_u1 = 1060.7142857142858` ✓ exact, 0 fails,
  0 und.
- Companion rows recomputed (same file): 4dB/plugin `f = 1.5835697721291835`
  (recomp Δ 7.1e-11, 2/112, Wilson `0.062781726562021` exact); 0dB/diff
  `f = 1.4214205811112823` (Δ 6.4e-11, 1/260, Wilson `0.021461310995004035`
  exact); 0dB/plugin `f = 2.032002676035956` (Δ 9.2e-11, 15/260, Wilson
  `0.09299462865279463` exact).
- Cross-check vs `F1_RESULT.md`: `1.376 / 1.584 / 1.421 / 2.032` ✓ (point
  display rounding only).
- Evidence type: 4dB rows **real-clean-OOS** (112 superframes never used
  before); 0dB rows **real-retest** (re-test,附测).
- Discrepancy vs logged: **None**.

## 5. NB S-5 full-chain rows — T2-1M/1.5M/2M (1.915 / 1.787 / 1.647)

- Artifact: `workspace/s5_nbfull/s5_20261006/s5_nb_summary.json` (keys `source`,
  `N`, `blocks`, `failures`, `undetected`, `E_u2`, `E_u1`, `E_L`, `FER_exact`,
  `FER_wilson_upper95`, `f_expected`, plus embedded per-row `H_A`/`H_AB`).
  (Task label "D-4" numbers live in this `s5_nb_summary.json` file.)

| source | n | E_L | FER | und | f logged | f recomputed (embedded H) | Wilson (logged/recomp) | f_up recomputed |
|---|---|---|---|---|---|---|---|---|
| T2-1M | 205 | 1192.4878048780488 | 7/205 = 0.03414634146341464 | 0 | 1.9152897638347242 | 1.9152897638347242 exact | 0.06879435521075036 exact | 2.2987479769042536 |
| T2-1.5M | 287 | 1193.6097560975609 | 8/287 = 0.027874564459930314 | 0 | 1.787127289919951 | 1.787127289919951 exact | 0.05403072824819326 exact | 2.0671692585999777 |
| T2-2M | 383 | 1196.6005221932114 | 6/383 = 0.015665796344647518 | 0 | 1.6470703301073069 | 1.6470703301073069 exact | 0.03375218691598122 exact | 1.8391615978113405 |

- Embedded scalars used: T2-1M (`9.997691909893774`, `0.7981344445358383`),
  T2-1.5M (`9.998295501729698`, `0.8249782281516383`), T2-2M
  (`9.998740112976703`, `0.8314077735449491`).
- Block-level decomposition, T2-1M
  (`workspace/s5_nbfull/s5_20261006/blocks_s5_1M.jsonl`, keys `L_u2`, `L_u1`,
  `u1_extra`, `u2_ok`, `exact_full`): 205 records; `mean L_u2 =
  1142.6341463414635` ✓ exact vs `E_u2`; `mean L_u1 + 320/205 u1_extra =
  48.292682926829265 + 1.5609756097560976 = 49.85365853658536` ✓ vs `E_u1`;
  7 fails ✓, 0 und.
- Cross-check vs `S5_RESULT.md`: `1.915 (2.299) / 1.787 (2.067) / 1.647 (1.839)`
  ✓ (`f_up` rounds to the logged `2.2987/2.0672/1.8392`); G-1 gate verdicts
  (1.40 gate MISS on all three rows; valid-wrong 0/205, 0/287, 0/383 MET) as
  logged — counts re-verified for T2-1M (0 undetected in blocks file).
- Evidence type: **real-retest** (VAL/HOLD already exposed; "再检验" per
  `S5_RESULT.md`).
- Discrepancy vs logged: **None**.

## 6. NB S-5 T2-1M row for context (same row as §5, full-symbol口径)

- Values frozen: `f = 1.9152897638347242`, `f_up = 2.2987479769042536`,
  `n = 205`, `FER = 7/205`, `und = 0`.
- Context notes (as logged, not re-adjudicated): full-symbol口径 (R11); proxy
  predicted FER 3–7% / f ~1.9 — T2-1M lands inside; T2-1.5M/2M measured lower
  (favorable-direction prediction miss, recorded in `S5_RESULT.md`).
- Evidence type: **real-retest**.
- Discrepancy: **None**.

## 7. MSD negatives

### 7a. M5 frozen MSD — 52/52 failures

- Artifact: `workspace/m5_realframe/m5_20261006/m5_msd_summary.json` (keys
  `source`, `N`, `blocks`, `failures`, `undetected`, `L_base`, `n_rescue`,
  `E_L`, `FER_exact`, `f_expected`); verdict companion
  `workspace/m5_realframe/m5_20261006/m5_verdicts.json`
  (keys `E_L`, `kept_weighted_penalty_bits`, `f_expected_recomputed`,
  `consistency_p_value`, `consistency_verdict`).
- Totals recomputed: `12 + 17 + 23 = 52` blocks, `52` failures, `und = 0`
  on all rows.
- f recomputed with each row's verdict-file `H_A`/`H_AB`: T2-1M
  `12.53121980684631` exact; T2-1.5M `12.124200870294004` exact; T2-2M
  `12.030975270206467` exact. (`FER = 1.0` ⇒ `f = (N·H_A + 64)/(N·H_AB)`.)
- Cross-check vs `M5_RESULT.md` MSD table (`12.53 / 12.12 / 12.03`,
  INCONSISTENT, p~0) ✓; synthetic band reference `0/300 → 0.0126` matches the
  recomputed `Wilson(0,300)` in §1 ✓.
- Evidence type: **real-consistency** (consistency check; verdict INCONSISTENT).
- Discrepancy vs logged: **None**.

### 7b. E-1 MSD retune best — f = 2.48 (m1200)

- Artifact: `workspace/e1_msdretune/e1_20261007/e1_summary.json` (keys `m1`,
  `N`, `blocks`, `failures`, `undetected`, `E_L`, `FER_exact`,
  `FER_wilson_upper95`, `f_expected`, plus `f_formula`, `H_A`, `H_AB`, `TAG`).

| m1 | E_L | FER | und | f logged | f recomputed | Wilson (logged/recomp) |
|---|---|---|---|---|---|---|
| 600 | 16089.666666666666 | 34/300 = 0.11333333333333333 | 0 | 2.515511009942025 | 2.515511010055862 (Δ 1.1e-10) | 0.15420023806384625 exact |
| 1200 (best) | 16689.666666666668 | 32/300 = 0.10666666666666667 | 0 | 2.481194067840267 | 2.4811940679525106 (Δ 1.1e-10) | 0.14670411773420264 exact |
| 2400 | 17889.666666666668 | 32/300 = 0.10666666666666667 | 0 | 2.5631723459962124 | 2.563172346112137 (Δ 1.2e-10) | 0.14670411773420264 exact |

- `N = 16384`, `n = 300` per row; `f_formula`,
  `H_A = 9.9976919099`, `H_AB = 0.7981344445`, `TAG = 64` as logged in-file.
- Best `f = 2.48119… → 2.48` ✓ (m1200 vs m600 Δ ≈ 0.034, statistical-tie note
  as logged).
- Evidence type: **synthetic** (T2-1M source, 300 blocks/point).
- Discrepancy vs logged: **None** (rounding-level only).

### 7c. S-1 proxy G-0 pattern (MSD plane-1 mass failure replicated in proxy)

- Artifacts: `workspace/s1_proxy/s1_20261006/s1_msd_summary.json` (keys
  `source`, `tier`, `N`, `blocks`, `failures`, `undetected`,
  `valid_wrong_total`, `plane1_failed`, `stage_passed`, `E_L`, `H_A`, `H_AB`,
  `FER_exact`, `f_expected`) and
  `workspace/s1_proxy/s1_20261006/s1_nb_summary.json` (keys `source`, `arm`,
  `tier`, `N`, `blocks`, `failures`, `undetected`, `valid_wrong_nb`,
  `n_rescue`, `u1_mm_total`, `u1_residual_blocks`, `E_L`, `FER_exact`,
  `f_expected`).
- MSD proxy (T2-1M, N=16384, n=100/tier): T1 `100/100` fails, all plane-1
  (`plane1_failed = 100`, `stage_passed = [100,0,…]`), `valid_wrong_total = 0`,
  `und = 0`, `f = 12.53121980684631`; T2 `100/100` fails
  (`plane1_failed = 84`; 16 plane-0 fails), `valid_wrong_total = 0`, `f =
  12.53121980684631`. (G-0 pattern = plane-1 mass failure reproduced; the
  `valid-wrong ≥ 1` G-0 sub-criterion reads `0` in this T2-1M pilot — recorded
  as-logged, no adjudication here.)
- NB proxy (T2-1M, N=1024, n=60/arm/tier): T1 full-symbol FER `36/60` both arms
  (`f ≈ 8.094`); T2 `43/60` both arms (`f ≈ 9.411`); `u1_mm_total = 56`
  (T1) / `77` (T2) per 60 blocks (≈ 0.93–1.28/block); `valid_wrong_nb = 0`.
- Evidence type: **synthetic** (TRAIN-split proxy, pilot T2-1M only).
- Discrepancy vs logged: **None** (values cited as read; no f recompute claimed
  for S-1 rows beyond noting the MSD `f = 12.5312…` equals the M5-T2-1M value
  because `FER = 1.0` collapses the formula to `(N·H_A + 64)/(N·H_AB)`).

## 8. G-1 ternary — H(e) = 0.8032 + closure

- Artifact: `docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/G1_TERNARY.md`
  (table columns `source`, `n`, `P0`, `P+1`, `P−1`, `rest`, `p`, `p−`, `H(e)`,
  `closure`; `H(e) = −Σ q·log2 q` over the three error values).
- T2-1M spot recompute from the logged distribution (`P0 = 0.76243`,
  `P+1 = 0.23619`, `P−1 = 0.001379`, `rest = 0`): closure sum
  `0.76243 + 0.23619 + 0.001379 = 0.999999` ✓; `H(e) = 0.8032` (recomputed
  `0.80316… → 0.8032` ✓ exact at 4dp). TRAIN `n = 315504` as logged.
- Remaining rows recomputed from their logged probabilities: T2-1.5M
  `0.8287` vs logged `0.8288` (see D2); T2-2M `0.8344` ✓; 0dB `0.8187` ✓;
  4dB `0.8026` ✓; 10dB `0.7887` ✓. (`p = P+1 + P−1`, `p−` conditional sign
  shares, and the 1.5M/2M sign-flip note verified arithmetically against the
  table, e.g. T2-1M `p = 0.23757`, `p− = 0.00580` ✓.)
- `lag-1 = 0.0004` (memoryless) and the per-pair exact-decomposition claims are
  recorded as logged in `G1_TERNARY.md` (they rest on ordered TRAIN pair arrays;
  no independent recompute of those two diagnostics was performed in this
  documentation-only pass — the H/closure arithmetic above is the spot-check).
- Evidence type: TRAIN-descriptive (accepted R1 TRAIN pairs, zero-decode;
  does not fit the decoder-evidence bins — labeled explicitly).
- Discrepancy: **D2 (rounding-level, explained)** — T2-1.5M `0.8288` vs `0.8287`
  recomputed from 5dp-rounded probabilities (logged probs sum to `1.000003`;
  probability-rounding sensitivity at this `p` is ~1e-4, fully accounting for
  the last-digit difference; the underlying full-precision H rounds to
  `0.8288`). No artifact edit; paper keeps `0.8288`.

## 9. R14 margins for the best row (ideal vs actual per level)

- Artifact: ideal values from `workspace/g5_bakeoff/g5_20261008/g5_summary.json`
  (keys `R14_ideal_A`, `R14_ideal_B`, identical on all 12 rows);
  actual values = §1 block means (deterministic disclosure).
- `R14_ideal_A = 25920.35083735033` bits/block (`0.79092` b/sym);
  `R14_ideal_B = 400.9290507185417` bits/block (`0.01224` b/sym).
- Actual (RA-q5-gap0.08/m3.0/N=32768): level A `28542.0`, level B `1203.0`.
- Margins: A `28542.0 − 25920.35083735033 = +2621.64916264967` bits (`+10.11%`,
  actual `0.87103` b/sym); B `1203.0 − 400.9290507185417 = +802.0709492814583`
  bits (`+200.06%`, actual `0.03671` b/sym).
- Interpretation for the paper: level-A operates ~10% above its ideal disclosure
  target; level-B disclosure is ~3× its ideal target in relative terms but only
  `802` bits absolute (≈ `0.025` b/sym), i.e. the B-level absolute overhead is
  small — the paper should quote both absolute and relative margins.
- Evidence type: ideal = analytic (P1-conditional-entropy targets, as logged);
  actual = **synthetic** measurement (300 deterministic blocks).
- Discrepancy vs logged: **None** (ideals read verbatim; actuals recomputed
  from blocks).

## 10. Discrepancy register (findings, not fixes — no artifact edited)

- **D1 (paper-wording finding)**: §2 — full-precision RA-vs-Polar gap is
  `0.011241424336682737`, which exceeds `0.01` by `0.00124`. The skeleton phrase
  "约 0.01 内" / "within 0.01 tie" is not strictly true at full precision.
  Required paper handling: quote the gap as `0.011` (3dp: `1.151 − 1.140`) and
  phrase the tie as approximate (e.g. "≈0.01, exact 0.011"), not as `≤ 0.01`.
- **D2 (rounding-level, explained)**: §8 — G-1 T2-1.5M `H(e)` recomputes to
  `0.8287` from the 5dp-rounded table probabilities vs logged `0.8288`;
  fully explained by probability display rounding (sensitivity ~1e-4). Keep the
  logged `0.8288`. No further action.
- **Otherwise: none.** Every other recompute matches its logged value exactly
  (rows with embedded full-precision H) or to ≤ ~1.2e-10 (rows using the
  10dp task scalars — display rounding of `H_A`/`H_AB` only). Wilson bounds
  match exactly in all 17 checked (k, n) pairs. Block-count totals (G-6: 35,
  M5-MSD: 52) and block-mean cross-checks (G-5 best/control, G-6 4dB-32768,
  F-1 4dB-diff, S-5 T2-1M layer split) all reconcile.
- Already-logged cross-checks: `G6_RESULT.md`, `F1_RESULT.md`, `S5_RESULT.md`
  (incl. `2.2987/2.0672/1.8392` footnote), `M5_RESULT.md`, `P1_TABLE.md`,
  `PAPER_SKELETON.md` §待填数字清单 — all consistent with the frozen values
  above except D1's wording caveat.
