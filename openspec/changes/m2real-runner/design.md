# M2REAL Runner — Design

Status: implementation-only 冻结。本文件冻结单文件决策与 assumed 销项；**不授权执行，不填 Müller 真值**。

## 1. 单文件决策（one additive module）

无既有 campaign CLI 能逐字跑 M2-REALCOMP 冻结网格（M0 只跑 NB 臂；`m2hdc/m2lb_arm_runner` 只跑合成 240 块采样臂），故新增**唯一** additive 模块 `comparison_bench/src/comparison_bench/cli/m2real_runner.py`（约 600 行），复用 `m2hdc/m2lb_arm_runner` 单文件先例结构（双旗门 + 根门 + `execute()` + fake 注入 + `block_accounting_csv` + `result_markdown`）。拒绝替代方案：在 `m2hdc/m2lb` 内加真实分支（污染冻结合成臂语义）、复用 `run_ir_benchmark` 通道（无 A-CMPE 冻结列）。

## 2. T0 open 状态（`m2-honest-baselines/design.md` 继承）

- Müller 待澄清表**仍 open**：本 runner 引用 `m2hdc.provisional_block_table()` 的 assumed-v1 值（[8,4]/cross1/floor1/max_passes4），每产物标注 `assumed-v1（Mueller 待澄清表待核对）`；`require_assumed_block_table()` 在每次执行入口校验字面相等 — 上游一旦填入真值即 refuse（STOP），须经 `/opsx-explore` 重冻后才可跟进。
- LB 盲增量：真实块只跑单 full-m 解码（matched 语义）；`blind_table_for` verbatim 校验 + report-only 记录（`blind_status` 列）；盲救援段会计列保留（fake/生产 outcome 均 13/11 键约束）。
- LB 逐块构造：per-block 1-frame 调用下 `frame_idx` 恒 0，同一臂内构造种子恒为冻结 2026092001（单码复用多块；方法字面约定 verbatim，未改；grant-time 可复议）。

## 3. 帧映射 BLOCKED 已解为 assumed（单 assumed 项）

1024 符号超帧 → 16×64 连续块、无余数（16×64 = 1024 精确整除）为**唯一 assumed 帧映射**（用户已冻）。`slice_real_blocks()` 强制：块长恒 64、每超帧恒 16 块、符号越出 0..1023 即 refuse（1024→64 之外新映射即 STOP）。超帧 success = 16 全 exact；leak 超帧求和；FER 分母恒为块数（3280/4592/6128 期望值记录 + `slice_match` 布尔，不做执行期 refuse —— fake 测试用 mock 小数组必须可跑；生产漂移由 m0 上游断言 + grant-time Pre-EXECUTE 复核）。

## 4. 种子规则（递增 + 双系区分）

- HDC：`(source, m) → 5701 系基址`（只读派生自 `m2hdc.M2HDC_ARM_SEED`，越界即 STOP）；块种子 = 基址 + 全局块序号 g。
- LB：`5601 基址`（只读 `m2lb.M2LB_BLOCK_BASE`，漂移即 STOP）；块种子 = 基址 + g；构造种子沿方法字面约定（2026092001 + frame_idx，见 §2）。
- 流标签 `o1_blk:{seed}` 全产物携带；真实臂零合成采样（模块内无采样器、无 `empirical_triple` 路径；除 m0 链外零 ttbin 扩展名字符）。

## 5. H 基双轨（f vs 校验器）

- 报告 f（`f_super/f_notag/f_eff`，D2 去 tag 口径）：M0 §3 `H_corr`（0.8012690084416184 / 0.8272902027770036 / 0.8333327179427281，只读 `m0.H_CORR`），`H_column = measured`。
- 方法校验器输入（`HdCascadeParams.h_basis` / `PlaneAllocation.h_basis` 的 verbatim 合成 F03 H 检查）：按冻结方法契约通过，不进 f 分子，产物注记 `assumed（denominator input only, no refit）`。分配行数本身与 H 无关（equal-share 整除），故双轨无数值冲突。

## 6. 会计与门（A-CMPE 全列映射）

- A-CMPE-1：四计数 + `undetected` 独立列；A-CMPE-2：f 三数分立行（presentation ban 结构化）；A-CMPE-3：`leak_EC + 64 tag + rescue + control + blind_stage` 单列分解；A-CMPE-4：wall/每块 wall/RSS/每块消息数（446 vs 3.14 独立口径）；A-CMPE-5：`N_req` report-only vs key-eligible（200/276/364）+ `d/q/n_IR` 分离 + 三组计数分离；A-CMPE-6：M0 行指针化（不抄数）+ F9(i) 全表标注；A-CMPE-7：claim 禁句（§8 逐字）+ measured/assumed/projected/qualified 四列归属（qualified 空）。
- D2：臂 `f_notag` 输入 + 规则逐字 + `DEFERRED`（待 M0 NB refs + 独立 Pre-RESULT）；本 runner 不计算 D2 分支标签。
- 预算门：源 wall 5400（超即 `INCOMPLETE-wall` 留存不续跑）、单解码 300（超即该块 fail 不重跑）、RSS 4 GiB（超即 `FAIL(budget-rss)` 停该源）、1 CPU（无并行代码）。
- 停机：F1–F7 任一改动需求、断言失败、新映射/种子外规则/Müller 真值填数 ⇒ STOP 回主线程（`refuse` rc=2）。

## 7. Explicitly not in design

- 授权、执行、Pre-EXECUTE/Pre-RESULT、M0 重跑、M0 数值复制、SKR/发表主张、acceptance、commit/push。
- Müller 真值、盲增量真实跑、u1 纠错进恢复链（= 新包，M0 数字不得回溯改写）。
