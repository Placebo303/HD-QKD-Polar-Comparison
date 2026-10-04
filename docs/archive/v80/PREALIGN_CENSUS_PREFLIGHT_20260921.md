# Pre-align H_full census preflight — READ-ONLY audit (2026-09-21)

- Scope: preparation for authorization, NOT execution. No `.ttbin` was opened, parsed, or loaded. No pipeline, conversion, decoder, or tool was executed. Evidence is code + metadata + prior reports only (all repo-resident paths quoted with lines).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`. Interpreter lane: repo `.venv` (authoritative per `docs/troubleshooting.md` Windows/WSL divergence entry).
- Related inventory (names-only, files unopened): `docs/DATA_INVENTORY_20260921.md`.

## Bottom line: **BLOCKED**

A zero-decode H_full census over the 7 newly offered datasets is not currently executable. Two independent hard blockers (either alone suffices):

- **B1 — the sole `.ttbin` reader cannot function in this environment** (TimeTagger absent; see Q1).
- **B2 — zero repo-resident alignment configuration exists for any of the 7 new datasets** (no channels / delay-offset / coin window / bin-width / frame-bins; see Q4). Every one of these is a free parameter the loader cannot derive from the file itself (see Q2).

Plus one uncertainty that must be settled before trusting any borrowed template:

- **B3 — channel-plan uncertainty, sharpest for Type0** (trio implicitly used A=1/B=5; the only repo Type0-with-channels precedent uses A=3/B=2 on a *different* acquisition; see Q4).

What is ready: the Jan-21 trio calibration template is complete and fully located (Q3), and the joint-histogram code paths exist (Q5) — but both are unusable until B1+B2(+B3) clear. Process note: any parsing is real-data execution and therefore DECIDE-gated (Pre-EXECUTE + explicit authorization + fresh additive output root).

---

## Q1 — Can we read `.ttbin` at all? **FAIL**

Commands run in repo root, nothing else executed:

```
.venv/bin/python -c "import TimeTagger; print('OK', TimeTagger.__file__)"
→ ModuleNotFoundError: No module named 'TimeTagger'  (exit 1)

.venv/bin/python -c "import numpy, pandas; print(numpy.__version__, pandas.__version__)"
→ 2.5.3 3.0.5  (verbatim; venv itself is healthy)

python3 -c "import TimeTagger; print('bare OK')"
→ ModuleNotFoundError: No module named 'TimeTagger'
```

- `TimeTagger.FileReader` existence/signature/docstring: **not determinable** — the package is absent, so nothing about `FileReader` could be inspected (no file was opened; per instructions no install was attempted).
- Consequence for the sole loader: `src/qkd_io/ttbin_pipeline.py::read_ttbin_events` (lines 91–150) does `from TimeTagger import FileReader` inside the function (line 148) and raises `RuntimeError("TimeTagger package not available...")` when the import fails (line 150). It implements **no** binary fallback ("intentionally does not implement a binary parser", lines 92–96). So today every call path through it fails before touching data.
- Dependency-note: TimeTagger is **not** in the declared dependency sets (`AGENTS.md` §8: root `numpy/pandas/numba/tqdm`; comparison `pyyaml/pyarrow/pytest`). Its absence is consistent with the manifest, not a broken install.
- **Unblock B1:** vendor TimeTagger package installed into `.venv` (needs explicit approval; package installs are outside agent constraints) — or — an approved alternate `.ttbin` reader wired behind `read_ttbin_events`. Verify with the same one-liner above (`import TimeTagger` → OK) before any further step.

## Q2 — Loader configuration (code reading only)

Source: `src/qkd_io/ttbin_pipeline.py::compute_ttbin_metrics` (line 371) with `run_ttbin_parse_pipeline` (line 557). Exact requirements, quoted:

```python
channels_cfg = (cfg.get("channels") ...) or {}
ch_a = _as_int(channels_cfg.get("A"))          # line 374
ch_b = _as_int(channels_cfg.get("B"))          # line 375
...
if ch_a is None or ch_b is None:
    raise ValueError("ttbin.channels.A and ttbin.channels.B are required")  # 378-379

pairing_cfg = (cfg.get("pairing") ...) or {}
window_ps = _as_int(pairing_cfg.get("coin_window_ps"), default=0) or 0      # 382
offset_ps = _as_int(pairing_cfg.get("offset_ps"), default=0) or 0           # 383
policy = str(pairing_cfg.get("policy") or "nearest_unique")                 # 384
# only "nearest_unique" supported (385-386)

framing_cfg = (cfg.get("framing") ...) or {}
bin_width_ps = _as_int(framing_cfg.get("bin_width_ps"), default=None)       # 389
frame_bins = _as_int(framing_cfg.get("frame_bins"), default=None)           # 390
align = str(framing_cfg.get("align") or "global")                           # 391 global|sync
postselect = str(framing_cfg.get("postselect") or "keep_all")               # 392 1click_each|keep_all
if bin_width_ps is None or frame_bins is None:
    raise ValueError("ttbin.framing.bin_width_ps and ttbin.framing.frame_bins are required")  # 393-394
```

Optional: `channels.sync` (line 376–377), `pairing.policy` (default `nearest_unique`), `framing.align` (default `global`), `framing.postselect` (default `keep_all`), top-level `segments` list for visibility only (lines 492–513).

**Free parameters per dataset** (nothing in a `.ttbin` determines them; the file yields only `(time_ps, channel, event_type)` event streams): `channels.A`, `channels.B`, (optionally `channels.sync`), `pairing.coin_window_ps`, `pairing.offset_ps`, `framing.bin_width_ps`, `framing.frame_bins` (+ `align`/`postselect` choices). The coincidence offset in particular must come from a per-dataset delay/peak calibration: the pairing kernel `_pair_nearest_unique` (line 219) applies `offset_ps` to side A before windowing, and framing (`_frame_global`, line 331; `_frame_sync`, line 340) is downstream of pairing — a wrong offset silently scrambles the joint histogram rather than erroring.

## Q3 — Known trio's frozen parameter set (calibration template)

The Jan-21 trio (`type2_1M_20260121_184040`, `type2_1p5M_20260121_183806`, `type2_2M_20260121_183657`) is fully calibrated. Values, each with file+line:

**Per-source core (all three agree except delay/peak):** d=1024, bin_width=200 ps, frame_period=204800 ps, pairing=`nearest`, rule=`legacy_v1`, threshold=40000 ps, gate=200 ps, corr_bins=16384, mapping=null.

| source | delay_used_ps | peak_center_ps | peak_sigma_ps | peak_to_bg | corr_argmax | n_pairs / frames |
|---|---|---|---|---|---|---|
| 1M `...184040` | −50 | −50 | 74.68 | 3808.6 | 8191 | 512000 rows; 519219 frames / 512144 clean |
| 1p5M `...183806` | +50 | +50 | 87.97 | 3366.1 | 8192 | 708352 rows; 722429 / 708417 clean |
| 2M `...183657` | +50 | +50 | 103.11 | 3699.4 | 8192 | 933120 rows (V26: 933120); 957951 / 933120 clean |

Provenance per value:

- Sidecar measured params: `workspace/v13r3fresh_20260816/sidecars/<sid>/sidecar_meta.json`, `materialize_params.used_params` (keys `dimension`, `bin_width_ps`, `delay_used_ps`, `peak_center_ps`, `peak_sigma_ps`, `peak_to_bg`, `corr_argmax`, `corr_bins`, `nearest_threshold_ps`, `gate_width_ps`, `frame_period_ps`, `pairing_mode`, `processing_rule_version`, `mapping`, `source_ttbin_paths`). 2M sidecar also records `source_point_dir` under the sibling checkout (`D:\Code\HD-QKD_Polar_Release\results\archive\workspace_override_points\d1024_bw200`) and `joint_origin: from_ttbin`.
- Frozen code mirrors: `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:65-81` (`SOURCES`: per-source `delay_used_ps`, `bin_width_ps: 200`, `frame_period_ps: 204800`, `parquet_rows`, frame counts); `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py:55-65` (`SOURCE_METADATA`: delay −50/+50/+50 with comment "V25 freeze decision 2026-08-18", `n_pairs` 512000/708352/933120).
- Build manifest: `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json` (schema `nbldpc_v13r3_fresh_pairs_build_manifest_v1`; processing point 1024,200 / factor 1 / block 0 / nearest / legacy_v1 / occupancy_filter 1 / joint `from_ttbin` / sequence `strict`; per-source main+chunk `.ttbin` paths, sizes, sha256).
- `channel_counts.npz` keys: `{sid}_N_ab_train_N_ab_train` (double suffix is the on-disk key, not a typo) at `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`; producer `run_v25_gate` at `nonbinary_v25_gate.py:552-596` (consumes `pairs.parquet`, writes counts + split/manifest/M0–M3 artifacts; refuses non-empty out dir, line 555–556).
- Channels: **implicit A=1/B=5, recorded nowhere per-source.** Evidence: `src/reconciliation/run_nbldpc_demo_point.py:108` defaults `raw_ch0_id=1, raw_ch1_id=5`; V56 design docs describe trio channels as "`channels 隐式 A1/B5`" (`openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/design.md:13`; `formal-ir-v56-input-domain-diagnosis/design.md:13`); sidecar `used_params.mapping` is null. Any new dataset borrowing "A1/B5" is an assumption, not a calibration.
- Pairs builder: the `pairs.parquet`+sidecar materialization ran 2026-08-16 through the `export_joint_sequence_sidecar` path with `materialize_origin: materialized_from_ttbin` into `results/real_sequences/d1024_bw200/blk0` — physically under the sibling `HD-QKD_Polar_Release` checkout paths. So the template's numeric values are authoritative, but the original build environment was partly external to this checkout.

**Correction to the task's memory pointer (verified against the actual file):** `v71_data_registry.json` (repo root) is schema `v71_data_v1` with top-level `dimension: 1024, bin_width_ps: 200, pairing: nearest, processing_rule: legacy_v1, data_sha: 84d62779, reused_from: v69` — but its three `sessions` are the **V55 intake set** (`20260123_1M_600k_0dB`, `20260107_PPLN_1p5M`, `20260123_2M_1p2M_0dB` → `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/...`), **not** the Jan-21 trio and carrying **no** delay/channel entries. The trio's delay mapping lives in the V25/V26 code + sidecars above, not in the v71 registry. Do not cite the v71 registry as the trio's calibration source.

## Q4 — New datasets: any repo-resident alignment config? **NO for all 7**

Searches covered `SHG_Type2PPLN`, `Type2PPLN_3s_2026-01-12`, `Type0_nofilter`, `2026.1.12/13/20`, `1_5M_3s_2026-01-20`, `193255`, `162106`, `162148`, `165236`, and repo-wide `Type0`. Result per dataset:

- **1.12 `Type2PPLN_3s_2026-01-12_165236{,.1}`** — NO. Only `docs/DATA_INVENTORY_20260921.md:15` filename row (sizes/mtimes; files sit directly in the date root, no subfolder) plus date-root sidecar *names* (unopened, excluded). No channels/delay/peak/bin/frame value anywhere.
- **1.13 `SHG_Type2PPLN_3s_2026-01-13_162106`** — NO. Only the inventory row (`DATA_INVENTORY_20260921.md:16`; no sidecars in dir). Nothing else in repo.
- **1.13 `SHG_Type2PPLN_3s_2_2026-01-13_162148`** — path-only, NO alignment values. Covered by `scripts/v65a_scout.py:56-63` (candidate id `2026-01-13 162148`, relative path + raw name, provisional tier B) and `docs/research_cycles/V65AR1/v65a_registry_stage0.json` — whose stage-0 verdict for this candidate is `V65A_INCOMPATIBLE / sidecar_ambiguous_provenance_conflict`: the dir's two `pie_skr_scan_ch1_5{,_new}.meta.json` declare provenance `D:\SPDC源测试\...` that matches neither the candidate dir nor raw path. They are PIE-SKR scan metas, not delay/peak/channel calibrations. No usable config is extractable.
- **1.20 `Type0_nofilter_{500K,1M,1_5M,2M}_3s_*` (4 dirs)** — NO frozen alignment; one *non-calibration* code reference. `experiments/run_golden_sweep_four_datasets.py:22-25` lists the four dirs as default datasets, but its ttbin handling (`:82-154`) *assumes* channels (`_extract_channels_from_out_root`, falling back to project default `1, 5` at line 102) and uses its own sweep-local cfg (`coin_window 200 / offset 0 / framing 20 ps × 256 / align sync / 1click_each`, lines 142–146) — that is a prior-sweep operating choice, not a per-Type0 delay/peak calibration, and reusing `offset_ps=0` as a census config would be unfounded.
- **Type0 vs Type2 channel plan** — repo says nothing establishing sameness; the only cautionary evidence points the other way: `Type0` occurs in `src/` **zero** times; the sole repo precedent of "Type0 + explicit channels" is a *different* acquisition (`tools/asenoise/*`, dataset `ASENoise_Type0`) using **`A=3, B=2`** (`tools/asenoise/README_ASENOISE.md:6`; `run_asenoise_type0_corrected_subset.py:39,415,570`). That does not prove the 1.20 Type0_nofilter wiring differs — but it kills any "Type0 obviously shares the Type2 A1/B5 plan" assumption. Status: **unknown, must be measured or sourced upstream**.

Honest metadata-level notes (from inventory only, not calibrations): all 10 locations show the same small-`X.ttbin` + large-`X.1.ttbin` pair pattern; `.1` sizes order monotonically with the rate tags (Type0: 12.6<22.2<31.9<45.7 MiB; trio: 21.0<29.6<39.8 MiB) — consistent with, but not proof of, the rate-ladder reading. The 1.20 dirs each contain an `e2e_new_ttbin_fullgrid_*` derived tree and the 1.21 dirs contain `run_config.json`/heavy sidecars — all listed by name only, unopened, excluded from evidence.

## Q5 — Pre-checks without reading data

- **`d` is a free framing parameter**, not fixed by anything in the files: census `d` = `framing.frame_bins` in the loader cfg (Q2); trio template used 1024 (`frame_bins: 1024` in `v65a_scout.py:23-31` CONTRACT; sidecar `dimension: 1024`). Prior grids explored other `d` (name-only evidence: `sidecars/d{16,...,2048}_bw{20…200}/` inside the 1.20 `e2e_*` trees; `jti_dim{8,16,32}_bw{...}` series on 1.12) — but those are unopened name listings, not calibrations.
- **Reusable implemented code paths exist, all currently gated on B1:**
  1. `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py::run_v25_gate` (line 552) — `pairs.parquet → N_ab → channel_counts.npz` + split/manifest/M0–M3. Reusable as-is for the census tail once pair tables exist; refuses to overwrite (line 555).
  2. `src/workflow/export_joint_sequence_sidecar.py` — the ttbin→joint/sequence exporter used for the trio. CLI surface (from argparse list at lines 1832–1848): `--point "d,bw"` (required), `--out-root` (required), `--sequence-source-mode`, `--joint-source-mode`, `--materialize-*` overrides (offset/max-pairs/frame-start/coinc-window/pairing-mode/rule-version/peak-gate-sigma/delay-override/occupancy-filter). It calls `_read_ttbin_timetags(ttbin_path, raw_ch0, raw_ch1)` (line 1030) with the A1/B5 default chain from `run_nbldpc_demo_point.py:108`.
  3. `src/reconciliation/run_nbldpc_demo_point.py:108-169` helpers (`_read_ttbin_timetags`, `_bin_indices_sorted_for_binwidth`, `_pairs_from_sorted_bins`) — already reused read-only by `scripts/v65a_scout.py:427-451` (`_read_raw_pairs`); the V65A CONTRACT (lines 23–35) pins the reusable numeric block: d=1024, bw=200, nearest, legacy_v1, period 204800, threshold 40000, gate 200.
- **Output-root protection:** the exporter materializes under `results/real_sequences/...` (lines 1483–1489) and the V25 gate refuses non-empty roots — both are frozen/append-only areas (`AGENTS.md` §5.2; `results/` read-only). A census needs a **fresh additive root** (e.g. new `comparison_bench/outputs_comparison/<census_id>/` + new workspace sidecar dir), never reuse of `v13r3fresh_*` / `nbldpc_v25_20260818` trees.

## Q6 — Environment hazards (Windows/WSL)

`docs/troubleshooting.md` contains **no** ttbin/TimeTagger/FileReader entry — there is no recorded WSL-specific hazard (or workaround) for this loader; its WSL behavior is **unknown**. Relevant recorded entries, quoted:

- Venv discipline (root cause of bare-interpreter failures): "System `/usr/bin/python3` has no project deps ... Use the repo venv" (`troubleshooting.md:26-37`); `AGENTS.md:280-284` ("OS: Windows host; WSL support via `wsl-env.sh`" ... "use repo venv `.venv/` only"; verify via `.venv/bin/python -c "import numpy,pytest..."`). This audit obeyed that lane.
- Pytest basetemp / Windows-path hazards: "bare `pytest -p no:cacheprovider` ... reported 26 passed + 7 setup errors" root-caused to "`pytest.ini` `addopts` carries a `--basetemp` Windows path (`D:/Code/...`) that is invalid under WSL" — fix `-o addopts=""` (`troubleshooting.md:410-424`); companion Windows entry: the same pinned basetemp collides with the protected `tmp_pytest` prefix and refuses in-test roots (`troubleshooting.md:466-489`); suite-verdict divergence Windows-vs-WSL with **WSL `.venv` authoritative** (`troubleshooting.md:492-504`). Implication for a census: run all qualification checks in WSL `.venv` with `-o addopts=""`, on a fresh additive root.
- Provenance paths: "Legacy Windows paths ... are **provenance only** — do not use them as execution defaults. For WSL, use POSIX paths" (`troubleshooting.md:92-101`; `AGENTS.md:172-174`). The trio sidecar/manifest `D:\...` ttbin paths fall under this rule.
- Parquet/pickle: outputs may silently fall back to pickle without `pyarrow`/`fastparquet` (`troubleshooting.md:64-78`) — census tooling must confirm parquet support before treating missing `.parquet` as a data problem.

## Unblock list (concrete artifacts/information each blocker needs)

1. **B1 (reader):** TimeTagger importable in `.venv` (approved install) or an approved alternate reader behind `read_ttbin_events`; acceptance = the Q1 one-liner prints OK. Until then no `compute_ttbin_metrics` call can succeed on any dataset.
2. **B2 (per-dataset alignment):** for each of the 7 datasets: physical channels A/B (+sync if used), delay/offset vs coincidence peak, coin window, bin_width, frame_bins, align/postselect choices — either from the upstream acquisition/scanner record (experiment logbook / `.ttbin` acquisition config / the unopened `run_config.json` and `e2e_*` trees, which would themselves need a scoped read authorization) or from an authorized per-dataset delay-peak scan (real-data execution → full DECIDE gate: prereg + Pre-EXECUTE + explicit user authorization + independent Pre-RESULT).
3. **B3 (Type0 channel plan):** positive wiring evidence for the 1.20 Type0_nofilter acquisition (or an authorized channel-enumeration scan) before borrowing trio A1/B5; the ASENoise A=3/B=2 precedent must be ruled in/out, not assumed away.
4. **Process:** DECIDE authorization + Pre-EXECUTE record (exact command, budget, stop rules, output-absence check) + fresh additive output root; `results/`, `comparison_bench/outputs_comparison/v13r3fresh_*`, `nbldpc_v25_20260818/`, and `workspace/v13r3fresh_20260816/` stay untouched.

*Audit method note: git read-only commands were unnecessary beyond file reads; pure-python checks used only repo `.venv` stdlib/numpy imports and JSON metadata reads. One file written (this report). No commit/push.*
