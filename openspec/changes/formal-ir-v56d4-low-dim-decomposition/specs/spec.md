# Delta Spec: formal-ir-v56d4-low-dim-decomposition

## ADDED Requirements

### Requirement: V56D4 32-State Low-Dimensional Mutual Information Decomposition
The diagnostic SHALL compute per-source 32-state mutual information `I(U1A;U1B)` and `I(U2A;U2B)` and cross terms `I(U1A;U2B)/I(U2A;U1B)` from `pairs.parquet` via `U1=sym>>5 (0..31), U2=sym&31 (0..31)` (`F03 5+5`, `32×32` joint counts, `numpy log2`, `5 bits` entropy ceiling), and report the contrast with the same-caliber `V13` reference (`workspace/v13r3fresh_20260816/pairs.parquet`). The 32-state estimate at `N=1024` over `1024` bins SHALL be recognized as far less biased than the 1024-state `1M`-bin plug-in and SHALL be used as the primary MI health check.

### Requirement: V56D4 Fixed Train/Val Cross-Entropy and Accuracy Shunt (No 1024 Plug-In MI)
The diagnostic SHALL shunt on **fixed `fit/val` cross-entropy and accuracy**, not on 1024-state plug-in `I`. With pre-registered `fit=[7,8,9,10] val=[15,16,17,18]` (`assert fit∩val==∅`, same-frame evaluation forbidden), it SHALL learn `P_fit(U1A|U1B)` and `P_fit(U2A|U2B)` (`32×32` column-normalized) on `fit` and report `CE_U1_val = E_val[-log2 P_fit]`, `acc_U1_val = mean_val(U1A==argmax P_fit)`, and likewise `CE_U2/acc_U2` on `val`. Full-data CE is for stability reference only. The diagnostic SHALL explicitly state that it does not shunt on `1024` plug-in `I≈8.4` (severely positively biased at `N=1024`).

### Requirement: V56D4 Stage-Wise V13 vs New-Session Pipeline Check
The diagnostic SHALL check `raw coincidence → pairing (policy/direction/threshold, Δt) → per-frame occupancy → frame anchor (peak_center vs global min, floor_div, period 204800, before/after pair index) → U1/U2 consistency` stage by stage, comparing the `V13` reference with each new session (1M/1p5M/2M), computing `I_32/CE/acc/occupancy/Δt` at each truncation and reporting `first_drop_stage` where `V13`-healthy metrics first collapse in the new session.

### Requirement: V56D4 V13-Known-Contract Two-Way Replay (No Grid Search)
The diagnostic SHALL replay **exactly the `V13` known contract** (`pairing policy/direction/threshold/frame-start` read live from `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` + `build_manifest.json`, not hard-coded) against the current intake contract (`200ps legacy_v1 nearest 1024` from `v55_intake_20260828/sidecars`), and report **only the two-way comparison** `V13-contract` vs `current-contract` on `val` (`I_32/CE/acc/NLL_32/q_mass_32` and `pipeline first_drop` disappearance). **No grid search** over `threshold/policy/direction/frame-start` SHALL be performed (candidate count `2`); no `val`-based picking.

### Requirement: V56D4 Two-Way Shunt (Pairing/Frame-Anchor vs True Domain Shift)
The diagnostic SHALL shunt to exactly one of:
- `PAIRING_OR_FRAME_ANCHOR_ERROR` — iff the `V13`-contract **recovers** low-dimensional association and `NLL` on `val` (e.g., `I_32` to `>70%` of `V13`, `CE` `3-4→1-2 bits`, `acc>60%`, `q_mass` `57-72%→<10%`, and `first_drop` disappears with contract switch), indicating the current intake contract is wrong and repairable;
- `TRUE_ACQUISITION_DOMAIN_SHIFT` — iff the `V13`-contract and current-contract are **jointly still low** on `val` (both `I_32<1.5 bits`, `CE>3 bits`, `acc<50%`, delta `<10%` or `I_32` delta `<0.5 bits`, and pipeline remains low across stages), indicating not a contract error but a true acquisition-domain shift (only then plan new `TRAIN-only` prior/leakage `m_total=floor((1.3*1024*H-64)/5)`).
Otherwise `INCONCLUSIVE_NEED_DEEPER_EVIDENCE` (mixed per-source allowed). The `V25` prior (`channel_counts.npz`) SHALL remain `TRAIN-only` and not be re-estimated from new TEST for training; no LDPC falsification claim.

### Requirement: V56D4 Decoder-Free Guard
The diagnostic SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ8/decoder/m2/leak/prior`, no `.../v56d4_*/run_01` creation, no rerun on the original `90`, `py_compile` PASS, `fit ∩ val == ∅` verified, and `1024` plug-in `MI` explicitly not used for shunt, with no grid search.

## MODIFIED Requirements

### Requirement: V56D3 Terminal Downgrade
`v56d3_symbol_decomposition.json`'s `overall` / `overall_shunt` and `shunt_per_source` SHALL be amended from `PAIRING_OR_FRAME_ANCHOR_ERROR` to `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT`, with `overall_shunt_original_superseded` preserved and `revision=V56D3R1_20260829_downgrade_bias_correction` recording the reason (1024-state `N=1024` plug-in `MI` severely positively biased and `MAP val < identity` shows no generalization; `V13` contract replay needs low-dim verification).

## REMOVED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` guards remain.
