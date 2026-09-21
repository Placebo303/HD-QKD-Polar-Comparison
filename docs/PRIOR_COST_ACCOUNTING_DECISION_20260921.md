# Prior Cost Accounting Decision — 2026-09-21 (Step-1 of V80 baseline §6)

> Docs-only. Authorizes NO execution, NO data access, NO commit/push. Authority: `docs/V80_BASELINE_20260921.md` (§2/§5/§6/§7).
> Sources: [REV]=`docs/PRIOR_COST_CLAIM_REVIEW_20260921.md` [AUD]=`docs/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md` [SIB]=`docs/SIBLING_PRIOR_PARAMETERIZATION_AUDIT_20260921.md` [X1]=`docs/research_cycles/V80-NBLDPC-JAN21/X1_CROSS_SOURCE_PACKET.md` [P3]=`.../P3_CENSUS_PACKET.md` [A1R]=`.../P3_A1_REVIEW.md` [P1]=`.../P1_PACKET.md`.
> Status: user-RATIFIED 2026-09-21 (baseline §7 items 1–7); this document executes baseline §6-step-1 only.

## §A Amortization / reuse statement (SETTLED here)

- **Read-only reuse (observable):** `gamma_f03.npz` is NEVER refitted — `B2F_RESULT:6` + `B2F_PACKET` ("NO refit, read-only"); `O1_PACKET:25` ("same 2M channel_counts.npz → gamma_f03.npz, read-only, synthetic draws"); `KANITSCHAR:5-6` (derived read-only bundle of measured 2M joint histogram); `S2C_PACKET:17-18` (2M TRAIN keys + `2M_gamma1_L1 (32,1024)`, `2M_gamma2_L2condU1 (32,32,1024)`); `B2E_PACKET:18`, `B2G_PACKET:14`, `B2E/B2F/B2G_PREEXEC:11-12`, `P0/O1R/L1B` paired-reuse notes — all bind the SAME frozen arrays across O1/O1R/P0/L1B/B2E/B2F/B2G/X1-2M. ⇒ the prior is a **ONE-TIME factory calibration**, not a per-packet cost. [REV]§2a.
- **Correct model: one-time pool amortization.** Honest per-source ratio is **0.12–0.26×** ([REV]§6b: CAL-scale 1,028,096 b ÷ 8,441,632 b = 0.12×; 2M-TRAIN-scale 2,195,748 b ÷ 8,441,632 b = 0.26×). NOT the 51–256× per-packet-recalibration figure (wrong model — repo never recalibrates per packet) and NOT the withdrawn 1.8× (no repo model reproduces it; 7.84375/4.22717≈1.856 is a 5-bit vs 10-bit symbol unit artifact, [AUD]§6, [REV]§6c).
- **Two binding constraints survive amortization:** (i) cross-source channel reuse is FORBIDDEN ([X1]:32, §4 — each source's γ differs; 1M/1.5M bundles must be materialized separately) ⇒ each source pays its own calibration; (ii) the repo's own 60/20/20 consecutive-time split ([P3]§7.4) makes the prior cost **1.50× the key it enables, per source** ([REV]§2c table: 1200/800, 1660/1107, 2187/1458 frames; forgone÷key = 60:40 exactly at constant 4016 b/superframe net).
- **SETTLED by this §:** reuse fact, one-time-pool model, 0.12–0.26× honest pool ratio, 1.50× per-source binding figure, withdrawal of 1.8× / 51–256×-as-planning-number. **Still OPEN:** §D.

## §B Disclosure route (DECIDED: sacrifice-the-sample, DEFAULT)

- **Rule:** the calibration/prior (TRAIN 60 %) sample is SACRIFICED — excluded from key generation. Its cost lands in the SKR numerator as forgone key only; it does NOT enter `λ_total`; `f_super`/`f_eff` are UNAFFECTED (`f_super=(5m+64)/content` identity on frozen m, FXR-3, [REV]§5.2; no prior term in `v80_o1_campaign.py:415-417`, `nonbinary_qspa.py:264-268`, `metrics/leakage.py:29-34`, [AUD]C1).
- **Alternative: PERMITTED-BUT-NOT-DEFAULT (disclose-the-statistic).** Exact cost: 36 b (=2·log₂262144; standard order ~(k/2)log n ≈18 b, [REV]§3a) is **8.36× the A208 headroom** (1.3·852.544−1104=**4.3075 b**, [REV]§5.4) ⇒ largest admissible m is **m ≤ 201** (⌊(1108.3075−64−36)/5⌋), inside the unmapped 188–208 cliff (`L1_CONSTRUCTION_MEMO:14` A188 FAIL↔A208 PASS; F202 already 6/240, f_eff=1.3794>1.3, `B2F_RESULT:57-61`). Anyone choosing it must re-derive the operating point and re-run certifiability FIRST.
- **Why default:** sacrifice is the standard finite-key PE treatment (random-sampling/Serfling; the sample is discarded by design, [REV]§1c) and the only route compatible with composable-security intent. Contrast: the sibling's zero-PE-leakage is a scope exclusion — `public_ec_only_not_secure` + `composable_security_claim_flag=0`, NO estimation-leakage variable exists ([SIB]S3–S4) — therefore NOT transferable ([REV]§4, baseline §4 ledger).

## §C Corrected key-eligible block counts (CORRECTS [P3]:43)

| src | frames | fr/superfr | planning superfr ([P3]:43, zero prior reserve) | TRAIN reserve (60 %) | key-eligible superfr (40 %) |
|---|---|---|---|---|---|
| 1M | 2000 | 4 | 500 | 1200 fr = 300 | **200** |
| 1.5M | 2767 | 4 | 691 | 1660 fr = 415 | **276** |
| 2M | 3645 | 4 | 911 | 2187 fr = 546 | **364** |
| pool | 8412 | 4 | 2102 (roadmap quotes 2103=⌊8412/4⌋; 1-fr gap 0.05 %, [REV]§2c) | 5047 | **840** |

Derivation: key fr = total−TRAIN (800/1107/1458); ÷4 floor ⇒ 200/276/364 ([REV]§1c, §2c; `decision-log.md:3078`). 2.5× overstatement corrected (2102→840).

- **Certifiability consequence (own-H basis governs; anchor context only):** `N_req=ceil(3·4.785675/(1.3−f_super))`. At own m_max — 1M@201 f≈1.29907 **N≈15438** ≫ 200; 1.5M@207 f≈1.29470 **N≈2708** ≫ 276; 2M@208 f=1.29181 **N=1754** ≫ 364 ([X1]:43; baseline §3 table). Even at m=200 — 2051/309/262 — every N_req still exceeds its key-eligible count. The [P3]§9.2 structural-uncertifiability conclusion only STRENGTHENS.
- Recompute (frozen, docs-only, NOT executed here): `.venv/bin/python -c "H,n=0.80361,1024; m=201; c=n*H; f=(5*m+64)/c; N=-(-3*4.785675//(1.3-f)); print(c,f,N)"` (repeat H=0.82896/m=207, H=0.83458/m=208, and m=200 rows); `.venv/bin/python -c "print((2000-1200)//4,(2767-1660)//4,(3645-2187)//4)"`.

## §D What this settles / does not

- **SETTLES:** amortization model (one-time pool, 0.12–0.26×; 1.50× per-source binds); disclosure route (sacrifice DEFAULT); block counts (200/276/364); F-3 ratification scope (A1-only, `允许你开始Stage 0.5与A1` grant, nil impact 8.7×/7× margins, [A1R]F-3); tolerances (±0.01 control / 0.02 support CONFIRMED, [A1R]§5–6); headline-source rule (2M alone carries A208; generality headlines LEAD with 1M, [P1]§9).
- **Does NOT settle:** whether to parameterize the prior (§5-iv; decoder-equivalence UNMEASURED, FXR-1 forbids entropy-parity reading); any operating point; any FER/SKR/route/qualification/publication claim. **Authorizes NOTHING** (no execution, no data, no gate change).

## §E Consequences for future packets

1. Calibration sample excluded from key; forgone key (1.50× per-source figure) REPORTED in any SKR numerator. 2. Key-eligible counts are 200/276/364, never 500/691/911. 3. Per-source f uses that source's OWN measured H_MM, never the anchor (I5; [X1]§5). 4. Generality headlines lead with 1M; 2M-only headlines FORBIDDEN. 5. If disclose-the-statistic is ever chosen: m re-derived (≤201 at A208 economics), 188–208 cliff mapped first, λ_total re-certified.
