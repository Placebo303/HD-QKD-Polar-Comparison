# Tasks: V70R1 Parametric Channel Model Check

**Lifecycle**: `DEVELOPMENT_RESULT_CANDIDATE / DECODER_FREE_EXECUTION_COMPLETE` / `V72_NOT_STARTED=true` — `f_actual=NOT_MEASURED` `decoder_calls=0` `used_test=false` — `3SHA 0509d10b/179916f7/36d493d8`
**HEAD**: `EXTERNALLY_BOUND_AT_PRE_EXECUTE` — 非自引用（`current_parent` `082fa89a`，不自引用未来 SHA；占位已删） **accepted_plan_sha** `0509d10ba78902b36f6bcf447f1ebfe289e03fc89b` (`0509d10b` revised_plan) **initial_implementation** `179916f7cfec0ea469683bb78083c3752700193d` **execution** `EXTERNALLY_BOUND_AT_PRE_EXECUTE` (`HEAD == origin/formal-ir-mainline` 推送后由 Pre-EXECUTE 外部核对) **Data SHA**: `84d62779` **Predecessor V71**: `6bc06d4d..487be113` latest `487be113` (`487be11387a5a68c275c43ccb5528ec700bfd3d3`) **Predecessor V70**: `9bc34be64a2822c8babb4320efb47fc7e335a21a`

## Phase A — 绑定与复用（无新数据）

- [x] **A1 复用 V70 registry**：直接读 `v70_data_registry.json` 的三 session 与 `stage2_CAL_frame_ids`(1024) / `stage2_VAL_frame_ids`(256)，不新建 registry、不换帧、不扩样。脚本内断言 `len(a_cal)==262144 && len(a_val)==65536`，每帧 256 对。
- [x] **A2 绑定 V70 权威值**：读 `v70_table.json` 的 `CE_full_VAL`（`7.150000879558332 / 7.547198 / 8.390100`）作为 M0 复现基准，落盘 `v70_reproduction {v70_CE_full_VAL, recomputed, abs_delta, reproduces}`。
- [x] **A3 SHA 绑定（已清理验收）**：`HEAD == origin/formal-ir-mainline` 推送后重核；`accepted_plan_sha` `0509d10ba78902b36f6bcf447f1ebfe289e03fc89b` (`0509d10b` revised_plan) 仅四文件（`proposal/design/tasks/specs`）且为 `179916f7` 后继；`git diff -- src/ == 0` 已核；四终态一致。

## Phase B — 三模型实现（decoder-free）

- [x] **B1 M0**：`hierarchical_P` 与 `select_lambda_table`，与 V70 逐位相同（同 `LAMBDA_GRID` 30 点、同 4-fold、同 `N_b==0` 回退）。
- [x] **B2 M1**：`delta_hist` + `fit_circulant` + `select_lambda_circulant`，CAL-only 选 `λ_K`，`K` 归一化。
- [x] **B3 M2**：`m2_shape`（三周期环绕、`δ_signed` 居中）+ `m2_nll_over_eps`（ε 向量化）+ `fit_m2`（`μ×s` 确定性网格）+ `select_m2_family`（CAL 4-fold CV 二选一）。
- [x] **B4 CE 只经直方图**：`ce_from_kernel` 从 1024 格直方图直算，M1/M2 的 CAL 拟合与 VAL 评估均不重扫 pairs。

## Phase C — 诊断量

- [x] **C1** `CE_*_VAL` / `CE_*_CAL` / `cal_val_nll_gap` 三模型分别落盘。
- [x] **C2** `map_accuracy_VAL`（M0 走 `argmax` 行，M1/M2 走 `hist[argmax K]`）与 `fano_upper_bound_diagnostic`，**标注为上界诊断**。
- [x] **C3** `required = ceil(1.3·1024·CE_VAL)` 不 cap、`gap = 10240 − required`、`margin_gap`、`f_max_channel_ceiling`、`classification`（沿用 V70 三分流阈）、`n_parameters`。
- [x] **C4** `sample_curve`：CAL 前缀 `32/64/128/256/512/1024` 帧，三模型各自仅重拟合 μ/s/ε（λ/λ_K/M2族固用全量1024帧CAL选出值，不做每前缀4-fold重选）<!-- ponytail: 固参版sample_curve，每前缀仅重拟合μ/s/ε，λ固用全量CAL值；不做每前缀4-fold重选以避免小样本高方差与O(6×4)成本，待大样本再考虑每前缀重选 -->，**同一 VAL** 评估；descriptive-only，不触发终态（原 `REDUCES_ESTIMATION_COST` 已删除）。
- [x] **C5** `delta_mass {mass_0, mass_p1, mass_m1, other}` on VAL，用于与 V56 诊断的 8 帧先验对照。

## Phase D — 终态分流

- [x] **D1 五终端 first-match 互斥**：`EVIDENCE_INVALID` > `TRANSLATION_INVARIANCE_REJECTED` > `CHANGES_CAPACITY_ROUTE` > `REDUCES_VAL_CE (route==false && ΔCE>=0.10)` > `NO_VALUE`（cost `sample_curve`/`estimation_cost_win` 仅 descriptive-only 不参与分流）。机械重分类：1M REDUCES / 1p5M CHANGES / 2M REDUCES / overall CHANGES（不重跑）。
- [x] **D2 Overall** 按同序在三 session 聚合，落盘 `terminal_counts` 五计数（`REDUCES_VAL_CE` / `NO_VALUE` 分离）。
- [x] **D3 非声称落盘**：`ce_decomposition_claimed: false`、`planning_f_is_not_achieved_f: true`、`used_val_in_selection: false`、`used_test: false`、`V71_not_started` 改为 `V72_not_started` 语义（V71 已完成）；`plan_revision` 记录 5 终态机械修订（`REDUCES_VAL_CE` 插入，cost descriptive-only，不重跑）。

## Phase E — 工件与自检

- [x] **E1 脚本**：`scripts/v70r1_parametric_channel_model_check.py`，`py_compile` PASS，`rg "decode_"` 0 hits，仅 `numpy/pandas/pyarrow`。
- [x] **E2 小测试**：`test_v70r1_parametric_channel_model_small.py`，20 项纯函数/合成数据测试，`pytest -q` **20 passed**（核归一化、平移不变核 CE 恒等、两点模型闭式、planted 参数回收 `μ≤0.25 / ε≤0.05`、`required` ceil 不 cap、`f_max` 恒等、三分流边界、V70 三行分类复现、Fano 单调与 `acc=0.4149→6.830`、`hierarchical_P` 公式与空行回退、终端有序唯一、网格冻结、decoder-free 源码检查）。
- [ ] **E3 执行回填**（需 `EXECUTE_AUTH`）：运行脚本得 `v70r1_results.json` + `v70r1_table.csv/.json`，回填本节与报告。
- [ ] **E4 报告**：`V70R1_PARAMETRIC_CHANNEL_REPORT.md`，per-session 三模型对照表 + 样本曲线（descriptive-only） + 四终端 + overall，与 json/csv 行对等，无 TBD。
- [ ] **E5 守卫 R70R1-01~10 落盘**：`v70r1_manifest.json:guards` 逐项 `true`（见 Design §7）。

## Phase F — 提交与等待复核

- [x] **F1 单独提交推送**四工件 + 脚本 + 小测试，返回新 Plan SHA，替换 `proposal/design/tasks/specs` 的 HEAD 占位。（`accepted_plan_sha` `0509d10ba78902b36f6bcf447f1ebfe289e03fc89b` 已写入四文件；`current_docs_head` 为本提交）
- [x] **F2 补齐** `DEVELOPMENT_RESULT_CANDIDATE / DECODER_FREE_EXECUTION_COMPLETE`：写入 `3SHA` `f_actual=NOT_MEASURED` `decoder_calls=0` `used_test=false` `V72_NOT_STARTED=true`，REPORT 扩逐源×三模型 9字段完整表 + `PRE_RESULT_ORDERING_DEVIATION`，新增6项测试，推送。

## Phase G — 补齐（R2 descriptive-only 固化）

- [x] **G1** REPORT 逐源×三模型 9字段完整表（CE_VAL/CE_CAL/cal_val_gap/MAP/fano/required/gap/margin/f_max/classification/params 中取9字段），明确 M0 cost descriptive-only 不触发终态，`R2 rerun=false`
- [x] **G2** `PRE_RESULT_ORDERING_DEVIATION`：记录 overall 首个非零终态 ordering vs 计数最多者 deviation（CHANGES 1 vs REDUCES 2）
- [x] **G3** 6项新增测试覆盖 lifecycle/3SHA/f_actual/decoder0/used_test/V72/9字段/ordering deviation

## 本变更显式禁止

重做输入合同或读 ttbin（V56R4 已接受 `TRUE_SESSION_DOMAIN_SHIFT`）；换处理点或做 `bin_width/dimension/pairing/mapping` 网格；用 VAL/TEST 择优 `λ/λ_K/M2 族/μ/s/ε`；读密封 TEST；改 `src/` 或 V70/V71 任何冻结数值与工件；把 `required` cap 在 10240 或用 `floor/round` 替 `ceil`；改规划因子 `1.3` 并宣称效率提高；**声称把 CE 分解为 `H_true + KL`** 或把 Fano 上界当作 `H` 的估计；报告任何 `f_actual`（decoder-free 轮次必须 `NOT_MEASURED`）；用 `0/4/10 dB` 同源梯度参与模型选择；创建 `run_01`；启动 V72 或预冻结 V72 OpenSpec；宣称 `FER/SKR/阈值/晋升/安全证明`；保留 TBD 占位。

## 验收

- `proposal/design/tasks/specs` 一致，HEAD `EXTERNALLY_BOUND_AT_PRE_EXECUTE` 非自引用（`current_parent` `082fa89a`，`accepted` `0509d10b` revised_plan / `initial` `179916f7`，`execution` `EXTERNALLY_BOUND_AT_PRE_EXECUTE` 由 Pre-EXECUTE 外部核对 `HEAD == origin/formal-ir-mainline` 推送后重核），`6bc06d4d..487be113` latest `487be113` `V71_KERNEL_ADAPTER_FEASIBLE / ADAPTER_REQUIRED` successor `v71_kernel_adapter_design`，Data `84d62779`，lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED=true`，V70 数值不变；仅四文件为 `179916f7` 后继，四终态一致。
- 三模型预注册（M0 表 / M1 circulant / M2 wrapped Gaussian-或-Laplace + 背景），M2 族由 CAL 4-fold CV 二选一已实现，VAL 只确认一次。
- CAL/VAL 帧复用 V70 已实现并断言；M0 复现 V70 `CE_full_VAL` 作为 `EVIDENCE_INVALID` 前置已实现。
- `required` 显式 ceil 不 cap、`gap` 显式、三分流阈与 V70 一致、`f_max` 与规划 `1.3` 分离已实现。
- 四终端 first-match 互斥完备、overall 同序聚合已实现。
- 样本需求曲线 `32..1024` 帧同一 VAL 已实现（descriptive-only，不触发终态）。
- 非声称字段 `ce_decomposition_claimed=false` / `planning_f_is_not_achieved_f=true` 已落盘。
- `py_compile` PASS，`pytest` 20 passed，`git diff -- src/ == 0`，`rg "decode_"` 0 hits，未建 `run_01`，未启 V72。
- **E3–F2 待 `EXECUTE_AUTH` / 推送后独立复核。**
