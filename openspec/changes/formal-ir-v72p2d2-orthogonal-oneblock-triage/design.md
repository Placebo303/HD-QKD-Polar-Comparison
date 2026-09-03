# V72P2D2 设计 (PLAN_CANDIDATE, 未接受, 不授权执行)

- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。不改 V72P1/V72P2/D1 已接受
  代码、结果、`OpenSpec`、`cycle_state.yaml`、memory。禁读 raw/parquet,禁运行 decoder,
  禁建结果目录。数学合同无法冻结则 §10 BLOCKED 列未决,禁 TBD 猜测。
- Ponytail lite:禁框架/插件/事件总线/缓存/锁/retry/checksum(AGENTS.md §5.7)。

## 1. 基线与输入冻结 (D2D2-01)

- 同一块:单块非新鲜 VAL1726–1729(session `20260123_1M_600k_0dB`,
  registry `v71_data_registry.json` schema `v71_data_v1`, data_sha `84d62779`,
  CAL702..1725 共享 prior;直接引用 D1,不重新读取)。
- 同 ladder:checkpoint_rows = `range(160,8993,128)+[9032,9036]`(72 点)。
- 同 edge 预算:`max_iter_per_checkpoint=10`,`max_total_iterations=720`(每臂);
  `llr_clip=20.0`,`convergence_tol=1e-6`,float64,warm-start 臂内携带(新边置零),
  A/B 不共享 mutable c2v(沿用 D1 语义)。
- 同验证泄漏口径:syndrome_ok(`syndrome_observed == syndrome_target[:ckpt]`)、
  tag_ok(64-bit)、finite;`protocol_accepted = finite && syndrome_ok && tag_ok`;
  `verified_exact_success = protocol_accepted && oracle_exact`;
  `undetected = protocol_accepted && !oracle_exact`(隔离,从不并入 success/FER)。
  计量沿用 D1 口径:`leak_IR=syndrome_bits+tag_bits`(9036+64=9100/臂),
  `total_public=leak_IR+71 CONTINUE`,分母为 selected CAL-CV CE `7.135005172802673`
  (D1: `f_model_relative=1.2455097837734634`,`f_public_model_relative=1.2552274974710365`,
  失败尝试计入,描述性)。
- 基线 A:复用 D1 Arm A 已记录事实(72 ckpt / 334 iters / `LADDER_EXHAUSTED` /
  bit 3100 / sym 620 / syndrome+tag+control 9036+64+71 / lambda `221.22162910704503` /
  CE `7.135005172802673`),禁重跑。D1 Arm B 事实(321 iters,同终态)仅作背景,不作为 D2 门槛。

## 2. L 臂:真正 layered(只变调度, D2D2-02)

- 原 H(9036x10240,nnz49620,check-degree `{4:1,5:4594,6:4441}`,deg2 9035) + M0 prior
  (lambda `221.22162910704503`,自然 log prior, floor 1e-300) + flooding 侧其余语义全同。
- 唯一 delta:check 更新顺序改为逐 row/check 顺序的 layered sweep(§3 合同)。
  不改图、不改 prior、不改 clip/tol/预算、不改 local-factor 语义。

## 3. Layered 11 点数学合同(逐 row/check 顺序, D2D2-03)

记 `v2c[e=(v,c)]`,`c2v[e=(c,v)]`,`b2f[sym,b]`,`f2b[sym,b]`,`APP[v]=f2b[v]+Σ_{e∋v}c2v[e]`,
`S[c]` 为 syndrome_target,check 度 `d=|N(c)|`,邻边集 `N(c)` 按 CSR 行顺序排列。
一次 sweep = 按 `c=0..active_rows-1` 顺序,对每行依次执行下述 1–7,行内边按 CSR 边序:

1. 旧 c2v 移除:对行内每边 `e∋c`,先用当前 `APP` 与旧 `c2v[e]` 得排除本边的 v2c:
   `v2c[e] = APP[v] - c2v_old[e]`(其中 `APP` 为本 sweep 已更新行的最新值,未更新行用旧值)。
2. 新 v2c 算新 c2v:用行内全部新 `v2c[N(c)]` 按 syndrome-aware SPA 求行内每边新值
   `c2v_new[e] = 2*arctanh(clip(flip(S[c],d) * Π_{e'∈N(c),e'≠e} tanh(v2c[e']/2)))`,
   `flip(S[c],d)=(-1)^S[c] * (-1)^{d mod 2 == 1 ? 1 : 0}`,clip 至 `±(1-1e-12)`,
   再 clip 至 `±llr_clip`(与 adapter `_check_update_numba`/python fallback 同 parity)。
3. 写回 bit_to_factor:行更新后立即对受影响 variable `v` 重算
   `b2f[v] = Σ_{e∋v} c2v_latest[e]`(已更新边用新值,未更新边用旧值)。
4. 重算 factor_to_bit:对受影响 symbol 的 10 bit 用 `local_factor_extrinsic`
   (目标 bit 的 b2f 项置零的 self-exclusion,1024 枚举,clip ±20)重算 `f2b`。
5. APP 更新:`APP[v] = f2b[v] + Σ_{e∋v} c2v_latest[e]`,clip ±20。
6. Self-exclusion:任何 `v2c[e]` 不得含本边旧 `c2v[e]`;任何 `f2b[sym,b]` 不得含本 bit 的 `b2f`。
7. Syndrome-aware sign:每行符号含 `S[c]` 与 check-degree parity,Numba/Python 双路径同义。
8. Sweep/residual 定义:一次 sweep = 全部 active 行各恰更新一次;
   `residual = max_e |c2v_new[e]-c2v_old[e]|`(全 active 边,一次 sweep 口径);
   `iters` 计 sweep 数,`edge_updates` 计行内边更新总数(单边 `max|c2v|` 与
   `max_v|Σ_{e∋v} c2v[e]|` 分开记录,见 §5)。
9. Budget 公平:每 ckpt 至多 10 sweep,每臂至多 720 sweep;与 flooding 的
   iter 上限数值相同,但语义为 sweep(须在报告中注明不可直接比 iter 绝对值,
   只比 escape/violation/验证三判别)。
10. Warm-start 携带:ck 内 sweep 串行;ck 间臂内携带旧 c2v,新激活边置零;
    L/I/P 臂间 c2v 独立,零共享。
11. 收敛 ≠ 验证:residual < tol 只记 `converged`,不记正确;验证仍按 §1 三条件。
    若实现不能逐条证明以上 1–10 与 flooding 的“旧 c2v 移除→新 v2c→新 c2v→
    写回 b2f→重算 f2b→APP 更新”顺序等价性,则在 tasks T1-L 记 BLOCKER(用最新
    消息列),禁把 row-loop 包 flooding 冒充为 layered。

## 4. I 臂:degree-balanced full-column interleaver(D2D2-04)

- 确定性静态置换,decoder-free 可先行试算(本计划内不试算、不执行):
  全 10240 列参与;前 1204 高连接列分散到每个 symbol 使每 symbol 含 1 或 2 个;
  其余列填满每 symbol 10 bit;算法/tie-break/seed 唯一冻结(未来实现时单值,
  本计划不定具体值,只定“唯一”要求);方向 old→物理 `sym*10+bit`。
- Syndrome 对映射后 H 与原物理 Alice 算(`syn = H_perm · alice_phys`);
  prior 对物理 symbol(行按物理 symbol 取 `P[bob_phys]`);candidate-vs-Bob 比较
  在物理 bit 上直接比。
- 不变量:shape 9036x10240、nnz49620、row-degree multiset `{4:1,5:4594,6:4441}`、
  col-degree multiset、`rank`、`prefix` 性质保持(置换不变性,未来 T1-I 断言)。
- 试算参考(路线研究即时静态复算,非门槛):每 symbol 总边数 min/median/max 41/47/65;
  `<=25` 与 `>=100` 的 symbol 均为 0;同 check 同 symbol 碰撞行 95,
  symbol `ΣC(k,2)` 95。95/95 仅参考非门槛,未来实现必须重算留痕,不得手填。

## 5. P 臂:冻结 M2 prior(D2D2-05)

- 原 H + flooding + layered 之外的其余语义全同;唯一 delta 是 prior 由 M0 换为冻结 M2。
- 冻结参数(来自 `v70r1_results.json` 1M session,CAL-only 选择,VAL 未参与选择):
  `family=laplace`,`mu=0.0`,`scale=0.2714417616594907`,`eps=0.562251256281407`,Q=1024。
- 公式冻结:`shape ∝ Σ_{period∈{-1,0,1}} exp(-|disp+period*Q-mu|/scale)`,
  `disp=signed((a-b) mod Q)`(signed 口径与 `v70r1_parametric_channel_model_check.py`
  `signed_disp` 一致);`K=(1-eps)*shape+eps/Q`;`P[a|b]=K[(a-b) mod Q]`;
  prior 自然 log(`log P`),CE log2,行归一,现有 floor 1e-300,不读 Alice、不重选。
- VAL CE 6.7871(`models.parametric.CE_VAL=6.787126437359054`,CAL 6.7479,gap 0.0393,
  n_params 4)仅历史参考,允许变差;禁“M2 CE 更低 ⇒ decoder 必改善”断言
  (M2 可能使 Bob-oriented prior 更尖锐而更难逃离固定点,见路线研究 §5 INFERENCE)。

## 6. 诊断聚合(每 ckpt 最少量, D2D2-06)

每 ckpt(L/I/P; A 复用 D1 不重记)记录标量,不存全量 prior/矩阵/LLR/边消息:

- `violation` = candidate syndrome 违反数(`weight(H_arm·hard XOR syn_target)`);
- `candidate_vs_Bob bit/symbol flips`;
- `L0 分位`(APP margin 分位数,固定分位点未来实现时冻结,本计划不定具体值);
- `F 分位 max`(`max|f2b|`,分位口径同上);
- `S_pre/post 分位 max`(`max_v|Σ_{e∋v} c2v[e]|`,sweep/iter 前后);
- `A_pre/post 分位 max`(`max|APP|`,前后);
- `delta_app`(前后 APP 差分量,范数口径未来冻结);
- `sign 翻转 ×2`(`sign(f2b)` 翻转数,`sign(APP)` 翻转数,相对首 ckpt);
- `zero` count(零消息/零 APP 计数,口径未来冻结);
- `residual`,`iters` + `edge_updates`,`finite`,`clip` 越界标记,
  `syndrome_tag_oracle` 事后四元组(syndrome_ok/tag_ok/oracle_exact/undetected)。
- 明确:单边 `max|c2v| ≠ max_v|Σ|`;收敛 ≠ 正确;`candidate==Bob` 直接比逐 bit/symbol,
  不得由等错误计数外推逐位相等;O1(`weight(H_arm[:r]·(Alice XOR Bob))`)仅 POSTHOC 辅助,
  全程标 `POSTHOC_RECONSTRUCTED`,不作 D 口径引用;不提交敏感数组
  (无逐符号密钥、无 syndrome bytes、无全量 LLR/边消息)。

## 7. 接口二选一(D2D2-07)

- A(推荐):新 runner 不调用 `run_incremental_decoder` 的列 deferred 路径
  (复用 D1 `run_arm`-style per-ckpt `run_decoder` 语义:warm c2v 显式传入/传出),
  则该 bug 不触发,adapter 零改动。
- B:若 L layered 必须复用 `run_incremental_decoder`,则做最小修复
  (返回 `variable_to_check_final` 拼出的全长 `variable_to_check`,其余逐字不变)
  + 回归(旧行为复现测试 + 新旧返回值对照测试),禁重构 adapter 其余逻辑。
- 选择在未来 Implementation 冻结时单选并记录;本计划不定,但禁“边用边修”。

## 8. 后继(仅描述, D2D2-08)

- Grouped-symbol mask BP(PROPOSED):每 1024-state symbol 为一变量;每条 binary check
  在同 symbol 内连边集合表为 XOR mask;每 `(check,symbol)` 只传 scalar parity;
  symbol-to-check 用完整 1024-state prior + 其余 mask 消息按该 mask parity 边缘化;
  check-to-symbol 按 binary parity SPA 组合。朴素量级约 41169 unique group/轮约 42M
  state-level evaluations(数量级估算,非 runtime 证据)。价值:直接传 symbol 内联合信息,
  消同一 check 内多 bit edge 人工 factor-cycle;仍受图/高码率限制。
  最小验证顺序:tiny `k=2/3` exhaustive posterior → 小 loopy synthetic → 单块真实诊断。
  未验证前不得称成功/突破容量。
- 三臂皆无 hard-bit escape 时停 binary edge-level 微调,转 grouped-mask tiny 排队或同块
  GF32 对照;不加迭代/调 damping/扩样。

## 9. 未来文件清单(Ponytail lite, D2D2-09)

- 上限 5 个新文件,能合一不拆,不建框架(示例合并方向,未来实现冻结时单选):
  新算法模块( layered + interleaver + M2 + metrics 合一优先 )×1 +
  CLI/runner(fake 注入 + 真实路径门禁 + 四文件写)×1 +
  focused test(T0/T1/T2 合一)×1 + 小 config(冻结常量)×1 + fixture(tiny 矩阵/先验)×1。
- 禁改 `src/`,`experiments/`,`tools/`,`results/`,既有 outputs;禁覆盖输出;禁建 `run_01`
  (实现任务内);测试用全新 `workspace/<task>/<uuid>` 根 + `pytest -p no:cacheprovider`,
  生产 decoder/raw-data 路径默认不进入(fake runner 显式注入才可调用)。

## 10. 未决 BLOCKER 位(无则空,禁 TBD 猜测)

- BLOCKED-1(Layered 等价性证明):若 §3 第 11 点证不出,记 BLOCKER,阻塞 T1-L ACCEPT,
  不降级为“近似 layered”。
- BLOCKED-2(分位点/范数口径):§6 中 L0/F/S/A 分位点与 `delta_app` 范数若未来实现前未冻结
  单值,记 BLOCKER,禁测试内自选。
- 本计划内无新增 BLOCKED(以上为未来实现 gate,此处仅占位声明)。
