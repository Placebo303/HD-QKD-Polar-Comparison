# V80 S2 Route Decision Memo (2026-09-21) — EXPLORE planning-only, decision support after the b2e FAIL

- Track EXPLORE planning-only (no code, no execution, no authorization, no route decision). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ≤80 lines.
- Parents: `B2E_RESULT_20260921.md` + `B2E_BATCH_END_REVIEW_20260921.md` (MAP-u1 13/13 both arms), `L1_REWORK_MEMO_V3` (γ1 stats; b2a/b2c/b2d), `L1_REWORK_MEMO_V2` (trade scan), `L1_CONSTRUCTION_MEMO` (m1+m2≤208, m1≥6), `P0/O1/O1R_RESULT` (L2 cliff), `L1B_STAGE_A_RESULT`, `S2_ACCOUNTING_MAP` (frozen convention), `PROGRAM_PLAN` §S2/§S3, `LITERATURE_PA_AWARE.md`.
- Goal: give the main thread a closed evidence statement and ranked options for the NB-LDPC S2 route. Non-goals: no code, no execution, no authorization, no FER/route/S3/qualification/publication claim.

## 1. Evidence closure — what is established (observations + provenance)

| # | Established observation | Provenance |
|---|---|---|
| E1 | Under genie-u1 the L2 leg passes only at m2≥200: A200 2/240 (0.83%) PASS, A202 0/240 PASS, A208 0/240 ×2 PASS; below it A188 4/14 (28.6%) FAIL-early-stop, A192 13/124 (10.5%) FAIL, A196 1/29 **no verdict** (interrupted). | P0_RESULT, O1_RESULT, O1R_RESULT, L1_REWORK_MEMO_V3 §1 |
| E2 | The L2 cliff is steep between m2=192 and 200: 8 rows (40 b) move block FER 10.5% → 0.83%. | L1_REWORK_MEMO_V3 §1 |
| E3 | MAP-û1 substitution kills every tested block: 13/13 fails in BOTH arms, all `max_iter_reached` at 300 iters (~70–77 s/decode); mean 7.69 mismatches/block (max 13); gate (b) B202 1.2905 PASS / B208 1.3257 FAIL; arm verdicts FAIL(a) / FAIL(a+b). | B2E_RESULT + B2E_BATCH_END_REVIEW |
| E4 | Failure mode is non-convergence, not converged-to-wrong-codeword. Attribution to the MAP substitution rests on the paired genie arms O1R/P0/L1B (no independence claim). | B2E_BATCH_END_REVIEW §4 |
| E5 | γ1 layer: block entropy 26.28 b (H_L1=0.02566205/symbol); uncertain columns mean 31.4/block, P(k≤4)=0 over 1e6 blocks; 973/1024 columns deterministic; top-5 entropy share 17% ⇒ enumeration (b2a, 32^k≈4.6e46) infeasible. | L1_REWORK_MEMO_V3 §2.1 |
| E6 | Dense-check L1 fails at the affordable sizes: C6 (m1=6) 13/27 = 48.1% FAIL-early-stop; C8 (m1=8) 6/85 = 7.1% RAW FAIL(budget, 1120.7 s > 300 s cap). m1≥6 is the content floor (26.28 b / 5 = 6 rows, f_L1(6)≈1.142). | L1B_STAGE_A_RESULT, L1_CONSTRUCTION_MEMO §1 |
| E7 | Inside the frozen box (m1+m2≤208, f_super≤1.3 with tag) **no** configuration has both legs passing: m1=6/8 FAIL (E6), m1=10–16 never executed, and funding them needs m2≤196, i.e. A188/A192 (FAIL) or A196 (unresolved). | L1_REWORK_MEMO_V3 §1 |
| E8 | Frozen accounting: f_super=(5·(m1+m2)+64)/852.544 ≤ 1.3 ⇒ total leak ≤ 1108.31 b, m1+m2≤208; A208 headroom only 4.31 b (< 1 row). | S2_ACCOUNTING_MAP, L1_CONSTRUCTION_MEMO §1 |

## 2. Options

### O-A — New u1 mechanism / joint single-layer design (b2c family)

- **A1. u1-repair by a small dense code with a NON-SPA decoder.** Change: keep m1=6–8 but replace FFT-SPA with hard-decision bit-flipping / one-step majority-logic + syndrome check. Cost: new decoder entrypoint + one packet (~600–900 s). Expected value: LOW-MODERATE — density is pathological (avg check degree 341 at m1=6, 256 at m1=8, girth 4 recorded) and f_L1(6)=1.142 leaves ~0 margin against 26.28 b of residual entropy; C6/C8 already show SPA's failure is density-driven, not iteration-driven. Risk: another dead leg inside a box that E7 already closes. Evidence that would decide: one C6-class arm with a non-SPA decoder; PASS would reopen the m1=6/m2≤202 split.
- **A2. Joint (u1,u2) single-layer factor graph.** Change: one NB-LDPC code over the 1024 GF(32)² pairs = 2048 GF(32) symbols, m≈208 rows, dv=2 ⇒ 4096 edges, **avg check degree 19.7** — versus 9.8 (L2-only) and 256–341 (L1-only). The layered split is what creates the undecodable dense layer; a joint code sits in the healthy density regime and needs no L1 construction, no u1 estimator, no L1↔L2 error propagation. Arithmetic (not a promise): error load ≈5–8% of 2048 ≈ 100–165 wrong symbols ≈ 500–825 b of error entropy vs 1040 b of syndrome ⇒ rate-wise comfortable, same margin as the genie arm. Cost: new MC-DE arm at the new length/rate + new construction (PEG, cycle control) + re-derivation of the disclosure basis (5m+64, unchanged formula, n=1024 denominator) + ~2× decode wall (~1100 s for 240 blocks). Risk: largest science change after O-B; DE threshold at the joint rate is unverified; S1→S2 chain continuity invalidated. Evidence that would decide: one MC-DE threshold point + one construction/FER arm at n=2048.
- **A3. Soft-marginalized (Bayes-optimal) L2 prior — the u1 estimator replaced by exact marginalization.** Change: feed the L2 decoder `P(U2|B) = Σ_u γ1(u|B)·γ2(·|B,u)` instead of conditioning on a u1 point estimate. Both factors are already frozen arrays (`g1` (32,1024), `g2` (32,32,1024)); the delta is ~10 lines in a thin new wrapper, no new code, no DE, no L1 construction, no accounting change (Bob's prior is computed from b alone ⇒ D-u1 = 0 measured, gate (b) unchanged at 1.294947). Why it is not foreclosed by b2e: chain rule gives H(U2|B) = 852.544 − 26.278 = **826.27 b**, essentially equal to the genie-conditioned H_L2·n ≈ 0.807×1024 = **826.37 b** ⇒ U1⊥U2|B holds to ~0.1 b, so the marginalized prior carries the *same entropy* as the genie prior; b2e only falsified the hard argmax commitment, not the information content. Precedent in-repo (frozen, read-only): v72p2d3/d7 L1→L2 recombination `q=softmax(L1 beliefs)`, `prior_l2 = q@P`. Cost: one arm ~550–600 s (A208-class) + negligible 32×32×1024 contraction. Risk: the mixture prior is flatter at the 31 uncertain columns (γ1 p_max≈0.71) and BP may still not converge; no baseline exists for this exact configuration. Evidence that would decide: FER at m=208 (240 paired blocks, gates fails≤12 AND f_super≤1.3). PASS ⇒ genie retires with no L1 code at all; FAIL ⇒ the u1 information loss itself is fatal at this budget and A2/O-B/O-D govern.

### O-B — Design-point change (n=2048, different q/rate, or abandoning the layered structure)

- What changes: a new MC-DE arm (S1 is rate-defined; the ensemble result at rate 0.797/n=1024 does not transfer), a new construction arm (PEG at n=2048; constructor support unchecked — the same uncertainty that O1 scoping carried for n=1024, which resolved feasible), and a new accounting line under the same frozen formula (content 2048×0.83256272 = 1705.088; m=416 ⇒ leak 2144, f = 1.25734, headroom 72.6 b vs 4.31 b today — the 64-bit tag share falls 0.0751 → 0.0375).
- Cost: ~2 DE runs + 1 construction + 1 FER arm; wall ~1100 s/arm. Evidence already pointing here: E2 (the cliff needs ~200 rows at n=1024, i.e. the design sits *on* the edge, not inside it) and A2's density argument. Note: O-B is a superset of A2's construction work — fund it *as* A2, not standalone.

### O-C — Accounting relaxation (b2d) — arithmetic, then claim cost

| Variant | Arithmetic | Relief | Claim cost |
|---|---|---|---|
| Tagless (drop the 64-b tag) | 1040/852.544 = 1.21988; headroom 68.31 b (13.66 rows) | **+64 b / +0.0751 f / 12.8 rows** | Violates the frozen "whole-frame with tag" authority (PROGRAM_PLAN §1.3, S2 map §3); tagless f is not comparable to published f. Report-only sensitivity line at most. |
| Layer-local basis | 1040/(1024×0.807) = 1.25854; headroom 34.28 b | +30 b / 6 rows | Same authority-rule violation (mixes layer-local with the 1.3 budget) and ignores the L1 leak. Report-only. |
| Per-frame n=256 with tag | (5m+64)/213.136 ≤ 1.3 ⇒ m ≤ 42/frame | **−10 rows/frame (−200 b)** | Not a relaxation: stricter than the superframe. The frozen superframe already captured the only tag-amortization gain available at fixed code length. |
| PA-aware (Tauz ITW 2024) | 0 b of f relief | **0 bits**; relaxes the FER gate (subset-success banks the same final key at fixed leak) | Needs Block-MDS/full-rank-complement construction + re-proof under our tag/leak books; misfits at rate 0.9 (S = 90% of symbols ⇒ ~7 of the 7.7 wrong symbols land inside S) and cond.-independence untested on Jan-21. Keep deferred to S3. |

Conclusion: **no accounting-only change both preserves the frozen claim basis and buys usable relief**; the binding constraint is decodability (E3/E6), not budget.

### O-D — Pause / close the S2 route with evidence archived

- What remains true and worth keeping: the S1 DE ensemble result; the O1R genie A208 PASS ×2 as a synthetic upper bound (0/240 at f=1.294947); the E1–E8 closure as a documented negative route. Cost zero. Risk: premature only if A3/A2 are judged worth one packet each; closing forfeits the A3 hypothesis, which b2e did not test.

## 3. Ranked recommendation (ADVISORY — the main thread decides)

1. **A3 (soft-marginalized prior) — recommended next, and the only probe I would fund before any new construction.** It is the cheapest decisive experiment on the table (~600 s, ~10 lines, no DE, no L1 code, no accounting change), it is *not* foreclosed by b2e (which tested only the hard argmax), and its entropy arithmetic (826.27 b vs 826.37 b) says it has the same rate margin the genie arm enjoyed. A PASS dissolves the whole layered blocker at once.
2. **A2 (joint single-layer, funded together with the n=2048 DE/construction work of O-B)** if A3 FAILs — highest structural value; the density argument (19.7 vs 256–341) is the only mechanism on this page that explains *why* the layered split is stuck.
3. A1 (non-SPA dense L1) — one piggyback arm at most; E7 already closes the box it lives in.
4. O-C — report-only sensitivity lines only; never a claim basis.
5. O-D — hold as the co-default if A3 FAILs and A2 is judged too expensive; archive E1–E8 either way.

## 4. Decision checklist for the main thread (yes/no) + no-auto-proceed

1. Authorize freezing an **A3 probe packet** (one arm m=208, 240 paired blocks `2026095601+idx`, gates fails/240≤12 AND f_super=(5·208+64)/852.544 = 1.294947 ≤ 1.3 with D-u1 = 0 measured)? Optional secondaries m=202/200 to probe cliff robustness.
2. If A3 PASSes: require an A208-class two-construct-seed replication (~1100 s) before any genie-retirement wording?
3. If A3 FAILs: fund A2 + the n=2048 DE/construction arm, or close the route (O-D)?
4. Is **A196 (m2=196)** worth one re-run? It is the only unexecuted point inside the cliff and the only funding source for m1=12 — but C12A (m1=12) was never executed either, so the split needs BOTH legs; recommendation: no re-run unless item 3 selects A1.
5. Are tagless / layer-local numbers allowed anywhere beyond report-only sensitivity? Recommendation: no.
6. Keep PA-aware (Tauz) deferred to S3 as currently tagged, or pull it forward as a synthetic FER-gate relaxation? Recommendation: keep deferred.
7. Confirm the A3 row formula and normalization (`Σ_u γ1(u|B)·γ2(·|B,u)`, XOR-centering by the true u2) at packet-freeze time — one-line convention check, no execution.

No-auto-proceed markers: this memo authorizes NOTHING — no execution, no packet freeze, no S3 entry, no route decision. Any new packet needs its own frozen packet + Pre-EXECUTE + fresh grant + batch-end review. No genie retirement is established by any existing arm (b2e falsified only *this* estimator). No cross-arm pooling; no monotonicity inference (A202 PASS ⇏ A200/A196 PASS). Paired-seed reuse carries no independence claim. Synthetic only — no real/Jan-21 frames.

## 5. Does-not-establish

No FER, no route/S3/qualification/publication claim; no L1-code necessity or sufficiency proof; no u1-repair-mechanism conclusion; no genie retirement; A196 carries no verdict; b2e establishes nothing about the u1 estimator beyond the hard-argmax path; all A2/A3 numbers above are hypotheses and arithmetic, not measurements. Records: no commit/push; branch untouched.
