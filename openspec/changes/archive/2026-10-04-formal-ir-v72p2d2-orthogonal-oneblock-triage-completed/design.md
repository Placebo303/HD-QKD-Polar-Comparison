# V72P2D2 正交单块分诊设计

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本设计绑定 base
`e094f7e548380db4bfcbc1fe73472e670c32379a`、分支
`formal-ir-v72p1-addendum-clean`。它只描述一次合规实现与诊断，不修改 V72P1、
V72P2 或 D1，不授权实现、decoder、真实数据、parquet 或结果输出。

本设计中的 `base_sha`、`accepted_plan_sha`、`implementation_sha` 只表示
AGENTS 要求的 Git commit/计划/实现版本绑定，不承担数据或 artifact 内容校验。
manifest 不含数据或 artifact 内容摘要、签名或其他校验字段。
Ponytail lite：算法模块、runner 和 focused test 各一个；不用框架、插件、事件
总线、缓存、锁、retry 或完整消息持久化。

## 1. 共同数据、数值和预算

诊断只使用 D1 已固定的同一非新鲜块：session
`20260123_1M_600k_0dB` 的 `VAL1726..1729`，四帧连续组成一个 1024-symbol
block。规划阶段不读取其 raw/parquet 内容。mother 为
`H_old.shape=(9036,10240)`、`nnz=49620`，check-degree
`{4:1,5:4594,6:4441}`，degree-2 列 `9035`。checkpoint ladder 是
`range(160,8993,128) + [9032,9036]`，共 72 点。

共同数值为 `float64`、`llr_clip=20.0`、`convergence_tol=1e-6`。每个 checkpoint
最多 10 次完整更新，每个新臂最多 720 次完整更新；不足一次完整更新时不启动
partial update。L 的一次完整更新定义为一个 active-row sweep；I/P 的一次完整
更新定义为一次 flooding iteration，均要求每个 active edge 恰更新一次。

一个 factor target evaluation 严格定义为计算一个
`f2b[sym,b]` 的完整 `Q=1024` 状态 marginal。核心 factor work 只统计实际
decoder update evaluations。核心 `local_factor_target_updates` 与
`state_evaluations` 固定为：L 每个 row 增加
`10*distinct_affected_symbols`，I/P 每个实际 flooding iteration 增加
`1024*10=10240`，并满足
`state_evaluations=1024*local_factor_target_updates`。实际完整更新数以 decoder
返回值为准，不能用请求的 max 值代替。

非核心阶段逐项计数：每臂一次完整 L0 `[1024,10]` batch 严格只计算一次，固定为
`diagnostic_L0_target_updates=10240`，并缓存供后续 checkpoint metrics 只读；任何
重复计算都另加 `10240` diagnostic targets，且 T2 失败。L 的每个实际 checkpoint
强制从 active state 完整 rebuild f2b，固定计 `10240` 个
`diagnostic_checkpoint_rebuild_target_updates`，不允许 cache/recompute 二选一；
L 的 final readout 复用最后状态，计 0。I/P 的每一次实际 `run_decoder` 调用末尾
由 adapter 重算完整 `factor_to_bit` batch，故增加
`diagnostic_final_readout_target_updates=10240`，对应 `10240*1024` state
evaluations；I/P 不得写成 final readout=0。这些阶段都不混入核心，且每臂输出各
阶段计数与总计。成本 preflight 为保守上界固定使用
`D=10240*(1+72)` diagnostic targets（L0 加 72 次完整 rebuild，L final readout
为 0）；实际结果仍必须报告真实阶段计数。

L 的结构上界为 active-row 总和 `338388`、每 row 至多 6 个 distinct symbols、
10 sweeps，即至多 `203032800` 个核心 factor targets 和
`207905587200` 个核心 state evaluations；该值仅为结构上界，不是实测成本证据。

对每个新臂独立初始化 c2v 为零，checkpoint 间携带该臂已激活边；新边置零。
L/I/P 不共享可变消息。A 不运行，仅读取 D1 已接受的 Arm A 共同指标。

无 tag 诊断固定 `tag_bits=0`、`tag_bits_published=0`、`tag_ok=NOT_APPLICABLE`；
诊断中不生成或处理 tag。每个 checkpoint 的核心判据只有
`syndrome_satisfied = finite && candidate syndrome 与公开 syndrome prefix 一致`。
该判据只作描述性诊断，不构成协议接受或验证成功。首次满足只记录
`first_syndrome_satisfied_ckpt`，不停止 ladder。arm 结束时只取最后一个已完成
checkpoint 的 candidate，并在同一个 checkpoint prefix 上计算
`final_syndrome_satisfied`；没有 candidate 时为 null。oracle 只在整个 ladder、
预算或异常结束后比较该 final candidate，形成 `final_oracle_exact`。不得把
first checkpoint 的 syndrome 与 final candidate 的 oracle 混合。最终分类为
`diagnostic_exact=final_syndrome_satisfied && final_oracle_exact` 与
`syndrome_collision_wrong=final_syndrome_satisfied && !final_oracle_exact`，仅作
描述性事后诊断。

## 2. 四臂正交性

| arm | H/物理坐标 | prior | 更新 |
|---|---|---|---|
| A | D1 已存原 H 结果 | D1 M0 | D1 已存 flooding 结果 |
| L | 原 H | M0 | `run_layered_decoder` |
| I | `H_I`，全列 degree-balanced interleaver | M0 | 既有 `run_decoder` flooding |
| P | 原 H | V70R1 M2 | 既有 `run_decoder` flooding |

M0 使用 D1 记录的 `lambda=221.22162910704503` 和
`CE_CAL_CV=7.135005172802673`。L/I/P 的 block、ladder、更新预算、clip、
tolerance 和 syndrome-only 诊断相同。不得合成 layered+I、I+M2 或 layered+M2
的臂。

## 3. L：真正的 row-serial layered decoder

### 3.1 状态和消息

对 active 图维护 `c2v[e]`、`b2f[v]`、`f2b[v]` 和未裁剪
`APP_raw[v]`，其中

```text
b2f[v] = sum(c2v[e] for e incident to v)
f2b[sym,b] = local_factor_extrinsic(
    prior_logp[sym,:], b2f[sym,other_bits_excluding_b])
APP_raw[v] = f2b[v] + b2f[v]
```

prior 只在 local factor 注入一次。`APP_clipped=clip(APP_raw,-20,20)` 只用于
诊断、输出和 hard sign；它不能进入 v2c。每个 v2c 必须是

```text
v2c[e=(v,c)] = f2b[v] + b2f[v] - c2v_old[e]
```

不得写成 `APP_clipped-c2v`，也不得用任何已裁剪 APP 作为内部状态。

### 3.2 checkpoint state rebuild

checkpoint 从上一 checkpoint 的 active c2v 前缀复制旧边，新激活边写零。
然后用完整 active c2v 重建 `b2f`，对每个 symbol 的 10 个 bit 运行
`local_factor_extrinsic` 重建 `f2b`，最后得到 `APP_raw`。这个 rebuild 在首个
sweep 前完成，并由单元测试验证；它不跨 block 携带状态。

### 3.3 一个 layered sweep 的严格顺序

设当前 active rows 为 `c=0..r-1`，第 `c` 行 CSR 边按原 edge 顺序排列，
`d_c` 为其度数，`S_c` 为目标 syndrome。

1. 进入 row `c` 时保存该行全部旧 `c2v` 的 row-start snapshot；row 内任何
   edge 都只能从这个 snapshot 及当前已提交的其他 rows 计算，不能看到同一 row
   已经写入的新 c2v。
2. 对该行每条边先计算全部 `v2c[e] = f2b[v] + b2f[v] -
   c2v_row_start[e]`，然后才计算任何新的 c2v。同一 row 的 v2c 不受 edge
   遍历顺序污染。
3. 对每条边同时使用该行全部 v2c 计算新 c2v：

   ```text
   sign(c,d) = (-1) ** (S_c + (d mod 2))
   p_e = sign(c,d) * product(tanh(v2c[e']/2)
                              for e' in row(c) if e' != e)
   c2v_new[e] = 2*atanh(clip(p_e, -1+1e-12, 1-1e-12))
   c2v_new[e] = clip(c2v_new[e], -20, 20)
   ```

   `S_c` 和 check-degree parity 必须显式进入 sign；syndrome 0/1、度 1/2/3 的
   sign 均由同一公式覆盖。
4. 只有整行新 c2v 全部计算完后才一次性 commit。对每个受影响变量，以新旧
   c2v 差更新 `b2f`；对每个受影响 symbol 重算全部 10 个 `f2b`，每个目标 bit
   排除自己的 b2f 项；随后更新该 symbol 全部 10 个 `APP_raw=f2b+b2f`。
5. 继续下一 row。前面已经 commit 的 rows 对后续 rows 可见；当前 row 内的
   v2c/c2v 则始终使用 row-start snapshot。
6. 一个完整 sweep 完成后，residual 是 sweep 开始的 active c2v snapshot 与
   sweep 结束 active c2v 的全 active-edge `max(abs(delta))`。`sweeps` 计完整
   sweep，`edge_updates` 计写入的 c2v 边数。
7. residual 小于 tolerance 只设置 `converged=true`，不改变 syndrome-only
   诊断流程；当前 checkpoint 未满足 syndrome 时按预算继续。

### 3.4 L API 与公平计量

新算法模块必须提供并只让 L 使用：

```python
run_layered_decoder(
    prior_logp, syndrome_target, indptr, indices,
    max_sweeps, warm_start_c2v
)
```

`warm_start_c2v.shape` 必须严格为 `(len(indices),)`；首 checkpoint 传全零数组，
后续 checkpoint 只传上一 checkpoint 的 active 前缀并将新增边置零。返回值必须
完整包含 `bit_to_factor`、`factor_to_bit`、`variable_to_check`、
`check_to_variable`、`app_llr`、`hard_bits`、`hard_symbols`、
`syndrome_observed`、`finite`、`residuals`、`converged`、`max_llr` 以及完整的
核心/诊断 factor 计数，供 runner 机械复算；runner 不把完整消息数组写入结果。
I/P 只调用现有 `run_decoder`，不调用 `run_incremental_decoder`。后者的
`variable_to_check_final` stale-return bug 作为独立 deferred bug，本周期不碰
adapter。

每个完整更新的公平字段是：一次 c2v edge update 写一个新 c2v，一次 v2c
evaluation 计算一个 v2c。一个 factor target evaluation 是一个
`f2b[sym,b]` over `Q=1024` states。核心
`local_factor_target_updates` 只含实际 decoder updates：L 每个 row 增加
`10*distinct_affected_symbols`，所以每个 sweep 是所有 active rows 的该值之和；
I/P 每个实际 flooding iteration 增加 `1024*10=10240`。核心
`state_evaluations` 始终等于 `1024*local_factor_target_updates`，不能用请求
的 max 值代替实际更新数。

非核心计数固定按阶段输出：L0 full `[1024,10]` batch 每臂严格只算一次，固定为
`diagnostic_L0_target_updates=10240`，并缓存；后续 checkpoint 的 L0 metrics 只能
读缓存，若重复计算则另加 `10240` diagnostic targets 并使 T2 失败。L 的每个
实际 checkpoint 都必须从 active c2v 形成 b2f 后完整 rebuild f2b，固定计入
`diagnostic_checkpoint_rebuild_target_updates +=10240`，不得选择 cache 路径；
L 的 final readout 复用最后状态，计 0。I/P 的每次实际 `run_decoder` 调用末尾
adapter 固定重算完整 `factor_to_bit` batch，计入
`diagnostic_final_readout_target_updates +=10240` 和
`10240*1024` diagnostic state evaluations；不得写成 I/P final readout=0。三项
相加为 `diagnostic_factor_target_updates`，并满足
`diagnostic_state_evaluations=1024*diagnostic_factor_target_updates`；纯 readout
次数另列 `diagnostic_readout_evaluations`，不混入任何 factor targets。I/P decoder
内 factor batches 全部属于 core，runner 只额外计 L0=10240 与每次调用末尾的
diagnostic final-readout batch。L 的 factor work 可能多于 I/P，必须单独报告，不能
用 edge/sweep 预算声称总计算相等。

预注册 ladder 的 active-row 总和为 `338388`。按每 row 至多 6 个 distinct
symbols、10 sweeps 计算，L 的结构上界为
`338388*6*10*10=203032800` 个核心 factor targets，及
`203032800*1024=207905587200` 个核心 state evaluations。这个上界不等于
实际计数，也不构成性能证据。

## 4. I：唯一 full-column degree-balanced interleaver

实现使用原 H 的 `degree = bincount(H_old.indices, minlength=10240)`，固定高
连接集合 `old_cols=0..1203`。先按 `(-degree[old_col], old_col)` 排序。维护
`info_count[sym]` 和 `info_load[sym]`，初值均为零。依次处理排序后的每个高连接
old column，选择满足 `info_count[sym] < 2` 且字典序最小的
`(info_load[sym], info_count[sym], sym)`；把该列放入该 symbol 当前的
`physical_bit=info_count[sym]`，即物理列 `10*sym+physical_bit`，然后增加
`info_count` 并把该列 degree 加入 `info_load`。

剩余物理 slots 按 `(symbol_id, bit_id)` 升序排列。固定
`rng=np.random.default_rng(20260902)`，对 old parity columns `1204..10239`
做一次 permutation，按该顺序依次填入剩余 slots。物理 bit 顺序为 LSB bit 0。
由此得到唯一 `old_to_phys`；同时构造并测试 `phys_to_old` 逆映射。

代数方向固定为：

```text
H_I[:, old_to_phys[j]] = H_old[:, j]
x_old[j] = x_phys[old_to_phys[j]]
H_I @ x_phys == H_old @ x_old (mod 2)
```

syndrome 使用映射后的 H_I 与物理 Alice bits，prior 使用物理 Bob symbol，
candidate-vs-Bob 比较也在物理 bit 坐标。实现须验证全列 bijection、每 symbol
10 个物理 bit、前 1204 列每 symbol 1 或 2 个，以及 shape、nnz、row-degree
multiset、column-degree multiset、rank、prefix nesting 不变。symbol 总边数和
mixed/pure cycle 统计由实现重算留痕；静态参考 `41/47/65`、`95/95` 不是门槛。

## 5. P：冻结 M2 prior

P 的 M2 参数直接采用 V70R1 1M CAL-only 结果：
`family=laplace`、`mu=0.0`、`scale=0.2714417616594907`、
`eps=0.562251256281407`、`Q=1024`。对 `d=0..1023` 使用

```text
signed_disp[d] = ((d + Q//2) mod Q) - Q//2
shape[d] = sum(exp(-abs(signed_disp[d] + period*Q - mu)/scale)
                for period in (-1,0,1))
shape = shape / sum(shape)
K = (1-eps)*shape + eps/Q
K = K / sum(K)
P(a|b) = K[(a-b) mod Q]
prior_logp[sym,a] = log(max(K[(a-int(bob_phys[sym])) mod Q], 1e-300))
```

`K` 先按公式正常归一，不能先对 K floor 或 floor 后重新归一；`1e-300` 只
保护 log，当前 `eps>0` 理论上不会触发。builder 只接收 `bob_phys` 和冻结
parameters，不能接 Alice。BP 输入是自然 log，CE 仅以 log2 报告。B_BITS
沿用 LSB bit 0。M2 历史 VAL CE `6.787126437359054` 不是性能门槛，M2 变差
也是合法结果。

I/P 的 `actual_iterations` 定义为既有 `run_decoder` 返回的 `len(residuals)`，而
不是 `max_iter`；每个实际 flooding iteration 增加
`local_factor_target_updates += 1024*10`，并同步增加
`state_evaluations += 1024*10240`。每次实际 `run_decoder` 调用末尾 adapter 的
完整 `factor_to_bit` batch 另增加
`diagnostic_final_readout_target_updates +=10240`，不得漏计或归入 core；runner
每臂 L0 只增加一次 `diagnostic_L0_target_updates=10240`。L 的每个实际 checkpoint
另增加一次完整 rebuild `diagnostic_checkpoint_rebuild_target_updates=10240`，L
final readout 复用最后状态为 0；L0 后续 metrics 只读缓存，重复 L0 重算另加
10240 且 T2 失败。所有诊断阶段都只计入对应 diagnostic 字段。

M2 的 synthetic 检查必须分别断言 K 与每个条件分布 P 均 finite、strictly
positive 且和为 1；`prior_logp` 必须 finite，并且
`exp(prior_logp[sym,:])` 与相应 P 行逐元素相等且和为 1。log-probability 可以为
负值，禁止以“logp positive”作为测试条件。

## 6. 每 checkpoint 标量诊断

固定 quantiles 为
`q=[0,0.01,0.05,0.25,0.5,0.75,0.95,0.99,1]`。固定
`zero_tol=1e-15`，sign 为 `-1/0/+1`，分别对应 `x<-tol`、
`abs(x)<=tol`、`x>tol`。

每个 L/I/P checkpoint 在首 sweep 前记录 pre，在最后完整 sweep 后记录 post：

- `L0` 是 `local_factor_extrinsic(prior_row, zeros(10), target_bit)` 的
  prior-only bit LLR，绝不是 APP。
- `F_pre/post` 是 factor-to-bit；`S_pre/post[v]` 是每变量 incident c2v
  的 signed sum；`A_raw_pre/post=F+S`。
- 对 L0、F、S、A_raw、`delta_app=A_raw_post-A_raw_pre`，各保存
  `signed_quantiles`、`abs_quantiles`、`max_abs`、`zero_count`。
- 保存 `sign(L0)->sign(F_post)` 和 `sign(F_post)->sign(A_raw_post)` 的
  3x3 transition counts；它们相对每个 checkpoint 的 L0，不相对首 checkpoint。
- 保存 candidate syndrome violation、candidate-vs-Bob bit/symbol flips、
  residual、sweeps、edge_updates、finite、clip counts，以及
  `syndrome_satisfied`、`tag_bits=0`、`tag_ok=NOT_APPLICABLE`。同时报告该
  checkpoint 的核心 target/state 增量与 diagnostic target/state/readout 增量。
  oracle 字段在 checkpoint 层为 null，并附
  `not_recorded_reason=oracle_runs_after_arm_end`。
- violation 固定为
  `weight(((H_arm[:r] @ hard_bits) % 2) XOR syndrome_target[:r])`。
- `c2v_at_clip_count` 统计 `abs(c2v)>=20-1e-12`，`f2b_at_clip_count` 同
  口径；`app_preclip_exceed_count` 统计 `abs(A_raw)>20`。APP 输出裁到 20，
  但不宣称保存了 factor preclip 值。

必须把单边 `max(abs(c2v))` 与 `max_v(abs(sum incident c2v))` 分开。不得用
residual 代表正确，不得由相同错误数推断 candidate==Bob；candidate-vs-Bob
必须直接比较。D1 的 O1 只能标为 `POSTHOC_RECONSTRUCTED`，不是本次原始诊断。
A 只允许与 D1 已存共同指标比较：`outcome`、`iterations`、
`candidate-vs-Bob`、D1 APP、D1 single-edge c2v，以及 O1 的
`POSTHOC_RECONSTRUCTED violation`；L/I/P 新增的 F/S/A/L0 等指标在 A 中不作
定量差分，也不从旧 artifact 补造。

arm 结束后只报告最后已完成 checkpoint 的
`final_checkpoint_rows`、`final_syndrome_satisfied`、`final_oracle_exact`、
`diagnostic_exact` 和 `syndrome_collision_wrong`。其中 `final_oracle_exact` 只
比较该 final candidate 与 Alice；`first_syndrome_satisfied_ckpt` 仅为传播诊断，
不得进入最终分类。

## 7. 动态公开计费

L/I/P 各自维护独立 counterfactual 计数器：
`syndrome_rows_published`、`syndrome_bits_published`、
`tag_bits_published=0`、`control_bits_sent`、`disclosed_rows`。在当前 checkpoint
开始前发布新增 syndrome rows；只有进入下一个 checkpoint 才发送并计入 1 个
CONTINUE control bit。首次 `syndrome_satisfied` 不停止、不改变计费，也不称
协议接受。若完整 ladder 到达 9036，名义公开计费为
`9036 syndrome bits + 71 control bits = 9107 bits`；预算中断、异常和 timeout
只保留已发布计数。每个状态必须满足
`disclosed_rows == syndrome_rows_published == syndrome_bits_published`，且三者
单调不减；三臂计数不相加，不称真实 session leakage。

## 8. 真实执行状态机与输出

真实执行阶段固定为一次 invocation：prep allowance 600 s，L/I/P 各 600 s，
总墙钟上限 2400 s，peak RSS 硬上限 2 GiB。准备或输入校验失败时三臂均为
`NOT_ATTEMPTED` 并以非零返回；任一新臂发生 exception、nonfinite、RSS 超限
或 soft timeout，该臂为 `BLOCKED`，立即停止 invocation，后续臂为
`NOT_ATTEMPTED`，已生成的四臂候选 artifact 保留。普通
`LADDER_EXHAUSTED` 或达到 720 的正常终态允许继续下一个新臂。L/I/P 各运行
一次，无 rerun、无事后调参；A 不重跑。

Pre-EXECUTE 必须先运行 cost-preflight：只用真实 mother 的结构、合成
prior/syndrome 与零/非零 warm state 测 layered kernel，固定代表点
`active_rows=160,2048,4096,8192,9036`，每点恰跑 1 个完整 sweep，不运行正式三臂、
不读取 raw/parquet。令
`U_r=10*sum(distinct_affected_symbols(row) for row<r)`，每点记录实际 `U_r` 与
elapsed；`tau=max(elapsed/U_r)`，其中 elapsed 包含真实 row scheduling 与核心
kernel overhead。完整 ladder 的核心上界工作量为
`W=sum(10*sum(distinct_affected_symbols(row) for row<ck) for ck in ladder)`。
诊断投影固定为 `D=10240*(1+72)` targets（L0 加 72 次完整 rebuild，L final
readout 复用状态为 0），`tau_diag` 为代表点完整 rebuild 的最大实测
seconds/target。非核心每-checkpoint fixed overhead 用独立 timer 测量，取
`h=max(observed_noncore_overhead)`，因此不出现负数；投影为
`projected_L_wall_s=(tau*W + tau_diag*D + 72*h)*1.2`。硬门槛是
`projected_L_wall_s<=600 s`，建议 20% 余量目标为 `<=480 s`；超过 600 s 必须
`PLAN_REVISE_REQUIRED`，不得修改科学算法绕过。真实 L 超过 600 s 的状态为
`RESOURCE_BLOCKED`，不能归因于路线失败。RSS 单独按固定采样口径记录。
RSS 只采样当前进程
`psutil.Process(os.getpid()).memory_info().rss`，在 prep、每 checkpoint 后和
arm 结束采样，`peak_rss_bytes` 为这些样本最大值。

输出根固定为
`comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`，
恰有 `manifest.json`、`results.json`、`table.csv`、`report.md`。顶层至少包含：

```text
schema, cycle, base_sha, accepted_plan_sha, implementation_sha,
source_registry, session_id, block_frame_ids, non_fresh, mother_shape,
mother_nnz, checkpoint_rows, max_sweeps_per_checkpoint,
max_total_sweeps, llr_clip, convergence_tol, dtype, arm_order,
invocation_status, prep_status, cost_preflight, projected_L_wall_s,
rss_sampling, arms, claim_boundary
```

其中 `base_sha`、`accepted_plan_sha`、`implementation_sha` 仅为 Git 版本绑定，
不是 artifact/data 内容字段。每个 `arms[arm_id]` 至少包含：

```text
status, graph_id, prior_id, schedule_id, attempted_checkpoints,
stop_reason, first_syndrome_satisfied_ckpt, final_checkpoint_rows,
final_syndrome_satisfied, final_oracle_exact, diagnostic_exact,
syndrome_collision_wrong, sweeps_used, edge_updates,
local_factor_target_updates, state_evaluations,
diagnostic_L0_target_updates, diagnostic_checkpoint_rebuild_target_updates,
diagnostic_final_readout_target_updates, diagnostic_factor_target_updates,
diagnostic_state_evaluations, diagnostic_readout_evaluations, total_target_updates,
total_state_evaluations, peak_rss_bytes, accounting, checkpoint_metrics,
common_metrics, new_metric_fields, posthoc_oracle
```

`accounting` 包含 `syndrome_rows_published`、`syndrome_bits_published`、
`tag_bits_published=0`、`control_bits_sent`、`disclosed_rows` 和
`public_disclosure_bits=syndrome_bits_published+control_bits_sent`。
每个 arm 的核心计数为 `local_factor_target_updates` 与
`state_evaluations=1024*local_factor_target_updates`；阶段计数满足
`diagnostic_factor_target_updates = diagnostic_L0_target_updates +
diagnostic_checkpoint_rebuild_target_updates + diagnostic_final_readout_target_updates`
以及 `diagnostic_state_evaluations=1024*diagnostic_factor_target_updates`。
`total_target_updates=local_factor_target_updates+diagnostic_factor_target_updates`
且 `total_state_evaluations=state_evaluations+diagnostic_state_evaluations`。
每个 checkpoint 必须断言 `disclosed_rows == syndrome_rows_published ==
syndrome_bits_published`。`checkpoint_metrics` 只含第 6 节标量；`tag_ok` 固定为
`NOT_APPLICABLE`，checkpoint 的 oracle 字段为 null，最终只在 arm 结束后的
`posthoc_oracle` 中填写 `final_oracle_exact`。A 的新指标结构为
`{value: null, not_recorded_reason: "D1 baseline did not record this metric; A was not rerun"}`，
不得补造值。L/I/P 的所有新指标必须填写真实聚合结果。四个文件不得包含秘密
数组或数据/artifact 内容校验字段。

## 9. grouped-symbol mask BP 后继

只有当 L/I/P 都没有 hard-bit escape 时，下一周期才可排队 grouped-symbol mask
BP tiny exhaustive 或同块 GF32 对照。本设计不实现后继。其固定研究假设是：
每个 1024-state symbol 为一个变量，同一 check 内属于该 symbol 的 bits 合并
为 XOR mask，每个 `(check,symbol)` 传 scalar parity message，symbol-to-check
用完整 prior 对 mask parity 边缘化，check-to-symbol 仍为 binary SPA。约
41169 unique groups、约 42M state evaluations/iteration 只是数量级估算，不是
性能证据；顺序为 tiny exhaustive、small loopy synthetic、single real block。
