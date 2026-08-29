# OpenSpec Tasks: formal-ir-v62-nbldpc-polar-reference-benchmark — V62 NB-LDPC vs Polar Reference 基准

**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — **仅 plan + alignment spike，未对齐前禁止实现/运行 decoder，不改 Polar Release，不继续 V61/V60**
**HEAD**: `6a3b873e` → 新 Plan SHA (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == 6a3b873e` 重核，不一致阻塞) + data SHA `84d62779` (200ps legacy_v1 nearest 1024, q1024)
**Predecessor**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` `efd34ef318...` (V55 二阶段性能候选已冻) + `formal-ir-v61` `7b476f62...` (安全规范仅参考)；本变更为 V55 候选的**参考对比开发基准**，不改二者终态
**Boundary**: 每 block 1024 symbols (`4×256 frames`), `GF32 log2q=5`, `tag=64 L2-only` 仅 `total` 计一次；`H1/Lane C/H_inc/Δ/decoder 90/1.0 poly37/estimator` 全冻；Polar `finite-key/PIE/SKR` 仅 `POLAR_REFERENCE_PROXY` 不升级；`R62-01` 冻结 `COMPETITIVE = overall -2 且 per-source -1 且 undetected==0`；`R62-02` 冻结 `leak_IR 已含 tag64` 与 `V55 domain-incompatible` 排除；未对齐 `V62_COMPARISON_DATA_NOT_ALIGNED` 停止

## Phase A — Polar reference 只读机械提取（decoder-free，禁止手填，file/function/key，POLAR_REFERENCE_PROXY）

- [ ] **A1 fetch 与 HEAD 自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline == 6a3b873e` 完整 40 位，不一致则阻塞；记录 `HEAD/origin/implementation SHA` 至 `V62` 报告 `provenance`，`rg "efd34ef" 0 hits` 旧 SHA 无残留（除历史记录），`rg "6a3b873e"` 新起点已验；`data SHA 84d62779` 已验
- [ ] **A2 Polar Release 只读定位（只读，不改）**：对 `D:\Code\HD-QKD_Polar_Release` 执行 `rg "polar|e2e|diag|results" --type csv` + `locate_existing_polar_outputs([Path("D:/Code/HD-QKD_Polar_Release")])` 机械定位候选 `Path`s，记录每候选 `stat.mtime/size` 与 `_read_csv_header` 列名，`git diff -- ../HD-QKD_Polar_Release` 零改已验（只读），`rg "polar_existing" 0 hits` 在 Polar Release 侧无侵入
- [ ] **A3 Polar 现有输出择优（机械打分，不手选）**：调用 `polar_existing_bridge.py:select_polar_output(candidates)` + `_score_candidate` (对 `polar_diag_summary.csv` / `polar_e2e_results_refresh.csv` 等 `PREFERRED_OUTPUT_ORDER` 打分 + `leak` 列加分 + `PASS` 行加分)，记录 `selected_path, score_tuple, PREFERRED_OUTPUT_ORDER`，`select_polar_output` 的幂等性已验（两次调用同路径）
- [ ] **A4 逐行机械提取（file/function/key，零手填）**：调用 `benchmark_rows_from_polar_output(selected_path)` 逐行提取 `dataset_id/loss_db/dimension/bin_width_ps/n_eff_pairs/frame_len_symbols/processing_rule_version/pairing_path_tag/threshold_ps/effective_pairing_window_ps/raw_ser/raw_ber/leak_EC_actual_bits/leak_EC_per_frame/leak_EC_per_input_bit/beta_eff_empirical/runtime_s/throughput_input/output/n_frames_total/success/failed_decode/failed_verify/accepted_frame_fraction/post_ir_ser/ber`，每项记录 `file=comparison_bench/src/comparison_bench/io/polar_existing_bridge.py + function=_first_float/_ci_float/_first_value/_first_int/benchmark_rows_from_polar_output + key=row[col]`，`beta_eff_empirical` 已验为 `compute_beta_eff_empirical(leak, n_bits, raw_ber)` 派生非手填
- [ ] **A5 伴随文件与缺失字段审计**：调用 `_companion_paths` + `_load_companion_supplements` 记录 `checked_files/by_key/missing_after_companion_scan` + `source_missing_fields`，对 `SUPPLEMENT_FIELDS = leak_EC_actual_bits/runtime_s/n_frames_success/failed_decode/failed_verify/throughput_input_bits_per_s` 逐项审计 `present/missing`，`missing_after_companion_scan` 已落盘 `v62_polar_reference.json`
- [ ] **A6 Polar 版本/commit/provenance 绑定**：对 `D:\Code\HD-QKD_Polar_Release` 执行 `git rev-parse HEAD` + `git log --oneline -1` + `experiments/run_real_polar_max_pie.py --version` (若存在) 记录 `polar_commit, polar_version, selected source_path, PREFERRED_OUTPUT_ORDER, companion checked_files`，`Polar Release` 不改已验（`git status --short` 在 Polar Release 侧无 dirty）
- [ ] **A7 PIE/SKR reference 公式审计（POLAR_REFERENCE_PROXY 标记）**：`rg "pie|skr|finite.key|leak_EC" D:\Code\HD-QKD_Polar_Release --type py --type csv -n` 逐项追踪 `PIE/SKR/finite-key` 公式/参数来源（`file:line:expr`），若 Polar 输出含 `pie/skr` 列则机械提取，否则 `missing` 并标记 `authority=POLAR_REFERENCE_PROXY, readiness=reference, proxy_only=true`，显式声明 `finite-key/PIE/SKR 仅 proxy 不升级`，不手填
- [ ] **A8 Polar reference 落盘（机械提取 JSON）**：落盘 `docs/research_cycles/V62P0/v62_polar_reference.json` (含 `polar_commit, polar_version, selected_path, score, per_row provenance + per_key file/function/key, companion checked_files, missing_fields, pie/skr proxy marking`) + `v62_polar_reference.csv` 紧凑表，`py_compile PASS`，`rg "decode_" 0 hits` 在探针侧已验

## Phase B — 公平比较集冻结与对齐探针（逐帧对应优先，按序 first-match，未对齐停止）

- [ ] **B1 冻结处理点与块形态（单点 84d62779）**：冻结 `dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, frame_len_symbols 1024 (4×256 frames), pairs_count 1024, BLOCK_LENGTH 1024, q=1024, log2q=5, tag 64 L2-only`，记录 `data SHA 84d62779` 语义，不改
- [ ] **B2 可重放性校验（hash 比对，decoder-free）**：对 Polar 侧每块 `source_path` 的 `pairs.parquet / sidecar a_eff.npy+b_eff.npy` 执行 `load_pairs_table(path) -> normalize_pair_columns -> build_frame_batch(q=1024, frame_len=1024)` 无损恢复，校验 `alice_symbol/bob_symbol ∈ [0,1024)` 且 `n_complete == n_rows//1024 ≥15 per source` 且 `rows_used==n_keep` 无尾帧残留，抽样 `sha256(alice.tobytes()+bob.tobytes())` 与 NB-LDPC 侧同 `frame_ids` 符号完全相等已验（`assert hash_equal`）
- [ ] **B3 V55 domain-incompatible 排除（硬门）**：检查若 Polar 侧处理点为 `V55 intake` 的 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` 的 `frames×256` 非 `1024-block legacy_v1` 或 `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` 或 `dimension≠1024` 或 `bin_width≠200ps` 或 `pairing_mode != nearest`，则判 `domain-incompatible` 禁用，不纳入比较集，记录 `v55_excluded_blocks.csv`，`rg "v55" 0 hits` 不纳入后已验
- [ ] **B4 不重估先验校验（只读）**：`load_v25_channel_counts()` 形态校验（`channel_counts.npz` 存在且 `keys` 含 `channel_counts`），确认比较集构建不读取新比较块做训练，`prior_is_train_only=true` 已验
- [ ] **B5 对齐探针实现（decoder-free, rg 0 hits）**：编写 `scripts/v62_polar_nbldpc_alignment_spike.py` (`python scripts/v62_polar_nbldpc_alignment_spike.py [--polar-root D:/Code/HD-QKD_Polar_Release] [--pairs-root ...] [--out docs/research_cycles/V62P0/v62_alignment_spike_report.json]`) → A2-A4 定位/择优/逐行提取 → B1-B4 冻结校验 → G1-G5 分层门判定 → 输出 `v62_alignment_spike_report.json/.csv` + `v62_paired_registry_candidate.json` (若对齐通过则含 `frame_ids` 逐块绑定)，`rg "decode_" 0 hits && rg "import.*decoder" 0 hits && rg "construct_" 0 hits` 已验，`py_compile PASS`，未创建 `run_01`
- [ ] **B6 对齐判定（first-match，未对齐停止）**：
  ```
  if not polar_reference_mechanically_extracted or not alignment_metadata_complete:
      overall = V62_EVIDENCE_INVALID
  elif K_aligned<45 or per_source<15 or not replayable or V55_domain_incompatible or pairing_mismatch or dimension/bw mismatch:
      overall = V62_COMPARISON_DATA_NOT_ALIGNED  # 停止，不伪造，不平均替代
  else:
      overall = V62_ALIGNMENT_READY  # 可冻结 paired registry
  ```
  `first_match` 显式记录，`V62_COMPARISON_DATA_NOT_ALIGNED` 时不创建 paired registry 正式版，不进 Phase D 执行
- [ ] **B7 Paired registry 冻结（若 ALIGNMENT_READY）**：落盘 `docs/research_cycles/V62P0/v62_paired_registry.json` ( authoritative, `S=3, B=15, total 45`, 每块 `block_id, source(1M/1p5M/2M), Polar frame_ids[4] == NB-LDPC frame_ids[4] (identical), held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode=paired_polar_nbldpc_v62_development, Polar source_path+commit, NB-LDPC H provenance (H1/Lane C/H_inc1/H_inc2), hash(alice||bob)`)，`K=45` 可机械校验，`gap≥4` 若超集分散则 `index_j=floor(j*(K-1)/14)` 否则直接取 aligned 45，`git diff -- ../HD-QKD_Polar_Release ==0` 已验

## Phase C — 指标冻结（主/次分层，undetected 隔离，PIE/SKR 仅排序）

- [ ] **C1 主指标 exact/accepted 冻结（overall+per-source）**：冻结 `exact_full = exact_u1 && exact_l2` per block 的 `overall 45` 与 `per-source 15` 计数/率，`verify_base/verify_stage1/verify_final` 与 `Polar n_frames_success` 分别计数（`exact != verify` 隔离），`Polar_success_45 = round(accepted_frame_fraction*45)` 与 `per-source = round(frac*15)` 折算已验
- [ ] **C2 四类与 undetected 隔离冻结**：冻结 `exact / detected (syndrome_fail) / decoder_non_syndrome (converged_no_syndrome) / undetected (syndrome_ok&&tag_ok&&!exact)` 四类计数，`undetected==0` 单独表永不并入 `success/FER`，`undetected>0` 则 `EVIDENCE_INVALID` 优先已验
- [ ] **C3 泄漏与 calls/rescue 冻结（decoder-free 公式校验）**：冻结 `leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184` 三档 (`leak=5*m_total+64` 双校验 `m_total 1405/1475/1540`) + `per_source_avg[s]=leak_base[s]+40*N_stage1[s]/15+40*N_stage2[s]/15` + `overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/45` + `per accepted = total_disclosed_bits / final_exact_full_count (为0则null)` + `calls: N_stage1_attempted=count(!verify_base) , N_stage2_attempted=count(!verify_base&&!verify_stage1), rescued_stage1, rescued_stage2, rescue_rate = rescued/attempted (禁 45-base_exact 分母)`，`py_compile` 前公式双校验已验
- [ ] **C4 runtime/throughput 冻结（仅报告可复现）**：冻结 `runtime_s per block + overall` (Polar 侧复用 `runtime_s`，NB-LDPC 侧未来实测) + `throughput_input/output` ( `n_bits/runtime`, `n_success*frame_len_bits/runtime` )，`benchmark_rows_from_polar_output` 的 `throughput` 派生已验
- [ ] **C5 pair delta 与 Wilson 冻结**：冻结 `per block NB-LDPC final vs Polar` 的 `exact delta, leak delta, runtime delta` 明细 + `Wilson 95%` per source & overall ( `exact/rate` 分别报告，不作门禁 )
- [ ] **C6 次级 PIE/SKR proxy 冻结（POLAR_REFERENCE_PROXY 仅排序）**：冻结 `PIE proxy = beta_eff_empirical * H_shannon` 与 `SKR proxy = accepted_frame_fraction * (PIE - leak_per_frame)` 用 Polar 同一 `shadow` 参数（`leak_EC_per_input_bit, raw_ber, beta_eff_empirical`）计算，报告显式 `POLAR_REFERENCE_PROXY` 不升级，不作门禁；泄漏分解语义不一致时该次对比次级失效已验

## Phase D — 45-block paired 开发基准设计与五终态（硬帽180，未对齐前不执行 decoder）

- [ ] **D1 规模冻结（15/source=45 blocks）**：冻结 `S=3, B=15, total 45`, 每块 `1024 symbols (4×256 frames)`, `K_aligned` 中若超集更大则 `index_j=floor(j*(K-1)/14) j=0..14` 分散选 `15/source`，否则直接取 aligned 45，`paired registry` 禁换块已验
- [ ] **D2 Polar 复用分支冻结（零 decoder）**：冻结 Polar 侧直接复用 `n_frames_success/failed_* / leak/runtime/verify/beta/pie proxy` 不重跑，不新增泄漏，不调参，`source_path+commit` 双绑定已验
- [ ] **D3 NB-LDPC 三阶段协议冻结（硬帽180, verification-only）**：
  ```
  per paired block:
    prior = TRAIN prior (shared)
    Polar reuse (no decode)
    NB-LDPC: H1 s1 -> L1 BP -> P(U2) (L1 45)
             base: H_base (m2) -> verify_base; if pass leak_base else H_joint1 (m2+8) -> verify_stage1; if pass leak_stage1 else H_total (m2+16) -> verify_stage2 leak_stage2
  budget: L1 45 + base45 + stage1≤45 + stage2≤45 =90-180 硬帽180 (L2 45-135)
  ```
  `verification-only` 触发已验，`leak_base/stage1/stage2` 三档 `1064/1094/1104→1104/1134/1144→1144/1174/1184` 已验，`rank_total==m2+16 nested/independence==8 row≤16` 已验
- [ ] **D4 零改校验（H/prior/decoder/增量）**：`H1-16 rank16, Lane C m2 184/190/192 support/标签/置换, H_inc1 det1 + joint1 192/198/200, H_inc2 det2 + total 200/206/208, decoder 90/1.0 poly37, TRAIN-only, L2-only tag, +40/+80` 全冻，不新增矩阵，不试 `Δm=4/12/16` 多档，不以 outcomes 选行，`rg "decode_" 0 hits` 在 plan 侧已验
- [ ] **D5 五终态冻结（first-match，COMPETITIVE 容差）**：
  ```
  if not polar_reference_mechanically_extracted or not alignment_metadata_complete or rank/nested/verification/记账失败:
      overall = V62_EVIDENCE_INVALID  # 优先
  elif not alignment_possible (K_aligned<45 or per_source<15 or V55_domain_incompatible or pairing_mismatch or not replayable):
      overall = V62_COMPARISON_DATA_NOT_ALIGNED  # 停止
  elif nbldpc_not_yet_executed (本轮):
      overall = V62_PLAN_CANDIDATE__ALIGNMENT_SPIKE_DONE
  # 未来执行后（需 alignment PASS + 独立 plan ACCEPT + EXECUTE_AUTH）:
  # elif nbldpc_overall_exact >= polar_overall_success -2  ∧ per_source nbldpc >= polar per_source -1  ∧ undetected==0 ∧ rank/nested/记账通过 → V62_COMPETITIVE
  # elif nbldpc_has_signal (any exact>0 or rescued>0 or residual improved) but not COMPETITIVE → V62_CORRECTION_WORKS_BUT_NOT_COMPETITIVE
  # else → V62_NO_RETAINED_SIGNAL
  ```
  `COMPETITIVE` 容差 `-2/45 overall, -1/15 per-source, undetected==0` 已显式，不以总体平均掩盖单源
- [ ] **D6 互斥性与伪造审计**：`assert overall in [EVIDENCE_INVALID, COMPARISON_DATA_NOT_ALIGNED, PLAN_CANDIDATE__ALIGNMENT_SPIKE_DONE, COMPETITIVE, CORRECTION_WORKS_BUT_NOT_COMPETITIVE, NO_RETAINED_SIGNAL] 且仅一态`，`rg "H_min.*=.*IAB|IAB.*H_min" 0 hits` 无自创，`old_data_fake_PE` 零验，`only_ALIGNMENT_READY_then_bench: assert (overall==COMPARISON_DATA_NOT_ALIGNED) == (K_aligned<45)` 已验

## Phase E — 对齐探针与报告交付（PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED，普通推送后停止）

- [ ] **E1 编写 `scripts/v62_polar_nbldpc_alignment_spike.py`** (decoder-free, 可选但本轮必验)：`python scripts/v62_polar_nbldpc_alignment_spike.py [--polar-root D:/Code/HD-QKD_Polar_Release] [--pairs-root ...] [--polar-csv ...] [--out-dir docs/research_cycles/V62P0]` → A2-A4 Polar 定位/择优/逐行提取 → B1-B4 冻结校验 → G1-G5 分层门判定 → 输出 `v62_polar_reference.json/.csv + v62_alignment_spike_report.json/.csv + v62_paired_registry_candidate.json` + 控制台摘要，`rg "decode_" 0 hits`，`py_compile PASS`，未创建 `run_01`，不改 `src//experiments//tools/` 且 `openspec/changes/formal-ir-v6[0-1]/` 零改，不进正式基准
- [ ] **E2 执行对齐探针（decoder-free, 只读）**：执行 `python scripts/v62_polar_nbldpc_alignment_spike.py` 记录 `K_aligned, per_source_aligned, replayable_hash_equal, V55_excluded, pairing_ok, dimension_ok, Polar provenance (commit/version/selected_path/score), per-row file/function/key`，`K_aligned<45` 时落盘 `V62_COMPARISON_DATA_NOT_ALIGNED` 报告并停止，不伪造
- [ ] **E3 撰写 `docs/research_cycles/V62P0/V62_ALIGNMENT_SPIKE_REPORT.md`**：`Polar reference 机械提取表` (commit/version/selected_path/每行 file/function/key/beta 派生/pie proxy 标记) + `公平比较集冻结表` (处理点 84d62779, 1024-block, pairing, source 分层, 不重估先验, V55 排除) + `对齐判定表` (K_aligned per-source, replayable, V55_domain_incompatible, pairing_mismatch) + `Phase C/D 指标与规模` (主/次指标, 45-block paired, 硬帽180) + `五终态与 COMPETITIVE 容差` + `overall 终态 (ALIGNMENT_READY 或 COMPARISON_DATA_NOT_ALIGNED)` 与规范闭合声明，数据与 `json/csv` 一致，显式 `V54-V55 m/leak 冻结` + `Polar proxy 不升级` + `tag 已含不重复` + `三源分别不平均` + `未对齐停止` + `本轮不执行 decoder`
- [ ] **E4 自检（gate）**：`py_compile PASS, rg "decode_" 0 hits && rg "import.*decoder" 0 hits && rg "construct_" 0 hits` (探针脚本侧)，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-1]/ ==0 && git diff -- ../HD-QKD_Polar_Release ==0` (除本变更外零改)，三源 `leak_without_tag/tag` 不重复已验，`GF32 5bits` 已验，不跨源平均已验，`COMPETITIVE -2/-1 容差` 已验，`only_ALIGNMENT_READY_then_bench` 已验，`K_aligned` 机械校验已验，`HEAD==origin (6a3b873e)` 已验，`run_01` 不存在已验，正式基准未触发已验
- [ ] **E5 普通推送新 Plan SHA 并停留 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`**（基于 `6a3b873e`），未创建任何 `run_01` decoder 执行，不碰 `V54-V61 m/leak`，`src//experiments//tools//V54-V61` 零改，普通推送（非 force）至 `formal-ir-mainline`，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`），`V62` 仍 `PLAN_CANDIDATE`，返回 `Plan SHA / implementation SHA / Polar provenance / K_aligned / paired registry / 五终态`，**不自动进入正式基准执行，不实现正式 runner**

## 本变更显式禁止

decoder 调用（`decode_* / construct_*` 等）在探针中；改 `V54 m1/m2/leak` 或 `H1/Lane C/Δ/decoder` 冻参或新增矩阵；改 `LDPC` 码族；重跑 Polar；自创 `H_min / finite-key / composable` 公式或造 `eps_sec/eps_cor/vis/phase-error` 参数；用旧数据伪造对齐（无相同符号重放时伪造 `frame_ids`）；重复扣除 `tag 64`；将总体平均掩盖单源阈值；网格调参；把 V55 `frames×256` 非 legacy_v1 输入当 1024-block；宣称 `FER/SKR/阈值/晋升`；创建正式 `run_01` decoder 执行；改 `src//experiments//tools//V54-V61`；将 Polar `proxy` 升级为 `composable`；在 `V62_COMPARISON_DATA_NOT_ALIGNED` 时仍进入正式基准；实现正式 runner/启动正式基准（本轮仅 4 工件+探针，普通推送新 Plan SHA 后停止）。

## 验收

- proposal/design/tasks/specs 一致 HEAD `6a3b873e`→新 Plan SHA 84d62779 lifecycle PLAN_CANDIDATE DEVELOPMENT_BENCHMARK EXECUTE_NOT_AUTHORIZED；Polar reference 机械提取 `file/function/key` 已落盘 `POLAR_REFERENCE_PROXY`，五终态按 `EVIDENCE_INVALID > COMPARISON_DATA_NOT_ALIGNED > COMPETITIVE (>CORRECTION_WORKS... >NO_SIGNAL)` 互斥先匹配，**未对齐 `V62_COMPARISON_DATA_NOT_ALIGNED` 立即停**，`COMPETITIVE` 需 `overall -2 且 per-source -1 且 undetected==0` 已显式
- Phase A Polar `version/commit/result provenance/frame-block IDs/success-FER/leakage/runtime/verification/PIE-SKR formula` 逐项 `file/function/key` 已覆盖，每项 `source(file:line:expr or data_path:provenance) / authority=POLAR_REFERENCE_PROXY / readiness=reference` 已定义，`beta_eff_empirical` 派生已验，`finite-key/PIE/SKR` 仅 proxy 不升级已验
- Phase B `1024-block + pairing nearest legacy_v1 + dimension 1024 + bin_width 200ps + source 分层 + 不重估先验 + V55 domain-incompatible 排除` 已冻结，`frame IDs` 逐块对应且 `Alice/Bob` 可重放 `hash` 已验，未对齐停止已验，不伪造已验
- Phase C 主指标 `exact_full/accepted (overall+per-source) / disclosure bits/block 与 per accepted / calls/rescue (N_stage1/N_stage2/rescue_rate) / runtime/throughput / undetected==0` 单独表，次级 `PIE/SKR proxy` 用 Polar 同一 shadow 参数仅排序已验
- Phase D `15/source=45 blocks` paired 开发基准 `Polar 复用 + NB-LDPC 90-180 硬帽180 (L2 45-135)` 已冻结，矩阵/`prior`/`decoder`/增量全冻 `Δ8+Δ8` 唯一，禁止新造第二候选已验
- Phase E 探针 `rg 0 hits` `py_compile` PASS 报告与 `json/csv` 一致 未建 `run_01` 未进正式基准 未重跑 Polar 未改 `V54-V61` 已普通推送新 Plan SHA `PLAN_CANDIDATE/DEVELOPMENT_BENCHMARK/EXECUTE_NOT_AUTHORIZED` 仅改本目录+`scripts/`+`docs/research_cycles/V62P0/`（`src//experiments//tools//V54-V61` 零改），`HEAD==origin (6a3b873e)` 已验，推送后等待独立审核，**不自动进入正式基准，不实现正式 runner**

