# Spec Delta: formal-nonbinary-ldpc-v32-operating-point-audit-correction

> Normative SHALLs for the V32 operating-point **audit-only correction**.
> 锚点：`proposal.md`（L1–L4 / S1–S5）、`design.md` §1–§12、`tasks.md`
> （Allowed New Files / Forbidden / Frozen Constants）。冻结数值跨四文件一致；
> 发现不一致 ⇒ STOP 上报，禁止静默改写任何一方。

## Scope

本变更是 **audit-only correction**：一个单一只读重算 CLI 从原始持久化记录独立重算
D0/D1/D2，并把 D3 重写为「精确 V31 层率下经验联合 P(A,B) 的 ensemble DE 收敛问题」的
**定义**（只定义，不执行），在唯一 additive 输出根产出恰八件 v2 证据，并以严格机械
优先级产出 candidate 终态。全程无 DE、无 decoder、无 graph builder、无 finite-control、
无 raw-data pipeline、无 longrun/minrerun/routeA、不触碰 sibling Polar checkout。
最终交付状态恒为 `candidate_only`，等待 Codex 主控 ACCEPT/REJECT。

被修正对象是旧 change
`formal-nonbinary-ldpc-v32-operating-point-consistency-audit`
及其旧 run_01 十件。处理原则：不删除、不修改、不「修复」——仅引用与标注，
全部输出适用以下四标签（verbatim 写入 v2 `audit_manifest.json` 的 `lifecycle_note`）：

```
post_hoc_exploratory_only
not_formal_pre_registered_gate
numerical_outputs_retained
scientific_terminal_superseded_pending_correction
```

### In scope

- 本 OpenSpec 四件套（proposal / design / specs / tasks）在任何实现之前完整冻结
  （A2 一致性自检 + A3 R1 ACCEPT_FREEZE + main 确认）。
- Correction verifier CLI：
  `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit_correction.py`
  （子命令 d0/d1/d2/d3/all + `--runner` 注入 + collision STOP + stage-0 七绑定校验）。
- 测试套件 T0/T1/T2/T3(smoke)：
  `comparison_bench/tests/test_nonbinary_v32_operating_point_audit_correction.py`。
- 唯一 additive 证据根八件（见 DEF-4）。
- workspace scratch：`workspace/nbldpc_v32_operating_point_audit_correction/<fresh-id>/`。
- Draft-only successor 材料（仅 `workspace/` 内，不注册变更、不执行）：V33
  rate-aligned empirical-channel ensemble DE OpenSpec 候选草案；NB-Polar feasibility
  concept note 草案。
- 三条分离 commit（spec freeze / impl / evidence），显式路径 staging。

### Out of scope（全部明确排除）

- 重跑任何 DE（含 bridge DE 复跑、V33 ensemble DE 执行）。
- 运行任何 decoder / graph builder / finite-control / raw-data pipeline /
  任何 `longrun_*` / `minrerun_*` / `routeA_*`。
- corrected matched-B1 对照实验（把 Q_B1 称为 matched empirical law 即违规）。
- NB-Polar 实验执行（concept note 草案除外）。
- n=2048 配置（本轮仅涉 n=1024）。
- 编辑 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md` / V32 final report /
  archive state（属 A11/A12，仅在 Codex 主控 ACCEPT 后按其指令执行）。
- qualification / promotion / deployment 措辞出现在任何本变更产物中即违规。
- 启动 V33 / NB-Polar / corrected-B1 successor 变更（draft-only 文件除外）。
- 回改旧审计 run_01 数值或任何 protected root（见 SHALL-N2）。

## Definitions

### DEF-1 输入绑定（7 行，全部 read-only）

| # | 绑定 | 路径与冻结内容 | 读法 |
|---|------|----------------|------|
| R1 | V32 bridge run_01 | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/` 下 `per_block.jsonl`（**247 行**）、`RUN_MANIFEST.json`、`summary_B0..B5.json` | 只读 |
| R2 | 旧审计 run_01 十件 | `nbldpc_v32_operating_point_audit/run_01/**`（audit_manifest.json、d0_signature.{json,md}、d1_consistency.{json,md}、d2_feasibility.{json,md}、d3_v26_evidence.{json,md}、final_branch_decision.json） | 只读；**仅作交叉引用与生命周期标注对象，其数值不作为可信源**（v2 全部独立重算） |
| R3 | V25 计数矩阵 | `nbldpc_v25_20260818/run_04/channel_counts.npz`，键名**逐字** `{sid}_N_ab_train_N_ab_train`（重复后缀是盘上键名的组成部分，非笔误） | 只读 |
| R4 | V25 汇总与划分 | 同 run_04 `channel_summary.json`：raw_ser 三源 **1M `0.239779296875` / 1p5M `0.2544695292735815` / 2M `0.2557409550754458`** 及 `pm1_mass` ±1 方向质量字段；`split_manifest.json` | 只读 |
| R5 | V26 run_02 DE 历史 | `nbldpc_v26_20260818/run_02/gate.json`（status `pass_target_f13`）、`best_passing_f`（A01=1.6 / A02=1.3）、`screen_results.json` + `confirmation_results.json`、`RUN_MANIFEST.design_constants` | 只读；仅历史对照（DEF-6），不得外推 |
| R6 | V31 run_01 manifest | `nbldpc_v31_20260820/run_01/RUN_MANIFEST.json` 的 `configs["1024"].sources[].{H.L1, H.L2, m1=16, m2∈{184,190,192}, m_total∈{200,206,208}, leak_total_bits∈{1064,1094,1104}, f_total≈{1.2971,1.2941,1.2949}}` | 只读 |
| R7 | V31 图身份与层率注册表 | 同 run_01 `matrix_audits.json`（packet_id `m1_16_n1024_n1024\|QC-cyclic-projective`）、`m1_registry.json`（L1 rate **0.984375 ×3 源**；L2 rates **0.8203125 / 0.814453125 / 0.8125**） | 只读 |

**stage-0 校验（MUST）**：CLI 在产出任何分析输出之前 MUST 校验全部 7 行绑定的
存在性 + 关键字面值（键名、raw_ser、m2 / leak_total_bits / rates / packet_id 等）+
文件 SHA256 身份；任一失败 ⇒ STOP（exit 非 0），不产出任何分析输出。
persisted terminal（V32 bridge `candidate_terminal.json` =
`finite_graph_decoder_mismatch`）按 distrust 读入，仅用于记录「该归因不被接受」，
其结论永不进入 v2 推理链。

### DEF-2 语义修正 C1–C6（normative，约束 D0–D3 每一步计算）

- **C1（B1 归因禁令）**：B1 发散观测本身成立（60/60 final > initial），但 B1 样本来自
  生成律 Q_B1（Alice uniform + Bernoulli(raw_ser) + uniform nonzero delta mod 1024），
  而后验似然来自 V25 经验联合 P(A,B)。生成器/后验律失配 ⇒ **禁止把 B1 发散归因到
  固定 QC 图或 decoder**。
- **C2（B2 sentinel）**：B2 的 `l2_errors_final=1024` 是 not_run sentinel（L1 失败后
  L2 未运行，x2_hat 不存在），不是 L2 发散证据。B2 必须排除出一切误差轨迹/发散统计，
  仅以 sentinel 计数 + 状态字段形式报告。
- **C3（B3/B4 命名禁令）**：B3/B4 为 improve-but-no-syndrome（final < initial 且
  syndrome/exact 恒假；均值约 ~250→~179 L2 errors）：有实质纠错能力但未达 syndrome
  收敛。**禁止用 "divergent" 描述 B3/B4**。
- **C4（无穷语义命名）**：完整期望 E_Q[−log P] = infinity（Q 有正质量落在 P=0 格上），
  完整量的唯一合法取值是字符串字面值 `"infinity"`（附推导行）；有限量只能命名
  `conditional_finite_support_mean` 与 `truncated_common_support_cross_entropy`；
  两者禁止称 full NLL / full cross entropy。
- **C5（empirical-P 可行性范围限定）**：empirical P 下预算可行性只能表述为 nominal
  information budget feasible——不含 finite-length、DE、fixed-graph、decoder 任何层面
  的可行性主张。
- **C6（Q_B1 不可行结论）**：原始 Q_B1 律在当前分配下标记为 information-theoretically
  infeasible at current allocation（推导见 DEF-3 Law B）。

### DEF-3 关键冻结数值

- **support-miss 参考值**（旧审计 v1 对照基准；v2 独立重算，差异逐源列 delta 如实记录，
  绝不静默对齐、绝不回改旧文件）：旧 `q_mass_on_p_zero_cells` ≈
  **0.239468 / 0.254127 / 0.255348**（1M / 1p5M / 2M）；旧 MC 条件均值 ≈
  **0.397–0.431** bits/symbol；旧截断交叉熵 ≈ **7.77–7.91** bits。
- **Q_B1 律（Law B）**：H_Q(B|A) = h2(raw_ser) + raw_ser·log2(1023) ≈
  **3.1921 / 3.3626 / 3.3773** bits/symbol（三源）；required_bits = n × H_Q @ n=1024
  ≈ **{3268.7, 3443.3, 3458.4}** bits vs pure syndrome total **{1000, 1030, 1040}**
  bits（gap 强烈为负 ≈ −2269 / −2413 / −2418 bits ⇒ information-theoretically
  infeasible at current allocation）。
- **MC 参数**（manifest 预冻结，禁 tuning）：seed=**20260822**；n_samples=**100000**；
  quantiles=**[0.05, 0.5, 0.95]**。
- **V31 层率与开销**：L1 **0.984375 ×3 源**；L2 **0.8203125 / 0.814453125 / 0.8125**；
  m1=**16**；m2 ∈ **{184, 190, 192}**；`leak_total_bits` verbatim
  **{1064, 1094, 1104}**；pure syndrome 重算 = (m1+m2)·5 = **{1000, 1030, 1040}**
  （L1_syndrome_bits = m1·5 = 80；L2_syndrome_bits = m2·5 ∈ {920, 950, 960}）。
- **raw_ser 三源值 verbatim**：见 R4。

### DEF-4 Run root 与恰八件输出

Run root（唯一写根）：
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/`

恰八件（多一件少一件都算违规）：

1. `audit_manifest.json` —— 7 行绑定逐一登记（路径 + SHA256）、Git HEAD、
   implementation identity（CLI 路径 + 自身 SHA256）、`no_de_run=true`、
   `no_decoder_run=true`、`old_roots_read_only=true`、`lifecycle_note`=四标签、
   本次输出文件列表、冻结 MC 参数与 bin 边界；
2. `d0_failure_signature.json` —— AC-D0 全量失效签名；
3. `d1_support_mismatch.json` —— AC-D1 支撑失配（含 naming_rules 与旧值对照列）；
4. `d2_dual_law_feasibility.json` —— AC-D2 双 law（两个平级对象）；
5. `d3_next_question.json` —— AC-D3 唯一问题 + 层率表 + `not_fixed_packet_de=true`；
6. `corrected_branch_decision.json` —— AC-T 终态选择 + C01–C13 checklist；
7. `readonly_review.json` —— AC-R 独立 reviewer 事后补写；
8. `operator_handoff.md` —— Operator Handoff 组 closeout 补写。

执行序（固定）：manifest freeze → d0 → d1 → d2 → d3 → corrected_branch_decision；
readonly_review.json 与 operator_handoff.md 由对应角色在该序列完成后补入。

### DEF-5 终态集与优先级（mechanical、strict order）

候选终态恰取三值之一，优先级严格（高者优先）：

```
audit_evidence_inconsistent  >  audit_verifier_blocked  >  audit_corrected_rate_aligned_de_required
```

### DEF-6 D3 唯一下一问题（只定义，不执行）

问题原文（逐字出现在 `d3_next_question.json` 的 `question` 字段）：

> 在 V25 empirical joint P(A,B)、F03/A02 分配和 V31 实际层率下，对应 ensemble DE
> 是否在三源、两层全部收敛？

红线：DE 是 ensemble/channel 分析，**不是 fixed-QC DE**；`not_fixed_packet_de=true`
必须写入。V26 历史（R5：gate `pass_target_f13`，best_passing_f A02=1.3）仅作其当时
运行点下的历史对照，**不可外推至 V31 层率**（层率不同 ⇒ 不是同一 ensemble 问题）。

stop 条件：任一 source/layer 不收敛 ⇒ 不启动 finite-control。
advance 条件：三源两层全部收敛 ⇒ 仅 ensemble/channel 层面允许继续；fixed packet
（QC 图）层面结论必须等待后续 finite-control 变更，本变更不发。

### DEF-7 V31 层率表（verbatim 写入 d3 输出）

| layer | 1M | 1p5M | 2M |
|---|---|---|---|
| L1 | 0.984375 | 0.984375 | 0.984375 |
| L2 | 0.8203125 | 0.814453125 | 0.8125 |

---

## Requirements (SHALL)

### Lifecycle (AC-L)

- **SHALL-L1**：实现与执行 MUST 发生于完整 OpenSpec 冻结之后（A2 四件套一致性自检 +
  A3 R1 ACCEPT_FREEZE + main 确认）。任何先于冻结提交的实现 commit 或真实输入执行
  即 lifecycle 违规（git 提交时间序为证据）。
- **SHALL-L2**：旧审计 run_01 十件与旧 change
  `formal-nonbinary-ldpc-v32-operating-point-consistency-audit` 全程字节不变；
  仅以 Scope 四标签代码块引用与标注，绝不回改、绝不「修复」、绝不静默对齐。

### No-run / No-overwrite (AC-N)

- **SHALL-N1**：全程禁止运行 DE、decoder、graph builder、finite-control、raw-data
  pipeline、任何 `longrun_*` / `minrerun_*` / `routeA_*`；禁止触碰
  `../HD-QKD_Polar_Release/**`（sibling Polar checkout）。
- **SHALL-N2**：以下根 byte-identical before/during/after 只读保护——五个旧根：
  1. `…/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/**`
  2. `…/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/**`
  3. `…/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_02/**`
  4. `…/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/**`
  5. `…/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/**`
  外加 archive 历史证据（`openspec/changes/archive/**`）与 frozen baseline
  `src/**`、`experiments/**`、`tools/**`、`results/**`。
- **SHALL-N3**：run root 已存在 ⇒ collision STOP（exit 非 0）；禁覆盖、禁自动 `run_02`；
  白名单 STOP 发生时现场证据不可变保留，终态按 DEF-5 优先级路由。
- **SHALL-N4**：全部写操作限于唯一新根（路径包含检查）+ fresh
  `workspace/<fresh-id>/` scratch/test roots；按 DEF-4 固定执行序进行，manifest
  先冻后算（MC 参数 / bin 边界 / lifecycle_note 四标签 / no_de_run / no_decoder_run /
  old_roots_read_only / Git HEAD / implementation identity 预冻结）。

### D0 全量失效签名重算 (AC-D0)

- **SHALL-D0a**：解析 `per_block.jsonl` 按每条记录 `arm` 字段分组（禁止行号定位）；
  强制计数断言 B5=1 / B0=6 / B1..B4 各 60（总 247）；任何 `block_uid` 重复 ⇒ STOP
  （evidence inconsistent）。
- **SHALL-D0b**：逐记录提取 design §4 字段清单（l1/l2 errors initial/final、
  terminal_decoder_status、l1_decoder_status_verbatim、iterations、unsatisfied_checks、
  posterior_nll/entropy、truth_symbol_rank、calibration_bucket、posterior_anomaly_block、
  residual_syndrome_stats.l1/l2_residual_checks、syndrome、exact、tag、false_accept、
  success）；arm×source 聚合输出 mean/median/min/max + 直方图（bin 边界在
  audit_manifest 预冻结，沿用旧 manifest error-delta 整数边与 log2 bits/symbol 边，
  执行前声明不调参）；单位规则：nll/entropy 同时报告 raw（per block）与 /1024
  （bits/symbol）两套，与参考熵比较一律用 bits/symbol；禁止任何「单样本代表全域」表述。
- **SHALL-D0c**：谓词机械验证，违反记该谓词 `signature_mismatch=true` 如实记录，
  禁止静默调和：
  - P-i：B1 全部 60 条 `l2_errors_final > l2_errors_initial` 且
    `posterior_anomaly_block=true`（活跃发散观测成立，但归因受 C1 约束）；
  - P-ii：B2 全部 60 条 `l2_errors_final == 1024`（sentinel），并按 C2 将 B2 排除出
    误差轨迹/发散统计（排除轨迹分析如实记录）；
  - P-iii：B3∪B4 记录 `l2_errors_final < l2_errors_initial` 且 `syndrome=false` 且
    `exact=false`（improve-but-no-syndrome，命名受 C3 约束）。

### D1 Q_B1/P 支撑失配重算 (AC-D1)

对每个源 s ∈ {1M, 1p5M, 2M}（raw_ser 取 R4 冻结值；P = N_ab/total 取 R3 键）：

- **SHALL-D1a**：解析构造 Q_B1(b|a) = (1−raw_ser_s)·δ_{b=a} +
  raw_ser_s·Uniform{b≠a mod 1024}，Q(a)=Uniform；逐源解析求和（非 MC）计算
  `q_mass_on_p_zero_cells`（Q 质量在 P=0 格上的积分）。
- **SHALL-D1b**：`full_expected_nll` 字段 = 字符串字面值 `"infinity"`，附一行推导：
  正质量（q_mass_on_p_zero_cells > 0）落在 P=0 格 ⇒
  E_Q[−log P] ⊇ 正质量·log(1/0) = ∞。
- **SHALL-D1c**：`conditional_finite_support_mean`：MC 仅对非命中样本计算，
  seed=20260822、n_samples=100000、quantiles=[0.05, 0.5, 0.95]——三项全部在 manifest
  预冻结（禁事后 tuning）；同时报告 `zero_hit_count` / `zero_hit_frequency`。
- **SHALL-D1d**：`truncated_common_support_cross_entropy`：仅在共同支撑格上的截断
  交叉熵，一并报告 `common_support_cell_count`。
- **SHALL-D1e**：三种量命名禁止互换或误用作 full NLL / full cross entropy（C4）；
  命名禁令作为 schema 描述字段 `naming_rules` 写入输出 json，使下游读者无法误读。
- **SHALL-D1f**：附旧审计对照列（DEF-3 冻结参考值）；v2 重算若与之不同，逐源列出
  delta 并解释来源（如 MC 实现/舍入差异），不做静默对齐，不回改旧文件。

### D2 双 law feasibility (AC-D2)

- **SHALL-D2a**：Law A `empirical_P_budget`（V25 经验 P + F03/A02 分配）链式熵核对：
  H(U1|B) + H(U2|B,U1) = H(A|B)，并与 V31 `configs["1024"].sources[].H.{L1,L2}`
  逐源核对，容差 1e-6 bits；超差 ⇒ binding drift STOP。泄漏侧双定义显式分开、
  不合并：`L1_syndrome_bits = m1·5 = 80`；`L2_syndrome_bits = m2·5 ∈ {920, 950, 960}`；
  `total_pure_recomputed = (m1+m2)·5 ∈ {1000, 1030, 1040}` vs
  `total_verbatim = leak_total_bits ∈ {1064, 1094, 1104}`（分开引用）；差距
  `gap_bits = leakage − required`（required = n×H，n=1024）及 leakage/required ratio
  按 layer/total 分别报告。
- **SHALL-D2b**：Law B `original_Q_B1_budget` 解析计算
  H_Q(B|A) = h2(raw_ser) + raw_ser·log2(1023)；`required_bits = n × H_Q` ≈
  {3268.7, 3443.3, 3458.4} @ n=1024；对 pure syndrome {1000, 1030, 1040} 的负 gap
  逐源列出（≈ −2269 / −2413 / −2418 bits）。
- **SHALL-D2c**：Law A 结论字段 `conclusion_scope` 强制区分 nominal feasibility 与
  finite-length/DE/fixed-graph/decoder feasibility，取值 verbatim（C5）：
  "nominal information budget feasible only — no finite-length/DE/fixed-graph/decoder
  feasibility claim"。
- **SHALL-D2d**：Law B 结论字段 = "information-theoretically infeasible at current
  allocation"（verbatim，C6），并注明不需要也不应该对 Q_B1 运行 DE（信息论不可行时
  DE 无意义）；两 law 以两个平级对象分开输出，禁止合并成一个布尔或互相替代
  （Law A 可行不救 Law B，Law B 不可行不否定 Law A 的 nominal 陈述）。

### D3 唯一下一问题 (AC-D3)

- **SHALL-D3a**：DEF-6 问题原文逐字嵌入 `d3_next_question.json` 的 `question` 字段，
  且写入 `not_fixed_packet_de=true`；「DE 是 ensemble/channel 分析，不是 fixed-QC DE」
  定性写入输出。
- **SHALL-D3b**：DEF-7 层率表 verbatim 写入输出。
- **SHALL-D3c**：V26 f=1.3（`pass_target_f13`、best_passing_f A02=1.3）仅作只读历史
  对照并注明不可外推至 V31 层率。
- **SHALL-D3d**：写入 stop/advance 条件：任一 source/layer 不收敛 ⇒ 不启动
  finite-control；三源两层全部收敛 ⇒ 仅 ensemble/channel 层面允许继续，fixed packet
  （QC 图）层面等待后续 finite-control 变更，本变更不发。

### Terminal State (AC-T)

- **SHALL-T1**：候选终态恰取 DEF-5 三值之一，按严格优先级机械选择；任一 D 判定失败
  ⇒ 按优先级降级为 `audit_evidence_inconsistent` 或 `audit_verifier_blocked`，
  理由逐条记录。
- **SHALL-T2**：终态 = `audit_corrected_rate_aligned_de_required` 当且仅当 C01–C13
  全部满足（在 corrected_branch_decision 内以 checklist 逐条布尔列出）：
  - C01. D0 全量重算记录与谓词一致（P-i/P-ii/P-iii 通过或 mismatch 已如实标注）；
  - C02. B2 sentinel 语义正确（=1024 not_run，排除出轨迹/发散统计）；
  - C03. B3/B4 improve-but-no-syndrome 表述正确（divergent 字样不得用于 B3/B4）；
  - C04. D1 零支撑质量逐源解析重算（q_mass_on_p_zero_cells 三源齐备）；
  - C05. 完整 NLL 标记为 infinity（字符串字面值 + 推导行）；
  - C06. conditional/truncated 指标命名正确（conditional_finite_support_mean /
    truncated_common_support_cross_entropy，无 full NLL/cross entropy 误用）；
  - C07. D2 同时报告双 law（empirical_P_budget 与 original_Q_B1_budget 并存、未合并）；
  - C08. empirical-P 仅标 nominal information budget feasible（conclusion_scope 逐字）；
  - C09. Q_B1 标 information-theoretically infeasible at current allocation（逐字）；
  - C10. D3 已改为 exact-V31-rate empirical-P ensemble DE 问题（question 逐字 + 层率表）；
  - C11. 全程无 DE / decoder 被调用（静态 + 运行期证据）；
  - C12. 旧证据根字节不变（V32 bridge run_01、旧审计 run_01、V25/V26/V31 各根前后
    哈希一致）；
  - C13. reviewer 独立复算通过（readonly_review.json 存在且 blocking=false）。
  任一不满足 ⇒ 按优先级降级，理由逐条记录。
- **SHALL-T3**：终态禁令七串仅作为 schema 校验目标（T1/T2 机械扫描），不得作为
  corrected_branch_decision 或任何 v2 报告的结论出现：
  `finite_graph_decoder_mismatch`；`QC graph confirmed failure`；
  `decoder confirmed failure`；`NB-Polar preferred`；`qualification-ready`；
  `promotion-ready`；`deployment-ready`。
  （注：`finite_graph_decoder_mismatch` 仅允许以被否定的历史对象身份出现在
  Scope/DEF-1 lifecycle 语境中。）

### Independent Review (AC-R)

- **SHALL-RV1**：`readonly_review.json` 由独立 reviewer 角色写入（既非实现者亦非
  执行者），从原始持久化记录独立重算 headline（尽量不走 CLI 代码路径）、不信主程序
  terminal，按 DEF-5 优先级 + C01–C13 重 derive 终态，核实全部 protected roots 前后
  哈希一致；内容含 findings / blocking / non-blocking 与重算值对照（reviewer id/role
  与分组 verdict）。
- **SHALL-RV2**：reviewer 在本变更中的唯一可写文件是 `readonly_review.json`；
  blocking=false ⇔ C13 成立。

### Operator Handoff (closeout)

- **SHALL-H1**：`operator_handoff.md` 补写入 run_01，含八要素：changed files /
  commands / results / evidence root / dirty worktree scope / frozen roots diff /
  known limitations / exact next authorization boundary；并显式含
  `candidate_only=true` 与 `main_acceptance_pending=true`。
- **SHALL-H2**：A11/A12（durable docs 与 archive 裁决）保持未勾选直到 Codex 主控
  审查；closeout 最终返回声明逐字：「candidate_only，等待 Codex 主控 ACCEPT/REJECT；
  未运行 DE，未运行 decoder，未启动 successor。」

---

## Acceptance Mapping

| AC 组 | SHALL 编号 | 验证方式 |
|------|----------|----------|
| AC-L | SHALL-L1, SHALL-L2 | git log 时间序核查（impl/执行晚于 freeze commit）；旧 run_01 十件与旧 change 前后 SHA256 对照不变 |
| AC-N | SHALL-N1–N4 | 静态 grep/AST import 白名单（stdlib + numpy；无 DE/decoder/graph-builder 标记）+ 运行期证据；五旧根 + archive + src/experiments/tools/results pre/post hash 日志；collision 端到端测试 |
| AC-D0 | SHALL-D0a–D0c | T1 分类/sentinel/谓词测试；T2 fake recount 独立复现 headline 数字；tamper 系列（count drift / source substitution ⇒ STOP） |
| AC-D1 | SHALL-D1a–D1f | T0 tiny 网格 q_mass_on_p_zero_cells 解析核对；infinity 语义断言（正质量⇒"infinity"，无正质量情形不得标 infinity）；manifest 预冻结参数比对；naming_rules schema 断言；对照 delta 列检查 |
| AC-D2 | SHALL-D2a–D2d | 链式熵容差测试（超差 STOP）；双 law 并存断言（缺任一 law 即 fail）；conclusion_scope/conclusion verbatim 断言；gap/ratio 分 layer/total 核对 |
| AC-D3 | SHALL-D3a–D3d | question wording 逐字断言；层率表常量 verbatim 断言；not_fixed_packet_de 存在性断言；V26 不可外推注明检查 |
| AC-T | SHALL-T1–T3 | 终态优先级机械测试（构造各失败组合验证降级序）；C01–C13 checklist 逐项核对；禁令七串扫描（schema 校验目标） |
| AC-R | SHALL-RV1–RV2 | readonly_review.json 存在性 + 作者角色隔离检查；R2 独立重算对照 worksheet（逐值相等布尔）；blocking=false ⇔ C13 |
| Operator Handoff | SHALL-H1–H2 | run_01 恰八件清单精确匹配；handoff 八要素内容检查；最终返回声明逐字核对 |
