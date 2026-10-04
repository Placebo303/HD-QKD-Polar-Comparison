# OpenSpec Proposal: formal-ir-v56d3-symbol-decomposition

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 符号映射分解，不运行 L1/L2 decoder，不改方法，不重跑原 90 块。**
**Domain**: Formal IR / V56D3 decoder-free 符号映射分解（V56D2 唯一后继）
**Change ID**: `formal-ir-v56d3-symbol-decomposition`
**Cycle ID**: `V56D3` (symbol mapping decomposition), predecessor `V56D2` `formal-ir-v56d2-calibration`
**Predecessor**: `formal-ir-v56d2-calibration` (HEAD `73bb21669c1b76039a6981151d8cc0008dc778d0`, branch `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点；结论 `MIXED_BY_SOURCE` 基础上 calibration `8 frames` 物化但 `run03` 存在 provenance 偏差)
**Branch**: `formal-ir-mainline`
**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` (V56D1 固化后) — **实际代码状态待 `git diff` 重测，`src/qkd_io` 属冻结基线**
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点不改)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅 decoder-free 统计与映射分解，不产生 `run_01` decoder 执行，不改 `H1/Lane C/Δ8/decoder 90/1.0`
**Method frozen**: `V54二阶段 H1-16(80b) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag` 完全冻结

> ponytail lite: 本变更仅 6 文件 (`proposal/design/tasks/specs/spec.md` + `v56d3_symbol_decomposition.py` decoder-free + `SYMBOL_DECOMPOSITION_REPORT.md`) + 1 个 provenance 等价性小样本证明；无 runner、无 decoder、无新矩阵，最短科学路径。laziest alternative: `numpy` 直算熵/MAP 已覆盖，无需新依赖。

## Goal

在 V56D2 calibration 之后，以最短科学路径启动 **V56D3 decoder-free 符号映射分解**，并先行修复 **V56D2 run03 的 provenance 偏差**，将三选一分流做成可判定落盘：

### 0. 先修 V56D2 run03 provenance（阻塞项）

- **问题**：执行中修改了 `src/qkd_io/ttbin_pipeline.py:compute_cross_correlation_histogram` 为 chunk 单次直方图（`# ponytail: chunk-level histogram — one histogram per chunk instead of per pair`），但记录 SHA 仍 `8d4df35c`（`HEAD 73bb216`），`src/` 属冻结基线不得在执行期留改动。
- **修复**：将该优化**移至诊断脚本内实现**（不在 `src` 留改动），用**小样本证明旧实现（逐 bin per-pair）与 chunk 实现逐 bin 完全相等**，记录**实际代码状态**（`git diff src/` + `HEAD == origin/formal-ir-mainline == implementation SHA` 重核）；若工作树在 run03 执行时确有差异，则该次输出标为 **`RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION` 而非权威结果**，需 `revert` 或将优化以诊断脚本内联方式重提交为新 SHA，再重跑诊断。
- **判定**：`src` 已 revert 且等价性证明通过，或差异已显式标注为 `PROVENANCE_DEVIATION`，方可进入 V56D3 主诊断。

### 1. V56D3 主诊断 — 区分三类失效（decoder-free，最小诊断）

区分 **可逆重标记 / pairing/frame anchor 错 / 不同统计域**：

1. **置换不敏感的互信息诊断**：计算 **V13** 与新三源的 `H(A)/H(B)/H(A|B)/I(A;B)`（基于 `pairs.parquet` 的 `alice_symbol/bob_symbol` 联合计数，`H` 与 `I` 对符号置换不敏感）。若互信息仍高而 `A==B` 坍塌，则指向映射/锚点错而非信道真退化。
2. **Identity vs 经验 MAP 诊断**：比较 `identity accuracy = mean(a==b)` 与**每 B 的经验 MAP** `a_MAP(b)=argmax_a C(a,b)` 的准确率（`C` 为 `1024×1024` 联合计数）。`I` 高 + MAP 高 + identity 低 ⇒ 可逆重标记；`I` 高 + MAP 亦低 ⇒ 非逐符号可逆（pairing/anchor/结构性）或需更大结构映射。
3. **Calibration 拟合/验证分离**：对 calibration `8 frames [7,8,9,10,15,16,17,18]` 做 **fit 4 / validation 4** 划分（例 `fit=[7,8,9,10] val=[15,16,17,18]` 或交替划分，预注册一种），**禁止同帧评价**（fit 上学映射，val 上测 `A==B/NLL/q_mass`）。
4. **仅检查有物理依据的映射族（预注册，不任意 1024 置换）**：
   - 全局 cyclic shift `b'=(b+k) mod 1024`（`k∈[0,1023]`，来自 bin origin / delay 整数 bin 错）
   - 全局 XOR `b'=b xor k`（`k∈[0,1023]`，Gray/binary 位序错位近似）
   - `32×32` 两轴交换/翻转（`a = 32*u1+u2` vs `32*u2+u1`，`u1/u2` 各轴 `reverse / swap`，对应 `F03 5+5` split 与硬件通道交错）
   - Gray ↔ binary 次序（`binary→Gray` 与 `Gray→binary`，各 `10 bit` 内）
   - `32*U1+U2` vs `32*U2+U1` 家族（`Lane C` 序错）
   > 不做任意 `1024!` 置换搜索；每族至多 `1024` 候选，总候选 `<5k`，可暴力枚举。
5. **逐阶段流水核对**（找 `A==B` 首次坍缩）：
   `paired timestamps → bin (200ps) → frame anchor (peak_center vs global min, floor_div) → Alice/Bob symbol (legacy_v1) → U1/U2 (F03 5+5)`，每阶段两侧一致性校验（例 `paired timestamps` 层 `I` 是否已高，`bin` 层后是否仍高，`frame anchor` 切换是否恢复等），定位首次坍缩点。

### 2. 分流判定（预注册三态互斥）

- **互信息仍高 + validation 某预注册映射恢复 `A==B/NLL`** → **`SYMBOL_MAPPING_CONTRACT_ERROR`**（可逆重标记，需修复 `mapping/bin_origin/wrap_rule/frame_anchor` 契约，另冻新 TEST 再 qualification；原 V55 90 永不重跑）
- **raw timing 强（`σ~127ps p2bg 378-708` 部分健康）且互信息高但所有物理映射失败** → **`PAIRING_OR_FRAME_ANCHOR_ERROR`**（非逐符号可逆，需查 `pairing threshold/policy/direction` 与 `frame_start/sync`/`occupancy_filter`）
- **互信息本身显著降低（`I(A;B)` 接近 0 或 `H(A|B)≈H(A)`）** → **`TRUE_ACQUISITION_DOMAIN_SHIFT`**（真域迁移，届时才规划新 `prior/泄漏`；`prior` 仍 `TRAIN-only channel_counts.npz`，不读新 TEST 做训练）

> **硬约束**：原 V55 90 永不重跑（已揭盲 `0/90`）；主算法（`H1/Lane C/Δ8/decoder 90/1.0/poly37/L2-only tag`）**不否定**，`V55 0/90` 不记为算法证伪证据。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder；不改 `H1-16 / Lane C / H_inc1/2 Δ8+8 / m2 184/190/192 / leak / tag / prior / decoder 90/1.0 poly37` 任一冻结量；不试新 `Δm/degree/seed`
- 不在原 V55 authoritative 90-block 上重跑任何 corrected pipeline / offset-corrected 重译（已揭盲 `0/90`，`base→Δ8→Δ16` 任一变体均禁）；不将映射分解择优值回注为新 pipeline
- 不做任意 `1024` 置换或 `1024!` 搜索、不训练神经网络映射、不做 `bin_width/dimension/pairing` 网格搜索（`200ps legacy_v1 nearest 1024` 单点锚点；`I/H` 度量本身对 `bin_width` 不敏感，仅报告已有 200ps 下值）
- 不宣称 LDPC 证伪 / FER / 阈值 / SKR / 晋升；本诊断仅为 `DIAGNOSIS_PLAN_READY` 的映射分解，不直接进入 qualification
- 不创建正式 `.../v56d3_*/run_01` decoder 执行；映射修复后**另冻全新 TEST blocks**再 qualification，需另起 OpenSpec 与独立授权
- 不改写/覆盖 `V38–V56D2` 任何已有输出与终态（只读）；不直接修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`

## Scope

1. **冻结方法零改**：`n=1024, m2 184/190/192, GF32 poly37, H1-16 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz), Lane C ordinal-2, H_inc1/2 Δ8+8, decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior` 全只读，**零 decoder**
2. **Provenance 修复（Phase 0）**：
   - `git diff src/qkd_io/ttbin_pipeline.py` 显式记录实际代码状态与 `HEAD/origin/implementation SHA` 三方一致校验；`src` 已 `revert` 到冻结基线或差异已标注
   - 小样本等价性证明：取 `≤1k` 事件的合成/截断真实 `t_A/t_B`，分别用旧 per-pair 与 chunk 实现算 `counts`，断言逐 bin `counts_old == counts_chunk`（`np.array_equal`），`py_compile` PASS
   - 若差异存在，`v56d2_calibration_run03.json` 追加 `provenance_deviation: true` 且 `overall = RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`，不作权威结果引用
3. **熵/互信息诊断（Phase A）**：读 `v55_intake_20260828/pairs/*.parquet` + `workspace/v13r3fresh_20260816/...` + `channel_counts.npz` 的 `C(a,b)`，算每源 `H(A),H(B),H(A|B),I(A;B)`（bits/symbol，与 `V13 0.80-0.83` 对比），`py` 直算无新依赖
4. **Identity vs MAP（Phase B）**：每源 `acc_identity = mean(a==b)`，`acc_map = mean(a == a_MAP(b))` 其中 `a_MAP(b)=argmax_a C_fit(a,b)`（`fit 4 frames` 上学，`validation 4 frames` 上测；另报全量 `fit+val` 仅作参考，**不以同帧 MAP 判恢复**）
5. **物理映射族枚举（Phase C）**：仅上述 5 族（`global shift / XOR / 32×32 swap/flip / Gray-binary / 32U1+U2 vs 32U2+U1`），每族在 `fit` 上择 `k*`（最大 `val` 上 `acc`/最小 `NLL`），在 `val` 上报告恢复度；**不任意 1024 置换**
6. **逐阶段流水核对（Phase D）**：若 `pairs` 已含 `t_A/t_B` 或可从 `ttbin_pipeline` 重算，按 `paired timestamps → bin → frame anchor → symbol → U1/U2` 逐段算 `I`/`acc`，报告首次坍缩阶段
7. **分流与落盘（Phase E）**：输出 `v56d3_symbol_decomposition.json`（`per_source {H/I/acc_identity/acc_map/mapping_candidates/val_recovery} + pipeline_stage`）+ `SYMBOL_DECOMPOSITION_REPORT.md`（三态判定与修复/排查清单），`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`

## Impact Scope

- **新增/修订（本诊断）**：`openspec/changes/formal-ir-v56d3-symbol-decomposition/` 下 6 文件：`proposal.md/design.md/tasks.md/specs/spec.md` + `v56d3_symbol_decomposition.py` (decoder-free) + `SYMBOL_DECOMPOSITION_REPORT.md`；`specs/spec.md` 为增量（本诊断仍 decoder-free，不改方法 spec 主体）
- **修正（provenance）**：`src/qkd_io/ttbin_pipeline.py` **revert 到冻结基线**（移除执行期 chunk 优化），优化以诊断脚本内联函数保留；或显式标注 `run03` 为 `RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`
- **只读依赖**：`src/qkd_io/ttbin_pipeline.read_ttbin_events/compute_cross_correlation_histogram`（冻结基线版，验证用）+ `v55_authoritative_registry.json` + `v55_intake_20260828/pairs/*.parquet + intake_report.json` + `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json + build_manifest.json` + `nbldpc_v25_20260818/run_04/channel_counts.npz` + `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh...`
- **不修改**：任何既有 `spec/代码/测试/输出`（除 `src` 的 revert 外）、`V38–V56D2` 输出、`outputs_comparison/workspace` 以外；不创建正式 TEST `run_01`；**零 decoder、零码参数**

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，lifecycle `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，HEAD `73bb2166` + branch `formal-ir-mainline` + data SHA `84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 H1/Lane C/Δ8/decoder、原 90 永不重跑、主算法不否定
- [ ] **Provenance 修复**可复现：`git diff src/` 已记录实际状态，`HEAD == origin/formal-ir-mainline == implementation SHA` 已校验；`src/qkd_io` 已 revert 到冻结基线（或差异已标注为 `RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`）；小样本 `counts_old == counts_chunk` 逐 bin 相等证明已落盘（`≤1k` 事件合成/截断样本，`np.array_equal` PASS）
- [ ] **Run03 定性**可复现：若执行期确有 `src` 改动，则 `v56d2_calibration_run03.json` 已追加 `provenance_deviation` 并重标 `RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION` 而非权威结果，不作后继引用依据
- [ ] **熵/互信息**可复现：每源 `H(A)/H(B)/H(A|B)/I(A;B)` 已基于 `pairs.parquet` + `channel_counts.npz` 算得（置换不敏感），与 V13 `H~0.80-0.83` 对比已报告
- [ ] **Identity vs MAP**可复现：每源 `acc_identity` 与 `acc_map = mean(a==a_MAP(b))` 已算得，`a_MAP` 在 `fit 4` 上学、`val 4` 上测，**禁同帧评价**已守卫
- [ ] **物理映射族**可复现：仅上述 5 族预注册映射已枚举（`global shift 1024 + XOR 1024 + 32×32 swap/flip + Gray/binary + 32U1+U2 vs 32U2+U1`），总候选 `<5k`，每族 `fit→val` 恢复度（`A==B/NLL/q_mass`）已报告，**无任意 1024 置换**
- [ ] **逐阶段流水**可复现：`paired timestamps → bin → frame anchor → symbol → U1/U2` 逐段 `I/acc` 已核对，首次坍缩阶段已定位
- [ ] **三态分流**可复现：`SYMBOL_MAPPING_CONTRACT_ERROR / PAIRING_OR_FRAME_ANCHOR_ERROR / TRUE_ACQUISITION_DOMAIN_SHIFT` 三选一已按 `I` + `val` 恢复判定落盘，且报告含对应修复/排查清单（新 prior/泄漏仅在 `TRUE_DOMAIN_SHIFT` 时才规划）
- [ ] `v56d3_symbol_decomposition.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`），仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v56d3_symbol_decomposition.json` + 控制台摘要；不创建 `run_01`
- [ ] `SYMBOL_DECOMPOSITION_REPORT.md` 已记录每源熵/MAP/映射族/val 恢复/流水坍缩点与总体分流，数据与 json 一致，结论不扩大为 FER/阈值/SKR/晋升，明确原 90 已揭盲不可复用、主算法不否定
- [ ] 已推送新 SHA 并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56d3_*/run_01` decoder 执行，不碰 V55 90 块

## Tasks

见 `tasks.md`（Phase 0 provenance 修复与等价性证明；Phase A 熵/互信息；Phase B Identity vs MAP；Phase C 物理映射族枚举；Phase D 逐阶段流水；Phase E 脚本与报告交付）

## Lifecycle

V56D2 当前 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（HEAD `73bb2166`, calibration `8 frames` 物化但 `run03` 有 provenance 偏差）；V56D3 本诊断 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅 decoder-free 映射分解，不实现 runner，不执行 decoder，不创建 run_01）；诊断后若 `SYMBOL_MAPPING_CONTRACT_ERROR` 则**另起 successor** 修复契约并冻全新 TEST blocks 再走 `QUALIFICATION_PLAN_READY`，若 `TRUE_DOMAIN_SHIFT` 则另规划新 `prior/泄漏`，本诊断不直接进入 qualification。
