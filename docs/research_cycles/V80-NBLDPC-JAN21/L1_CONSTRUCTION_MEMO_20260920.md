# L1 construction memo (2026-09-20) — EXPLORE planning-only, design memo

- Track EXPLORE planning-only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Goal: retire genie-u1 ceiling (D1) with a real L1 construction path. Non-goals: no code, no execution, no authorization, no FER/route claim.
- Scope: this memo only (`L1_CONSTRUCTION_MEMO_20260920.md`); frozen refs quoted, nothing invented. Acceptance: ≤80 lines, numbers below traceable to cited code/docs.

## 1. Accounting coupling — RESOLVED: O1 m-rows were L2-only

- Verdict: O1 A188/A208 m=188/208 are the L2 single-code rows ONLY, not L2+L1 totals. Proof: `v80_o1_campaign.leak_basis` L350-396 `leak=m*5+64`, `f_super=(m*5+64)/852.544`; no m1 term; L1 carried as GENIE label only (packet §4/§9, O1R result D1).
- Combined-system constraint (frozen f_super basis, PROGRAM_PLAN §1.3 + S2 map §1): total leak = 5×(m1+m2)+64 ≤ 1108.31 bits (f_super≤1.3, content 852.544).
- Integer cap: m1+m2 ≤ floor((1108.31−64)/5) = 208. Current A208 headroom = 1108.31−1104 = 4.31 bits < one row (5 bits): ANY m1≥1 breaks budget unless m2 drops ≥1:1.
- L1 content: n·H_L1 = 1024×0.02566205 = 26.28 bits (S1_READINESS anchor). Capacity m1 ≥ ceil(26.28/5) = 6 rows (30 bits; f_L1 = 5m1/26.28; f_L1(6)≈1.142, f_L1(8)≈1.522).
- Trade: m1=6 → m2≤202 (rate 0.80273); m1=8 → m2≤200. L2 gives up 6–8 rows (30–40 bits) from the only passing point.
- Risk anchor: A188 (m=188) FAIL 4/14 early-stop, FER 28.6% ↔ A208 (m=208) PASS 0/60 + 0/240×2. The 188–208 cliff shape is unmapped; m≈200–202 is untested and sits inside that margin.

## 2. L1 design options (all n in GF(32) symbols, λ={2:1} default)

- (a) Same PEG at n=1024, m1≈6–8, rate 0.99414–0.99219. FEASIBILITY FLAG: all-dv-2 → edges 2048; avg check degree 2048/6≈341 (m1=8: 256). Each check touches ~341 symbols — extremely dense; expect girth collapse (fc>0), weak locality, heavy FFT-check cost. PEG trial pins (fc=0/girth≥6) will likely fail at first trial; do not assume scoping §5 transfers.
- Alt (a2): per-frame L1, n=256, m1'≈2/frame (content 6.57 bits/frame; 10 bits, f≈1.522). Check budget 4×2=8 rows/1024-equiv — same total, same budget hit. Pros: reuses n=256 PEG path, smaller/faster trials, frame-local decode. Cons: 4 small ultra-high-rate codes (avg check deg 512/2=256 — still dense), 4× failure points.
- (b) L1 DE need: one MC-DE threshold point via V26 kernel at the L1 rate with the L1 sampler (`v80_s1_mcde_runner.make_centered_sampler` L1 branch L492-506: b~p_b, u1~g1[:,b], XOR-centered; S1 CONFIRM convention). L1 rate ≈0.994 is far above the S1 L2 grid — threshold (f_L1≈1.14–1.52) is not inherited from any L2 DE cover.
- (c) L1 decoder mapping (frozen only, no invention): F03 `nonbinary_v25_gate.py:53` L1=`("gf32",5,[9,8,7,6,5])`; `factor_layers` v29 L269-273 `((values>>5)&31,(values&31))` → L1 obs y1=(b>>5)&31 (L2 was b&31); rows=`posterior_rows("L1",b)` = `p_u1_gb.T[b]` (v26_channel L236-237, no u1 conditioning — L1 decodes first); prior via `_center_rows` v28 L189-197 XOR; entrypoint `decode_error_domain_posterior` v28 L155-186. L1-first ordering (decode u1, then condition L2 on û1) is the structural change vs genie.

## 3. Gate implications + recommended pre-arm

- Combined dual-layer gate: block/frame success needs BOTH layers exact (genie ceiling retires; L2-only FER no longer sufficient). Error propagation (L1 û1→L2 rows) must be counted, never assumed away.
- Stats: mirror O1R width (240 blocks, paired seeds, ≤5% bar) for the combined gate once both codes exist; keep f_super≤1.3 AND-gated on measured D_blind.
- Main uncertainty = m2-reduction risk (§1 cliff). Recommended pre-arm (cheapest decisive probe, L2-only, BEFORE building L1): FER check of the SAME n=1024 PEG family at reduced m2 (A202 primary; A200/A206 optional arms) under genie-u1, O1 block semantics. If A202 fails, the m1+m2≤208 box has no confirmed L2 leg — stop before spending L1 construction/DE.
- Packet outline: P0 pre-arm (A202 genie FER) → P1 L1-DE threshold → P2 L1 PEG constructability (fc/girth pins) → P3 dual-layer combined FER. Risks: dense-check infeasibility; L1 f≈1.14–1.52 threshold miss; error propagation; zero budget slack (any D_blind>4 bits fails).

## 4. Does-not-establish; no execution; no authorization

- Establishes no L1 code, no threshold, no combined FER, no route/S3/real-data claim. This memo authorizes NOTHING; each packet above needs its own frozen packet + Pre-EXECUTE + fresh grant.
