# AGENT_HANDOFF

最后更新：2026-08-12（Asia/Shanghai）

本文件是本仓库当前状态的权威交接入口。`AGENT_PROJECT_MEMORY.md` 保留较长的背景与接口清单；如果两者对“当前状态”的描述不一致，以本文件和仓库内现有证据为准。

## 2026-08-12 V3 科研口径收口（当前主入口）

- V2 Q3 四损耗 back-half 已完成；最终只读重建位于 `results/paper_grade_v3/reconciled_stage2_20260812_final_v3/`，共 `484/484` 可报告 reconciliation rows，四份 formal validator 均通过。
- 主指标改为 `PIE_reconciled_net=max(0,(total_kept_info_bits-total_leak_ec_bits)/n_pairs_actual)` 与 `SKR_reconciled_net_bps=PIE_reconciled_net*coincidence_rate_hz`。`PIE_main/SKR_main_bps` 只映射到这两个字段。
- 主指标的论文表述只能是“公开 EC 泄漏扣除后的净共享比特/率”，`claim_boundary=public_ec_only_not_secure`；它不是 secret-key rate，也不含 Eve 信息、phase-error/parameter-estimation 或 privacy amplification。
- 旧 `PIE_secure_actual_ir/SKR_secure_actual_ir_bps` 存在接受率归一化的量纲不一致，现仅为兼容诊断字段；全部标记 `scientifically_blocked_dimensional_inconsistency` 与 `diagnostic_only`，不得引用为论文结果。
- Stage 0 已移除缺失采集时长时的 5 s 回退，并恢复 occupancy sidecar 解析；缺失可核验速率来源时主指标 fail closed。V3 使用 authoritative candidate grid table 中保留的 measured rate，484 行均记录来源标签。
- 复现命令、统计摘要与声明边界见 `docs/POLAR_RECONCILED_RESULT_V3.md`。上一版 V2 Stage 2 表不得替代 V3 主表。

## 2026-08-11 Polar 论文级 V2 更正（优先阅读）

- 历史 Route A v1 的 `484/484` 结果继续保留，但已降级为历史工程证据，不能再作为论文级 correctness 结果引用。
- 已完成的 V2 代码更正包括：任意信息位普通 SCL 最小路径度量、随机且记录的 Toeplitz 验证种子、确定性候选随机种子、单侧 Wilson FER 验收、逐层 PIE/元数据一致、有效样本去除 block-success 双计数、非 composable 安全标签。
- 冻结规范与审计证据分别见 `docs/POLAR_PAPER_GRADE_QUALIFICATION_V2.md` 和 `docs/POLAR_PAPER_GRADE_AUDIT_V2.md`。
- Q0 组合测试通过；Q1 同种子单点两次输出一致；四损耗 d4/20 ps 的 decoder/replay canary 均无解码或验证失败。
- 32-bit tag canary 的联合上界为 `1.40e-9` 至 `1.26e-8`，超过 `eps_cor=1e-10`，因此已判定预算失败；主参数已在全量 replay 前改为 64 bit。未完成的 tag-32 全量指标任务保存在 `results/paper_grade_v2/four_loss_parts_tag32_budget_failed/`，不得引用。
- tag-64 Q2 已在 20/16/10/6 dB 的 d4/20 ps 代表点重新通过：分别审计 6/15/54/54 块，全部解码匹配且验证通过，联合上界 `3.25e-19` 至 `2.93e-18`。Q3 可据此重新启动；只有四份 loss-specific validator 均无错误且 `epsilon_EC_bound <= 1e-10` 后才允许合并或升级结论。
- tag-64 Q3 已完成，冻结 Stage 1 位于 `results/paper_grade_v2/four_loss_parts_tag64/`；经 V3 Stage 2 口径修正后，四损耗 validator 均通过。
- 既有 `results/authoritative/` 未被覆盖；V2 仅写入 `results/paper_grade_v2/`。
- 当前安全边界：V2 的 reconciliation/correctness 可做论文级资格审查；visibility/finite-size 输出仍是 calibrated model-based non-composable shadow，缺失 protocol-specific phase-error 与 parameter-estimation observables。

## 一页结论

- 项目已从多分支研究开发收口到 `main`；2026-07-25 刷新远端后，本地及远端可见分支均已进入 `main`，收口 merge commit 为 `bd18e07`。
- 当前工程主线为 `.ttbin` / timing input → E2E extraction → symbol mapping / sidecars → Polar actual-IR replay → Route A reconciliation/correctness accounting；论文引用使用 V3 public-EC-only 主表。
- Route A correctness v1 的四损耗 `484/484` formal rows 是历史结果；其公开标签派生 hash 与 CA-SCL 口径不满足 V2 论文级资格。
- Route B-lite 已完成并归档，结论是“局部有效、整体不稳定”的 limited / partial negative result；不得迁入主线。
- Route C / q-ary Polar 没有形成完整可交付主线；仓库中只有 nonbinary LDPC demo 入口，若重启 Route C 应作为独立研究任务。
- 项目明确定位为从仓库根目录运行的脚本仓库，不引入无用途的 Python package scaffolding。
- P0/P1 工程收口已完成：README 和依赖已校正，维护文档使用相对路径，5 个 raw-data-free smoke tests 已建立，9 个 authoritative packs 已生成并复验 tree SHA-256。
- 原始数据和约 39.1 GiB 本地结果仍不受 Git 管理；其中 authoritative packs 有 12,542 个文件，由 tracked checksum manifest 覆盖。
- 因此当前判断是：**科学主线、历史结果与基础发布治理已可交接；严格安全证明和 raw-data 全量复现仍是更高阶段工作。**

## 当前进展

| 工作面 | 状态 | 当前证据 | 下一步 |
|---|---|---|---|
| E2E / Polar 前半链 | 已实现 | `experiments/run_e2e_pipeline.py`、`experiments/run_real_polar_max_pie.py`；本轮 `--help` 与 compileall 通过 | 有原始数据时做新目录 smoke，不覆盖权威结果 |
| actual-IR reconciled-net 主报告线 | 已通过 | V3 `484/484` rows；四份 formal validator；主字段恒等式通过 | 仅按 public-EC-only、not-secure 口径引用 |
| Route A correctness v1 | 历史工程证据 | 4 losses × 121 points；`484/484` formal rows；4 个 validation `ok` | 不再作为论文级 correctness 引用；使用 V2 |
| Polar correctness V2/Q3 | 已完成 | `results/paper_grade_v3/reconciled_stage2_20260812_final_v3/`；4×121 rows | 冻结并使用 V3 报表 |
| refined cross-loss 历史结果 | 已完成 | 4 个 loss 均 `121/121` actual coverage；refined 表中 positive actual rows 为 `312` | 只从 authoritative pack 引用 |
| Route A formal cross-loss 结果 | 已完成 | formal pack 中 positive actual rows 为 `293` | 不要和 refined pre-formal 的 `312` 混用 |
| Route B-lite | 已完成并归档 | 20 dB：47 improve / 46 degrade / 28 tie，中位改进为 0 | 停止扩展；除非有新的 symbol-offset / reliability-order 方案 |
| Route C / q-ary Polar | 未形成完整主线 | 无完整 q-ary encoder / decoder / replay / security 接口闭环 | 仅在明确立项后独立推进 |
| 工程发布质量 | P0/P1 已完成 | README/requirements 已校正；5 个 unittest smoke tests；9 个 authoritative pack digests 已复验 | 有 approved artifact host 后再发布大结果包 |

## 科学口径

当前默认报告字段：

```text
PRIMARY_REPORTING_MODE = actual_ir_reconciled_net_not_secure
PIE_main
SKR_main_bps
main_result_source = actual_ir_reconciled_net_not_secure
claim_boundary = public_ec_only_not_secure
BETA_BASELINE_ROLE = comparison_only
NIU_2016_STATUS = not_supported_by_current_observables
```

已知问题（2026-08-14 确认，详见 `docs/decision-log.md`）：`post_selection_correction` 把 0–1 的接受帧比例当作 bits/symbol 从旧 `PIE_secure_actual_ir`/`PIE_secure_beta_baseline` 中减法扣除，属量纲错误 + 重复计入。旧列已 blocked/仅诊断，当前主口径（reconciled net）不受影响；`PIE_secure_beta_baseline` 解读时须注明 ~1 bit/sym 的系统性下偏。

历史 Route A correctness v1（仅供 provenance，不再作为 V2 主口径）：

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

完整的 9-pack 文件数、字节数与 tree SHA-256 位于：

- `docs/AUTHORITATIVE_RESULTS_CHECKSUMS.json`
- 生成/验证工具：`tools/verify_authoritative_results.py`

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
python -m unittest discover -s tests -v
python -m compileall -q src experiments pipelines tools analysis tests
python experiments\run_e2e_pipeline.py --help
python experiments\run_real_polar_max_pie.py --help
python pipelines\current\routeA_run_formal_cross_loss.py --help
python tools\security_reports\round2_build_finite_key_audit_table.py --help
python tools\asenoise\export_ttbin_cross_correlation.py --help
python tools\verify_authoritative_results.py --verify docs\AUTHORITATIVE_RESULTS_CHECKSUMS.json
```

Smoke tests 覆盖：

- portable results/runtime path；
- universal-hash verification transcript；
- deterministic authoritative pack digest；
- 小型 finite-key security-table fixture；
- active docs 的本机绝对仓库路径与跨项目 CLI 污染回归。

环境：

```text
Python 3.12.12
numpy 2.4.0
```

本轮未运行：

- 原始 `.ttbin` 读取；
- C++ decoder 全量回放；
- full-grid Polar；
- Route A full cross-loss rerun；
- ASENoise full replay。

因此本轮验证证明“代码可解析、关键 correctness helper 可运行、历史结果证据齐全”，不证明在当前机器上完成了端到端全量复现。

## P0/P1 完成记录

P0：

1. README 中的 `yfinance` / trading / LLM/operator-gate 污染已删除。
2. 仓库已明确为 script repository；删除无效的 `pip install -e .`，未增加无用途的 package scaffolding。
3. `requirements.txt` 与实际 tracked Python imports 对齐；`TimeTagger` 和 `g++` 作为外部/系统依赖单独说明。
4. 统一 `main` 在本轮验证、提交后推送。

P1：

1. `tests/test_smoke.py` 提供 5 个 raw-data-free unittest smoke tests。
2. `docs/AUTHORITATIVE_RESULTS_CHECKSUMS.json` 覆盖 9 个 authoritative packs；生成后已立即完整复验。
3. README、当前 mainflow 和 latest-results 文档已使用 repo-relative links；历史 raw-data path 只保留为 provenance，不作为新命令默认值。
4. `AGENT_PROJECT_MEMORY.md` 顶部已明确标为 historical orientation；当前状态以本 handoff 为准。

## 剩余外部边界

这些不是未完成的 P0/P1 代码项：

1. 仓库没有 approved artifact host，因此 authoritative results 仍通过受控文件传输获得；checksum 可验证完整性，但不提供虚构下载地址。
2. 外部 ASENoise master CSV 不在 `results/authoritative/`，因此不在当前 checksum manifest 覆盖范围内。
3. fresh clone 不含 raw `.ttbin`、Swabian `TimeTagger` runtime 或约 39.1 GiB 本地结果。
4. 本轮未执行 raw-data E2E、full-grid Polar 或 full Route A replay。
5. strict Zhong 2015 / full Niu 2016 proof instantiation 仍未完成。

## 下一步建议

1. 配置 approved artifact host 后发布 authoritative pack，并用现有 checksum 工具验证上传/下载副本。
2. 在具备 raw data、TimeTagger 和 decoder toolchain 的机器上运行一个新输出目录 E2E smoke。
3. 只有高风险实验、多人并行或 Route C 独立立项时再创建开发分支。

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
