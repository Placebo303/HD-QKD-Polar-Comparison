# V68 Balanced GF32 Bit-Partition Report (PLAN_CANDIDATE / DECODER_FREE)

**Lifecycle**: PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED — 1024维符号 GF32两层验证冻结仅重划分10 bits，枚举252 CAL-only max→sum→abs→lex 选 S*，Phase A CAL-only Phase B VAL确认，V67三Session Stage2复用，per-session 4分流 + 总体3态 + common审计，不跑decoder不构矩阵。

**HEAD**: fcf3e457ecf45c58e23f91d750acd5267d541795  **Data SHA**: 84d62779 (d1024 bw200 nearest legacy_v1)
**Method frozen**: n1024 q1024 GF32 poly37 H1 16x1024 rank16 80b U=32*U1+U2 F03 5+5 natural，per frame 256，Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 disabled full-tag canonical leak 5*(m1+m2)+64。

## Enumerate 252 + unique lexicographic max→sum→abs→lex

- S_list = combinations(range(10),5) 252行，S_nat=(5,6,7,8,9) index 251。
- 每 S bits_S(s) -> (u1',u2') 如 spec：u1' = Σ ((s>>S[k])&1)<<k, T=sorted(B\S)。natural时 bits_S(s)=s>>5 验证通过。
- 链式 |CE_full-CE1-CE2|<1e-9 每 S 每 session 已验。

## Per-session CAL-only S* (T from CAL 4-fold m_cv)

| session | source | S*_per_session(CAL) | CAL m1_cv/m2_cv | max/sum/abs | VAL m1/m2 raw | VAL max/sum/abs | nat m1/m2 raw | ΔCE1/ΔCE2 | Δmax/Δsum |
|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 1M | (4,5,7,8,9) | 1034/866 1034/1900/168 | 1025/880 9589 1025/1905/145 | 1024/881 9589 | +0.007 / -0.018 ... | +1 / 0 |
| 20260107_PPLN_1p5M | 1p5M | (5,6,7,8,9) nat | 1077/927 1077/2004/150 | 1070/941 10119 1070/2011/129 | 1070/941 10119 | 0 / 0 | 0/0 |
| 20260123_2M_1p2M_0dB | 2M | (4,5,6,8,9) | 1187/1046 1187/2233/141 | 1178/1056 11234 1178/2234/122 | 1178/1057 11239 | +0.001 / -0.001 | 0/ -5 |

*完整 252 行见 v68_table.csv/json，T排序 max→sum→abs→lex 唯一。*

- Phase A CAL-only：S* 来自 CAL 4-fold m_cv (held-out CE)，used_val_in_selection==False && used_test==False。
- Phase B VAL确认：S* 与 S_nat 在 VAL256 (65536 pairs) 上独立 CE1/CE2/CE_full 已计，chain_ok，已验 m_raw ceil 不 cap，raw=5*(m1+m2)+64。

## Common审计

- S*_common(CAL) = (4,5,7,8,9)  T_common = max_sess aggregation (max_max, max_sum, max_abs, S_lex)。
- common per session VAL：
  - 1M: m1 1025 m2 880 raw 9589  STILL_HEAVY
  - 1p5M: m1 1070 m2 940 raw 10114 STILL_HEAVY (common vs per-session diff 0/ -1)
  - 2M: m1 1179 m2 1056 raw 11239 STILL_HEAVY

- common_feasible_count = 0/3，per_session_feasible_count = 0/3。
- overall = V68_OVERALL_STILL_HEAVY (0 feasible；即便均衡重划分亦仍 heavy，需更深表示如 Gray/2+8)。
- cal_val_consistency per session：1M False, 1p5M True, 2M False (VAL argmin S* vs CAL S*)，以 CAL 为准，VAL不重选。

## Per-session 4分流 + 总体3态 (优先级 EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > BALANCED_FEASIBLE > STILL_HEAVY)

- 1M: V68_STILL_HEAVY (m1 1025≥1024) successor new_representation
- 1p5M: V68_STILL_HEAVY (m1 1070≥1024) successor new_representation
- 2M: V68_STILL_HEAVY (m1 1178≥1024) successor new_representation
- counts: EVIDENCE 0, MODEL_NOT_STABLE 0, BALANCED_FEASIBLE 0, STILL_HEAVY 3
- overall 3态：BALANCED_COMMON_FEASIBLE 0, BALANCED_PER_SESSION_ONLY 0, STILL_HEAVY 3 -> overall STILL_HEAVY
- capacity_warning (m1_ge_1024/m2_ge_1024/disclosure_ge_5120) 正交旗标已落盘，q_mass/joint/H_cal 仅描述性，不入稳定性门禁。

## 附：1024维冻结与decoder-free守卫

- git diff -- src/ ==0 已验，H1/Lane C/H_inc/decoder/full-tag 零改，rg "decode_|construct_|gf_rank|nested" 0 hits，rg -i "met|protograph" 0 hits，py_compile PASS，pytest 小测试 PASS，m_raw 未 cap (grep min(1024 0 hits)，VAL未参与选优，TEST未读，252已枚举，T max→sum→abs→lex 唯一。
- 本轮止于 PLAN_CANDIDATE / DECODER_FREE，未创建任何 .../v68_*/run_01，不比较方法，不转 qualification。

## Files

- v68_data_registry.json (复用 V67 Stage2 3 sessions total 3 per_category 1,1,1 zero_overlap_verified)
- scripts/v68_spike.py (decoder-free)
- v68_results.json + v68_table.csv/json (752? 756行 252*3 + header) 行对等
- v68_manifest.json guards R68-01..10 true
- test_v68_spike_small.py

等待 PLAN_ACCEPT + EXECUTE_AUTH 方可进入后续码设计/decoder。
