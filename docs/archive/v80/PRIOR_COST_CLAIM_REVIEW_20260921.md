# Prior/Calibration Cost Claim — Adversarial Scientific Review (2026-09-21, read-only)

- Reviewer: `reviewer-go` (taste instance, `step-5-preview`). Read-only. No code, no data, no pipeline, no commit/push.
- Claim under review (user-raised): *"The project does not account for the cost of the channel PRIOR (calibration). CAL (frames 702–1725, 262,144 symbols) is fit and frozen but its sacrifice is not counted in the leakage/f accounting. Therefore reported f/net key is optimistic. At current scale this is the DOMINANT term: sacrificing CAL costs ~1.05 Mbits of expected key per packet while a 4–5 block packet produces far less — roughly 1.8× the output. A parameterized ±1 prior (V25 C03, ~2 parameters, holdout NLL 0.807 flat with the full table) would cost only ~36 bits to disclose, or ~2,000 symbols — so parameterization wins on BOTH data requirement and disclosure cost. Reserve: C03's flat NLL only shows the channel's information content is captured; the decoder uses per-coordinate LLRs and may still benefit from the per-B table — this must be measured."*
- Method: `read` + `grep` + pure arithmetic (`.venv/bin/python`, no project modules, no data files). Every number below is either quoted with file:line or recomputed and labelled.
- Concurrent fact-finding audit `docs/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md` **appeared during this review** (it was absent at first read). It is cited where it independently corroborates; this review adds the amortization model, the f-vs-net-key adjudication, the disclosure-in-λ_total consequence, and the honest ratios.

---

## 0. Verdict summary

| # | Attack surface | Verdict | One-line decisive evidence |
|---|---|---|---|
| 1 | "CAL would otherwise be key" | **QUALIFIED** | CAL 702–1725 is the **Jan-23** 1M session, declared out-of-scope for V80 (`S0_RESULT.md:127-131`); the Jan-21 prior sample is the 60 % TRAIN split. PE-sample sacrifice is the *standard* finite-key treatment, not an accounting bug — but the repo never writes the SKR formula that would include it, and its planning block counts (500/691/911) reserve **zero** frames for it. |
| 2 | Amortization / reuse | **UPHELD (and stronger than claimed)** | `gamma_f03.npz` is read-only and reused verbatim across O1/O1R/P0/L1B/B2E/B2F/B2G/X1 — one-time fit, amortized. But cross-source channel reuse is **FORBIDDEN** (`X1_CROSS_SOURCE_PACKET.md:32`), so the amortization base is one source, and the repo's own 60/20/20 split makes the prior cost **1.50×** the key it enables per source. |
| 3 | ~36 bits / ~45,800 bits / O(k log n) | **QUALIFIED** | 36 = 2·log₂(262144) exactly; 45,810 = 2545×18 exactly — arithmetic checks out but uses `k·log n`, 2× the standard `(k/2)·log n`. k=2545 is the **1M Jan-21** joint support; the actual CAL table has **139,766** nonzero cells and the 2M channel behind `gamma_f03` has **2821**. "~2,000 symbols" is unsupported: 36 bits ≡ **9.2** GF(32)-symbols of forgone net key. |
| 4 | Parameterized prior ≡ full table for the DECODER | **UPHELD (reserve is correct)** | No V80 experiment compares them. Repo evidence runs the *other* way: FXR-1 explicitly forbids entropy-parity reading ("entropy of prior ≠ decodability"), and the D7 `q@P` precedent is a **decoder-internal** softmax recombination, not a Bayes marginal — it does not transfer. |
| 5 | Does this invalidate f or only net-key/SKR? | **REFUTED for f; UPHELD for net-key/SKR** | `f_super=(5m+64)/852.544` is an accounting identity on frozen m; gate (b) passes **by construction** (FXR-3). A prior disclosure is not EC leakage. **But** if the prior is publicly disclosed it enters `λ_total` — and then even 36 bits forces m 208→201. See §5. |
| 6 | "Quantity-order error" severity | **QUALIFIED — direction survives, magnitude and figure do not** | Honest ratios: **51–256×** (per-packet recalibration), **1.50×** (repo's per-source split discipline), **0.12–0.26×** (one-time pool amortization), **1.07×** (one 240-block arm). The claimed **1.8× does not reproduce** under any repo-grounded model. |

---

## 1. Attack surface 1 — is the premise right that CAL data would otherwise be key?

**Verdict: QUALIFIED.** Three separate sub-findings.

**(a) The named CAL is not V80 data.** `MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md:93` (verified directly): `cal_start 702, cal_end 1725, n_frames 1024, pairs_per_frame 256, n_symbols 262144`; `:77`: `nonzero: 139766. Zero: 908810.`; `:92-93`: `session 20260123_1M_600k_0dB; source 1M`. That is a **Jan-23** session, and `S0_RESULT.md:127-131` records the Jan-23/Jan-07 pools (`20260123_1M_600k_0dB` / `20260107_PPLN_1p5M` / `20260123_2M_1p2M_0dB`) as `NOT Jan-21 → out-of-scope`. So the specific object named in the claim was **never candidate key material for the V80 line** — the "1.05 Mbits of forgone key" framing does not apply to it. This is the claim's largest factual slip.

**(b) The transferred premise is nevertheless real.** The V80 prior `gamma_f03.npz` is built from the **Jan-21 2M TRAIN split**: `S2C_EXPERIMENT_PACKET_20260920.md:17` — `channel_counts.npz 2M train key (type2_2M_20260121_183657_N_ab_train*, (1024,1024) float64)`; `L1_REWORK_MEMO_V3_20260921.md:36` — `sidecar N=559872`. `split_manifest.json` gives 2M TRAIN 2187 frames / 559,872 pairs, VAL 729 / 186,624, HOLD 729 / 186,624. Those 559,872 symbols are drawn from the same source S3 would use for key. **The premise transfers; the citation does not.**

**(c) "Uncounted cost" vs "standard PE sacrifice".** In finite-key QKD the parameter-estimation sample is sacrificed **by design** and the reduced key length is exactly what the bound accounts for (random-sampling / Serfling construction). So "262,144 symbols not used as key" is the *expected, correct* cost of any calibrated protocol — not evidence of an accounting bug. The repo's genuine gap is narrower and still real:
- **No SKR/net-key formula exists to be optimistic about.** Every V80 packet carries an explicit negative ceiling: `P1_PACKET.md:58` `NO real-data/FER/SKR/qualification/publication claim`; `P3_CENSUS_PACKET.md:180` `This packet establishes NO FER, NO SKR, NO operating point … NO publication number`. S3 (the SKR-bearing phase) is **not authorized and not executed**. There is therefore no *reported* net-key number that is optimistic — only a *planning* ledger (`PROGRAM_PLAN.md:34`, `net = A·5·n − leak`) that has never been instantiated on real frames.
- **The planning ledger does reserve zero frames for the prior.** `P3_CENSUS_PACKET.md:43`: `superframes = floor(frames/4) = 500/691/911 at n=1024` — computed from the **full** frame counts 2000/2767/3645 (`decision-log.md:3078`). `ROADMAP-20260921.md` (P5) repeats `全部可用超帧（n=1024：500 / 691 / 911；n=2048：250 / 345 / 455）`. Nothing subtracts the TRAIN/CAL sample. Under the repo's own 60/20/20 split discipline the key-eligible counts are **200 / 276 / 364 (pool 840)** — a **2.5× overstatement** of available key superframes. **This is the concrete, repo-grounded instance of the gap, and it is a net-key/SKR gap, not an f gap.**

---

## 2. Attack surface 2 — amortization: is "1.8× per packet" silently assuming per-packet recalibration?

**Verdict: UPHELD (the claim's amortization critique is correct, and the honest number is worse than it thinks).**

**(a) The repo's reuse model is one-time, amortized — quoted.** `B2F_EXPERIMENT_PACKET_20260921.md` / `B2F_RESULT_20260921.md:6`: `NO refit (gamma_f03.npz read-only)`. `O1_EXPERIMENT_PACKET_20260920.md:25`: `same 2M channel_counts.npz → gamma_f03.npz … Read-only, synthetic draws`. `KANITSCHAR_RELEVANCE_ADJUDICATION_20260921.md:5-6`: `gamma_f03.npz is a DERIVED read-only bundle of the measured 2M joint histogram`. Every V80 arm (O1, O1R, P0, L1B, B2E, B2F, B2G, X1-2M) binds the **same frozen arrays**; `X1_CROSS_SOURCE_PACKET.md:32` names 2M as `frozen … read-only` while 1M/1.5M bundles must be materialized separately. So the per-packet cost is **not** 262,144 symbols — the claim's "1.8× per packet" does silently assume per-packet recalibration and is wrong on that basis.

**(b) Stationarity evidence, quoted and bounded.** `P3_A1_REVIEW.md:24` (item 8, PASS): `slopes −3.2e−9/+1.7e−9/−4.7e−10; all |acf| ≤ 0.005 (mismatch lag1 0.0017/0.0004/0.0048; H_L1 lag1 −0.0010/−0.0016/−0.0007)`. **But the same item records the power limit**: `the ACF battery has power only against frame-to-frame correlations ≳0.005 (SE ≈ 1/√n_frames ≈ 0.0010–0.0014; all observed |acf| within ~3.5 SE of zero) and cannot probe frame-internal memory — precisely the mechanism that would break gamma_f03 transferability (Q2). The memoryless symbol-level assumption is NOT FALSIFIED, but "not falsified" ≠ "validated"`. So the amortization is *supported but not certified* — an honest qualification, not a refutation.

**(c) The binding constraint is cross-source, not temporal.** `X1_CROSS_SOURCE_PACKET.md:32`: `Cross-source channel reuse is FORBIDDEN (each source's γ differs)`. Therefore the amortization base is **one source**, not the pool. Combined with the repo's own 60/20/20 split discipline:

| source | frames | TRAIN (prior) | VAL+HOLD (key) | superframes key (n=1024) | prior forgone net (b) | key net (b) | **prior ÷ key** |
|---|---|---|---|---|---|---|---|
| 1M | 2000 | 1200 | 800 | 200 | 1,204,800 | 803,200 | **1.500×** |
| 1p5M | 2767 | 1660 | 1107 | 276 | 1,666,640 | 1,108,416 | **1.504×** |
| 2M | 3645 | 2187 | 1458 | 364 | 2,195,748 | 1,461,824 | **1.502×** |
| pool | 8412 | 5047 | 3365 | **840** | 5,067,188 | 3,373,440 | **1.502×** |

(Recomputed: net = 5·1024 − (5·208+64) = 4016 b per superframe = 3.921875 b per GF(32) symbol, from `PROGRAM_PLAN.md:68-69` + `F_EFF_ACCOUNTING_NOTE_20260921.md:23-24`.) The ratio is exactly 60:40 because TRAIN is 60 % and the per-symbol net is constant. **Under the repo's actual split discipline the prior costs 1.5× the key it enables — which is in the same ballpark as the claim's 1.8× and directionally confirms "dominant at current scale".** [Minor repo inconsistency worth recording: the per-source floors sum to 2102 superframes while the roadmap quotes "pool 2103" (= ⌊8412/4⌋); the 1-superframe gap is 0.05 % and changes no conclusion.]

---

## 3. Attack surface 3 — is disclosure really ~36 bits for a 2-parameter prior?

**Verdict: QUALIFIED on every component.**

**(a) The arithmetic, re-derived.** `36 = 2 × log2(262144) = 2 × 18` (exact). `45,810 = 2545 × 18` (exact). Both check out. **But the convention is `k·log₂ n`, which is 2× the standard leading-order parametric description length / mutual-information cost `(k/2)·log₂ n`** (BIC / MDL for a regular k-parameter model). Correct order for k=2: **~18 bits**, not 36. Right order of magnitude; factor 2 high; the repo states no per-parameter disclosure rate anywhere.

**(b) The security logic — "sacrifice the sample" vs "disclose the statistic".** The parameters are fitted *from* the sample, so the disclosure is a function of the sample and does carry `I(θ̂; D) ≈ (k/2)·log₂ n` bits about the **calibration sample**. Under the standard random-sampling construction the calibration sample is discarded, so this costs **zero key bits** — it costs public bandwidth only. The *data* cost (the sample not being key) is the real cost and is the standard PE sacrifice. **The claim's "36 bits … or ~2,000 symbols" conversion is a category error**: it prices a public-bandwidth statistic in forgone-key units. Correct conversion: 36 bits ≡ **9.2 GF(32)-symbols** of forgone net key (36 / 3.921875) or 7.2 symbols of gross. The "~2,000 symbols" figure has no repo source (it resembles a sample-size requirement for estimating two probabilities at ~1 % precision — a different quantity).

**(c) k is misattributed, and the direction of the error matters.** Independently re-verified:
- `2545` = **1M Jan-21** joint support — `data_inventory.json`: `source_id: type2_1M_20260121_184040, parquet_rows: 512000, joint_counts_sparse_nonzero: 2545`. Siblings: 2610 (1p5M), **2821 (2M — the channel actually behind `gamma_f03`)**.
- The **CAL** table (`20260123_1M_600k_0dB`) has **139,766** nonzero cells on 262,144 samples = **1.88 samples/cell** (`MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md:77`). At that occupancy the empirical table is essentially a memorization of the sample: its mutual information with the sample approaches the whole sample, and the `O(k log n)` reading with small k **fails by ~55×**. For the full nonparametric table, **"sacrifice the sample" is the only defensible treatment** — which is the claim's own reserve, arrived at from the other side.
- For the actual V80 prior (2M, 2821 occupied cells on 559,872 training symbols ≈ 198 samples/cell), the disclosure cost is `2821·log₂(559872) = 53,850 b` (or 26,925 b under `(k/2)log n`). So **the ~45,800-bit figure is the right ORDER for the real V80 prior, with the wrong k and the wrong n.**

**(d) "Flat with the full table" is not a measured repo fact.** `model_holdout_scores.csv` contains C01–C06 only; **there is no full-nonparametric-table holdout score**. The G8 attempt was blocked: `JS_TABLE_HOLDOUT.json:1` — `(H) BLOCKED on 47.2%/47.0% seen-column-unseen-u1 mass (no rule, STOP upheld) — NO holdout joint computed`. What *is* measured: C03 holdout 0.80662701 / 0.82712905 / 0.82768944 for 1M/1p5M/2M, vs C01 QSC 3.196/3.347/3.335 and C02 V17-product 3.321/3.497/3.478 — i.e. **C03 beats the aggregate models by ~4× and C06 jitter+bg (0.880) by ~0.07 bits**. The nearest full-table anchor is the V49 TRAIN-pool plug-in 0.80104 (1M) / 0.83256272 (2M), which is **in-sample** — so "0.807 flat with the full table" is an *inference from an in-sample/out-of-sample pair*, not a holdout comparison. Directionally supportive, evidentially weaker than stated.

**(e) "~2 parameters" is wrong as stated.** `nonbinary_v25_gate.py:364-371` — `_delta_model_hist` normalizes a **1024-bin** modular-delta histogram with pre-registered additive smoothing `h = (h + DELTA_SMOOTH_EPS/Q)/(1+DELTA_SMOOTH_EPS)`; `:404-406` computes `pooled_ab` **per source inside the per-source loop**, so C03 is per-source (hence `R18_VERDICT.md:1`: `pooled model never scored (C03==C04 bit-identical)`). Nominally ≤1023 dof. "~2" is defensible only as an *effective*-dof reading (M0 mass table `report:19-23`: 1M mass0 0.7602 / +1 0.2384 / −1 0.0013). The repo's own parameterized prior `v72p2d5_shift_prior.py` is likewise a 1024-bin `q[delta]` histogram with `eps` fallback — again ~1024 nominal dof, small effective dof.

---

## 4. Attack surface 4 — is the parameterized prior equivalent for the DECODER?

**Verdict: UPHELD — the claim's reserve is correct, and the repo evidence actively warns against the optimistic reading.**

**(a) No V80 experiment compares a parameterized prior against the full table under the actual decoder.** All V80 arms (O1/O1R/P0/L1B/B2E/B2F/B2G/X1) bind the frozen `gamma_f03.npz` full factorized table. There is no C03/shift-prior arm at n=1024 GF(32).

**(b) The repo's own recorded lesson runs directly against entropy/NLL parity.** `B2F_RESULT_20260921.md:28` (FXR-1, MANDATORY reading constraint): `Measured prior entropy ≈852.5 b/block ≈ H_full·n = 852.544 — i.e. the Bayes-marginal row IS P(U2|b_i), ~26 b/block FLATTER (weaker) than the genie row 826.266 b … This result must NOT be read as entropy parity`. Memory `:4156`: `entropy of prior ≠ decodability — measured marginal prior entropy ≈852.5 ≈ H_full·n, ~26 b/block flatter than genie 826.27, yet BP converges (no entropy-parity reading; FXR-1)`. **This is direct in-repo evidence that a weaker-entropy prior can decode as well as or better than a sharper one** — i.e. NLL parity is not a decodability proxy. It cuts both ways: it does not prove C03 works, but it removes the main *a priori* argument that it must fail.

**(c) The V72P2D3/D7 `q@P` precedent does NOT settle the question.** `V72P2D3-GF32/EXECUTION_PACKET.md:32,36`: `q=softmax(final_beliefs)` … `production prior_l2=q@P`. That `q` is the **decoder's own L1 soft belief**, so `q@P` is a decoder-internal extrinsic recombination of *beliefs*. The V80 question is whether a **Bayes marginal over the true u1 from the frozen channel** (`marg = einsum("nu,nuv->nv", g1c.T, cond)`, `B2F_RESULT_20260921.md:6`) can be replaced by a *parameterized* per-coordinate table. Different object, different information flow. **The precedent is not transferable, and must not be cited as if it were.**

**(d) The decoder-level prior evidence that does exist is off-design-point.** `V72P3S1-SHIFT/RESULT.md:1`: `128 calls / 2 accepts / 2 verified-success / 0 undetected … PAIRED vs R9-modelF (Δ = shift − modelF per block): mean Δ = −15.0000 … better 127/128` — and `:4` CEILING: `Diagnostic-only: SHIFT-HELPS = residual-level improvement (paired mean Δ −15.0, 127/128 improved), NOT an FER / SKR improvement claim`. Memory `:4425-4428`: `R20 PRIOR-HELPS (uniform 0/128 resid-97.0 vs modelF 1/128; paired mean Δ+10.64, modelF-better 123/128)` and `S1 SHIFT-HELPS … prior ladder PRODUCTIVE: uniform 0 → modelF 1 → shift 2`. So a *structured/parameterized* prior has been shown to beat both uniform and the nonparametric concentration prior **at the decoder** — but on the Jan-23 pool, at n=64, on residuals, never at the V80 design point. This is the strongest existing evidence *for* the claim's direction and the clearest statement of what is missing.

---

## 5. Attack surface 5 — does this change any existing result's validity? (THE KEY QUESTION)

### 5.1 Plain answer

**The prior-cost gap does NOT invalidate any `f_super` / `f_eff` claim. It invalidates net-key / SKR claims — and, separately, the *certifiability block counts* that the roadmap uses to decide which source can carry a headline.**

### 5.2 Why f is untouched — quoted

- `v80_o1_campaign.py:415-417`: `m = int(ARMS[arm]["m"])` / `leak = float(m * 5 + 64)` / `f_super = leak / CONTENT_BITS`. Two terms only.
- `B2F_RESULT_20260921.md:25`: `Gate (b) is an accounting identity on frozen m (both arms pass by construction; FXR-3). Gate (a) is the scientific test: both arms PASS.`
- `F_EFF_ACCOUNTING_NOTE_20260921.md:38-40`: `The frozen gate (b) f_super ≤ 1.3 is a SUCCESS-FRAME quantity, NOT a literature-comparable f_eff` … `1.294947 (or 1.259759) must NEVER be quoted as f_eff.`
- The A208 0/240 at `f_super = 1104/852.544 = 1.294947` is therefore: gate (b) an arithmetic identity on frozen m and frozen H_full; gate (a) a FER measurement on 240 **synthetic** blocks drawn from the frozen read-only bundle. **Neither term has a prior-cost input.** Adding or removing a calibration sample cannot move either number.

### 5.3 Why f is *already* optimistic for a different, already-recorded reason

The denominator is the exposure, and it is a **statistical-PE** exposure, not a prior-cost one. `P3_CENSUS_PACKET.md:98`: `V80 anchor 0.83256272 = H_full(2M) … equals the V49 TRAIN-pool plug-in cross-entropy … It is a train-side plug-in number. Its own measured train→hold gap on the same source is +0.0204 b/symbol (TRAIN 0.83256 → HOLD 0.85297). The census must state which side of the split every reported number is on.` Consequence, already recorded and governing: `P3_A1_REVIEW.md` corrected verdicts give per-source MM-corrected `H_full` 0.80361 / 0.82896 / 0.83458, and 1M at m=208 is `OUT@208 (f=1.341606)` (recomputed: 1104/(1024×0.80361) = 1.34160 ✓). **So the f claims are sensitive to the prior's estimation side — but through the entropy denominator, which the repo already tracks — not through a missing "prior cost" term.**

### 5.4 The one route on which prior cost *does* enter the f numerator — and it is decisive

`ROADMAP-20260921.md:229-231` freezes `verification-aware λ_total = leak_EC + 64` (≡ ε_EV ≈ 2⁻⁶³). If the prior is treated as a **publicly disclosed statistic** (the claim's preferred route), its bits belong in `λ_total`, and `λ_total` **is** the numerator of `f_super`. Recomputed:

| prior disclosure added to numerator | m=208 | m=207 | m=202 | m=201 | m=200 |
|---|---|---|---|---|---|
| +0 b | 1.294947 | 1.289083 | 1.259759 | 1.253894 | 1.248029 |
| +18 b (`(k/2)log n`, k=2) | 1.316061 | 1.310196 | 1.280872 | 1.275007 | 1.269142 |
| +36 b (claim's figure) | **1.337174** | 1.331309 | 1.301985 | 1.296120 | 1.290256 |

A208 headroom is `1.3·852.544 − 1104 = 4.3075 bits`. **36 bits is 8.36× the entire headroom; even 18 bits is 4.18×.** The largest m admitting a 36-bit prior disclosure is **m=201** (`floor((1108.3075−64−36)/5)`), i.e. the operating point must move from 208 to **201** — seven rows / 35 syndrome bits surrendered to pay 36 disclosure bits, a near-wash in bits that relocates the arm into the **unmapped cliff**: `L1_CONSTRUCTION_MEMO_20260920.md:14` records `A188 (m=188) FAIL … ↔ A208 (m=208) PASS` and `The 188–208 cliff shape is unmapped; m≈200–202 is untested and sits inside that margin`; soft-marginal F202 (m=202) is already 6/240 with `f_eff = 1.3794 > 1.3` (`B2F_RESULT_20260921.md:57-61`).

**So the claim's "parameterization wins on disclosure cost" is refuted as stated: under the repo's own `λ_total` convention a parameterized prior is NOT cheap — it is 4–8× the entire budget headroom at the only passing operating point.** What parameterization genuinely wins is the **data requirement** (attack surface 2/6), which is the net-key/SKR axis.

### 5.5 Net-key / SKR — where the gap is real

Independently confirmed, no prior term anywhere: `nonbinary_qspa.py:264-268` returns exactly `{"syndrome_disclosure_bits", "verification_tag_bits", "key_dependent_disclosure_bits_total", "public_control_bits"}` — and `public_control_bits` is the natural home for a prior-disclosure term and is **0** in every V80 campaign. `metrics/leakage.py:29-34` (`estimate_ldpc_leak_bits = syndrome + verify + puncture/shortening`) has no prior term. `SECURITY_MODEL.md:122-125` caps the scope: `Composable finite-size security is out of scope for this IR line (companion-paper scope)`. Corroborated by the concurrent audit (`PRIOR_COST_ACCOUNTING_AUDIT_20260921.md:12`, C1 CONFIRMED). Related-but-different already-named extras: `S2_ACCOUNTING_MAP_20260920.md:24-26` — `L1 actual redundancy + blind-reconciliation extra disclosure must still be counted`. Prior cost would be a **third** item on that list.

---

## 6. Attack surface 6 — severity calibration: the honest ratios

All recomputed from `PROGRAM_PLAN.md:68-69` + `F_EFF_ACCOUNTING_NOTE_20260921.md:23-24`: content 852.544 b, m=208 ⇒ leak 1104 b, **net 4016 b per n=1024 superframe = 3.921875 b per GF(32) symbol**.

**(a) The claim's own inputs.** CAL = 1024 frames × 256 = 262,144 symbols = 256 superframes ⇒ forgone net = 262,144 × 3.921875 = **1,028,096 b ≈ 1.03 Mbits** (the claim's "~1.05 Mbits" is right to ~2 %; they evidently used 4 b/symbol).

**(b) Honest ratio under every amortization model:**

| model | prior cost | key output | **ratio** |
|---|---|---|---|
| Per-packet recalibration, "packet" = 4 V80 blocks (1024 symbols each) | 1,028,096 b | 16,064 b | **64.0×** |
| Per-packet recalibration, "packet" = 5 V80 blocks | 1,028,096 b | 20,080 b | **51.2×** |
| Per-packet recalibration, "packet" = 4 frames (256 symbols) | 1,028,096 b | 4,016 b | **256×** |
| Per-packet recalibration, "packet" = 5 frames | 1,028,096 b | 5,020 b | **204.8×** |
| One 240-block V80 arm (the actual experimental unit) | 1,028,096 b | 963,840 b | **1.07×** |
| Repo's per-source 60/20/20 split discipline (any source) | 1,204,800–2,195,748 b | 803,200–1,461,824 b | **1.50×** |
| One-time calibration amortized over the whole Jan-21 pool (CAL-scale) | 1,028,096 b | 8,441,632 b | **0.12×** |
| One-time calibration amortized over the pool (2M-TRAIN-scale) | 2,195,748 b | 8,441,632 b | **0.26×** |

**(c) The claimed 1.8× does not reproduce.** No repo-grounded model yields it. Nearest neighbours: the 60:40 split ratio 1.50× (real, §2c); the unit-conversion factor 7.84375/4.22717 ≈ 1.856 flagged by the concurrent audit (`PRIOR_COST_ACCOUNTING_AUDIT_20260921.md:86`) as a GF(32)-vs-full-ToA-symbol artifact of a **non-existent** source number (its C3 is NOT-PRESENT: `P20Q` and `138516` have zero hits in `docs/` and `src/`). **On current evidence 1.8× is a unit/attribution artifact, not a cost ratio.**

**(d) Severity: the "quantity-order error" label does not survive as stated, but the underlying exposure is real and currently unbounded.**
- **Refuted:** "1.8× per packet" (per-packet recalibration is not the repo's model; the honest figure is 51–256× under that model, 1.50× under the repo's split discipline, 0.12–0.26× under pool amortization).
- **Refuted:** "36 bits is cheap" (§5.4: 4–8× the headroom at the only passing point).
- **Refuted:** "~2,000 symbols" for 36 bits (correct: 9.2 symbols).
- **Qualified:** "f is optimistic" — f is untouched; the f *denominator* is optimistic for an already-recorded in-sample reason.
- **UPHELD:** the prior is the single largest undisclosed input, it has **no stated amortization basis anywhere in the repo**, the planning block counts (500/691/911 vs 200/276/364) overstate key-eligible superframes by 2.5×, and composable finite-size is punted to a companion paper so nothing downstream will catch it. For a publication SKR claim this is **material**; for the current synthetic gates the exposure is **nil** (fixed read-only bundle, no real frames).

---

## 7. Consolidated chain verdict (link by link)

| Link in the claim | Verdict |
|---|---|
| "CAL 702–1725 / 262,144 symbols is fit and frozen" | **QUALIFIED** — true of the Jan-23 1M session (`MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md:93`); the V80 prior is instead the Jan-21 2M TRAIN split, N=559,872 (`L1_REWORK_MEMO_V3:36`). |
| "Its sacrifice is not counted in the leakage/f accounting" | **UPHELD** — no prior term in `nonbinary_qspa.py:264-268`, `metrics/leakage.py:29-34`, `v80_o1_campaign.py:415-417`, or `ROADMAP:229-231`. |
| "Therefore reported f is optimistic" | **REFUTED** — `f_super` is an accounting identity on frozen m (FXR-3); no prior input. |
| "Therefore reported net key is optimistic" | **UPHELD, with no victim yet** — no SKR/net-key number has been reported (all packets carry negative SKR ceilings); the exposure is in the *planning* ledger and in the 500/691/911 vs 200/276/364 block counts. |
| "~1.05 Mbits per packet" | **QUALIFIED** — 1.028 Mbits is correct for CAL-as-256-superframes; "per packet" is wrong (amortized, read-only, one-time). |
| "roughly 1.8× the output" | **REFUTED** — no repo-grounded model yields 1.8×; honest values 51–256× / 1.50× / 0.12–0.26× / 1.07×. |
| "C03 ≈ 2 parameters" | **REFUTED as stated** — 1024-bin smoothed delta histogram, nominally ≤1023 dof (`nonbinary_v25_gate.py:364-371`). |
| "holdout NLL 0.807" | **UPHELD** — 0.80662701 / 0.82712905 / 0.82768944 (`model_holdout_scores.csv`). |
| "flat with the full table" | **QUALIFIED** — no full-table holdout exists (G8 BLOCKED, `JS_TABLE_HOLDOUT.json:1`); only an in-sample plug-in anchor (0.80104/0.83256272) is available. |
| "~36 bits to disclose" | **QUALIFIED** — 2·log₂(262144) exactly, but 2× the standard `(k/2)log n`; and 36 b is 8.36× the A208 headroom if it enters `λ_total`. |
| "~45,800 bits for a ~2545-parameter table" | **QUALIFIED** — arithmetic exact, k misattributed (2545 = 1M support; CAL = 139,766; 2M channel = 2821); right order for the real prior (53,850 b at k=2821, n=559,872). |
| "table carries O(k log n) MI about A given B" | **QUALIFIED / partly REFUTED** — fails at CAL occupancy (1.88 samples/cell ⇒ table ≈ memorized sample); holds for the 2M channel (~198 samples/cell). |
| "parameterization wins on BOTH data requirement and disclosure cost" | **SPLIT** — wins on data requirement (UPHELD); loses on disclosure cost under the repo's `λ_total` convention (REFUTED, §5.4). |
| "NLL parity ≠ decoder parity — must be measured" | **UPHELD** — no such measurement exists; FXR-1 forbids the parity reading; the D7 `q@P` precedent is non-transferable. |
| "DOMINANT term at current scale" | **QUALIFIED** — dominant for net-key/SKR at the repo's split discipline (1.50×); irrelevant to f; irrelevant to the current synthetic gates. |

---

## 8. What must be measured to settle the decoder question (and the accounting question)

**Decoder equivalence (the claim's own reserve — highest scientific value, cheapest):**
1. **A single frozen EXPLORE arm at the V80 design point (n=1024, GF(32), λ={2:1}, A208/A202 instances, paired seeds 2026095601+idx, 240 blocks) with the prior swapped from the full `gamma_f03` table to the C03/`v72p2d5_shift_prior` parameterized ±1 table**, reporting the same frozen gates (a) fails/240 ≤ 12 and (b) `f_super`, plus the report-only columns (prior entropy, iterations, u1_mismatches). This is a **one-arm, ~11–22 min** measurement (b2f cost bracket: 672.6 s / 1346.9 s per 240 blocks) and it directly settles "does the per-B table buy decodability the parameterization cannot."
2. **A per-block `Ĥ` vs pooled `Ĥ` spread probe (zero decode)** — already queued in the roadmap as the Scarinzi trigger; it also bounds how much of the full table's value is block-local vs pool-global, which is exactly the information the parameterization would discard.
3. **A C03-vs-full-table holdout NLL on the 2M source** (closing the G8 BLOCKED gap), so the "flat with the full table" claim becomes a measurement rather than an in-sample/out-of-sample inference.

**Accounting (must precede any publication SKR claim):**
4. **A frozen amortization/reuse statement for the prior**: one-time factory calibration reused across the full Jan-21 pool (→ 12–26 % severity, low) vs per-session re-estimation disclosed against that session's key (→ 1.50× severity at the repo's 60/20/20 split, high). This is the single item that most changes severity, and it costs nothing to write.
5. **A decision on the disclosure route and its accounting home**: "sacrifice the sample" (cost = forgone frames, belongs in the SKR numerator only) vs "disclose the statistic" (cost = `λ_total` bits, belongs in `f_super` too, and forces m 208→201). These are **not** equivalent and the repo has chosen neither.
6. **Correct the S3 block counts** from 500/691/911 to the key-eligible 200/276/364 (or state explicitly that the prior sample is a separate, non-key stream), and re-run the certifiability rule `N ≥ ⌈3·4.785675/(1.3−f_super)⌉` against the corrected counts — the structural uncertifiability conclusion (`P3_CENSUS_PACKET.md:148`) only gets stronger.
7. **State which side of the split every reported `H_full` is on** (already required by `P3_CENSUS_PACKET.md:98`); the anchor is a TRAIN-side plug-in with a measured +0.0204 b/symbol train→hold gap, which is a separate and already-recorded optimism in the f denominator.

---

## 9. Checklist

- [x] Matches OpenSpec spec — no OpenSpec change is implicated: this review changes no frozen quantity, gate, threshold or packet. If items 4–6 above are adopted, they require a new OpenSpec change (accounting/`λ_total` semantics).
- [x] Tests pass — no code changed; arithmetic re-verified with `.venv/bin/python` (pure arithmetic, no project imports, no data files).
- [x] No scope creep — read-only review, one file written.
- [ ] `docs/decision-log.md` / `docs/troubleshooting.md` needs update? — **Yes, if the main thread accepts §8 items 4–6.** Recommended as one decision-log entry recording: (i) prior/calibration cost is a THIRD uncounted extra alongside L1 share and blind rounds (`S2_ACCOUNTING_MAP:24-26`); (ii) it belongs in net-key/SKR and in the S3 block counts, NOT in `f_super` under the sacrifice route; (iii) the two routes are not equivalent and neither is chosen; (iv) the "1.8×" figure is withdrawn as unsupported. No troubleshooting entry — no failure mode was reproduced.

**Does NOT establish:** no FER/SKR/route/qualification/publication claim; no measurement performed; no frozen quantity, gate, threshold or packet changed; nothing authorized.
