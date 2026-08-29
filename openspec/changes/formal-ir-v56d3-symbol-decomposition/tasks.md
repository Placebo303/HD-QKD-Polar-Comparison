# OpenSpec Tasks: formal-ir-v56d3-symbol-decomposition — V56D3 decoder-free 符号映射分解

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 符号映射分解，不运行 L1/L2 decoder**
**HEAD**: `73bb21669c1b76039a6981151d8cc0008dc778d0` (branch `formal-ir-mainline`, V56D1 固化后) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084`
**Predecessor**: `formal-ir-v56d2-calibration` (MIXED_BY_SOURCE + calibration 8 frames + run03 provenance 偏差待修)
**Revision**: V56D3 — 新增 Phase 0 provenance 修复 + Phase A-E 映射分解；方法仍冻结，零 decoder

## Phase 0 — V56D2 run03 provenance 修复（阻塞项，decoder-free）

- [ ] **0.1 记录实际代码状态**：`git diff -- src/qkd_io/ttbin_pipeline.py` + `git status -- src/` + `git rev-parse HEAD` + `git rev-parse origin/formal-ir-mainline` + `rg "8d4df35c" 0 hits` 校验 `HEAD == origin/formal-ir-mainline == implementation SHA`（若有 `src` diff 则记录 diff 行数与 `ponytail: chunk-level histogram` 位置），结果写入 `v56d3_symbol_decomposition.json:provenance.actual_code_state` 与报告 §0
- [ ] **0.2 将优化移出 src**：`src/qkd_io/ttbin_pipeline.py:compute_cross_correlation_histogram` **revert 到冻结基线**（per-pair 旧版或冻结版 chunk 二选一，但必须与 `HEAD 73bb216` 一致）；chunk 单次优化保留为诊断脚本内联函数 `compute_corr_chunk()` / `hist_chunk()`（不在 `src` 留改动），`src` 改动后 `py_compile` PASS
- [ ] **0.3 小样本等价性证明**：用 `≤1k` 事件的合成/截断 `t_A/t_B`（例 `np.random.seed(0) t_A sorted 0..1e9, t_B = t_A + N(0,100ps) + 50ps offset`）分别调旧 per-pair 与新 chunk 实现，断言逐 bin `counts_old == counts_chunk`（`np.array_equal` PASS，`n_bins=16384, bin100, max819200, edges[-1]=max_lag`），落盘 `provenance_equivalence_proof.json` 或 `json:provenance.equivalence`
- [ ] **0.4 标定 run03**：若确认执行期 `src` 确有差异，则 `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration_run03.json` 追加 `provenance_deviation: true` 且 `overall = RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`（加 `provenance_note: "src/qkd_io histogram modified to chunk single but SHA still 8d4df35c, src belongs to frozen baseline; result not authoritative"`），并在报告 §0 声明后继不作权威引用；若已 revert 且证明通过则标 `provenance_restored: true`

## Phase A — 熵/互信息诊断（置换不敏感，decoder-free）

- [ ] **A1 计算 V13 与新三源 H/I**：读 `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*.parquet`（三源 `alice_symbol/bob_symbol`） + `workspace/v13r3fresh_20260816/.../pairs.parquet`（V13 参考，若缺则用 `channel_counts.npz` 的 `delta` 近似对比）+ `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`（仅对比，不训），按 `C(a,b)→P→H(A)/H(B)/H(A,B)/H(A|B)/I` 公式（`log2`）算 bits/symbol（双报 `×1024` bits/block），逐源落盘 `per_source.{H_A,H_B,H_A_given_B,I_AB}`
- [ ] **A2 解读**：报告 `I` 是否仍高（`>5 bits` vs V13 `~9.2`）而 `acc_identity` 坍塌（`27-42%`）；若 `I` 高 ⇒ 可逆重标记/锚点错，若 `I` 低 ⇒ 真域迁移需 entropy 增

## Phase B — Identity vs 经验 MAP（decoder-free, fit/val 分离）

- [ ] **B1 定义 fit/val**：预注册固定 `fit=[7,8,9,10] val=[15,16,17,18]`（2 blocks×4 的前 4 vs 后 4），从 `pairs.parquet: frame_id` 切片；`C_fit(a,b)` 仅 `fit` 4 frames 上计数，`a_MAP(b)=argmax_a C_fit(a,b)`（`1024` 长度数组，`b` 无观测时 `a_MAP(b)=b`）
- [ ] **B2 计算双准确率**：每源算 `acc_identity = mean_{val}(a==b)` 与 `acc_map = mean_{val}(a==a_MAP(b))`（**val 上测，禁同帧**）；另报 `acc_identity_all / acc_map_all`（全 8 帧）仅作参考，不作分流依据
- [ ] **B3 守卫**：脚本中显式 `assert set(fit) ∩ set(val) == ∅` 且 `fit` 上学 `val` 上测，无同帧 leakage；`rg "decode_" 0 hits`

## Phase C — 物理映射族枚举（仅预注册 5 族，不任意 1024 置换）

- [ ] **C1 枚举族**：
  - `global_shift`: `k∈[0,1023] b'=(b+k)%1024`
  - `global_xor`: `k∈[0,1023] b'=b xor k`
  - `axis_32x32`: `≤8` 种（`swap U1↔U2` × `flip U1/U2` 各 `reverse`）
  - `gray_binary`: `b'=gray_to_binary(b)` / `binary_to_gray(b)`
  - `u1u2_order`: `32*U1+U2` vs `32*U2+U1`
  总候选 `<5k`（`1024+1024+8+2+2`），脚本暴力枚举，**不做任意 1024 置换**（`rg "permutation.*1024" 0 hits` 无全搜索）
- [ ] **C2 fit→val 恢复**：每族在 `fit` 上择 `k* = argmax_k mean_{fit}(a==π_k(b))`（或最小 `NLL` via `channel_counts.npz` column-norm `P(A|B)`），在 `val` 上报告 `acc_π/val, NLL/val (bits/sym), q_mass/val, mass_0±1/val`；预注册单一择优规则（`acc` 优先，`NLL` 次之）
- [ ] **C3 恢复阈**：`val` 上 `acc>60%` 且 `NLL 22-28→<5` 且 `q_mass 57-71%→<10%` 才算该族恢复；否则不判 `SYMBOL_MAPPING_CONTRACT_ERROR`

## Phase D — 逐阶段流水核对（找首次坍缩，decoder-free）

- [ ] **D1 定义流水**：`paired timestamps (t_A,t_B) → bin (200ps floor_div) → frame anchor (peak_center vs global min, wrap floor_div, period 204800) → symbol (legacy_v1) → U1/U2 (F03 5+5: U1=sym>>5, U2=sym&31, Gray 可选)`，每阶段两侧一致性校验（例 `frame_anchor` 切 `peak_center` vs `global min` 两种，`bin` 与 `symbol` 分离）
- [ ] **D2 逐段算 I/acc**：若 `pairs` 已含 `t_A/t_B` 或可从 `ttbin_pipeline` 重算，按阶段截断算 `I/acc_identity/acc_map`（复用 Phase A/B 公式），报告 `per_stage {stage, I, acc_identity, acc_map}` 与 `first_collapse_stage`（`I/acc` 首次从 `>5 bits/>60%` 跌至 `<2 bits/<50%` 的阶段）
- [ ] **D3 定位**：若 Stage 1（paired timestamps）已低 ⇒ `pairing` 错；Stage 2 后高 Stage 3 后低 ⇒ `frame_anchor` 错；Stage 4 后高 Stage 5 后低且某 `π` 恢复 ⇒ 符号序错；落盘至 `json:pipeline_stage`

## Phase E — 脚本与报告交付（DIAGNOSIS_PLAN_READY）

- [ ] **E1 编写 `v56d3_symbol_decomposition.py`** (decoder-free, 本变更目录下): `python v56d3_symbol_decomposition.py [--pairs-root ...] [--v13-root ...] [--counts ...] [--out v56d3_symbol_decomposition.json]` → 固定 `fit=[7,8,9,10] val=[15,16,17,18]` 算 `H/I + acc_identity/acc_map + 物理5族 fit→val + 流水分段`，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v56d3_symbol_decomposition.json` + 控制台摘要
- [ ] **E2 编写 `SYMBOL_DECOMPOSITION_REPORT.md`**: 每源 `H/I/acc_identity/acc_map/5族 val恢复/流水坍缩点` + 总体三态分流（`SYMBOL_MAPPING_CONTRACT_ERROR / PAIRING_OR_FRAME_ANCHOR_ERROR / TRUE_ACQUISITION_DOMAIN_SHIFT` 三选一，逐源可 `MIXED_BY_SOURCE`），数据与 json 一致，含修复/排查清单（`SYMBOL_MAPPING` 时修 `mapping/bin_origin/wrap/frame_anchor/Gray` 契约，`PAIRING` 时查 `threshold/policy/direction/frame_start/sync`，`TRUE_SHIFT` 时才规划新 `prior/泄漏`），结论不扩大为 FER/阈值/SKR/晋升，显式 `原 90 已揭盲不可复用` 与 `主算法不否定`
- [ ] **E3 自检**：`py_compile` PASS, `rg "decode_" 0 hits`, `fit∩val==∅` 已验, `I/H` 置换不敏感已报告, `5族 <5k` 已验, `pipeline_stage` 已定位, `provenance` 实际代码状态与等价性证明已落盘, 报告与 json 一致
- [ ] **E4 推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`**，未创建任何 `.../v56d3_*/run_01` decoder 执行，不碰 V55 90 块，不运行 decoder，仅改本目录文件与脚本（+ `src` 的 revert 如需），三态分流后**另起 successor** 动作（`SYMBOL_MAPPING` 则另冻新 TEST 再 qualification，`TRUE_SHIFT` 则另规划 `prior/泄漏`）

## 本诊断显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 offset/mapping-corrected 重译）；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v56d3_*/run_01` decoder 执行；任意 `1024` 置换/`1024!` 搜索/神经网络映射；`bin_width/dimension/pairing` 网格；将映射分解择优值回注为新 pipeline；**重发明 V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing 近似物化**；同帧 `fit/val` 评价；覆盖已有输出。

## 验收

- proposal/design/tasks/specs 一致 HEAD 73bb2166 84d62779 lifecycle DIAGNOSIS_PLAN_READY DECODE_FORBIDDEN 三态分流互斥明确
- `git diff src/` 实际状态与等价性 `counts_old == counts_chunk` 逐 bin 相等证明已落盘，`src` 已 revert 或 run03 已标 `RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`
- 每源 `H/I` 置换不敏感已算，`acc_identity vs acc_map (fit 4→val 4, 禁同帧)` 已算，仅 5 族物理映射 `fit→val` 恢复已验（`acc>60% NLL<5`），流水 `first_collapse_stage` 已定位
- 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA DIAGNOSIS_PLAN_READY 仅改本目录（+ src revert），原 90 未碰 主算法不否定
