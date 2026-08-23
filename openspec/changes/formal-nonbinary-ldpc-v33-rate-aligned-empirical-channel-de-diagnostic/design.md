# Design: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW**

## §1 Input Bindings（7 行，全部只读；distrust 旧 terminal 惯例沿用）

| # | 绑定 | 路径/键 | 用途 |
|---|---|---|---|
| R1 | V25 train counts | `nbldpc_v25_20260818/run_04/channel_counts.npz` 键 `{sid}_N_ab_train_N_ab_train`（逐字，含重复后缀） | DE channel construction 唯一数据源 |
| R2 | V25 summary/split | `channel_summary.json`（raw_ser 三源逐字）、`split_manifest.json` | raw_ser 恒等校验；train/holdout 边界声明 |
| R3 | V31 manifest | `RUN_MANIFEST.json configs["1024"].sources[].{H.L1,H.L2,m1,m2,m_total,leak_total_bits,f_total}` | 层率与分配恒等校验 |
| R4 | V31 matrix audits | `matrix_audits.json` packet_id `m1_16_n1024_n1024\|QC-cyclic-projective`、L1 shape [16,1024] | packet 恒等 |
| R5 | V31 registry | `m1_registry.json registered_calls`（allocation `m1_16_n1024` 过滤） | 层率表逐字核对 |
| R6 | V26 历史 | `gate.json`/`best_passing_f`/design_constants | 只读对照（不可外推） |
| — | 代码事实 | harness L555–564（Q_B1 定义，仅作历史引用）；V26 sampler L10–13 | D3/claim 引用 |

stage-0 校验失败 → STOP。**validation/holdout 数据永不进入 channel construction。**

## §2 DE 计算管线（per call）

call = (source s, layer i, seed k)。固定顺序枚举：
`1M/L1/33101 … 2M/L2/33105`（source 外层、layer 中层、seed 内层，均升序），共 30 calls。

1. 由 N_ab 构造 P(A,B)=N_ab/total 与层条件总体（F03：U1=A>>5、U2=A&31；
   L1: P(U1|B)；L2 true-predecessor-conditioned: P(U2|B,U1)）。
2. R_i(s)=1−m_i(s)/1024；ρ_i=make_rho(R_i(s), lambda={2:1})。
3. 以 PCG64(seed=k) 初始化 MC-DE：n_samples=2000/迭代、max_iter=200、
   entropy_tol=0.01 bits/symbol、streak=20。
4. 判敛：连续 streak 次迭代层互信息增量 ≥ −entropy_tol 且轨迹稳定 ⇒ PASS(达到
   streak)；运行至 max_iter 未达 streak ⇒ FAIL（含有限振荡）；过程中出现
   NaN/Inf/负概率/归一化失败/异常 ⇒ INCONCLUSIVE(对应 reason)。
5. 每 call 结束立即持久化 per-call 记录（参数、seed、迭代轨迹摘要、终态、
   reason codes），随后才进入下一 call。

## §3 零分母处理（Zero-Denominator）

正概率抽样点若命中非法 L2 conditional denominator（P(U1|B=b) 列和为 0 导致
P(U2|B,U1) 条件不可定义），该 call 立即终止：
`INCONCLUSIVE(reason="inconclusive_input_binding")`。禁止 one-hot fallback、
禁止样本级跳过、禁止以平滑/占位分布替代。

## §4 聚合与优先级（candidate）

- **call** → 如上三态 + reason codes。
- **cell=(s,i)**（5 seeds）：任一 INCONCLUSIVE ⇒ cell INCONCLUSIVE(reasons 合并)；
  全 PASS ⇒ cell PASS；否则 cell FAIL。
- **overall**：任一 cell INCONCLUSIVE ⇒ overall INCONCLUSIVE；全 cells PASS ⇒
  overall `pass_rate_aligned_empirical_de`；否则 overall
  `rate_allocation_or_ensemble_fail`。
- 优先级 INCONCLUSIVE > FAIL > PASS；未覆盖组合 → inconclusive with reasons。

## §5 输出（run_01 内）

`audit_manifest.json`（绑定 SHA256+候选矩阵+判敛参数+lifecycle 标注+Git HEAD+
implementation identity；freeze 先于计算）、`de_call_matrix.json`（30 call 记录）、
`de_cell_matrix.json/md`（6 cell 判定）、`final_state.json`（overall 终态+reasons）、
`v26_reference_readonly.json`、`operator_handoff.md`、`readonly_review.json`（R2 写入）。
collision → STOP（exit 码区分 ok/collision/blocked/inconclusive/write-guard）。

## §6 测试分层

- T0：compile/import；toy 可解通道判敛小数学；层率表/rho 构造断言；
  not_fixed_packet_de 断言；zero-denominator 触发断言；collision 拒绝；
  import 白名单（无 decoder/graph-builder/生产 DE 入口）。
- T1：绑定漂移拒绝；层率/分配篡改拒绝；判敛参数篡改拒绝（manifest 冻结）；
  zero-denominator one-hot fallback 检测；trace 不完整拒绝；out-of-root 写拒绝。
- T2：fake DE runner 全流程三通道（可解→PASS / max_iter→FAIL / NaN→INCONCLUSIVE）
  × 聚合路由；独立重算复现终态；strict replay；exact-once 顺序断言；
  collision 端到端。
- T3：真实输入只读身份核验 + protected roots 快照不变（最小集）。

全部 fresh `workspace/<id>/` basetemp + `-p no:cacheprovider`；fake DE runner 显式注入。

## §7 自主权边界

可自主：内部结构/fixture/CLI 细节/JSON 布局/测试拆分/basetemp/范围内 bug 修复。
STOP 上报：改科学问题/层率表/make_rho 参数/调用矩阵候选值（freeze 后任何改动）；
跑真实 DE（授权前）；触碰 protected roots；启动 finite-control/NB-Polar/
corrected-B1；qualification/promotion 措辞；push；改 memory/archive；
requirement ambiguity。
