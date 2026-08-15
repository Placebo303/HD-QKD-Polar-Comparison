# V13-R3 Fresh Data Intake / Drift Precheck Plan (2026-08-16)

Status: **AMENDED PLAN — D0–D5 executed; D5 drift_exceeded; P/E/V gated**
Change: `formal-nonbinary-ldpc-v13-r3-fresh-acquisition`

> This document supersedes the draft that was colloquially called “v16”.
> V16 is an archived aborted draft; this is the V13-R3 fresh data intake amendment.

## 0. Verdict on the previous draft

The previous draft must **not** be executed as a fresh-confirmation path:

1. The three provided sources are `2026-01-21` captures, i.e. **not fresh** under the
   frozen design (§1: later than V13 history and not covered by historical locks).
2. Existing D2 smoke evidence already shows drift:
   - `D:\Code\HD-QKD_Polar_Release\workspace\v13r3fresh_d2_smoke\sidecar_meta.json`
     - `raw_ser = 0.254663`
     - `map_sanity.verdict = "FAIL"`
     - `fail_reason = "map_ser>=0.1"`
   - V13 D01 reference: raw SER mean `0.0771`, interval `0.0391–0.1133`.
3. `block_index 0/1/2` is invalid with the Release materializer:
   - `_resolve_materialize_max_pairs` returns `0` (uncapped) for `d=1024`, `max_pairs<=256`;
   - `start = block_index * n_take` then fails for `block_index > 0`.
4. Execute/verify tooling does not exist yet.
5. Approval policy is now `never`: no interactive approval gates, but frozen scientific
   stop rules still apply automatically.

## 1. D0 — Data admission / freshness gate (COMPLETED)

Decision: **reject as fresh-confirmation source**.

Evidence:
- acquisition timestamps: `2026-01-21` < fresh boundary.
- loss metadata: paths/run_config do not prove 10 dB Type-II.
- folder1 is already present in Release scratch materialize evidence.

Output:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_intake_20260816/intake_decision.json`

## 2. D1 — Environment and isolation baseline

- Record Release `HEAD=581cd05`, Comparison `HEAD=e31dedf`.
- Record `git status --porcelain=v1` before/after.
- Verify Python 3.12, numpy, pandas, pyarrow, TimeTagger.
- Snapshot Release scratch paths:
  - `results/archive/workspace_override_points/d1024_bw200/**`
  - `results/real_sequences/d1024_bw200/**`

## 3. D2/D3 — Sidecar extraction (corrected)

Each source:
- use `--block-index 0`
- independent out-root
- explicit `--materialize-max-pairs 0`
- explicit `--materialize-occupancy-filter 1`
- explicit `--materialize-diagnostics 1`
- env `HDQKD_TTBIN_FILE_OVERRIDE` = main `.ttbin`
- env `HDQKD_TTBIN_CH_A_OVERRIDE=1`, `HDQKD_TTBIN_CH_B_OVERRIDE=5`

Source tags:
- `type2_1p5M_20260121_183806`
- `type2_1M_20260121_184040`
- `type2_2M_20260121_183657`

Staging isolation:
- move `attempt_0` and `blk0` to per-source `_previous` before each run
- copy new `attempt_0`/`blk0` to per-source `_after` after each run

Ready-to-run workspace orchestrator:
`workspace/v13r3fresh_20260816/run_d2_d5.ps1`

Validation:
- `a_eff.npy`, `b_eff.npy`, `sidecar_meta.json`, `joint_counts_sparse.json`,
  `chan_ll_table.npy`, `map_sanity.csv`, diagnostics files
- integer dtype, equal shapes, symbols `⊆ [0,1024)`
- `sequence_source_mode=strict`, `sequence_is_sampled=0`,
  `joint_source_mode=from_ttbin`, `joint_origin=from_ttbin`,
  `materialize_origin=materialized_from_ttbin`, `materialize_ok=1`
- nested `used_params.source_ttbin_paths` equals the source main ttbin
- `occupancy_filter.filter_enabled=1`

## 4. D4 — Pairs-table construction

- 256 symbols/frame; drop tail; record tail.
- Columns: `frame_id,pair_idx,alice_symbol,bob_symbol`.
- Output:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/<source_tag>/pairs.parquet`
- Root `build_manifest.json` records ttbin sha256, sidecar hashes, commands, env,
  git HEADs, frame counts, timestamp.
- Self-check with `load_pairs_table` + `normalize_pair_columns`.

## 5. D5 — Read-only drift precheck

Reference (V13 D01):
- raw SER mean `0.0771`, frame interval `0.0391–0.1133`
- conditional entropy `0.5469729` bits/symbol
- bit-plane mismatch MSB-first Gray, monotone `3.05e-5 -> 3.75e-2`

Frozen stop:
- `|mean_ser - 0.0771| > 0.03`
- `|H - 0.5469729| > 0.3`
- non-monotone bit-plane mismatch

Any breach → `drift_exceeded`, automatic stop, no P/E/V.

Executed on all three sources (2026-08-16). Full report:
`workspace/v13r3fresh_20260816/precheck_report.json` — `precheck_state=drift_exceeded`
for all three sources. Per frozen stop rule, do **not** proceed to P/E/V.

## 6. P1/P2 — Only if D0 freshness + D5 pass

Command:
```powershell
python -m comparison_bench.src.comparison_bench.cli.run_v13r3_fresh_prepare prepare `
  --production-prepare-authorized `
  --declared <p1.parquet> --declared <p2.parquet> --declared <p3.parquet> `
  --discovery-root D:\Code\HD-QKD_Polar_Comparison\comparison_bench\outputs_comparison\formal_ir_methods `
  --seed 20260815 `
  --run-id v13r3fresh_prepare_20260816 `
  --output D:\Code\HD-QKD_Polar_Comparison\comparison_bench\outputs_comparison\nonbinary_diagnostics\v13r3fresh_prepare_20260816
```

Main-thread review: plan_sha256, eligible>=192, exclusions, roles, scale, stop rules.

## 7. E0 — Execute/verify implementation (missing)

New files:
- `formal_ir/nonbinary_v13r3_fresh_execute.py`
- `cli/run_v13r3_fresh_execute.py`
- `cli/verify_v13r3_fresh_execute.py`
- tests (T0/T1)

## 8. E1/V1

- E1: drift recheck + decode canary 64 + confirmation 128 once, keep all evidence.
- Any failure → `frozen failure`.
- V1: read-only verifier, no byte changes.
- All green → `fresh-confirmed` (not promotion/qualification).

## 9. C — Closeout

- Update tasks.md, decision-log, memory §53, CURRENT_TASK/AGENT_HANDOFF.
- Local commit only; no push.
- Release scratch not committed.
- If D0/D5 stop: keep P1 `no_eligible_frames`; new intake package marks
  `data_intake_rejected`.

## 10. Extensions

- D-cal: positive control with canonical 10 dB source
  `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808`
- Fresh acquisition spec: >2026-08-16, 10 dB Type-II, q=1024, Gray, 256 symbols/frame,
  bw200, channels 1/5, >=256 complete frames (prefer >=1024).
- Legacy audit alternative: separate OpenSpec change, claim `legacy_drift_audit` only.
