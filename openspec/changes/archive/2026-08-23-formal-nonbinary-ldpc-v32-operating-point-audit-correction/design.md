# Design: formal-nonbinary-ldpc-v32-operating-point-audit-correction

> 本文件与 `proposal.md` 的 L1–L4 / S1–S5 / 交付物清单 / 成功标准逐条对齐；
> 数值冻结值以本文与 proposal 为准，tasks.md 不得改写。

## §0 Overview

本变更是 audit-only correction：一个单一只读重算 CLI
（`comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit_correction.py`）
从原始持久化记录独立重算 D0/D1/D2，并把 D3 重写为「精确 V31 层率下经验联合 P(A,B) 的
ensemble DE 收敛问题」的定义（只定义、不执行），在唯一 additive 输出根
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/`
产出恰八件 v2 证据；全程无 DE、无 decoder、无 graph builder、无 finite-control、
无 raw-data pipeline、无 longrun/minrerun/routeA、不触碰 sibling Polar checkout。
Ponytail 纪律：stdlib + 已装 numpy，单文件单职责；无缓存层、无重试框架、无原子写、
无校验和体系（SHA256 仅用于 manifest 输入身份记录这一项既有惯例）。

## §1 生命周期缺陷证据（对应 proposal L1–L4）

- **L1/L2 — 实现与执行先于完整 OpenSpec 提交**。证据行（可核查）：
  - `workspace/nbldpc_v32_operating_point_audit/OPERATOR_HANDOFF.md` §1 提交链自证：
    `60117174` = "impl(nbldpc-v32-audit): read-only operating-point consistency audit
    with T0-T2 suite（impl + tasks.md）"，且注明「运行时 HEAD = 60117174（正式执行发生时
    的提交）」；`dda3503e`（= H_spec2）= "spec(nbldpc-v32-opaudit): freeze … OpenSpec
    （补交 proposal/design/spec 三文件）"。
  - 核查命令：`git log --oneline -- comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit.py`
    （impl 提交在前）与 `git log --oneline -- openspec/changes/formal-nonbinary-ldpc-v32-operating-point-consistency-audit/`
    （spec 补交在后）；时间序即证明 impl → 旧审计运行 → dda3503e 规格补交。
  - 结论：审计执行先于其规格冻结提交（dda3503e 在运行之后），故该 change 不能作为
    pre-registered formal gate。
- **L3 — tasks 未勾选 vs handoff 声称完成**。证据行：
  - 旧 change `openspec/changes/formal-nonbinary-ldpc-v32-operating-point-consistency-audit/tasks.md`
    中 P3.1–P3.3、P4.1–P4.3、P5.1–P5.3 全部为未勾选 `- [ ]`（含 P5.2 R2 独立复核项）。
  - 同变更 `OPERATOR_HANDOFF.md` §3 却声称：「P3（候选验收）：ACCEPT_CANDIDATE」「P5.2 R2
    （独立证据复核）：ACCEPT_CANDIDATE_EVIDENCE —— …… **本次 R2 结论已持久化于本 handoff，
    不存在 pending 状态**」。
  - 矛盾：handoff prose 声称的验收状态没有任何 tasks 证据支撑。
- **L4 — 磁盘上无可验证独立 reviewer artifact**。证据行：旧 run_01 目录恰十件——
  `audit_manifest.json`、`d0_signature.{json,md}`、`d1_consistency.{json,md}`、
  `d2_feasibility.{json,md}`、`d3_v26_evidence.{json,md}`、`final_branch_decision.json`；
  其中不存在任何独立 reviewer 产物（`readonly_review.json` 不存在于旧 run_01）。
  「R2 逐位吻合复算」没有可核查的独立文件载体；prose 不能替代独立 acceptance record。

**结论行（适用于旧 change 与旧 run_01 全部输出，写入 v2 manifest 的 lifecycle_note）**：

```
post_hoc_exploratory_only
not_formal_pre_registered_gate
numerical_outputs_retained
scientific_terminal_superseded_pending_correction
```

本修正不删除、不修改、不「修复」旧证据；仅引用与标注（数值不作为可信源，
见 §2 R2 行）。docs/nbldpc-v32-main-review-verdict-20260822.md（Codex 终审：
EVIDENCE_VALID_BUT_ATTRIBUTION_INCONCLUSIVE）作为本修正的科学动机引用。

## §2 输入绑定表（7 行；全部 read-only；persisted terminal 一律 distrust）

| # | 绑定 | 路径与冻结内容 | 读法 |
|---|------|----------------|------|
| R1 | V32 bridge run_01 | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/` 下 `per_block.jsonl`（247 行）、`RUN_MANIFEST.json`、`summary_B0..B5.json` | 只读 |
| R2 | 旧审计 run_01 十件 | `nbldpc_v32_operating_point_audit/run_01/**`（§1 清单十文件） | 只读；**仅作交叉引用与生命周期标注对象，其数值不作为可信源**（v2 全部独立重算） |
| R3 | V25 计数矩阵 | `nbldpc_v25_20260818/run_04/channel_counts.npz`，键名**逐字** `{sid}_N_ab_train_N_ab_train`（重复后缀是盘上键名的组成部分，非笔误） | 只读 |
| R4 | V25 汇总与划分 | 同 run_04 `channel_summary.json`：raw_ser 三源 **1M `0.239779296875` / 1p5M `0.2544695292735815` / 2M `0.2557409550754458`**，及 `pm1_mass` ±1 方向质量字段；`split_manifest.json` | 只读 |
| R5 | V26 run_02 DE 历史 | `nbldpc_v26_20260818/run_02/gate.json`（status `pass_target_f13`）、`best_passing_f`（A01=1.6 / A02=1.3）、`screen_results.json` + `confirmation_results.json`、`RUN_MANIFEST.design_constants` | 只读；仅历史对照（§7），不得外推 |
| R6 | V31 run_01 manifest | `nbldpc_v31_20260820/run_01/RUN_MANIFEST.json` 的 `configs["1024"].sources[].{H.L1, H.L2, m1=16, m2∈{184,190,192}, m_total∈{200,206,208}, leak_total_bits∈{1064,1094,1104}, f_total≈{1.2971,1.2941,1.2949}}` | 只读 |
| R7 | V31 图身份与层率注册表 | 同 run_01 `matrix_audits.json`（packet_id `m1_16_n1024_n1024\|QC-cyclic-projective`）、`m1_registry.json`（L1 rate **0.984375 ×3 源**；L2 rates **0.8203125 / 0.814453125 / 0.8125**）。stage-0 层率校验必须按 allocation（`m1_16_n1024` 或等价定位键）过滤条目——同文件含其他 allocation 条目，禁止全表扫描比对 | 只读 |

- persisted terminal（V32 `candidate_terminal.json` = `finite_graph_decoder_mismatch`）
  按 S1 distrust 处理：读入仅用于记录「该归因不被接受」，其结论永不进入 v2 推理链。
- **stage-0 校验**：CLI 启动后先验证全部 7 行绑定存在性 + 关键字面值（键名、raw_ser、
  m2/leak_total_bits/rates/packet_id 等）+ 文件 SHA256 身份；任一失败 → STOP
  （exit 非 0），不产出任何分析输出。

## §3 语义修正条款（normative，约束 D0–D3 每一步计算）

- **C1（B1 归因禁令）**：B1 发散由 support mismatch 支配——发散观测本身成立
  （60/60 final > initial），但 B1 样本来自生成律 Q_B1（Alice uniform +
  Bernoulli(raw_ser) + uniform nonzero delta mod 1024），而后验似然来自 V25 经验联合
  P(A,B)。生成器/后验律失配 ⇒ **禁止把 B1 发散归因到固定 QC 图或 decoder**。
- **C2（B2 sentinel）**：B2 的 `l2_errors_final=1024` 是 not_run sentinel
  （L1 失败后 L2 未运行，x2_hat 不存在）。B2 必须排除出一切误差轨迹/发散统计；
  仅以 sentinel 计数 + 状态字段形式报告。
- **C3（B3/B4 命名禁令）**：B3/B4 为 improve-but-no-syndrome（final < initial 且
  syndrome/exact 恒假；均值约 ~250→~179 L2 errors）：有实质纠错能力但未达 syndrome 收敛。
  **禁止用 "divergent" 描述 B3/B4**；措辞限于 improve-but-no-syndrome /
  trapping-like / finite-redundancy ceiling 方向。
- **C4（无穷语义命名）**：完整期望 E_Q[−log P] = infinity（Q 有正质量落在 P=0 格上；
  正质量 × log(1/0) = ∞），任何有限 MC 均值只能叫 `conditional_finite_support_mean`
  （仅非命中样本条件统计），共同支撑截断交叉熵只能叫
  `truncated_common_support_cross_entropy`；两者**禁止称 full NLL / full cross entropy**。
  完整量的唯一合法取值是字符串 `"infinity"`。
- **C5（empirical-P 可行性范围限定）**：empirical P 下的预算可行性只能表述为
  nominal information budget feasible——不含 finite-length、DE、fixed-graph、decoder
  任何层面的可行性主张。
- **C6（Q_B1 不可行结论）**：原始 Q_B1 律在当前分配下标记为
  information-theoretically infeasible at current allocation（推导见 §6 第二 law）。

## §4 D0 重算设计 — 全量失效签名

- 解析方式：按每条 JSONL 记录的 `arm` 字段分组（禁止行号定位）。
- 计数断言：B5=1 / B0=6 / B1..B4 各 60（总 247）；任何 `block_uid` 重复 → STOP
  evidence inconsistent（exit 非 0，保留现场）。
- 逐记录提取字段清单（v2 schema 按 §8 重命名承载同类信息）：
  `l1_errors_initial/final`、`l2_errors_initial/final`、`terminal_decoder_status`、
  `l1_decoder_status_verbatim`、`iterations`、`unsatisfied_checks`、`posterior_nll`、
  `posterior_entropy`、`truth_symbol_rank`、`calibration_bucket`、
  `posterior_anomaly_block`、`residual_syndrome_stats.l1_residual_checks /
  l2_residual_checks`、`syndrome`、`exact`、`tag`、`false_accept`、`success`。
- 聚合：arm×source 分组输出 mean / median / min / max + 直方图（bin 边界在
  audit_manifest 预冻结，沿用旧 manifest 的 error-delta 整数边与 log2 bits/symbol 边，
  见旧 run_01 `audit_manifest.frozen.histogram_bins`；执行前声明，不调参）。
  单位规则：nll/entropy 同时报告 raw（per block）与 /1024（bits/symbol）两套；
  与参考熵比较一律用 bits/symbol。
- 谓词机械验证（违反 → 该谓词 `signature_mismatch=true` 如实记录，禁止静默调和）：
  - **P-i**：B1 全部 60 条 `l2_errors_final > l2_errors_initial` 且
    `posterior_anomaly_block=true`（活跃发散观测成立，但归因受 C1 约束）。
  - **P-ii**：B2 全部 60 条 `l2_errors_final == 1024`（sentinel）且按 C2 排除出轨迹统计。
  - **P-iii**：B3∪B4 记录 `l2_errors_final < l2_errors_initial` 且 `syndrome=false`
    且 `exact=false`（improve-but-no-syndrome，按 C3 命名）。
- 输出：`d0_failure_signature.json`（+ md 可选），含 per-arm/source 表与完整分布；
  报告中**禁止任何「单样本代表全域」的表述**（一切结论必须落到全量计数/分布上）。

## §5 D1 重算设计 — Q_B1/P 支撑失配（support mismatch）

对每个源 s ∈ {1M, 1p5M, 2M}（raw_ser 取 R4 冻结值；P = N_ab/total 取 R3 键）：

- 构造（解析式）：`Q_B1(b|a) = (1−raw_ser_s)·δ_{b=a} + raw_ser_s·Uniform{b≠a mod 1024}`，
  `Q(a)=Uniform`。
- `q_mass_on_p_zero_cells`：Q 质量在 P(a,b)=0 格上的积分，**解析求和**（非 MC）。
- `full_expected_nll` 字段 = 字符串字面值 `"infinity"`，附一行推导：
  正质量（q_mass_on_p_zero_cells > 0）落在 P=0 格 ⇒ E_Q[−log P] ⊇ 正质量·log(1/0) = ∞。
- `conditional_finite_support_mean`：MC 仅对非命中样本计算，seed=`20260822`、
  n_samples=`100000`、quantiles `[0.05, 0.5, 0.95]`——三项全部在 manifest 预冻结；
  同时报告 `zero_hit_count` / `zero_hit_frequency`。
- `truncated_common_support_cross_entropy`：仅在共同支撑格上的截断交叉熵，
  一并报告 `common_support_cell_count`。
- 与旧审计对照列（只读引用，差异如实写进 v2 报告，绝不回改旧文件）：
  旧 q_mass_on_p_zero_cells ≈ **0.239468 / 0.254127 / 0.255348**（1M/1p5M/2M）；
  旧 MC 条件均值 ≈ **0.397–0.431** bits/symbol；旧截断交叉熵 ≈ **7.77–7.91** bits。
  v2 重算若与之不同，逐源列出 delta 并解释来源（如 MC 实现/舍入差异），不做静默对齐。
- 命名禁令（C4）作为 schema 描述字段写入输出 json（`naming_rules` 字段），
  使下游读者无法误读 conditional/truncated 为 full NLL/cross entropy。

## §6 D2 双 law 设计 — 两级 feasibility 分开报告

### Law A：empirical_P_budget（V25 经验 P + F03/A02 分配）

- 链式核对：H(U1|B) + H(U2|B,U1) = H(A|B)，并与 V31 `configs["1024"].sources[].H.L1/H.L2`
  逐源核对，容差 1e-6 bits；超差 → binding drift STOP。
- 泄漏侧（V31 verbatim + 重算两条定义显式分开，不合并）：
  - `L1_syndrome_bits = m1·5 = 80`（log2(32)=5 bits/symbol）；
  - `L2_syndrome_bits = m2_by_source·5 ∈ {920, 950, 960}`；
  - `total_pure_recomputed = (m1+m2)·5 ∈ {1000, 1030, 1040}`；
  - `total_verbatim = leak_total_bits ∈ {1064, 1094, 1104}`（verbatim 含预算开销，
    与 pure syndrome 定义分开引用）。
- 差距：`gap_bits = leakage − required`（required = n×H，n=1024，按 layer/total 分别报）
  及 leakage/required ratio 按 layer/total。
- 结论字段：`conclusion_scope = "nominal information budget feasible only — no
  finite-length/DE/fixed-graph/decoder feasibility claim"`（C5 逐字）。

### Law B：original_Q_B1_budget（生成律 Q_B1）

- 解析计算 `H_Q(B|A) = h2(raw_ser) + raw_ser·log2(1023)` bits/symbol，
  三源近似值 **≈ {3.1921, 3.3626, 3.3773}**（1M/1p5M/2M）。
- `required_bits = n × H_Q ≈ {3268.7, 3443.3, 3458.4}` bits @ n=1024。
- 对比 pure syndrome `{1000, 1030, 1040}` ⇒ gap 强烈为负（≈ −2269 / −2413 / −2418 bits）
  ⇒ 结论字段 `conclusion = "information-theoretically infeasible at current allocation"`（C6）。
- 附句（写入报告）：不需要也不应该对 Q_B1 运行 DE——信息论不可行时 DE 无意义。

**红线**：两个 law 的 feasibility 分开输出为两个独立对象；**禁止合并成一个布尔**
或互相替代（Law A 可行不救 Law B，Law B 不可行不否定 Law A 的 nominal 陈述）。

## §7 D3 重写设计 — 唯一下一问题（只定义，不执行）

- 唯一问题原文（逐字出现在 `d3_next_question.json` 的 question 字段）：

  > 在 V25 empirical joint P(A,B)、F03/A02 分配和 V31 实际层率下，对应 ensemble DE
  > 是否在三源、两层全部收敛？

- 层率表（verbatim 写入输出）：

  | layer | 1M | 1p5M | 2M |
  |---|---|---|---|
  | L1 | 0.984375 | 0.984375 | 0.984375 |
  | L2 | 0.8203125 | 0.814453125 | 0.8125 |

- V26 历史对照（R5，只读）：gate `pass_target_f13`、best_passing_f A02=1.3 是 V26 当时
  运行点下的通过记录，**仅作历史对照并注明不可外推至 V31 层率**（层率不同 ⇒ 不是同一
  ensemble 问题）。
- stop 条件：任一 source/layer 不收敛 → 不启动 finite-control。
- advance 条件：三源两层全部收敛 → 仅说明 ensemble/channel 层面允许继续；
  fixed packet（QC 图）层面结论必须等待后续 finite-control 变更，本变更不发。
- 声明字段：`not_fixed_packet_de=true`。
- 红线：DE 是 ensemble/channel 分析，不是 fixed-QC-graph 分析；该定性写入输出。

## §8 输出八件 schema 要点

Run root（唯一写根）：
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/`

恰八件（多一件少一件都算违规）：

1. `audit_manifest.json`：输入路径 + SHA256 身份（7 行绑定逐一登记）、当前 Git HEAD、
   implementation identity（CLI 文件路径 + 自身 SHA256）、`no_de_run=true`、
   `no_decoder_run=true`、`old_roots_read_only=true`、
   `lifecycle_note` = §1 四标签、本次输出文件列表、冻结的阈值/MC 参数
   （seed 20260822 / n 100000 / quantiles）/bin 边界。
2. `d0_failure_signature.json`（+ `.md` 可选）：§4 全量签名。
3. `d1_support_mismatch.json`：§5 支撑失配（含 naming_rules 与旧审计对照列）。
4. `d2_dual_law_feasibility.json`：§6 双 law（empirical_P_budget 与 original_Q_B1_budget
   两个平级对象）。
5. `d3_next_question.json`：§7 唯一问题 + 层率表 + not_fixed_packet_de=true。
6. `corrected_branch_decision.json`：`selected_branch` 只能取冻结终态三值（与 DEF-5/§9
   完全一致）：`"audit_corrected_rate_aligned_de_required"` 或 `"audit_evidence_inconsistent"`
   或 `"audit_verifier_blocked"`；`branch_inputs` 引用各 D 判定（d0_signature_mismatch、d1 结论、d2 双 law
   结论、d3 定义完成度）。
7. `readonly_review.json`：由**独立 reviewer 角色**后置写入（findings / blocking /
   non-blocking / 重算值对照）；实现者与执行者不得代写。
8. `operator_handoff.md`：changed files / commands / evidence root / dirty worktree
   scope / frozen roots diff / known limitations / exact next authorization boundary。

- collision：run root 已存在 → STOP，禁覆盖、禁自动 `run_02`。
- 所有输入只读；全部写操作仅限本根（路径包含检查）。
- 执行序：manifest freeze → d0 → d1 → d2 → d3 → corrected_branch_decision；
  readonly_review / operator_handoff 由对应角色在该序列完成后补入。

## §9 终态优先级与 13 条件

优先级（机械、严格序）：
`audit_evidence_inconsistent` > `audit_verifier_blocked` > `audit_corrected_rate_aligned_de_required`。

候选终态 = `audit_corrected_rate_aligned_de_required` 当且仅当以下 13 条全部满足
（corrected_branch_decision 内以 checklist 逐条布尔列出）：

1. D0 全量重算记录与谓词一致（P-i/P-ii/P-iii 通过或 mismatch 已如实标注）；
2. B2 sentinel 语义正确（=1024 not_run，排除出轨迹/发散统计）；
3. B3/B4 improve-but-no-syndrome 表述正确（无 divergent 字样用于 B3/B4）；
4. D1 零支撑质量逐源解析重算（q_mass_on_p_zero_cells 三源齐备）；
5. 完整 NLL 标记为 infinity（字符串字面值 + 推导行）;
6. conditional/truncated 指标命名正确（conditional_finite_support_mean /
   truncated_common_support_cross_entropy，无 full NLL/cross entropy 误用）；
7. D2 同时报告双 law（empirical_P_budget 与 original_Q_B1_budget 并存、未合并）；
8. empirical-P 仅标 nominal information budget feasible（conclusion_scope 逐字）；
9. Q_B1 标 information-theoretically infeasible at current allocation（逐字）；
10. D3 已改为 exact-V31-rate empirical-P ensemble DE 问题（question 逐字 + 层率表）；
11. 全程无 DE / decoder 被调用（静态 + 运行期证据）；
12. 旧证据根字节不变（V32 bridge run_01、旧审计 run_01、V25/V26/V31 各根前后哈希一致）；
13. reviewer 独立复算通过（readonly_review.json 存在且 blocking=false）。

任一条不满足 → 按优先级降级为 evidence_inconsistent 或 blocked，理由逐条记录。

## §10 终态禁令（七个不得出现的结论字符串）

以下字符串不得作为 corrected_branch_decision 或任何 v2 报告的结论出现
（作为 schema 校验目标，T1/T2 加机械扫描）：

```
finite_graph_decoder_mismatch
QC graph confirmed failure
decoder confirmed failure
NB-Polar preferred
qualification-ready
promotion-ready
deployment-ready
```

（注：`finite_graph_decoder_mismatch` 仅允许以被否定的历史对象身份出现在 §1/lifecycle
语境中，禁止作为 v2 结论。）

## §11 测试分层 T0/T1/T2/T3（frozen）

统一环境：fresh `workspace/<change>/<fresh-id>/` root +
`pytest -p no:cacheprovider --basetemp <root>`（Windows）；不删除 legacy pytest-of-admin
目录；ACL 报错记录为环境约束，不为绕过而改科学代码。

- **T0 结构/tiny math**：py_compile/import；CLI `--help`；tiny synthetic
  support-mismatch 数学（小网格上 q_mass_on_p_zero_cells 解析值核对）；infinity
  语义断言（正质量→"infinity"，无正质量情形不得标 infinity）；rates 常量断言
  （§7 层率表逐字比对）；禁止导入 DE/decoder/runner（静态 AST import 白名单 =
  stdlib + numpy）；input/output same-root 拒绝。
- **T1 单元/tamper**：D0 全量分类正确；B2 sentinel 不计入 divergence 统计；B3/B4
  improvement-but-no-syndrome 分类；D1 analytic vs MC 容差一致（toy 上解析可核对）；
  conditional/truncated label 断言；D2 双 law 并存断言（缺任一 law 即 fail）；D3
  question wording 断言（原文逐字 + 「不是 fixed-QC DE」表述 + `not_fixed_packet_de`
  存在性）；old output overwrite guard；no forbidden imports/calls（终态禁令七串扫描）。
- **T2 fake qualification**：fake fixture 完整 correction 流程（合成 per_block +
  tiny channel_counts，经显式 fake runner 注入，绝不触生产 runner）；独立 recount
  复现 headline 数字；persisted terminal tamper 检测；persisted summary tamper；
  record count drift；source/rate/law substitution（换源/换率/换 law 任一 → STOP）；
  deep semantic tamper；strict replay（同输入重跑输出一致，时间戳类字段除外并白名单）；
  terminal priority 机械性（构造各失败组合验证优先级序）。
- **T3 只读回归（最小必要集合，不得写成 full T3）**：真实 V32/V31/V25/V26 输入存在性
  与关键身份（stage-0 等价检查）；不调 DE/decoder；canonical/frozen roots 前后不变
  （哈希快照对比）。准确措辞："T3 smoke: PASS; full frozen T3 regression: not in scope."

## §12 自主权边界（frozen）

**可自主**：HEAD/dirty worktree 清点报告；acceptance ID 分配；最小 JSON schema 细节
（§8 要点之内）；只读重算的具体实现；T0–T3 测试组织与拆分；允许文件内的 bug 修复；
reviewer 编排（角色隔离前提下）；非阻塞建议记录；DE draft / NB-Polar concept note
起草（仅 workspace 内，不注册变更、不执行）；operator handoff 维护；允许范围内 commit。

**禁止自主（STOP-and-report）**：把 candidate 标为主控 ACCEPT；改冻结阈值/层率/信道
定义；把 Q_B1 称 matched empirical law；运行任何 DE 或 decoder；加样本或 rerun V32；
tuning（含事后调 bin/threshold/seed）；用新 seeds 补救不一致结果；启动 corrected
matched-B1 / NB-Polar 实验；写 qualification/promotion 措辞；修改 durable memory /
archive；push；清理用户 untracked 文件；修改 AGENTS.md；触碰 sibling checkout；
遇到 requirement ambiguity 时不停下来猜测（必须 STOP 上报）。

每处 `ponytail:` 简化须注明 ceiling 与升级路径（例如：MC 条件均值仅非命中样本——
ceiling 是它不是完整期望；升级路径是显式分母模型，本变更明确不做）。
