# AGENT_HANDOFF

最后更新：2026-07-25 16:30（Asia/Shanghai）

本文件是本仓库当前状态的权威交接入口。`AGENT_PROJECT_MEMORY.md` 保留较长的背景与接口清单；如果两者对“当前状态”的描述不一致，以本文件和仓库内现有证据为准。

## 一页结论

- 项目已从多分支研究开发收口到 `main`；2026-07-25 刷新远端后，本地及远端可见分支均已进入 `main`，收口 merge commit 为 `bd18e07`。
- 当前可交付的是一条研究级 HD-QKD Polar 主线：`.ttbin` / timing input → E2E extraction → symbol mapping / sidecars → Polar actual-IR replay → Route A finite-key accounting → `PIE_main` / `SKR_main_bps`。
- Route A 的 correctness-side verification v1 已完成：四个 loss 共 `484/484` 个 formal rows，四份 validation 均为 `ok`，无 errors / warnings。
- Route B-lite 已完成并归档，结论是“局部有效、整体不稳定”的 limited / partial negative result；不得迁入主线。
- Route C / q-ary Polar 没有形成完整可交付主线；仓库中只有 nonbinary LDPC demo 入口，若重启 Route C 应作为独立研究任务。
- 项目还不是干净的可安装软件包：缺少自动化测试与打包元数据，README 有明显的跨项目内容污染，原始数据和约 39.1 GiB 本地结果不受 Git 管理。
- 因此当前判断是：**科学主线与历史结果已可交接；严格安全证明、发布文档和可重复安装仍未收口。**

## 当前进展

| 工作面 | 状态 | 当前证据 | 下一步 |
|---|---|---|---|
| E2E / Polar 前半链 | 已实现 | `experiments/run_e2e_pipeline.py`、`experiments/run_real_polar_max_pie.py`；本轮 `--help` 与 compileall 通过 | 有原始数据时做新目录 smoke，不覆盖权威结果 |
| actual-IR finite-key 主报告线 | 已建立 | `PIE_main`、`SKR_main_bps`，`main_result_source=actual_ir_finite_key` | 保持 proxy / shadow 字段为诊断用途 |
| Route A correctness v1 | 已完成 | 4 losses × 121 points；`484/484` formal rows；4 个 validation `ok` | 若论文要求严格证明，另立 proof-observable 工作包 |
| refined cross-loss 历史结果 | 已完成 | 4 个 loss 均 `121/121` actual coverage；refined 表中 positive actual rows 为 `312` | 只从 authoritative pack 引用 |
| Route A formal cross-loss 结果 | 已完成 | formal pack 中 positive actual rows 为 `293` | 不要和 refined pre-formal 的 `312` 混用 |
| Route B-lite | 已完成并归档 | 20 dB：47 improve / 46 degrade / 28 tie，中位改进为 0 | 停止扩展；除非有新的 symbol-offset / reliability-order 方案 |
| Route C / q-ary Polar | 未形成完整主线 | 无完整 q-ary encoder / decoder / replay / security 接口闭环 | 仅在明确立项后独立推进 |
| 工程发布质量 | 部分完成 | 源码可编译、入口可解析；无正式 test suite / package metadata | 先修 README、依赖声明和最小 smoke tests |

## 科学口径

当前默认报告字段：

```text
PRIMARY_REPORTING_MODE = actual_ir_finite_key
PIE_main
SKR_main_bps
main_result_source = actual_ir_finite_key
BETA_BASELINE_ROLE = comparison_only
NIU_2016_STATUS = not_supported_by_current_observables
```

Route A correctness v1：

```text
verification_protocol_id = uhv1_per_block
verification_family = universal_hash
verification_scope = per_block
verification_tag_bits = 32
epsilon_EC_bound = min(1, invoked_block_count * 2^-verification_tag_bits)
```

只允许声称 correctness-side verification interface 已形式化。不得声称已经完成 strict Zhong 2015 或 full Niu 2016 proof instantiation。

当前结果中的两组 cross-loss 数字属于不同阶段：

- refined pre-formal actual-IR pack：`cross_loss_positive_actual_rows = 312`；
- Route A formal correctness pack：`cross_loss_positive_actual_rows = 293`。

引用时必须标注所用 pack，不得把两者拼成同一条结果。

## 权威结果与代码入口

`results/` 被 Git 忽略。本机现有结果约 39.1 GiB，目录分区如下：

- `results/authoritative/`：当前可引用结果；
- `results/supporting/`：直接支撑材料；
- `results/diagnostics/`：诊断与探针；
- `results/archive/`：历史、Route B-lite 与 disposable 记录。

主要权威结果：

- `results/authoritative/_tmp_longrun_fresh_rerun`
- `results/authoritative/_tmp_minrerun_stageC_security_20dB`
- `results/authoritative/_tmp_minrerun_stageD_cross_loss`
- `results/authoritative/_tmp_routeA_correctness_formal_stageD_cross_loss`

主要当前入口：

- 前半链：`experiments/run_e2e_pipeline.py`
- Polar evaluation：`experiments/run_real_polar_max_pie.py`
- Route A current pipelines：`pipelines/current/`
- security reports：`tools/security_reports/`
- ASENoise：`tools/asenoise/`
- Route B-lite archive：`tools/archive/routeB_lite/`

不要再使用重构前的根级 `tools/routeB_*`、`tools/round2_*`、`tools/run_asenoise_*` 路径。

## Git 收口状态

2026-07-25 执行了：

1. `git fetch --all --prune`
2. `project-restructure-20260427` 快进合并到 `main`
3. `origin/main` 合并到 `main`
4. README 冲突保留较新的发布结构；远端旧提交只修正旧版 README 围栏，没有独立功能需要迁移

已核对为 merged 的本地分支：

- `codex/feat/polar-diagnostics-occupancy`
- `codex/route-c-q-polar`
- `project-restructure-20260427`

已核对为 merged 的远端分支：

- `origin/codex/feat/polar-diagnostics-occupancy`
- `origin/project-restructure-20260427`
- `origin/main`

分支引用尚未删除。保留它们不影响主线；确认不再需要恢复点后可另行删除。当前另有：

- detached worktree：`C:/Users/admin/.codex/worktrees/10ed/HD-QKD_Polar_Release`，停在 `62a16dd`；
- 两个旧 stash，内容是 cross-correlation 初版及其 `ttbin_pipeline` 配套修改；当前主线已有更完整实现，本轮未删除 stash。

不要在未核对 worktree 与 stash 的情况下做批量删除。

## 本轮验证

通过：

```powershell
python -m compileall -q src experiments pipelines tools analysis
python -c "..."  # universal-hash verification transcript smoke
python experiments\run_e2e_pipeline.py --help
python experiments\run_real_polar_max_pie.py --help
python pipelines\current\routeA_run_formal_cross_loss.py --help
python tools\security_reports\round2_build_finite_key_audit_table.py --help
python tools\asenoise\export_ttbin_cross_correlation.py --help
```

环境：

```text
Python 3.12.12
numpy 2.4.0
scipy 1.16.3
```

本轮未运行：

- 原始 `.ttbin` 读取；
- C++ decoder 全量回放；
- full-grid Polar；
- Route A full cross-loss rerun；
- ASENoise full replay。

因此本轮验证证明“代码可解析、关键 correctness helper 可运行、历史结果证据齐全”，不证明在当前机器上完成了端到端全量复现。

## 已知阻塞与风险

优先级 P0：

1. `README.md` 的 Installation / Minimal Example / Known Issues 段落混入了不属于本项目的 `yfinance`、trading day、`--skip-llm`、`--operator-gate` 等内容。
2. README 写了 `pip install -e .`，但仓库没有 `pyproject.toml`、`setup.py` 或 `setup.cfg`。
3. README 的 dependency table 与 `requirements.txt` 不一致；`.ttbin` 还依赖外部 `TimeTagger` runtime。
4. `main` 尚未推送；在本 handoff 提交后预计相对 `origin/main` ahead 18。推送前用 `git status --short --branch` 重新确认。

优先级 P1：

1. 没有正式 test suite；目前只有 compileall、CLI help 与历史结果 validation。
2. `results/` 完全被忽略；fresh clone 不含权威结果，发布时需要独立 artifact manifest / 校验和 / 下载方式。
3. 文档仍含 Windows 绝对路径；新命令优先写 repo-relative path。
4. `AGENT_PROJECT_MEMORY.md` 含一部分 memory-derived / uncertain 内容，不能替代本轮实测证据。

## 下一步建议

最短收口顺序：

1. 清理 README 的跨项目内容，只保留真实 CLI 参数和安装前提。
2. 决定项目是“脚本仓库”还是“可安装 package”；如果只是脚本仓库，删除 `pip install -e .`，无需增加打包框架。
3. 补 2–3 个最小 smoke tests：runtime path、universal-hash transcript、一个不读 raw data 的 security-table fixture。
4. 为 authoritative result pack 生成文件清单与 SHA-256；不要把 39.1 GiB 结果直接提交进 Git。
5. 核对后推送统一 `main`；暂时没有继续保留活跃开发分支的必要。只有高风险实验、多人并行或 Route C 独立立项时再开新分支。

推送前检查：

```powershell
git status --short --branch
git branch --no-merged main
git branch -r --no-merged main
git log --graph --decorate --oneline -n 25
```

## 不可破坏的边界

- 不覆盖 `results/authoritative/`。
- 新实验必须写入新的、明确命名的 ignored output root。
- 不提交 raw `.ttbin`、本地结果包、cache 或 workspace artifact。
- 不静默修改 CSV schema、CLI 参数、security constants、epsilon budgets、verification tag bits 或 main reporting semantics。
- 不把 proxy / shadow / estimate 指标写成最终 secure result。
- 不把 Route B-lite 迁回主线。

## 参考文档

- `docs/CURRENT_MAINLINE.md`
- `docs/PROJECT_CLASSIFICATION_20260427.md`
- `docs/RESULTS_MANIFEST_20260427.md`
- `docs/RESULTS_INTERPRETATION.md`
- `docs/SECURITY_MODEL.md`
- `docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md`
- `docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md`
- `docs/archived_studies/routeB_lite/ROUTE_B_LITE_FINAL_SUMMARY_20260415.md`
