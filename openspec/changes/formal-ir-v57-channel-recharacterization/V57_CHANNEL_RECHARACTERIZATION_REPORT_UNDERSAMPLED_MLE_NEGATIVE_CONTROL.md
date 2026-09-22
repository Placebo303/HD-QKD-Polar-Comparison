# V57 Channel Recharacterization Report — UNDERSAMPLED_MLE_NEGATIVE_CONTROL (8192)

HEAD ea39a83d844ce60c86418b753cf95576416233f4 origin ea39a83d844ce60c86418b753cf95576416233f4 data_sha 84d62779 lifecycle ESTIMATOR_UNDERSAMPLED / DECODE_FORBIDDEN / UNDERSAMPLED_MLE_NEGATIVE_CONTROL
Cal 19..50 (32 frames, 8192 pairs/source) Val 77..108 (32, 8192) unified three sources
Zero overlap all=True proofs={'cal_cap_val': True, 'cal_val_cap_v55': True, 'cap_v56': True, 'in_range': True} counts_valid_all=True chain_ok_all=True
Overall verdict: **V57_CHANNEL_RECHARACTERIZATION_FAIL (ESTIMATOR_UNDERSAMPLED_MLE_NEGATIVE_CONTROL)**

> **RETAINED NEGATIVE CONTROL** — 本文件为前版 8192 裸MLE 结果的归档，不覆盖。原因：1024×1024=1M cell 上 8192 样本导致 99.35%零、val 59-74%落零cell、NLL 30bits 源于1e-15裁剪非信道失败、H_cal 2.3 vs NLL 30 分裂为稀疏过拟合。修订版 512+512 (131072/split) + Dirichlet Laplace α=1.0 平滑 + ceil + 估计器门禁 为主路径，本文件仅作对照。

Boundary: V55 90 permanently banned (revealed 0/90); V25 m2 184/190/192 deprecated not reused; only all-pass allows V58; Cal/Val same acquisition as diagnosis, fresh within-session confirmation only; no FER/threshold/SKR claim.

| src | F | H_cal | H1 | H2 | m_total | m1 | m2 | f_eff | leak | Δm | Δleak | NLL_val | NLL_V25 | acc_val | acc_cal | q_mass | zero_frac | H_val | V1 | V2 | V3 | V4 | PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 2130 | 2.270263 | 2.062662 | 0.207602 | 591 | 537 | 54 | 1.298634 | 3019 | 391 | 1955 | 30.151053 | 28.666092 | 0.365356 | 0.421021 | 0.594727 | 0.994514 | 2.275877 | False | False | False | True | False |
| 1p5M | 5125 | 2.403452 | 2.201245 | 0.202206 | 627 | 574 | 53 | 1.299807 | 3199 | 421 | 2105 | 32.844171 | 30.970832 | 0.293091 | 0.379028 | 0.648438 | 0.994193 | 2.413038 | False | False | False | True | False |
| 2M | 5513 | 2.639138 | 2.421779 | 0.21736 | 689 | 632 | 57 | 1.298438 | 3509 | 481 | 2405 | 37.521407 | 35.353695 | 0.19812 | 0.29895 | 0.743408 | 0.993552 | 2.653507 | False | False | False | True | False |

Gate V1: NLL_val <= H+0.5 && <=1.5 && < V25-5 ; V2: acc>=60% && >=cal-10pp ; V3: q_mass<=20% ; V4: |H_val-H_cal|<=0.20 && <=25%

**FAIL (ESTIMATOR_UNDERSAMPLED) — 裸MLE零概率+1e-15 clamp导致30bits虚高，非信道难度；修订版以131k+平滑消除，q_mass/MAP仅描述，估计器门禁 EG1-3 为准。**

V25 deprecated m2 184/190/192 and m1=16 not reused; new m_ceil (revised) only for V58 planning, not instantiated in V57; FORBIDDEN. Retained as UNDERSAMPLED_MLE_NEGATIVE_CONTROL, not overwritten.
