# V72P2D2 tasks (PLAN_CANDIDATE, 未接受, 不授权执行)

- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本表仅冻结任务与验收,
  不实现、不运行 decoder、不读 raw/parquet、不建结果目录。
- 验收 ID 稳定(`D2T0-*`,`D2T1L-*`,`D2T1I-*`,`D2T1P-*`,`D2T1M-*`,`D2T2-*`);
  子代理如实回 ID,不重述规格。任一数学合同证不出记 BLOCKER,禁 TBD 猜测。
- 不改 V72P1/V72P2/D1 已接受代码结果 `OpenSpec`/`cycle_state.yaml`/memory;
  禁写 `PLAN_ACCEPTED`/授执行。Ponytail lite:禁框架/插件/事件总线/缓存/锁/retry/checksum。

## T0 编译/导入/结构/小数学(无 decoder、无 parquet)

- D2T0-1 `py_compile` + import:未来新模块/CLI/test/config 可导入,无隐式生产调用。
  验收:全 PASS;测试默认不进入真实 decoder/raw 路径(须显式 fake 注入)。
- D2T0-2 冻结常量对照:checkpoint 72 点/ladder、`max_iter` 10/720、`clip` 20、`tol` 1e-6、
  shape 9036x10240/nnz49620、lambda/CE、M2 四参数与 §5 公式符号一致。
  验收:与 design §1/§5 逐字一致,不一致即 FAIL。
- D2T0-3 口径测试(沿用 D1 `count_four_cycles`/`count_collisions` 定义):
  tiny 1 check × bits {0,1}(bps=10 同 symbol) ⇒ pure-H 0,mixed symbol ΣC2 1。
  验收:`ASSERT_PASS`,仅校验口径,不证明科学结论。
- D2T0-4 M2 kernel 行归一:冻结参数下 `Σ_disp K = 1`(tol 1e-12),`P` 行和 1。
  验收:数值 PASS(纯数学,无 Alice/Bob)。
- D2T0-5 接口选择声明:单选 A 或 B(见 design §7)并记录,禁“边用边修”。
  验收:选择明确;选 B 须附最小修复 diff + 新旧对照回归计划(本任务只计划,不实现)。

## T1-L layered 合同单元(对应 design §3)

- D2T1L-1 顺序公式:逐 row/check 顺序实现 §3 的 1–7(旧 c2v 移除→新 v2c→新 c2v→
  写回 b2f→重算 f2b→APP 更新),self-exclusion + syndrome-aware sign 双路径一致。
  验收:tiny 树/单行用例与手算 SPA 一致(tol 1e-9)。
- D2T1L-2 sweep/residual:一次 sweep = 全 active 行各一次;`residual=max|c2v_new-c2v_old|`;
  `iters` 计 sweep,`edge_updates` 另计;`max|c2v|` 与 `max_v|Σ|` 分开输出。
  验收:计数语义测试 PASS。
- D2T1L-3 budget 公平与 warm-start:ckpt 上限 10 sweep/臂上限 720 sweep;ck 间臂内携带、
  新边置零;臂间独立。验收:预算截断 + 跨 ck 携带测试 PASS。
- D2T1L-4 收敛 ≠ 验证:`converged=(residual<tol)`,验证三条件独立。验收:语义测试 PASS。
- D2T1L-5 BLOCKER 门:若 D2T1L-1 证不出真 layered(与 §3 1–10 等价),记 BLOCKER,
  阻塞 T1-L ACCEPT,禁 row-loop 包 flooding 冒充。验收:BLOCKER 或 PASS 二选一,无 TBD。

## T1-I interleaver 确定性(对应 design §4)

- D2T1I-1 唯一性:算法/tie-break/seed 单值冻结,同 seed 重跑逐字相等。
  验收:两次构造 `col_map` byte-identical。
- D2T1I-2 分布:全 10240 列置换;前 1204 每 symbol 1 或 2 个;其余填满 10 bit。
  验收:分布断言 PASS。
- D2T1I-3 方向与口径:syndrome 对映射后 H 与原物理 Alice;prior 对物理 symbol;
  candidate-vs-Bob 在物理 bit 直接比。验收:方向测试 PASS(含 B 臂同口径描述)。
- D2T1I-4 不变量:shape/nnz/row-degree multiset/col-degree multiset/rank/prefix 保持。
  验收:与原 H 对照 PASS(重算,非手填)。
- D2T1I-5 参考重算:41/47/65 与 95/95 在本实现上重算留痕,标“参考非门槛”。
  验收:数值记录 + 非门槛声明,缺一即 FAIL。

## T1-P M2 prior 冻结(对应 design §5)

- D2T1P-1 参数冻结:`laplace,mu=0.0,scale=0.2714417616594907,eps=0.562251256281407`,Q=1024。
  验收:与 `v70r1_results.json` 1M session 一致,不重选。
- D2T1P-2 公式:`shape/K/P` 按 design §5,prior 自然 log,CE log2,行归一,floor 1e-300。
  验收:tiny 对照(含 wrap period -1/0/1) PASS。
- D2T1P-3 隔离:不读 Alice,VAL CE 6.7871 仅历史记录,允许变差声明齐全。
  验收:无 Alice 输入引用 + 声明文本检查 PASS。

## T1-METRICS 诊断聚合(对应 design §6)

- D2T1M-1 最小标量集:violation/flips/L0 分位/F 分位 max/S_pre-post/A_pre-post/
  delta_app/sign×2/zero/residual/iters+edge_updates/finite/clip/syndrome_tag_oracle。
  验收:fake 轨迹上字段齐全,缺一即 FAIL。
- D2T1M-2 语义隔离:`max|c2v|≠max_v|Σ|` 分开;收敛 ≠ 正确;`candidate==Bob` 直接比;
  O1 标 POSTHOC;无敏感数组。验收:语义测试 + 输出 dir 扫描(无密钥/syndrome/LLR 数组) PASS。

## T2 矩阵完整冻结(fake tiny + 严格口径,无真实执行)

- D2T2-1 fake 端到端:L/I/P 三臂在 tiny 图 + 合成先验上各跑通 ladder(含 warm-start、
  预算截断、四文件 schema 校验,但写 `workspace/<task>/<uuid>` 临时根,不写生产根)。
  验收:三臂完成 + 四文件恰四 + 不覆盖既有输出。
- D2T2-2 严格 replay:同 seed 重跑逐字一致(科学字段)。验收:PASS。
- D2T2-3 生产门禁:默认无 fake 注入时不进入真实 decoder/raw/parquet/输出根;
  `run_01` 不存在检查。验收:门禁测试 PASS。
- D2T2-4 脏树 scope:显式任务文件清单 + 冻结目录 diff + 输出根 absence 检查。
  验收:按 AGENTS.md §10.1 第 11 条报告 deltas。

## 计划冻结自检(本变更内,无代码运行)

- D2T-PLAN-1:5 文件齐且仅 5 新增;无实现代码块;无执行授权语句;DOI/历史边界措辞检查。
  验收:人工 checklist PASS(记录在未来 REVIEW_ENTRYPOINT,不在本计划内建文件)。
