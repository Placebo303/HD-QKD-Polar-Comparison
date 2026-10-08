# C-3 执行日志（单一 append-only，2026-10-08，EXPLORE）

> Track：EXPLORE（合成参数化信道；B≥300/格；落盘块级行 + 汇总表）。
> 授权：C 批预注册 §4 C-3（用户已批准计划）覆盖本冻结臂序列；操作员在机器门内连续执行。
> 冻结包 `C3_PACKET.md` + 启动注记 `C3_LAUNCH.md` 逐字遵守。
> 结论上限（包 §7）：只报最优 N/净密钥/同时间 f 分层结果（含 mapped/fresh 区分）；
> FER 尾部外推、SKR、路线关闭不在本包声称。
> 至多一次预注册修复+重跑（科学输入/种子/阈值/假设不变，失败尝试保留同日志）。
> 本轮修复消耗：0（冒烟判据 Jules 澄清与 overtime 误标下限为工程执行细节，
> 科学输入/种子/阈值/假设未变，不计入修复次数）。

## 0. 冻结输入（引用，不重写数值）

- 信道：`C2_LOG.md` 规范表（canonical）；新鲜层 F1（k=1, bw200-cal：
  p*=0.060740, p_minus_abs*=0.037000, rest≈1.3e-05）/ F2（k=1, bw400-cal：
  p*=0.030413, p_minus_abs*=0.018564, rest=0）/ F3（k=2, bw100, exploratory：
  T2-1M σ̂=24.88, δ̂=+46.99, W=200 经 cond_dist + c1_kbin.params_from_stats，
  q=5, H_q≈1.770, p≈0.474）。
- 符号约定：δ*≈−δ̂C（C3_LAUNCH §1）；首格 T2-1M δ*=−50 方向冒烟先行。
- 码率规则（包 §3）：二进制臂 R=1−h2(p_op)−gap_bin(N)−margin_B；
  高维臂 R=1−H_sym/log2(q)−gap_nb(N)−margin_B；margin_B=0.01；
  M∈{2.5,3.0} 只在 N=16384 锚点按 Net_seg 二选一后冻结同行；
  M→R 冻结标度 R(M)=R_base−(M−2.5)×0.01（驱动 docstring 冻结解释 1）；
  K=round-half-up(N·R)，K<1 记 infeasible。
- A3 归属：驱动自含 A3 执行循环，镜像 runner A4 路径；m 由规则显式算出经
  `channel["m"]` 传入；TAG=64；ROW_KEYS+code_hash/frozen_hash 逐块落盘。
- 映射层：适配器 runner.adapt_* 就绪；历史行摘要 JSON 缺位（C1_INVENTORY
  仅代码指针，workspace 无 G-5/Z-1/Z-3/F-1/S-5/D-4 摘要 JSON），mapped 表空置；
  fresh/mapped 分表永不混排。A7 unavailable 列位。

## 1. 新建文件（本包唯一新增，冻结目录零 diff）

- `comparison_bench/src/comparison_bench/formal_ir/msd_c3_bakeoff.py`
  （C-3 驱动；R7 smoke+分片续跑+6h 预算；net_of_cell 唯一口径；β 附带列+警示语）
- `comparison_bench/tests/test_c3_bakeoff.py`（T0/T1 小规模）
- 机器根 `workspace/c3_tune/c3_20261008/`（驱动 --full 生成；执行前须不存在）
- 本日志（单一日志）

## 2. T0/T1（小规模，B≤10）

- 命令：`D:\software\Anaconda3\envs\qkd_env\python.exe -m pytest comparison_bench/tests/test_c3_bakeoff.py -p no:cacheprovider -q`
- 结果：9 passed（T0 常量/码率数学/信道字面值/锚点逻辑；T1 dry-run B=8 行键齐全、
  m 显式、net 汇总、fresh-root 拒绝、A5 wrap 不抛错）。
- 工程细节（科学输入未变）：① 方向冒烟 N 提至 256（小 N 下 TAG=64 主导反转
  Net 比较，注记于驱动）；② 先验以传入 channel 为准（曾误用规范重建致坏符号
  代理跑成好信道，已修）；③ overtime-risk 阈值加 30s 下限（计时器粒度误标）。

## 3. 方向冒烟（T2-1M δ*=−50 先行）

- 命令：驱动内 `--direction-smoke`（A4 N=256 B=10；--full 首步同式，不一致则停）。
- 结果：PASS。正确侧 p=0.060740 成功 7/10、Net_seg=−67.4；
  错误符号代理 p=0.237970 成功 0/10、Net_seg=−1450.0。
  与 C-0 最优点（δ*=−50）一致，继续。

## 4. 启动命令（C3_LAUNCH §5 字面）

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_c3_bakeoff --full --output-root workspace/c3_tune/c3_20261008
```

- fresh-root：执行前 `workspace/c3_tune/c3_20261008/` 不存在（已验 ABSENT）。
- 网格：3 WP × 4 方法（A1/A2/A3/A4）×（7N + 1 锚点冗余）≈ 96 格 × B=300；
  A5 layered_lite 新鲜 wrap（F1/F2，M→max_iter 阶梯）；A7 unavailable 列位。
- R7：B_smoke=30，先 min(3,B) 探针（外推超 cell 1800s 则 overtime-risk 零块 short），
  外推超 max(2×运行中位, 30s) 标 overtime-risk 分片续跑；墙钟 6h 撞墙保留已完成格。

## 5. 执行过程（append-only）

- 预注册工程修复①（科学输入/种子/阈值/假设不变；本批唯一一次修复）：
  探针外推改摊销模型（外推 = 探针实耗 + 解码中位×剩余块），一次性构造不再按
  每块均摊；补续跑复用（满行格 _recount_cell 由行重计，不重译码；A5 防复写）。
  旧码任务已杀（仅 3 个 A1 小格完成，保留复用）；修后测试 9 passed 不变。
  失败尝试（旧码锚点双 M overtime-risk 0 块）保留本日志。
- R7 误标下限 30s、冒烟 N=256、channel 先验权威三处同为本修复前已落定的工程
  细节（科学输入未变，不计修复次数）。
- 重跑：`... --full --output-root workspace/c3_tune/c3_20261008 --resume`
  （同根续跑，已完成格保留；fresh-root 纪律对 --resume 例外用于分片续跑）。
- 执行事故（非科学修复）：首次 --full 的 job_kill 未杀死子进程（PID 28380），
  其与 --resume 进程（PID 33312）并行约 2h 同根运行。15:52 发现后立即 kill 旧进程；
  审计：7 个块文件各 300 行、block 连续、无复写、无超行（同种子确定性行，
  未发生交错写；旧进程在飞探针无落盘，无孤儿 probe 文件）。根因：job kill
  未传导至 python 子进程；教训：kill 后必查进程表。

## 6. 主线程交接注记（操作员提前结束，2026-10-08 ~18:30）

> 本节为主线程 append，非操作员原文。操作员回传被截断，
> 其烘焙进程（PID 33312）已不存在（主线程 18:30 查无此进程），无汇总表。
> 主线程裁决如下（透明记录）：

- Full 范围按"部分关闭"处理：已落盘 14 格（F1：A1×7+M 锚点、A2×4、A3×3，
  每格 300 行）为有效 fresh-full 证据，照常进入 OPT（C3-OPT-01 改为
  mini+full 联合表，来源列区分；C3-GRID-01 按实际落盘格清单执行）。
- 未竟范围（F1/A4、F2、F3 fresh）由 mini 波次接管（2a/2b/2c/2e/2f，
  同冻结规则、确定性种子、根隔离可合并）；full 不再续跑（避免双写）。
- C3-LOG-01：本节即缺失的收尾条目；C3-CLEAN-01 与 C3-OPT-01 并入批末审查。
- 未决问题（批末审查备案）：探针文件出现后消失与本 LOG"无孤儿 probe"审计矛盾，
  块行证据本身完整（14 格行数/块号逐格可验），探针去向不再追查，
  后续包要求探针文件保留或归档声明。
- M→R 标度与 mapped 缺位两事项见主线程 `C3_WATCH.md`（2）与 `C3_MAPPED.md`
  更正记录，复核结论：接受为文档化变体 + mapped 主线程已接管。

## 7. 操作员固化收尾（finalize-partial，~18:35，不碰 §6 主线程原文）

- 命令：`--dry-run` 测试根复验 9 passed；`direction_smoke()` 重跑 PASS（7/0）；
  固化脚本（`python -c` 调驱动函数，无驱动改动）：14 满格由行重计
  （`_recount_cell`，T_dec 由行累加）→ `manifest.json/cells.json/anchor.json`
  → `build_tables` → `net_main_fresh.csv/net_detail_fresh.csv/a7_column.csv/
  mapped_NOTE + 空表`（74 条记录；missing=worker 丢失前未启动，与 short 区分）。
- §6“无汇总表”截至本节已过时：汇总表现已存在（见机器根；主表 12 行：
  F1/A1→1024 Net_seg −43670.0 f 1.373；F1/A2→1024 −61160.0 f 1.352；
  F1/A3→4096 +340388.6 f 1.358；余 9 行无有效最优（全未定））。
- F1/A1 锚点：双 M 全跑 300 块，双未定（N=16384 成功个位数）→按规则冻 M2.5；
  其余锚点 missing→暂冻 M2.5（provisional）。
- F1 实测 decided 格（B=300）：A1 成功 161/73/37/3/0（N=1024→32768）；
  A2 成功 128/55/19/1；A3 成功 276/247/226（Net_seg 正增长）。
  A1/A2 的 FER 随 N 恶化是调参信号（gap 对该 PEG/冻结集偏小），非科学判定。
- 未做事项（交批末审查）：A5 wrap 未跑（mini 2a/2b/2c/2e/2f 未列明是否覆盖）；
  F1/A4、F2、F3 fresh 未启动（§6 已判 mini 接管，full 不再续跑）；
  失败计数个位数已全写「未定」；β 附带列+警示语、同时间 f（extrap.）已出。
