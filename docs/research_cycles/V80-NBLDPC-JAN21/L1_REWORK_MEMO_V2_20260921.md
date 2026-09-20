# L1 rework memo v2 (2026-09-21) — EXPLORE planning-only, design memo

- Track EXPLORE planning-only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Parents: Stage A result 20260921 + rework memo 20260921 (option (a) now empirically FAILED) + construction memo 20260920 + P0 (A202/A200 PASS) + O1/O1R + S2 map.
- Goal: pick the next cheapest decisive probe. Non-goals: no code, no execution, no authorization, no FER/route claim.

## 1. Stage A data summary (observations only)

- C6 (m1=6): 27 blocks, 13 fails, FER 0.481, FAIL-early-stop (13th fail block 26). C8 (m1=8): 85 blocks, 6 fails, 7.1% PARTIAL raw rate, FAIL(budget) — block-84 per-decode overrun 1120.7 s > 300 s cap, terminal non-resumable per frozen code + packet §6. Neither PASSED; no A PASS exists.
- Check degrees (n=1024, all-dv-2, 2048 edges): m1=6 → ~341; m1=8 → 256; m1=12 → ~171; m1=16 → 128. Trend 48% → 7.1% tracks density; both still far from sparse (m2≈200 → deg ~10).
- Interpretations (not claims): (i) more rows → lower density → m1≥12–16 might decode; (ii) dense-check BP may be fundamentally poor at any m1≤16 (girth-4/pigeonhole regime, weak extrinsic) — trend could plateau; (iii) per-decode instability is real: successes ~2–12 iters, failures pile to max_iter=300 and wall blows past the 300 s cap on dense graphs.
- Frozen cap rule: max_iter=300/streak 3 breach = counted fail, run CONTINUES; per-decode wall >300 s = arm-terminal FAIL(budget), FAIL states NEVER resume. Options (future packet only): keep frozen rule; add wall-partial resume; lower max_iter for L1 legs; wall→iter early-abort. No change here.

## 2. TRADE SCAN (recommended candidate) — fund m1=12–16 from m2

- Box frozen: m1+m2 ≤ 208 (leak 5·(m1+m2)+64 ≤ 1108.31, f_super ≤ 1.3). Anchors: m2=200 PASS (A200 2/240), m2=188 FAIL (A188 4/14 early-stop); 192/196 UNTESTED inside the cliff.
- Splits: m2=196 → funds m1=12 (leak 1104, f_super ≈1.29495, same as A208); m2=192 → funds m1=16 (leak 1104, same mapping). Both keep the frozen total-208 budget line.
- Scan arms (all synthetic, paired blocks `2026095601+idx`, same machinery): L2 probes P0-style genie-u1 at m2=196 and/or 192 (cheap: ~765–937 s/arm, 1 window ≤3600 s, RSS ~165 MB); L1 probes Stage-A-style at m1=12 and/or 16 (cheap but overrun risk as in C8; same caps).
- Most decisive single L2 point: **m2=192** — it funds the best L1 leg (deg 128). 192 PASS ⇒ 16-split viable (196 likely but still needs its own arm, no monotonicity claim); 192 FAIL ⇒ fall back to 196/12 split.
- Gates (AND per arm): fails/240 ≤ 12 (FER ≤ 5%) AND f_super-mapping ≤ 1.3 carried. Then combined Stage B (real û1→L2 chain) ONLY at a split where BOTH legs passed.

## 3. Alternative mechanisms (only if trade scan fails)

- (b2a) MAP/enumeration over L1: content 26.28 bits; most of 1024 symbols near-deterministic (per-symbol H 0.0257 bits). Method: from γ1 count positions with max-posterior <0.99 (or entropy > t) → k uncertain GF(32) symbols; 32^k enumeration (k=5 → 33M borderline; k≥6 infeasible) + syndrome check. Cost: new decoder entrypoint + leakage re-derivation; needs a γ1-count first (no execution here).
- (b2b) Per-frame partitioned checks (n=256, m1'=3–4/frame): check deg 512/3 ≈ 171, /4 = 128 — SAME density, 4× failure points. No density gain; not recommended.
- (b2c) Different L1 family (QC/dense-optimized short high-rate code, algebraic/RM-like): plausibly the right fix for dense regime but a new construction path + pins + packet. Develop second, after (b2a) count.
- (b2d) PA-aware accounting reframing (see LITERATURE_PA_AWARE): parallel, changes claim basis, fixes no decoder. Keep as background only.
- Order if scan fails: count uncertain-k from γ1 (read-only arithmetic) → (b2a) if k ≤ ~5 → else (b2c) new-family packet.

## 4. Recommendation + scan packet outline (no-auto-proceed)

- Recommend: freeze a combined scan packet — Arm L2a m2=192 (+optional L2b m2=196) P0-style; Arm L1a m1=16 (+optional L1b m1=12) Stage-A-style; gates §2; budgets P0 caps (≤900 s est, 1 window ≤3600 s, RSS <4 GiB, ≤1 resume, early-stop at 13th fail).
- Interpretation rule: L2@192 PASS AND L1@16 PASS ⇒ Stage B packet at 192+16 MAY be frozen (not executed); any leg FAIL ⇒ return to main thread for (b2a)/(b2c) decision. Scan NEVER authorizes Stage B execution; Stage B needs its own frozen packet + Pre-EXECUTE + fresh grant.
- No-auto-proceed markers: no Stage B on partial/single-leg pass; no pooling across m; no monotonicity inference (192⇏196); paired-block reuse carries no independence claim.

## 5. Does-not-establish; no authorization

- Establishes no code, threshold, FER, or route claim. Authorizes NOTHING; scan packet needs freezing + review + grant before any execution.
