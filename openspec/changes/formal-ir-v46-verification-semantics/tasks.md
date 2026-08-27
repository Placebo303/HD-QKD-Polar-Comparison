# OpenSpec Tasks: formal-ir-v46-verification-semantics

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V47。**
**Execution status**: 本轮不授权任何实现/执行；以下任务待独立 plan ACCEPT 后方可进入 A-phase；当前不跑 decoder，不写产出。

## Phase A — 语义冻结（plan ACCEPT 后）

- [ ] **A1** 冻结 tag 语义常量：`tag = trunc64(SHA256(canonical_bytes(x_hat)))`（前 8B, big-endian），`canonical_bytes` 打包方式（定长 `n` bytes / `q=32` 5-bit 打包）二选一冻结，L2-only `x2_hat` vs `x1_hat||x2_hat` 明确其一；与 `SOURCE_L2_TAG_BITS` 的 `984/1014/1024` 含 64 计费一致，不新增泄漏。
- [ ] **A2** 冻结重分类语义：`wrong_codeword = syndrome_ok && !exact` → `tag_mismatch → detected_failure`，`tag_match && !exact → undetected_error (≈2^-64)`；`exact_l2` 仍 oracle 判真；pre-tag 时序（`wrong/G3/exact` 在 verification 之前）断言。
- [ ] **A3** 冻结终态可区分：`verification failure`（detected）vs `structure failure`（`!syndrome_ok && !exact`）vs `undetected` 正交计数与 `reason_code`；`wrong_codeword_reclassified_as_detected` 度量。
- [ ] **A4** 冻结只读输入与隔离根：V45 `v45_records.json/.csv` + `v45_summary.json` 只读；增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/` fail-closed；最小三件套文件集与无 NPZ 约束。
- [ ] **A5** 冻结 390221 边界：同 `errors_final=3` 不等同同码字，未保存 `x_hat/hash` 的历史记录标记 `verification_not_applicable_missing_hash`，不补造。

## Phase B — 只读复核（decoder-free，零新 decoder invocations）

- [ ] **B1** 只读加载 V45 18 L2 records，校验 `wrong_codeword_l2 = syndrome_ok && !exact` 定义与 `G3` pre-tag 时序一致性；记录 `leakage_already_accounted` 声名与 `984/1014/1024` 一致性。
- [ ] **B2** 对含 `x_hat` 的记录重算 `tag_hat/tag_true` 并比对 `verification_accept`；重分类 `detected/undetected/structure` 并汇总 `verification_summary`（detected/undetected/structure 计数）。
- [ ] **B3** 校验 V45 输出 byte-identical（mismatch → invalid），校验无 NPZ 写、无 V45 文件改动。

## Phase C — Decoder-free 自检（可选，fake fixtures）

- [ ] **C1** `tag_of` 确定性：同 `x_hat` 多次调用 tag 等值；截断 64-bit 正确；`canonical_bytes` 归一化跨端一致。
- [ ] **C2** 分流正确：`syndrome_ok && !exact && tag_mismatch → detected`，`tag_match && !exact → undetected`，`!syndrome_ok → structure`。
- [ ] **C3** 边界：缺 `x_hat/hash` → `verification_not_applicable_missing_hash`，不判 invalid；`exact_l2` 仍以 oracle 为准，不被 verification 覆盖。

## Phase D — 隔离写出（需 EXECUTE_AUTH，仍零新 decoder invocations）

- [ ] **D1** 获独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V46P0、scope `v46_verification_semantics_readonly_once`，HEAD `f59ab60a`）。
- [ ] **D2** 恰好一次：`python scripts/verify_v46_tags.py --execution-authorized --authorized-target-sha <sha>`（decoder-free）；写增量根三件套 `v46_records_verify.json/.csv` + `v46_summary.json`（含 detected/undetected/structure + leakage 已计声名 + provenance）+ 失败时 `v46_invalid_notice.json`；CSV/JSON 行对等；不写 NPZ。
- [ ] **D3** 只读 postcheck：18 行复核视图完整、V45 byte-identical、summary 可区分 `verification failure` vs `structure failure`、未宣称 decoder exact rate 提升。

## Phase E — 结果复核

- [ ] **E1** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含 verification 重分类计数与 claim boundary（不提升 decoder exact rate）。
- [ ] **E2** 主线程/ reviewer 独立重算 verification 分流与计数；verdict 入 `REVIEW_VERDICT.md`。
- [ ] **E3** Memory triage 单独里程碑（本轮禁改 `AGENT_PROJECT_MEMORY.md`）；不启动 V47。

## 本变更期间显式禁止

plan ACCEPT 前实现；新增 decoder/矩阵/参数网格/调参；改写/覆盖 V45 输出；以非 canonical 方式生成 tag；把 `exact_l2` 静默转 `verification_accept`；把 `390221` 同残留宣称为同码字；新增泄漏计费；作 FER/阈值/SKR/安全/资格/晋升陈述；rerun/resume/补偿；自接受；自动启动后继（含 V47）；import v45 decoder 执行路径作生产解码。
