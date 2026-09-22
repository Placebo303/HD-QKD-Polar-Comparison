# X1 Experiment Packet (2026-09-21) — FROZEN, NOT GRANTED

- Track: **EXPLORE** synthetic only (**EXPLORE_HEAVY** cost annotation: 15 arms). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-X1 (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh explicit grant per arm required (§8).
- Why synthetic (no new real-data read): the per-source joint channels are derived from **already-measured histograms materialized by the A1 census** (`workspace/p3_census_3954637c/`, per `docs/research_cycles/V80-NBLDPC-JAN21/P3_A1_REVIEW.md`). **No `.ttbin` access is authorized in this batch** — any `.ttbin` read is a STOP-BLOCKED science-input change (§7).
- Planning authority: user strategic directive 2026-09-21 ("test the WORST source, not the best"; anti-cherry-picking) + corrected design-point verdicts in `workspace/p3_census_3954637c/DESIGN_POINT_ARITHMETIC.md` (F-1 closure).
- Parents: `P3_A1_REVIEW.md` (§5 estimator rigor, §7 design-point table, findings F-1/F-4/F-5) + `P1_PACKET.md` (rescue rule, gates) + `P2_PACKET.md` (§3 single-instance curve precedent, §4 P1-ownership precedent) + `B2F_RESULT_20260921.md` (soft-marginal lineage, cost bracket) + `B2G_RESULT_20260921.md` (no-pooling rule) + `F_EFF_ACCOUNTING_NOTE_20260921.md` (slope 4.785675) + `KANITSCHAR_RELEVANCE_ADJUDICATION_20260921.md` (2M bundle provenance).

## 1. Hypothesis (to test, NOT a claim)

- H: the soft-marginal FER-vs-m cliff keeps its shape across sources with position set by each source's own H_full, so each source's operating point (m_base for P1 rescue) is settable from evidence, not from 2M assumption. All existing cliff data (A188/A192/A196/A200/A202/A208 genie + soft-marginal b2f/b2g) is on the **2M frozen channel only**; **m_min is UNMEASURED for every source**.
- Corrected per-source H_full (MM-corrected, `DESIGN_POINT_ARITHMETIC.md`): 1M **0.80361** (plug-in 0.79813); 1.5M **0.82896** (plug-in 0.82498); 2M **0.83458** (plug-in 0.83141). Anchor V49 TRAIN-pool 0.83256272 (`P1_PACKET.md` §2).
- Corrected m_max = floor((1.3·1024·H−64)/5): 1M **201**; 1.5M **207**; 2M **209 → capped at 208** (frozen integer cap m1+m2 ≤ 208, `L1_CONSTRUCTION_MEMO_20260920.md` §1, still binds for 2M). Thresholds: A208 needs H ≥ 0.829327 (=1104/1331.2); A200 H ≥ 0.799279; A199 H ≥ 0.795523.
- Corrected verdicts (use these, NOT the review's plug-in-only table): 1M **OUT@208** (threshold-H gap 0.0257 ≈9.0× bootstrap CI halfwidth 0.00285 — interval-halfwidth multiple, NOT a standard-deviation multiple; the bootstrap percentile interval does not bracket the plug-in point estimate — genuine) but **IN@200 (f=1.29300, N=2051) / @199 (f=1.28692, N=1098)**; 1.5M **INDETERMINATE@208** (0.82896 is 0.00037 below 0.829327, inside CI half-width 0.00221) but **IN@200 (1.25345, N=309) / @199 (1.24756, N=274)**; 2M **IN@208** (1.29181, N=1754) / @200 (1.24501, N=262) / @199 (1.23916, N=236).
- Alignment carried (§3A, correlation-derived, all `ok`, one-bin AGREE): 1M bin 8191 → −50 ps (p2bg 1186.3, σ 66.41); 1.5M bin 8192 → +50 (748.2, 70.71); 2M bin 8192 → +50 (546.1, 70.92) (`P3_A1_REVIEW.md` findings 1–3).

## 2. Frozen objective

- Measure the soft-marginal FER-vs-m cliff curve for EACH source, so (a) each source's operating point is known, (b) cross-source behaviour is characterized, (c) P1's per-source base rate is set from evidence not assumption (`P1_PACKET.md` §9 amendment consumes X1, never assumes it).

## 3. Frozen grid (15 arms; actual integers)

- Shape per source: {m_max−16, m_max−12, m_max−8, m_max−4, m_max}, spacing Δm=4 (=20 b leak steps). Justification: genie cliff width is 8 rows (E1: m2 192→200, `P1_PACKET.md` §1) plus ~26 b/block marginal-prior penalty ≈ 5 rows (FXR-1, `B2F_RESULT_20260921.md`); a 16-row span brackets plateau→cliff→floor for each source's own H; top pinned at own corrected m_max so every gate-(b) verdict is on that source's own basis.
- **X1-1M (m_max=201): {185, 189, 193, 197, 201}** — top = true max (f@201 ≈ 1.29907 ≤ 1.3; m=202 OUT).
- **X1-1.5M (m_max=207): {191, 195, 199, 203, 207}** — top avoids adjudicating @208 (INDETERMINATE: point f@208 ≈ 1.30055 > 1.3 but threshold gap inside CI).
- **X1-2M (m_max=209→cap 208): {192, 196, 200, 204, 208}** — uniform Δm=4 preserved by pinning top at the frozen cap instead of the raw 209; control arm on the frozen channel.
- 240 paired blocks per point. Seeds reuse the frozen literals `2026095601+idx` idx 0..239, stream `o1_blk:{seed}` (same integers as O1R/P0/L1B/b2e/b2f/b2g, `B2F_RESULT_20260921.md`) — per-source sampler draws differ by channel, so SAME integers carry NO cross-source frame-identity claim. Construction instance SINGLE 2026092001 for curve coherence (P2 §3 precedent); no new seed literals invented; workspace-root UUID `[TO BE FROZEN]` at Pre-EXECUTE.

## 4. Prior / decoder (per source; lineage b2f/b2g)

- b2f verbatim formula + v28 `decode_error_domain_posterior` max_iter 300/streak 3, `exact_match` accept, NO genie/argmax/L1 (`P1_PACKET.md` §3; `B2F_RESULT_20260921.md`).
- Channel bundle PER SOURCE from already-measured histograms (no `.ttbin`): 2M = frozen `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz` read-only (provenance `KANITSCHAR_RELEVANCE_ADJUDICATION_20260921.md` + `S2C_EXPERIMENT_PACKET_20260920.md`); 1M/1.5M bundles = **[BLOCKING — TO BE MATERIALIZED]** as read-only derived artifacts from the A1-census histograms. **Cross-source channel reuse is FORBIDDEN** (each source's γ differs).
- Standalone per-m constructs (A-series precedent, NOT P1 nested submatrices): pins fc=0 + rank-full + twice-identical GATED, girth recorded-not-gated (P0/B2G precedent). Arm IDs carry construction labels distinctly (X1-*-S<m>-standalone).

## 5. Metrics (frozen computation rule)

- Per (source, m): FER = fails/240, iters, wall/block, f_super = (5m+64)/(1024·H_source_corrected) on the arm's OWN source H, f_eff = f_super + 4.785675·FER (`F_EFF_ACCOUNTING_NOTE_20260921.md` §5). `undetected`-class logged separately, NEVER merged into success. NO pooling across sources, m-points, or construction instances.

## 6. Gates (AND)

- (a) fails/240 ≤ 12 internal route gate (5% continue/stop, DECISION-1 context — NOT certifiability).
- (b) f_super ≤ 1.3 on the source's OWN corrected H (§5 rule).
- (c) Certifiability rule N ≥ ceil(3·4.785675/(1.3−f_super)). **Plain consequence: (c) FAILs for essentially every arm** — at own m_max, N_req ≈ 15438 (1M@201) / ≈2708 (1.5M@207) / 1754 (2M@208) ≫ single-source pool counts 500/691/911 (`P3_CENSUS_PACKET.md` §9.2; F-5 keeps the two superframe quantities separate); arms that pass (a) sit at high m where (c) fails, arms that pass (c) sit at low m where (a) fails. **FORBIDDEN: presenting any single-source f_eff as a certifiable literature-comparable number.**

## 7. Budgets / scope / stop

- Per (source, m) arm: wall ≤ **1800 s** (cost bracket F202 1346.9 s/240, `B2F_RESULT_20260921.md`); per-decode ≤ 300 s terminal; RSS < 4 GiB; 1 CPU. **Total ceiling 15 × 1800 s = 27000 s.**
- Roots `workspace/x1_<uuid8>` fresh additive per arm (UUID + absence proven at Pre-EXECUTE); `results/` + `comparison_bench/outputs_comparison/` forbidden. New thin campaign module only; ALL frozen modules read-only; fake-only tests (per-source bundle binding refusal on cross-source channel, standalone-construct pins, bar/gate arithmetic incl. rule-(c), root refusal). No production decode in tests.
- STOP on any science-input change (n/m/tag/H/λ/seeds/thresholds/channel/decoder/hypothesis/data roles) — **re-reading any `.ttbin` or opening both pair members is STOP-BLOCKED**. No retry/resume/adaptive search; ≤1 preregistered engineering repair+rerun for infrastructure failure only, unchanged scientific inputs, failed attempt retained.
- Known overlaps (scheduling notes, NOT double-measurement): X1-2M points coincide with b2f citations (F202 6/240, F208 0/240 @2001, same channel/seeds — X1 re-measures as single-batch curve, citations retained as cross-batch consistency checks, never pooled); X1-2M m=200 is a STANDALONE construct, distinct from P1 Stage-1's nested leading-200 submatrix @2001 (both labeled, never equated; P2 §4 ownership of the P1 value stands); X1-2M {192,196,204} coincide with planned P2 arm-(ii) points (`P2_PACKET.md` §3 — main thread schedules ONCE, the other consumes by reference; `P2_PACKET.md` itself is NOT amended here).

## 8. Entry evidence + authorization gate (EXPLICIT USER GATE — STOPS HERE)

- Entry: (a) executor built per §7 (incl. 1M/1.5M bundles unblocked); (b) Q0–Q6 Pre-EXECUTE (branch `formal-ir-v72p1-addendum-clean`; scope cleanliness; frozen contract §§1–7; output-absence + rg proofs; focused tests incl. dry per-source bundle binding + dry-construct pins per m); (c) FRESH EXPLICIT USER GRANT per arm ("X1-<source>-<m> execute" — this packet's freeze is NOT a grant).
- Deliverables per arm: `X1_RESULT_*.md` (FER, iters, wall/RSS, f_super/f_eff own-basis, undetected log) + `rows.json` + `block_accounting.csv` per root. Prompt: `X1_CROSS_SOURCE_PROMPT.md`.
- Batch: ONE append-only `EXPLORATION_LOG.md` + ONE batch-end independent review (no per-arm review). Claim ceiling: synthetic per-source FER curves ONLY; NO FER/SKR/route/qualification/publication claim; **establishes no cross-source generality claim by itself** (generality needs P1 rescue PASS on 1M + comparison, `P1_PACKET.md` §9).

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved to the consolidated baseline. This file is retained as history. Executed evidence and review verdicts recorded here remain authoritative; do not cite its frozen clauses as current without checking the baseline.
