# V72P2D1-PARITY Corrigendum（独立纠正文件，不改写历史原文）

- Cycle: V72P2D1-PARITY. 日期: 2026-09-04.
- 性质: 仅文档纠正。直接引用已复算事实，不重新计算、不运行 decoder、
  不重跑 A/B、不调参、不覆盖
  `comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/`
  四文件（manifest.json / results.json / table.csv / report.md）、
  不读逐符号密钥数据。
- 历史原文（`RESULT_SUMMARY.md` / `REVIEW_VERDICT.md` /
  `cycle_state.yaml` / `AGENT_PROJECT_MEMORY.md` 相关条目）保持原样，
  以本文件为准进行纠正阅读。

## 1. 纠正对象：旧同构外推与“环数未变”解释

- 旧 `RESULT_SUMMARY.md` “Mechanical M1-M7 pass” 段原文写
  “four-cycles 1196/1196, collisions 1194/1194
  (graph-isomorphic under column permutation; recomputed, not hand-filled)”。
- 该句把纯 H check–check 统计误作固定 symbol 分组下完整因子图同构的证据，
  且“collisions 1194/1194”不适用于 symbol-factor–check 口径。
  原文保留，此处纠正其解释，不删除原文。

## 2. 两种图统计（部分已验证，部分为外部引用）

| 统计口径 | Arm A | Arm B | 说明 |
|---|---|---:|---|
| pure-H check–check 四环数 | 1196 | 1196 | 库内已验证事实（results.json/manifest一致）；仅二元校验矩阵 H 本身的 check–check 环统计 |
| symbol-factor–check 涉及数 | 8452 | 328 | 外部复算引用，库内未留痕，待补证据，暂不作验证事实 |
| collision rows | 8170 | 326 | 外部复算引用，库内未留痕，待补证据，暂不作验证事实；与上一行同口径 |

- 计数定义与函数名引用本次未在库内留log，待补证据后方可作验证事实。
- 明确：纯 H check–check 环数一致（1196/1196，库内已验证）
  不得外推为固定 symbol 分组下完整因子图同构；
  上表 B 侧（328/326）及 A 侧同口径值（8452/8170）为外部复算引用，
  库内未留痕，暂不作验证事实，不用于本周期科学结论。

## 3. D1 边界与 NOT_RECORDED 清单

- D1 只能称“输入 syndrome 一致性”（72 ckpt × 2 臂，
  syndrome-recompute match，mismatch_rows 0）。
- 以下观测在本周期 D1–D8 标量范围内为 NOT_RECORDED，
  不得由 D1 外推：
  - 候选 syndrome 违反数；
  - 违反数分位数；
  - sum(c2v)；
  - prior-only 基准；
  - 边缘增益。

## 4. 两臂候选-vs-Bob 与计量（已记录事实，直接引用）

- 两臂 72 ckpt candidate-vs-Bob 全 0
  （D2 vs-Bob sym_errors 0，D3 vs-Bob bit_errors 0，
  D6 flips 0/0，D7 deg2/rest bit errors 0/0）。
- 迭代数 A 334 / B 321；终态均为 LADDER_EXHAUSTED，
  验证失败（accepted false，exact false，oracle_exact false；
  undetected false 且隔离，从不并入 success/FER）。
- 原计量保留：每臂 leak_IR 9100 bits（9036 syndrome + 64 tag），
  total modelled public 9171 bits（+71 CONTINUE control）；
  f_model_relative 与 f_public_model_relative 口径不变。

## 5. 修正后科学结论（仅描述性，不扩展因果）

- 在单个非新鲜诊断块 VAL1726–1729 上，两臂终态同为
  LADDER_EXHAUSTED、错误计数与披露计量相同，
  迭代数不同（334 vs 321）。
- 鉴于第 2 节的图统计差异与第 3 节的 NOT_RECORDED 清单，
  不得将“ladder 结果未动”等同于“因子图结构未变”或任何因果解释；
  未完成观测不重写成 PASS；不做 FER / SKR / 信息论极限 /
  方法定级 / 推广性断言。

## 6. 离线补证链接（追加，不改历史测量）

- 见 `docs/research_cycles/V72P2D1-PARITY/OFFLINE_EVIDENCE.md`
  与脚本 `workspace/v72p2d1_offline_e45269c9/recompute.py`
 （命令 `python workspace/v72p2d1_offline_e45269c9/recompute.py`，
  decoder-free、CAL-free，不重跑 A/B，不覆盖四文件）。
- 证据状态更新（第 2 节表格口径不变，仅更新证据状态）：
  - pure-H check–check 1196/1196：库内已验证（含本补证复算）。
  - pure-H collision 对数 1194/1194：库内已验证（含本补证复算）；
    禁止冒充 symbol rows。
  - symbol-factor ΣC(k,2) 8452/328（本臂列号 `v//10` 重分组）：
    workspace 离线复算值，口径见补证 §3；最小口径测试 ASSERT_PASS。
  - symbol / collision rows 8170/326：仍为外部预期，
    本次 workspace 未独立输出该行数，仍待库内留痕，暂不作验证事实。
- 第 2 节“外部复算引用，库内未留痕”降级语义保留为历史记录；
  本节仅对上列四项分别标注新证据状态，不删除原降级表述，
  不改变计量与科学结论。
