# Spec Delta: formal-ir-v56d2-calibration — V56D2R1 minimal revision

**Change**: `formal-ir-v56d2-calibration` (V56D2R1 calibration, successor of V56D1 `MIXED_BY_SOURCE`)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free, no new decoder execution
**Revision**: `V56D2R1` — `FAIL_NEED_FIX` → `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`; routing 去≥40% 硬门，timing 缺失→`EVIDENCE_INCOMPLETE`，环境锁定 V56D1 同 TimeTagger，复用 V13 实现，固定 8 帧 additive `run_02`
**Predecessor spec**: `formal-ir-v56d1-raw-a2-diagnosis` (decoder-free A2) + `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (authoritative 90-block frozen)

## Delta (additive, no modification to frozen V54 method)

### 1. Explicit materialization contract (additive, R1 environment-locked + V13 reuse)

- Per-source `sidecar_meta.json: used_params` SHALL contain `delay_used_ps (unique -50/+50/-50, not cherry-picked) / peak_center_ps / peak_sigma_ps / corr_argmax / corr_bins / peak_to_bg / peak_status / channels {A:1,B:5} / gate_width_ps 200 / pairing_threshold_ps 40000 / frame_start_ps / frame_anchor / mapping / wrap_rule floor_div / frame_period_ps 204800 / occupancy_filter` plus `provenance {path,sha256,size}` and `ttbin_merge {merge_verified}` plus `environment {interpreter_path, timetagger_version, total_events, acquisition_duration_s}`
- `|peak_center - delay_used|<50ps` AND `sign(peak)==sign(delay)` SHALL hold per source when timing evidence complete (mechanical check); when timing not recomputed SHALL be `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`, SHALL NOT be `FAIL_NEED_FIX`
- Raw recomputation SHALL directly reuse `V13 verified read_ttbin_events + compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max819200/n16384, lag=t_B-t_A)` implementation (SHALL NOT reinvent approximate materialization) decoder-free; SHALL run in `V56D1 successful TimeTagger environment` (record interpreter_path/TimeTagger version/input event count); timing fields SHALL be truly recomputed, missing → `EVIDENCE_INCOMPLETE`

### 2. Zero-overlap calibration frames (additive, R1 fixed 8 frames additive)

- Per source fixed `8 frames [7,8,9,10,15,16,17,18] = 2 blocks×4`, `pairs_per_frame 256`, `frame_id ∈ [0,F-1]`, `gap≥4`
- `set(calibration_frame_ids) ∩ set(v55_authoritative_registry.selected_frame_ids) == ∅` SHALL hold per source and overall (mechanical)
- Outputs `calibration_registry.json` + `calibration_manifest.json` with `overall_zero_overlap_verified: true`; SHALL write additive `run_02` / revision dir, SHALL NOT overwrite `v56d2_calibration.json` (`run_01`)

### 3. Dual-contract verification (additive, decoder-free, R1 corrected)

- `timing_contract_verified = (50≤σ≤150) && (|peak-delay|<50 && sign一致) && (gate200 && threshold40000 && frame_start已落盘) && p2bg_assessed` AND timing fields truly recomputed in `V56D1 same TimeTagger environment`; missing → `CALIBRATION_EVIDENCE_INCOMPLETE / ENVIRONMENT_AND_CONTRACT_NOT_REPRODUCED`, SHALL NOT be `FAIL_NEED_FIX`
- `routing_contract_verified = (specified channels exist and non-zero: count_A>0 && count_B>0 && unique⊇{1,5}) && (pairing without cross-channel/missing-column/erroneous-merge: frac_other<20%)`; SHALL NOT enforce `frac≥40%` per channel hard gate; `frac_A/B` SHALL be reported only (e.g. 1M/2M 36.4% likely from detection efficiency, not proof of routing error)
- `p2bg>1000` SHALL be assessed per-source as `HEALTHY>1000 / PARTIAL 500-1000 / LOW<500` (current 708/629 PARTIAL, 378 LOW); SHALL NOT hard-fail all sources with single shared threshold; report `should_share_threshold_across_acquisitions` and `recommended_per_source_threshold`
- `calibration_pass = timing_contract_verified && routing_contract_verified && A==B_cal>60% && NLL/q_mass 回落 && p2bg_assessed` (per source); overall `PASS` only if all 3 sources pass; if timing incomplete → `CALIBRATION_EVIDENCE_INCOMPLETE`; if timing complete still `NLL 20-30` → true domain issue

### 4. Correlation / NLL regression (additive, decoder-free, R1)

- On calibration fixed `8 frames [7,8,9,10,15,16,17,18]` SHALL report `A==B_rate`, `delta mass_0+mass_±1`, `NLL bits/block` via `channel_counts.npz` P(A|B) (TRAIN, column-norm), `q_mass_on_p_zero`; expect `A==B>60%` (from 27-41%), `NLL 28-35→~0.82*1024`, `q_mass 57-71%→3%`; after correction still require `A==B>60%` and `NLL/q_mass` regression; if timing complete still `NLL 20-30` → true domain issue; else if timing incomplete → `CALIBRATION_EVIDENCE_INCOMPLETE` stay `DIAGNOSIS_PLAN_READY`

### 5. Lifecycle guard (additive, R1)

- SHALL NOT rerun corrected pipeline on original V55 90-block (already unblinded `0/90`); SHALL NOT tune `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior`; SHALL NOT claim FER/SKR/promotion; SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` until successor freezes new TEST blocks; `rg "decode_" 0 hits`; SHALL NOT overwrite `v56d2_calibration.json` (`run_01`), SHALL write additive `run_02` / revision dir; SHALL NOT run decoder; SHALL NOT touch V55 90 blocks; SHALL only modify files under `openspec/changes/formal-ir-v56d2-calibration/` and script gates, then push new SHA
