# Spec Delta: formal-ir-v56d2-calibration

**Change**: `formal-ir-v56d2-calibration` (V56D2 calibration, successor of V56D1 `MIXED_BY_SOURCE`)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free, no new decoder execution
**Predecessor spec**: `formal-ir-v56d1-raw-a2-diagnosis` (decoder-free A2) + `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (authoritative 90-block frozen)

## Delta (additive, no modification to frozen V54 method)

### 1. Explicit materialization contract (additive)

- Per-source `sidecar_meta.json: used_params` SHALL contain `delay_used_ps (unique -50/+50/-50, not cherry-picked) / peak_center_ps / peak_sigma_ps / corr_argmax / corr_bins / peak_to_bg / peak_status / channels {A:1,B:5} / gate_width_ps 200 / pairing_threshold_ps 40000 / frame_start_ps / frame_anchor / mapping / wrap_rule floor_div / frame_period_ps 204800 / occupancy_filter` plus `provenance {path,sha256,size}` and `ttbin_merge {merge_verified}`
- `|peak_center - delay_used|<50ps` AND `sign(peak)==sign(delay)` SHALL hold per source (mechanical check)
- Raw recomputation SHALL use `read_ttbin_events(main) + compute_cross_correlation_histogram(ch_a=1,ch_b=5,bin100/max819200/n16384, lag=t_B-t_A)` decoder-free

### 2. Zero-overlap calibration frames (additive)

- Per source `8-16 frames = 2-4 blocks×4`, `pairs_per_frame 256`, `frame_id ∈ [0,F-1]`, `gap≥4`
- `set(calibration_frame_ids) ∩ set(v55_authoritative_registry.selected_frame_ids) == ∅` SHALL hold per source and overall (mechanical)
- Outputs `calibration_registry.json` + `calibration_manifest.json` with `overall_zero_overlap_verified: true`

### 3. Dual-contract verification (additive, decoder-free)

- `timing_contract_verified = (50≤σ≤150) && (|peak-delay|<50 && sign一致) && (gate200 && threshold40000 && frame_start已落盘) && p2bg_assessed`
- `routing_contract_verified = (frac_A≥40% && frac_B≥40% && frac_other<20% && unique⊇{1,5})`
- `p2bg>1000` SHALL be assessed per-source as `HEALTHY>1000 / PARTIAL 500-1000 / LOW<500` (current 708/629 PARTIAL, 378 LOW); SHALL NOT hard-fail all sources with single shared threshold; report `should_share_threshold_across_acquisitions` and `recommended_per_source_threshold`
- `calibration_pass = timing_contract_verified && routing_contract_verified && A==B_cal>60% && NLL/q_mass 回落 && p2bg_assessed` (per source); overall `PASS` only if all 3 sources pass

### 4. Correlation / NLL regression (additive, decoder-free)

- On calibration 8-16 frames SHALL report `A==B_rate`, `delta mass_0+mass_±1`, `NLL bits/block` via `channel_counts.npz` P(A|B) (TRAIN, column-norm), `q_mass_on_p_zero`; expect `A==B>60%` (from 27-41%), `NLL 28-35→~0.82*1024`, `q_mass 57-71%→3%`; else `FAIL_NEED_FIX` stay `DIAGNOSIS_PLAN_READY`

### 5. Lifecycle guard (additive)

- SHALL NOT rerun corrected pipeline on original V55 90-block (already unblinded `0/90`); SHALL NOT tune `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior`; SHALL NOT claim FER/SKR/promotion; SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` until successor freezes new TEST blocks; `rg "decode_" 0 hits`
