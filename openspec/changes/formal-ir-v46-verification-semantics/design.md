# OpenSpec Design: formal-ir-v46-verification-semantics

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V47。**
**Cycle**: `V46P0`
**Predecessor**: V45 `formal-ir-v45-l1-app-soft-transfer` (HEAD `f59ab60a`)
**Investigation anchor**: `f59ab60a` 三项只读结论（tag 仅记账 / 390221 同残留非同码字 / wrong_codeword 陪集语义 + pre-tag 时序正确）
**HEAD**: `f59ab60a`（实现冻结时 `git rev-parse` 精确重绑）

## 1. 科学问题（单一）

> V45 的 `+64 tag` 仅记账（`SOURCE_L2_TAG_BITS` → `984/1014/1024`，路径 `v45:216-222,598,1182-1242`，未生成/传输/接受），V46 是否以**最小、确定性、可重放**的 64-bit verification 把 `wrong_codeword = syndrome_ok && !exact` 从静默陪集错误转为 **detected failure**，且不改 `exact_l2` oracle 判真、不宣称 decoder exact rate 提升？

分支冻结：当前属“tag 仅记账”分支 → 规划真实 deterministic 64-bit verification；若 tag 已实际执行则应改规划“保存最小 decoded-difference 诊断 + L2 图/陪集歧义调查”，本轮不走（互斥）。

## 2. 冻结语义

### 2.1 Tag 来源与归一化（确定性）

- **Input**: `x_hat`（L2 解码输出码字比特/符号的 canonical bytes；若 L1+L2 联合验收则为 `x1_hat||x2_hat`，本设计默认 L2-only `x2_hat`，与 `leak_total = 5·m2+64` 的 L2 tag 计费一致；实现时二选一冻结，不可中途切换）。
- **Hash**: `tag = trunc64(SHA256(canonical_bytes(x_hat)))` — 取前 8 字节（big-endian），`canonical_bytes` 为定长、小端/大端冻结其一（推荐 big-endian 定长 `n` bytes，`q=32 → 5 bits/symbol` 打包方式冻结），hex/bytes 表示唯一。
- **Determinism**: 同一 `x_hat` 必得同一 tag；实现提供 `tag_of(x_hat) ↔ tag_of(x_hat_oracle_recomputed)` 双向重算一致性自检。
- **Leakage**: 已计入 `leak_total`（`L2+tag = 920/950/960 +64 = 984/1014/1024`，Treatment 若含 L1 则 `1064/1094/1104`），V46 不新增、不重复计费，summary 显式标注“leakage already accounted”。

### 2.2 时序（pre-tag 正确性保留）

```
decode(H, prior, syndrome) → syndrome_ok / exact_l2 (oracle vs u_true) / wrong_codeword_l2 (=syndrome_ok && !exact) / G3
        ↓  (pre-tag, V45 已正确)
verification: tag_hat = trunc64(SHA256(x_hat)), tag_true = trunc64(SHA256(x_true)); accept = (tag_hat == tag_true)
        ↓
reclassified: wrong_codeword && tag_mismatch → detected_failure
              wrong_codeword && tag_match    → undetected_error (≈2^-64)
              !wrong_codeword                → 保持原 exact/syndrome 语义
```

`wrong_codeword_l2 / G3 / exact_l2` 均在 tag 检查之前计算，不得后移；verification 仅追加 acceptance gate。

### 2.3 390221 证据边界

现有证据仅 `errors_final=3` 相同，不能确认同一码字（未保存 `x_hat/hash`，路径缺口）。V46 不追溯宣称 390221 为同码字；verification 落地后，未保存 `x_hat` 的历史记录仍标记 `verification_not_applicable_missing_hash`，不补造。

### 2.4 Detected vs Undetected vs Structure

- **Detected failure** (`verification failure`): `syndrome_ok && !exact && tag_mismatch` — LDPC 陪集错误被 tag 捕获，计为 detected，不计 exact。
- **Undetected error**: `syndrome_ok && !exact && tag_match` — 概率约 `2^-64`，仍 `!exact`，不计 exact，单独计数 `undetected_count`。
- **Structure failure**: `!syndrome_ok && !exact` — 结构/译码未收敛，与 verification 正交。
- `exact_l2` 仍为 oracle 判真（ground truth），verification 不覆盖 exact；summary 同时报告 `exact_l2` 与 `verification_accept`。

## 3. Workload（最小）

- **主路径**: 对 V45 `v45_records.json/.csv`（18 L2 records）的只读复核：校验 `wrong_codeword` 定义、重算 `tag_hat/tag_true`（需 `x_hat` 存在时）、重分类 `detected/undetected/structure`，零新 decoder invocations。
- **自检**（可选，decoder-free）: 用固定 fixtures 校验 `tag_of` 确定性、截断、归一化、跨端一致性；不跑生产 decoder。
- **不做**: 新 decoder 调用、重跑 V45 27 invocations、任何 longrun/minrerun/routeA。

## 4. 终态机（可区分 verification vs structure）

在 V45 五终态基础上，V46 summary 增量 `verification_summary`，正交区分：

- `verification_failure_count`（detected）vs `structure_failure_count`（pre-tag `!syndrome_ok`）
- `undetected_error_count`（`≈2^-64`）
- `wrong_codeword_reclassified_as_detected` 计数（V46 机制有效性度量）

V45 终态本身不重定义；V46 仅在其后追加 verification 维度的可区分原因码（`reason_code ∈ {verification_mismatch, undetected, structure}`）。

## 5. 证据与隔离

- **只读输入**: V45 `run_01/v45_records.json/.csv`、`v45_summary.json`（byte-identical，不修改）。
- **增量根**（仅执行获批后建）: `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/` — fail-closed 若已存在。
- **最小文件集**: `v46_records_verify.json/.csv`（18 行复核视图，含 `tag_hat/tag_true/verification_accept/reclassified`）、`v46_summary.json`（含 detected/undetected/structure 计数与 `leakage_already_accounted` 声名）、失败时 `v46_invalid_notice.json`；不写 NPZ。
- **V45 输出保持 byte-identical**（mismatch 即 invalid）。

## 6. 实现草图（后继轮次，当前不授权）

- 新模块 `comparison_bench/src/comparison_bench/formal_ir/v46_verification_semantics.py`: 纯函数 `canonical_bytes(x_hat)`, `tag_of(x_hat)`, `verify(x_hat, x_true)`, `reclassify(record, tag_hat, tag_true)`；不 import decoder，不新增 decoder 参数。
- 可选 CLI `scripts/verify_v46_tags.py`: decoder-free 重放，默认拒绝，需 `--execution-authorized --authorized-target-sha <sha>`，SCOPED dirty 检查，零 decoder calls。
- 测试仅 fake fixtures：确定性、归一化、截断、detected/undetected 分流、leakage 已计声名。

## 7. 自由裁量 D1-D6

- **D1 单机制**: 仅 deterministic 64-bit SHA256-trunc64 verification，不做多哈希/多长度对比。
- **D2 最小 workload**: 只读复核 18 records，零新 decoder invocations。
- **D3 不改 V45**: 输出隔离，V45 byte-identical。
- **D4 泄漏已计**: `984/1014/1024` 含 64，不重复计费。
- **D5 exact 仍 oracle**: verification 不替代 exact_l2。
- **D6 终态可区分**: verification failure vs structure failure 正交原因码。

## 8. 与 V45 的衔接与禁止

- 保留 V45 `wrong_codeword/G3/exact_l2` pre-tag 时序与定义（§2.2）。
- 禁止：新增 decoder/矩阵/调参、把 tag 未覆盖历史宣称为同码字、把 `exact_l2` 静默转 `verification_accept`、作 FER/SKR/资格陈述、自接受、自动启动 V47。
