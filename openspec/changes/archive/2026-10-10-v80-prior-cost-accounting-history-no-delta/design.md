# V80 Prior-Cost Accounting — Design

Sources: `docs/V80_BASELINE_20260921.md` (§§0.1/0.2/2–5/7; THE planning authority),
`docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md` ([DEC] §§A–E),
`docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` (estimator/slope verification),
`docs/PRIOR_COST_CLAIM_REVIEW_20260921.md` ([REV] §§1–6), `docs/SECURITY_MODEL.md`
(prior-term absence), `AGENTS.md` §1.2/§3/§6/§10.3.
Condensation + governance promotion only; no new numbers beyond restatement, all marked
to source or as pending recompute. `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` was ABSENT
at drafting time — corrected `N_req` values are baseline-§3 values marked pending recompute.

## Frozen accounting (quoted, unchanged)

- Superframe n = 1024 GF(32) symbols, n_bits = 5120, anchor H_full = 0.83256272 b/sym,
  content = 852.544 b (baseline §2; [P1]§2).
- `f_super = (5·(m1+m2)+64)/852.544 ≤ 1.3` ⇒ leak ≤ 1108.31 b ⇒ m1+m2 ≤ 208. A208:
  leak 1104, f = 1.294947, headroom 4.3075 b (baseline §2; [REV]§5.4).
- `f_eff = f_super + 4.785675·FER` on each arm's OWN m/H basis (baseline §2; pending
  P-V2 slope verification, §0.2 — frozen-planning arithmetic retained, no slope conclusion).
- `λ_total = leak_EC + 64` (≡ε_EV≈2⁻⁶³); `net = A·5·n − leak`; nominal superframe
  5120−1104 = +4016 b (baseline §2). **The prior term is absent — CONFIRMED gap**
  ([AUD] C1; zero prior-term hits in `SECURITY_MODEL.md`).

## 1. Amortization model (DECIDED: one-time factory calibration)

- **Read-only reuse (observable, [DEC]§A):** `gamma_f03.npz` is NEVER refitted —
  `B2F_RESULT:6` + `B2F_PACKET` ("NO refit, read-only"), `O1_PACKET:25`, `KANITSCHAR:5-6`,
  `S2C_PACKET:17-18`, `B2E_PACKET:18`, `B2G_PACKET:14`, `P0/O1R/L1B` paired-reuse notes —
  all bind the SAME frozen arrays across O1/O1R/P0/L1B/B2E/B2F/B2G/X1-2M. The prior is a
  **ONE-TIME factory calibration**, not a per-packet cost ([REV]§2a). The frozen
  amortization/reuse statement NOW EXISTS (baseline §5-i, partially settled).
- **Withdrawn sensitivity figure (NOT a planning number):** the "0.12–0.26× per-source
  ratio" ([REV]§6b: CAL-scale 1,028,096 b ÷ 8,441,632 b = 0.12×; 2M-TRAIN-scale
  2,195,748 b ÷ 8,441,632 b = 0.26×) is recorded here as a WITHDRAWN sensitivity figure
  and SHALL NOT be used for planning. Reason: its denominator mixed the sacrificed TRAIN
  pool with key-eligible material and it is incompatible with the cross-source reuse ban
  ([X1]§4 — each source pays its own calibration; 1M/1.5M bundles must be materialized
  separately). It stays in history only; citing it as a cost justification is refused.
- **Binding figures that survive:** (i) cross-source channel reuse FORBIDDEN ([X1]:32, §4)
  ⇒ each source pays its own calibration; (ii) the repo's own 60/20/20 consecutive-time
  split ([P3]§7.4) makes the prior cost **1.50× the key it enables, per source**
  ([REV]§2c table: 1200/800, 1660/1107, 2187/1458 frames; forgone÷key = 60:40 exactly at
  constant 4016 b/superframe net; [DEC]§A). The 1.50× figure BINDS any SKR claim
  (baseline §5-i). The withdrawn 1.8× and 51–256×-as-planning-number stay withdrawn
  (baseline §4 ledger).

## 2. Disclosure route (DECIDED: sacrifice-the-sample DEFAULT)

- **Rule ([DEC]§B; baseline §§2/5-ii/7-4):** the calibration/prior (TRAIN 60 %) sample is
  SACRIFICED — excluded from key generation. Its cost lands in the SKR numerator as
  forgone key ONLY; it does NOT enter `λ_total`; `f_super`/`f_eff` are UNAFFECTED
  (`f_super = (5m+64)/content` identity on frozen m; no prior term in
  `v80_o1_campaign.py:415-417`, `nonbinary_qspa.py:264-268`, `metrics/leakage.py:29-34`).
  Under this DEFAULT the entire 36-bit consequence below is inert (f/m unaffected).
- **Alternative: PERMITTED-BUT-NOT-DEFAULT (disclose-the-statistic).** Conditional cost
  (REVISE A2; non-default-branch conditional, NOT the headline finding): UNDER A PER-BLOCK
  DISCLOSURE MODEL ONLY — iff every block bears the full 36 b cost charged against that
  block's 1.3 gate — 36 b (= 2·log₂262144; standard order ~(k/2)log n ≈ 18 b, [REV]§3a)
  is 8.36× the A208 headroom 4.3075 b ([REV]§5.4) ⇒ largest admissible m is m ≤ 201
  (⌊(1108.3075−64−36)/5⌋ = 201), inside the unmapped 188–208 cliff. Under the AMORTIZED
  alternative — prior disclosed once per same-source batch — the per-block cost is
  36/200 ≈ 0.18 b (1M) or 36/364 ≈ 0.099 b (2M) (counts §3), and m ≤ 201 does NOT follow.
- **Boundaries (both branches):** NEITHER budget may be used until the total transcription
  (bits disclosed, encoding, precision, public-message protocol) AND its amortization basis
  (per-block vs per-batch, batch size) are DEFINED. 36 b itself is NOT a proven
  security-leakage quantity: the real C03 is a 1024-bin smoothed histogram (≤1023 dof;
  [AUD] C4), and no two-parameter encoding, precision, or public-message protocol has been
  established ([REV]§3). Anyone choosing disclose-the-statistic must define transcription +
  amortization FIRST, then re-derive the operating point and re-run certifiability ([DEC]§E-5).
- **Why default:** sacrifice is the standard finite-key PE treatment (random-sampling /
  Serfling; the sample is discarded by design, [REV]§1c) and the only route compatible
  with composable-security intent. The sibling's zero-PE-leakage is a scope exclusion
  (`public_ec_only_not_secure` + `composable_security_claim_flag=0`, NO estimation-leakage
  variable exists, [SIB] S3–S4) — NOT transferable ([REV]§4; baseline §4 ledger).

## 3. Data roles / key-eligible counts (CORRECTS [P3]:43)

- **Roles (RETAINED [P3]§7.4):** 60/20/20 consecutive-time TRAIN/VAL/HOLD by ascending
  frame index; split manifest written before any statistic; HOLD single use; VAL
  recorded-unused. TRAIN (60 %) is the calibration reserve and, under the §2 DEFAULT, is
  excluded from key generation.
- **Corrected counts ([DEC]§C; baseline §§2/5-iii):** planning counts 500/691/911 reserved
  zero frames for the prior ⇒ SUPERSEDED for planning (history only; baseline §0.1). The
  key-eligible superframe counts are **200 / 276 / 364** (pool 840 vs 2103; 2.5×
  overstatement corrected, [REV]§1c):

  | src | frames | fr/superfr | planning ([P3]:43) | TRAIN reserve (60 %) | key-eligible (40 %) |
  |---|---|---|---|---|---|
  | 1M | 2000 | 4 | 500 | 1200 fr = 300 | **200** |
  | 1.5M | 2767 | 4 | 691 | 1660 fr = 415 | **276** |
  | 2M | 3645 | 4 | 911 | 2187 fr = 546 | **364** |
  | pool | 8412 | 4 | 2102 (roadmap 2103 = ⌊8412/4⌋; 1-fr gap 0.05 %) | 5047 | **840** |

  Derivation: key fr = total − TRAIN (800/1107/1458); ÷4 floor ⇒ 200/276/364
  ([REV]§1c, §2c; `decision-log.md:3078`).
- **Certifiability consequence (own-H basis governs; REVISE R5; values pending recompute —
  `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` ABSENT, baseline-§3 numbers retained):**
  `N_req = ceil(3·4.785675/(1.3−f_super))`, `f = (5m+64)/(1024·H)`, full-precision H_MM
  0.8036079281174853 / 0.8289616869054485 / 0.8345846048587662 (read-only from
  `workspace/p3_census_3954637c/census_table.json`; [DEC]§C). At own m_max — 1M@201
  N = 15487 ≫ 200; 1.5M@207 N = 2700 ≫ 276; 2M@208 N = 1754 ≫ 364. At m = 200:
  1M 2051 > 200 NO; 1.5M 309 > 276 NO; 2M 262 < 364 YES-on-count (zero-failure still
  required). At m = 199: 1M 1098 > 200 NO; 1.5M 274 < 276 YES-on-count PROVISIONAL
  (2-block margin, pending full-precision recompute); 2M 236 < 364 YES-on-count. The
  blanket "every N_req still exceeds its key-eligible count at m = 200" is FALSE and stays
  corrected. [P3]§9.2 structural-uncertifiability holds at m_max, NOT uniformly at m = 200.

## 4. Estimator caveat (UNVERIFIED pending re-run; P-V1)

- **Finding (CONFIRMED by `docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` §§T1–T2):**
  the A1 census plug-in `h_full_f03` (`comparison_bench/src/comparison_bench/cli/p3_census_a1.py:94–128`)
  is a CONDITIONAL entropy `Ĥ(A|B) = Ĥ(A,B) − Ĥ(B)` (chain rule over the F03 bijection),
  but the added Miller–Madow term (`p3_census_a1.py:349`, `K` = joint support per line 347)
  is the JOINT-entropy correction `(K_AB−1)/(2N·ln2)`. Correct first-order conditional term
  is `(K_AB−K_B)/(2N·ln2)` — the code over-corrects by exactly `(K_B−1)/(2N·ln2) ≥ 0`.
- **What is missing:** `K_B` (occupied B columns in TRAIN `N_ab`) is computed NOWHERE and
  persisted NOWHERE (no marginal, no per-B counts, no `N_ab` in any of the three
  `workspace/p3_census_3954637c/T2-*.json`; verification §T1 key inventory). Correct
  correction = applied − over; unit over per `K_B−1`: 1M 2.2863e-06, 1.5M 1.6339e-06,
  2M 1.2237e-06 bits.
- **Magnitude and verdict impact (verification §T2):** max plausible over (K_B ≤ 1024;
  plausible ≈1024 is INFERENCE, not fact) is 0.002339 / 0.001672 / 0.001252 bits
  (0.82σ / 0.76σ / 0.65σ of bootstrap CI hw 0.00285/0.00221/0.00193) — BELOW one CI
  halfwidth each. NO IN↔OUT flip in range (1M stays OUT@208 and IN@200; 1.5M stays
  INDETERMINATE@208; 2M stays IN@208). Only verdict-adjacent movement: 1M m_max 201→200
  if K_B ≳ 253 (plausible but INFERENCE); 1.5M m_max stays 207.
- **Status:** direction is optimistic (H up ⇒ f down ⇒ m_max up), but the per-source
  design points remain UNVERIFIED pending a re-run that persists `K_B` (baseline §0.2
  P-V1; `tasks.md` PC-T3). No MM-estimand conclusion is asserted here; out-of-box verdicts
  above are the verification's no-flip result, not a design-point certification.

## 5. What is explicitly NOT claimed

- NO composable-security result: `docs/SECURITY_MODEL.md` itself excludes composable
  finite-size security, and the prior term is absent there (gap, not proof).
- NO SKR number, NO operating point, NO route selection, NO qualification, NO publication
  claim on this basis ([REV]§5.2 claim-ceiling; [P3]§12).
- NO proof that sacrifice-the-sample completes a Serfling/random-sampling argument under
  the repo's continuous-time 60/20/20 split — sacrifice is the DEFAULT accounting route,
  not a finished finite-size proof. Parameterization (§5-iv) stays OPEN (decoder-equivalence
  UNMEASURED, FXR-1 forbids entropy-parity reading).
- Pending verifications P-V1 (MM estimand) / P-V2 (f_eff slope) are placeholders
  (baseline §0.2); conclusions NOT preempted here.

## Auth boundary

- Freeze consumes nothing; authorizes nothing (no execution, no data, no gate change).
  Any future census re-run (e.g. `K_B` persistence) is DECIDE: signed prereg + Pre-EXECUTE
  + fresh explicit grant + independent Pre-RESULT + main-thread acceptance. S3 packaging
  restates key-eligible counts (see `tasks.md` PC-T2). This change does not retire or amend
  the four existing v80 change directories; their SHALLs stand until properly archived.
