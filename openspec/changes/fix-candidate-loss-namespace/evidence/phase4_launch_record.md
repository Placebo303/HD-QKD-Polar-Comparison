# Phase 4 启动记录 — fix-candidate-loss-namespace（F6）

**启动时间：2026-08-26T01:52:41+08:00。前提：F2 终态三门全 PASS（evidence/phase3_gates_final_report.md §4）。**
任务根：`workspace/fix-candidate-loss-namespace/p4_20260826_020352/`（launcher 日志 `launcher.log`、`launcher_err.log`、`liveness_300s.txt`）。
启动脚本：`workspace/fix-candidate-loss-namespace/launch_phase4_lossfix.ps1`（顺序分离进程，每档 Wait-Process 后进下一档）。

## 1. 三档顺序分离进程（10 → 6 → 16）

| 档 | 状态 | PID 文件 | stdout/stderr 日志 |
|---|---|---|---|
| 10dB 全网格 | **RUNNING**（首档，2026-08-26T01:52:41 启动） | `p4_20260826_020352/loss_10dB_pid.txt` | `loss_10dB_stdout.log` / `loss_10dB_stderr.log` |
| 6dB 全网格 | PENDING（等 10dB 退出后由 launcher 自动启动） | `loss_6dB_pid.txt`（未生成） | 同名规则 |
| 16dB 全网格 | PENDING | `loss_16dB_pid.txt`（未生成） | 同名规则 |

- 首档主 PID：**9876**；launcher PID：23336。
- 命令（逐字）：`python pipelines/current/routeA_run_formal_cross_loss.py --losses 10 --output-dir results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300_lossfix_v1 --shards 16 --workers 12 --metric-jobs 12 --frames 300 --seed 20260228 --verification-tag-bits 64 --candidate-dirs "10=D:\Code\HD-QKD_Polar_Release\results\authoritative_nsfix\e2e_10dB_fullgrid_pairing_v2_candidate_lossfix_v1"`
- 候选目录指向 lossfix 三目录（F3 bootstrap + F4 回填完成）；20dB 不重跑（T4.3 沿用既有产物）。

## 2. 首档存活核验

### t≈60s（01:53:45）
- 进程树：launcher(23336) → routeA(9876) → round1a(52760) → max_pie(38684) → **12 个 metric worker python**（--metric-jobs 12 池），共 15 个 python 存活；
- 聚合 CPU 已达 ~4149 CPU·s ⇒ 多核满载计算中；输出根已生成
  `four_loss_parts_frames300_lossfix_v1/loss_10dB/stage0_replay_index/_recomputed_replay_inputs/`。

### t≈300s（02:01:56，见 liveness_300s.txt）
- 主进程 9876 ALIVE；python 总数 15；聚合 CPU 6507 CPU·s（较 60s 点 +2358 ⇒ 持续满载）；
- stdout/stderr 均 0 字节 —— 与 v4 首次 launch 完全相同的 Python 输出缓冲现象（非故障信号；stderr 无 traceback 即无错）；
- stage0 重算输入目录文件数开始增长。

## 3. 冻结参数（不可中途更改）

科学：`--frames 300 --seed 20260228 --verification-tag-bits 64`；并行：`--shards 16 --workers 12 --metric-jobs 12`（核数冻结依据 evidence/phase4_launch_config.md）。
环境：`NUMBA_CACHE_DIR=%TEMP%\numba_cache_v4`、`NUMBA_DISABLE_CACHING=1`、`PYTHONIOENCODING=utf-8`。

## 4. 边界与红线

- 输出仅写入 `results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300_lossfix_v1/`（新路径）与 workspace 任务根；旧产物只读。
- 后续监控（各档退出码、stage0→2 推进、validator 121/121）由主线发起，操作员不再介入。
