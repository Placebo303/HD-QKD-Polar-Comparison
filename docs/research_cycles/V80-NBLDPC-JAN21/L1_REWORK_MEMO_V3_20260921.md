# L1 rework memo v3 (2026-09-21) — EXPLORE planning-only, design memo (scan closure + option b2e)

- Track EXPLORE planning-only (no code, no execution, no authorization). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Parents: rework memo v2 §2 trade scan + SCAN_PREEXEC/SCAN_ARMS_REVIEW_20260921 + L1B Stage A result/review (C6/C8) + O1 (A188/A208) + O1R (A208 ×2) + P0 (A202/A200) + L1_CONSTRUCTION_MEMO + S2 map + S1 readiness. NEW option **b2e** (cheap-u1-estimator probe); b2a/b2c demoted to fallback.
- Goal: close the dense-check-L1 trade scan factually and pick the next cheapest decisive probe. Non-goals: no code, no execution, no FER/route/S3/qualification/publication claim, no authorization.

## 1. Scan closure — observations only (machine verdicts, provenance per row)

| leg | m / m1 | blocks decoded | fails | FER | verdict | provenance |
|---|---|---|---|---|---|---|
| L2 A188 | 188 | 14 (60-block design, bar 3) | 4 | 28.6% | FAIL-early-stop (4th fail, block 13) | O1_RESULT_20260920.md |
| L2 A192 | 192 | 124 (240 design, bar 12) | 13 | 10.5% | FAIL-early-stop (13th fail, block 123) | workspace/p0_226c6dee/manifest.json |
| L2 A196 | 196 | 29 (bar 12) | 1 | 3.4% | **INCOMPLETE-wall — interrupted, NO verdict** | workspace/p0_23ce5cb9/manifest.json |
| L2 A200 | 200 | 240 | 2 | 0.83% | PASS | P0_RESULT_20260920.md |
| L2 A202 | 202 | 240 | 0 | 0% | PASS | P0_RESULT_20260920.md |
| L2 A208 | 208 | 240 ×2 (R1/R2) | 0 | 0% | PASS | O1R_RESULT_20260920.md |
| L1 C6 | m1=6 | 27 | 13 | 48.1% | FAIL-early-stop (13th fail, block 26) | L1B_STAGE_A_RESULT_20260921.md |
| L1 C8 | m1=8 | 84 (+1 overrun row) | 6 | 7.1% RAW | FAIL(budget) (block-84 decode 1120.7 s > 300 s cap; terminal, non-resumable) | L1B_STAGE_A_RESULT/REVIEW_20260921.md |

- A192 quarter trend (report-only): 4/60 → 6/60 → 3/4 partial ⇒ fails accumulate with block index. A196 1/29 has no complete quarter (0/60 recorded) and carries no verdict; no monotonicity may be inferred across m.
- **Observation (not a claim):** inside the frozen box (m1+m2 ≤ 208, f_super ≤ 1.3) no split has BOTH legs passing under the dense-check-L1 + genie-u1-L2 family. m1=6/8 legs FAIL; m1=10–16 legs were never executed (no `l1b_*` root beyond C6/C8; C12A/C16A appear only as recorded pins in SCAN_ARMS_REVIEW) and could only be funded by m2 ≤ 196 — i.e. by A188/A192 (FAIL) or A196 (unresolved). The closure comes from the funding leg, not from any positive density result.
- **The L2 cliff steepens between m2=192 and m2=200:** 8 rows (40 bits) move block FER from 10.5% to 0.83%; A196 (1/29) sits inside that gap with no verdict.

## 2. NEW option b2e — the cheap-u1-estimator probe (primary recommendation to analyze)

- Motivation: every L2 arm above CONDITIONS on u1 — `posterior_rows_l2` = gamma_2(.|b,u1) (v26_channel L239-244); the u1 dependence lives entirely in Bob's per-symbol prior. Retiring genie therefore does not obviously require an L1 CODE — it requires a u1 estimate at Bob.
- Question: is û1_i = argmax_u γ1(u1|b_i) (free argmax, no decoder, no L1 construction, no DE) enough to keep A208-level decoding?

### 2.1 γ1 statistics — MEASURED read-only (2026-09-21); b2e probe input (no runner, no DE)
- Anchor reproduced: measured p_b-weighted mean H(γ1(·|b)) = **0.02566205** bits/symbol (= H_L1 anchor, S1_READINESS) ⇒ total block entropy 1024 × 0.02566205 = **26.28 bits**.
- Column structure (1024 B-values; p_b = empirical train P(B), sums to 1, min 6.54e-4): **973 deterministic** (γ1 one-hot, H=0, p_b-weight 0.9499) · **20 near-certain** (H 0.0184–0.0505, p_max 0.9943–0.9983 ⇒ 1−p_max 0.0017–0.0057; p_b-weight 0.0194) · **31 uncertain** (H 0.7742–0.8740, p_max 0.7059–0.7722 ⇒ 1−p_max 0.2278–0.2941; p_b-weight 0.0306, holding 97.9% of column entropy and 99.3% of mismatch mass).
- (a) MAP û1: p_b-weighted mean 1−p_max = **0.007909/symbol ⇒ expected 8.10 mismatches per 1024-block** (8.04 uncertain band + 0.06 near-certain band). Column distribution of 1−p_max: p10 = p50 = p90 = 0, max 0.2941 (p_max min 0.7059; no argmax ties). Bounds: E[H] ⇒ ≤ 26.3, −log2 p_max ⇒ ≤ 13.5, measured **8.10** (the H-bound is loose ≈3.3×).
- (b) Entropy: p_b-weighted quantiles p50 = p90 = 0, p95 0.0184, p99 0.8334, max 0.8740 (< log2 32 = 5 ⇒ no near-uniform column). H>0.1: 31/1024 (share 0.0303; p_b-weight 0.03063); H>0.5: the same 31 (0.03063); **H>1.5: 0/1024**. Per-block total entropy (MC 1e6 blocks, seed 20260921, b_i i.i.d. ~ p_b): mean 26.274, p10 20.47, p50 26.09, p90 32.18, p99 37.39, p99.9 41.26, max 49.45 (all-max-column bound 894.96 unreachable).
- (c) Concentration, expected-composition block (position weights 1024·p_b): top-k entropy share k=1 **3.5%**, k=3 **10.3%**, k=5 **17.0%**, k=10 **33.4%**; 50% of block entropy needs k=16, 90% k=29, 99% k=39. Uniform-over-b one-liner (pre-registered): k=1/2/4/8/16/32/64 → 3.4/6.7/13.3/26.3/51.8/98.0/100.0%.
- (d) b2a call — §3 thresholds (k ≤ ~4 conceivable / k ≥ 6 infeasible) UNCHANGED; k is now resolved: per-block uncertain count k(H>0.5) = mean **31.4**, p50 31, p90 39, p99 45, max 60, and **P(k≤4) = 0** over 1e6 blocks (any H>0: mean 51.3, max 88). k≈31 ⇒ 32^k ≈ 4.6e46 ⇒ **b2a enumeration stays infeasible for every block**; entropy is spread, not concentrated (top-5 = 17%), so no small-k subset recovers it. Consequence for §2.3 choice (iii): ~31.4 symbols × 5 b ≈ 157 b ≫ 4.31 b headroom ⇒ dead unless m2 drops 1:1.
- Provenance (read-only; npz md5 + mtime unchanged, no other file written): keys `2M_gamma1_L1` (32,1024) float64 and `2M_p_b` (1024,) float64 (sidecar N=559872). Command: `.venv/bin/python -c "import numpy as np; d='docs/research_cycles/V80-NBLDPC-JAN21/'; z=np.load(d+'gamma_f03.npz'); pb=np.load(d+'gamma_f03_pb.npz')['2M_p_b']; g=z['2M_gamma1_L1']; H=-np.sum(g*np.log2(np.maximum(g,1e-300)),axis=0); am=g.argmax(0); i=np.arange(1024); print('map_err',round(float(pb@(1-g[am,i])),6),'H',round(float(pb@H),6)); [print(t,round(float(pb@(H>t)),5)) for t in (0.1,0.5,1.5)]; s=np.sort(H)[::-1]; print('topk_share',[round(float(s[:k].sum()/H.sum()),4) for k in (1,2,4,8,16,32,64)])"` → `map_err 0.007909 H 0.025662 | 0.1 0.03063 | 0.5 0.03063 | 1.5 0.0 | topk_share [0.0336,0.0672,0.1329,0.2629,0.5182,0.9804,1.0]`. Block-level totals, k counts and top-k shares come from the same two arrays via a /tmp script (seed 20260921, 1e6 blocks, b_i i.i.d. ~ p_b). Report as numbers with thresholds, not promises (see §3).

### 2.2 Probe definition (synthetic, paired)
- Arms: **B208 PRIMARY** — A208 code (m=208, λ={2:1}, construct seed 2026092001/trials 20; pins fc=0 + rank-full + twice-identical GATED, girth recorded-not-gated) with the u1 source switched genie → MAP. Optional secondaries B202/B200 (P0 code family, m=202/200).
- Blocks/seeds: 240 blocks, literal paired base 2026095601+idx (same frames as O1R/P0/L1B; NO independence claim), stream `o1_blk:{seed}`; construct seed 2026092001.
- Executor delta (thin, additive; no frozen-module edits): replace `posterior_rows_l2(bundle, b, u1)` by `posterior_rows_l2(bundle, b, û1)` with û1 = argmax over g1[:,b]; add per-block mismatch count Σ_i 1[û1_i ≠ u1_i] (true u1 known in the synthetic draw — measurement only, labeled not-a-disclosure).
- Gates (AND per arm): (a) fails/240 ≤ 12 (early-stop at 13th); (b) f_super-with-D-u1 ≤ 1.3 (§2.3).
- Budgets (P0/O1R caps): ~900 s est, 1 window ≤3600 s, per-decode ≤300 s, RSS <4 GiB, ≤1 wall-partial resume; expected wall like A208 genie runs (~550–570 s, RSS ~166 MB) with negligible added MAP cost.

### 2.3 Accounting implication — exactly what gate (b) becomes
- Structural note (frozen error-domain semantics): û1 is computed at Bob from b alone (γ1 = P(U1|B)); Alice's disclosure is unchanged (syndrome of x=u2 only). The estimator itself forces no extra disclosure ⇒ m1 L1 rows may become unnecessary, returning L2 rows to 208 — or estimator failures may be corrected cheaply.
- Freeze a **D-u1** term anyway (measured; initial 0.0 with the MEASURED-placeholder NEVER-ASSUME-ZERO label) so gate (b) always reads f_super = (m2·5 + 64 + D-u1)/852.544 ≤ 1.3.
- Choice (i) estimator-only: D-u1 = 0.0 measured, m2 = 208 ⇒ 1104/852.544 = 1.294947, headroom 4.31 b (any later measured D-u1 > 4 bits fails gate (b)).
- Choice (ii) advance-conservative surcharge (reserve 30 b): m2 ≤ 202 ⇒ 1074/852.544 = 1.259759 (A202 line), headroom 34.3 b.
- Choice (iii) estimator + targeted repair (disclose only uncertain positions): 5 bits per GF(32) symbol ⇒ the 4.31 b headroom buys 0 symbols; viable only if the pending γ1 stats show the uncertain count is 0, or if m2 drops 1:1. Land the final gate on the probe's MEASURED D-u1 and mismatch count.

## 3. b2a enumeration analysis (brief, honest)

- Mechanism: hold MAP positions, enumerate 32^k over the uncertain symbols plus a syndrome check; cost = new decoder entrypoint + leakage re-derivation + gate re-basis.
- Feasible only if the per-block uncertain count k is small AND its tail is thin: 32^4 ≈ 1.05M (borderline), 32^5 ≈ 33.6M (no), k ≥ 6 ≈ 1.07e9 (no). k itself is PENDING (§2.1).
- What IS feasible today: nothing beyond obtaining the k counts; small-k exhaustive with dense checks is conceivable only if k ≤ ~4 for (nearly) every block. No promise.

## 4. Recommendation + packet outline (no auto-proceed)

- Recommend b2e next: cheapest decisive step — one arm, ~550–570 s, thin executor delta, no L1 construction, no DE, no m2 trade. If it PASSES at A208-level gates, genie retirement may not require any L1 code construction at all, decoupling the biggest blocker from the dense-check regime.
- Packet outline (freeze separately; own Pre-EXECUTE + fresh grant): arms B208 (+optional B202/B200); seeds 2026095601+idx ×240, stream `o1_blk:`, construct seed 2026092001/trials 20; executor delta = u1 source switch (genie→MAP) + û1-mismatch measurement + D-u1 accounting columns; gates §2.2; budgets §2.2; artifacts manifest.json + rows.json + block_accounting.csv + group_accounting.csv under fresh `workspace/b2e_<uuid8>`; STOP rules = any science-input change, any gate breach, any per-decode >300 s (terminal), ≥4 GiB RSS, >3600 s window.
- Ordering: b2a / b2c (or a hybrid) only if b2e FAILS; b2a additionally needs the §2.1 counts attached to the same freeze step (no new execution).

## 5. Does-not-establish; no authorization

- Establishes no FER, no route/S3/qualification/publication claim; genie retirement is NOT established by any existing arm; A196 has no verdict; no cross-arm pooling; paired-seed reuse carries no independence claim; synthetic only (no real/Jan-21 frames). This memo authorizes NOTHING; the b2e packet needs freezing + review + grant before any execution.
