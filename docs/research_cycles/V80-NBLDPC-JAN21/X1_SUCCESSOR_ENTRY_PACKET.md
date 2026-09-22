# X1 Successor Entry Packet (2026-09-21) — FROZEN, NOT GRANTED

- Track: **EXPLORE** (synthetic only; **EXPLORE_HEAVY** cost annotation: 15 arms × ≤1800 s = 27000 s ceiling). Zero `.ttbin` reads (STOP-BLOCKED per the retained clause). Zero decoder-kernel changes.
- Acceptance ID (proposed): **G-X1S** (successor entry; distinct from the frozen-never-granted G-X1 of the archived packet — that ID is history only and is NOT reused as authority). This packet is FROZEN, NOT GRANTED. It authorizes NOTHING.
- Planning authority: `docs/V80_BASELINE_20260921.md` (§0.1 retained-clause index rows for [X1] — the ONLY citable source of X1's frozen clauses; §1 invariants I1–I6; §3 corrected design points + certifiability; §5; §6-2 X1 step; §7). Every number below traces to baseline §0.1/§3 or the R1 artifacts; anything new is marked `[TO BE MEASURED]` / `[TO BE FROZEN]`; no new constant is introduced.
- Parent contracts (structure only, NOT current authority): `docs/research_cycles/V80-NBLDPC-JAN21/X1_CROSS_SOURCE_PACKET.md` + `X1_CROSS_SOURCE_PROMPT.md` (each carries a SUPERSEDED banner; retained for history — provenance pointers below go via the baseline §0.1 index, never directly to the archived files as authority).
- Entry-blocker close-out (the ONLY new fact since the freeze): the R1 histogram re-run (Acceptance ID G-R1, accepted 2026-09-21) EXECUTED and PASSED independent Pre-RESULT — sparse TRAIN `N_ab` + `p_b_train` are persisted and checksum-verified for all three Jan-21 sources in `workspace/r1_histogram_5e2a91c4/` (18 files). X1's 15 arms are no longer bundle-blocked, but they still require their OWN entry gate (this packet + prompt + prereg, fresh Pre-EXECUTE, explicit grant). Nothing in the baseline authorizes any X1 arm.
- Technical sources (every frozen clause restated FROM one of these; unknowns marked):
  - Retained-frozen X1 clauses: baseline §0.1 rows `[X1]§3` (grid), `[X1]§4` (prior/decoder/bundles), `[X1]§5` (metrics own-basis), `[X1]§6` (gates), `[X1]§7` (budgets/stop/overlaps); related overlap partition baseline §0.1 `[P2]§3`–`[P2]§§4–6`, P1-consumption baseline §0.1 `[P1]§9` / §7-6/§7-7.
  - Corrected basis: baseline §3 (R1-corrected `H_corr`, `m_max`, `f@208`, `N_req`, certifiability vs key-eligible 200/276/364) + `R1_PRERESULT_REVIEW.md` §§3–4 + `R1_INDEPENDENT_ACCEPTANCE.md`.
  - Bundle-input inventory: `workspace/r1_histogram_5e2a91c4/` (`T2-<SRC>.json` + `T2-<SRC>_N_ab_train_sparse.npz` + `T2-<SRC>_p_b_train.npy`, §2.6) + `R1_HISTOGRAM_RERUN_PACKET.md` §§2.5–2.7 (estimator definition, bundle sets, 2M report-only rule).
  - Bundle builder (pure numpy, no `.ttbin`): `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py` (`load_channel_counts()` L82–110, `ChannelAdapter` L123+).
  - Bundle consumer (zero code change): `comparison_bench/src/comparison_bench/formal_ir/v80_s2c_campaign.py:187` `bind_empirical_bundle()` (shape/normalization gates).
  - Blocker analysis + builder/consumer paths + cost + 2M-only sufficiency: `docs/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md` (T1–T5).
  - Disclosure-model conditional: baseline §2(a) + §5(ii)–(iii) (sacrifice-the-sample DEFAULT; amortized 0.18/0.099 b/blk; per-block-only m≤201 relocation).
  - Archive non-citability rule: `openspec/changes/amend-openspec-archive-superseded-before-execution/` (archived `2026-09-21-v80-x1-cross-source-cliff-superseded/` files are provenance only via the §0.1 index).
  - House packet style mirrored: `R1_HISTOGRAM_RERUN_PACKET.md` + `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` + `R1_HISTOGRAM_RERUN_PROMPT.md`.
- Source-key block (display labels; `{source}` bundle-key prefix separately frozen in §2.6): T2-1M (1M), T2-1.5M (1.5M), T2-2M (2M).
- Branch context: `formal-ir-v72p1-addendum-clean`; publication branch `formal-ir-v80-nbldpc-jan21`. No switch, no commit, no push, no PR in this packet.
- Planning only. NO execution, NO `.ttbin` access, NO workspace write, NO commit/push authorized or performed by this packet.

## §1 Purpose — per-source cliff curves → per-source m_min

1. Measure the soft-marginal FER-vs-m cliff curve for EACH Jan-21 source on its OWN channel bundle, yielding per-source `m_min` — the smallest `m` that passes the frozen route gate on that source's own basis. `m_min` was NEVER measured on any source; the A1/R1 census supplies `H`, not `m_min`.
2. Unlock P1's per-source rescue base (baseline §0.1 `[P1]§9`, §7-6/§7-7): P1 consumes X1 per source and never assumes 2M. No P1 arm runs here.
3. Settle the conditional m≤201 operating-point question — CONDITIONAL on the per-block disclosure model ONLY (baseline §2(a)): IF the disclose-statistic route were ever chosen under per-block charging, the operating point relocates to m≤201, inside the unmapped 188–208 cliff this step maps. Under the RATIFIED amortized/sacrifice-the-sample default ([DEC]§B; baseline §5-ii), m≤201 does NOT follow and this step is read as pure cliff characterization.
4. Hypothesis (to test, NOT a claim): the soft-marginal FER-vs-m cliff keeps its shape across sources with position set by each source's own `H_corr`, so each source's operating point is settable from evidence, not from 2M assumption. All existing cliff data is on the 2M frozen channel only.

## §2 Frozen design (restated FROM baseline §0.1 [X1] rows — baseline governs)

### §2.1 Sources (display labels; key prefix in §2.6)

- All three Jan-21 trio sources: **T2-1M, T2-1.5M, T2-2M** (display: 1M / 1.5M / 2M). Synthetic channel sampling ONLY — no `.ttbin` member is opened in this batch (any `.ttbin` read is STOP-BLOCKED, §2.8).
- Corrected basis (baseline §3, R1-corrected — gate (b) MUST use these, NOT the archived defective values; see §9 conflicts):
  - `H_corr` = **0.8012690084416184 / 0.8272902027770036 / 0.8333327179427281** (Δ vs defective −0.0023389196758668573 / −0.0016714841284448667 / −0.0012518869160380586, saturating the pre-registered bound at K_B = 1024).
  - `m_max` = **200 / 207 / capped-208** (1M 201→200 FLIP confirmed on measured K_B; 2M raw 209→cap 208, cap binds).
  - `f@208` = **1.34552190 (1M, OUT) / 1.30320049 (1.5M, nominal OUT; threshold-H gap vs CI halfwidth = 0.92 ⇒ statistical status INDETERMINATE-vs-OUT — planning treatment OUT on the frozen point-estimate gate (b)) / 1.29375096 (2M, IN on f-margin)**.
  - Certifiability vs key-eligible **200/276/364** (zero-failure still required): **1M NO everywhere** (m_max 200 N=4447; m=199 N=1541); **1.5M NO everywhere** (m_max 207 N=5315; m=200 N=327; m=199 N=288 — the defective-basis "YES-by-2-blocks PROVISIONAL" at m=199 FLIPS to NO); **2M m=200/199 YES-on-count** (271/244 ≤ 364), **m=208 f-IN but NOT count-certifiable** (2298 > 364), capped m_max 208 NO.

### §2.2 Frozen grid (15 arms; actual integers — baseline §0.1 [X1]§3)

| arm family | m values (Δm=4) | note |
|---|---|---|
| X1-1M | **{185, 189, 193, 197, 201}** | top 201 is the RETAINED-FROZEN grid top; it now sits ABOVE corrected m_max 200 (f@201 > 1.3 ⇒ expected gate-(b) OUT). Grid UNCHANGED (baseline retains it frozen); interpretation expects OUT — do NOT move the grid silently (§9-2). |
| X1-1.5M | **{191, 195, 199, 203, 207}** | top pinned at own corrected m_max 207. |
| X1-2M | **{192, 196, 200, 204, 208}** | top pinned at the frozen cap 208 (raw m_max 209 arithmetically valid but frozen-invalid); control arm on the frozen channel. |

- 240 paired blocks per arm. Seeds reuse the frozen literals **`2026095601+idx`**, idx 0..239, stream **`o1_blk:{seed}`** (same integers as O1R/P0/L1B/b2e/b2f/b2g) — per-source sampler draws differ by channel, so SAME integers carry NO cross-source frame-identity claim. Construction instance SINGLE **2026092001** for curve coherence. Workspace-root UUID(s) `[TO BE FROZEN]` at Pre-EXECUTE.

### §2.3 Constructs (standalone; baseline §0.1 [X1]§4 + [X1]§7)

- Standalone per-m constructs (A-series precedent, NOT P1 nested submatrices): pins **fc=0 + rank-full + twice-identical GATED**, girth recorded-not-gated. Arm IDs carry construction labels distinctly (`X1-*-S<m>-standalone`).
- **X1-2M m=200 STANDALONE ≠ P1 nested leading-200** (REVISE R6; baseline §0.1 `[X1]§7` + `[P1]§3`): the two m=200 values are NON-INTERCHANGEABLE (P2 §4 ownership: P1 owns its m=200 measurement; P2/X1 consume by reference, never substitute).

### §2.4 Prior / decoder (per source; b2f lineage — baseline §0.1 [X1]§4)

- **b2f verbatim** formula + v28 `decode_error_domain_posterior` **max_iter 300 / streak 3**, **`exact_match`** accept, NO genie/argmax/L1.
- Channel bundle PER SOURCE, read-only (§2.6). **Cross-source channel reuse is FORBIDDEN** (each source's γ differs) — executor refuses a channel whose source label ≠ arm source.
- NO decoder/DE/graph-kernel change in this batch. NO prior refit.

### §2.5 Metrics (frozen computation rule — baseline §0.1 [X1]§5 + I5)

- Per (source, m): **FER = fails/240**, iters, wall/block, **`f_super = (5m+64)/(1024·H_source_corr)` on the arm's OWN source `H_corr`** (§2.1), **`f_eff = f_super + 4.785675·FER`** (frozen slope) on the same own basis.
- **`undetected`-class logged separately, NEVER merged into success.** NEVER quote `f_super` as `f_eff` when FER > 0.
- **NO pooling** across sources, m-points, or construction instances. NO cross-m monotonicity assumption: report each arm as **monotone / non-monotone / censored** (bar-12 early-stop arms are CENSORED), no inference across m.

### §2.6 NEW entry task — build the 1M/1.5M (+verification-2M) channel bundles (precise spec)

This is the ONLY task that is new since the freeze; everything else is restatement. The factorization step is seconds of numpy with zero code change (assessment T3); the missing input it needed is now in the R1 root.

**Inputs (read-only; R1 root — the bundle-input authority, NOT the A1 root):**

- `workspace/r1_histogram_5e2a91c4/T2-1M_N_ab_train_sparse.npz` + `T2-1.5M_N_ab_train_sparse.npz` + (`T2-2M_N_ab_train_sparse.npz` — verification-only, see below), each with keys `row`, `col`, `count` (int64 COO triplets), `shape=(1024,1024)`, `N_train`.
- `workspace/r1_histogram_5e2a91c4/T2-<SRC>_p_b_train.npy` ((1024,) float64, sum = 1).
- `workspace/r1_histogram_5e2a91c4/T2-<SRC>.json` (checksums + scalars: `N_train` 315504 / 441487 / 589461; `K_AB` 2395 / 2439 / 2597; `K_B_train` 1024 ×3; `H_L1/H_L2/H_plug/H_corr/H_MM_old/Δ`; reconstruction sum + nnz; split side TRAIN; alignment fields).
- 2M frozen lineage (read-only reference, NEVER refit): `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz`.

**Process (frozen builder, zero code change):**

1. Per source, dense-reconstruct TRAIN `N_ab` (1024,1024) from the COO triplets (row/col/count) in memory.
2. Factorize via the frozen builder with **zero code change**: `ChannelAdapter(fact_id="F03", source=<V26 source id>, N_ab=<dense TRAIN>)` — pure column-normalization per the V26 table pattern (`P_ab = N_ab/sum`; `P_a_gb` column-normalized; `p_b` col-sums; L1 → (32,1024) P(U1|B); L2 → (32,32,1024) P(U2|B,U1) with the frozen `posterior_rows` delta-at-0 fallback on P(U1|B)=0 cells). No fitting. Cost: seconds of numpy.
3. **2M continues to use the frozen `gamma_f03.npz` read-only — NEVER refit.** A re-derived 2M factorization from the R1 COO may be built for VERIFICATION ONLY (ΔH/Δp_b comparison per the R1 §2.7 report-only rule); it MUST NEVER be substituted into any decoder path.

**Output location (recommendation with rationale):**

- RECOMMENDED: fresh additive machine root **`workspace/x1_bundles_<UUID8>/`** (UUID `[TO BE FROZEN]`, absence proven at Pre-EXECUTE), holding the bundle npz pair (naming below) + `BUNDLE_BUILD_LOG.md` + verification report. RATIONALE: invariants I6 require additive `workspace/<id>_<uuid>` roots for machine artifacts; the `docs/research_cycles/` cycle dir holds frozen contracts only — committing ~100–300 KB binaries there would extend the historical 2M committed-file exception (`gamma_f03.npz` in the cycle dir) into new binaries, defeat Pre-EXECUTE output-absence provability, and violate the minimal-commit posture. REJECTED alternative: cycle-dir additive naming (e.g. `docs/research_cycles/V80-NBLDPC-JAN21/x1_gamma_*.npz`) — recorded here as considered-and-rejected for those reasons.
- Per-arm decode roots remain SEPARATE fresh additive roots `workspace/x1_<uuid8>/` per §2.7 (bundle root is shared read-only input, never a decode-output root).

**Naming convention (frozen; key prefix `[TO BE FROZEN]` at Pre-EXECUTE from the proposal below — no new constant):**

- Bundle npz: `x1_gamma_f03r1.npz` carrying `{source}_gamma1_L1` **(32,1024)** + `{source}_gamma2_L2condU1` **(32,32,1024)** per source; sidecar: `x1_gamma_f03r1_pb.npz` carrying `{source}_p_b` **(1024,)** per source.
- PROPOSED `{source}` key prefix: **`1M` / `1p5M` / `2M`** (matching `SOURCE_METADATA` labels + the existing frozen `2M_*` precedent; `1.5M` remains a DISPLAY-ONLY alias and MUST NEVER appear as a bundle key). The operator freezes the exact prefix triple at Pre-EXECUTE; any deviation is a science-input change (STOP).
- Normalization gate (bind-time, fail-closed): `{source}_p_b` sum = **1±1e-9**, else refuse (no uniform fallback).

**Verification (all must PASS before any arm runs — gate G-D, §4):**

1. `bind_empirical_bundle()` shape/normalization gates on the built files: g1 (32,1024) finite/nonneg/colsums=1 (atol 1e-9); g2 (32,32,1024) finite/nonneg/cond-rowsums over axis=1 =1 (atol 1e-9); p_b (1024,) finite/nonneg/sum=1±1e-9.
2. Reconstruction checksums vs the R1 root: dense sum == `N_train` (315504/441487/589461); nnz == `K_AB` (2395/2439/2597); occupied-B columns == `K_B` (1024 ×3); `p_b` == COO colsum/N (maxabs 0); `H_L1+H_L2 == H_plug` identity.
3. 2M verification-only comparison (report-only FINDING, never smoothed, never refit — R1 §2.7 rule carried forward): per-plane ΔH_L1/ΔH_L2 + p_b L_inf of the re-derived-2M factorization vs the frozen `gamma_f03.npz` sidecars; materiality |ΔH| > 0.01/plane OR p_b L_inf > 1e-3 ⇒ FINDING escalated to the main thread.

### §2.7 Budgets / scope / stop (baseline §0.1 [X1]§7)

- Per (source, m) arm: wall **≤1800 s**; per-decode **≤300 s** terminal; RSS **< 4 GiB**; **1 CPU**. Total ceiling **15 × 1800 s = 27000 s** (single bootstrap-free ceiling — there is no bootstrap in X1; the R1 bootstrap-waiver history is IRRELEVANT here).
- Roots `workspace/x1_<uuid8>` fresh additive per arm (UUID + absence proven at Pre-EXECUTE); `results/` + `comparison_bench/outputs_comparison/` FORBIDDEN. New thin campaign module ONLY (if a thin runner is needed at all — the consumer path needs zero code change); ALL frozen modules read-only; fake-only tests (per-source bundle-binding refusal on cross-source channel, standalone-construct pins, bar/gate arithmetic incl. rule-(c), root refusal). No production decode in tests.
- **STOP** on any science-input change (n/m/tag/H/λ/seeds/thresholds/channel/decoder/hypothesis/data roles) — **any `.ttbin` read (either member, any dataset) is STOP-BLOCKED**. No retry/resume/adaptive search; **≤1 preregistered engineering repair+rerun** for infrastructure failure ONLY, unchanged scientific inputs, failed attempt retained in the same root(s).
- **bar-12 early-stop**: an arm whose fails exceed 12 before block 240 MAY stop early as a gate-(a) FAIL; the arm is reported CENSORED (fails-at-stop/blocks-at-stop + projected NEVER), never extrapolated to 240, never pooled.
- **Wall-partial ⇒ INCOMPLETE**, retained, never continued.

### §2.8 Overlaps / scheduling (run ONCE; consume by reference — baseline §0.1 [X1]§7 + [P2]§3–§4)

- **X1-2M {192,196,204} vs P2 arm-(ii): run ONCE.** Whichever cycle runs them first, the other consumes BY REFERENCE (never re-measures, never substitutes constructions).
- **X1-2M m=200 STANDALONE ≠ P1 nested leading-200** (§2.3) — both labeled, never equated; P1 ownership of its m=200 measurement stands.
- **F202 / F208 (b2f: 6/240, 0/240 @2001, same channel/seeds — CORRECTED REVISE R6: B2F measured F202, not "F200")** are consumable BY CITATION as cross-batch consistency checks on the corresponding X1-2M curve points, NEVER pooled with X1's single-batch curve. X1 re-measures its grid as a single-batch curve.
- m=200 belongs to NO other cycle's construction: P2 MUST NOT re-measure m=200 (baseline §0.1 `[P2]§§4–6` FORBIDDEN list).

### §2.9 Outputs

- Per arm (in its `workspace/x1_<uuid8>/` root): `X1_RESULT_*.md` (FER, iters, wall/RSS, f_super/f_eff own-basis, undetected log) + `rows.json` + `block_accounting.csv`.
- Batch (one EXPLORE batch): ONE append-only `EXPLORATION_LOG.md` (attempts, the ≤1 preregistered engineering correction if used, final evidence, batch-end review) + bundle-build log/verification report + ONE batch-end independent review. No per-arm review.

## §3 Track justification + EXPLORE chain

- **Why EXPLORE, explicitly**: (i) inputs are synthetic channel draws from already-persisted histograms — NO real/raw acquisition data is opened (zero `.ttbin` reads); (ii) the work is bounded (15 arms, frozen grid/seeds/instance/pins) and reversible (fresh additive roots, no protected-root writes); (iii) outputs are diagnostic FER curves that feed a LATER route decision but make NO FER/SKR/qualification/promotion/publication claim themselves. Per `AGENTS.md` §1.2 applicability matrix this is "Synthetic route gate (diagnostic/construction arms)" → EXPLORE (`EXPLORE_HEAVY` cost annotation for the 27000 s ceiling; the route-closing decision itself remains DECIDE and is NOT made here).
- **EXPLORE contract applied**: ONE packet+prompt pair (this packet + `X1_SUCCESSOR_ENTRY_PROMPT.md`); ONE authorization covering the frozen conditional arm sequence (prereg signature, §8); per-arm machine roots + ONE append-only `EXPLORATION_LOG.md`; at most ONE preregistered repair+rerun with unchanged scientific inputs/seeds/thresholds/data roles/hypothesis (failed attempt retained in the same log/roots); multi-seed default is SATISFIED by construction (240 paired blocks, frozen seed stream `o1_blk:{seed}` — no additional seed axis is invented); batch-end independent review (no per-arm authorization/return/repair-review files).
- Escalation: EXPLORE MUST escalate to DECIDE before continuing on real data, route-closing thresholds, publication claims, destructive output, materially higher cost, or any change to scientific inputs/hypothesis. Calling the frozen decoder on synthetic bundle draws does NOT force DECIDE.

## §4 Gates (frozen, binary per gate)

- **G-A (route gate):** fails/240 ≤ 12 per arm (5% continue/stop internal context — NOT certifiability). Bar-12 early-stop arms are gate-(a) FAIL + CENSORED.
- **G-B (efficiency gate):** `f_super ≤ 1.3` on the arm's OWN R1-corrected `H_corr` (§2.1 values). NOTE: 1M grid top m=201 is EXPECTED-OUT on this gate (retained-frozen grid, §2.2); 1.5M@208 is not in the grid (no verdict taken).
- **G-C (N-rule + presentation ban):** `N ≥ ceil(3·4.785675/(1.3−f_super))` evaluated per arm (expected to FAIL on essentially every high-m arm that passes G-A); **FORBIDDEN: presenting any single-source `f_eff` as a certifiable literature-comparable number.** f-margin IN (e.g. 2M high-m) and N-count certifiability are DISTINCT verdicts and MUST be kept distinct (cf. R1 F3 wording finding).
- **G-D (bundle entry — ALL must PASS before ANY arm runs):** §2.6 verification items 1–3 (bind shape/normalization gates; R1 checksum identities; 2M report-only comparison with materiality bars |ΔH|>0.01 / p_b L_inf>1e-3 ⇒ FINDING, never refit). FAIL ⇒ STOP-BLOCKED for the affected source (other sources may proceed), no fallback bundle, no vintage substitution.
- **G-E (integrity/stop):** budgets (§2.7) held; zero `.ttbin` reads; cross-source reuse refused; no pooling; no `undetected`-merging; no `f_super`-as-`f_eff`; no cross-m monotonicity inference; `git diff -- src/` empty; protected roots untouched. FAIL ⇒ STOP-BLOCKED, batch-end review adjudicates.
- Batch closes ONLY with the batch-end independent review + main-thread acceptance. Any gate FAIL blocks promotion of that arm's evidence; never publish-then-patch.

## §5 Scope / non-goals (explicitly forbidden)

- No real data (any `.ttbin` read STOP-BLOCKED); no decoder/DE/graph-kernel change; no prior refit (2M `gamma_f03.npz` read-only, NEVER refit); no P1/P2 execution; no operating-point selection; no FER/SKR/route/qualification/publication claim.
- No change to any frozen scientific input (n, m grid, tag, H_corr basis, gates, thresholds, seeds 2026095601+idx / instance 2026092001, split roles, trio parameters, estimator definition, slope 4.785675).
- No pooling across sources/m/instances; no `undetected`-merging; no quoting TRAIN numbers as held-out or vice versa without the split side (TRAIN-side provenance carried on every row).
- FORBIDDEN (always): opening either `.ttbin` member or concatenating; cross-source channel reuse; vintaged `channel_counts.npz` substitution (V25 August vintage N differs +2.7/+3.9% — a science-input change for the main thread only, NEVER an executor substitution); modifying `src/`; writing to `results/` or `comparison_bench/outputs_comparison/`; any `tools/longrun_*`/`minrerun_*`/`routeA_*`; `experiments/run_e2e_pipeline.py`; inventing alignment parameters, seeds, paths, block counts, or bundle-key prefixes; committing or pushing.
- Implementation-only change note (`AGENTS.md` §1.2 matrix): building the thin runner/bundle factorization with NO execution carries no track gate by itself; the track gate attaches at the first synthetic execution (EXPLORE batch authorization here).

## §6 Claim ceiling

- Synthetic per-source FER curves ONLY (fails/240 + f_super/f_eff on own corrected H + iters/wall + undetected log). Curves do NOT select an operating point; the operating-point decision is a LATER DECIDE step consuming these curves + P1 rescue results.
- Generality headlines LEAD with 1M (anti-cherry-picking, baseline §7-6). **2M-only headline FORBIDDEN.**
- `H_corr` is CONDITIONAL on the R1 re-derived §3A alignment and the TRAIN split side (carried on every row). The m≤201 relocation is CONDITIONAL on the per-block disclosure model only (baseline §2(a)); under the ratified sacrifice/amortized default it does NOT follow.

## §7 Executor tasks (for coder agents — implementation only, no requirement changes)

1. **T-X1S-1 (bundle build, additive, seconds):** From the R1-root COO triplets, dense-reconstruct per-source TRAIN `N_ab` and factorize via the UNMODIFIED `ChannelAdapter(fact_id="F03", …)` into the §2.6 bundle npz pair under `workspace/x1_bundles_<UUID8>/` (UUID `[TO BE FROZEN]`). 2M re-derivation VERIFICATION-ONLY (never substituted). If ANY frozen arithmetic must change to add persistence, STOP and return to planner instead of guessing.
2. **T-X1S-2 (verification reporter, read-only):** Implement the §2.6/G-D checks as a read-only reporter (bind gates + R1 checksum identities + 2M report-only comparison with frozen materiality bars). No refit path, no overwrite path in code.
3. **T-X1S-3 (tests, fake-only):** Unit tests on synthetic histograms: bundle round-trip (reconstructed dense == original; sum + nnz checksums), `bind_empirical_bundle()` shape/normalization refusal gates (incl. cross-source-label refusal), standalone-construct pin checks (fc=0/rank-full/twice-identical), bar/gate arithmetic incl. rule-(c), root-refusal. Zero production decoder calls in tests; no `.ttbin` in tests; test-only fake runner explicitly passed.
4. **T-X1S-4 (thin arm runner IF needed — additive only):** If no existing CLI runs the §2 grid verbatim, add ONE thin campaign module that binds the §2.6 bundles read-only and runs the frozen b2f/v28 procedure per arm with the frozen seeds/instance/pins. NO kernel change; NO new seed/threshold/constant. If the runner cannot be built without changing frozen modules, STOP and return to planner.
5. **T-X1S-5 (prompt/prereg fill-in at execution time):** Operator fills UUIDs, exact bundle paths, key-prefix freeze, budget confirmation, and grant at Pre-EXECUTE per `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md`; NOT done in this planning task.
- Small-task note: T-X1S-1–T-X1S-3 are bounded additive tasks (seconds-scale numpy + fake-only tests) suitable for direct delegation once this packet + prereg are granted; no `/opsx-explore` needed (builder/consumer paths and R1 inputs are fully characterized in the cited sources).

## §8 Entry evidence + authorization gate (EXPLICIT USER GATE — STOPS HERE)

- Entry: (a) T-X1S-1–T-X1S-3 built + fake-only tests pass; (b) §2.6 bundle build + G-D verification DONE and recorded; (c) Q0–Q6 Pre-EXECUTE recorded (intended branch state = this packet; scoped cleanliness incl. worktree-dirt enumeration; frozen contract §§1–7; output-absence + `rg` proofs; dry per-source bundle binding + dry-construct pins per m); (d) FRESH EXPLICIT USER GRANT in `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` (blank until signed — the frozen packet and prereg authorize NOTHING by themselves).
- `[BLOCKING: needs user input]` — bundle-root UUID + per-arm root UUID pattern, exact bundle paths + key-prefix freeze, budget-ceiling confirmation (single bootstrap-free ceiling ≤27000 s), arm order confirmation, signature (or verbatim conversation grant recorded per §7 of the prereg — THIS-cycle mode only, not pre-authorized here).
- This freeze is NOT a grant. Pre-EXECUTE + grant precede ANY execution (prompt §19 restates the stop).

## §9 Known baseline-vs-archive deltas (REPORTED, not resolved — baseline governs)

Provenance pointers via the §0.1 index only (archived files NEVER cited as authority):

1. **H basis / design points:** archived X1 §1 uses defective-MM H (0.80361/0.82896/0.83458; m_max 201/207/209→208; N_req ≈15438/≈2708/1754; 1.5M INDETERMINATE@208, IN@200/199; pool counts 500/691/911) — SUPERSEDED by the R1-corrected §2.1 values (baseline §3 + R1 acceptance). Gate (b) MUST use `H_corr`.
2. **1M grid top vs corrected m_max:** retained-frozen 1M top 201 now sits ABOVE corrected m_max 200 — grid UNCHANGED per baseline §0.1 `[X1]§3`; the arm is EXPECTED-OUT on G-B (characterization value only: confirms the cliff floor location above max).
3. **2M overlap partition:** archived X1 §§3/7 full 2M {192,196,200,204,208} + re-measure-F202/F208 + P1-nested distinction + P2-once scheduling is now SPLIT across baseline §0.1 `[P2]§3` (192,196,204 NEW / 200 OWNED-BY-P1 / 202,208 BY CITATION) and `[X1]§7` (single-batch re-measure, citations as consistency checks never pooled) — this packet keeps BOTH (full 15-arm freeze + once-scheduling + STANDALONE-vs-nested distinction + F202-not-F200 correction).
4. **Bundle premise:** archived X1 §1-l5 "materialized by the A1 census" — SUPERSEDED-as-premise (baseline §0.1 `[X1]§1-l5`; assessment T2 proof). Bundle-input authority is the R1 root (§2.6), NOT the A1 root.
5. **Certifiability counts:** archived X1 §6(c) pool 500/691/911 + approximate N_req — SUPERSEDED by key-eligible 200/276/364 ([DEC]§C; baseline §2/§5-iii) and [REC]/R1-corrected N_req (15487/2700/1754 at m_max; 1.5M m=199 FLIP to NO).
6. **Stale text:** `~9σ`, pre-correction N_req, banner closing sentence, stale pre-archive paths in the archived proposal/design/packets + memory lines — history only per baseline §3 stale list; deliberately NOT rewritten, NEVER cited as current.
