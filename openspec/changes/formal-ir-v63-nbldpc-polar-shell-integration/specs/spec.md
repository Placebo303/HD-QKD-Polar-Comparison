# OpenSpec Spec: formal-ir-v63-nbldpc-polar-shell-integration

**Lifecycle**: `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件，未适配前禁止实现/运行 decoder，不改 Polar src
**Change**: `formal-ir-v63-nbldpc-polar-shell-integration` (`V63P0`, branch `formal-ir-mainline`, HEAD `fad33f4b935e73972b5be4d02ec7901214fa0046`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (`cb60c5dd48...`, V54 二阶段 `Δ8+Δ8` 性能候选) + `formal-ir-v62` 仅 proxy 参考

## 1. 变更类型与生命周期

- **Type**: `SHELL_INTEGRATION` — Polar pipeline 外壳保留 + NB-LDPC IR 模块替换的壳集成（smoke 9 + development 90, 预算 18-36 / 180-360 硬帽），非 formal qualification/promotion/安全证明。
- **Lifecycle**: `PLAN_CANDIDATE / SHELL_INTEGRATION / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件，未适配前禁止任何 decoder 实现/执行与正式 `run_01` 创建。
- **Branch**: `formal-ir-mainline`；`HEAD` `fad33f4b935e73972b5be4d02ec7901214fa0046` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞；本次推送新 Plan SHA 后停止。
- **Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200 pairing=nearest rule=legacy_v1`) — 同域单点；新 session 需 domain_check + calibration + m1/m2 重算后才可运行。

## 2. 冻结方法（NB-LDPC 完全冻结，外壳保留/IR 替换）

### 2.1 NB-LDPC 不变量（V54 完全冻结）

- `n =1024 symbols/block` (`4×256 frames`), `q =1024 (GF32 symbols 0..1023)`, `log2 q =5`, `GF32 poly=37 (0b100101)`, `tag =64 bits/block L2-only 仅 total 计一次`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`L1-APP`: `p_i(u1)=P(U1|B_i) → BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs → q_i=softmax(BP_i) → P_i(U2)=Σ q_i P(U2|B,u1)` (TRAIN prior `channel_counts.npz` via `load_v25_channel_counts()` 只读，不重估)。
- `Lane C` ordinal-2 `s38310x`：`m2 =184 (1M) /190 (1p5M) /192 (2M)`，`support/标签/置换/MET图` 全冻。
- `H_inc1 8×1024 det1` + `H_joint1 192/198/200×1024` nested；`H_inc2 8×1024 det2` + `H_total 200/206/208×1024` nested；`rank_joint1==m2+8`, `rank_total==m2+16`, `independence_1==8`, `independence_2==8`, `row≤16`, `col_inc≤1`, `E≈96`。
- `decoder`: `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop`；`verification`: `tag_scope=l2_only compute_tag_64(empty_uint8,x2) trunc64` + `syndrome_ok && tag_ok` 双条件；`rescue 触发 = verification-only`。
- `leak`: `leak_base=5*m2+5*16+64 →1064/1094/1104`, `leak_stage1=leak_base+40 →1104/1134/1144`, `leak_stage2=leak_base+80 →1144/1174/1184` (`tag` 已含，不重复扣除)。
- `prior = TRAIN-only`，evaluation blocks 来自冻结 held-out (非 TRAIN)。

### 2.2 外壳保留清单（只读，不改 src/experiments/tools）

- `TTBin读取、通道选择、delay/pairing、symbol materialization(1024 symbols)、session/source/frame provenance、参数估计分层、verification/丢帧、PA、认证开销报告、Polar PIE/SKR 参数参考` — 均只读复用 Polar pipeline 壳（`src/` + `experiments/run_e2e_pipeline.py` 的非 IR 段 + `comparison_bench/io`）。
- `beta_eff_empirical` 必须由 `compute_beta_eff_empirical` 派生，永不手填。
- `finite-key/PIE/SKR` 仅 `POLAR_REFERENCE_PROXY`，不升级。

### 2.3 IR 替换接口（core replacement）

- **Input**: `FrameBatch(dataset_id, alice_symbols: np.ndarray[1024,1024), bob_symbols: np.ndarray[1024,1024), dimension=1024, frame_len_symbols=1024, metadata={source, block_id, frame_ids[4], held_out_ordinal_start/end, pairs_count, sampling_mode, session_id, provenance})` via `load_pairs_table→normalize_pair_columns→build_frame_batch`.
- **Output**: 统一 `IRRunResult` 扩展（per frame + aggregate）：
  ```
  reconciled_symbols: np.ndarray (x2_hat, 1024) per frame  # IR 输出
  accepted: bool per frame (=syndrome_ok && tag_ok)
  rejected: bool per frame (=!accepted)
  exact: bool per frame (=exact_full = exact_u1 && exact_l2 oracle)
  syndrome_ok: bool per frame
  tag_ok: bool per frame (L2-only trunc64)
  undetected: bool per frame (=syndrome_ok && tag_ok && !exact)  # 单独表，永不并入 accepted
  actual_disclosure_bits: int per frame (=leak_base 1064/1094/1104 or leak_stage1 1104/1134/1144 or leak_stage2 1144/1174/1184 by stage_used)
  decoder_calls: int per frame (2-4 breakdown: L1 1 + base 1 + stage1 ≤1 + stage2 ≤1)
  runtime_s: float per frame + aggregate
  stage_used: enum {base, delta8, delta16} per frame  # base=0, delta8=stage1, delta16=stage2
  ```
- **PA 输入**：`PA.leak = actual_disclosure_bits per frame`（含 tag 64b，已计），`PA.input = reconciled_symbols` 仅对 `accepted` 帧；`undetected` 帧虽 `accepted` 但 `!exact`，计入 `undetected` 单独表。
- **禁止**：复用 `Polar leak_EC_actual_bits` 作 NB-LDPC PA 输入；`tag 64` 重复扣除；`accepted == exact` 假定（两者分别计数）。

### 2.4 禁止

- 禁改任一冻结量、新增矩阵/标签/`prior`/阈值/`decoder`、试 `Δm=4/12/16` 多档、引入第二候选择优、用 outcomes 选行、调 `row_degree` 上限；违者 `EVIDENCE_INVALID`。
- 禁改 `src/experiments/tools` 任何文件（只读复用外壳）；禁重跑 Polar IR；禁把 `POLAR_REFERENCE_PROXY` 升级为 composable。
- 禁重估先验（新 session 未通过 `domain_check + calibration + m1/m2 重算` 前禁运行）；禁跨域假同域。
- 未创建正式 `run_01` 前禁 `decode_*` 新增在 plan 侧。

## 3. Phase A — 壳/IR 接口与适配设计

### 3.1 适配入口（预冻结，不在本轮实现）

- `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`:
  - `class NbLdcShellIRAdapter(IRMethod):`
    - `__init__(self, source: str, counts: np.ndarray, field: GF2mField, H_base, H_joint1, H_total)`
    - `run(self, batch: FrameBatch) -> IRRunResult` (per block `base→stage1→stage2` 条件递进，`verification-only`，返回上述扩展字段)
  - 内部组合 `v54_two_stage_incremental_l2_rescue` 的 `construct_h_* / leak_for / compute_l2_tag / CallAccounting / BLOCK_WINDOWS` + `v38_architecture_triage.construct_lane_c_prototype` + `v35_algorithm_development.compute_tag_64`。
- `comparison_bench/src/comparison_bench/pipeline/shell_integration.py`:
  - `def run_shell_pipeline(ttbin_root: Path, source: str, block_ids: list[int], counts: np.ndarray) -> ShellResult`
  - 串联 `TTBin→load_pairs_table→normalize→build_frame_batch→NbLdcShellIRAdapter→verification→leakage stats→PA(actual_disclosure_bits)→report`。

### 3.2 校核清单（decoder-free 公式校验）

- `leak=5*m_total+64` 双校验 `m_total 184/190/192 +8/+16` 且 `stage1-base=40, stage2-stage1=40`。
- `PA 输入 = actual_disclosure_bits` 非 `Polar leak_EC`。
- `IRRunResult` 扩展字段完整性（`reconciled_symbols/accepted/exact/undetected/actual_disclosure_bits/decoder_calls/runtime/stage_used` 齐全）。

## 4. Phase B — 同域 smoke 冻结（3/source=9 blocks，硬帽36）

### 4.1 处理点单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, channels A1/B5, frame_len 1024, pairs 1024, BLOCK_LENGTH 1024` — 单点。

### 4.2 规模与注册表

- `S=3, B=3, total 9`, 每块 `1024 symbols`；若 held-out 超集 `K>9` 则 `index_j=floor(j*(K-1)/2) j=0..2` 分散选 `3/source`，否则取已验 43 中的 9。
- `v63_smoke_registry.json` (authoritative): `block_id, source(1M/1p5M/2M), frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63_smoke`。
- `git diff -- src/ ==0` 已验，registry `禁换块`。

### 4.3 贯通验证

- `TTBin→PA` 全链路、`leak_actual 按 stage_used 三档计`、`stage_used 分布 base/delta8/delta16`、`decoder_calls 18-36 (per block 2-4)`、`runtime/throughput 可复现`、`proxy yield 可算`。
- `K_available<9` 或校验失败 → `SHELL_DOMAIN_NOT_ALIGNED` 停止。

### 4.4 预算

- `L1 9 + base9 + stage1≤9 + stage2≤9 =18-36 硬帽36 (L2 9-27)`，`per block 2-4 calls`。

## 5. Phase C — 同域正式 development 设计（30/source=90 blocks，硬帽360，门禁 frozen）

### 5.1 规模

- `S=3, B=30, total 90`, 每块 `1024 symbols (4×256 frames)`；枚举剩余非重叠四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916`），过滤与已用 `V48/V50/V51/V52/V53/V54`（含 smoke 9）重叠者得 `K2`，按 `ordinal` 排序后以 `index_j=floor(j*(K2-1)/29) j=0..29` 分散选 `30/源`。
- `v63_dev_registry.json` (authoritative): 同 smoke schema，`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63`，`K2≥90` 才合法，否则 `SHELL_DOMAIN_NOT_ALIGNED`。

### 5.2 三阶段协议（硬帽360, verification-only）

```
per block (90 blocks, 30/source):
  prior = TRAIN prior (shared)
  shell: TTBin→FrameBatch (1024) → L1-APP (H1 s1 → BP → q → P(U2)) // 90 次总计，per block 1 (L1)
         base: H_base(m2) → verify_base ; if pass leak_base else H_joint1(m2+8) → verify_stage1 ; if pass leak_stage1 else H_total(m2+16) → verify_stage2 leak_stage2
  PA: leak = actual_disclosure_bits per frame by stage_used
budget: L1 90 + base90 + stage1≤90 + stage2≤90 =180-360 硬帽360 (L2 90-270)
comp: exact_full=exact_u1&&exact_l2, verify=syndrome_ok&&tag_ok, tag=L2-only 64b
```

- `rank_total==m2+16 nested/independence==8 row≤16` 已验；`leak_base/stage1/stage2` 三档已验。
- 仅 `适配 PASS + 独立 plan ACCEPT + EXECUTE_AUTH` 后才允许创建正式实现并执行。

### 5.3 主指标与门禁（first-match）

```
if not shell_adapter_aligned or not alignment_metadata_complete or rank/nested/verification/记账/域检查失败:
    overall = V63_EVIDENCE_INVALID  # 优先
elif not domain_possible (K2<90 or per_source<30 or not replayable or new_session_without_calibration):
    overall = V63_SHELL_DOMAIN_NOT_ALIGNED  # 停止，不进 decoder
elif nbldpc_not_yet_executed (本轮):
    overall = V63_PLAN_CANDIDATE__SHELL_INTEGRATION_DONE
# 未来执行后（主门禁为 accepted/exact）:
# elif final_accepted >=70/90 ∧ per_source >=20/30 ∧ final_exact >=70/90 ∧ per_source exact >=20/30 ∧ undetected==0 ∧ rank/nested/记账通过 → V63_SHELL_DEVELOPMENT_PASS
# elif has_signal (any exact>0 or rescued>0) but not PASS → V63_SHELL_CORRECTION_WORKS_BUT_NOT_PASS
# else → V63_SHELL_NO_RETAINED_SIGNAL
```

- `PASS` 需 `overall final accepted≥70/90` 且 `per-source ≥20/30` 且 `overall final exact≥70/90 且 per-source exact ≥20/30` 且 `undetected==0` 且 `rank/nested/verification/记账/域检查` 通过；`accepted` 与 `exact` 分别达标（禁相等假定）。
- `CORRECTION_WORKS_BUT_NOT_PASS`: `exact>0` 或 `rescued>0` 但未达 `PASS`。
- `NO_RETAINED_SIGNAL`: `exact==0` 且 `rescued==0` 且无改善信号。
- `EVIDENCE_INVALID` 优先于 `SHELL_DOMAIN_NOT_ALIGNED`。

### 5.4 次级（仅排序，POLAR_REFERENCE_PROXY）

- `PIE proxy = beta_eff_empirical * H_shannon` 与 `SKR proxy = accepted_fraction * (PIE - leak_per_block/1024)` 用 Polar 同一 `shadow` 参数，仅排序，不作门禁。
- 显式 `POLAR_REFERENCE_PROXY`，不升级；泄漏分解语义不一致时次级失效。

## 6. Phase D — 外壳结果（security/PIE/SKR proxy）

- `PA.leak = actual_disclosure_bits per frame`（三档按 `stage_used`，含 tag 64b）。
- `security/PIE/SKR` 沿用 Polar reference 参数（`leak_EC_actual_bits, raw_ber, beta_eff_empirical`）标记 `authority=POLAR_REFERENCE_PROXY, readiness=reference, proxy_only=true`，不宣称 `composable`/`eps_sec/eps_cor/vis/phase-error` 有限密钥证明。
- 外壳报告含 `session/source/frame provenance + accepted/exact 四类 + disclosure per frame(三档) + per accepted + calls/rescue + runtime/throughput + stage_used 分布 + PA input leak 明细 + proxy PIE/SKR/key length + Wilson 95%` overall+per-source。

## 7. 真实数据二档边界（同域 vs 新 session）

- **同域可直接运行**：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, frame_len 1024, source 1M/1p5M/2M held-out 1600-1999/2213-2766/2916-3644`，`43/45` 已验 `hash_equal`，剩余需 `decoder-free 符号一致性校验`。
- **新 session 准入**：`decoder-free 信道域检查`（`P(B)` χ² / `H(A|B)` 漂移 `>0.05 bits` 判 `out-of-domain`）→ `新 calibration P(U1|B) via get_l1_prior_p_u1_given_b + P(U2|B,U1) via get_l1_app_prior_l2/factorize_f03` → `重算 m_total=floor((1.3*n*H-64)/5), m1=round(m_total*H1/H_total)` 后才可运行；期间**不调 LDPC**。

## 8. 与 V54/V62 衔接与守卫

- `V54` 二阶段 `Δ8+Δ8` 为本壳集成的 NB-LDPC 唯一臂；不改 `V54 registry` 与终态，不继续 `V54 run_01`。
- `V62` 仅为 reference 参数来源，不改 `V62` 的 `POLAR_REFERENCE_PROXY` 判定；本壳集成的 `PIE/SKR proxy` 仅 `shadow` 排序，不升级。
- 守卫：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-2]/ ==0` (除本变更外零改)，`py_compile PASS`，`HEAD==origin (fad33f4b)` 已验，`run_01` 不存在，正式壳集成未触发已验。

## 9. 证据写出（预冻结，未来执行）

- 固定增量根（decoder 前建，fail-closed）：`comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_smoke/` 与 `/run_01/`。
- 文件：`v63_records.json/.csv` (smoke `9-27` / dev `90-270` L2行)、`v63_summary.json`（分层含 shell 贯通）、`v63_shell_registry.json`, `v63_invalid_notice.json` (失败时)、`v63_data_readiness.json` (G1-G5)。CSV/JSON 行对等；禁写 NPZ。本轮仅冻结计划，不创建输出。

## R63 Revisions (PLAN_REVISION_CANDIDATE, 2026-08-30, HEAD 5602f11c)

**R63 Lifecycle**: PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED revision of 5602f11c, decoder-free spike only.
- **R63-01 32*u1+u2+exact**: Input FrameBatch holds full symbols s in [0,1023]; decomposition u1 = s //32 in [0,31], u2 = s %32 in [0,31]; reconstruction s_hat = 32*u1_hat + u2_hat (10-bit). reconciled_symbols is s_hat array (0..1023). exact_full = (u1_hat==u1_true and u2_hat==u2_true); exact_u1, exact_l2 separately counted. GF32 field operations apply to 5-bit sub-symbols only; full symbol is 10-bit composition.
- **R63-02 NbLdpcShellResult not change signature**: IRRunResult (comparison_bench/src/comparison_bench/methods/base.py) signature frozen no field rename/add/remove. New type ShellResult/NbLdpcShellResult wraps IRRunResult plus reconciled_symbols, accepted, exact, undetected, actual_disclosure_bits, decoder_calls, stage_used, pa_proxy. Verification: git diff -- comparison_bench/src/comparison_bench/methods/base.py ==0.
- **R63-03 smoke INTEGRATION_REPLAY_SMOKE 90 fresh zero overlap**: v63_smoke_registry.json authoritative 9 blocks sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63_smoke (INTEGRATION_REPLAY_SMOKE); v63_dev_registry.json authoritative 90 blocks sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63 (INTEGRATION_FRESH_CANDIDATE). Generation reads only frame_ids/metadata, zero decoder calls. Verified smoke intersect fresh = empty and smoke union fresh disjoint from V48..V54 used intervals (frame_ids exact overlap check).
- **R63-04 DOMAIN_CALIBRATION_REQUIRED**: Gate DOMAIN_CALIBRATION_REQUIRED blocks new-session execution unless domain_check PASS (P(B) chi2 p>=0.01 and |delta H(A|B)|<=0.05 bits) and if out-of-domain then calibration P(U1|B)/P(U2|B,U1) + m_total/m1 recomputation completed and persisted. Same-domain (84d62779) requires domain_check PASS but skips recalibration. Failure emits DOMAIN_CALIBRATION_REQUIRED without decoder.

