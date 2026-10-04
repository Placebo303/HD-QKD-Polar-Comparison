# M2 Honest Baselines — Proposal

- Change: `m2-honest-baselines`
- Track: 无 gate (documentation-only change 本体；`AGENTS.md` §1.2 适用性矩阵 "Documentation-only changes" 行)。本 change 只冻结两基线的方法契约与任务顺序；**不写 `comparison_bench/` 任何代码，不跑任何执行，不 commit/push，不产生 FER/SKR/资格化/发表主张**。
- Scope: T0 M2 OpenSpec（proposal + design + tasks + `specs/` delta 两新文件）。
- Predecessor inputs (read-only, prerequisites only depend on completed numbers):
  - M0 RESULT / 冻结输入 / 预算实测（已完成数）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/SAME_DATA_CMP_METRICS.md` §10 (A-CMPE-1..7)；
  - 起点文件（只增量，不改逻辑）: `comparison_bench/src/comparison_bench/methods/cascade_lite.py` + `comparison_bench/src/comparison_bench/methods/cascade/single_kernel.py`。

## Why

P5 同数据对照需要两个诚实二元基线替代当前稻草人：(1) HD-Cascade（Müller 2024 三改，含并行版）；(2) 分层二元 LDPC（按位面熵分配码率 + 盲协调，替换 V19 保守行数 f=4.169 稻草人）。无冻结契约就无法实现，也无法满足 A-CMPE 逐条映射。

## What (frozen scope)

1. **HD-Cascade**: Müller 2024 三改，**并行版优先**，增量规模约 300–500 行，**只增量起于** `cascade_lite.py` + `methods/cascade/single_kernel.py`（不改既有逻辑/接口）。
2. **分层二元 LDPC**：逐 Gray 位面熵分配码率 + 盲协调（多段小步长），替换 V19 保守行数（f=4.169）稻草人；位面熵用冻结值，不重拟合。
3. 两方法均受 `SAME_DATA_CMP_METRICS` §10 **A-CMPE-1..7 逐条映射**约束（映射表见下）。

## A-CMPE-1..7 mapping (summary; full text in design §7)

| ID | 本 change 落点 |
|---|---|
| A-CMPE-1 | 两方法 per-source 四计数独立列；`undetected` 隔离，禁并入 success/FER；禁跨源合并 |
| A-CMPE-2 | `f_super` 与 `f_eff`（本臂 m 基）双数并列，禁互相替代 |
| A-CMPE-3 | `leak_EC` + 64-bit tag ⇒ verification-aware `λ_total`；EC/验证标签/控制轮次分列；prior 成本行不进 f 分子 |
| A-CMPE-4 | 总/每块/每译码 wall + 峰值 RSS + 交互消息数（Müller 446 vs 3.14 口径：每帧消息数） |
| A-CMPE-5 | `N_req` report-only vs key-eligible（200/276/364）分列；`d`/`q`/`n_IR` 分离；合成/真实/key-eligible 三组计数分离 |
| A-CMPE-6 | 历史行（R3/MLC）不可比即标；r=10 探针行独立，不替真实结论 |
| A-CMPE-7 | 无安全观测量 ⇒ 仅"实测纠错/公开开销收益"，禁 SKR；数字落 measured/assumed/projected/qualified 四列之一 |

## Schema stability (AGENTS.md §5.3)

- **声明：本 change 不改 schema/列名/键名/CLI/输出文件名。** CSV 列名、JSON/YAML 键、CLI 参数名、配置键、输出文件命名约定均不变。
- `specs/` delta 只增两新契约文件（`methods/hd-cascade`、`methods/layered-binary`）；**禁改 `openspec/specs/` 现有文件**。
- 将来落地实现若需新列/新文件，须另开实现 change 并遵守 §5.3。

## Non-goals

- 不写 `comparison_bench/` 代码；不改现有 `cascade_lite` / `single_kernel` / `layered_ldpc_lite` 逻辑。
- 不改 P3/P4/TIMING/NOW、`docs/decision-log.md`、`AGENTS.md`。
- 不执行（含 benchmark/smoke/解码/真实数据访问）；不 commit/push；不授权任何执行。
- 无 FER 胜负预设；无阈值门；无发表/资格化主张。

## Affected specs

- None pending delta.（本 proposal 不改既有 spec；delta 契约见 `specs/` 两新增文件。）
