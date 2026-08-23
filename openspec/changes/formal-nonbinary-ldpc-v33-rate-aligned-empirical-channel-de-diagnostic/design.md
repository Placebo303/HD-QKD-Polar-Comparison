# Design: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW**

## §1 Bindings

输入绑定以 **spec.md 的 Binding Registry R1–R7 为唯一规范表**（SHALL-BIND1）；
本文件不维护缩略副本。要点重述（规范语义见 spec）：

- 全部只读；persisted terminal distrust 惯例沿用。
- **仅使用三源 train 计数矩阵**；validation/holdout 永不进入 channel construction。
- **R5 边界**：只用于 allocation/packet identity 核对；不是 V33 finite matrix、
  不是 QC packet、不是任何 DE 输入。
- **R6 边界**：只允许读取 source ID、allocation ID、m1、m2、rate、H identity；
  **禁止继承** V31 的 seeds、f、n_samples、max_iter、tol、streak 或其他任何
  DE 参数。
- **GF(32) 身份**：`GF2mField.create(32)`，primitive polynomial = **37**
  （0b100101），polynomial basis；symbol encoding / field_id =
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`
  （与 V31 manifest 一致）。stage-0 field_id 不匹配即 STOP——V26 的边系数
  permutation 依赖具体域表示，q=32 不足以唯一确定。

### Stage-0 binding failure（冻结语义）

stage-0 任一绑定校验失败时：

```
zero DE calls（一次都不运行）
不进入任何 call/cell 聚合
overall = INCONCLUSIVE
reason ∈ {missing_input, binding_drift, field_mismatch,
          allocation_mismatch, malformed_input}   （固定枚举，固定优先级无关）
不创建伪造的 30-call 记录
```

## §2 DE 计算管线（per call）

call = (source s, layer i, seed k)。固定顺序枚举：
source 外层（1M→1p5M→2M）× layer 中层（L1→L2）× seed 内层（33101→33105 升序），
共 **30 calls**。

1. **Sampler semantics**：每次抽取自 flatten 后的 P_s(A,B)=N_ab/total
   （三源独立、永不合并）；层条件总体按 F03 构造：U1=A>>5、U2=A&31；
   L1 使用 P(U1|B)；L2 使用同一真实 A 的真实 U1 构造 P(U2|B,U1)
   （true-predecessor-conditioned）。
2. 后验按真实 layer symbol 做 GF-XOR centering：真值移至 index 0（V26 误差域
   约定）；PCG64(seed=k) 固定 draw order。
3. m_i 取绑定值（L1: m1=16；L2: m2 per source）；R_i(s)=1−m_i/1024；
   ρ_i=make_rho(R_i(s), lambda={2:1})；n_samples=2000/迭代；max_iter=200。

### 步骤 4 —— 机械判敛判据（唯一判据）

MC-DE population 的总体平均分类熵，与 V26 `mean_bits_entropy(c2v, q)` 同义：

```
H_t = mean_bits_entropy(c2v_t, q)
    = (1/M) · Σ_{j=1..M} H( p_{t,j} )                                [bits/symbol]

H(p_{t,j}) = Σ_{x=0..q−1} − p_{t,j}(x) · log2( p_{t,j}(x) )
M = c2v_t.shape[0] = n_samples = 2000      （population rows）
```

**M 是 MC-DE population rows 数（2000），不是块分配长 n=1024。**
p_{t,j}(x) 为第 t 次迭代时 population row j 在符号 x 上的概率分布
（q=32），H(·) 为该分布的分类熵。

- call **PASS** 当且仅当：全程概率有效（无 NaN/Inf/负概率/归一化失败）
  且存在连续 **streak=20** 次迭代满足 **H_t < 0.01 bits/symbol**；
- 有效运行至 **max_iter=200** 仍未满足（**包括有限振荡**）⇒ **FAIL**；
- 计算过程中出现 NaN/Inf/负概率/归一化失败/异常 ⇒ INCONCLUSIVE(对应 reason)。

不使用"互信息增量"、不使用任何未定义的"轨迹稳定"措辞。正概率抽样点命中非法
条件分母 ⇒ INCONCLUSIVE(reason=inconclusive_input_binding)，禁止 one-hot
fallback（§3）。

5. 每 call 结束立即持久化 per-call 记录（参数、seed、逐迭代 H_t 轨迹、终态、
   reason codes），随后才进入下一 call。

## §3 零分母处理（Zero-Denominator）

正概率抽样点若命中非法 L2 conditional denominator（P(U1|B=b) 列和为 0 导致
P(U2|B,U1) 条件不可定义），该 call 立即终止：
`INCONCLUSIVE(reason="inconclusive_input_binding")`。禁止 one-hot fallback、
禁止样本级跳过、禁止以平滑/占位分布替代。

## §4 Official Run Lifecycle 与写根规则（fix B4/C6）

一次正式 execute 的入口顺序：

```
execute 入口：run_01 已存在 ⇒ collision STOP（exit 码区分）
否则 mkdir run_01
→ 写 pre-execution manifest（绑定 SHA256 + 候选矩阵转正为冻结值 + 判敛参数
   + lifecycle 标注 + git HEAD + implementation identity）
→ 按固定顺序执行 30 calls（每 call 持久化后进入下一 call）
→ cell/overall 聚合 → final_state.json
```

同一次 execute 内刚创建的 root 不被自身后续阶段判为 collision。

**写根规则（统一措辞）**：
- production execute 只写 official run_01；
- fake/test-only 只写 fresh workspace root（`workspace/<fresh-id>/`），绝不创建
  official run_01；
- verify 子命令默认只读；
- ER1 仅允许在 official run_01 内新增 `readonly_review.json` 一个文件。

聚合（candidate）：cell=(s,i) 任一 INCONCLUSIVE ⇒ INCONCLUSIVE(reasons 合并)；
全 PASS ⇒ PASS；否则 FAIL。overall：任一 cell INCONCLUSIVE ⇒ INCONCLUSIVE；
全 cells PASS ⇒ `pass_rate_aligned_empirical_de`；否则
`rate_allocation_or_ensemble_fail`。优先级 INCONCLUSIVE > FAIL > PASS；
未覆盖组合 → inconclusive with reasons。

## §5 输出（run_01 内）

`audit_manifest.json`（pre-execution）、`de_call_matrix.json`（30 call 记录）、
`de_cell_matrix.json/md`（6 cell 判定）、`final_state.json`（overall 终态+reasons）、
`v26_reference_readonly.json`（R7 对照）、`readonly_review.json`（ER1 写入）、
`operator_handoff.md`（closeout）。exit 码区分 ok/collision/blocked/
inconclusive/write-guard。

## §6 测试分层

- T0：compile/import；toy 可解通道判敛小数学；**M≠n toy：构造
  c2v_t.shape[0]=M≠1024 的 population，断言 H_t 按 M 求均值**；层率表/rho 构造
  断言；not_fixed_packet_de 断言；zero-denominator 触发断言；collision 拒绝；
  import 白名单（无 decoder/graph-builder/生产 DE 入口）。
- T1：五类 stage-0 reason 各至少一例（missing_input/binding_drift/field_mismatch/
  allocation_mismatch/malformed_input）且均满足 zero-DE-calls + 无伪造 call 记录；
  层率/allocation 篡改拒绝；判敛参数篡改拒绝（manifest 冻结）；
  zero-denominator one-hot fallback 检测；trace 不完整拒绝；out-of-root 写拒绝；
  official-root 创建守卫。
- T2：fake DE runner 全流程三通道（可解→PASS / max_iter 含有限振荡→FAIL /
  NaN→INCONCLUSIVE）× 聚合路由；独立重算复现终态；strict replay；exact-once
  顺序断言；同 execute 内后续阶段不重复触发 collision 断言。
- T3：真实输入只读 binding/identity 核验（R1–R7 存在性/SHA256/字面值）+
  protected roots pre/post unchanged；**不调用真实 DE**。

全部测试仅写 fresh `workspace/<id>/` basetemp + `-p no:cacheprovider`；fake DE
runner 显式注入。

## §7 自主权边界

可自主：内部结构/fixture/CLI 细节/JSON 布局/测试拆分/basetemp/范围内 bug 修复。
STOP 上报：改科学问题/层率表/make_rho 参数/调用矩阵候选值（freeze 后任何改动）；
跑真实 DE（授权前）；触碰 protected roots；启动 finite-control/NB-Polar/
corrected-B1；qualification/promotion 措辞；push；改 memory/archive；
requirement ambiguity。
