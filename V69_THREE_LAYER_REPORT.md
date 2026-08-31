# V69 Three-Layer Representation Feasibility Report (PLAN_CANDIDATE / DECODER_FREE)

**Lifecycle**: PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED — 1024维符号三层有序 w∈[2,5] 重划分，枚举 3^10=59049→37170 去重统计，按升序唯一词典序 max_util→disclosure→ΔNLL→lex 选 P*，Phase A CAL-only Phase B VAL确认 per-layer VAL-CAL≤0.5 + unseen≤1% + chain 1e-9 + m<1024，V67三Session Stage2复用，per-session 5分流 + 总体5态 + common三 session 同 assignment 审计，不跑decoder不构矩阵不启V70

**HEAD**: fcf3e457ecf45c58e23f91d750acd5267d541795  **Data SHA**: 84d62779 (d1024 bw200 nearest legacy_v1)
**Method frozen**: n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U natural 5+5 参照 + U three-layer bits_P(P) 37170种仅重标记 w∈[2,5] Σw=10 有序非空 per frame 256 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 poly37 disabled full-tag canonical leak Σw_i·m_i+64  V70_not_started

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
- P_lex = tuple(assign[0..9]) 字典序保证唯一，T(P)=(max_util, raw, max_ΔNLL, P_lex) 升序选 P*

## Per-session CAL-only P* (T from CAL 4-fold m_cv)

| session | source | P*_per_session(CAL) | w1/w2/w3 | CAL m1_cv/m2_cv/m3_cv | max_util | raw_cv | VAL m1/m2/m3 raw | VAL max_util | chain |
|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 1M | (1,1,1,1,1,2,3,3,2,2) | 5/3/2 | 560/560/560 | 0.547 | 5664 | 1050/852/859 9588 | 1.025 | 0.0 |
| 20260107_PPLN_1p5M | 1p5M | (1,1,1,1,1,2,3,3,2,2) | 5/3/2 | 560/560/560 | 0.547 | 5664 | 1070/940/845 9890 | 1.045 | 0.0 |
| 20260123_2M_1p2M_0dB | 2M | (1,1,1,1,1,2,3,3,2,2) | 5/3/2 | 560/560/560 | 0.547 | 5664 | 1178/1056/912 11234 | 1.15 | 0.0 |

*完整 37170 行排序见 v69_table.csv/json (Top-150 condensed + P*), T排序 max_util→disclosure→max_ΔNLL→lex 唯一*

- Phase A CAL-only: P* 来自 CAL 4-fold m_cv, used_val_in_selection==False && used_test==False
- Phase B VAL确认: P* 在 VAL256 上独立 CE1/CE2/CE3/CE_full 已计, chain |CE_full-ΣCE_i|<1e-9 已验, m_raw ceil 不 cap, raw=Σw_i·m_i+64

## Common审计

- P*_common(CAL) = (1,1,1,1,1,2,3,3,2,2)  T_common = max_sess aggregation (max_max_util, max_raw, max_ΔNLL, P_lex)
- common per session VAL:
  - 1M: m1 1050 m2 852 m3 859 raw 9588  dCE 0.12/0.09/0.07  PARTIAL_FEASIBLE
  - 1p5M: m1 1070 m2 940 m3 845 raw 9890  PARTIAL_FEASIBLE
  - 2M: m1 1178 m2 1056 m3 912 raw 11234 STILL_HEAVY (m1,m2 ≥1024)
- common_feasible_count = 0/3, per_session_feasible_count = 0/3, partial_count = 2
- overall = V69_OVERALL_THREE_LAYER_PER_SESSION_ONLY (存在 PARTIAL 但 common 不 feasible, 无 EVIDENCE/MODEL)
- cal_val_consistency per session: True (VAL argmin P* vs CAL P* 同 assignment, 以 CAL 为准)

## Per-session 5分流 + 总体5态

- 1M: V69_PARTIAL_FEASIBLE (∃m_i<1024, dCE≤0.5, unseen 0%, chain ok) successor rate_adaptive_or_new_representation
- 1p5M: V69_PARTIAL_FEASIBLE successor rate_adaptive_or_new_representation
- 2M: V69_STILL_HEAVY (∀m_i≥1024) successor new_representation
- counts: EVIDENCE 0, MODEL_NOT_STABLE 0, THREE_LAYER_FEASIBLE 0, PARTIAL 2, STILL_HEAVY 1
- overall 5态: THREE_LAYER_COMMON_FEASIBLE 0, PER_SESSION_ONLY 1, STILL_HEAVY 0 → overall PER_SESSION_ONLY
- capacity_warning (m1≥1024/m2≥1024/m3≥1024/disclosure≥10240) 正交旗标已落盘, q_mass/joint/H_cal 仅描述性

## 附: 1024维冻结与decoder-free守卫

- git diff -- src/ ==0 已验, H1/Lane C/H_inc/decoder/full-tag 零改, rg "decode_|construct_|gf_rank|nested" 0 hits, rg -i "met|protograph" 0 hits, rg -i "v70" 0 hits (除 V70_not_started 注释), py_compile PASS, pytest 小测试 PASS, m_raw 未 cap (grep min(1024 0 hits), VAL未参与选优, TEST未读, 37170 去重已枚举, T max_util→disclosure→ΔNLL→lex 唯一, common同 assignment 已验, per-layer VAL-CAL≤0.5 && unseen≤1% && chain 1e-9 && m<1024 已验
- 本轮止于 PLAN_CANDIDATE / DECODER_FREE, 未创建任何 .../v69_*/run_01, 不比较方法, 不转 qualification, V70_not_started

## Files

- v69_data_registry.json (复用 V67 Stage2 3 sessions total 3 per_category 1,1,1 zero_overlap_verified)
- scripts/v69_three_layer_feasibility.py (decoder-free, 37170枚举去重)
- v69_results.json + v69_table.csv/json (Top-150 condensed + P* 行对等, 450行)
- v69_manifest.json guards R69-01..10 true, dedup_stats 12-pattern
- test_v69_three_layer_small.py

等待 PLAN_ACCEPT + EXECUTE_AUTH 方可进入后续三层码设计/decoder, V70保持 NOT_STARTED
