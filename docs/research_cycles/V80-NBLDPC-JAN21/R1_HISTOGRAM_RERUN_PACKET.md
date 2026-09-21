# R1 Histogram Re-run Packet (2026-09-21) — FROZEN, NOT GRANTED

> **Amendment 2026-09-21 (main-thread decision: 那就不豁免 — bootstrap NOT waived).**
> Bootstrap (≥200 resamples, frozen seed 20260921) is REQUIRED; the row-B / waived / NO-CI
> budget alternative is withdrawn (§2.8, §8). Design points without uncertainty are not
> admissible for design-point decisions (§6). Prereg/prompt files untouched by this amendment.

- Track: **DECIDE** (real/raw acquisition data; outputs feed design-point and route decisions). See §3 for the explicit justification.
- Acceptance ID: **G-R1** (packet frozen, NOT granted). Authorizes NOTHING. Nothing may run without the full DECIDE chain (§3 + `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` signature + Pre-EXECUTE).
- Parent contract (structure only, NOT current authority): `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md` (carries a supersede banner).
- Planning authority: `docs/V80_BASELINE_20260921.md` (§1 invariants, §3 results, §5 open decisions, §6 forward plan).
- Technical sources (every number below traces to one of these; unknowns marked `[TO BE MEASURED]` / `[TO BE FROZEN]`):
  - Estimator defect, quantified: `docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` (esp. §§T1–T3).
  - Current design-point table to be re-derived: `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` (§§1–4) and Baseline §3.
  - Entry-blocker analysis + builder path: `docs/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md` (esp. §§T2–T4).
  - Frozen trio parameters: `docs/PREALIGN_CENSUS_PREFLIGHT_20260921.md` (§Q3).
  - Mandatory alignment: `docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md` (§D) and P3 packet §3A.
  - Member semantics: `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` (§§C–E).
  - Existing executor to extend: `comparison_bench/src/comparison_bench/cli/p3_census_a1.py` (defect at lines 344–349; transient `p_b` at line 103).
  - Bundle builder (pure numpy, no `.ttbin`): `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py` (`load_channel_counts()` L82–110, `ChannelAdapter` L123+).
  - Bundle consumer (zero code change needed): `comparison_bench/src/comparison_bench/formal_ir/v80_s2c_campaign.py:187` `bind_empirical_bundle()` (`{source}_`-prefixed keys, shape/normalization gates).
- Branch context: `formal-ir-v72p1-addendum-clean`; publication branch `formal-ir-v80-nbldpc-jan21`. No switch, no commit, no push, no PR in this packet.
- Planning only. NO execution, NO `.ttbin` access, NO workspace root, NO commit/push authorized or performed by this packet.

## §1 Purpose — one re-read closes two open items

From Baseline §5 + the pre-launch review:

1. **Estimator defect (UNVERIFIED design points).** `p3_census_a1.py:349` adds the JOINT-entropy Miller–Madow correction `(K_AB−1)/(2N·ln2)` to the CONDITIONAL plug-in `H(A|B) = H_L1+H_L2`. Correct first-order form is `(K_AB−K_B)/(2N·ln2)`. `K_B` was never persisted (transient `p_b` at line 103) and is unrecoverable from the three 74-key JSONs. Max plausible over-correction 0.0023/0.0017/0.0013 b = 0.65–0.82× CI halfwidth; **no out-of-box verdict flips**, but corrected values are unknown (estimator-verification §§T1–T2).
2. **X1 entry blocker.** The 1M/1.5M channel bundles were never materialized — A1 built `N_ab` in memory and persisted only summaries (X1 assessment §T2: exhaustive key inventory + directory-wide grep, zero histogram keys). X1's 15 cliff arms are entry-blocked (Baseline §6-2).

These are the same re-read: one histogram-only pass over all three sources, persisting everything needed for both — minimum one `K_B_train` per source (required), ideal sparse `N_ab_train` (required here — this is what unblocks X1).

## §2 Frozen design

### §2.1 Datasets
- All three Jan-21 trio sources: **T2-1M, T2-1.5M, T2-2M**, **base member (`X.ttbin`) only, vendor auto-follow** covers `.1`. Never both members; never concatenate (Baseline I1; member-semantics §§C–E).
- Base paths: `[TO BE CONFIRMED at Pre-EXECUTE]` against `docs/DATA_INVENTORY_20260921.md` (same trio members A1 read). No path invented here.

### §2.2 Frozen trio parameters (preflight §Q3 — imposed, unchanged)
- d=1024, bin_width=200 ps, frame_period=204800 ps, pairing `nearest` (loader policy `nearest_unique`), rule `legacy_v1`, threshold=40000 ps (template provenance only, unused by frozen loader), gate/coin_window=200 ps, corr 16384 bins (100 ps / ±819200 ps), channels **A=1/B=5**, framing `global`, postselect `keep_all`.
- Prior recorded offsets (COMPARISON ONLY, never input): −50/+50/+50 ps (bins 8191/8192/8192).

### §2.3 Mandatory §3A correlation alignment first (per source, pre-pairing)
- Frozen procedure: `compute_cross_correlation_histogram(events, ch_a=1, ch_b=5, bin_width_ps=100, max_lag_ps=819200)` → `pk = argmax` → `offset_ps = +lag_center_ps[pk]` (lag convention `t_B − t_A`; offset added to side A). No interpolation; bin centre only.
- Frozen gates (all must pass, else **STOP-BLOCKED for that source**, continue others, no fallback to 0/borrowed/recorded, no post-hoc bin widening): p2bg ≥ 100; single dominant mode (no secondary local maximum > 50% of primary outside ±1000 ps of pk); crude sigma 10–500 ps; non-empty channels/histogram.
- Record per source: `offset_ps_derived`, `peak_bin_index`, `peak_center_ps`, `peak_to_bg`, `sigma_crude_ps`, `align_status` + one-bin comparison against recorded −50/+50 (|derived − recorded| ≤ 100 ps AND bin-index difference ≤ 1; disagreement beyond one bin is a FINDING, reported, never adjusted).
- Expected re-derivation targets `[TO BE RE-MEASURED]` (Baseline §3; A1 measured): 1M bin 8191 → −50 (p2bg 1186.3, σ 66.41); 1.5M bin 8192 → +50 (748.2, 70.71); 2M bin 8192 → +50 (546.1, 70.92).

### §2.4 Split (identical realization to A1 — required for comparability)
- 60/20/20 consecutive-time by ascending frame index (V49 convention); split manifest written as the FIRST artifact, before any statistic.
- Histograms are built on the **TRAIN pool only**. VAL/HOLD are not read for statistics (A1's hold gap stands; R1 does not touch HOLD).

### §2.5 Frozen estimator specification (ONE definition — run and re-analysis must agree)
- **Estimand (explicit): the CONDITIONAL entropy `H(A|B)`**, realized as `H_L1 + H_L2` under factorization F03 (`u1 = a>>5`, `u2 = a&31`), plug-in `P(a|b) = N_ab[a,b]/N_ab[:,b]` on the TRAIN pool, bits per GF(32) symbol. NOT joint entropy.
- Corrected Miller–Madow (frozen): **`H_corr = H_plug + (K_AB − K_B) / (2 · N_train · ln2)`**, where `K_AB` = occupied joint cells of TRAIN `N_ab`, `K_B` = occupied marginal-B columns of TRAIN `N_ab` (`#{b : N_ab[:,b].sum() > 0}`), `N_train` = TRAIN pair count (NOT full-pool `n_pairs_N`).
- Defective value (persisted alongside for auditability): `H_MM_old = H_plug + (K_AB − 1)/(2·N_train·ln2)`; delta `Δ = H_MM_old − H_corr = (K_B − 1)/(2·N_train·ln2) ≥ 0`.
- Current (defective-basis) values being replaced — full precision from the recompute doc (recompute §1; Baseline §3): H_MM 0.8036079281174853 / 0.8289616869054485 / 0.8345846048587662; H_plug 0.7981344445358378 / 0.8249782281516377 / 0.8314077735449492; K_AB 2395/2439/2597; N_full 525831/735780/982182; recovered N_train ≈ 315504.0/441487.0/589461.0 (inverted from persisted scalars — inference, NOT reused by R1); applied MM +0.0054734836/+0.0039834588/+0.0031768313; CI hw 0.00284610/0.00220976/0.00193486 (200 resamples, seed 20260921).
- Design-point arithmetic (frozen rules, full-precision H ONLY — never rounded substitution; cf. razor-thin 1.5M@207 N_req = 2699.955…): content = 1024·H_corr; `f(m) = (5m+64)/content`; `m_max = ⌊(1.3·1024·H − 64)/5⌋` (frozen cap m ≤ 208 applies); `N_req = ⌈3·4.785675/(1.3−f)⌉` (`inf` if f ≥ 1.3); thresholds H ≥ 0.829327 (@208) / 0.799279 (@200) / 0.795523 (@199); slope 4.785675 frozen.

### §2.6 Persisted artifacts per source (the point of the run)
Required (per-source either ALL persist or NONE — gate (c)):
1. `K_B_train` (integer, occupied marginal-B count on TRAIN) — **required** (fixes the correction exactly).
2. `p_b_train` (1024,) float64, sum = 1 — **required** (occupancy cross-checks; X1 sidecar input).
3. Sparse `N_ab_train` — **required** (unblocks X1): `<SRC>_N_ab_train_sparse.npz` with keys `row`, `col`, `count` (int64 COO triplets), `shape=(1024,1024)`, `N_train`; dense-reconstruction checksum (sum + nnz) recorded in JSON for verification.
4. Scalars (full precision): `N_train`, `K_AB`, `H_L1`, `H_L2`, `H_plug`, `H_corr`, `H_MM_old`, `Δ`, bootstrap CI on the CORRECTED statistic (lo/hi/hw, ≥200 resamples, frozen seed 20260921 — see §2.8).
5. Provenance per number: split side (TRAIN vs full pool) stated on every row; alignment fields (§2.3); `duration_measured_s` / `filename_duration_tag` / `tag_disputed` (measured span, never the tag); `dataset_wall_s`, reader/RSS telemetry.

R1 does NOT build gamma npz files (no `ChannelAdapter` factorization here — that is seconds of numpy downstream at X1 entry, against the persisted sparse histograms, with zero code change via `bind_empirical_bundle()`).

### §2.7 2M consistency check (report-only FINDING, never smoothed over)
- The re-derived 2M bundle inputs MUST be compared against the existing frozen `gamma_f03.npz` lineage (built from `channel_counts.npz`, TRAIN N=559872; X1 assessment §T1).
- Comparison rule (all reported, none gated except as stated): report ΔN_train (R1 `[TO BE MEASURED]` vs 559872 — a delta here is EXPECTED: different pairing realization/scope, V25 parquet rows 512000/708352/933120 vs A1 N=525831/735780/982182; N alone is never a discrepancy finding), per-plane ΔH_L1/ΔH_L2 vs the frozen bundle sidecars, and p_b max-abs-diff.
- Materiality bar: |ΔH| > 0.01 b/sym per plane OR p_b L_inf > 1e-3 ⇒ FINDING, escalated to the main thread. 2M is the V80 frozen-channel source: any material discrepancy is a finding, not a failure to be smoothed over. NEVER refit/replace `gamma_f03.npz` in this packet; NEVER substitute the re-derived bundle into any decoder path.

### §2.8 Bootstrap (frozen — REQUIRED, no waiver)
- Bootstrap on the corrected statistic is REQUIRED: ≥200 resamples, frame-level, frozen seed 20260921 (A1 precedent; P3 §6 requires CI for every below-anchor design-point candidate). NO waiver path exists.
- REMOVED — bootstrap is required; the NO-CI alternative is withdrawn by main-thread decision 2026-09-21. The former row-B / bootstrap-waiver / `NO-CI` path (operator-may-skip with main-thread approval at Pre-EXECUTE) is deleted in its entirety and SHALL NOT be authorized at Pre-EXECUTE or recorded in the signature block.
- Budget table (single bootstrap-inclusive ceiling):

| item | ceiling |
|---|---|
| Per `.ttbin` read | ≤ 300 s |
| Per-dataset all-in (read + §3A + pairing/framing/bincount + persistence + bootstrap) | ≤ 1800 s |
| Trio total | ≤ 5400 s |
| Peak RSS | < 4 GiB |
| Decoder / DE / graph calls | **0** |

- Precedent: A1 measured 688/1053/1246 s per dataset WITH the bootstrap dominating; histogram-only pass over both 1M/1.5M estimated ~5–15 min without it (X1 assessment §T4). No retry/resume/adaptive search; wall-partial ⇒ INCOMPLETE, retained, never continued; ≤1 preregistered engineering repair+rerun for infrastructure failure ONLY, scientific inputs unchanged, failed attempt retained in the same root.

### §2.9 Outputs
- Fresh additive root `workspace/r1_histogram_<uuid8>` (absence proven at Pre-EXECUTE; UUID `[TO BE FROZEN]`).
- Per source: `<SRC>.json` (all §2.6 scalars + alignment/span/split/provenance) + `<SRC>_N_ab_train_sparse.npz` + `<SRC>_p_b_train.npy`.
- Shared: `split_manifest.json` (first artifact), `corrected_design_points.json/.csv` (per source, full precision: H_corr, content, m_max raw+capped, f@208/@200/@199, N_req), `delta_vs_baseline_S3.md` (per-source ΔH/Δcontent/Δf/Δm_max/ΔN_req + verdict movement vs Baseline §3), `alignment_table.md`, `R1_RESULT.md`.
- Then: independent Pre-RESULT review → acceptance → main-thread close-out of the two items.

## §3 Track justification + DECIDE chain
- **Why DECIDE, explicitly**: (i) it reads **real/raw acquisition data** (`.ttbin` streams) — DECIDE-eligible per `AGENTS.md` §1.2 ("Real/private/raw data … always DECIDE"); (ii) its outputs correct published design points and materialize inputs to a route-driving campaign (X1) — claim-bearing per the applicability matrix ("Real-data development/validation → DECIDE, full DECIDE gate contract"). Calling a zero-decode reader does not by itself force DECIDE; the real-data + claim-bearing combination does.
- Consequently NOTHING may run without, in order: (1) accepted preregistration (`R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` signed by the user — signature block BLANK until the user fills it); (2) **Pre-EXECUTE** — exact command, budget, output-absence proof, explicit authorization, scoped cleanliness, focused tests; (3) ONE execution + ONE result record; (4) **independent Pre-RESULT** review; (5) **main-thread acceptance**. FAIL at any gate blocks the next step.

## §4 Gates (frozen, binary per gate)
- **(a) Alignment §3A per source.** FAIL ⇒ STOP-BLOCKED for that source, continue others, no fallback, no pairing/histogram/entropy for it.
- **(b) Span-continuity assertion.** Span > 0 AND |span − mtime-gap| ≤ tol (tol 0.5 s proposed, `[TO BE CONFIRMED]` at authorization) else STOP-BLOCKED for that source (span ≈ 2× gap ⇒ doubling; span ≪ gap ⇒ silent truncation).
- **(c) Both-or-neither (artifact atomicity).** Per source, the estimator-correction set (K_B + corrected H) and the bundle set (sparse N_ab + p_b) persist together or not at all. A source yielding one but not the other is INCOMPLETE; no partial close-out of either open item is claimed on it.
- **(d) `K_B` sanity.** 1 ≤ K_B ≤ 1024 AND K_B < K_AB, else STOP-BLOCKED for that source (equality is practically impossible at N_train ~3–6×10⁵ over ~2400 cells and signals corruption).
- **(e) 2M consistency (§2.7).** Report-only: material discrepancy ⇒ FINDING escalated to main thread; never refit, never substitute, never smooth over.
- **(f) Determinism vs A1.** Same deterministic code + same base member ⇒ identical streams: frame counts, split boundaries, and derived alignment must reproduce A1 exactly (one-bin AGREE is the minimum reporting bar; exact equality expected). Mismatch ⇒ STOP-BLOCKED for that source (input/environment drift ⇒ infrastructure, eligible for the ≤1 engineering-repair path, never silently continued).

## §5 Scope / non-goals
- Does NOT run X1's cliff curves (those need their own packet with the materialized bundles as input).
- Does NOT change any frozen scientific input (n, m, tag, H_full anchor, gates, thresholds, seeds, split rule, trio parameters).
- Does NOT retract or re-run the A1 synthetic FER arms (b2f/b2g etc.) — unaffected.
- FORBIDDEN (always): opening both pair members or concatenating; pooling across sources; any decoder/DE/graph call; any `tools/longrun_*`/`minrerun_*`/`routeA_*`; modifying `src/` (`git diff -- src/` must stay empty); writing to `results/` or `comparison_bench/outputs_comparison/`; reading excluded derived artifacts; merging `undetected` into success (N/A here — invariant kept); inventing alignment parameters, seeds, paths, or block counts; committing or pushing.

## §6 Claim ceiling
- Corrected per-source design points + materialized channel-bundle inputs ONLY. No FER/SKR/route/qualification/publication claim.
- The corrected design points do NOT by themselves authorize X1 — X1 needs its own entry gate (bundles as input + fresh Pre-EXECUTE + explicit grant; X1 remains ENTRY-BLOCKED until this packet's artifacts land AND its own gate passes).
- `H_corr` is CONDITIONAL on the re-derived §3A alignment (reported as a derived measurement with acceptance status) and on the TRAIN split side.
- Design points without bootstrap uncertainty are NOT admissible for design-point decisions: every reported design-point row carries its CI (lo/hi/hw); a `NO-CI` row does not exist in this packet.

## §7 Executor tasks (for coder agents — implementation only, no requirement changes)
1. **T-R1-1 (executor):** Create additive module `comparison_bench/src/comparison_bench/cli/r1_histogram_rerun.py` (new file; do NOT rewrite `p3_census_a1.py`): reuse its frozen read → §3A alignment → pairing/framing → TRAIN-split → `h_full_f03` path byte-identically (same imports of frozen `ttbin_pipeline` arithmetic and `align_wrapper`). ADD ONLY: (i) `K_B_train` computation on TRAIN `N_ab`; (ii) `p_b_train` capture; (iii) sparse COO persistence of TRAIN `N_ab`; (iv) corrected MM + old defective MM + delta; (v) bootstrap CI on the CORRECTED statistic (seed 20260921, ≥200 resamples); (vi) per-source JSON + shared design-point/delta tables per §2.9. If any frozen arithmetic must change to add persistence, STOP and return to planner instead of guessing.
2. **T-R1-2 (2M check):** Implement the §2.7 comparison as a read-only reporter (frozen bundle opened read-only; no refit, no overwrite path in code).
3. **T-R1-3 (tests, fake-only):** Unit tests on synthetic histograms: K_B edge cases (single occupied column; full support), corrected-vs-old identity (`Δ = (K_B−1)/(2N ln2)`), sparse round-trip (reconstructed dense == original; sum + nnz checksums), `bind_empirical_bundle()` shape/normalization gates against a synthetic factorization. Zero production decoder/DE/graph calls in tests; no `.ttbin` in tests; test-only fake runner explicitly passed.
4. **T-R1-4 (prompt/prereg fill-in at execution time):** Operator fills base paths, UUID, budget row, and tolerance confirmations at Pre-EXECUTE per `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md`; NOT done in this planning task.
- Small-task note: T-R1-1–T-R1-3 are bounded additive implementation tasks suitable for direct delegation once this packet + prereg are signed; no `/opsx-explore` needed (estimator defect and builder path are fully characterized in the cited sources).

## §8 Entry evidence + authorization gate (EXPLICIT USER GATE — STOPS HERE)
- Entry: (a) T-R1-1–T-R1-3 built + fake-only tests pass; (b) Q0–Q6 Pre-EXECUTE recorded (intended branch state = this packet; scoped cleanliness; frozen contract §§1–7; output-absence + `rg` proofs; dry control read); (c) FRESH EXPLICIT USER GRANT in `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` (blank until signed).
- `[BLOCKING: needs user input]` — base paths confirmation, UUID, budget-row confirmation (single bootstrap-inclusive ceiling ≤5400 s; the waived row is withdrawn), span-tolerance + anchor-tolerance confirmations, signature.
- This freeze is NOT a grant.
