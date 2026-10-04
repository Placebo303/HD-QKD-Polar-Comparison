# V69 Three-Layer Representation Feasibility Report (PLAN_CANDIDATE / DECODER_FREE)

**Lifecycle**: PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED — 1024维符号三层有序 w∈[2,5] 重划分，枚举 3^10=59049→37170 去重统计，按升序唯一词典序 max_util→disclosure→ΔNLL→lex 选 P*，Phase A CAL-only 真实4-fold CV Phase B VAL确认 per-layer VAL-CAL≤0.5 + unseen≤1% + chain 1e-9 + m<1024，V67三Session Stage2复用，per-session 5分流 + 总体5态 + common三 session 同 assignment 审计，不跑decoder不构矩阵不启V70

**HEAD (plan/implementation/result)**: d6f590ac6f30deaa8b0bf6cf5c419593fc037720  **Data SHA**: 84d62779 (d1024 bw200 nearest legacy_v1) — plan SHA = implementation SHA = result SHA (HEAD==origin/formal-ir-mainline, no separate result commit; fcf3e457 predecessor retired)
**Method frozen**: n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U natural 5+5 参照 + U three-layer bits_P(P) 37170种仅重标记 w∈[2,5] Σw=10 有序非空 per frame 256 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 poly37 disabled full-tag canonical leak Σw_i·m_i+64  V70_not_started — **真实CAL 4-fold CV重做，删合成CE/硬编码dCE**

## Enumerate 3^10→37170 去重统计

- raw 3^10=59049 个 B→{1,2,3} 分配由 itertools.product([1,2,3],repeat=10) 升序生成
- 过滤 2≤w_i≤5 且 Σw_i=10 且 S_i≠∅ 得 valid 37170
- 12种 w pattern 各计数:

| pattern (w1,w2,w3) | count |
|---|---|
| (2,3,5) | 2520 |
| (2,4,4) | 3150 |
| (2,5,3) | 2520 |
| (3,2,5) | 2520 |
| (3,3,4) | 4200 |
| (3,4,3) | 4200 |
| (3,5,2) | 2520 |
| (4,2,4) | 3150 |
| (4,3,3) | 4200 |
| (4,4,2) | 3150 |
| (5,2,3) | 2520 |
| (5,3,2) | 2520 |
| total | 37170 |

- dedup_stats {raw 59049, valid 37170, per_pattern 12, empty_filtered 21879, width_filtered 21879} 已落盘 v69_manifest.json:enum
- P_lex = tuple(assign[0..9]) 字典序保证唯一，T(P)=(max_util, raw, max_ΔNLL, P_lex) 升序选 P* — **真实CAL 4-fold CV均值CE_cv**

## Per-session CAL-only P* (T from 真实CAL 4-fold m_cv, Ps_trains预计算)

| session | source | P*_per_session(CAL) | w1/w2/w3 | CAL m1_cv/m2_cv/m3_cv | max_util_cv | raw_cv | max_ΔNLL_cv | VAL m1/m2/m3 raw | VAL max_util | chain | dCE1/dCE2/dCE3 | VAL ΔNLL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 1M | (3,3,3,2,1,1,2,1,1,1) | 5/2/3 | 1034/837/885 | 1.010 | 9563 | 0.0163 | 1025/843/905 9590 | 1.001 | 0.0 | 0.037/0.008/0.044 | 0.015 |
| 20260107_PPLN_1p5M | 1p5M | (2,2,3,2,3,1,1,1,1,1) | 5/3/2 | 1077/943/902 | 1.052 | 10082 | 0.0157 | 1070/950/927 10118 | 1.045 | 0.0 | 0.028/0.015/0.037 | 0.024 |
| 20260123_2M_1p2M_0dB | 2M | (2,2,3,2,1,1,1,3,1,1) | 5/3/2 | 1187/1059/1026 | 1.159 | 11228 | 0.0115 | 1178/1063/1047 11237 | 1.150 | 0.0 | 0.034/0.008/0.031 | 0.005 |

*完整 37170 行排序见 v69_table.csv/json (condensed Top-50 per session + P*, 151行), T排序 max_util→disclosure→max_ΔNLL→lex 唯一，Phase A 真实4-fold*

- Phase A CAL-only 真实4-fold: P* 来自 CAL 4-fold 均值 CE_cv→m_cv, used_val_in_selection==False && used_test==False, Ps_trains预计算 per fold
- Phase B VAL确认: P* 在 VAL256 上真实 CE1/CE2/CE3/CE_full 已计, chain |CE_full-ΣCE_i|<1e-9 已验, m_raw ceil 不 cap, raw=Σw_i·m_i+64, per-layer dCE=|VAL-CE_cv|真实

## Common审计

- P*_common(CAL) = (2,2,3,2,1,1,1,3,1,1)  T_common = (1.159,11228,0.0179, P_lex) — max_sess aggregation (max_max_util, max_raw, max_ΔNLL, P_lex)
- common per session VAL真实:
  - 1M: m1 1025 m2 894 m3 858 raw 9587 dCE 0.038/0.018/0.034 max_dCE 0.038 PARTIAL_FEASIBLE (m2<1024)
  - 1p5M: m1 1070 m2 948 m3 928 raw 10114 dCE 0.029/0.014/0.039 max_dCE 0.039 PARTIAL_FEASIBLE
  - 2M: m1 1178 m2 1063 m3 1047 raw 11237 dCE 0.034/0.008/0.031 STILL_HEAVY (m1,m2,m3 ≥1024? m1 1178≥1024)
- common_feasible_count = 0/3, per_session_feasible_count = 0/3, partial_count = 2
- overall = V69_OVERALL_THREE_LAYER_PER_SESSION_ONLY (存在 PARTIAL 但 common 不 feasible, 无 EVIDENCE/MODEL)
- cal_val_consistency: 1M False, 1p5M False, 2M True — VAL最优P*_val均为common (2,2,3,2,1,1,1,3,1,1)，仅2M与CAL P*一致，以CAL为准

## Per-session 5分流 + 总体5态

- 1M: V69_PARTIAL_FEASIBLE (∃m_i<1024: m2 843<1024, m3 905<1024, dCE≤0.5, unseen 0%, chain ok) successor rate_adaptive_or_new_representation
- 1p5M: V69_PARTIAL_FEASIBLE successor rate_adaptive_or_new_representation
- 2M: V69_STILL_HEAVY (m1 1178≥1024) successor new_representation
- counts: EVIDENCE 0, MODEL_NOT_STABLE 0, THREE_LAYER_FEASIBLE 0, PARTIAL 2, STILL_HEAVY 1
- overall 5态: THREE_LAYER_COMMON_FEASIBLE 0, PER_SESSION_ONLY 1, STILL_HEAVY 0 → overall PER_SESSION_ONLY
- capacity_warning (m1≥1024/m2≥1024/m3≥1024/disclosure≥10240) 正交旗标已落盘, q_mass/joint/H_cal 仅描述性

## 附: 1024维冻结与decoder-free守卫

- git diff -- src/ ==0 已验, H1/Lane C/H_inc/decoder/full-tag 零改, rg "decode_|construct_|gf_rank|nested" 0 hits, rg -i "met|protograph" 0 hits, rg -i "v70" 0 hits (除 V70_not_started 注释), py_compile PASS, pytest 小测试 PASS, m_raw 未 cap (grep min(1024 0 hits), VAL未参与选优, TEST未读, 37170 去重已枚举, T max_util→disclosure→ΔNLL→lex 唯一, common同 assignment 已验, per-layer VAL-CAL≤0.5 && unseen≤1% && chain 1e-9 && m<1024 已验, **真实CAL 4-fold/CAL CE_cv/VAL dCE均真实**
- 本轮止于 PLAN_CANDIDATE / DECODER_FREE, 未创建任何 .../v69_*/run_01, 不比较方法, 不转 qualification, V70_not_started — **重做完成，真实CAL制品已重生**

## Files

- v69_data_registry.json (复用 V67 Stage2 3 sessions total 3 per_category 1,1,1 zero_overlap_verified)
- scripts/v69_three_layer_feasibility.py (decoder-free, 真实4-fold 37170枚举, Ps_trains预计算, 删合成CE/硬编码dCE)
- v69_results.json + v69_table.csv/json (condensed Top-50 per session + P* 行对等, 151行, 真实dCE)
- v69_manifest.json guards R69-01..10 true, dedup_stats 12-pattern
- test_v69_three_layer_small.py

等待 PLAN_ACCEPT + EXECUTE_AUTH 方可进入后续三层码设计/decoder, V70保持 NOT_STARTED
