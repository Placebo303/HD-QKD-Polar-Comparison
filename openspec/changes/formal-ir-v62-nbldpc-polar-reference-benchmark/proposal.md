# OpenSpec Proposal: formal-ir-v62-nbldpc-polar-reference-benchmark

**Status**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 仅产出对齐可复现的基准计划与 decoder-free 对齐探针，不实现/运行 decoder，不改 Polar Release，不继续 V61/V60 数值
**Domain**: Formal IR / V62 NB-LDPC vs Polar reference 冻结对比基准 (V55 二阶段 rescue 的参考价值判定)
**Change ID**: `formal-ir-v62-nbldpc-polar-reference-benchmark`
**Cycle ID**: `V62P0` (nbldpc-polar-reference-benchmark), predecessor `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (`efd34ef318014e1d0505605062057b042e2180eb`) + `formal-ir-v61-security-measurement-specification` (`7b476f62...`) 共存，本变更为 V55 性能候选的**参考对比开发基准**，不改二者终态
**Branch**: `formal-ir-mainline`
**HEAD**: `6a3b873e` (用户给出当前 HEAD 前缀，实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == <full-40>` 重核为准；不一致阻塞；本次推送新 Plan SHA)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 冻结处理点，见 V54/V55) — 仅 NB-LDPC 侧锚点；Polar 侧实际 `pairing/threshold/dimension/block` 以 Phase A 机械提取为准，Phase B 逐块校验一致性
**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan + alignment spike，未对齐前禁止 decoder 实现/执行
**Method frozen**: `H1-16 (V31-H1-QC 16×1024 rank16 80b) + L1-APP syndrome-derived BP_i via H1 (TRAIN prior V25 channel_counts.npz)` + `Lane C support/标签/置换/MET图 ordinal-2 s38310x m2 184/190/192` + `H_inc1 8×1024 det1 / H_joint1 192/198/200 + H_inc2 8×1024 det2 / H_total 200/206/208 嵌套 rank m2/m2+8/m2+16` + `decoder 90/1.0 poly37 early-stop + L2-only 64-bit tag compute_tag_64(empty,x2) + verification-only + 每增量+40` 完全冻结零改（V54 唯一性能候选）

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free 对齐探针脚本 + 1 对齐报告 JSON/CSV；无 decoder、无矩阵改动、无新依赖（`numpy/pandas/pyarrow` 已装仅作探针校验）。laziest alternative: 若 Phase A/B 机械校验失败（无相同输入可重放），则直接落盘 `V62_COMPARISON_DATA_NOT_ALIGNED` 停止，不伪造对齐、不手填、不重估先验。

> **研究问题**：在**完全相同冻结数据块**（相同 `frame IDs / 1024-block / pairing / source` 分层，且 NB-LDPC 能用相同 Alice/Bob symbols 重放）上，**最佳 NB-LDPC (H1-16+L1APP+Lane C+Δ8+Δ8, leak 1144/1174/1184 stage2)** 的**实际纠错价值**相对 Polar Release 已有结果如何？回答仅 `COMPETITIVE / CORRECTION_WORKS_BUT_NOT_COMPETITIVE / NO_RETAINED_SIGNAL / COMPARISON_DATA_NOT_ALIGNED / EVIDENCE_INVALID` 五选一，`COMPETITIVE` 需 `NB-LDPC exact 不低于 Polar 容差且 undetected==0`。

## Goal

以最短可信路径在**完全冻结方法**与**只读 Polar 参考**下，完成**逐帧对应、公平泄漏/运行时长可比**的开发基准对比，回答 NB-LDPC 的保留价值：

1. **Phase A 只读提取 Polar reference（机械提取，零手填）**：从 `D:\Code\HD-QKD_Polar_Release` 及当前仓 `polar_existing` 桥接结果机械提取 Polar 版本/`commit`/结果 `provenance`、`frame/block IDs`、`success/FER`、`leakage`、`runtime`、`verification`、`PIE/SKR reference 公式/参数`，每项记录 `file/function/key`，禁止手填；Polar `finite-key/PIE/SKR` 仅标记 `POLAR_REFERENCE_PROXY` 不升级为 composable。
2. **Phase B 冻结公平比较集（逐帧对应优先）**：优先**逐帧对应且 NB-LDPC 能用相同 Alice/Bob symbols 重放**，强制 `相同 frame IDs、1024-block (4×256 frames)、pairing nearest legacy_v1、source 分层 1M/1p5M/2M`、不重估先验、不使用 V55 domain-incompatible 输入；若无法逐块同输入则 `V62_COMPARISON_DATA_NOT_ALIGNED` 停止，不伪造对齐。
3. **Phase C 指标冻结**：主指标 `exact_full/accepted rate (overall + per-source)、disclosure bits/block (总体与 per accepted)、calls/rescue (N_stage1_attempted/N_stage2_attempted/rescue_rate)、runtime/throughput、undetected==0`；次级仅用 Polar 同一 `shadow` 参数算 `PIE/SKR proxy` 作排序参考，不作门禁、不升级 claim。
4. **Phase D 开发基准设计（45 blocks paired）**：先 `15/source =45 blocks` paired development benchmark，Polar 直接复用不重跑，NB-LDPC `90-180 calls 硬帽180 (L1 45+base45+stage1≤45+stage2≤45, L2 45-135)`，不得调矩阵/`prior`/`decoder`/增量。
5. **终态五选一（first-match）**：`COMPETITIVE / CORRECTION_WORKS_BUT_NOT_COMPETITIVE / NO_RETAINED_SIGNAL / COMPARISON_DATA_NOT_ALIGNED / EVIDENCE_INVALID`，`COMPETITIVE` 至少 `NB-LDPC exact 不低于 Polar 容差且 undetected==0`（容差见 §Scope 冻结）。

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺 — 若未来执行配对基准，最终报告 SHALL 按 `overall + per-source` 分别包含 `exact_full vs Polar success`、`verify` 分别计数、`undetected` 隔离、`disclosure bits/block` 三档分布与 `per accepted`、`calls/rescue_rate per stage`、`runtime/throughput`、`paired delta` 明细、`PIE/SKR proxy` 仅排序；门禁仅用主指标，secondary 仅描述性。

## Non-Goals

- 不改 `H1-16 / L1-APP / Lane C / H_inc1/H_inc2=Δ8+Δ8 / m2 184/190/192 / decoder 90/1.0 poly37 / TRAIN-only prior / L2-only tag / verification-only / leak 1064/1094/1104→1144/1174/1184` 任一冻结量；不新增矩阵/标签/`prior`/阈值/`decoder` 参数，新增即 `EVIDENCE_INVALID`。
- 不修改 `D:\Code\HD-QKD_Polar_Release` 任何文件（只读提取；`git diff -- ../HD-QKD_Polar_Release ==0` 语义）；不重跑 Polar decoder；不把 `POLAR_REFERENCE_PROXY` 升级为 `composable` 或安全证明。
- 不重估先验（`V25 channel_counts.npz` 只读）；不用 V55 `domain-incompatible` 输入（V55 intake `256/frame` pairing 非 `1024-block` legacy_v1 或非 `A1/B5` 处理点则判不兼容）。
- 不创建正式 `comparison_bench/outputs_comparison/formal_ir_methods/v62_*/run_01` 或执行 decoder（本轮仅 plan + alignment spike，`rg "decode_" 0 hits` 在 spike 中，`py_compile PASS`）。
- 不继续 `V61/V60` 数值计算、有限密钥网格、或 `V55` 正式 `run_01` 执行；不改 `V38–V61` 既有输出与终态（`git diff -- openspec/changes/formal-ir-v6[0-1]/ ==0` 等）。
- 不做 `FER/阈值/SKR/安全/资格/晋升` 的扩大陈述；tag 仍 L2-only `≈2^-64` 工程近似；不宣称信息论安全界。
- 不伪造对齐：无相同输入可重放时直接 `V62_COMPARISON_DATA_NOT_ALIGNED` 停止，不以 `SER/vis` 代理或跨块平均冒充逐帧对应。

## Scope

1. **冻结 NB-LDPC 方法（完全冻结，零改，V54 complete）**：`n=1024, m2 184/190/192, GF32 poly37, H1 16×1024 rank16, L1-APP q_i=softmax(BP_i) via BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs (TRAIN prior), Lane C ordinal-2, H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 poly37 early-stop, verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64 syndrome_ok&&tag_ok, leak_base 1064/1094/1104 leak_stage1 1104/1134/1144 leak_stage2 1144/1174/1184 (+40/+80), TRAIN-only prior, verification-only 触发`。`exact_full=exact_u1&&exact_l2` oracle 仅统计。
2. **Phase A Polar reference 只读提取（机械提取，file/function/key，零手填，POLAR_REFERENCE_PROXY）**：对 `D:\Code\HD-QKD_Polar_Release` 执行只读 `rg` + `locate_existing_polar_outputs` + `_read_csv_header/_load_companion_supplements/benchmark_rows_from_polar_output` 机械提取（见 `comparison_bench/src/comparison_bench/io/polar_existing_bridge.py`），每项记录 `source_path, commit/version, processing_rule_version, pairing_path_tag, threshold_ps, bin_width_ps, dimension, n_eff_pairs, n_frames_total, n_frames_success/failed_decode/failed_verify, accepted_frame_fraction, raw_ser/raw_ber, leak_EC_actual_bits (+ leak_per_frame/per_input_bit), beta_eff_empirical (derived), runtime_s, throughput, verification fields, PIE/SKR formula (若仓内存在)`，并标记 `authority=POLAR_REFERENCE_PROXY, readiness=reference`，显式声明 `finite-key/PIE/SKR 仅 proxy 不升级`。
3. **Phase B 公平比较集冻结（逐帧对应优先，按序 first-match）**：
   - **优先对齐路径**：相同 `Alice/Bob symbols` 可重放（`polar_existing` 桥接或 Polar Release 原始 `pairs.parquet / sidecar a_eff.npy+b_eff.npy / ttbin→pairs` 输入可被 `load_pairs_table→normalize_pair_columns→build_frame_batch` 无损恢复，且 NB-LDPC 同 `q=1024, frame_len=1024, pairing=nearest legacy_v1` 可读）；强制 `frame IDs 对应、1024-block (4×256 frames) 连续、pairing nearest legacy_v1、source 分层 1M/1p5M/2M、delay_used_ps/bandwidth 一致`；逐块校验 `alice_symbol/bob_symbol` 完全相等（抽样 `hash` 比对）。
   - **不重估先验**：`V25 channel_counts.npz` 形态只读校验，不用新比较块训练。
   - **禁用 V55 域不兼容输入**：若 Polar 侧处理点为 `V55 intake` 的 `frames×256` 非 legacy_v1 或 `dimension≠1024` 或 `bin_width≠200ps` 或 `pairing_mode != nearest`，则判 `domain-incompatible` 禁用，不纳入比较集（避免 V55 的 `86+86` 行 `pairing_mode` 漂移）。
   - **未对齐停止**：若 `K_aligned <45` 或无法满足每源 `15` 逐帧对应且符号可重放，则 `overall = V62_COMPARISON_DATA_NOT_ALIGNED` 停止，不伪造、不平均替代、不放宽。
   - **若对齐通过**：冻结 `v62_paired_registry.json`（每块 `block_id, source, Polar frame_ids[4], NB-LDPC frame_ids[4] (identical), held_out_ordinal_start/end, pairs_count=1024, BLOCK_LENGTH=1024, sampling_mode=paired_polar_nbldpc_v62_development, Polar source_path+Polar commit, NB-LDPC H provenance`），`K=45` 规模可机械校验。
4. **Phase C 指标冻结（主/次分层，undetected 隔离）**：
   - **主指标（门禁与价值判定）**：`exact_full/accepted rate (overall 45 + per-source 15)、per-source exact_full 与 verify 分别计数、四类 exact/detected/decoder_non_syndrome/undetected（undetected==0 单独表，永不并入 success/FER）、disclosure bits/block (三档 leak_base/stage1/stage2 分布) 与 per accepted (total_disclosed_bits / final_exact_full_count, 为0则null)、calls/rescue (N_stage1_attempted=count(!verify_base) 与 N_stage2_attempted=count(!verify_stage1&&!verify_base) 及 rescue_rate, 禁用 45-base_exact 作分母)、runtime/throughput (per block + overall, 仅描述性但需可复现)、pairwise delta (base vs stage1 vs final vs Polar per block)`。
   - **次级（仅排序）**：用 Polar 同一 `shadow` 参数（`leak_EC_per_input_bit, raw_ber, beta_eff_empirical` 所在 `benchmark_rows_from_polar_output` 公式与 `compute_beta_eff_empirical` 的 `H(q)` 分解）计算 `PIE = beta_eff_empirical * H_binary_raw_ber` 与 `SKR proxy = accepted_frame_fraction * (PIE proxy - leak_per_frame)` 类 `shadow` 仅排序，不作门禁、不升级 claim，报告显式 `POLAR_REFERENCE_PROXY`。
   - **禁止**：泄漏分解语义不一致时跨方法排序（`leak_EC_actual_bits` 的 `tag` 与 `leak_other` 记账需显式一致性校验）。
5. **Phase D 开发基准设计（45 blocks paired, 硬帽180）**：
   - **规模**：`15/source =45 blocks` (`S=3, B=15`)，每块 `1024 symbols` (`4×256 frames`)，`K_aligned` 中确定性分散 `index_j=floor(j*(K-1)/14)` 若超集更大（否则直接取 aligned 45）。
   - **Polar 侧**：直接复用 `Polar reference` 已有结果 `n_frames_success/failed_*` 等，不重跑，不新增泄漏，不调参。
   - **NB-LDPC 侧**：`L1 45 + base45 + stage1≤45 + stage2≤45 =90-180 硬帽180 (L2 45-135)`，`per block L1 1+base1+stage1≤1+stage2≤1`，`verification-only` 触发 (`syndrome_ok&&tag_ok` 才增量)，`leak_base/stage1/stage2` 三档 `1064/1094/1104 →1104/1134/1144 →1144/1174/1184` (per source)。
   - **零改**：矩阵/`prior`/`decoder`/增量全冻，不引入第三增量或 `Δm=4/12/16` 多档，不以 outcomes 选行。
6. **终态五选一（first-match，互斥，COMPETITIVE 容差冻结）**：
   ```
   if not polar_reference_mechanically_extracted or not alignment_metadata_complete or old_data_fake_PE or verification_caliber_mismatch:
       overall = V62_EVIDENCE_INVALID
   elif not alignment_possible (K_aligned<45 or not per_source_15_paired_replayable or V55_domain_incompatible or pairing_mismatch):
       overall = V62_COMPARISON_DATA_NOT_ALIGNED  # 停止，不进 decoder
   elif nbldpc_execution_not_yet_done (本轮):
       overall = V62_PLAN_CANDIDATE__ALIGNMENT_SPIKE_DONE  # 本轮仅 plan + spike，不判后续三态
   # 未来执行后（需新 OpenSpec + 独立授权）再判：
   # elif nbldpc_overall_exact >= polar_overall_success -2  ∧ per_source nbldpc >= polar per_source -1  ∧ undetected==0  ∧ rank/nested/verification/记账通过
   #        → V62_COMPETITIVE
   # elif nbldpc_has_signal (any exact>0 or residual improvement) but not COMPETITIVE → V62_CORRECTION_WORKS_BUT_NOT_COMPETITIVE
   # else → V62_NO_RETAINED_SIGNAL
   ```
   - **COMPETITIVE 容差冻结**（配对开发基准 45 块）：`overall exact_full ≥ Polar overall success -2` (44/45 容差) 且 `per-source exact_full ≥ Polar per-source success -1` 且 `undetected==0` 且 `rank/nested/verification/记账` 通过；`disclosure/PIE proxy` 仅报告不作硬门禁，但 `leak_per_accepted` 需可比（语义一致性校验通过）。
   - `CORRECTION_WORKS_BUT_NOT_COMPETITIVE`：NB-LDPC `exact_full>0` 或 `stage1/stage2 rescued>0` 或 `mean residual improvement` 但未达 `COMPETITIVE` 容差。
   - `NO_RETAINED_SIGNAL`：`exact_full==0` 且 `rescued==0` 且无残留改善信号。
   - `V62_EVIDENCE_INVALID` 优先于 `COMPARISON_DATA_NOT_ALIGNED`。
7. **Lifecycle 冻结**：本轮 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何 `NB-LDPC` 正式执行需 `alignment_spike PASS + 独立 plan ACCEPT + 显式 EXECUTE_AUTH 绑定到精确实现 SHA + paired registry`；不启动下一阶段正式执行；本轮仅四工件+decoder-free 对齐探针。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v62-nbldpc-polar-reference-benchmark/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）+ `scripts/v62_polar_nbldpc_alignment_spike.py` (decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`, 只读提取 Polar reference + 对齐校验) + `docs/research_cycles/V62P0/v62_alignment_spike_report.json/.csv`（探针输出，含 Polar provenance、frame/block IDs、success/FER、leakage、runtime、verification、PIE/SKR formula proxy 标记、对齐判定）。
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/formal_ir/v62_nbldpc_polar_benchmark.py`（仅组合 V54 冻结方法+paired 45-block+二阶段条件 runner+Polar 复用，不新增 decoder）+ `scripts/execute_v62_benchmark.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`，**仅当 alignment PASS + 独立 plan ACCEPT + EXECUTE_AUTH 后才允许创建**。
- **只读依赖**：`comparison_bench/src/comparison_bench/io/polar_existing_bridge.py` (`locate_existing_polar_outputs/select_polar_output/benchmark_rows_from_polar_output/_load_companion_supplements`)、`comparison_bench/src/comparison_bench/io/pairs_loader.py` (`load_pairs_table/normalize_pair_columns`)+`dataset_builder.py` (`build_frame_batch`)、V31 H1、V25 `channel_counts.npz`、`D:\Code\HD-QKD_Polar_Release` (只读)、`comparison_bench/outputs_comparison/v55_intake_20260828` 仅作 `domain-incompatible` 负例参考（不纳入比较）、authoritative `v55_authoritative_registry` 仅作已用区间排除参考。
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V61` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不改 `D:\Code\HD-QKD_Polar_Release`；不创建正式 `run_01` 输出。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `6a3b873e` 前缀（重核 `6a3b873e` 完整 40 位），`branch formal-ir-mainline`，`data SHA 84d62779` (`d=1024 bw=200 pairing=nearest legacy_v1`) 已记录，`implementation_started=false`，`production_outputs_created=false`，明确“未对齐前不得实现/运行 decoder，不改 Polar Release，不继续 V61/V60，等待 alignment spike + 独立 review”。
- [ ] Phase A 机械提取可复现：`D:\Code\HD-QKD_Polar_Release` 及当前仓桥接结果已通过 `polar_existing_bridge.py` 的 `locate/select/benchmark_rows` 机械提取，每项 `file/function/key` 已记录，无手填，`rg` 可复现，Polar `finite-key/PIE/SKR` 仅标记 `POLAR_REFERENCE_PROXY` 不升级，`beta_eff_empirical` 为 `compute_beta_eff_empirical` 派生（见 `comparison_bench/src/comparison_bench/metrics/leakage.py`）。
- [ ] Phase B 公平比较集可机械校验：`1024-block (4×256 frames) + pairing nearest legacy_v1 + dimension 1024 + bin_width 200ps + source 分层` 已冻结，`frame IDs` 逐块对应且 `Alice/Bob symbols` 可重放已验（`hash` 比对），`V25 prior` 只读，不重估，V55 `domain-incompatible` 输入已排除，未对齐时 `V62_COMPARISON_DATA_NOT_ALIGNED` 已正确停止，不伪造。
- [ ] Phase C 指标已冻结：主指标 `exact_full/accepted rate (overall+per-source)、disclosure bits/block 与 per accepted、calls/rescue (N_stage1/N_stage2/rescue_rate, 禁 45-base_exact 分母)、runtime/throughput、undetected==0` 单独表；次级 `PIE/SKR proxy` 用 Polar 同一 shadow 参数仅排序，不作门禁，报告显式 `POLAR_REFERENCE_PROXY`。
- [ ] Phase D 开发基准已冻结：`15/source=45 blocks` paired，Polar 直接复用不重跑，NB-LDPC `90-180 calls 硬帽180 (L2 45-135)`，`per block 2-4 calls`，矩阵/`prior`/`decoder`/增量全冻 `Δ8+Δ8` 唯一，禁止新造第二候选。
- [ ] 终态五选一已冻结：`V62_COMPETITIVE / V62_CORRECTION_WORKS_BUT_NOT_COMPETITIVE / V62_NO_RETAINED_SIGNAL / V62_COMPARISON_DATA_NOT_ALIGNED / V62_EVIDENCE_INVALID` 互斥且 `EVIDENCE_INVALID` 优先；`COMPETITIVE` 需 `overall NB-LDPC ≥ Polar -2 且 per-source ≥ Polar per-source -1 且 undetected==0` 已显式，不以总体平均掩盖单源。
- [ ] 本轮产出边界已冻结：仅四工件+对齐探针脚本/报告，**禁 production module/CLI/tests/正式 output root/执行 decoder/自授 EXECUTE_AUTH**；探针 `rg "decode_" 0 hits`、`py_compile PASS`、`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v6[0-1]/ ==0`（除本变更外零改），`git diff -- ../HD-QKD_Polar_Release ==0` 语义只读。
- [ ] 已推送并停在 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` 等待独立 plan review + alignment spike 复核。

## Tasks

见 `tasks.md`（Phase A Polar reference 只读机械提取；Phase B 公平比较集冻结与对齐探针；Phase C 指标冻结；Phase D 45-block paired 开发基准设计与五终态；显式禁止清单与对齐门禁）。

## Lifecycle

前代 `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (`efd34ef318...`, `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED`) 与 `formal-ir-v61-security-measurement-specification` (`7b476f62...`, `PLAN_CANDIDATE / DECODE_FORBIDDEN`) 共存；V62 当前 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`（HEAD `6a3b873e`, branch `formal-ir-mainline`, data SHA `84d62779`），止于 plan + alignment spike，未对齐前禁止 decoder 实现/执行；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何正式基准执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA + `v62_paired_registry.json`；本轮仅四工件+对齐探针，45块为 paired development benchmark，V62 通过仍仅 `development benchmark` 证据，不扩大为 qualification/promotion/安全证明。
