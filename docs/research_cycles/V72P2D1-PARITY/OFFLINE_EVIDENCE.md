# V72P2D1-PARITY 离线补证（decoder-free，CAL-free）

- Cycle: V72P2D1-PARITY. 日期: 2026-09-04.
- 性质: 离线补证，直接引用 coder-fast 已复算事实，不重新跑 decoder、
  不重跑 A/B、不改算法、不覆盖
  `comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/`
  四文件（manifest.json / results.json / table.csv / report.md）、
  不读逐符号密钥数据以外的数据（仅读 VAL1726..1729 四帧 + registry，不读 CAL）。
- 历史原文（`RESULT_SUMMARY.md` / `REVIEW_VERDICT.md` /
  `cycle_state.yaml` / `CORRIGENDUM.md`）保持原样，本文件仅补充证据链。

## 1. 复算命令与脚本路径

- 脚本: `workspace/v72p2d1_offline_e45269c9/recompute.py`
- 命令: `python workspace/v72p2d1_offline_e45269c9/recompute.py`
- 约束（脚本内已固化）: 不 import / 不调用 run_decoder /
  execute_diagnostic / run_arm；不改算法（图计数器与冻结 harness 逐字一致）；
  不写 `comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/`；
  不读 CAL / 不做 refit。

## 2. 实际值表（直接引用已复算事实）

| 项 | Arm A | Arm B | 备注 |
|---|---|---:|---|
| 母图 M × NBIT | 9036 × 10240 | 9036 × 10240 | 两臂同形 |
| 母图 nnz | 49620 | 49620（列置换后不变） | `generate_h_mother_sparse` |
| col_map | 恒等 | `[1204:10239] = 1204 + permutation(9035)`，`default_rng(20260902)`，首尾 `col_map[0]=0`、`col_map[10239]=10239` | 诊断专用 seed |
| pure-H check–check 四环 ΣC(k,2) | 1196 | 1196 | 库内已验证（本补证） |
| pure-H collision 对数（check 对，k≥2 计 1） | 1194 | 1194 | 库内已验证（本补证）；**禁止冒充下一行** |
| symbol-factor ΣC(k,2)（本臂列号 `v//10` 重分组） | 8452 | 328 | workspace 离线复算值，口径见 §3 |
| symbol / collision rows 外部预期 | 8170 | 326 | **外部预期，本次 workspace 未独立输出该行数，仍待库内留痕** |

## 3. 口径定义

- pure-H 口径：直接对二元校验矩阵 H 的 CSR（`indptr` / `indices`）统计。
  `count_four_cycles` = 对每个 variable 列相连 check 对计数 `pair_count`，
  求 ΣC(k,2)；`count_collisions` = 满足 k≥2 的 check 对个数。
- symbol-factor 口径（`symbol_sigma_c2`，bps=10）：
  对每行 check，将本臂列号按 `s = v // 10` 重分组（sym*10+bit 布局假设，
  B 臂在置换后按置换后列号重分组，故与 A 可比性仅限同口径描述），
  每 symbol 内出现 k 个 bit 则贡献 C(k,2)，按行求和。
  单 check 触及同 symbol 两 bit 贡献恰为 1（即一条混合四环
  check–bit1–symbol–bit2–check）。
- 严禁把 pure-H collision 对数 1194/1194 冒充 symbol rows 8170/326；
  两者口径不同，数值不可互换。

## 4. 最小口径测试（ASSERT_PASS）

- 输入：1 check × bits {0,1}（bps=10 下同属 symbol 0）。
- 期望：pure-H = 0，混合 symbol ΣC2 = 1。
- 结果：`CALIBER_TINY pure_H=0 mixed_symbol_C2=1 ASSERT_PASS=True`。
- 作用：仅校验 §3 两口径定义实现正确，不证明任何科学结论。

## 5. D2/D3 前提与 O1 曲线摘要

- D2/D3 前提：`results.json` 两臂各 72 ckpt，`D2_sym_errors` 与
  `D3_bit_errors` 全 0，前提成立（`D2D3_PREMISE_ALL_ZERO=True`）。
- O1 曲线：`O1(r) = weight(H_arm[:r] · e)`，`e = Alice XOR Bob`，
  `VAL=1726..1729`（session `20260123_1M_600k_0dB`），
  `raw_bit_errors=3100` / `raw_sym_errors=620`。
- 输入范围：仅读 VAL 四帧（每帧 256 行、pair_idx 去重、symbol ∈ [0,1024)）
  + `v71_data_registry.json` 元数据与 provenance 路径；不读 CAL702..1725。
- 检查点行：`range(160, 8993, 128) + [9032, 9036]`。
- 全程标签：逐行与状态行均标 `POSTHOC_RECONSTRUCTED`；
  非原始诊断输出，仅为事后重构曲线，不得作原始 D 口径引用。

## 6. UNKNOWN 条件

- `D2D3_PREMISE_ALL_ZERO=False` → `O1_STATUS=UNKNOWN reason=D2D3_premise_failed`。
- pandas 不可用 → `UNKNOWN: pandas unavailable (...)`。
- registry 不可读 → `UNKNOWN: registry unreadable (...)`。
- session 缺失 → `UNKNOWN: session 20260123_1M_600k_0dB not in registry`。
- VAL parquet 缺失 → `UNKNOWN: VAL parquet missing (...)`。
- VAL 读取失败 → `UNKNOWN: VAL parquet read failed (...)`。
- 任一帧行数 ≠256 / pair_idx 不去重 / symbol 越界 / 四帧拼接形状 ≠(1024,)
  → 对应 `UNKNOWN` 原因行，O1 不输出。
- 本补证引用的是前提成立分支；若复现环境触发任一 UNKNOWN，
  O1 不得引用为事实。

## 7. 原四文件状态

- `comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/`
  四文件未动、未覆盖。本补证不改变其内容与计量。
