# X1 Entry-Blocker Assessment — 2026-09-21 (read-only capability assessment)

> Read-only. No `.ttbin` opened, no data parsed/loaded, no pipeline run, no commit/push.
> Nothing under `workspace/` or any protected root was modified. `.npz` contents below
> are cited from repo-side manifests/packets/code, never by loading the files.
> Planning authority: `docs/V80_BASELINE_20260921.md` (esp. §6 step 2). X1 packet cited
> for technical requirements only (it carries a SUPERSEDED banner).

## T1 — What the X1 packet requires as "bundles"

Per `X1_CROSS_SOURCE_PACKET.md` §4 (+`S2C_EXPERIMENT_PACKET_20260920.md` §2, `S1_READINESS.md` §S1r-gamma):

- A per-source bundle is a **read-only derived artifact** consisting of:
  - gamma npz keys `{src}_gamma1_L1` **(32,1024)** — g1[u1,b] = P(U1|B);
  - `{src}_gamma2_L2condU1` **(32,32,1024)** — g2[u1,u2,b] = P(U2|B,U1), Q5 branch-a axes
    (joint÷marginal; P(U1|B)=0 cells take the frozen `posterior_rows` delta-at-0 fallback);
  - scalar sidecars H_L1 / H_L2;
  - sibling sidecar key `{src}_p_b` **(1024,)** with normalization gate sum=1±1e-9 (else refuse).
- 2M = frozen `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` (100106 B, 2026-09-19)
  + `gamma_f03_pb.npz` (9011 B). Provenance: `run_04/channel_counts.npz` 2M train key
  (`type2_2M_20260121_183657_N_ab_train*`, (1024,1024) float64), TRAIN N=559872
  (`KANITSCHAR_RELEVANCE_ADJUDICATION_20260921.md:5`, `L1_REWORK_MEMO_V3:36`).
- 1M/1.5M bundles = **[BLOCKING — TO BE MATERIALIZED]** as read-only derived artifacts
  **from the A1-census histograms** (`workspace/p3_census_3954637c/`).
- Two hard rules: **cross-source channel reuse is FORBIDDEN** (each source's γ differs);
  **any `.ttbin` read inside the X1 batch is STOP-BLOCKED** (X1 §7) — X1 assumes the
  histograms already exist because (X1 §1 line 5) they were "materialized by the A1 census".
  **That premise is false** (see T2). Baseline §6-2 restates the block:
  "Entry-blocked until 1M/1.5M bundles materialized."
- Budget context: 15 arms, 240 blocks each, wall ≤1800 s/arm ⇒ **27000 s ceiling** (EXPLORE_HEAVY).
  X1-2M {192,196,204} scheduled ONCE vs P2 arm-(ii) (consume by reference).

## T2 — What already exists (the crux)

`workspace/p3_census_3954637c/` contains 12 entries (RESULT_SUMMARY's "11 files" + later
`DESIGN_POINT_ARITHMETIC.md` F-1 closure). Sizes (`ls -la`, read-only):

| file | size (B) | content |
|---|---|---|
| `T2-1M.json` | 1171249 | summary only (see below) |
| `T2-1.5M.json` | 1628202 | summary only |
| `T2-2M.json` | 2158164 | summary only |
| `census_table.json` / `.csv` | 5481 / 2731 | per-source scalar rows |
| `split_manifest.json` | 1108 | 60/20/20 frame ranges only |
| `H_full_table.md` / `alignment_table.md` / `memory_stationarity.md` | 1151 / 571 / 1468 | tables |
| `PRE_EXECUTE.md` / `RESULT_SUMMARY.md` / `DESIGN_POINT_ARITHMETIC.md` | ~5 KB each | process/result/design points |

**The raw joint histograms were NOT persisted.** Evidence:

1. Complete top-level key inventory of `T2-1M.json` (74 `^  "key":` grep hits, all enumerated):
   config/provenance scalars, alignment block, `qber`, `n_pairs_N`, `support_cells`,
   `H_L1/H_L2/H_full_plug/H_full_MM/MM_correction`, holdout scalars, bootstrap CI scalars,
   `per_frame_weight_hist` (3 bins), `block_Hfull_series` (129763 floats — accounts for ~1 MB),
   anchor scalars, `dataset_wall_s`. **No histogram key of any name.**
2. Directory-wide grep for `counts_ab|joint|gamma|sparse|nonzero|hist2d|channel_counts`
   over the census root: **zero matches**. A second grep for `N_ab|"_counts|counts_|"counts|1024,1024|shape`
   in `T2-1M.json`: **zero matches**.
3. File sizes scale with `n_superframes` (129763/180536/239420 → 1.17/1.63/2.16 MB),
   consistent with `block_Hfull_series` dominating. A sparse joint histogram (~2400 nonzero
   cells) would add only ~50–100 KB *plus named keys* — absent.
4. The A1 CLI (`comparison_bench/src/comparison_bench/cli/p3_census_a1.py:344`) builds
   `N_ab = np.bincount(...)` **in memory** from paired symbols and writes only JSON summaries
   (`json.dump` at lines 309/502/547 — splits, tables, per-dataset records). Nothing persists N_ab.

**Finding: only summary statistics (N, support, H_L1/H_L2, MM, CI) were kept. Rebuilding N_ab
for 1M/1.5M requires re-running pairing over `.ttbin` events — a new real-data read
(DECIDE track). That is the crux of the blocker, and X1 §1-line-5's premise does not hold.**

Related nuance (does NOT unblock X1 as frozen, but recorded for the main thread):
`S1_READINESS.md` §S1r-gamma says `gamma_f03.npz` was built per-source with
"`1M/1p5M/2M` kept independent" — but the frozen file as consumed everywhere today carries
**only 2M keys** (all campaign manifests cite `2M_gamma1_L1/2M_gamma2_L2condU1/2M_p_b`;
100 KB ≈ one source). The 1M/1.5M factorized arrays are not in the frozen file.
Separately, the *unfactorized* V25 train histograms for all three sources still exist as
`run_04/channel_counts.npz` `*_N_ab_train*` keys (per `S1_READINESS:89-90`,
`nonbinary_v26_channel.py:78-110`, `channel_summary.json` per-source entries,
`data_inventory.json` nonzero 2545/2610/2821) — but that is an **August vintage/scope**
(parquet rows 512000/708352/933120 vs A1's N=525831/735780/982182, different pairing
realization), NOT the A1 histograms X1 names. Using it would be a science-input change
for the main thread to adjudicate, not an executor substitution.

## T3 — Code path that builds a bundle

- **Builder (pure numpy, no `.ttbin`):**
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py`
  - `load_channel_counts()` (L82–110): reads per-source train `N_ab` (1024,1024) from an
    *already-computed* counts npz. Never touches `.ttbin`.
  - `ChannelAdapter(fact_id, source, N_ab)` (L123+): pure column-normalization per the V26
    table pattern — `P_ab = N_ab/sum`, `P_a_gb` column-normalized, `p_b` col-sums,
    L1 → (32,1024) P(U1|B), L2 → (32,32,1024) P(U2|B,U1). No fitting.
  - S1_READINESS confirms this exact class built `gamma_f03.npz` from counts only.
  - **Cost once N_ab exists: seconds.**
- **Consumer (already per-source-ready):**
  `formal_ir/v80_s2c_campaign.py:187 bind_empirical_bundle()` loads
  `f"{source}_gamma1_L1" / f"{source}_gamma2_L2condU1"` + sidecar `f"{source}_p_b"`,
  with shape gates (32,1024)/(32,32,1024) and the p_b normalization gate. A 1M/1.5M bundle
  in the same naming convention plugs in with **zero code change**.
- **What A1 actually ran** (`cli/p3_census_a1.py`): `.ttbin` read → §3A alignment histogram
  (`align_wrapper`, `compute_cross_correlation_histogram` 16384 bins) → pairing
  (`nearest_unique`, coin 200 ps) → framing → in-memory `N_ab` bincount → `h_full_f03(N_ab)`
  → 200-resample bootstrap + block series + ACF + hold-NLL → JSON summaries.
- **Verdict on cheap-vs-expensive:** the factorization step is cheap; the missing input
  (N_ab) is expensive because its only frozen-consistent source is a fresh `.ttbin` pass.

## T4 — Honest cost to unblock X1

- **Frozen-consistent path (A1-derived N_ab):** new DECIDE-track real-data read of the 1M
  and 1.5M base members. A1 precedent (`RESULT_SUMMARY.md`): 687.6 s (1M) / 1053.1 s (1.5M)
  full-census walls; `.ttbin` reads 0.33–0.47 s; 1M §3A align compute 73.4 s.
  A histogram-only rerun skips the 200-resample bootstrap (the dominant cost — 200× bincount
  over ~300–430k TRAIN pairs), the block-H series, drift/ACF, and hold-NLL. Remaining work per
  source: read (~0.5 s) + §3A alignment histogram (~1–2 min, scales with event counts:
  1M had 2.31M/3.23M A/B events) + pairing/framing/bincount (same event scale, minutes) +
  ChannelAdapter factorization (seconds). **Reasoned estimate: a few minutes per dataset,
  ~5–15 min for both sources** (vs ~29 min for the two full A1 arms). The mandatory §3A
  alignment re-run is required but its *read* is <0.5 s; the align *compute* was ~73 s for 1M.
- **After unblock:** bundle materialization is seconds of numpy; then X1 proper up to
  27000 s (15×1800 s ceiling), EXPLORE_HEAVY, with fresh Pre-EXECUTE + explicit per-arm grant
  (X1 frozen, NOT granted).
- **Non-frozen shortcut (for main-thread decision only):** factorize the existing V25
  `channel_counts.npz` 1M/1.5M train keys — zero `.ttbin`, minutes total — but it answers a
  *different* channel vintage than X1's A1-basis contract (N differs by +2.7/+3.9%,
  different pairing realization/scope). Executor must NOT substitute this silently.

## T5 — Is a 2M-only sweep sufficient?

- **What 2M-only answers:** the "doubly motivated" operating-point question — where the cliff
  sits in 188–208 on the frozen 2M channel, hence whether m≤201 (forced by a disclosed 36 b
  prior vs 4.3 b A208 headroom, baseline §2) still decodes. 2M bundle exists; only
  {192,196,204} need fresh arms (F200/F208 consumable by b2f reference: 6/240 and 0/240;
  X1 re-measures as single-batch curve, never pooled). Cost ≤3×1800 s, **no entry blocker**.
- **What 2M-only does NOT answer:** X1's primary purpose — per-source m_base for P1 rescue
  ("never assume 2M", P1 §9) — and the cycle's anti-cherry-picking directive: the user
  strategic directive is "test the WORST source, not the best", and baseline §7-6 **forbids**
  reporting 2M-only as any generality headline (generality headlines LEAD with 1M, which is
  OUT@208 ~9σ but IN@200/199). The cliff position is set by each source's own H
  (m_max 201/207/208), so 2M cannot proxy 1M's cliff.
- **Assessment:** a 2M-only sweep is a legitimate, cheap, immediately-runnable **down payment**
  that settles the operating-point half of the motivation; it **cannot substitute** for the
  1M/1.5M sweeps for any cross-source or generality claim. Recommend sequencing (2M now →
  1M/1.5M after unblock) rather than either/or, if the main thread wants early signal.

## Bottom line

- **X1's entry blocker is EXPENSIVE-track, not cheap:** the 1M/1.5M joint histograms were
  summarized, never persisted (proven by exhaustive key inventory + directory-wide grep), so
  unblocking needs new DECIDE-track `.ttbin` reads — but the cost is **minutes (~5–15 min
  for a histogram-only pass over both sources), not hours**; the factorization itself is seconds.
  (A stale-vintage zero-`.ttbin` shortcut via V25 `channel_counts.npz` exists but changes the
  science input and needs a main-thread decision.)
- **2M-only is sufficient for the operating-point question (m≤201 on the frozen channel) and
  runnable today; it is NOT sufficient for X1's cross-source mandate** — the 1M/1.5M sweeps
  are genuinely required for per-source m_base and any generality claim.
