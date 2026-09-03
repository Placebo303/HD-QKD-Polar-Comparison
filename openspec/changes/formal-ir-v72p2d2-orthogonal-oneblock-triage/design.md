# V72P2D2 正交单块分诊设计

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本设计绑定
`e094f7e548380db4bfcbc1fe73472e670c32379a`、分支
`formal-ir-v72p1-addendum-clean`。它只描述未来一次合规实现与诊断，不修改
V72P1、V72P2 或 D1，也不授权实现、decoder、真实数据、parquet 或结果输出。

Ponytail lite：算法模块、runner 和 focused test 各一个；不用框架、插件、事件
总线、缓存、锁、retry、checksum、完整消息持久化或新的 adapter 抽象。

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

对每个新臂独立初始化 c2v 为零，checkpoint 间携带该臂已激活边；新边置零。
L/I/P 不共享可变消息。A 不运行，仅读取 D1 已接受的 Arm A 共同指标。

协议验证只沿用现有 64-bit tag 与 syndrome 语义：当前候选同时满足 finite、
`syndrome_observed == syndrome_target[:r]` 和既有 `tag_ok` 才是
`protocol_accepted`；oracle 只在结束后比较。converged 永不替代验证。

## 2. 四臂正交性

| arm | H/物理坐标 | prior | 更新 |
|---|---|---|---|
| A | D1 已存原 H 结果 | D1 M0 | D1 已存 flooding 结果 |
| L | 原 H | M0 | `run_layered_decoder` |
| I | `H_I`，全列 degree-balanced interleaver | M0 | 既有 `run_decoder` flooding |
| P | 原 H | V70R1 M2 | 既有 `run_decoder` flooding |

M0 使用 D1 记录的 `lambda=221.22162910704503` 和
`CE_CAL_CV=7.135005172802673`。L/I/P 的 block、ladder、更新预算、clip、
tolerance、验证和计费相同。不得合成 layered+I、I+M2 或 layered+M2 的臂。

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
   c2v_row_start[e]`，然后才计算任何新的 c2v。这样同一 row 的 v2c 不受 edge
   遍历顺序污染。
3. 对每条边同时使用该行全部 v2c 计算新 c2v：

   ```text
   sign(c,d) = (-1) ** (S_c + (d mod 2))
   p_e = sign(c,d) * product(tanh(v2c[e']/2)
                              for e' in row(c) if e' != e)
   c2v_new[e] = 2*atanh(clip(p_e, -1+1e-12, 1-1e-12))
   c2v_new[e] = clip(c2v_new[e], -20, 20)
   ```

   `S_c` 和 check-degree parity 必须显式进入 sign；目标 syndrome 为 0 或 1、
   度 1/2/3 的 sign 均由同一公式覆盖。
4. 只有整行新 c2v 全部计算完后才一次性 commit。对每个受影响变量，以新旧
   c2v 差更新 `b2f`；对每个受影响 symbol 重算全部 10 个 `f2b`，每个目标 bit
    排除自己的 b2f 项；随后更新该 symbol 全部 10 个 `APP_raw=f2b+b2f`。
5. 继续下一 row。前面已经 commit 的 rows 对后续 rows 可见；当前 row 内的
   v2c/c2v 则始终使用 row-start snapshot。
6. 一个完整 sweep 完成后，residual 是 sweep 开始的 active c2v snapshot 与
   sweep 结束 active c2v 的全 active-edge `max(abs(delta))`。`sweeps` 计完整
   sweep，`edge_updates` 计写入的 c2v 边数。
7. residual 小于 tolerance 只设置 `converged=true`，仍须进行 syndrome/tag
   验证。若当前 checkpoint 未验证成功，按预算继续 checkpoint。

### 3.4 L API 与公平计量

新算法模块必须提供并只让 L 使用：

```python
run_layered_decoder(
    prior_logp, syndrome_target, indptr, indices,
    max_sweeps, warm_start_c2v
)
```

返回内部 decoder 所需消息和诊断标量；runner 不把完整消息数组写入结果。
I/P 只调用现有 `run_decoder`，不调用 `run_incremental_decoder`。后者的
`variable_to_check_final` stale-return bug 作为独立 deferred bug，本周期不碰
adapter。

每个完整更新的公平字段是：一次 c2v edge update 写一个新 c2v，一次 v2c
evaluation 计算一个 v2c，一次 local-factor target update 计算一个目标 bit 的
1024-state marginal。每个完整 sweep/iteration 每个 active edge各更新一次；
记录 `local_factor_target_updates` 与
`state_evaluations=1024*local_factor_target_updates`。L 的 local-factor work
可能多于 I/P，必须单独报告，不能用 edge/sweep 预算声称总计算相等。

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
P(a|b) = K[(a-b) mod Q]
prior_logp[sym,a] = log(max(K[(a-int(bob_phys[sym])) mod Q], 1e-300))
```

`K` 先按公式正常归一，不能先对 K floor 或 floor 后重新归一；`1e-300` 只
保护 log，当前 `eps>0` 理论上不会触发。builder 只接收 `bob_phys` 和冻结
parameters，不能接 Alice。BP 输入是自然 log，CE 仅以 log2 报告。B_BITS
沿用 LSB bit 0。M2 历史 VAL CE `6.787126437359054` 不是性能门槛，M2 变差
也是合法结果。

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
  residual、sweeps、edge_updates、finite、clip counts、syndrome_ok、tag_ok、
  oracle_exact 和 undetected 状态。
- violation 固定为
  `weight(((H_arm[:r] @ hard_bits) % 2) XOR syndrome_target[:r])`。
- `c2v_at_clip_count` 统计 `abs(c2v)>=20-1e-12`，`f2b_at_clip_count` 同口径；
  `app_preclip_exceed_count` 统计 `abs(A_raw)>20`。APP 输出裁到 20，但不宣称
  保存了 factor preclip 值。

必须把单边 `max(abs(c2v))` 与 `max_v(abs(sum incident c2v))` 分开。不得用
residual 代表正确，不得由相同错误数推断 candidate==Bob；candidate-vs-Bob
必须直接比较。D1 的 O1 只能标为 `POSTHOC_RECONSTRUCTED`，不是本次原始诊断。
A 只允许与 D1 已存共同指标比较：`outcome`、`iterations`、
`candidate-vs-Bob`、D1 APP、D1 single-edge c2v，以及 O1 的
`POSTHOC_RECONSTRUCTED violation`；L/I/P 新增的 F/S/A/L0 等指标在 A 中不作
定量差分，也不从旧 artifact 补造。
结果不得写秘密数组、Alice/Bob symbols、syndrome bytes、完整 prior、完整
消息或逐 symbol 数组。

## 7. 动态公开计费

L/I/P 各自维护独立 counterfactual 计数器：
`syndrome_rows_published`、`syndrome_bits_published`、
`tag_bits_published`、`control_bits_sent`、`disclosed_rows`。在当前 checkpoint
开始前发布新增 syndrome rows；第一次进入 tag 验证前发布一次 64 tag bits；
只有进入下一个 checkpoint 才发送并计入 1 个 CONTINUE control bit。成功的
IR disclosure 为 `reached_rows+64+control_bits_sent`；满 ladder 失败为
`9036+64+71`；异常和 timeout 都保留已经发布的计数，不回滚。三臂计数不相加，
不预填 `9100`。A 的 D1 历史计量只作为共同指标背景，不改写成新臂计量。

## 8. 真实执行状态机与输出

真实执行阶段固定为一次 invocation：prep allowance 600 s，L/I/P 各 600 s，
总墙钟上限 2400 s，peak RSS 硬上限 2 GiB。准备或输入校验失败时三臂均为
`NOT_ATTEMPTED` 并以非零返回；任一新臂发生 exception、nonfinite、RSS 超限
或 soft timeout，该臂为 `BLOCKED`，立即停止 invocation，后续臂为
`NOT_ATTEMPTED`，已生成的四臂候选 artifact 保留。普通
`LADDER_EXHAUSTED` 或达到 720 的正常终态允许继续下一个新臂。L/I/P 各运行
一次，无 rerun、无事后调参；A 不重跑。

输出根固定为
`comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`，
恰有 `manifest.json`、`results.json`、`table.csv`、`report.md`。顶层至少包含：

```text
schema, cycle, base_sha, implementation_sha, source_registry, data_sha,
session_id, block_frame_ids, non_fresh, mother_shape, mother_nnz,
checkpoint_rows, max_sweeps_per_checkpoint, max_total_sweeps,
llr_clip, convergence_tol, dtype, arm_order, invocation_status,
prep_status, arms, claim_boundary
```

每个 `arms[arm_id]` 至少包含：

```text
status, graph_id, prior_id, schedule_id, attempted_checkpoints,
stop_reason, sweeps_used, edge_updates, local_factor_target_updates,
state_evaluations, accounting, checkpoint_metrics, common_metrics,
new_metric_fields
```

`accounting` 包含四个公开计数器和 `disclosed_rows`；`checkpoint_metrics` 只含
第 6 节标量。A 的 `new_metric_fields` 结构为
`{value: null, not_recorded_reason: "D1 baseline did not record this metric; A was not rerun"}`
而不是补造值。L/I/P 的所有新指标必须填写真实聚合结果。路径、时间戳、wall
和 RSS 属于运行元数据，不参与科学字段确定性比较。四个文件不得包含秘密数组。

## 9. grouped-symbol mask BP 后继

只有当 L/I/P 都没有 hard-bit escape 时，下一周期才可排队 grouped-symbol mask
BP tiny exhaustive 或同块 GF32 对照。本设计不实现后继。其固定研究假设是：
每个 1024-state symbol 为一个变量，同一 check 内属于该 symbol 的 bits 合并
为 XOR mask，每个 `(check,symbol)` 传 scalar parity message，symbol-to-check
用完整 prior 对 mask parity 边缘化，check-to-symbol 仍为 binary SPA。约
41169 unique groups、约 42M state evaluations/iteration 只是数量级估算，不是
性能证据；顺序为 tiny exhaustive、small loopy synthetic、single real block。
