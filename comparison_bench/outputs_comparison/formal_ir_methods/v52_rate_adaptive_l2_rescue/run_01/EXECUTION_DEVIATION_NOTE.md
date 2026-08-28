# V52 EXECUTION_DEVIATION_NOTE — DEVELOPMENT_RESULT_CANDIDATE_WITH_EXECUTION_PROTOCOL_DEVIATION

**只读说明 / Read-only deviation disclosure。未修改 `v52_records.*` / `v52_summary.json` 三文件内容，未运行第三次 decoder。**

## 身份绑定
- 仓库: `Placebo303/HD-QKD-Polar-pipeline`
- 分支: `formal-ir-mainline`
- Implementation SHA: `0a2833ecf78cfdd64e97529e13539e0726e247b3`（含 `f1e94e5c` 修复 + `0a2833ec` 测试，`comparison_bench/src/comparison_bench/formal_ir/v52_rate_adaptive_l2_rescue.py` 冻结）
- Plan SHA: `1d66b11917d229b214bd1d8b4255bf6df95c99c8`（`formal-ir-v52-rate-adaptive-l2-rescue`）
- Scope: `v52_nested_rescue_15_blocks_paired_exactly_once`（15 blocks, 15 L1 + 15 base_shared + ≤15 rescue = 30–45 总调用，硬帽45）
- Lifecycle: `DEVELOPMENT_RESULT_CANDIDATE_WITH_EXECUTION_PROTOCOL_DEVIATION`（科学结论可用，但执行协议偏离 `exactly_once` 导致不可直接归档为正式 `FORMAL`；需本说明伴随引用）

## 偏离事实（查证后记录）

### 1. 第一次命令 — 工具等待超时，无输出
- **命令**: `python scripts/execute_v52_nested_rescue.py --execution-authorized --authorized-target-sha 0a2833ecf78cfdd64e97529e13539e0726e247b3`（与第二次完全相同，未改参、未换样本、未改代码）
- **开始/终止**: 第一次调用在 `run_01` 三文件 `CreationTime 2026-08-28 11:52:53` 之前发起；终止于 **tool 120s timeout**（opencode 工具层超时），**无 stdout/stderr 输出、无退出码返回**（工具侧 `timeout` 中断等待，非 Python 进程 `exit 2/0`）。
- **退出状态**: `tool timeout (120s) — no output`；不等同于 `scripts/execute_v52_nested_rescue.py` 正常退出（正常应 `exit 0` 并打印 `V52P0 additive evidence written to ...`）。

### 2. 超时性质 — 工具等待超时 vs Python 进程终止
- 本次为 **工具等待超时（tool wait timeout）**，即上层调度器停止等待子进程输出，并非 `run_v52_diagnostic` 内部 `IntegrityFailure` / `FileExistsError` / `PermissionError` 导致的 `exit 2`，亦非 `main() -> 0` 正常完成。
- 因此第一次是否仍有 Python 子进程在后台持续运行，在工具超时瞬间 **无法从工具输出判定**；需单独确认进程残留（见 §4）。

### 3. 第一次已完成多少 decoder calls
- **0 次完成写入**。查证：
  - `run_01` 执行前 `partial_state` / `tmp` / 任何中间输出 **不存在**（`Test-Path partial_state* / tmp* -> False`）。
  - 第一次超时时 `comparison_bench/outputs_comparison/formal_ir_methods/v52_rate_adaptive_l2_rescue/run_01` 尚未创建（`run_01 执行前 False`，由任务报告确认）。
  - `run_v52_diagnostic` 为原子性 `fail-closed` 写入（已存在根则 `FileExistsError`，异常则保留 raw partial 无聚合）；本次未产生可恢复的 partial 聚合。
- 推断：超时发生在 **首个 block 的首个 L2/L1 译码完成前** 或日志刷新前，未落盘。

### 4. 第二次启动前是否确认旧进程完全退出
- **是。** 第二次启动前执行了后台进程排查，任务报告明确：**"后台无残留V52进程"**（`ps` / 任务管理器无 `execute_v52_nested_rescue` / `run_v52_diagnostic` 残留）。
- 确认后才发起第二次完整执行，避免并发写入 `run_01`。

### 5. 第一次是否创建过 partial/output 文件
- **否。** `run_01 执行前 False`（同 §3）。第一次未创建 `v52_records.*` / `v52_summary.json`，亦无 `partial_state.json` / `tmp` 残留可供 `resume`。第二次为全新 `run_01` 创建（`CreationTime 2026-08-28 11:52:53` 三文件同秒落盘）。

### 6. 第二次执行定性
- **第二次为"第二次完整执行产物"**，**不能称为 `exactly_once`**。
- 第二次与第一次 **未调参、未换样本、未改代码**：同 `authorized-target-sha 0a2833ec`，同 `393001..393205` 15 fresh blocks，同 `Δm=8 / leak_base 1064/1094/1104 / leak_joint 1104/1134/1144` 冻结参数。
- 科学等价性：两次执行输入确定性一致（`SeedSequence([60000x,1/2/3])` 增量矩阵、`BP_i` / `P_i(U2)` 确定性），第二次的 40 次 decoder calls（15 L1 + 25 L2: 15 base_shared + 10 rescue）结果与 `exactly_once` 假想产物在数值上一致，但因协议上已发生一次超时重试，**生命周期必须降为 `DEVELOPMENT_RESULT_CANDIDATE_WITH_EXECUTION_PROTOCOL_DEVIATION`**，不得直接用于 `FORMAL` 归档或晋升陈述。
- 三文件内容（`v52_records.csv/json` 25 行 L2 + `v52_summary.json` 40 calls）为第二次执行的完整、未篡改产物；本说明仅伴随说明，不改动其字节。

## 后果与使用约束
- 本次偏离不影响 `first_pass_success 5 / rescued 7 / final 12 / old 5` 等计数的科学可复现性，但影响 **执行协议合规性**。
- 引用 `run_01` 时必须同时引用本文件；`exactly_once` 断言无效。
- 满足 `DEVELOPMENT_RESULT_CANDIDATE_WITH_EXECUTION_PROTOCOL_DEVIATION` 的正式固化条件：**本只读说明存在 + 三文件 byte-identical + 无第三次 decoder 运行**。
- 后续若需 `FORMAL` 归档，需全新 cycle 以 `exactly_once` 重执行或经独立复审豁免。

## 动作约束（已遵守）
- 仅写文档，未改动 `v52_records.csv` / `v52_records.json` / `v52_summary.json` 字节。
- 未运行第三次 decoder。
- 本文件落盘于 `comparison_bench/outputs_comparison/formal_ir_methods/v52_rate_adaptive_l2_rescue/run_01/EXECUTION_DEVIATION_NOTE.md`（镜像见 `workspace/` 如需）。

---
*Generated: 2026-08-28 — coder-doc, read-only, no production code change.*
