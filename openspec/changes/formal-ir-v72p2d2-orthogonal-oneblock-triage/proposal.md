# V72P2D2 正交单块分诊计划候选 — Proposal (PLAN_CANDIDATE, 未接受, 不授权执行)

- Change: `formal-ir-v72p2d2-orthogonal-oneblock-triage`
- Date: 2026-09-04. Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`.
- 本文仅为计划候选。不是 `PLAN_ACCEPTED`,不是实现授权,不是 decoder 授权,
  不是 scientific promotion 记录。任何 L/I/P、interleaver、mask BP、GF32 对照
  均需新计划独立 review 与明确执行授权后方可进行。
- 约束(本变更内固化):只允许新增 5 个文件(本目录 4 个 + `docs/research_cycles/V72P2D2-TRIAGE/PLAN_CANDIDATE.md`);
  禁实现代码、禁运行 decoder、禁读 raw/parquet、禁真实执行、禁建结果目录;
  不改 V72P1/V72P2/D1 已接受代码、结果、`OpenSpec`、`cycle_state.yaml`、memory;
  禁写 `PLAN_ACCEPTED`/授予执行。

## Goal

在单个非新鲜诊断块上,用一次性的四臂对照区分当前 binary flooding 失败的三个正交因素,
不预设优胜者:

- 科学问题(直接引用已验证观测,不重新计算):单块 binary flooding 候选全 ckpt 逐 bit 等于 Bob、
  APP 约 0.8、单边 c2v 约 0.025、A/B 均 `LADDER_EXHAUSTED`。
  具体锚点见 `docs/research_cycles/V72P2D1-PARITY/`:
  `RESULT_SUMMARY.md`(A 334 iters / B 321 iters, bit 3100 / sym 620, 72 ckpt 全候选-vs-Bob 0,
  APP max 约 0.788–0.8004)、`CORRIGENDUM.md`(NOT_RECORDED 清单)、`OFFLINE_EVIDENCE.md`、
  `ALGORITHM_ROUTE_RESEARCH.md` §3(静态 dataflow 审查:弱消息固定点为 INFERENCE,非已证根因)。
- 一次单块正交区分 L 调度 / I degree-role 对齐 / P prior,不扩大到九块,不写 FER/SKR/信息极限。

## Non-Goals

- 不重跑 D1 Arm A(基线复用,禁重跑);不做九块确认/FER/SKR/信息极限/方法定级/推广。
- 不调参、不混合三臂(每臂只变一个因素)、不事后调参、不重选 M2 参数。
- 不重构 `v72p1_soft_joint_adapter.py`;不修复除接口二选一之外的任何 adapter 逻辑。
- 不做 grouped-symbol mask BP 实现与 GF32 对照(仅描述后继,见 design §8)。
- 不写三臂必胜;M2 VAL CE 低不得直接推断 decoder 一定改善(见 §5 INFERENCE)。
- Ponytail lite 禁止:框架/插件/事件总线/缓存/锁/retry/checksum(见 AGENTS.md §5.7)。

## Impact Scope

- 允许新增(本变更,共 5 个,唯一精确清单):
  1. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/proposal.md`(本文件)
  2. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/design.md`
  3. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/tasks.md`
  4. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/specs/spec.md`
  5. `docs/research_cycles/V72P2D2-TRIAGE/PLAN_CANDIDATE.md`
- 未来实现(另走 Plan/Implementation/Pre-EXECUTE/Pre-RESULT,本次不授权)的新文件上限 5 个、
  能合一不拆(详见 design §9):新算法模块 + CLI/runner + focused test + 小 config/fixture 各至多其一,
  合并优先,不建框架。
- 冻结目录零改动:`src/`,`experiments/`,`tools/`,`results/`,
  `comparison_bench/outputs_comparison/` 现有输出,D1 四文件,
  V72P1/V72P2/D1 的 `cycle_state.yaml`、已接受 `OpenSpec`、memory。
- 未来执行输出(如另行授权)新根恰四文件(manifest/results/table/report),禁覆盖既有输出,禁建 `run_01`
  (本计划不建任何结果目录)。

## 冻结(摘要,完整定义见 design + spec)

- 四臂(同 block/ladder/edge 预算/clip/tol/验证泄漏口径):
  - 基线 A:复用 D1 Arm A 已记录事实,禁重跑。
  - L:原 H + M0 prior + 真正 layered,只变调度(11 点数学合同,design §3)。
  - I:deterministic degree-balanced full-column interleaver + M0 prior + flooding
    (全 10240 列;前 1204 每 symbol 1 或 2 个;其余填满 10 bit;唯一算法/tie-break/seed;
    old→物理 `sym*10+bit` 方向;syndrome 对映射后 H 与原物理 Alice 算;prior 对物理 symbol;
    保持 shape 9036x10240/nnz49620/row-col degree multiset/rank/prefix;
    试算 41/47/65、95/95 仅参考非门槛)。
  - P:原 H + 冻结 V70R1 M2 laplace(`mu=0.0`,`scale=0.2714417616594907`,`eps=0.562251256281407`,
    Q=1024,`shape ∝ Σ_period exp(-|disp+period*Q-mu|/scale)`,`K=(1-eps)*shape+eps/Q`,
    `P=K[(a-b) mod Q]`,prior 自然 log、CE log2、行归一、现有 floor 1e-300,不读 Alice、不重选;
    VAL CE 6.7871 仅历史,允许变差)。
- 接口二选一:A(推荐)不调用列 deferred bug 路径,或 B 必须调用则最小修复 + 回归,禁重构 adapter。
  Bug 位置:`comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py`
  `run_incremental_decoder` 末尾已算 `variable_to_check_final` 但返回旧 `variable_to_check_active`
  填充的 `variable_to_check_full`(见 `ALGORITHM_ROUTE_RESEARCH.md` §3;D1 用 `run_decoder`,
  与本次 D1 失败无关)。
- 诊断聚合每 ckpt 最少量(完整清单见 design §5);明确单边 `max|c2v| ≠ max_v|Σ|`,
  收敛 ≠ 正确,`candidate==Bob` 直接比,O1 POSTHOC 辅助,不提交敏感数组。
- T0/T1-L/T1-I/T1-P/T1-METRICS/T2 矩阵完整冻结见 tasks.md;数学合同无法冻结则 BLOCKED 列未决,
  禁 TBD 猜测。

## Acceptance Criteria

- AC1:5 文件齐且仅 5 文件新增;无实现代码、无 decoder 运行、无 raw/parquet 读取、
  无结果目录创建、无既有文件改动(含 `cycle_state.yaml`/memory/`OpenSpec` 已接受部分)。
- AC2:四臂正交性文本可审:每臂“仅改变的因素”唯一且与其余臂不混合;基线 A 明确禁重跑。
- AC3:Layered 11 点合同逐条可证或明确标 BLOCKED(禁猜测);证不出真用最新消息而
  禁 row-loop 包 flooding 冒充(见 design §3 第 11 点)。
- AC4:I 非门槛数值(41/47/65、95/95)明确标“参考非门槛”;P 的 VAL CE 明确标“历史非门槛,
  允许变差”;无 M2 优胜/因果/推广断言。
- AC5:未来执行合同含同 D1 块非新鲜、A 不重跑、L/I/P 各一次、无 rerun、独立 c2v、
  新根恰四文件、预算数值依据,并声明另走 Plan/Implementation/Pre-EXECUTE/Pre-RESULT,
  本计划不授权。
- AC6:预注册判别与三无-escape 停止规则完整(禁 FER/SKR/因果/M2 优胜/推广)。
- AC7:文献 DOI 与历史边界齐全且措辞正确(见下)。

## 文献 DOI 与历史边界(措辞冻结)

- PEG: https://doi.org/10.1109/TIT.2004.839541 (重构图基础候选,不保证 finite-length 成功)。
- Layered: https://doi.org/10.1109/SIPS.2004.1363033 (调度改善 ≠ capacity/FER 突破)。
- Spatial coupling: https://arxiv.org/abs/1001.1826 (需针对性 DE,有耦合/边界/有限长代价)。
- Non-binary LDPC: https://arxiv.org/abs/2305.08631 (保留符号相关性需正确 full-vector 语义)。
- 历史边界:旧 GF32 主候选相关同域真实数据 V54 development 43/45、V64 full-symbol
  verification 22/24、undetected 0(实际成功证据,不自动转移到当前 binary mother);
  V5-C2 384/384 另一条已冻结域/方法边界仅历史背景;V67–V72P1 为容量/kernel/synthetic
  qualification/接口/诊断证据,不能冒充真实纠错成功;V72P0 tiny-tree 仅验证小树语义。
  不写三臂必胜。

## Tasks(指向 tasks.md)

- T0 编译/导入/结构/小数学(无 decoder、无 parquet)。
- T1-L layered 合同单元;T1-I interleaver 确定性;T1-P M2 prior 冻结;T1-METRICS 诊断聚合。
- T2 矩阵完整冻结(fake tiny + 严格口径,无真实执行)。
- 计划冻结自检(本变更内,无代码运行):5 文件清单、禁项、措辞检查。
