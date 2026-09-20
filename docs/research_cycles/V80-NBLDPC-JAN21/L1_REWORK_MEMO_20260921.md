# L1 rework memo (2026-09-21) — EXPLORE planning-only, design memo

- Track EXPLORE planning-only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Parents: L1 memo + L1B packet (E1 pins) + L1B pre-exec (dry-construct STOP) + P0 result (A202/A200 PASS, genie-u1).
- Goal: unblock Stage A after m1 dry-construct STOP. Non-goals: no code, no execution, no authorization, no FER/route claim.

## 1. Diagnosis: dense-check regime — fc==0 is the wrong gate for m1 legs

- Measured (pre-exec Q5, seed 2026092001/trials 20): m1=6 fc=34608/girth 4; m1=8 fc=18368/girth 4 — rank-full + twice-identical HELD, fc pin refused both (STOP-BLOCKED, zero decodes). m2 legs gate-clean (202/200: fc0/g8/rank-full/twice).
- Mechanism (memo §2a confirmed): n=1024, all-dv-2 → 2048 edges over 6–8 checks ⇒ avg check degree ≈341 (m1=6) / 256 (m1=8). This is ∅ sparse LDPC: every check touches ~1/3–1/4 of all symbols; any two vars sharing ≥2 of 6–8 checks form a 4-cycle — unavoidable by pigeonhole, not a PEG-seed defect. No reseed/retune fixes combinatorics.
- Root cause: the fc==0/girth-≥6 pin was copied from the L2 sparse regime (m≈200, check deg ≈10) where fc=0 is attainable. Applied to m1=6–8 it gates on an impossible property.

## 2. Options analysis (cost/feasibility; ★ = changes science inputs ⇒ new packet + review)

- (a) AMEND L1B E1 pins for m1 legs only: DROP fc gate; keep rank-full + twice-identical GATED; fc/girth RECORDED as covariates (R2/P0 precedent for girth). Cost: executor-only pin edit + focused fake tests; zero new science. Then Stage A measures the real question: does q=32 SPA converge on a dense 6–8-check graph at tiny entropy (26.28 bits)? Cheapest decisive probe. Risk: SPA may not converge (dense graph, weak extrinsic) — that outcome IS data, not a gate failure.
- (b1) ★ L1 as 4× shorter codes (n=256, m1'=2/frame; 4×2=8 rows/1024-equiv). Same budget hit. Per-code check deg 512/2=256 — STILL dense; 4× failure points; new code family ⇒ new packet + new pins + full Stage A redesign. Fallback only.
- (b2) ★ Different L1 mechanism (syndrome-only / guess-and-check per block exploiting 26.28-bit entropy; or reduced-search over u1 support). Science change: leakage formula + decoder entrypoint + gate semantics all re-derive. Feasible but a new method packet, not an amendment. Fallback if (a) shows dense-SPA failure.
- (b3) ★ Account L1 differently (e.g., BCH-like over 10-bit symbols). FROZEN: no BCH path exists in repo; leakage basis (5 bits/row GF(32)) + GF(32) decoder chain assumed throughout. Open question, not a scoped alternative — would need full proposal. Not recommended now.
- (b4) ★ L1 as separate channel-facing step with own budget line (re-derive f within f≤1.3). Breaks frozen total-rows=208 accounting (packet §1: leak 1104 fixed); any re-derivation re-opens S2 map + program-plan §1.3. Last resort only.

## 3. Recommendation: (a) first, (b1/b2) as fallback

- Amend E1 for the m1 legs, run Stage A unchanged otherwise (blocks, gates, budgets, stop rules frozen). If A6/A8 FAIL empirically ⇒ escalate to (b1/b2) rework, not another pin tweak.
- EXACT AMENDMENT TEXT (replaces L1B packet §1 pin bullet for m1 legs; m2 legs unchanged):
- "Pins — m1 legs (1024,6)/(1024,8): rank-full AND construct-twice-identical GATED (mismatch ⇒ STOP-BLOCKED); four_cycles + min_girth RECORDED-not-gated as covariates (dense-check regime: expected fc>0/girth 4, memo 20260921 §1). Pins — m2 legs (1024,202)/(1024,200): fc==0 AND rank-full AND twice-identical GATED; girth recorded. f_L1 informational only, never gated."

## 4. Blind-budget tie-in

- Total rows fixed at 208 (C6/C8) ⇒ leak 1104, headroom 4.31 bits UNCHANGED by this amendment. Blind options remain queued; any D_blind>4 bits still fails gate (b). Row-count trade (m1≥6 capacity floor; m2≥~200 given A188 FAIL/A200 PASS) is untouched — amendment changes constructability gating only, not budget.

## 5. Does-not-establish; no authorization

- Establishes no L1 code, threshold, FER, or route claim. Authorizes NOTHING; amendment needs frozen-packet edit + review + fresh Stage-A grant before any execution.
