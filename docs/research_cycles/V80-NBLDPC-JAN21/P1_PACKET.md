# P1 Experiment Packet (2026-09-21) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only (EXPLORE_HEAVY cost annotation). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-P1 (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh explicit grant per arm required (§8).
- Planning authority: `docs/ROADMAP-20260921.md` §2 (DECISION-1/2) + §3 P1 + §4 decision tree + §8 review table. This packet implements the roadmap's corrected P1 (review items 3/6/7/10); it does not re-decide anything.
- Parents: `B2F_RESULT_20260921.md` (F208 0/240, F202 6/240 @seed 2026092001) + `B2G_RESULT_20260921.md` (F208 0/240, F202 4/240 @seed 2026092011) + `P0_RESULT_20260920.md` (genie A200 2/240, A202 0/240) + `S2_ROUTE_DECISION_MEMO_20260921.md` (E1 cliff, E3 b2e, E6 L1B) + `SCAN_INTERRUPT_20260921.md` (A192 13/124, A196 no verdict) + `F_EFF_ACCOUNTING_NOTE_20260921.md` (slope, f vs f_eff) + `S2_ACCOUNTING_MAP_20260920.md` + `L1_CONSTRUCTION_MEMO_20260920.md` §1 (m1+m2≤208 box) + read-only code (`v80_o1_campaign`, `v80_s2c_campaign`, `v80_b2f_campaign`, `v80_b2g_campaign`, `nonbinary_v28`, `nonbinary_v10_fftqspa`, `peg`).

## 1. Hypothesis (to test, NOT a claim)

- H: under the exact Bayes-marginal L2 prior (b2f lineage, D-u1 = 0.0 structural), blocks that fail at m_base = 200 are rescued by an incremental +8-row syndrome (total 208), so the post-rescue (final) FER = 0 with expected leakage inside the frozen box — i.e. the genie L2 cliff (E2: 8 rows move FER 10.5% → 0.83% between m2 = 192 and 200, `S2_ROUTE_DECISION_MEMO_20260921.md` E1 / `SCAN_INTERRUPT_20260921.md`) is *rescuable* by rate adaptation (Kasai 2010 / Müller blind / Chen 2025 IEEE 11440984 lineage, per roadmap §3 P1).
- Mechanism basis (enacted, not speculated): on the SAME paired 240 frames, every soft-marginal F202 failure (b2f 6/240, b2g 4/240) lies inside a frame set that the m = 208 code decodes cold at 0/240 (both instances) — "+6/+8 rows do rescue these exact blocks" when delivered as a cold full-matrix decode. What is UNMEASURED: (a) the m = 200 soft-marginal baseline FER; (b) whether the rescue works through the *incremental* (nested) construction; (c) warm-start dynamics (excluded by design, §3).
- Pre-registered NON-prediction: the m = 200 soft-marginal baseline FER is a MEASURED outcome with NO point prediction. The roadmap's conditional arithmetic (IF base fails ≈ 10/240 AND all convert THEN E[leak] = 1065.7 b ⇒ f ≈ 1.250, headroom ≈ 42.6 b, N ≥ 288) is quoted as arithmetic only; "10/240" has no direct evidence (6+4 summation is the banned cross-instance pooling, roadmap §8 item 10). The packet freezes the computation rule (§5), never the outcome.

## 2. Frozen accounting (quoted, unchanged)

- Whole-frame-with-tag basis. Superframe n = 1024 GF(32) symbols, n_bits = 5120, H_full = 0.83256272 b/symbol, content = 852.544 b/frame (`PROGRAM_PLAN.md` §1.3; `L1_CONSTRUCTION_MEMO_20260920.md` §1).
- f_super = (5·(m1+m2)+64)/852.544 ≤ 1.3 ⇒ total leak ≤ 1108.31 b ⇒ m1+m2 ≤ 208 (hard integer cap). A208: leak 1104, f_super = 1.294947, headroom 4.31 b. A202: f_super = 1.259759. A200: leak 1064, f_super = 1.24803 (`P0_RESULT_20260920.md`; `L1_CONSTRUCTION_MEMO_20260920.md` §1; `O1_EXPERIMENT_PACKET_20260920.md` L36).
- f_eff = f_super + 4.785675·FER on each arm's OWN basis. NEVER report f_super as f_eff (`F_EFF_ACCOUNTING_NOTE_20260921.md` §5; per-arm-own-basis rule, `B2G_RESULT_20260921.md` GBR-1).
- Out-of-box arms, DELETED (roadmap §8 item 3): m_base = 202+8 = 210 rows ⇒ f = 1.30668 > 1.3; m_base = 200 two-segment ⇒ 216 rows ⇒ f = 1.34185. ONLY m_base = 200 + Δm = 8 single segment (total 208) stays inside.

## 3. Frozen construction (nested; the E[leak] formula requires it)

- Per construction instance (2026092001 = R1, 2026092011 = R2): ONE matrix — the frozen same-instance A208 matrix (fc = 0, rank-full 208, twice-identical already pinned in b2f/b2g manifests). NO new 208-construction.
- Base code = rows [0,200) (LEADING 200 rows) of that A208 matrix. Rescue transmission = rows [200,208) syndrome (40 b). Rescue decode = COLD full-matrix decode with the same A208 matrix (rows [0,208)).
- Why nested (explicit): a non-nested fallback (base-A200 syndrome + full-A208 re-disclosure) would cost rescued blocks 1064+1104 b and breach the box at any non-trivial trigger rate; only the nested form makes the frozen E[leak] = 1064+40·r mechanically honest. A deployed scheme would use purpose-built rate-compatible codes; this batch tests the rescue/efficiency hypothesis, NOT nested-construction optimality (stated caveat).
- Consequences (frozen): the base code is NOT P0's A200 (`construct_arm("A200",…)`); P0/genie anchors are context, never predictions. Base-submatrix quality is itself measured (Stage 1). WARM-START IS FORBIDDEN: both stages decode cold from the prior (warm-start dynamics ≠ cold m = 208 decode — retained unknown, roadmap §3 P1). Submatrix pins at Pre-EXECUTE (dry, zero-decode): rank = 200 REQUIRED (else STOP-BLOCKED); girth MEASURED-recorded-not-gated (P0/B2G precedent). 208-matrix pins carried (already verified, re-asserted).
- Prior/decoder (b2f lineage, verbatim): π_i(e) = Σ_u1 γ1(u1|b_i)·γ2(y_i⊕e|u1,b_i), y_i = b_i&31, via `marg = np.einsum("nu,nuv->nv", g1c.T, cond)` + row-guard + `center_rows_prior`; feed `v28.decode_error_domain_posterior(field, y.tolist(), dense, s_x, prior, 300)`; max_iter = 300/streak 3; per-decode cap 300 s; accept = `exact_match`; NO genie u1, NO argmax û1, NO L1 code (`B2F_EXPERIMENT_PACKET_20260921.md` §2).

## 4. Arms (EXACTLY two — one per construction instance; report separately, NO pooling)

- **P1-R1**: instance 2026092001 (girth 8 recorded, `B2F_RESULT_20260921.md`). **P1-R2**: instance 2026092011 (girth 6 recorded, `B2G_RESULT_20260921.md` GBR-4). Each arm = 240 paired blocks, seeds 2026095601+idx idx 0..239, stream `o1_blk:{seed}` (SAME frames as O1R/P0/L1B/b2e/b2f/b2g — paired contrast, NO independence claim, no cross-instance pooling per `B2G_RESULT_20260921.md` §"Does NOT establish").
- Each arm executes TWO frozen stages (§5). This realizes the authorized "2 instances × {baseline-only, rescue}" structure; budget ceiling ≤ 4 arm-equivalents, 2 executed — unspent budget is NOT authorization. Joint A2 is NOT in this packet (DECISION-2: demoted to P4 construction sub-arm).

## 5. Procedure + metrics (frozen computation rule)

- Stage 1 (baseline-only): decode all 240 blocks with the base (leading-200) code. Log per block: status, iters, decode_s, `prior_entropy_bits` + `u1_mismatches` (report-only, b2f precedent). Baseline fails k/240 = [TO BE MEASURED].
- Stage 2 (rescue): for EXACTLY the Stage-1 non-`success` blocks (exact_match false; any syndrome-valid-but-mismatched block logged separately as `undetected`-class, NEVER merged into success), disclose rows [200,208) and COLD re-decode with the full 208 matrix. Final fails F/240 = [TO BE MEASURED].
- Frozen metrics: trigger rate r = (#rescued)/240; E[leak] = 1064 + 40·r; f_exp = E[leak]/852.544 (arm's OWN blended basis); f_eff = f_exp + 4.785675·(F/240); headroom = 1108.31 − E[leak]; wall total + per-block mean, peak RSS. Conditional reference (arithmetic, NOT prediction): r = 10/240 ⇒ E[leak] = 1065.7 ⇒ f ≈ 1.250 ⇒ headroom ≈ 42.6 b ⇒ N ≥ 288 (roadmap §3 P1).

## 6. Gates (AND; §8 review items 6/7 incorporated)

- (a) Final fails/240 = **0** (HARD — DECISION-1 certifiability scope: zero-failure arms ONLY; 1 fail in 240 ⇒ Clopper–Pearson upper ≈ 1.94% ≫ 1.045% allowance at f ≈ 1.25, `docs/ROADMAP-20260921.md` §2). Retained context (no verdict rides on it): Stage-1 baseline reported against internal bar fails ≤ 12 (FER ≤ 5% route continue/stop gate, DECISION-1).
- (b) f ≤ 1.3 on the arm's own basis: worst-case (all-triggered, total 208) f_super = 1.294947 ≤ 1.3 by construction AND f_exp ≤ 1.3 (implied by (c)).
- (c) Headroom = 1108.31 − E[leak] ≥ **21.5 b** (⇔ required N ≤ 570; 20 b would imply N ≥ 612 — NOT used, roadmap §8 item 6). Effective trigger cap: r ≤ (1086.81−1064)/40 = 57.0%.
- Interpretation: PASS (all three) ⇒ report to main thread; decision-tree PASS branch (P3 audit → P5 n = 1024). FAIL (any gate, incl. rescue non-conversion ⇒ "cliff not rescuable") ⇒ return to main thread; decision-tree FAIL branch (P4 becomes S3-mandatory). Neither authorizes anything further.

## 7. Budgets / scope / stop

- Per arm: 240 Stage-1 decodes + ≤ k rescue decodes; wall ≤ 3600 s TOTAL (both stages, single window); per-decode ≤ 300 s (overrun = terminal, block counted fail, no continuation); RSS < 2 GiB; 1 CPU. Cost bracket: F208 672.6 s / F202 1346.9 s per 240 decodes (`B2F_RESULT_20260921.md`).
- Roots `workspace/p1_<uuid8>` fresh additive per arm (UUID + absence proven at Pre-EXECUTE); `results/` + `comparison_bench/outputs_comparison/` forbidden. New thin campaign module only; ALL frozen modules read-only; fake-only tests (contraction, nesting row-split identity rows[0,200)+rows[200,208) = rows[0,208), cold-restart wiring, trigger-set exactness, E[leak]/f/headroom arithmetic, bar/headroom gates, root refusal). No production decode in tests.
- STOP on any science-input change (n/m/tag/H/λ/seeds/thresholds/channel/decoder/hypothesis/data roles). NO retry/resume/adaptive search (stricter than b2f precedent, frozen here): wall-partial ⇒ INCOMPLETE-wall retained, no continuation. ONE preregistered engineering repair+rerun allowed SOLELY for infrastructure failure (process death, no verdict possible) with UNCHANGED scientific inputs — failed attempt retained in the same log; any second failure ⇒ batch FAIL (EXPLORE contract, AGENTS.md §1.2).
- FORBIDDEN (always): touching any existing evidence root; real/Jan-21 data; changing m, tag, H_full, n, or any gate; pooling across construction instances (incl. 6+4-style sums); merging `undetected` into success; quoting f_exp/f_super as f_eff when F > 0; warm-start; second construction matrix per instance; two-segment rescue.

## 8. Entry evidence + authorization gate (EXPLICIT USER GATE — STOPS HERE)

- Entry: (a) executor built per §7; (b) Q0–Q6 Pre-EXECUTE (branch `formal-ir-v72p1-addendum-clean`; scope cleanliness; frozen contract §§1–7; output-absence + rg proofs — `2026095601–5840` hits only in frozen docs+roots, `p1_` absent; focused tests incl. dry submatrix-rank pins per instance + 1-block dry decode per stage); (c) FRESH EXPLICIT USER GRANT per arm ("P1-R1 execute" / "P1-R2 execute" — this packet's freeze is NOT a grant).
- Deliverables per arm: `P1_RESULT_*.md` (verdict, Stage-1 k/240, rescue conversions, final F/240, r, E[leak], f_exp, f_eff own-basis, headroom, wall/RSS, per-60 tally report-only, undetected log) + `rows.json` + `block_accounting.csv` per root. Prompt: `P1_PROMPT.md`.
- Batch: ONE append-only `EXPLORATION_LOG.md` (attempts, preregistered repair if used, final evidence) + ONE batch-end independent review (no per-arm review). Claim ceiling: synthetic paired frames; rate-adaptation efficiency only; NO real-data/FER/SKR/qualification/publication claim. This packet authorizes NOTHING.
