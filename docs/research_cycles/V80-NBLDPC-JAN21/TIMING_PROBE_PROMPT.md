# TIMING 耗时实测 Prompt（执行面，TIMING-2）— 授权块未填 = 未授权，禁止执行

> 配套 packet：`TIMING_PROBE_PACKET.md`（同目录）。科学冻结输入 F1–F8 全表、产出字段 §3、验收 §8、claim ceiling §9、与 P4 边界 §10 以 packet 全文为准；本文件只放执行面，各节均为草案逐字原文（§11 授权门 / §5 白名单与禁令 / §4 停止门·一次授权覆盖 T1→T2 / §6 命令模板·`timeout 1810` 双保险与 fake-only 测试 / §2 F2 种子禁令与 F8 至多 1 次修复 / §7 合约 / §12 创建范围声明），不改任何冻结值。packet §11 全 BLANK ⇒ 本文件任何命令在主线程填写授权块前一律不得执行。

## §11 Pre-EXECUTE 待填槽（执行时填，未填 = 未授权）
### §11 授权块（空白待签；未填 = 未授权；全包唯一填充处）

（待填槽 Q0–Q6 与授权块全文见 `TIMING_PROBE_PACKET.md` §11；当前全 BLANK = 未授权。）

## §5 预算 / 允许 / 禁止文件

- **预算（本包自身，冻结提议、授权块定值）**：**单调用帽 600 s**（= 被测帽之一，超即 `INCOMPLETE-call`）；**批次总 ceiling ≤ 1800 s**（提案；执行时在授权块填定值——注意本包 ceiling 应 ≤ 被测的 3600 s，避免测帽包比帽还贵）；**RSS < 2 GiB**；**1 CPU**；unspent budget ≠ authorization。
- **允许文件（白名单，exhaustive）**：
  1. 新增 `comparison_bench/src/comparison_bench/cli/timing_probe_runner.py`（或复用 `p4_feas_construct.py` 的 fake/计时通路——**二选一，Pre-EXECUTE 冻结所选路径**；若复用则该文件仅以现有 flag 只读调用，**禁改其一字节**）；
  2. 新增 `comparison_bench/tests/test_timing_probe_fake.py`（fake-only、tiny 输入、`pytest -p no:cacheprovider`、测试根 = pytest **`tmp_path`**——零仓库写入，不占用 `workspace/TIMING/` 输出根、不新建 `_pytest_` 目录）；
  3. 输出根 **`workspace/TIMING/<uuid8>/`**（fresh additive；`timing_records.jsonl`、`timing_summary.md`）；
  4. `docs/research_cycles/V80-NBLDPC-JAN21/` 下四件：`TIMING_PROBE_PACKET.md`（本文件落档）、`TIMING_PROBE_PROMPT.md`、`TIMING_EXPLORATION_LOG.md`（append-only）、`TIMING_BATCH_END_REVIEW.md`（执行后）。
  5. 只读 import：`nonbinary_v10_peg`（`rank_GF1024`/`peg_construct`/`_bfs_distance`）、`nonbinary_v26_mcde.make_rho`——**行为零改动**。
- **禁止文件（exhaustive）**：`results/`、`comparison_bench/outputs_comparison/`（禁写，§5.2）；`src/`、`experiments/`、`tools/`（冻结基线，`git diff -- src/` MUST EMPTY）；**P1 族**（`P1_PACKET.md`、`P1_STAGE1_*`、`workspace/P1_STAGE1/`）、**S0.1 族**（`S0_1_*`、`workspace/S0_1/`）；P4 族写操作（`P4_FEAS_PACKET.md`/`P4_FEAS_PROMPT.md`/`workspace/P4_FEAS/` 只读不碰，本包**无权**改其 §5）；真实 **`.ttbin` / `gamma_f03*.npz`**；`AGENTS.md`、`docs/decision-log.md`、`docs/troubleshooting.md`、`docs/NOW.md`、`docs/EXECUTION_PLAN_20260922.md`；`tools/longrun_*`/`minrerun_*`/`routeA_*`、`experiments/run_e2e_pipeline.py`；**禁 commit / push**。

## §4 停止门（二元、零译码可判定）

- **G-A 范围**：任一真实数据读取、任一 `decode_calls≠0`、任一禁写路径写入 ⇒ STOP-BLOCKED。
- **G-B 预算**：单 case 超 600 s ⇒ `INCOMPLETE-call`（记录即证据，不算失败）；批次超 ceiling ⇒ `INCOMPLETE-batch`，全部已写行保留、禁聚合覆盖、禁 rerun/resume/adaptive。
- **G-C 秩序**：T1 全部 12 case 完成（或终态）前禁进 T2；一次授权覆盖冻结臂序（无逐臂授权）。
- **G-D 变更**：任何 F1–F8 改动（含加尺度、加 repeats、改 k、改种子）⇒ STOP 回主线程；实现若需改冻结模块行为才能跑通 ⇒ STOP（先 OpenSpec，AGENTS §3）。

## §6 命令模板（占位符执行时冻结）

```
# 0) 聚焦 fake-only 测试（Pre-EXECUTE Q4；已验证 pytest 命令，磁盘根 = pytest tmp_path，无 --root）
.venv/bin/pytest -p no:cacheprovider -q comparison_bench/tests/test_timing_probe_fake.py

# 1) 唯一一次授权执行（一次授权覆盖 T1→T2 冻结臂序）
timeout -k 10 1810 .venv/bin/python -m comparison_bench.src.comparison_bench.cli.timing_probe_runner \
  --root workspace/TIMING/<uuid8> --uuid8 <uuid8> --execution-authorized --execute-real \
  --batch-cap-s <BATCH_CEILING> --rss-gib 2   # 单调用 600 s = runner 内层 deadline 检测（F8，非 CLI 旗标）；1810 = 批次级 timeout 双保险
```

## §2 冻结科学输入 — 逐字复制 F2 种子禁令与 F8 修复名额（完整 F1–F8 见 packet §2）

| # | 项 | 冻结值 |
|---|---|---|
| F2 | 种子 | 专用 timing 种子（**非** P4 谱系）：T1 矩阵种子 `2026092401..2026092412`（按 case×repeat 顺序逐一分配）；T2 PEG 种子 `2026092421, 2026092422`（每尺度各两次）。**禁用 `2026092001`/`2026092011`**（保 P4 F3 `rg` 独占门）；执行者不得自行发明种子 ⇒ 冲突即 STOP。 |

| # | 项 | 冻结值 |
|---|---|---|
| F8 | 停止/失败类别 | 单调用超 **600 s** = `INCOMPLETE-call` 记录、**不续跑不重试**（该超时本身即是"帽太小"的有效实测证据）。**双保险 = 内层检测 + 批次级 timeout，无 per-call 抢占**：600 s 由 **runner 内层 deadline 检测**（超限落 `INCOMPLETE-call` 并停续跑，非 CLI 旗标），外层唯一兜底是 §6 cmd1 的**批次级** `timeout -k 10 1810`；**不为单 case 另起外部 `timeout` 进程、无 per-call 抢占式杀进程**；批次 wall 超 ceiling = `INCOMPLETE-batch` 保留、永不续跑；异常 = 该 case 记 `error` 保留原始 traceback。**至多 1 次预注册工程修复**（仅基础设施失败；科学输入/seeds/阈值全不变；失败尝试同日志保留；未用则写 `no repair path used` 行；第二次失败 ⇒ STOP-BLOCKED，AGENTS §1.2）。 |

## §7 合约（逐字；完整 §7 见 packet）

- 合约（两文件制）：一个 packet+prompt 对 + 一个 append-only log + 一个 batch-end 独立评审；一次授权覆盖冻结臂序；至多一次预注册 repair+rerun；repeats=3 + 双 seeds 满足"变异性可能混淆时 multi-seed 默认"。

## §12 本任务（planner 冻结）创建范围声明 — TIMING-3

- 本任务**只产出本草案文本（返回主线程落档）**；未写任何文件、未执行任何构造/计时/测试、未改 P1/S0.1/P4 族与 `src/`/`docs/NOW.md`/`decision-log`/`AGENTS.md`、未 commit、未 push。
- 科学阈值零改动：1.3 门、leak/tag/H_anchor、`undetected` 隔离、禁合并——全部不涉及；本包无任何阈值。
- 结果数值未预设：全部 wall/RSS/拟议帽值 = `[TO BE MEASURED]`。
