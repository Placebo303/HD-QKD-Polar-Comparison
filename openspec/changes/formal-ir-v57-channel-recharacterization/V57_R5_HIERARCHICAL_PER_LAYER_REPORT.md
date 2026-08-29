# V57 Channel Recharacterization Report — RESULT_ACCEPTED_FAIL / PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN — R5 hierarchical per-layer

HEAD e81a88f23f76dd313f0ab7390495389f39f9bdcd origin e81a88f23f76dd313f0ab7390495389f39f9bdcd data_sha 84d62779 lifecycle V57_CHANNEL_RECHARACTERIZATION_RESULT_ACCEPTED_FAIL / PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN
Cal 512+512 per source (131072 pairs/split) via available[0:512]/[512:1024] four-fold zero overlap, hierarchical λ·P_global grid [0.1, 1.0, 10.0] Cal内4-fold择优 Val单次评估, per-layer m1=min1024 ceil(1.3*1024*H1/5) m2=min1024 ceil(1.3*1024*H2/5) total 0..2048 FULL_DISCLOSURE not INVALID, Fano校验
Zero overlap all=True proofs={'cal_cap_val': True, 'cal_val_cap_v55': True, 'cap_v56': True, 'cap_undersampled': True, 'size512': True, 'in_range': True} counts_valid_all=True chain_ok_all=True fano_ok_all=True negative_control_archived=False
Overall verdict: **V57_CHANNEL_RECHARACTERIZATION_RESULT_ACCEPTED_FAIL** / PREDICTIVE_MODEL_NOT_STABLE (EG2 three-source fail + lambda upper bound indicates model not stable)

Boundary: V55 90 permanently banned; V25 m2 184/190/192 deprecated; only EG1-3 all-pass allows V58; Cal/Val same acquisition as diagnosis, fresh within-session only; MAP/q_mass descriptive only; per-layer ceil 0..2048 FULL_DISCLOSURE not INVALID, Fano; 8192 MLE retained as negative control; no FER/threshold/SKR claim. DECODE_FORBIDDEN.

## Hierarchical smoothing
P(a|b)=(C_ab+λ P_global(a))/(N_b+λ) λ grid [0.1, 1.0, 10.0] Cal 4×128 4-fold择优 Val单次评估, per-layer m1=min1024 ceil(1.3*1024*H1/5) m2=min1024 ceil(1.3*1024*H2/5), Fano H≤h(Pe)+Pe log2(1023)

## Estimator Gates (R5 hierarchical per-layer)
- EG1 NLL finite & improved: NLL_hier<15 && <MLE-5 && <V25
- EG2 CV consistency: |NLL_val - NLL_cal|≤0.5 && rel≤25% && |fold1-fold2|≤0.5
- EG3 Entropy stability & convergence: |H_val-H_cal|≤0.20 && rel≤25% plus 32→512 series
- Fano: H_hier ≤h(Pe)+Pe log2(1023) per source
- Per-layer: m1=min1024 raw_m1, m2=min1024 raw_m2 total 0..2048 FULL_DISCLOSURE_LAYER if raw>1024 not INVALID
- Descriptive only: q_mass_mle, zero_frac, acc_hier (no 60% hard gate, no q≤20% hard gate)

| src | F | H_hier | H1 | H2 | H_mle | bestλ | raw_m1 | raw_m2 | m1 | m2 | total | FULL | f_eff | leak | Δm | NLL_hier | NLL_mle_clamp | NLL_V25 | acc_hier_desc | q_mass | zero_frac | H_val_hier | FanoOk | EG1 | EG2 | EG3 | PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 2130 | 5.275049 | 3.682639 | 1.59241 | 4.548541 | 10.0 | 981 | 424 | 981 | 424 | 1405 | False | 1.312377 | 7089 | 1205 | 8.226968 | 27.147756 | 28.545622 | 0.415375 | 0.526352 | 0.929956 | 5.275153 | True | True | False | True | False |
| 1p5M | 5125 | 5.539611 | 3.845981 | 1.693631 | 4.837508 | 10.0 | 1024 | 451 | 1024 | 451 | 1475 | False | 1.3114 | 7439 | 1269 | 8.758544 | 28.971876 | 30.650154 | 0.374054 | 0.562088 | 0.925069 | 5.541033 | True | True | False | True | False |
| 2M | 5513 | 6.152108 | 4.216095 | 1.936013 | 5.50594 | 10.0 | 1123 | 516 | 1024 | 516 | 1540 | True | 1.232428 | 7764 | 1332 | 9.99596 | 33.335836 | 35.383771 | 0.278595 | 0.648491 | 0.913233 | 6.129651 | True | True | False | True | False |

### Convergence series (Cal subset → Val NLL_hier, H_hier) Val单次评估
- 1M bestλ 10.0 CV {'0.1': {'fold_nlls': [11.481644, 11.596018, 11.532524, 11.523065], 'avg_nll': 11.533313}, '1.0': {'fold_nlls': [9.71844, 9.810199, 9.760801, 9.752035], 'avg_nll': 9.760369}, '10.0': {'fold_nlls': [8.070337, 8.139429, 8.104156, 8.095961], 'avg_nll': 8.102471}}: 32→ NLL 7.533866 H 7.356783 zero 0.994516; 128→ 7.648041 H 5.719237; 256→ 7.928136 H 5.334311; 512→ 8.226968 H 5.275049 FanoCal 6.824447 Pe 0.584602
- 1p5M bestλ 10.0 CV {'0.1': {'fold_nlls': [12.368545, 12.332701, 12.310582, 12.245653], 'avg_nll': 12.31437}, '1.0': {'fold_nlls': [10.459549, 10.429895, 10.412736, 10.360073], 'avg_nll': 10.415563}, '10.0': {'fold_nlls': [8.665538, 8.642134, 8.629873, 8.589473], 'avg_nll': 8.631755}}: 32→ NLL 8.021825 H 7.413767 zero 0.994164; 128→ 8.125176 H 5.896587; 256→ 8.436858 H 5.55481; 512→ 8.758544 H 5.539611 FanoCal 7.210547 Pe 0.625755
- 2M bestλ 10.0 CV {'0.1': {'fold_nlls': [14.166953, 14.146429, 14.145486, 14.218184], 'avg_nll': 14.169263}, '1.0': {'fold_nlls': [11.964648, 11.94798, 11.948353, 12.005149], 'avg_nll': 11.966532}, '10.0': {'fold_nlls': [9.877136, 9.864347, 9.866013, 9.907024], 'avg_nll': 9.87863}}: 32→ NLL inf H 7.530007 zero 0.993444; 128→ 9.218066 H 6.241595; 256→ 9.614035 H 6.031617; 512→ 9.99596 H 6.152108 FanoCal 8.098825 Pe 0.725151

### Negative Control (8192 MLE, retained)
Previous 8192 MLE: H 2.27/2.40/2.64 vs NLL 30.15/32.84/37.52, q_mass 59/64/74%, zero 99.4%, acc 36/29/19% (clamp 1e-15虚高). Retained as v57_channel_recharacterization_undersampled_mle_negative_control.json/md with UNDERSAMPLED_MLE_NEGATIVE_CONTROL. New 131k hierarchical λ·P_global per-layer eliminates clamp虚高, H_hier ~4-6 vs 9.8 Laplace, NLL converges toward H, Fano校验通过.

### Boundary m1=1024 m2<1024 case
Per spec: raw_m1=ceil(1.3*1024*H1/5) capped 1024, raw_m2 likewise, total 1291 with m1=1024 m2=267 is legal (>1024 but ≤2048) and does NOT trigger EVIDENCE_INVALID, only FULL_DISCLOSURE_LAYER flag and true f_eff recalc; dual gate m1≤1024&&m2≤1024 is correct bound.

**FAIL / PREDICTIVE_MODEL_NOT_STABLE — EG2 three-source fail (+ lambda upper bound 10) indicates predictive model not stable; not EVIDENCE_INVALID, not allowed decoder TEST; do not expand lambda grid, V58 still PENDING DECODE_FORBIDDEN.**

V25 deprecated m2 184/190/192 and m1=16 not reused; new m per-layer only for V58 planning, not instantiated in V57; hierarchical lambda grid 0.1,1,10 Cal内4-fold择优 Val单次, per-layer ceil total 0..2048 FULL_DISCLOSURE; DECODE_FORBIDDEN.

---
R5 solidified: head==origin==implementation SHA e81a88f23f76dd313f0ab7390495389f39f9bdcd, hierarchical λ·P_global Cal内4-fold择优 Val单次, EG1 true EG2 false EG3 true, Fano/zero-overlap valid, 2M FULL_DISCLOSURE, V58 BLOCKED. Science: new session非不可编码但当前1024态 hierarchical不稳定, 1p5M接近完整公开U1 (raw 1024 capped), 2M需完整公开U1 (raw 1123→1024), 需先算密钥余量再V58.
