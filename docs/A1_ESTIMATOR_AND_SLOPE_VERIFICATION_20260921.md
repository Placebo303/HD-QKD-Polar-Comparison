# A1 Estimator (S1) and f_eff Slope (A4) Verification — 2026-09-21 (read-only + arithmetic)

> Read-only verification. No `.ttbin` opened, no data parsed/loaded, no pipeline/decoder executed,
> no commit/push, nothing under `workspace/` modified. All arithmetic via `.venv/bin/python`
> (inference bounds explicitly labeled). One deliverable file per tasking.

## T1 — S1 vs the actual code (VERBATIM QUOTES)

**Estimator** (`comparison_bench/src/comparison_bench/cli/p3_census_a1.py`, lines 94–128).
`h_full_f03(N_ab)` builds the plug-in **conditional** entropy by the chain rule over the
F03 bijection `a=(u1,u2)`, `u1=a>>5`, `u2=a&31` (lines 104–105), weighting by the empirical
`p_b` (line 103: `p_b = (N.sum(axis=0) / tot)`):

- H_L1 loop (lines 106–113): `H1 += p_b[b] * float(-np.sum(pu1 * np.log2(pu1)))`
- H_L2 loop (lines 114–127): `H2 += p_b[b] * s * float(-np.sum(pu2 * np.log2(pu2)))`
- line 128: `return float(H1), float(H2), float(H1 + H2)`

So `H_L1 + H_L2` is algebraically the plug-in conditional entropy `Ĥ(A|B) = Ĥ(A,B) − Ĥ(B)`
(the grouped chain rule sums to the same value as the flat conditional plug-in, since
`(u1,u2)` is a bijection of `a`). The review's "H(A|B) = H_L1 + H_L2" premise is correct.

**MM correction** (lines 344–349, TRAIN pool only):

```
344:     N_ab = np.bincount(as_[tr_idx] * 1024 + bs[tr_idx],
345:                        minlength=1024 * 1024).reshape(1024, 1024).astype(np.float64)
346:     N = int(N_ab.sum())
347:     K = int(np.count_nonzero(N_ab))
348:     H1, H2, Hf = h_full_f03(N_ab)
349:     mm = (K - 1) / (2 * N * math.log(2)) if N > 0 else None
```

`K` is the **joint** support `K_AB` (nonzero cells of the 1024×1024 TRAIN `N_ab`);
`N` is the TRAIN pair count. Module docstring (lines 25–28) freezes exactly this:
`Miller-Madow (K-1)/(2N·ln2)` — a single joint `K`, no marginal term.

**`K_B` is computed nowhere.** Grep over the file for `K_B|Kb|p_b|marginal|count_nonzero`
hits only: transient `p_b` inside `h_full_f03` (line 103, used for weighting, never
returned), transient column sums (lines 100, 359–361 for the hold-NLL `Pagb`), and the
joint `K` (line 347). No occupied-B count, no marginal histogram, no per-B counts
leave the function.

**Persisted per-dataset JSON** (lines 350–356; key inventory of all three
`workspace/p3_census_3954637c/T2-*.json` confirms — 74 keys each, enumerated):

```
350:     rec["support_cells"] = K
...
352:     rec["H_L1"] = H1
353:     rec["H_L2"] = H2
354:     rec["H_full_plug"] = Hf
355:     rec["H_full_MM"] = (Hf + mm) if mm is not None else None
356:     rec["MM_correction"] = mm
```

Persisted: `support_cells` (= K_AB on TRAIN), `n_pairs_N` (FULL-frame pairs, not the
TRAIN N used in line 349), `H_L1/H_L2/H_full_plug/H_full_MM/MM_correction`, holdout
scalars, bootstrap CI, `per_frame_weight_hist` (mismatch counts), `block_Hfull_series`.
**`K_B`, the B marginal `p_b`, per-B counts, and `N_ab` are NOT persisted** (consistent
with `docs/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md` T2: directory-wide grep for
`counts_ab|joint|gamma|N_ab` returns zero matches).

**T1 verdict: review characterization CORRECT.** The plug-in is a conditional entropy
but the added MM term is the *joint*-entropy correction `(K_AB−1)/(2N·ln2)`. To first
order the conditional plug-in `Ĥ(A,B)−Ĥ(B)` carries bias `(K_AB−K_B)/(2N·ln2)` nats
(Miller–Madow biases subtract: joint `(K_AB−1)` minus marginal `(K_B−1)`), so the code
over-corrects by exactly `(K_B−1)/(2N·ln2) ≥ 0`. The review's deterministic example
holds: 4 deterministic A=B categories ⇒ `K_AB = K_B = 4`, true first-order correction
0, code adds `3/(2N·ln2) > 0`. (Grouping into L1/L2 levels does not change the
first-order count — the sum is the same plug-in functional.)

## T2 — Bias magnitude (persisted numbers + labeled inference)

Persisted TRAIN-joint support and recovered TRAIN N
(`N = (K−1)/(2·MM·ln2)` inverted exactly from persisted scalars; note the MM
denominator is TRAIN N, **not** `n_pairs_N`):

| source | K_AB (`support_cells`) | N_full (`n_pairs_N`) | N_train (recovered) | applied MM |
|---|---|---|---|---|
| T2-1M | 2395 | 525831 | 315504.0 | +0.0054734836 |
| T2-1.5M | 2439 | 735780 | 441487.0 | +0.0039834588 |
| T2-2M | 2597 | 982182 | 589461.0 | +0.0031768313 |

(N_train ≈ 60% of N_full in each case, consistent with the 60/20/20 frame split.)

**`K_B` is NOT recoverable** from anything persisted (see T1 key inventory). Correct
conditional correction = applied − over, over `= (K_B−1)/(2N·ln2)`. Unit over per
`K_B−1`: 1M `2.2863e-06`, 1.5M `1.6339e-06`, 2M `1.2237e-06` bits.

Range over `K_B ∈ [1, 1024]` (B alphabet size caps `K_B ≤ 1024`; **plausible value
≈1024 is INFERENCE, not fact** — rationale: N_train ≈ 3–6×10⁵ pairs over 1024 B-bins
gives ~300–580 pairs/expected bin under near-uniform Bob time-bins, so empty B-bins
are implausible; hold-uncovered pairs are tiny, 91/105130, 109/147141, 118/196458,
consistent with dense B support — but uniformity is assumed, not measured):

| source | over range (bits) | H_corr range (persisted → min) | max-over in CI units |
|---|---|---|---|
| T2-1M | [0, 0.002339] | 0.80360793 → 0.80126869 | 0.82σ (CI_hw 0.00284610) |
| T2-1.5M | [0, 0.001672] | 0.82896169 → 0.82729018 | 0.76σ (CI_hw 0.00220976) |
| T2-2M | [0, 0.001252] | 0.83458460 → 0.83333270 | 0.65σ (CI_hw 0.00193486) |

**Direction:** over-correction biases `H_full` UP ⇒ `content = 1024·H` UP ⇒
`f = (5m+64)/content` DOWN (**optimistic**, as the review states) ⇒ `m_max` UP
(optimistic). Correcting moves every f UP and every m_max DOWN-or-flat.

**Could the out-of-box verdicts flip?** (`DESIGN_POINT_ARITHMETIC.md` verdicts:
1M OUT@208 / IN@200, 1.5M INDETERMINATE@208, 2M IN@208.)

- T2-1M@208: f = 1.341606 → 1.345522 at max over. Stays OUT (more OUT). No flip.
- T2-1M@200: f = 1.292997 → 1.296771 at max over. Stays IN (≤1.3). No flip of the
  IN/OUT verdict — **but `m_max` 201 → 200 for any `K_B ≥ ~253`**
  (201 needs H ≥ 1069/1331.2 = 0.8030334; budget 0.0005746 bits = 251 `K_B−1` units),
  so under the plausible `K_B ≈ 1024` the published `m_max = 201` ticks down to 200.
- T2-1.5M@208: f = 1.300573 → 1.303200 at max over. Nominally further above 1.3,
  but the shortfall-vs-threshold gap (0.002037) remains **inside** CI_hw (0.00221,
  ratio 0.92σ) — verdict stays **INDETERMINATE** even at max plausible over. No flip.
  `m_max` stays 207 across the whole range.
- T2-2M@208: f = 1.291810 → 1.293751 at max over. Stays IN with margin. `m_max`
  stays 209. No flip.

Bottom line for T2: **no IN↔OUT verdict flips** anywhere in the admissible range;
the only verdict-adjacent movement is 1M `m_max` 201→200 (conditional on the
inferred, unmeasured `K_B ≳ 253`) and 1.5M@208 drifting toward-but-not-into OUT.

## T3 — What a re-run must persist

To make the conditional MM correction auditable **without changing the frozen
estimator**, persist per dataset (TRAIN pool, same split realization):

1. **Minimum (one integer): `K_B_train`** = number of occupied B columns in TRAIN
   `N_ab` (`int((N_ab.sum(axis=0) > 0).sum())`). Together with already-persisted
   `K_AB` and recoverable TRAIN `N`, this fixes the correct correction exactly:
   `(K_AB − K_B)/(2N·ln2)`.
2. Recommended: the full B marginal (`p_b`, 1024 floats) — enables percentile/
   occupancy cross-checks of the `K_B ≈ 1024` inference above.
3. Ideal: the sparse TRAIN `N_ab` (or per-column counts) — also unblocks the X1
   1M/1.5M bundles (`X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md` T2–T4).

**Yes, this requires a new `.ttbin` read** (DECIDE track, Pre-EXECUTE + explicit
authorization): the A1 census kept only summary scalars; `N_ab` was in-memory only
(`p3_census_a1.py:344`, `json.dump` at 309/502/547 writes summaries). Cost precedent
per the X1 assessment: histogram-only pass ≈ **5–15 min for both sources**
(read ~0.5 s + §3A align compute ~1–2 min + pairing/framing/bincount minutes +
numpy factorization seconds; the 200-resample bootstrap that dominated the
687.6 s/1053.1 s full-census walls is skippable for a `K_B`-only pass). A `K_B`-only
pass is the cheapest variant (one integer per source plus the already-frozen
pairing path); bundle-grade persistence costs the same read.

## T4 — A4 arithmetic (full-precision persisted H, `.venv/bin/python`)

Conventions: (i) frozen fixed slope 4.785675; (ii) `slope_arm = (5120−5m)/(1024·H)`;
(iii) all-attempts-charged. FER = 0.025 throughout.

**Review's F202 example REPRODUCED EXACTLY** (to 6 dp: 1.379401 / 1.380281 / 1.409898)
on the **nominal/anchor basis** `1024·H = 852.544` (i.e. `H = 0.8325625`,
the frozen `ANCHOR_H_FULL = 0.83256272` basis from `F_EFF_ACCOUNTING_NOTE §4`,
**not** any source's measured corrected H):

| m (nominal H) | f_super | slope_arm | (i) fixed | (ii) arm-slope | (iii) leak+FER·n |
|---|---|---|---|---|---|
| 199 | 1.242165 | 4.838460 | 1.361807 | 1.363126 | 1.392304 |
| 200 | 1.248029 | 4.832595 | 1.367671 | 1.368844 | 1.398168 |
| **202** | **1.259759** | **4.820866** | **1.379401** | **1.380281** | **1.409898** |
| 208 | 1.294948 | 4.785677 | 1.414590 | 1.414590 | 1.445087 |

**Which H the review used:** the nominal 2M-family anchor basis (852.544 b), as in
`F_EFF_ACCOUNTING_NOTE §4` and the b2f/b2g gate-(b) denominators — not 1M/1.5M/2M
measured corrected H (822.89/848.86/854.61 b). Note m=208 `slope_arm = 4.785677 ≈
4.785675`: the frozen slope **is** the m=208 arm slope on nominal H (exact to rounding).

**Transcription flag (task text vs review number):** the task's parenthetical
"(iii) ⇒ `f_eff = (5m+64)/((1−FER)·1024·H)`" evaluates to **1.292061** at F202, NOT
the review's 1.409898. The review's 1.409898 corresponds to
`f_eff = ((5m+64) + FER·5120)/(1024·H)` = (1074+128)/852.544 — i.e. failed frames
charged full `n = 5120` bits on top of full disclosure, equivalently
`net = 5120 − f_eff·content` with `net = (1−FER)·5120 − (5m+64)`. The task arrow
renormalizes content to kept frames instead; the table above uses the form that
reproduces the review's number. The ≤0.000001 residuals on all three review figures
confirm the match.

Per-(source own corrected H, m) table (same three variants):

| source (own H_corr) | m | f_super | slope_arm | (i) fixed | (ii) arm-slope | (iii) |
|---|---|---|---|---|---|---|
| T2-1M (0.80360793) | 199 | 1.286921 | 5.012793 | 1.406563 | 1.412241 | 1.442469 |
| | 200 | 1.292997 | 5.006717 | 1.412639 | 1.418165 | 1.448545 |
| | 202 | 1.305149 | 4.994565 | 1.424791 | 1.430013 | 1.460698 |
| | 208 | 1.341606 | 4.958108 | 1.461248 | 1.465558 | 1.497154 |
| T2-1.5M (0.82896169) | 199 | 1.247560 | 4.859477 | 1.367202 | 1.369047 | 1.398351 |
| | 200 | 1.253451 | 4.853587 | 1.373092 | 1.374790 | 1.404242 |
| | 202 | 1.265231 | 4.841806 | 1.384873 | 1.386276 | 1.416022 |
| | 208 | 1.300573 | 4.806465 | 1.420215 | 1.420734 | 1.451364 |
| T2-2M (0.83458460) | 199 | 1.239155 | 4.826737 | 1.358797 | 1.359823 | 1.388930 |
| | 200 | 1.245006 | 4.820886 | 1.364647 | 1.365528 | 1.394781 |
| | 202 | 1.256707 | 4.809185 | 1.376349 | 1.376936 | 1.406482 |
| | 208 | 1.291810 | 4.774082 | 1.411452 | 1.411162 | 1.441585 |

Fixed-vs-arm-slope gap at F202/nominal is **0.000880** (1.379401 vs 1.380281);
largest in-table gap is 1M@199, 0.005678 — all immaterial against the 1.3 gate
(no conclusion changes under either slope convention).

## T5 — What the repo actually froze (quotes)

`F_EFF_ACCOUNTING_NOTE_20260921.md`:

- §4 (line 24): "`slope = (5120−1040)/852.544 = 4.7857`" — the m=208 numerator
  (1040 = 5·208), frozen as a **constant**.
- §5 (lines 37–40): "Any arm with **FER > 0** must be reported with **BOTH** numbers:
  gate-(b) `f_super` (success-frame) and `f_eff = f_super + 4.7857·FER` (FER-aware)."
  and "**1.294947 (or 1.259759) must NEVER be quoted as `f_eff`.**"

`B2F_RESULT_20260921.md` amendment (lines 57–62, per BFR-3/GBR-2):

- "The previously stated **f_eff = 1.4146** for b2f F202 (6/240) is **WRONG**: it was
  computed on the **m=208 basis** (`1.294947 + 4.7857×(6/240) = 1.4146`) instead of the
  **m=202 arm's OWN** f_super." … "Correct value … `f_super(m=202) = 1074/852.544 =
  1.259759` ⇒ **f_eff = 1.259759 + 4.7857×(6/240) = 1.259759 + 0.119643 = 1.3794**."
- "Per-arm basis rule (standing): each arm's f_eff uses **that arm's OWN**
  `f_super = (5m+64)/852.544` (m=202 → 1.259759; m=208 → 1.294947) — never a sibling
  arm's or a different-m basis."

`B2G_RESULT_20260921.md` GBR-1 (lines 59–62) applies the identical rule to b2g F202
(4/240): "**`f_eff = 1.259759 + 4.7857×(4/240) = 1.259759 + 0.079762 = 1.3395`**."

**T5 verdict: A4 is a RE-RAISE of a settled convention, not a new finding.**
The frozen convention is explicit and already corrected once in exactly the
direction the review pushes: **slope FIXED at the m=208 value 4.785675 for all arms;
`f_super` per-arm OWN-m basis; gate-(b) stays a success-frame quantity.** The review's
first point (slope_arm varies with m) is arithmetically true but was knowingly frozen
away — residual effect ≤ ~0.001–0.006 in f_eff, gate-irrelevant. The review's second
point (all-attempts-charged contract) is a counterfactual contract the repo never
adopted; frozen net accounting is the Müller-Eq.(13) form (`F_EFF_NOTE §3`, failed
frames at full-frame `n` bits). Genuine-but-minor residue (recorded, not fixed here):
the note's "mathematically equivalent" claim is approximate — Eq.(13)-implied slope
`(5120−1104)/852.544 = 4.7106` differs from frozen 4.7857 by ~1.6% (≈0.0019 in f_eff
at FER=0.025); and the review's (iii) exceeds the Eq.(13) form by ~0.003 at F202
(1.409898 vs 1.412759) because it charges disclosure in full rather than pro-rated.
Neither affects any PASS/FAIL or out-of-box verdict.

## Bottom line

- **S1 CONFIRMED (wrong estimand for the MM correction).** Code adds joint correction
  `(K_AB−1)/(2N·ln2)` (`p3_census_a1.py:349`, `K` = joint support per line 347) to a
  conditional plug-in (`h_full_f03`, lines 94–128); correct first-order term is
  `(K_AB−K_B)/(2N·ln2)`. **Bias direction: optimistic** (H up ⇒ f down ⇒ m_max up).
  **Cannot be recomputed without new `.ttbin` reads: `K_B` is neither computed nor
  persisted** (no marginal, no per-B counts, no `N_ab` in any of the 3 JSONs).
- **Bias magnitude is sub-CI but verdict-adjacent:** max plausible over
  0.002339/0.001672/0.001252 bits (0.82σ/0.76σ/0.65σ). **No IN↔OUT flip** in range:
  1M stays OUT@208 and IN@200; 1.5M stays INDETERMINATE@208 (0.92σ at max over);
  2M stays IN@208. Only movement: 1M `m_max` 201→200 if `K_B ≳ 253` (plausible but
  INFERENCE).
- **A4 is already settled — re-raise, not a new finding.** Frozen convention quote:
  "`f_eff = f_super + 4.7857·FER`" with "**that arm's OWN** `f_super = (5m+64)/852.544`"
  (`F_EFF_ACCOUNTING_NOTE §5`; `B2F_RESULT` GBR-2 amendment; `B2G_RESULT` GBR-1).
  Review's F202 triple verified exactly on the nominal 852.544 basis; fixed-vs-arm
  slope gap (0.0009) is gate-irrelevant.
- **Re-run cost:** DECIDE-track histogram-only (or `K_B`-only) pass over the 1M + 1.5M
  (+2M control) base members; precedent estimate **~5–15 min total**, plus mandatory
  Pre-EXECUTE + explicit authorization. Minimum new artifact: one integer `K_B_train`
  per source (recommended: + `p_b` vector; ideal: sparse `N_ab`, which also unblocks X1).
