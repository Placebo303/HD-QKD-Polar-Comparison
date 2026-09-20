# Raw-data inventory — newly offered acquisition datasets (2026-09-21)

- Inventory date (UTC): 2026-09-21. Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`. Raw root: `/mnt/d/Data/Raw Data/`.
- Method: `ls` / `ls -R` (names only) + `find -iname '*.ttbin'` with size/mtime. **No `.ttbin` was opened, parsed, or loaded. No pipeline, decoder, DE, or `tools/*` was run. No derived-result file was opened for scientific content — derived files are listed by name only.**
- The single write of this turn is this file. Nothing was written anywhere else.

## 1. Per-dataset classification table

Conventions: sizes as `bytes (MiB, 1 MiB = 1048576 B)`. mtime in filesystem-reported `CST`.
Every dataset location contains a **pair**: one small `X.ttbin` (~8–21 KB) and one large `X.1.ttbin` (tens of MB).
The pairing pattern itself is an observation; what the small file *means* (header-only vs first chunk) is NOT established (see §4).

| label | date | type-tag (from name) | count-rate tag (from name) | duration tag | resolved POSIX path | ttbin files found (bytes / MiB / mtime) | derived-artifact folders/files present-but-EXCLUDED | notes |
|---|---|---|---|---|---|---|---|
| 1.12-Type2PPLN | 2026-01-12 | Type2PPLN | unknown (no rate tag in name) | `3s` | `/mnt/d/Data/Raw Data/2026.1.12/` (files sit directly in date root, no per-dataset subfolder) | `Type2PPLN_3s_2026-01-12_165236.ttbin` — 8160 B (0.008 MiB), 2026-01-12 16:52:36 · `Type2PPLN_3s_2026-01-12_165236.1.ttbin` — 16909712 B (16.126 MiB), 2026-01-12 16:53:06 | Date-root sidecars (names only, unopened, excluded): `111Bidirectional_histogram_2026-01-12_165000.txt`, `Bidirectional_histogram_2026-01-12_164025.txt`, `Bidirectional_histogram_2026-01-12_164310.txt`, `Bidirectional_histogram_2026-01-12_165452.txt`, `BFC_correlation.opju`, `BFC_correlation.pptx`, `JTI提取.opju`, `W20260112-2.CSV`, `bp20260112.CSV`, `bpcenter.CSV`, `bpleft.CSV`, `bpleft1.CSV`, `bpright.CSV`, `bpright1.CSV`, `lp20260112.CSV`, `lp20260112.opju`, `jti_dim{8,16,32}_bw{50,100,200,300}ps.{counts,normalized}.csv` + `.meta.json` series, `jti_summary.json` | User gave entries 5–6 WITHOUT a subfolder — confirmed correct as-given (both files exist at date-root level). Only location in this batch without a per-dataset subfolder. Base/.1 mtime gap ≈ 30 s (largest gap in batch; all others ≈ 3 s). |
| 1.13-SHG-a | 2026-01-13 | SHG_Type2PPLN | unknown | `3s` | `/mnt/d/Data/Raw Data/2026.1.13/SHG_Type2PPLN_3s_2026-01-13_162106/` | `SHG_Type2PPLN_3s_2026-01-13_162106.ttbin` — 8256 B (0.008 MiB), 2026-01-13 16:21:06 · `SHG_Type2PPLN_3s_2026-01-13_162106.1.ttbin` — 59329744 B (56.581 MiB), 2026-01-13 16:21:09 | None inside this dataset dir (only the 2 ttbin files) | Entries 3–4 resolve exactly as given. Largest `.1.ttbin` pair-member runner-up (56.6 MiB). |
| 1.13-SHG-b | 2026-01-13 | SHG_Type2PPLN (`_2` suffix = second run) | unknown | `3s` | `/mnt/d/Data/Raw Data/2026.1.13/SHG_Type2PPLN_3s_2_2026-01-13_162148/` | `SHG_Type2PPLN_3s_2_2026-01-13_162148.ttbin` — 8160 B (0.008 MiB), 2026-01-13 16:21:48 · `SHG_Type2PPLN_3s_2_2026-01-13_162148.1.ttbin` — 60113104 B (57.328 MiB), 2026-01-13 16:21:51 | Same-dir sidecars (names only, unopened, excluded): `SHG_Type2PPLN_3s_PIESKR.opju`, `pie_skr_scan_ch1_5.csv` + `.meta.json`, `pie_skr_scan_ch1_5_new.csv` + `.meta.json` | Entries 1–2 resolve exactly as given. Largest `.1.ttbin` in batch (57.3 MiB). Only SHG dir carrying analysis sidecars. |
| 1.20-Type0-500K | 2026-01-20 | Type0 (+`nofilter`) | 500K | `3s` | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_500K_3s_2026-01-20_193050/` | `Type0_nofilter_500K_3s_2026-01-20_193050.ttbin` — 21072 B (0.020 MiB), 2026-01-20 19:30:50 · `Type0_nofilter_500K_3s_2026-01-20_193050.1.ttbin` — 13240624 B (12.627 MiB), 2026-01-20 19:30:53 | `e2e_new_ttbin_fullgrid_20260305_031909/` containing (names only, unopened, excluded): `_tmp_grid_table.csv`, `_tmp_src_table.csv`, `e2e_alignment_audit.csv`, `polar_e2e_results.csv`, `ttbin_quick_analysis.json/.md`, `sidecars/d{16,32,128,256,1024,2048}_bw{20…200}/` subdirs | Entry 10 was given as bare dir — confirmed it IS a dir, ttbin pair inside. |
| 1.20-Type0-1M | 2026-01-20 | Type0 (+`nofilter`) | 1M | `3s` | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_1M_3s_2026-01-20_192857/` | `Type0_nofilter_1M_3s_2026-01-20_192857.ttbin` — 21072 B (0.020 MiB), 2026-01-20 19:28:57 · `Type0_nofilter_1M_3s_2026-01-20_192857.1.ttbin` — 23285488 B (22.207 MiB), 2026-01-20 19:29:00 | `e2e_new_ttbin_fullgrid_20260304_231635/` with same file layout as above (names only, unopened, excluded) | Entry 8 was given as bare dir — confirmed dir, pair inside. |
| 1.20-Type0-1.5M | 2026-01-20 | Type0 (+`nofilter`) | 1_5M (=1.5M) | `3s` | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_1_5M_3s_2026-01-20_193255/` | `Type0_nofilter_1_5M_3s_2026-01-20_193255.ttbin` — 21072 B (0.020 MiB), 2026-01-20 19:32:55 · `Type0_nofilter_1_5M_3s_2026-01-20_193255.1.ttbin` — 33469312 B (31.919 MiB), 2026-01-20 19:32:58 | `e2e_new_ttbin_fullgrid_20260305_055352/` with same file layout as above (names only, unopened, excluded) | Entry 7 was given as bare dir — confirmed dir, pair inside. `.1.ttbin` size ordering 500K < 1M < 1.5M < 2M holds (12.6 < 22.2 < 31.9 < 45.7 MiB) — consistent with rate-tag meaning, but still filename-level evidence only. |
| 1.20-Type0-2M | 2026-01-20 | Type0 (+`nofilter`) | 2M | `3s` | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_2M_3s_2026-01-20_193411/` | `Type0_nofilter_2M_3s_2026-01-20_193411.ttbin` — 21072 B (0.020 MiB), 2026-01-20 19:34:11 · `Type0_nofilter_2M_3s_2026-01-20_193411.1.ttbin` — 47920192 B (45.700 MiB), 2026-01-20 19:34:14 | `e2e_new_ttbin_fullgrid_20260305_011024/` with same file layout as above (names only, unopened, excluded) | Entry 9 was given as bare dir — confirmed dir, pair inside. |
| 1.21-Type2-1.5M (known trio) | 2026-01-21 | Type2 | 1-5M (=1.5M) | `3s` | `/mnt/d/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/` | `Type2_1-5M_3s_2026-01-21_183806.ttbin` — 21264 B (0.020 MiB), 2026-01-21 18:38:06 · `Type2_1-5M_3s_2026-01-21_183806.1.ttbin` — 31014064 B (29.577 MiB), 2026-01-21 18:38:09 | `run_config.json` (name only, NOT opened, excluded) | Entry 11 was given as bare dir — confirmed dir, pair inside. One of the Jan-21 trio already in use. |
| 1.21-Type2-1M (known trio) | 2026-01-21 | Type2 | 1M | `3s` | `/mnt/d/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/` | `Type2_1M_3s_2026-01-21_184040.ttbin` — 21264 B (0.020 MiB), 2026-01-21 18:40:40 · `Type2_1M_3s_2026-01-21_184040.1.ttbin` — 22025840 B (21.005 MiB), 2026-01-21 18:40:43 | HEAVY derived tree (names only, unopened, excluded): 12 top-level `ab_*`/`abcd_*`/`ooc_*`/`ratebook_*`/`seed_sweep_*` CSV+MD sidecars, ~109 `results*` subdirs (`results`, `results_ab_*`, `results_l{2,3,4,5,74}_*`, `results_nb_mlc_*`, `results_ooc_*`), ~100 `run_config*.json` files | Entry 12 was given as bare dir — confirmed dir, pair inside. By far the most analysis-contaminated folder in the batch — treat every non-ttbin file here as untrusted. |
| 1.21-Type2-2M (known trio; V80 frozen channel source) | 2026-01-21 | Type2 | 2M | `3s` | `/mnt/d/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/` | `Type2_2M_3s_2026-01-21_183657.ttbin` — 21264 B (0.020 MiB), 2026-01-21 18:36:57 · `Type2_2M_3s_2026-01-21_183657.1.ttbin` — 41768912 B (39.834 MiB), 2026-01-21 18:37:00 | `run_config.json` (name only, NOT opened, excluded) | Entry 13 was given as bare dir — confirmed dir, pair inside. `.1.ttbin` size ordering 1M < 1.5M < 2M holds (21.0 < 29.6 < 39.8 MiB). |

**Totals: 20 `.ttbin` files = 10 base + 10 `.1` files, across 10 dataset locations in 4 date roots. No `.ttbin` exists nested deeper than the dataset top level** (`find -mindepth 3 -iname '*.ttbin'` under the four date roots returns nothing).

## 2. Full date-root listings (incl. datasets the user did not list)

### 2026.1.12 — `/mnt/d/Data/Raw Data/2026.1.12/`
- The 2 user-listed ttbin files sit directly here (no subfolder). Everything else in this root is sidecar/derived material (listed in the table row above; names only, excluded).
- No subdirectories at all. No other ttbin.

### 2026.1.13 — `/mnt/d/Data/Raw Data/2026.1.13/`
- `SHG_Type2PPLN_3s_2026-01-13_162106/` — user-listed (ttbin pair, no sidecars).
- `SHG_Type2PPLN_3s_2_2026-01-13_162148/` — user-listed (ttbin pair + PIE-SKR sidecars, excluded).
- **Unlisted, confirmed no ttbin inside:**
  - `20260113_165733/` — `heralded_g2_cw.{pdf,png,_data.csv,_metadata.json,_params.csv}` only.
  - `20260113_170216/` — `g2_fitting.pptx`, `g2_fitting_valley.opju`, + same `heralded_g2_cw.*` set.
  - `20260113_170828/` — same `heralded_g2_cw.*` set only.
- Root-level files: `HOM准直功率标定.opju/.pptx/.xlsx`.
- All `heralded_g2` / HOM / `.opju` / `.pptx` / `.xlsx` material: names only, excluded as derived.

### 2026.1.20 — `/mnt/d/Data/Raw Data/2026.1.20/`
- The 4 user-listed `Type0_nofilter_*` dirs (each: ttbin pair + one `e2e_new_ttbin_fullgrid_*` derived tree, excluded).
- Root-level files: `Bidirectional_histogram_2026-01-20_213539.txt`, `Type0-SHG.opju` (names only, excluded).
- No other subdirectories. No other ttbin.

### 2026.1.21 — `/mnt/d/Data/Raw Data/2026.1.21/`
- User's prior knowledge of this root **confirmed**: `20260121_175713/`, `20260121_180507/`, `20260121_181033/`, `20260121_182048/`, `JSI(测了一点).xlsx`, `Type2PPLN_775.6CAR.opju`, `Type2PPLN_775.6CAR.xlsx` all present, plus the 3 user-listed `Type2_*` dataset dirs.
- **Unlisted folders recursed — confirmed NO `.ttbin` in any of them:**
  - `20260121_175713/`, `20260121_180507/`, `20260121_181033/` — `heralded_g2_cw.{pdf,png,_data.csv,_metadata.json,_params.csv}` only.
  - `20260121_182048/` — same `heralded_g2_cw.*` set + `Type2PPLN_775.6g2.opju`.
- `JSI(测了一点).xlsx`, `Type2PPLN_775.6CAR.opju/.xlsx`: names only, excluded as derived.

## 3. Discrepancies (as-given path vs observed)

Strictly speaking **all 13 entries resolved** — no path failed. The following are structural observations, not failures:

1. **Entries 5–6 (2026.1.12): user omitted a subfolder — correctly so.** The files exist directly at `/mnt/d/Data/Raw Data/2026.1.12/Type2PPLN_3s_2026-01-12_165236{,.1}.ttbin`. There is no per-dataset subfolder on 1.12, unlike the 1.13/1.20/1.21 sessions. Any tooling that assumes `<date>/<dataset>/*.ttbin` nesting will need a special case for 1.12.
2. **Entries 7–13: user gave bare directories with no filename — correctly so.** Each is a directory containing exactly 2 ttbin files (the `X.ttbin` + `X.1.ttbin` pair). Resolved paths: `<dir>/<dirname>.ttbin` and `<dir>/<dirname>.1.ttbin` (with `1_5M`/`1-5M` spelling preserved per session: 1.20 uses `1_5M`, 1.21 uses `1-5M`).
3. **No `*.ttbin` missing anywhere; no fallback search was needed.** `find` over all four date roots returns exactly the 20 files of the 10 expected pairs — no orphans, no extras, no nested copies.
4. **Mtime sanity (observation, not provenance):** in every pair, the base `X.ttbin` mtime matches the timestamp embedded in its filename to the second, and the `.1.ttbin` follows ~3 s later (1.12: ~30 s later). This is consistent with the `3s` acquisition tag but is filesystem evidence only, not acquisition-log proof.

## 4. Candidate classification for future use (ALL INFERRED-FROM-FILENAME — NOT established)

- **Family A — Type0 nofilter rate ladder (1.20, 4 sets):** `Type0_nofilter_{500K,1M,1_5M,2M}_3s_*`. INFERRED-FROM-FILENAME: same source (Type0 phase-matching, no filter), same 3 s acquisition, swept count-rate/attenuation ladder. Supporting (weak) evidence: `.1.ttbin` sizes increase monotonically with the rate tag (12.6 / 22.2 / 31.9 / 45.7 MiB). Use-case hypothesis (inference): rate-vs-quality tradeoff studies.
- **Family B — Type2 rate ladder (1.21, 3 sets = known trio):** `Type2_{1M,1-5M,2M}_3s_*`. INFERRED-FROM-FILENAME: same Type2 source, 3 s, rate ladder. Sizes increase monotonically with rate tag (21.0 / 29.6 / 39.8 MiB). Already in use; 2M set is the V80 frozen-channel source.
- **Family C — SHG Type2PPLN pair (1.13, 2 sets):** `SHG_Type2PPLN_3s_*` and `SHG_Type2PPLN_3s_2_*` (~42 s apart). INFERRED-FROM-FILENAME: SHG-pumped Type2PPLN configuration differing from Family B's source; `_2` = immediate repeat run. Largest `.1.ttbin` files in the batch (~57 MiB each) — consistent with (but not proof of) a brighter/different operating point.
- **Family D — early Type2PPLN single (1.12, 1 set):** `Type2PPLN_3s_*`, no rate tag, no subfolder, accompanied by JTI/histogram sidecars. INFERRED-FROM-FILENAME: earliest session; predates the rate-ladder naming convention; possibly a different acquisition protocol (note the anomalous 30 s base→.1 mtime gap vs ~3 s everywhere else).
- **Cross-family inference (weak):** 1.12/1.13 sessions predate the 1.20/1.21 ladder sessions and use different naming (no rate tags, `SHG_` prefix, flat layout), so they likely come from an earlier acquisition protocol — but the protocol (PM/EB settings, channel mapping, sync usage) is NOT recoverable from filenames and must come from acquisition logs or the ttbin stream itself (see §5).
- **The universal `X.ttbin` + `X.1.ttbin` pairing** (small ~8–21 KB + large MB-scale file) is an observed filesystem regularity across all 10 locations. What the small file contains is NOT established by this inventory — do not assume header-only vs data-chunk without vendor documentation or a controlled read.

## 5. ttbin loader capability (item 6 — code inspection only, nothing executed)

- **Loader location:** `src/qkd_io/ttbin_pipeline.py` (575 lines; `src/qkd_io/__init__.py` is empty). Sole ttbin reader in the repo.
- **Quoted entry points:**
  - `read_ttbin_events(ttbin_file: Path | str) -> TTBinEvents` (line 91) — "Read .ttbin using TimeTagger's FileReader if available. This function intentionally does not implement a binary parser for the .ttbin format. It relies on the official TimeTagger Python package when installed."
  - `compute_ttbin_metrics(*, events: TTBinEvents, cfg: dict[str, Any]) -> dict[str, Any]` (line 371) — event selection, pairing, framing/symbol mapping; requires caller-supplied `channels.A/B`, `pairing.coin_window_ps/offset_ps`, `framing.bin_width_ps/frame_bins`.
  - `run_ttbin_parse_pipeline(...)` (line 557) — full parse pipeline wrapper.
  - Helpers: `compute_cross_correlation_histogram` (252), `_pair_nearest_unique` (219), `_frame_global` (331), `_frame_sync` (340), `compute_delta_distribution_from_joint_sparse` (48). Dataclass `TTBinEvents(time_ps, channel, event_type, missed_events)` (line 19).
  - Consumers: `src/reconciliation/run_nbldpc_demo_point.py::_read_ttbin_timetags` (line 108, wraps `read_ttbin_events`); `src/workflow/export_joint_sequence_sidecar.py` imports `_read_ttbin_timetags` (line 31).
- **Is there a lightweight header/metadata-only read? NO.** `read_ttbin_events` opens `TimeTagger.FileReader` and drains the whole stream in 1M-event chunks via `hasData()/getData()` → `getChannels()/getTimestamps()/getEventTypes()/getMissedEvents()`. Those six calls are the ONLY FileReader API surface used anywhere in the file — no header/config/acquisition-counter/session accessor is called. The repo explicitly refuses to implement a binary parser, so without the vendor `TimeTagger` package installed nothing can be read at all (it raises `RuntimeError: TimeTagger package not available`).
- **Bearing on the PM/EB and acquisition-protocol question:** the loader yields only raw `(time_ps, channel, event_type)` streams; acquisition duration itself is derived downstream from `min/max(time_ps)` span, not from file metadata. There is corroborating repo evidence that header acquisition identity is unavailable: `V67_FEASIBILITY_REPORT.md` notes `acquisition_id = session_id` fallback because "ttbin header acquisition_counter [is] missing". So PM/EB settings, filter configuration, channel-plan/sync usage, and protocol version CANNOT be extracted via the current loader — they must come from acquisition logs, operator notes, or a vendor-documented header read that does not currently exist in the repo. Building such a probe would be new scope (and would touch real data → DECIDE track).
- **NOT run:** neither `read_ttbin_events` nor any consumer was invoked on the new data (or any data) in this turn.

## 6. Boundary note

- Nothing parsed, nothing loaded, no pipeline/decoder/DE/tools run, no derived-result file opened for content.
- Derived artifacts (every `results*/`, `e2e_new_ttbin_fullgrid_*/`, `sidecars/`, CSV/JSON/MD/PNG/PDF/OPJU/PPTX/XLSX sidecar listed above) were inventoried by NAME ONLY and are explicitly EXCLUDED from consideration as untrusted, unknown-provenance material.
- The single write of this turn is this file: `docs/DATA_INVENTORY_20260921.md`. Nothing was written outside `docs/`.
