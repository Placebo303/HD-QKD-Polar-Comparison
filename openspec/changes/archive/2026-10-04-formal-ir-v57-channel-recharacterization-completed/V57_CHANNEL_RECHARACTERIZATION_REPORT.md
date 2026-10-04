# V57 Channel Recharacterization Report — PENDING_REVISED / DECODE_FORBIDDEN — Laplace per-layer

HEAD 777338e5a5e347d9e6ab3ed6258b594c3606bbf4 origin 777338e5a5e347d9e6ab3ed6258b594c3606bbf4 data_sha 84d62779 lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN
Cal 512+512 per source (131072 pairs/split) via available[0:512]/[512:1024] four-fold zero overlap, Laplace α=1.0 P=(C+1)/(N_b+1024), per-layer m_i=min(1024,ceil(1.3*1024*H_i/5)) total 0..2048 dual gate FULL_DISCLOSURE
Zero overlap all=True proofs={'cal_cap_val': True, 'cal_val_cap_v55': True, 'cap_v56': True, 'cap_undersampled': True, 'size512': True, 'in_range': True} counts_valid_all=True chain_ok_all=True negative_control_archived=False
Overall verdict: **V57_CHANNEL_RECHARACTERIZATION_FAIL** / PREDICTIVE_MODEL_NOT_STABLE (EG2 three-source fail + lambda upper bound indicates model not stable)

Boundary: V55 90 permanently banned; V25 m2 184/190/192 deprecated; only EG1-3 all-pass allows V58; Cal/Val same acquisition as diagnosis, fresh within-session only; MAP/q_mass descriptive only; per-layer ceil+tag dual gate total 0..2048 FULL_DISCLOSURE; 8192 MLE retained as negative control; no FER/threshold/SKR claim. DECODE_FORBIDDEN.

## Laplace smoothing per-layer
P(a|b)=(C_ab+1.0)/(N_b+1.0*Q) Q=1024 alpha=1.0 frozen, per-layer m1=min(1024,ceil(f N H1/5)) m2=min(1024,ceil(f N H2/5)) total 0..2048, FULL_DISCLOSURE if ceil>1024

## Estimator Gates (REVISED2 per-layer)
- EG1 NLL finite & improved: NLL_smooth<15 && <MLE-5 && <V25
- EG2 CV consistency: |NLL_val - NLL_cal|≤0.5 && rel≤25% && |fold1-fold2|≤0.50
- EG3 Entropy stability & convergence: |H_val-H_cal|≤0.20 && rel≤25% plus 32→512 series
- Dual gate: m1≤1024 && m2≤1024 total ≤2048, FULL_DISCLOSURE not INVALID
- Descriptive only: q_mass_mle, zero_frac, acc_smooth (no 60% hard gate, no q≤20% hard gate)

| src | F | H_smooth | H1 | H2 | H_mle | m_total | m1 | m2 | FULL | f_eff | leak | Δm | NLL_smooth | NLL_mle_clamp | NLL_V25 | acc | q_mass | zero_frac | H_val | EG1 | EG2 | EG3 | PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 2130 | 9.762926 | 4.960033 | 4.802893 | 4.548541 | 2048 | 1024 | 1024 | True | 1.030685 | 10304 | 1848 | 7.712168 | 27.147756 | 28.545622 | 0.415375 | 0.526352 | 0.929956 | 9.762582 | True | False | True | False |
| 1p5M | 5125 | 9.785474 | 4.96578 | 4.819694 | 4.837508 | 2048 | 1024 | 1024 | True | 1.02831 | 10304 | 1842 | 7.998174 | 28.971876 | 30.650154 | 0.374054 | 0.562088 | 0.925069 | 9.785109 | True | False | True | False |
| 2M | 5513 | 9.839356 | 4.979154 | 4.860202 | 5.50594 | 2048 | 1024 | 1024 | True | 1.022679 | 10304 | 1840 | 8.64987 | 33.335836 | 35.383771 | 0.278595 | 0.648491 | 0.913233 | 9.837494 | True | False | True | False |

### Convergence series (Cal subset → Val NLL_smooth, H_smooth) Val single eval
- 1M: 32→ NLL 9.18239 H 9.991649 zero 0.994516; 128→ 8.448336 H 9.954001; 256→ 8.07177 H 9.893724; 512→ 7.712168 H 9.762926
- 1p5M: 32→ NLL 9.323163 H 9.992181 zero 0.994164; 128→ 8.662116 H 9.958589; 256→ 8.321779 H 9.903773; 512→ 7.998174 H 9.785474
- 2M: 32→ NLL 9.591593 H 9.993464 zero 0.993444; 128→ 9.12175 H 9.967453; 256→ 8.877416 H 9.926355; 512→ 8.64987 H 9.839356

### Negative Control (8192 MLE, retained)
Previous 8192 MLE: H 2.27/2.40/2.64 vs NLL 30.15/32.84/37.52, q_mass 59/64/74%, zero 99.4%, acc 36/29/19% (clamp 1e-15虚高). Retained as v57_channel_recharacterization_undersampled_mle_negative_control.json/md with UNDERSAMPLED_MLE_NEGATIVE_CONTROL. New 131k Laplace per-layer eliminates clamp虚高, dual gate total ≤2048, m1=1024 boundary legal.

### Boundary m1=1024 m2<1024 case
Per spec: m1=min(1024,ceil(f N H1/5)) and m2 likewise, total m1+m2 ≤2048; m1=1024 with m2<1024 is legal (total >1024 but ≤2048) and does NOT trigger EVIDENCE_INVALID, only FULL_DISCLOSURE_LAYER flag and true f_eff recalc; dual gate m1≤1024&&m2≤1024 is the correct bound (not m_total≤1024).

**FAIL / PREDICTIVE_MODEL_NOT_STABLE — EG2 three-source fail (+ historical lambda upper bound 10) indicates predictive model not stable; not EVIDENCE_INVALID, not allowed decoder TEST; do not expand lambda grid, V58 still PENDING DECODE_FORBIDDEN.**

V25 deprecated m2 184/190/192 and m1=16 not reused; new m per-layer only for V58 planning, not instantiated in V57; Laplace alpha=1.0 fixed Cal only, per-layer ceil total 0..2048 dual gate FULL_DISCLOSURE; DECODE_FORBIDDEN.