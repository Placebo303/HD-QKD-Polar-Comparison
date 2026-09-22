# TTBIN Reading Cross-Check: Checkout B (Polar Release) → Checkout A (Research Mainline)

- Date: 2026-09-21. Author: coder-fast subagent (read-only recon).
- A = `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`.
- B = `/mnt/d/Code/HD-QKD_Polar_Release`, branch **`codex/security-workbench-master-roadmap`** (observed read-only via `git branch --show-current`; this checkout is NOT on `polar-mainline` right now — any "B says X" claim below must be pinned to this branch/commit, and B was NOT switched).
- Constraints honoured: read-only in both checkouts; no pipeline/decoder run; no `.ttbin` parsing; no commit/push/branch-switch. Only filesystem `ls` / `grep` / `git grep` and file reads. One write: this file.

## 1. All ttbin-reading code in B

`grep -rn "ttbin" --include='*.py' -il` hits cluster in three functional readers plus consumers. Every actual byte-level read goes through the vendor package.

### 1a. `src/qkd_io/ttbin_pipeline.py::read_ttbin_events` — PRIMARY reader (same lineage as A's)

> `"Read .ttbin using TimeTagger's FileReader if available. This function intentionally does not implement a binary parser for the .ttbin format. It relies on the official TimeTagger Python package when installed."` (lines 91–96)

> `from TimeTagger import FileReader  # type: ignore` … `raise RuntimeError(f"TimeTagger package not available; cannot read .ttbin: {exc}") from exc` (lines 148–150)

Loop form: `while reader.hasData(): data = reader.getData(1_000_000)` → `getChannels()/getTimestamps()` (+ best-effort `getEventTypes()/getMissedEvents()`), concatenated to int64. Returns `TTBinEvents(time_ps, channel, event_type, missed_events)`. Optional parsed-cache via `HDQKD_TTBIN_CACHE*` env (npz + sha256 key, lines 113–146) — caching of parsed arrays only, no header logic.

### 1b. `low_dim_opt/core/ttbin_io.py::read_ttbin_events` — SECOND reader, different acquisition

> `from TimeTagger import FileReader  # local import: optional heavy dependency` … `reader = FileReader(str(path))` (lines 166–170)

Serves the `PolarizationEntanglement/curve` data (`<link>_HV/_VH` per-link files, pm1/pm2/pm4/pm5/pm6; docstring lines 1–33). Same vendor requirement. Adds `split_signal_channels` (channels `< 1000` = signal, `>= 1000` = virtual incl. ch1001 coincidence channel), coarse→fine peak-lag estimator, greedy 1-1 pairing, absolute-time framing `bin = t // bw; sym = bin % d`. **Not applicable to the Jan ToA datasets; do not reuse its channel plan.**

### 1c. `src/reconciliation/run_nbldpc_demo_point.py::_read_ttbin_timetags` — thin wrapper

> `def _read_ttbin_timetags(ttbin_path: Path, raw_ch0_id: int = 1, raw_ch1_id: int = 5) -> _TT:` … `events = read_ttbin_events(ttbin_path)` (lines 108–109)

Defaults channels (1, 5); filters `event_type == 0`; merges/sorts to `(TimeTag, Ch)`. Consumer, not a reader.

### 1d. Negative results (definitive)

- **No `import struct` anywhere** in B's `src/ pipelines/ tools/ security_tool/ low_dim_opt/core/ experiments/ comparison_bench/` (grep, zero hits) → **no pure-python binary header parser exists**.
- `src/reconciliation/verification.py` `unpackbits` hits are `np.unpackbits` bit-plane extraction for reconciliation — unrelated to `.ttbin` bytes.
- **No header/metadata accessor exists**: acquisition metadata is *derived post-parse*, never read from file headers: `compute_ttbin_metrics` → `events_summary {timetag_min/max/span, acquisition_duration_s}` (ttbin_pipeline.py lines 415–418, 521–530); `security_tool/common/ttbin_metrics.py::CanonicalTtbin` is a *"Validated read-only view of one stored ttbin_metrics.json"* (line 63), i.e. an adapter over already-computed JSON; `security_tool/common/session_identity.py::SessionKey` binds `{dataset_id, ttbin_source, timetag_min/max_ps, acquisition_duration_s, dimension, bin_width_ps, pairing_policy, coin_window_ps, offset_ps, channel_a/b, …}` (lines 42–57) — identity constructed from metrics+config, not from file headers.
- A's `src/qkd_io/ttbin_pipeline.py` was confirmed to be the same lineage (identical `read_ttbin_events` docstring/behaviour, `def` list matches: `read_ttbin_events`, `_pair_nearest_unique`, `compute_cross_correlation_histogram`, `_frame_global/_sync`, `compute_ttbin_metrics`, `run_ttbin_parse_pipeline`). A lacks nothing B has at the byte-reading layer.

**§1 answer: B has NO vendor-free reader. Both checkouts require the `TimeTagger` package (`FileReader`) for every `.ttbin` byte. Evidence: quotes above + zero `struct` imports.**

## 2. Alignment / channel-plan configuration in B

There is **no per-dataset YAML/JSON alignment config** in B. (`comparison_bench/configs/*.yaml` carry zero `ttbin` keys — verified by grep on `benchmark_realdata.yaml`.) Alignment is a **schema + runtime peak-search**, not a frozen table:

- **Config schema** (required keys, `compute_ttbin_metrics`, ttbin_pipeline.py lines 371–400): `channels {A, B, sync?}` · `pairing {coin_window_ps, offset_ps, policy = "nearest_unique"}` · `framing {bin_width_ps, frame_bins, align ∈ {global, sync}, postselect ∈ {1click_each, keep_all}}`, plus optional `segments` for visibility.
- **Delay resolution** (`src/workflow/export_joint_sequence_sidecar.py::materialize_real_sequences_for_point`, line 1055): `used_delay_ps = delay_override_ps ?? ttbin_cfg.delay_ps ?? ttbin_cfg.offset_ps ?? 0`, **but auto peak-search overrides it**: `if auto_peak_delay_for_nearest and peak_status == "ok" …: used_delay_ps = int(peak_center_ps)` (lines ~1102–1106). `--force-align` (e2e line 1137) forces re-alignment; `--offset-ps` (e2e line 1148) is the manual bypass (`"[E2E] manual offset override ps=…"`).
- **Channel defaults seen in tracked code**: e2e `_extract_channels_from_cfg` falls back to `(1, 2)` (run_e2e_pipeline.py lines 853–868); the golden script uses `(1, 5)` with comment `"Project default for current ttbin datasets."` (run_golden_sweep_four_datasets.py lines 101–102); the WP1 adapter test fixture uses `{A:1, B:5, sync:None}, coin 80, bw 80, d 1024, align sync, 1click_each` (test_wp1_ttbin_adapter.py).
- **Probe/fallback metrics cfg** in the golden script (`_compute_metrics_from_ttbin`, lines 142–146): `channels {1,5,None}, pairing {coin 200, offset 0, nearest_unique}, framing {bw 20, d 256, align sync, postselect 1click_each}`.
- **Shard selection rule** (`_resolve_ttbin_file`, lines 59–79): prefer the small main-header `<name>.ttbin`, exclude `.N.ttbin` shards (`re \.\d+\.ttbin$`); TimeTagger follows the `.1` chain itself (also stated in low_dim_opt ttbin_io lines 121–123).
- **Portability helper**: `src/runtime_paths.py::map_data_path` maps `D:\Data\…` → `$PROJECT_DATA_ROOT/…` or WSL `/mnt/d/…`; used by the golden script line 28.

## 3. Coverage of the NEW datasets in B (tracked files only, `git grep`)

| Dataset | Repo-resident alignment config? | Evidence |
|---|---|---|
| `Type2PPLN_3s_2026-01-12_165236` (2026.1.12) | **NOT FOUND** | Zero `git grep` hits for `165236`, `Type2PPLN_3s`, `2026-01-12`, `2026.1.12` in tracked files |
| `SHG_Type2PPLN_3s_2026-01-13_162106` | **NOT FOUND** | Zero hits for `162106`, `SHG_Type2`, `2026-01-13`, `2026.1.13` |
| `SHG_Type2PPLN_3s_2_2026-01-13_162148` | **NOT FOUND** | Zero hits for `162148` (same as above) |
| `Type0_nofilter_500K_3s_2026-01-20_193050` | **PARTIAL — path + shared defaults, no per-dataset values** | `experiments/run_golden_sweep_four_datasets.py` lines 21–26 list all four Jan-20 dirs as `DEFAULT_DATASETS`; channels (1,5) default + §2 probe cfg apply uniformly; per-dataset delay left to runtime peak-search |
| `Type0_nofilter_1M_3s_2026-01-20_192857` | **PARTIAL** (same) | Same file, line 22 |
| `Type0_nofilter_1_5M_3s_2026-01-20_193255` | **PARTIAL** (same) | Same file, line 25 |
| `Type0_nofilter_2M_3s_2026-01-20_193411` | **PARTIAL** (same) | Same file, line 23 |
| Type0 vs Type2 channel-plan distinction | **NONE for the Jan datasets** | Only tracked Type0/Type2 note is a different family: `tools/asenoise/README_ASENOISE.md:6` — ``run corrected Type0 E2E/Polar subset with channels `A=3,B=2` `` (ASENoise route, not Jan data) |

Data-presence note (directory listing only, no parsing): all exist under `/mnt/d/Data/Raw Data/`: `2026.1.12/` holds `Type2PPLN_3s_2026-01-12_165236.ttbin` + `.1.ttbin` shard (+ vendor JTI CSVs); `2026.1.13/` holds `SHG_Type2PPLN_3s_2026-01-13_162106/` and `SHG_Type2PPLN_3s_2_2026-01-13_162148/` subdirs; `2026.1.20/` holds the four `Type0_nofilter_*` subdirs. Layout differs (single-file vs per-dataset dirs); the golden `_resolve_ttbin_file` handles both (file → use directly; dir → header `.ttbin` pick).

## 4. Known-trio cross-check (Jan-21)

- **B's tracked files contain NO reference to the trio.** `git grep` for `20260121`, `2026.1.21`, `2026-01-21`, `184040`, `183806`, `183657`, `type2_1M/1p5M/2M`, `jan21` (any case): zero true hits. The single match (`cross_loss_reconciled_master_table.csv:108`) is a **false positive** — substring of the float `0.9973383018365716` (`…3018365716`), verified by CSV-column inspection.
- On-disk actual names (listing only): `Type2_1M_3s_2026-01-21_184040/`, `Type2_1-5M_3s_2026-01-21_183806/` (hyphen, not `p`), `Type2_2M_3s_2026-01-21_183657/` under `/mnt/d/Data/Raw Data/2026.1.21/`.
- **Verdict: A's mapping (1M/−50 ps, 1p5M/+50 ps, 2M/+50 ps) is NEITHER verified NOR corrected by B's tracked files.** Consistent with §2's design (B peak-searches delay per run instead of freezing per-dataset offsets), frozen trio offsets would only exist in untracked run outputs, which were deliberately not inspected. No discrepancy found; confirmation still outstanding.

## 5. Outputs proving the path works (paths + CLI form only; no scientific content opened)

- **No tracked/committed output references any new dataset** (`git grep` §3/§4 + filename scan for `*fullgrid* *golden*four* *192857* *193411* *165236* *162106*` under B's `results/ workspace/ low_dim_opt/outputs/`: only old `e2e_*dB_fullgrid_pairing_v2_candidate*` dirs for the QKD_Loss family). No `e2e_new_ttbin_fullgrid_*` / `golden_four_sweep_summary_*` artifacts exist in B.
- **Documented working CLI form** (front-half extraction, from `docs/CURRENT_MAINLINE.md:25–30` and `docs/POLAR_CODE_MAINFLOW_20260327.md` Stage 1):
  - `python experiments/run_e2e_pipeline.py --ttbin <head.ttbin> --skip-polar --force-align --out-root <e2e_out>` (single dataset; note `--ttbin`, not `--ttbin-override`)
  - Golden four-dataset form (`run_golden_sweep_four_datasets.py::_run_one`, lines 250–272): `python experiments/run_e2e_pipeline.py --dims 4,8,16,32,64,128,256,512,1024,2048,4096 --bws 20,30,40,50,60,80,100,120,150,180,200 --ttbin-override <dataset_dir> --extract-workers 12 --jobs 12 --out-root <dataset_dir>/e2e_new_ttbin_fullgrid_<ts> --force-align`, then `run_real_polar_max_pie.py --grid-table <e2e_out>\_tmp_grid_table.csv …` for the back half.
- So the invocation pattern for the new datasets is proven **as code + docs**, but **no executed result for them is committed in B**.

## 6. Importability of B's reader into A (feasibility only — no copy without OpenSpec)

- `src/qkd_io/ttbin_pipeline.py` module-level imports are **stdlib + numpy only** (`json, hashlib, math, os, sys, time, dataclasses, pathlib, typing`, lines 1–13); `TimeTagger` is a lazy in-function import. Dependency-wise it is standalone and copyable.
- BUT: (a) it buys nothing vendor-free — the `FileReader` requirement travels with it; (b) it is not a pure IO leaf — the same module houses `compute_ttbin_metrics` / `run_ttbin_parse_pipeline` and the e2e-supported metrics schema, so importing it drags B's schema along; (c) **A already holds the same reader** (identical behaviour/docstring, §1d) — there is nothing to gain by copying.
- The genuinely reusable, decoupled pieces are small pure functions, not the reader: `_resolve_ttbin_file` (header-vs-shard pick) and `map_data_path` (Windows→WSL data-root mapping) — either could be re-implemented in a few lines under an OpenSpec change if needed.

## Bottom line

- **Vendor-free ttbin reader in B? NO** (`src/qkd_io/ttbin_pipeline.py`; explicitly *"intentionally does not implement a binary parser"*; zero `struct` usage repo-wide).
- **Alignment parameter table** (filled where tracked, else NOT FOUND):

| Dataset | ch A/B | bin_width_ps | frame_bins (d) | coin_window_ps | offset/delay_ps | align/postselect |
|---|---|---|---|---|---|---|
| Trio 1M 184040 | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND (A claims −50; unconfirmed) | NOT FOUND |
| Trio 1p5M 183806 | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND (A claims +50; unconfirmed) | NOT FOUND |
| Trio 2M 183657 | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND (A claims +50; unconfirmed) | NOT FOUND |
| Jan-12 Type2PPLN 165236 | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND |
| Jan-13 SHG ×2 | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND |
| Jan-20 Type0 ×4 | (1,5) default | probe grid 20–200 | probe grid 4–4096 | 200 (probe) | 0 fallback → runtime peak-search | sync / 1click_each (probe) |

- **Trio correction from B: none** — no tracked evidence; A mapping stands unconfirmed, undisputed.
- **UNBLOCKED now**: exact CLI pattern for new datasets (`--ttbin-override` + `--force-align` fullgrid sweep; `--offset-ps` bypass exists); channel default (1,5) + probe grid for Jan-20 Type0; header-vs-shard selection rule; WSL path mapping; on-disk data presence + layout (single-file Jan-12 vs dir-per-dataset others).
- **Still BLOCKED for a zero-decode H_full census**: (1) `TimeTagger` vendor package is mandatory in this environment — no `.ttbin` byte can be read without it, in either checkout; (2) no frozen per-dataset alignment for Jan-12/13 (or trio) — first contact must be a peak-scan/census run under DECIDE (real data), not a config lookup; (3) B's checkout is currently on `codex/security-workbench-master-roadmap`, not `polar-mainline` — re-verify against `polar-mainline` before citing B as baseline authority.
