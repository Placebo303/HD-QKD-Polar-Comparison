# V80-P3 Real-Data H_full Census — Design

Sources: `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md` (+ parents listed
there), `docs/ROADMAP-20260921.md` §2/§3 P3/§4/§5/§8, `docs/DATA_INVENTORY_20260921.md`,
`AGENTS.md` §1.2/§3/§10.1/§10.3, `docs/research-cycle-sop.md` §4/§10.
Condensation only; no new numbers beyond the arithmetic derived in §5 below, which is
recomputed from the frozen constants and marked as such.

## Frozen accounting (quoted, unchanged)

- Superframe n = 1024 GF(32) symbols, n_bits = 5120, H_full = 0.83256272 b/symbol,
  content = 852.544 b/frame (`PROGRAM_PLAN.md` §1.3; `S2_ACCOUNTING_MAP_20260920.md` §1;
  `L1_CONSTRUCTION_MEMO_20260920.md` §1).
- `f_super = (5·(m1+m2)+64)/852.544 ≤ 1.3` ⇒ leak ≤ 1108.31 b ⇒ m1+m2 ≤ 208.
  A208: leak 1104, f_super = 1.294947, headroom 4.31 b.
- `f_eff = f_super + 4.785675·FER`, slope `4.785675 = (5120−1040)/852.544`
  (`F_EFF_ACCOUNTING_NOTE_20260921.md` L24, Müller Eq.(13) convention). Never quote
  `f_super` as `f_eff`.
- Required zero-failure blocks `N ≥ ⌈3·4.785675/(1.3 − f_super)⌉` (rule of three,
  ceiling). Per-source superframes at n=1024: 500 / 691 / 911 (pool 2103).

## Estimator definition (single, frozen)

- `H_full ≡ H_L1 + H_L2` under F03 (`u1 = A>>5`, `u2 = A&31`), exactly
  `nonbinary_v26_channel.py::ChannelAdapter._build_entropy`: plug-in
  `P(a|b) = N_ab[a,b]/N_ab[:,b]`, zero cells dropped (not floored),
  `H_L1 = Σ_b p_b H(P(·|b))`, `H_L2 = Σ_b p_b Σ_u1 p(u1|b) H(P(·|b,u1))`,
  bits per GF(32) symbol.
- The V80 anchor `0.83256272` = `H_full(2M)` = `0.02566205 + 0.80690067`
  (`nonbinary_v26_gate.py::V25_H["A02"]`) and equals the V49 **TRAIN-pool** plug-in
  cross-entropy `0.8325627219222382`. Its own train→hold gap is +0.0204 b/symbol.
  V19's `0.549955` is a declared synthetic independence constant (different definition);
  V25's ≈0.80–0.86 empirical conditionals are the comparable family.
- Comparability flag: YES only if (config = V80 convention) ∧ (estimator = this
  definition) ∧ (split side = TRAIN plug-in); otherwise DIRECTIONAL-ONLY or NO.

## Bias / uncertainty (anti-sparse-artifact)

- Per dataset, mandatory: raw `N`, `N_ab` occupancy map, support size, occupancy;
  Miller–Madow `Ĥ_MM = Ĥ_plug + (K−1)/(2N·ln2)`; held-out gap `Δ = NLL_HOLD − H_TRAIN`;
  frame-level bootstrap CI (≥200 resamples, frozen seed) — required for every dataset
  with `H_full < 0.83256272`.
- Hard rule: no design-point use of an `H_full` without an uncertainty statement.
  Insufficient support ⇒ reported as `INSUFFICIENT-SUPPORT`, excluded from ranking.

## Memory & stationarity battery

- Per-frame error-weight distribution (mean/median/min/max/p99 + histogram), with R14
  (U2 72.70/77.62/90.07) and R2DIAG (119–128, mean 123.7) as labelled, non-pooled
  comparators.
- Block-to-block drift: per-superframe-block `P(B)`, `P(A)`, support, `H_L1`, `H_L2`,
  plus max−min and least-squares slope over block index. Reported, not gated.
- Lag-1/lag-2 autocorrelation of per-frame mismatch count and per-frame `H_L1`.
  A positive result falsifies the memoryless `gamma_f03` assumption and escalates.
- V49 60/20/20 consecutive-time split by ascending frame index; the split manifest is
  written **before** any statistic; HOLD touched exactly once.

## Mandatory pre-pairing correlation alignment wrapper (frozen packet §3A; lab authority 2026-09-21)

- Capability authority: `docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md` §§A–D. `src/qkd_io/ttbin_pipeline.py:252-328` provides the histogram only (no argmax/peak); `:219-249` adds `offset_ps` to side A (hence `offset_ps = +peak_center_ps` under lag convention `t_B − t_A`); `:371-392` has no auto-align (`offset_ps` defaults 0; `framing.align` is frame anchoring). Precedent ports `bin_width_ps=100`/`max_lag_ps=819200` (16384 bins) from `openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/diagnosis_raw_a2.py:315` and `formal-ir-v56d2-calibration/v56d2_calibration.py:139`. Sibling same-lineage estimator `src/workflow/export_joint_sequence_sidecar.py:715-851` + adoption `:1064-1098` auto-adopts any `ok` argmax with zero prominence/SNR gate (limitation this design fills with frozen gates).
- Wrapper design (NEW ADDITIVE module only — never `src/`; V56D3 revert precedent `openspec/changes/formal-ir-v56d3-symbol-decomposition/proposal.md:22`; `git diff -- src/` must be empty): `read_ttbin_events` (base `X.ttbin` only, vendor auto-follow; alias shim + repo-root `PYTHONPATH` per env PASS) → `compute_cross_correlation_histogram(bin100/max_lag819200)` → `argmax` (no interpolation) → acceptance gates (`peak_to_bg ≥ 100` with median-bg ±2-bin exclusion; single dominant mode [HEURISTIC: no secondary local max > 50% of primary outside ±1000 ps]; crude ±12-bin sigma 10–500 ps; ok-equivalent status) → `offset_ps=+peak_center` → `compute_ttbin_metrics` with that offset. Call order enforced: no pairing/histogram/entropy call for a dataset precedes a passed alignment for it. Derived ONCE per dataset on the merged stream, never per-frame. Trio −50/+50 (bins 8191/8192; `docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md` §C) are prior evidence only, never inputs.
- Branch redefinition: A1 ALSO runs alignment and must AGREE with recorded −50/+50 within one-bin tolerance (else a reported FINDING); Branch B delay/offset is MEASURED by correlation (no longer fitted) while channel plan + framing stay fitted/imposed (`d` IMPOSED-NOT-MEASURED — correlation cannot identify binning); A2/C scopes unchanged. Per-row fields: `offset_ps_derived`, `peak_bin_index`, `peak_center_ps`, `peak_to_bg`, `sigma_crude_ps`, `align_status`, prior offset comparison-only. `H_full` conditional on the derived offset.
- Stage 0.5 boundary facts carried (probe `docs/research_cycles/V80-NBLDPC-JAN21/P3_STAGE05_PACKET.md`; exact result artifact paths `[TO BE CITED at Pre-EXECUTE]`): `getConfiguration()` → `dict`, 20 keys, zero PM/EB keys ⇒ PM/EB-from-header hypothesis REFUTED at payload level; SHG-A `registered channels=[1,5,9,13,17]` vs `getChannelList()=[1001,1,5]` ⇒ channel plan from `getChannelList()`/measurements only.

## Alignment gating decision tree (the authorization question)

- The loader (`src/qkd_io/ttbin_pipeline.py`) yields only `(time_ps, channel,
  event_type)`; requires the vendor `TimeTagger` package. Env PASS 2026-09-21
  (authority `docs/TTBIN_ENV_SETUP_20260921.md`): repo `.venv` has
  `Swabian-TimeTagger==2.22.6`; bare `import TimeTagger` fails so every entrypoint
  MUST call `comparison_bench/src/comparison_bench/io/ttbin_compat.py::install_timetagger_alias()`
  BEFORE any TimeTagger import and run with repo-root `PYTHONPATH`; `src/` stays frozen.
  `FileReader` public surface is `getChannelList/getConfiguration/getData/getLastMarker/hasData`
  (channels/timestamps/event-types live on the `getData()` buffer, not the reader).
  `getConfiguration()` ("configuration at the time of file creation") MAY supply channel
  roles/gates for some datasets — if it does, that dataset's branch-B alignment could upgrade
  from FITTED to READ-FROM-FILE — marked `[TO BE DETERMINED BY STAGE 0.5]`; branches unchanged.
  `compute_ttbin_metrics` needs caller-supplied channels, pairing window/offset, and
  framing. Only Family B has repo-resident V80-convention values; Family A's
  repo-resident values impose `d=256`/`bin 20 ps`/`align=sync`/`1click_each`
  (`experiments/run_golden_sweep_four_datasets.py` L142-146); Families C/D have none.
- Branches (user selects; packet does not): **A1** configured-only control (Family B,
  cheapest, validates the machinery against the anchor); **A2** A1 + Family A under its
  own declared convention (comparability broken, needs its own declaration); **B**
  empirical alignment estimation for unconfigured datasets (parameter fitting on real
  data, pre-registered acceptance rule, published with the result, declared in any
  publication); **C** exclude unconfigured datasets.
- Branch B acceptance rule: unique argmax channel pair with second-best ≤ 50 % of best;
  single dominant coincidence peak; `offset_ps` = peak, `coin_window_ps` = frozen
  multiple of peak width. Otherwise STOP-BLOCKED.
- **Identifiability limit (must be stated)**: coincidence throughput identifies the
  channel plan and the window/offset, but NOT `bin_width_ps`/`frame_bins` (re-binning
  only relabels symbols). `d = 1024` is therefore **IMPOSED-NOT-MEASURED** under
  Branch B and every resulting row carries that label plus `ALIGNMENT-FITTED`.
- Stage 0.5 file-identity + span-continuity probe (mandatory, separately signed as
  `P3_STAGE05_PACKET.md`, must PASS before any Stage 1 read) decides auto-follow
  coverage: open ONLY `X.ttbin` (never `.1`, never both — both-member concatenation is
  HARD-FORBIDDEN because members are NESTED/SUPERSET: byte-identical configs, shared
  start, vendor auto-follow docstring, 8 KB Jan-12 base alone spanning 29.9999524 s;
  authority `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §C); record `getConfiguration()`
  verbatim + type, `getChannelList()`, `getLastMarker()`, and a minimal first/last-timestamp
  span drain. Pass rule: span > 0 AND span consistent with `.1`−base mtime gap; both-or-neither,
  span ≤ 0, or mismatch ⇒ STOP-BLOCKED. Duration is MEASURED (span), never the filename tag:
  rows carry `duration_measured_s`/`filename_duration_tag`/`tag_disputed`; Jan-12 quarantined
  at 30.0 s, tag disputed (authority §D). A doubled stream would silently corrupt every
  estimator/uncertainty and memory statistic, so the prohibition gates all of them.

## Certification arithmetic (conditional; derived here, not a new constant)

- Conditional table at `m_max(H) = ⌊(1.3·1024·H − 64)/5⌋`: anchor 0.83256272 → m 208,
  f 1.294947, headroom 4.31 b, N ≥ 2842; 0.80690067 → m 202, f 1.299823, headroom
  0.15 b, N ≥ 81156; 0.80 → m 200, f 1.298828, headroom 0.96 b, N ≥ 12252; 0.75 →
  m 186, f 1.294271, headroom 4.40 b, N ≥ 2506; 0.70 → m 173, f 1.296038, headroom
  2.84 b, N ≥ 3624; 0.65 → m 160, f 1.298077, headroom 1.28 b, N ≥ 7466; 0.60 →
  m 146, f 1.292318, headroom 4.72 b, N ≥ 1869.
- Derived structural result (this change, from the frozen constants; to be confirmed by
  the main thread): at `m = m_max`, `slack(H) < 5` bits always, so
  `N_req = ⌈14701.59·H/slack⌉ > 2940.32·H`. At the anchor this exceeds 2448 and equals
  2842 — above the pool (2103) and far above any single source (≤911). Certifiability
  against 911 blocks would need `H < 0.310`; against the pool `H < 0.716`.
- "Lower `H_full` buys headroom" is FALSE at fixed m: at A208,
  `f_super = 1104/(1024·H) ≤ 1.3` requires `H ≥ 0.829327`, so any dataset below that is
  out of box. The real lever is the pair `(H_full, m_min)`; `m_min` is not measured
  here. The capacity-equivalent reference line `m_cap = n·H/5` (f ≈ 1.07–1.11,
  N ≈ 63–93) is reported for later use only and is not a claim.

## Gates / budgets / forbidden (freeze)

- Control gate: Family-B 2M `H_full` within the frozen tolerance of `0.83256272`
  (proposed ±0.01 b/symbol, V26 `ENTROPY_TOL_BITS` granularity precedent, to be
  confirmed at the authorization gate). FAIL ⇒ the machinery is not validated and must
  not be pointed at new data.
- Alignment gate (Branch B) and support gate (bootstrap CI half-width ≤ proposed
  0.02 b/symbol) as above; memory/stationarity statistics are reported, not gated, and a
  positive result escalates to the main thread.
- ≤1800 s/dataset single window; ≤5400 s (A1) / ≤18000 s (B); RSS < 4 GiB;
  0 decoder/DE/graph/`tools/*` calls; ≥200 bootstrap resamples/dataset; wall-partial ⇒
  `INCOMPLETE` retained; ≤1 preregistered engineering repair+rerun for infrastructure
  failure only, inputs unchanged.
- Fresh additive `workspace/p3_census_<uuid8>`; `results/` and
  `comparison_bench/outputs_comparison/` forbidden; frozen modules read-only; new thin
  module only; fake-only tests; per-frame statistics must assert equality with
  `compute_ttbin_metrics` aggregates on the control arm.
- Forbidden: reading excluded derived artifacts; overwriting evidence roots; pooling
  across datasets/families; merging `undetected` into success; quoting TRAIN plug-in as
  held-out (or vice versa) without the split side; averaging V19's `0.549955` with an
  empirical number; inventing alignment parameters, seeds, or block counts; changing any
  frozen constant or the estimator definition; commit/push/PR.

## Auth boundary

- Freeze consumes nothing. Execution requires: signed `PREREG_AND_AUTH.md` (naming the
  §4 branch, dataset list, config path, seed, tolerances, wall ceiling) → Pre-EXECUTE
  Q0–Q6 → one bounded run → independent Pre-RESULT → main-thread acceptance.
- A FAIL at any gate blocks the next step; no publish-then-patch. The route decision
  (which source carries the headline; whether synthetic→real transfer holds) is made by
  the main thread, not here.
