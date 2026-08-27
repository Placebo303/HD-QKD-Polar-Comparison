# Delta Specification: formal-ir-v46-verification-semantics

**Cycle**: `V46P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V47。**
**Predecessor**: V45 `formal-ir-v45-l1-app-soft-transfer` (HEAD `f59ab60a`, tag 仅记账)
**Investigation**: `f59ab60a`（`+64 tag` 仅记账 984/1014/1024 路径 `v45:216-222,598,1182-1242`；390221 同残留非同码字；`wrong_codeword=syndrome_ok&&!exact` 陪集语义；pre-tag 时序正确）
**Mechanism id**: `deterministic_64bit_verification_sha256_trunc64`
**HEAD**: `f59ab60a`

## R1. Predecessor binding

V46 SHALL 仅基于 V45 证据（`f59ab60a` 三项只读结论）规划。若 tag 已实际执行则本 spec 不适用，应另立“最小 decoded-difference 诊断 + L2 图/陪集调查”分支（互斥）。V46 SHALL NOT 追溯改写 V45 终端/结论/输出，不启动 V47，实现前需独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、实现 SHA、cycle V46P0、scope `v46_verification_semantics_readonly_once`）。

## R2. Single mechanism — deterministic 64-bit verification

本变更 SHALL 仅实现单一机制：`tag = trunc64(SHA256(canonical_bytes(x_hat)))`（取 SHA-256 前 8 字节，big-endian），`canonical_bytes` 为定长归一化（`n` bytes，`q=32` 5-bit 打包方式冻结其一），确定性、可重放。SHALL NOT 新增 decoder、矩阵、参数网格、联合图、第二哈希对比。Tag SHALL 已计入 `leak_total = 5·m + 64`（`L2+tag = 984/1014/1024`，含 L1 则 `1064/1094/1104`），V46 SHALL NOT 新增或重复计费，summary SHALL 显式声名 `leakage_already_accounted`。

## R3. Minimal workload — read-only re-audit, zero new decoder invocations

Workload SHALL 为对 V45 已有 18 L2 records 的只读复核与 tag 重放校验，零新 decoder invocations。可选至多一次 decoder-free 的 `tag_of` 确定性自检（fake fixtures）。SHALL NOT 重跑 V45 27 invocations，不执行任何生产 decoder、longrun/minrerun/routeA。

## R4. Source, normalization, leakage — frozen

Tag 来源 SHALL 为 `x_hat` canonical bytes（默认 L2-only `x2_hat`，若选 `x1_hat||x2_hat` 则全量冻结其一，不可中途切换）；归一化（大小端、定长、截断位置）SHALL 冻结且测试可断言；泄漏 SHALL 已计（`920/950/960 +64 =984/1014/1024`），与 `SOURCE_L2_TAG_BITS` 一致。缺 `x_hat/hash` 的历史记录（如 390221 仅 `errors_final=3`）SHALL 标记 `verification_not_applicable_missing_hash`，不得宣称为同码字/同 tag。

## R5. Detected vs undetected — wrong_codeword reclassification

`wrong_codeword = syndrome_ok && !exact` SHALL 为 LDPC 错误陪集解。Verification 后 SHALL 重分类：
- `syndrome_ok && !exact && tag_mismatch → detected_failure`（verification failure，主路径）
- `syndrome_ok && !exact && tag_match → undetected_error`（概率约 `2^-64`，单独计数 `undetected_count`）
`wrong_codeword` SHALL 主要转为 `detected_failure`；`undetected_error` 不计 exact，单独报告。

## R6. Oracle truth preserved — exact_l2 remains ground truth

`exact_l2` SHALL 仍为 oracle 判真（vs `u_true/x_true`），verification 的 `accept` SHALL NOT 覆盖或重定义 `exact_l2`。Summary SHALL 同时报告 `exact_l2` 与 `verification_accept`，且不得宣称提升 decoder exact rate。

## R7. Pre-tag timing — preserved

`wrong_codeword_l2 / G3 / exact_l2` SHALL 保持在 verification 之前计算（pre-tag 时序正确，沿用 V45），verification 仅在其后追加 gate。时序后移即 invalid。

## R8. Outputs unchanged — V45 byte-identical

V46 SHALL NOT 修改任何 V45 已有输出；V45 `results/` 与 `comparison_bench/outputs_comparison/` 下既有文件 SHALL 保持 byte-identical（mismatch 即 `V46_EVIDENCE_INVALID`）。V46 证据 SHALL 隔离于新根 `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/`，fail-closed 若已存在。

## R9. Evidence outputs — minimal fixed set

授权写出 SHALL 仅为最小固定集：`v46_records_verify.json/.csv`（18 行复核视图，含 `tag_hat/tag_true/verification_accept/reclassified ∈ {detected,undetected,structure,not_applicable,exact}`）、`v46_summary.json`（含 `detected/undetected/structure` 计数、`wrong_codeword_reclassified_as_detected`、`leakage_already_accounted`、`canonical_bytes` 归一化声名、provenance）、失败时 `v46_invalid_notice.json`；CSV/JSON 行对等；SHALL NOT 写任何 NPZ；输出根在全部守卫通过后创建。

## R10. Terminal distinguishability — verification vs structure

Summary 终态 SHALL 可区分 `verification failure`（tag mismatch 的 detected）与 `structure failure`（`!syndrome_ok && !exact`），以正交 `reason_code ∈ {verification_mismatch, undetected, structure}` 与分层计数呈现。`V45_EVIDENCE_INVALID` 优先；V46 不重定义 V45 五终态，仅追加 verification 维度。

## R11. Integrity, guard ordering, tiers

Runner SHALL 实现三层：
- **Tier 0 拒绝**（默认拒绝、必带 `--execution-authorized --authorized-target-sha`、HEAD 精确等值、SCOPED tracked-dirty、输出根已存在）最先、不创建文件、非零退出、零 calls。
- **Tier 1 预检失败**（只读输入缺失、V45 byte-identical 失败、归一化不一致）建增量根写 invalid 三件套后停止，不 rerun。
- **Tier 2 中途异常**（`BaseException`）在已建根内保留 raw partial + notice + summary 后重抛。
跨条件 outcome 差异永为信号，不作完整性失败；缺 `x_hat` 不作 invalid，仅 `not_applicable`。

## R12. Claim boundary

结果仅支持“V45 记账 tag 转为确定性 verification 后的重分类”有界陈述。SHALL NOT 宣称 decoder exact rate 提升、FER/阈值/SKR/安全/正式资格/晋升、真帧行为、把同 `errors_final` 等同同码字。无论结果如何禁止：新增 decoder/调参、重复计泄漏、把 `exact_l2` 静默转 `verification_accept`、自动启动 V47。

## R13. Lifecycle

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。SHALL NOT 启动 V47。
