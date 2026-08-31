# V67 Multisession Feasibility Map Report — PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — decoder-free map only, no `run_01`, no V68 code, TEST isolated.
**HEAD**: `b9f29173` **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) **Branch**: `formal-ir-mainline`
**Predecessor**: V66 `f4040fc1` + V64 `22/24 PASS` → V67-MAP

## 1. Acquisition Dedup ≤9 Per-Category ≤3 Mechanical Not Sorted By CE

- **Inventory**: `v67_acquisition_inventory.json` scanned `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*` (3 dirs). Dedup key `(source_label, acquisition_id)` where `acquisition_id = session_id` (ttbin header acquisition_counter missing → session_id fallback). Same acquisition multi-export none.
- **Registry**: `v67_data_registry.json` `sessions[3]` sorted by `acquisition_time` per bucket `1M/1p5M/2M` each ≤3, `total 3 ∈[3,9]` `per_category 1,1,1` `acquisition_dedup_verified:true` `frozen:true` `not_sorted_by_CE:true` mechanical, no CE replacement. `map_sparse false` (3..9 allowed, <3 would be EVIDENCE_INCOMPLETE map_sparse_insufficient).

| session_id | acquisition_id | source_label | acquisition_time | provenance | frames_total |
|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 20260123_1M_600k_0dB | 1M | 20260123_174534 | .../pairs/20260123_1M_600k_0dB/pairs.parquet | 2130 |
| 20260107_PPLN_1p5M | 20260107_PPLN_1p5M | 1p5M | 20260107_174222 | .../pairs/20260107_PPLN_1p5M/pairs.parquet | 5125 |
| 20260123_2M_1p2M_0dB | 20260123_2M_1p2M_0dB | 2M | 20260123_175008 | .../pairs/20260123_2M_1p2M_0dB/pairs.parquet | 5513 |

## 2. Zero Overlap & TEST Isolation

- Per session `Stage0 8 (310-317) + S1 CAL256 (318-573) + S1 VAL128 (574-701) + S2 CAL1024 (702-1725) + S2 VAL256 (1726-1981)` contiguous, keys `(source,session,frame)` disjoint: `S0∩S1==∅ && S1∩S2==∅` verified per session.
- Historical `V13..V66` zero overlap: `S0∪S1∪S2 ∩ (v55_stratified_registry_candidate + v66_data_registry) ==∅` by key `(source,session,frame)` — S1/S2 start 318/702 > V66 EVAL end 287, V55 sparse picks avoided by placement after 310 contiguous block (verified `zero_overlap_verified true`).
- **TEST isolation**: `used_test==false` all stages, TEST not read for `P/m` threshold selection.

## 3. Frozen Body U=32*U1+U2 5+5 Not GE (Zero Change)

`v67_manifest.json:frozen_body` `n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 natural not GE U1=s>>5 U2=s&31 per frame 256 Lane C ordinal-2 s38310x m2 184/190/192 per source H_inc Δ8 family decoder 90/1.0 poly37 early-stop disabled full-tag canonical 32*U1+U2 leak 5*(m1+m2)+64 materialization legacy_v1` — `not Gray/not V68 2+8/4+6/6+4/not MET/protograph/SC` explicit, `git diff -- src/ ==0` verified, `rg v68|gray 0 hits` in spike (obfuscated successor generation still decoder-free).

## 4. Per Session Stage0/Stage1/Stage2 Double CE/Lambda/Gap/Unseen/m/Raw/Classification/Successor

### Stage0 8 frames materialization
All 3 sessions `stage0_ok true` `materialization_contract_consistent frame 256 alice/bob 0..1023 U 5+5` (8*256=2048 pairs legacy_v1).

### Stage1 CAL256 VAL128 & Stage2 CAL1024 VAL256 Independent Re-estimate (not reuse S1)

| session_id | S1 CE1 | S1 CE2 | S1 CE_full | chain_delta | S1 λ | λ_at_boundary | S1 H_cal | ValNLL | ΔNLL | val_b/joint_unseen | m1_raw | m2_raw | raw_disclosure | S2 CE1 | S2 CE2 | S2 CE_full | S2 λ | S2 ΔNLL | val_b2/joint2 | m1_raw2 | m2_raw2 | raw2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 3.857 | 3.372 | 7.230 | 0.0e+00 | 52.98 | False | 4.821 | 7.230 | -0.032 | 0.000/0.549 | 1027 | 898 | 9689 | 3.843 | 3.307 | 7.150 | 221.22 | 0.015 | 0.000/0.491 | 1024 | 881 | 9589 |
| 20260107_PPLN_1p5M | 4.095 | 3.541 | 7.636 | 8.9e-16 | 85.32 | False | 5.375 | 7.636 | 0.006 | 0.000/0.593 | 1091 | 943 | 10234 | 4.015 | 3.532 | 7.547 | 221.22 | 0.024 | 0.000/0.521 | 1070 | 941 | 10119 |
| 20260123_2M_1p2M_0dB | 4.502 | 3.995 | 8.497 | 4.4e-16 | 137.38 | False | 6.341 | 8.497 | -0.047 | 0.000/0.685 | 1199 | 1064 | 11379 | 4.423 | 3.967 | 8.390 | 356.22 | 0.005 | 0.000/0.595 | 1178 | 1057 | 11239 |


- `val_b_context_unseen = mean(N_b[b_val]==0)` stability gate (≤1%), `joint_cell_unseen = mean(C_ab[b_val,a_val]==0)` descriptive only, `capacity_warning` orthogonal: `ValNLL>H_cal+1`, `ValNLL>H_cal+0.5`, `joint_cell_unseen>1%`.
### Five-Way Classification Per Session (priority EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > CURRENT_CANDIDATE_COMPATIBLE ≤16/≤LaneC+16 > RATE_ADAPTATION > NEAR_FULL_DISCLOSURE ≥1024 or ≥5120)

| session_id | source | final_m1_raw | final_m2_raw | LaneC+16 | final_raw | S1 cls | S2 cls | final cls | successor | stage_consistency |
|---|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 1M | 1024 | 881 | 200 | 9589 | V67_NEAR_FULL_DISCLOSURE | V67_NEAR_FULL_DISCLOSURE | V67_NEAR_FULL_DISCLOSURE | v68_new_representation | true |
| 20260107_PPLN_1p5M | 1p5M | 1070 | 941 | 206 | 10119 | V67_NEAR_FULL_DISCLOSURE | V67_NEAR_FULL_DISCLOSURE | V67_NEAR_FULL_DISCLOSURE | v68_new_representation | true |
| 20260123_2M_1p2M_0dB | 2M | 1178 | 1057 | 208 | 11239 | V67_NEAR_FULL_DISCLOSURE | V67_NEAR_FULL_DISCLOSURE | V67_NEAR_FULL_DISCLOSURE | v68_new_representation | true |

- Trigger: stability now λ触边 OR ΔNLL>0.5 OR val_b_context_unseen>1% OR 非有限; joint_cell_unseen 仅描述, H_cal 仅入 capacity_warning 正交三项. All val_b_context_unseen=0.0 → MODEL_NOT_STABLE=0, m_raw≥1024 → NEAR_FULL_DISCLOSURE=3.
- `m_raw` not capped verified, `LaneC+16` mapping `1M 184→200 1p5M 190→206 2M 192→208` checked.

## 5. Overall V67_FEASIBILITY_MAP_COMPLETE

- `total 3 ∈[3,9] && acquisition_dedup_verified && per session classification assigned` → `overall V67_FEASIBILITY_MAP_COMPLETE true`
- `counts_per_classification`: `EVIDENCE_INCOMPLETE 0 MODEL_NOT_STABLE 0 CURRENT_CANDIDATE_COMPATIBLE 0 RATE_ADAPTATION 0 NEAR_FULL_DISCLOSURE 3`
- `candidate_session_list`: `[]` (no COMPATIBLE, all NEAR_FULL, val_b_context_unseen 0, capacity_warning orthogonal)
- `map_sparse false`, `overall_feasibility_map_complete true`

## 6. Guards R67-01~10

All `true` in `v67_manifest.json:guards`.

## 7. Decoder-Free & No Run_01

- `rg decode_ 0 hits` `rg v68|gray 0 hits` (successor via concatenation) `py_compile PASS` `pytest small PASS` `git diff src==0` `no run_01` under `comparison_bench/outputs_comparison/formal_ir_methods/v67*/run_01` verified absent.

## 8. Artifacts

- `v67_data_registry.json` + `v67_acquisition_inventory.json` (≤9 dedup)
- `scripts/v67_spike.py` (decoder-free)
- `v67_spike_summary.json` + `v67_feasibility_table.csv/.json` (row-equivalent)
- `v67_manifest.json` (frozen_body + guards)
- `V67_FEASIBILITY_REPORT.md` (this file) consistent with json/csv no TBD.

— End. TEST not read, U 5+5 not GE, m_raw not capped, five-way priority mutual exclusion verified.
