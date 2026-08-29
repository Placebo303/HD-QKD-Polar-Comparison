# V57 Channel Recharacterization Report — PENDING_REVISED / DECODE_FORBIDDEN — hierarchical

HEAD b7b559eb775c89ba097681db9f1eb176c223168c origin b7b559eb775c89ba097681db9f1eb176c223168c data_sha 84d62779 lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN
Cal 512+512 per source (131072 pairs/split) via available[0:512]/[512:1024] four-fold zero overlap, hierarchical λ·P_global grid [0.1, 1.0, 10.0] Cal内4-fold择优 Val单次评估, Fano校验, ceil 0≤m≤1024 tag counted
Zero overlap all=True proofs={'cal_cap_val': True, 'cal_val_cap_v55': True, 'cap_v56': True, 'cap_undersampled': True, 'size512': True, 'in_range': True} counts_valid_all=False chain_ok_all=False fano_ok_all=True negative_control_archived=False
Overall verdict: **V57_EVIDENCE_INVALID**

Boundary: V55 90 permanently banned; V25 m2 184/190/192 deprecated; only EG1-3 all-pass allows V58; Cal/Val same acquisition as diagnosis, fresh within-session only; MAP/q_mass descriptive only; ceil+tag+Fano; 8192 MLE retained as negative control; no FER/threshold/SKR claim. DECODE_FORBIDDEN.

## Hierarchical smoothing
P(a|b)=(C_ab+λ P_global(a))/(N_b+λ) λ grid [0.1, 1.0, 10.0] Cal 4×128 4-fold择优 Val单次评估, Fano H≤h(Pe)+Pe log2(1023)

## Estimator Gates (revised hierarchical)
- EG1 NLL finite & improved: NLL_hier<15 && <MLE-5 && <V25
- EG2 CV consistency: |NLL_val - NLL_cal|≤0.5 && rel≤25% && |fold1-fold2|≤0.5
- EG3 Entropy stability & convergence: |H_val-H_cal|≤0.20 && rel≤25% plus 32→512 series
- Fano: H_hier ≤ h(Pe)+Pe log2(1023) per source
- Descriptive only: q_mass_mle, zero_frac, acc_hier (no 60% hard gate, no q≤20% hard gate)

| src | F | H_hier | H1 | H2 | H_mle | bestλ | m_ceil | m1_ceil | m2 | f_eff | leak | Δm | NLL_hier | NLL_mle_clamp | NLL_V25 | acc_hier_desc | q_mass | zero_frac | H_val_hier | FanoOk | EG1 | EG2 | EG3 | PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 2130 | 5.275049 | 3.682639 | 1.59241 | 4.548541 | 10.0 | 1392 | 972 | 420 | 1.300343 | 7024 | 1192 | 8.226968 | 27.147756 | 28.545622 | 0.415375 | 0.526352 | 0.929956 | 5.275153 | True | True | False | True | False |
| 1p5M | 5125 | 5.539611 | 3.845981 | 1.693631 | 4.837508 | 10.0 | 1463 | 1016 | 447 | 1.300823 | 7379 | 1257 | 8.758544 | 28.971876 | 30.650154 | 0.374054 | 0.562088 | 0.925069 | 5.541033 | True | True | False | True | False |
| 2M | 5513 | 6.152108 | 4.216095 | 1.936013 | 5.50594 | 10.0 | 1626 | 1115 | 511 | 1.300685 | 8194 | 1418 | 9.99596 | 33.335836 | 35.383771 | 0.278595 | 0.648491 | 0.913233 | 6.129651 | True | True | False | True | False |

### Convergence series (Cal subset → Val NLL_hier, H_hier) Val单次评估
- 1M bestλ 10.0 CV {'0.1': {'fold_nlls': [11.481644, 11.596018, 11.532524, 11.523065], 'avg_nll': 11.533313}, '1.0': {'fold_nlls': [9.71844, 9.810199, 9.760801, 9.752035], 'avg_nll': 9.760369}, '10.0': {'fold_nlls': [8.070337, 8.139429, 8.104156, 8.095961], 'avg_nll': 8.102471}}: 32→ NLL 7.533866 H 7.356783 zero 0.994516; 128→ 7.648041 H 5.719237; 256→ 7.928136 H 5.334311; 512→ 8.226968 H 5.275049 FanoCal 6.824447 Pe 0.584602
- 1p5M bestλ 10.0 CV {'0.1': {'fold_nlls': [12.368545, 12.332701, 12.310582, 12.245653], 'avg_nll': 12.31437}, '1.0': {'fold_nlls': [10.459549, 10.429895, 10.412736, 10.360073], 'avg_nll': 10.415563}, '10.0': {'fold_nlls': [8.665538, 8.642134, 8.629873, 8.589473], 'avg_nll': 8.631755}}: 32→ NLL 8.021825 H 7.413767 zero 0.994164; 128→ 8.125176 H 5.896587; 256→ 8.436858 H 5.55481; 512→ 8.758544 H 5.539611 FanoCal 7.210547 Pe 0.625755
- 2M bestλ 10.0 CV {'0.1': {'fold_nlls': [14.166953, 14.146429, 14.145486, 14.218184], 'avg_nll': 14.169263}, '1.0': {'fold_nlls': [11.964648, 11.94798, 11.948353, 12.005149], 'avg_nll': 11.966532}, '10.0': {'fold_nlls': [9.877136, 9.864347, 9.866013, 9.907024], 'avg_nll': 9.87863}}: 32→ NLL inf H 7.530007 zero 0.993444; 128→ 9.218066 H 6.241595; 256→ 9.614035 H 6.031617; 512→ 9.99596 H 6.152108 FanoCal 8.098825 Pe 0.725151

### Negative Control (8192 MLE, retained)
Previous 8192 MLE: H 2.27/2.40/2.64 vs NLL 30.15/32.84/37.52, q_mass 59/64/74%, zero 99.4%, acc 36/29/19% (clamp 1e-15虚高). Retained as v57_channel_recharacterization_undersampled_mle_negative_control.json/md with UNDERSAMPLED_MLE_NEGATIVE_CONTROL. New 131k hierarchical λ·P_global eliminates clamp虚高, H_hier ~4-6 非9.8, NLL converges toward H, Fano校验通过.

**EVIDENCE_INVALID — zero overlap or counts or chain or Fano or m bounds invalid, no estimation, no V58; fix Cal/Val or expand further.**

V25 deprecated m2 184/190/192 and m1=16 not reused; new m_ceil only for V58 planning, not instantiated in V57; lambda grid Cal内4-fold择优 Val单次, ceil 0≤m≤1024 tag Fano; DECODE_FORBIDDEN.