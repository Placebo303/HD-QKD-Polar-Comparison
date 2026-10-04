# Correlation-alignment capability audit — READ-ONLY (2026-09-21)

- Scope: code + metadata reads only. **No `.ttbin` opened, parsed, or loaded. No pipeline, conversion, decoder, or tool executed.** No writes except this file. No commit/push. No modification to `src/` or the sibling checkout.
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`. Sibling: `/mnt/d/Code/HD-QKD_Polar_Release`.
- Driver: lab authority requires delay auto-alignment by CROSS-CORRELATION before any pairing (the set delay is not trustworthy). This must become a mandatory P3-census (A1 arm) step before pairing/histogram/entropy.
- Related: `docs/PREALIGN_CENSUS_PREFLIGHT_20260921.md` (B1 reader blocker, B2/B3 config blockers — all still stand), `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md` §4.2–4.4 (Branch B already pre-registers fitted alignment with acceptance rule).

---

## A — This repo's correlation capability (`src/qkd_io/ttbin_pipeline.py`, frozen, read-only)

### A1. `compute_cross_correlation_histogram` (lines 252–328) — EXISTS, histogram only, no peak search

Full signature (line 252–261):

```python
def compute_cross_correlation_histogram(
    *,
    events: TTBinEvents,
    ch_a: int,
    ch_b: int,
    bin_width_ps: int,
    max_lag_ps: int,
    chunk_size: int = 100_000,
    time_tag_only: bool = True,
) -> dict[str, Any]:
```

- Takes: parsed `TTBinEvents(time_ps, channel, event_type, missed_events)` (line 19) + two channel ids. Not raw times — caller must have `read_ttbin_events` output (which needs the TimeTagger package; B1 blocker unchanged).
- Bin structure (lines 293–295): `n_bins = ceil(2*max_lag_ps / bin_width_ps)`; edges from `-max_lag_ps` in steps of `bin_width_ps`, last edge pinned to `+max_lag_ps`. **Lag convention: `lag_ps = t_B − t_A`** (docstring lines 262–266).
- Counting (lines 298–308): per-A-chunk `searchsorted` window `±max_lag_ps` in B, `np.histogram` of lags per A event — i.e. a FULL windowed pair count, O(window occupancy), not nearest-neighbour-only.
- Returns (lines 311–328): `lag_left_ps / lag_right_ps / lag_center_ps / counts` + `summary{channel_A/B, bin_width_ps, max_lag_ps, lag_convention, count_A/B, total_pairs_in_window, acquisition_duration_s, time_tag_only}`. **No peak field, no argmax, no interpolation.** Caller must do `pk = int(np.argmax(counts))`.
- Exact call precedent already in repo: `openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/diagnosis_raw_a2.py:315` and `formal-ir-v56d2-calibration/v56d2_calibration.py:139`: `compute_cross_correlation_histogram(events=events, ch_a=1, ch_b=5, bin_width_ps=100, max_lag_ps=819200)` → 16384 bins, `lag = t_B − t_A`.

### A2. `_pair_nearest_unique` (lines 219–249) — offset enters here

```python
def _pair_nearest_unique(*, t_a: np.ndarray, t_b: np.ndarray, window_ps: int, offset_ps: int) -> tuple[np.ndarray, np.ndarray]:
    """Greedy monotonic 1-1 pairing within a symmetric time window."""
    ...
    a = np.asarray(t_a, dtype=np.int64) + np.int64(offset_ps)
    b = np.asarray(t_b, dtype=np.int64)
```

Offset is added to side A, then greedy monotone 1–1 pairing within `±window_ps`. Sign consequence: with lag convention `t_B − t_A`, a measured peak at `+L` means B lags A by L, so A must be shifted forward by L: **`offset_ps = +peak_center_ps`**. (Consistent with the sidecar path, which subtracts the same delay from B: `b_bin = floor((t1 − delay)/bw)`, `export_joint_sequence_sidecar.py:1164,1219` — algebraically identical.)

### A3. `compute_ttbin_metrics` (line 371) — required keys; NO built-in alignment

```python
ch_a = _as_int(channels_cfg.get("A"))          # 374
ch_b = _as_int(channels_cfg.get("B"))          # 375
...
window_ps = _as_int(pairing_cfg.get("coin_window_ps"), default=0) or 0      # 382
offset_ps = _as_int(pairing_cfg.get("offset_ps"), default=0) or 0           # 383
policy = str(pairing_cfg.get("policy") or "nearest_unique")                 # 384 (only policy accepted)
bin_width_ps = _as_int(framing_cfg.get("bin_width_ps"), default=None)       # 389 (required)
frame_bins = _as_int(framing_cfg.get("frame_bins"), default=None)           # 390 (required)
align = str(framing_cfg.get("align") or "global")                           # 391 global|sync
postselect = str(framing_cfg.get("postselect") or "keep_all")               # 392
```

`pairing.offset_ps` defaults to 0 and is consumed only via A2. `framing.align` is frame anchoring (global-t0 vs sync-channel), NOT delay alignment. There is no peak-search, scan, or auto-align branch anywhere in this function or in `run_ttbin_parse_pipeline` (line 557).

### A4. CLI surface (grep-verified)

- `experiments/run_e2e_pipeline.py`: `--force-align` (line 1102), `--offset-ps` (1113–1117, "manual delay/offset override … applies to all requested points"), `--coinc-window-override-ps` (1118), `--ttbin/--ttbin-override/--ttbin-file-override` (1140–1146), `--ttbin-ch-a/b-override` (1148–1158). No `--align` flag exists anywhere (framing `align` is a config value, not CLI).
- `src/workflow/export_joint_sequence_sidecar.py` CLI: `--materialize-delay-override-ps` (1846), `--materialize-offset-override-ps` (1839), `--materialize-coinc-window-override-ps` (1841), `--materialize-peak-gate-sigma` (1845), `--materialize-pairing-mode` (1843).
- The REAL auto peak search lives in `src/workflow/export_joint_sequence_sidecar.py::_estimate_peak_stats_from_timetags` (lines 715–851), wired in `materialize_real_sequences_for_point` (lines 1064–1098). It is separate from `ttbin_pipeline` (see §B for the algorithm; the two checkouts share it).
- Adjacent heuristic tool (NOT recommended as-is): `tools/asenoise/export_ttbin_cross_correlation.py` — own centered-axis histogram variant (line 45, adds `center_lag_ps`), channel auto-selection "two highest-count channels among `ch < 1000`" (lines 30–42), plus a refine pass (lines 261–280). Convenience heuristic; the `ch<1000` rule is explicitly not a repository channel protocol (sibling `AGENT_PROJECT_MEMORY.md` B6 note).

### A5. Verdict for Task A

**Yes — correlation histogram + delay-peak location is computable with existing repo code unmodified**, as two frozen calls plus a thin new wrapper (additive script, not `src/`):

```python
events = read_ttbin_events(ttbin_path)   # needs TimeTagger package (B1 blocker stands)
corr = compute_cross_correlation_histogram(events=events, ch_a=..., ch_b=...,
                                           bin_width_ps=100, max_lag_ps=819200)  # 16384 bins
pk = int(np.argmax(corr["counts"]))
peak_center_ps = float(corr["lag_center_ps"][pk])
offset_ps = int(round(peak_center_ps))   # lag convention t_B − t_A; see A2
metrics = compute_ttbin_metrics(events=events, cfg={
    "channels": {"A": ch_a, "B": ch_b},
    "pairing": {"coin_window_ps": ..., "offset_ps": offset_ps, "policy": "nearest_unique"},
    "framing": {"bin_width_ps": 200, "frame_bins": 1024, "align": "global", "postselect": "keep_all"}})
```

What is missing (must be newly written, additive-only): the argmax + acceptance-gate wrapper. It must NOT be added inside `src/` (frozen baseline; cf. the V56D3 incident where `compute_cross_correlation_histogram` was modified mid-execution and had to be reverted — `openspec/changes/formal-ir-v56d3-symbol-decomposition/proposal.md:22`). Verify `git diff -- src/` is empty before any census use.

---

## B — Sibling's proven alignment procedure (`/mnt/d/Code/HD-QKD_Polar_Release`)

### B1. The e2e peak search is the SAME function in both checkouts

`diff` of `_estimate_peak_stats_from_timetags` between the two `src/workflow/export_joint_sequence_sidecar.py` files shows logic-identical content (only line-ending noise). Sibling `experiments/run_e2e_pipeline.py` carries the same flags: `--force-align` (line 1137), `--offset-ps` (1148–1152, identical help text), `--ttbin/--ttbin-override` (1175–1181), `--ttbin-ch-a/b-override` (1183–1193). There is no independent "sibling algorithm" for the HD-QKD path — one shared lineage.

Concrete algorithm (`_estimate_peak_stats_from_timetags`, `export_joint_sequence_sidecar.py:715–851`):

1. Input: two sorted timetag arrays (t0=A, t1=B). Subsample A to ≤300 000 points via `linspace` (lines 751–755) — **approximation #1 (prereg as heuristic)**.
2. dt per A event = nearest-neighbour only: closest of the two bracketing B events (`searchsorted`, lines 759–764) — **approximation #2: NOT a full correlation; far-side pairs never enter the histogram**.
3. Dynamic range (lines 770–778): requested `max(50 000, 2*frame_period)`; expanded to `max(4*frame_period, 50 000)`, capped at 20 000 000. For the census point d=1024/bw=200 (period 204 800): requested 409 600 → effective **rg = 819 200 ps**. Bin (line 1077 call site): `max(10, bw//2)` = **100 ps** for bw=200. Bins ≤400 001 cap with auto-coarsening (795–796). Census-point histogram: **16384 bins over ±819 200 ps** — identical numbers to the V56D2 fixed-port call.
4. Peak rule (lines 814–819): **plain `np.argmax`**, `peak_center = (e[pk]+e[pk+1])//2` (bin centre, no interpolation, no centroid, no fit).
5. Diagnostics: bg = median excluding ±2 bins around peak (821–825); `peak_to_bg = peak/bg` (826); sigma = bg-subtracted weighted std over ±12 bins (830–838, code comment: "Crude local sigma").
6. Status: `ok / empty_input / empty_after_range_filter / empty_hist` (727–740, 780–789, 805–812, 841).
7. Adoption (`materialize_real_sequences_for_point`, 1064–1098): if pairing is `nearest` AND `frame_period ≥ HDQKD_NEAREST_FRAME_THRESHOLD_PS` (default 40 000, env-overridable, line 1041) AND no `delay_override_ps` → `used_delay_ps = peak_center_ps` when status is `ok` (1094–1095). `--offset-ps` sets `delay_override_ps`, which DISABLES the auto path (1064, 1094). `--force-align` forces re-materialization via the `need_realign` gate (`run_e2e_pipeline.py:169–189`, cond_C_force). **No prominence/SNR/symmetry acceptance gate exists in this path** — any `ok` argmax is adopted, however weak. That absence must be pre-registered as a limitation (P3 §4.3 rule 2 already demands a frozen prominence rule to fill it).

### B2. Sibling `low_dim_opt/core/ttbin_io.py::estimate_peak_lag` (lines 259–300) — different data, heuristic only

Coarse-then-fine on curve polarization-entanglement files (NOT the HD-QKD time-bin path; module docstring lines 1–33 declares deliberate divergences): pre-pair greedy at lag 0 within ±10 000 ps → dt histogram, coarse 100 ps bins (200 bins) → `argmax` centre → fine ±1500 ps window, 5 ps bins → `argmax` centre = `peak_lag_ps`. Constants lines 75–78 (`_LAG_COARSE_WINDOW_PS=10_000`, `_LAG_COARSE_BIN_PS=100`, `_LAG_FINE_WINDOW_PS=1_500`, `_LAG_FINE_BIN_PS=5`). **No background, sigma, prominence, or rejection criterion** — returns 0 on empty input, otherwise always a number. Pure heuristic; usable as cross-check only, and only with preregistration. Do NOT cite its ±10 ns range as transferable: the HD-QKD path scans ±819 200 ps because the frame period demands it.

### B3. Golden sweep

`experiments/run_golden_sweep_four_datasets.py::_compute_metrics_from_ttbin` (lines 142–146) uses a fixed probe cfg (`coin 200 / offset 0 / bw 20 × d 256 / sync / 1click_each`) — an operating choice, not a calibration. Reusing `offset_ps=0` as census config would be unfounded (preflight Q4).

---

## C — Trio delay/peak cross-check (measured, not nominal)

### C1. Sidecar values verified live (matches preflight; quoted from `workspace/v13r3fresh_20260816/sidecars/<sid>/sidecar_meta.json → materialize_params.used_params`)

| source | delay_used_ps | peak_center_ps | peak_sigma_ps | peak_to_bg | corr_bins | corr_argmax | peak_scan_range_ps | peak_bin_ps | peak_status | delay_override_ps |
|---|---|---|---|---|---|---|---|---|---|---|
| 1M `…184040` | −50 | −50 | 74.68 | 3808.6 | 16384 | 8191 | 819200 | 100 | ok | null |
| 1p5M `…183806` | +50 | +50 | 87.97 | 3366.1 | 16384 | 8192 | 819200 | 100 | ok | null |
| 2M `…183657` | +50 | +50 | 103.11 | 3699.4 | 16384 | 8192 | 819200 | 100 | ok | null |

Mirrors: `nonbinary_v25_gate.py:65–81` (`SOURCES` delay −50/+50/+50, bw 200, period 204800); `nonbinary_v26_channel.py:55–65` (`SOURCE_METADATA`, comment: "the *existing* delay configuration, **never re-estimated**; V25 freeze decision 2026-08-18").

### C2. What `argmax8191/8192` actually means — resolved, no guessing

The estimator builds `edges = arange(−819200, 819200+100, 100)` → 16384 bins (code §B1 items 3–4; sidecar `peak_scan_range_ps=819200, peak_bin_ps=100` confirm: 2·819200/100 = 16384 exactly). Bin 8191 spans [−100, 0) with centre **−50**; bin 8192 spans [0, +100) with centre **+50**. `peak_center_ps = (e[pk]+e[pk+1])//2` (line 816). Therefore:

- `corr_argmax` is the 0-based bin index of the histogram maximum;
- the recorded `−50/+50` "offset" **is the bin centre of that argmax bin** — i.e. the measured correlation peak sits one half-bin off exact zero, at the histogram centre;
- `delay_used_ps == peak_center_ps` in all three sidecars with `delay_override_ps: null` and `peak_status: "ok"` → the auto rule (lines 1094–1095) adopted the measured peak verbatim.

**Conclusion: the recorded offsets WERE verified against a measured correlation peak; they are not nominal set-points.** The measurement chain is fully auditable (status/argmax/bins/range/bin-width all persisted per source). Strengths: p2bg 3300–3800 (very prominent), sigma 75–103 ps (≈ detector jitter scale, sane). Caveats: (i) 100 ps bins quantize the answer to ±50 ps — the −50/+50 split across sources is a one-bin flip, physically indistinguishable from zero; (ii) channels A=1/B=5 are implicit (preflight Q3, `run_nbldpc_demo_point.py:108` defaults; sidecar `mapping: null`); (iii) V26 explicitly never re-estimates — reuse is a freeze decision, not a fresh measurement.

---

## D — Recommended frozen alignment procedure (for main-thread freeze; DECIDE-gated execution)

D1. **Function**: frozen `compute_cross_correlation_histogram` (A1 call box, §A5) + new additive wrapper (workspace/comparison_bench new file — never `src/`). Do NOT route A1 through `_estimate_peak_stats_from_timetags`' nearest-neighbour approximation when the full histogram is affordable; the full count is the more defensible primary, with the estimator as cross-check. Do NOT embed auto-align into `compute_ttbin_metrics` (would modify frozen `src/`).

D2. **Frozen ports**: `bin_width_ps=100`, `max_lag_ps=819200` (16384 bins), lag convention `t_B − t_A`, channels per dataset (trio-type: A=1/B=5; new datasets: channel plan from Branch-B scan or Stage-0.5 `getConfiguration()`, never assumed).

D3. **Peak rule**: `pk = argmax counts`; `peak_center = lag_center[peak]`; **no interpolation** (100 ps bins; sub-bin fitting is unjustified at p2bg≫100 and would be a new heuristic).

D4. **Conversion**: `offset_ps = +peak_center_ps` (sign per §A2).

D5. **Acceptance (freeze numbers before run; P3 §4.3 rule 2 slot)**: `peak_status`-equivalent ok (non-empty both channels, non-empty histogram); `peak_to_bg ≥ 100` (trio floor is 3300 — 100 is a lenient, pre-registered bar); exactly one dominant mode (no second bin > 50 % of peak outside ±1000 ps of pk — mirrors P3 §4.3 rule 1 style); `10 ≤ sigma ≤ 500 ps` sanity. Anything else → **STOP-BLOCKED**, return to main thread, no pairing/histogram/entropy for that dataset.

D6. **Failure/ambiguity**: STOP-BLOCKED (never fall back to `offset 0`, never borrow another dataset's offset, never widen bins post-hoc — any of those is a science-input change per P3 §11).

D7. **Scope**: re-derive **per dataset** (user requirement; delay is acquisition-specific). Per-file within a dataset: NO — pair members are NESTED via vendor auto-follow (P3 hard prohibition §4), so open base `X.ttbin` only and align once on the merged stream. Per-frame realignment: NO — no evidence of intra-acquisition drift at the 204 800 ps frame scale; per-frame fitting would multiply selection bias. One offset per dataset, published with `alignment_mode: "FITTED"` per P3 §4.3 rules 4–6 (imposed framing d=1024/bw=200 labelled `IMPOSED-NOT-MEASURED` per §4.2).

D8. **Heuristics that must be preregistered as such**: linspace 300k subsample; nearest-neighbour dt (if estimator used as cross-check); median-bg excluding ±2 bins; "crude" ±12-bin sigma; asenoise `ch<1000` auto-channel rule (do not use for A1); low_dim_opt coarse-fine estimator (different acquisition, no acceptance gate — cross-check only). Selection-bias note: fitting uses only coincidence throughput, never the joint histogram (P3 §4.3 rule 6).

---

## Bottom line

- **Correlation-based auto-alignment CAN be done with existing repo code unmodified**: `read_ttbin_events` → `compute_cross_correlation_histogram(bin100/max_lag819200)` → `argmax` → `offset_ps=+peak_center` → `compute_ttbin_metrics`. The only new code is an additive argmax+acceptance wrapper (not in `src/`).
- **Must be frozen before A1**: ports (100/819200/16384), peak rule (argmax, no interpolation), conversion sign, numeric acceptance bar (D5), STOP-BLOCKED policy, per-dataset scope, `alignment_mode: "FITTED"` labelling — plus the two standing blockers: **B1** (TimeTagger package in `.venv`) and per-dataset **channels** (B3 for Type0; Stage 0.5 may supply them).
- **Modifying frozen `src/` is required for nothing** in this plan; embedding auto-align into `compute_ttbin_metrics`/`run_ttbin_parse_pipeline` is the one variant that WOULD require it, and is therefore rejected.
- The trio's −50/+50 offsets are measured peak-bin centres (argmax 8191/8192 of 16384), adopted verbatim by the auto rule — the procedure the user demands is exactly what produced them.

*Audit method: file reads + grep + `diff` only. One file written (this report). No commit/push.*
