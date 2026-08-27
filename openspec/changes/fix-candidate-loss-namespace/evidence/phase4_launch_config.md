# Phase 4 启动配置冻结 — fix-candidate-loss-namespace（F5）

冻结时间：2026-08-26（启动前）；本文件为 Phase 4 并行参数的溯源记录，科学参数不在其列、另行冻结。

## 1. 硬件探测

| 项 | 值 | 来源 |
|---|---|---|
| 逻辑核数 | **20** | `os.cpu_count()` / `NUMBER_OF_PROCESSORS=20`（2026-08-26 现场探测） |

## 2. 冻结的并行配置（上限 12）

| 参数 | 值 | 说明 |
|---|---|---|
| stage0 `--metric-jobs`（→ round1a `--jobs`） | **12** | min(20, 12)；round1a 经 run_real_polar_max_pie 重算层表 |
| stage1 `--workers`（→ replay shards 并行度） | **12** | min(20, 12) |
| `--shards` | **16** | 不变（任务书硬约束） |
| 科学参数 | `--frames 300 --seed 20260228 --verification-tag-bits 64` | 冻结，不得改动 |

## 3. 启动形态

- 三档顺序分离进程：10dB 全网格 → 6dB 全网格 → 16dB 全网格；每档独立 PID + stdout/stderr 日志。
- 进程命令：`python pipelines/current/routeA_run_formal_cross_loss.py --losses <L> --output-dir results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300_lossfix_v1 --shards 16 --workers 12 --metric-jobs 12 --frames 300 --seed 20260228 --verification-tag-bits 64 --candidate-dirs "<L>=<lossfix 绝对路径>,..."`。
- 候选目录（F3 已补齐 round1a bootstrap 五件套并经单点冒烟；F4 后 16dB=121/121 格）：
  - `results/authoritative_nsfix/e2e_10dB_fullgrid_pairing_v2_candidate_lossfix_v1`
  - `results/authoritative_nsfix/e2e_6dB_fullgrid_pairing_v2_candidate_lossfix_v1`
  - `results/authoritative_nsfix/e2e_16dB_fullgrid_pairing_v2_candidate_lossfix_v1`
- 环境：`NUMBA_CACHE_DIR=%TEMP%\numba_cache_v4`、`NUMBA_DISABLE_CACHING=1`（沿用 v4 惯例）、`PYTHONIOENCODING=utf-8`。

## 4. 基线改动说明（唯一代码触碰面）

`pipelines/current/routeA_run_formal_cross_loss.py` 新增可选旗标 `--candidate-dirs`
（格式 `"10=path,6=path"`；缺省空 ⇒ 行为与现状逐字节一致：candidate_dir_for_loss → authoritative 回退）。
`src/`、`experiments/`、`tools/` 零改动。该旗标仅为把候选目录指向 lossfix 命名空间，
不改变任何流水线语义（stage0/1/2/validation 调用序列原样复用 routeA 主流程）。
