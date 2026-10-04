# OpenSpec Design: formal-ir-v62-nbldpc-polar-reference-benchmark

**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — **仅 plan + decoder-free 对齐探针，未对齐前禁止实现/运行 decoder，不改 Polar Release，不继续 V61/V60**
**Cycle**: `V62P0`
**Predecessor**: `formal-ir-v55` (`efd34ef318...`) 冻结二阶段 rescue 性能候选 + `formal-ir-v61` (`7b476f62...`) 冻结安全测量规范，本变更为 V55 候选的**参考对比开发基准**
**Freeze HEAD**: `6a3b873e` (branch `formal-ir-mainline`, 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) — **data SHA** `84d62779` (`d=1024 bw=200 pairing=nearest rule=legacy_v1`, 单点, 见 V54/V55 semantics)
**Feasibility**: V54 二阶段 `H_total 200/206/208 rank m2+16 nested True` 已在 V54 spike 三源实证；`polar_existing_bridge.py` 的 `locate/select/benchmark_rows` 对 Polar 现有输出可机械提取；唯一待验为**是否能在完全相同冻结数据块上逐帧对应且符号可重放**。
**Key judgement**: **算法价值需在相同输入上对比，而非各自最优报告的数值对比**；若 Polar 与 NB-LDPC 输入不可逐块同输入，则对比无意义，直接 `V62_COMPARISON_DATA_NOT_ALIGNED` 停止，不伪造、不泛化。

## 1. 科学问题与关键判断

> 在**完全冻结 V54 二阶段最佳 NB-LDPC**（`H1-16 + L1-APP + Lane C + Δ8+Δ8, leak 1144/1174/1184 stage2`）的**相同参数**下，**与 Polar Release 已有结果在完全相同冻结数据块上逐帧对应**时，NB-LDPC 是否具有可保留的纠错价值？价值仅分 `COMPETITIVE / CORRECTION_WORKS_BUT_NOT_COMPETITIVE / NO_RETAINED_SIGNAL` 三档，`COMPETITIVE` 需 `exact 不低于 Polar 容差且 undetected==0`。

- **对照**：单一对照臂为 `polar_existing` 已有结果（只读复用，不重跑）；NB-LDPC 三阶段 `base vs stage1(Δ8) vs final(Δ16)` 配对（同一 `P_i(U2)` 与 `bob`/`prior` 共享，仅 `H_L2/syndrome` 不同），但与 Polar 的对比为 `final NB-LDPC vs Polar final` 逐块配对（每块 1024 symbols 同步）。
- **不改项**：不改 `H1-16/Lane C/H_inc1/H_inc2/m2/prior/decoder 90/1.0 poly37/verification L2-only +40/80` 任一部件；**不测新矩阵/标签/prior/阈值/decoder 参数**，新增即 `EVIDENCE_INVALID`；不重估先验（`V25 channel_counts.npz` 只读）。
- **逐帧对应优先**：`K_aligned=45` 规模使 `COMPETITIVE` 的 `-2/45` 容差与 `per-source -1/15` 可机械判定；预算 `90-180` 硬帽180；每源块数平衡，之后禁换块。
- **通过后的 claim 边界**：即使 `V62_COMPETITIVE`，仍仅为**开发基准在冻结 45 块上的配对对比证据**（绑定 Polar `commit/version` 与 NB-LDPC `H provenance` + `paired registry`），不等同全域 FER/阈值/SKR/资格/晋升/安全证明；报告显式标注 Polar 来源与处理点 `84d62779`，声明 `POLAR_REFERENCE_PROXY` 仅参考。

## 2. 冻结语义 — V54 方法与 Polar 参考零改

### 2.1 固定不变项（NB-LDPC 冻结，零改，V54 complete）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 symbols/block (`4×256 frames`) | V31/V54 |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` `v35_algorithm_development` |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop` | V43/V52 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` `load_v25_channel_counts()` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | `m1=16`, tag 64b L2-only |
| 泄漏 stage1 | `leak_stage1=5*(m2+8)+80+64 → 1104/1134/1144 (+40)` | `Δm=8` det1 |
| 泄漏 stage2 | `leak_stage2=5*(m2+16)+80+64 → 1144/1174/1184 (+80)` | `Δm=8` det2, `H_total 200/206/208` |
| H_inc1/H_joint1 | `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` `8×1024` det1 + `h_joint1 192/198/200×1024` nested | V52 冻结 |
| H_inc2/H_total | `h_inc_1M_det2 / h_inc_1p5M_det2 / h_inc_2M_det2` `8×1024` det2 + `h_total 200/206/208×1024` nested | V54 冻结 |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64, `syndrome_ok && tag_ok` 双条件 | V35 |
| Prior | `TRAIN-only` via `load_v25_channel_counts()`，comparison blocks 来自冻结 held-out (非 TRAIN) | V25 |
| Rescue触发 | `verification-only`：仅未通过 `verify` 才进入下一阶段 | V52/V53/V54 |
| Δm | `8+8=16` per source, `leak_stage1-leak_base=40` `leak_stage2-leak_stage1=40` | V54 |

- `exact_full = array_equal(x_hat, u2_true)` oracle；`exact_u1/exact_l2` 分别报告；`exact` 仅统计不触发增量。
- 相同 `bob`/`prior`/`P_i(U2)` 在 `base vs stage1 vs final` 间共享；仅 `H_L2/syndrome` 不同。
- **V62 禁止任何新矩阵/标签/prior/阈值/decoder 参数变更**，违者 `EVIDENCE_INVALID`；`V61/V60` 数值不继续。

### 2.2 Polar reference 只读语义（POLAR_REFERENCE_PROXY，不升级）

| 提取项 | 机械来源 `file/function/key` | 语义 |
|---|---|---|
| Polar 版本/commit/provenance | `D:\Code\HD-QKD_Polar_Release` 的 `git rev-parse HEAD` + `experiments/run_real_polar_max_pie.py` 版本 + `polar_existing_bridge.py:resolve_polar_output_from_metadata` 的 `source_path` | 只读，不改 Polar Release |
| 结果文件选择 | `polar_existing_bridge.py:locate_existing_polar_outputs` + `select_polar_output` + `_score_candidate` (对 `polar_diag_summary.csv / polar_e2e_results_refresh.csv` 等打分) | 机械择优，不手选 |
| 列提取 | `benchmark_rows_from_polar_output` + `_read_csv_header/_load_companion_supplements/_ci_float/_first_float/_first_value/_first_int` + `metrics/leakage.py:compute_beta_eff_empirical` | 逐列 `file:line:expr` 可重现 |
| 逐行关键 keys | `dataset_id, loss_db, dimension, bin_width_ps, n_eff_pairs, frame_len_symbols, processing_rule_version, pairing_path_tag, threshold_ps, effective_pairing_window_ps, raw_ser, raw_ber, leak_EC_actual_bits, leak_EC_per_frame, leak_EC_per_input_bit, beta_eff_empirical, runtime_s, throughput_input/output, n_frames_total/success/failed_decode/failed_verify, accepted_frame_fraction, status/sidecar_verdict` | 见 `benchmark_rows_from_polar_output` 行 `rows.append({...})` |
| verification | `sidecar_verdict/status` + `n_frames_failed_verify` + `post_ir_ser/ber` | Polar 既有 `verify` 口径，标记 `POLAR_REFERENCE_PROXY` |
| PIE/SKR | 若 Polar 输出含 `pie/skr/finite-key` 列则机械提取，否则 `missing` 并标记 `POLAR_REFERENCE_PROXY` 不自创 | 禁止 hand-fill，缺则 `null` |
| 伴随文件 | `_companion_paths` + `_load_companion_supplements` 的 `checked_files/by_key/missing_after_companion_scan` | `source_missing_fields` 与 `missing_after_companion_scan` 显式记录 |

- `beta_eff_empirical` 必须由 `leak_EC_actual_bits / n_bits / raw_ber` 派生（`leakage.py`），永不手填。
- `finite-key/PIE/SKR` 仅 `POLAR_REFERENCE_PROXY`，不升级为 `composable`，不与 NB-LDPC 的 `V61 ell` 混同。
- 相同 `polar_existing` 输入上 `benchmark_rows_from_polar_output` 的幂等性由探针校验（两次调用行数/关键列相等）。

### 2.3 数据裁决（对齐门，V55 domain-incompatible 排除）

- **V55 intake 不兼容域**：`comparison_bench/outputs_comparison/v55_intake_20260828` 的 `sidecars/pairs` 为 `256/frame` 非 `1024-block legacy_v1` 且 `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative`，与本比较要求的 `pairing nearest legacy_v1 / 1024-block / A1/B5` 非同域，**禁止纳入 V62 比较集**（探针显式 `rg` 校验 `V55_domain_incompatible`）。
- **可重放判定**：`pairs.parquet` 或 `sidecar a_eff.npy+b_eff.npy` 经 `load_pairs_table→normalize_pair_columns→build_frame_batch (q=1024, frame_len=1024)` 可无损恢复 `alice_symbol/bob_symbol ∈ [0,1024)` 且 `n_complete == n_rows//1024 ≥15` per source 且 `rows_used==n_keep` 无尾帧残留，`hash(alice||bob)` 逐块比对 Polar 侧与 NB-LDPC 侧完全相等。
- **未对齐停止**：若 `K_aligned<45` 或 per source `<15` 或 `pairing_mismatch` 或 `dimension/bw` 不一致或 `V55_domain_incompatible`，则 `overall = V62_COMPARISON_DATA_NOT_ALIGNED` 停止，不伪造。

### 2.4 合格比较样本（paired 45-block，冻结）

- **目标运行域声明（冻结）**：`D_target = { stratum_1M, stratum_1p5M, stratum_2M }`，处理点 `dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1` (**单点**，`84d62779`)，`source` 三源各一 held-out 区间（与 `V55 intake` 不同，与 `V48-V54` 已用区间零重叠可校验）。
- **处理点**：`d=1024 bw=200 pairing=nearest rule=legacy_v1` (84d62779)，单点。
- **Provenance**：每源 `pairs` 来源 `source_path` + `sha256/size/mtime` + `Polar commit/version` + `NB-LDPC H provenance (H1/Lane C/H_inc1/H_inc2)` 双侧绑定。
- **结构**：每块 `1024 symbols` (`4×256 frames` 连续)，`frame_id` 排序连续无缺失，`0..1023` 范围，`BLOCK_LENGTH=1024`。
- **主样本 (paired authoritative)**：`S=3, B=15` 共 `45` blocks，若 Polar 侧超集 `K_polar ≥45` 则 `index_j=floor(j*(K-1)/14) j=0..14` 分散选 `15/source`，否则取全部 aligned 并判 `V62_COMPARISON_DATA_NOT_ALIGNED`；`v62_paired_registry.json` 为唯一合法配对比。
- **标识**：`block_id, source, Polar frame_ids[4]=NB-LDPC frame_ids[4] (identical), held_out_ordinal_start/end, pairs_count=1024, BLOCK_LENGTH=1024, sampling_mode=paired_polar_nbldpc_v62_development, Polar source_path+commit, NB-LDPC matrix_ids`，**禁换块/禁重采样** (自 registry authoritative 起)。

### 2.5 二阶段协议（条件 HARQ，verification-only，冻结，等待授权执行）

```
per paired block (45 blocks, 15/source):
  prior = TRAIN prior (shared, V25)  // 不重估
  Polar:  reuse existing success/failed_* / leak/runtime/verify (no decode)
  NB-LDPC:
    H1 s1 via true u1, L1 decode → BP → q → P(U2)  // 45 次总计，per block 1 (L1)
    base: decode_L2(H_base, P(U2), s_base) → verify_base = syndrome_ok && tag_ok ; exact_base
    if verify_base:  final_exact = exact_base, leak = leak_base (=1064/1094/1104), stage=base, used_inc1=False, used_inc2=False
    else:
      s_inc1 = H_inc1 * u2_true ; s_joint1=[s_base; s_inc1]
      stage1: decode_L2(H_joint1, P(U2), s_joint1) → verify_stage1 ; exact_stage1
      if verify_stage1: final_exact = exact_stage1, leak = leak_stage1 (=1104/1134/1144), used_inc1=True, used_inc2=False
      else:
        s_inc2 = H_inc2 * u2_true ; s_total=[s_base; s_inc1; s_inc2]
        stage2: decode_L2(H_total, P(U2), s_total) → verify_stage2 ; exact_stage2
        final_exact = exact_stage2, leak = leak_stage2 (=1144/1174/1184) 无论成功/失败, used_inc1=True, used_inc2=True
  // exact_* 仅 oracle 统计，触发仅 verification; base/stage1 仅分层报告，主判 base→Δ16 (final) vs Polar
  // 每块 L1 1 + base L2 1 + 条件 stage1 ≤1 + 条件 stage2 ≤1；45 块总 L1 45+base45+stage1≤45+stage2≤45=90-180 硬帽180，L2 45-135
```

- `exact_*` oracle；`tag_ok` 真实 L2-only 哈希；公开成功以 `tag_ok` 判，`exact` 仅作 oracle 统计但报告两者。
- **预算冻结**：`45 块` 时 `L1 45+base45+stage1≤45+stage2≤45=90-180 硬帽180，L2 45-135`，`base` 兼 old 不重复。

## 3. 指标冻结（主/次分层，undetected 隔离）

### 3.1 主指标（门禁与价值判定，per-source 分层，R62-03 严格）

> **R62-03 严格 Polar 1024-block**：每冻结块 `Polar_block_verified_accept = 4 连续 256-frames 全部 success 且全部 verification pass ?1:0`；`Polar_block_leak=Σ4帧 disclosure`，`Polar_block_runtime=Σ4帧 runtime`；`Polar_block_exact` 仅当 Polar 含逐帧 exact truth 时聚合否则 `null`，禁止由 `accepted_frame_fraction` / aggregate FER 推导；缺逐帧 `ID/success/verification/leak/runtime` 任一 → `V62_COMPARISON_DATA_NOT_ALIGNED` 立即停止。禁止 `round(aggregate*45)`、aggregate FER 造 per-block、`accepted vs exact` 直比。

| 指标 | 定义 | 分层 | 门禁 |
|---|---|---|---|
| `Polar_block_verified_accept` / `NB verify_final` 主比较 | `Polar: 4帧全 success&&verify ?1:0` per block；`NB: verify_final = syndrome_ok&&tag_ok` per block；`overall 45` 与 `per-source 15` 计数 `rate=count/45 或 /15` | overall + per source | `COMPETITIVE` 需 `NB verify_final ≥ Polar -2 (overall) 且 per-source ≥ Polar per-source -1 且 NB undetected==0` |
| `NB exact_full` oracle audit | `exact_full = exact_u1 && exact_l2` 仅统计，不作主门禁；两侧均有逐帧 exact truth 时附加 paired 审计，否则不得用 accepted 代 exact | per source + overall | 仅审计（`exact==verify` 禁假定） |
| `verify` 分别计数 | `verify_base / verify_stage1 / verify_final` 与 `Polar_block_verified_accept` 分别计数 | per stage per source | 完整性校验 |
| `undetected` | `syndrome_ok&&tag_ok && !exact_full` | 全局单独表 | `undetected==0` 全局，否则 `EVIDENCE_INVALID` 优先 |
| `disclosure bits/block` | `Polar: Σ4帧 leak`；`NB: leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184` 三档 + `per_source_avg[s]=leak_base[s]+40*N_stage1[s]/15+40*N_stage2[s]/15` + `overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/45` + `per accepted = total_disclosed_bits / NB_verify_final_count (为0则null)` | per source + overall | 仅报告，不硬门禁，但需语义一致性校验 |
| `calls/rescue` | `N_stage1_attempted=count(!verify_base)`, `N_stage2_attempted=count(!verify_base&&!verify_stage1)`, `rescued_stage1 = count(verify_stage1&&exact_stage1&&!verify_base)`, `rescued_stage2 = count(verify_stage2&&exact_stage2&&!verify_after_stage1)`, `rescue_rate = rescued/attempted` (禁 `45-base_exact` 分母) | per source + overall | 仅报告 |
| `runtime/throughput` | `Polar: Σ4帧 runtime_s` per block + overall；`NB: runtime_s per block + overall`；`throughput_input_bits_per_s = n_bits/runtime` (Polar 用 `Σ4帧`) | per source + overall | 仅报告，需可复现 |
| `paired delta` | `per block NB-LDPC final vs Polar_block_verified_accept` 的 `verify delta, leak delta (=NB leak - Σ4帧 leak), runtime delta` 明细 | per block | 诊断 |
| `Wilson 95%` | `overall 45 与 per-source 15` 的 Wilson 下界按 `verify`（主）与 `exact`（审计）分别报告 | per source + overall | 仅报告，不作门禁 |

- 四类 `exact/detected/decoder_non_syndrome/undetected` 需分别计数；`undetected` 永不并入 `success/FER`。
- 任意 `rank/nested/verification/记账` 失败 → `EVIDENCE_INVALID` 优先。

### 3.2 次级（仅排序，POLAR_REFERENCE_PROXY）

- 用 Polar 同一 `shadow` 参数（`benchmark_rows_from_polar_output` 的 `leak_EC_actual_bits, raw_ber, beta_eff_empirical`）计算 `PIE proxy = beta_eff_empirical * H_binary_shannon(raw_ber)` 与 `SKR proxy = accepted_frame_fraction * (PIE - leak_per_frame)` 类 `shadow`，三源独立，仅排序，不作门禁。
- 报告显式标注 `POLAR_REFERENCE_PROXY`，不升级为 `composable`，不与 `V61 ell` 混同。
- 禁止：泄漏分解语义不一致时跨方法 PIe/SKR 排序（`leak_EC_actual_bits` 的 `tag` 与 `leak_other` 需显式校验一致）。

### 3.3 预注册统计（分层，paired）

- 同块配对的 NB-LDPC `final` vs `Polar` 差异为诊断量，永不作完整性失败。
- `McNemar / binomial paired` 的 `p` 值可作为 `COMPETITIVE` 的补充描述（`p>0.05` 视为不劣），但**不替代** `-2/-1` 容差硬门禁。

## 4. 数据就绪门（decoder-free，G1-G5 分层，alignment spike）

| 门 | 检查项 | 探针判定 |
|---|---|---|
| G1 | Polar 文件可读且机械提取通过 | `locate_existing_polar_outputs` 非空且 `select_polar_output` 非 None 且 `benchmark_rows_from_polar_output` 非空且 `source_missing_fields` 与 `missing_after_companion_scan` 已记录 |
| G2 | Polar provenance 完整 | `source_path + commit/version + processing_rule_version + pairing_path_tag + threshold_ps/bw/dimension` 每行齐全 |
| G3 | 各 stratum 明确且 1024-block | `dimension==1024, bin_width 200ps, pairing nearest legacy_v1, frame_len_symbols 1024, pairs_count 1024` per block |
| G4 | NB-LDPC 可重放 | `load_pairs_table→normalize_pair_columns→build_frame_batch (q=1024, frame_len=1024)` 对同一 `source_path` 可恢复 `alice/bob` 且 `hash` 相等 |
| G5 | 排除 V55 domain-incompatible | `pairing_mode != nearest` 或 `frames×256` 非 `1024-block` 时判 `V55_domain_incompatible` 排除 |

- 三源全 PASS 且 `K_aligned ≥45` 且 `per-source ≥15` ⇒ `ALIGNMENT_READY`，可冻结 `v62_paired_registry.json`；否则 `V62_COMPARISON_DATA_NOT_ALIGNED` 停止。
- 本轮探针 `workspace/v62_alignment_spike/` 执行 `G1-G5` decoder-free分支，零 `decode_*` 调用（`rg "decode_" 0 hits`）。

## 5. 预算（已冻结，90-180 硬帽180，paired 45-block）

- `L1 45` 固定（每块 1 次 `H1→BP→P(U2)`，共享于三阶段）
- `base L2 45` 固定（每块 1 次 `H_base`）
- `stage1 L2 0–45` 条件（仅 `!verify_base` 者）
- `stage2 L2 0–45` 条件（仅 `!verify_base && !verify_stage1` 者）
- 总 `45+45+0–45+0–45 =90-180 硬帽180，L2 45-135`，`per block 2-4 calls`

## 6. 门禁与五终态（已冻结，COMPETITIVE 容差，R62-03 严格）

对 `45-block` paired 开发基准判定 (15/source，R62-03 严格 per-block)：

- **计数（R62-03 禁 round/aggregate 拼块）**：`Polar_block_verified_accept` 按 `4 consecutive 256-frames 全部 success 且全部 verify ?1:0` 逐块求和得 `overall/ per-source (45/15)`，`Polar_block_leak=Σ4帧`，`Polar_block_runtime=Σ4帧`，`Polar_block_exact` 仅当逐帧 exact truth 齐全时聚合否则 `null`；**禁止** `round(accepted_frame_fraction*45)`、`aggregate FER 造 per-block`、`accepted vs exact 直比`；缺逐帧 `ID/success/verification/leak/runtime` 任一 → `V62_COMPARISON_DATA_NOT_ALIGNED` 立即停止。`NB-LDPC verify_final` 与 `exact_full` 分别计数；`undetected` 单独表。
- **分层**：各源各自 `NB-LDPC base/stage1/final/rescued_stage1/rescued_stage2 (verify_final vs exact_full 分别)` 与 `Polar per-source verified_accept` 及 `leakage/rescue_rate/runtime` 分别报告；`base/stage1` 仅分层报告不作主判；`NB exact_full` 仅 oracle audit。
- **泄漏**：Polar `Σ4帧 leak` vs NB 三档 `leak_base/stage1/stage2` 分布 + `per_source_avg` + `overall_avg` + `per accepted (=total_disclosed / verify_final)` + `Wilson 95%` per source & overall 的描述性；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance。
- **预注册五终态（冻结，paired 45-block，first-match，R62-03）**：

```
if not polar_reference_mechanically_extracted or not alignment_metadata_complete or rank/nested/verification/记账失败:
    V62 = EVIDENCE_INVALID  # 优先
elif not polar_per_frame_complete (缺逐帧 ID/success/verification/leak/runtime 任一):
    V62 = COMPARISON_DATA_NOT_ALIGNED  # 立即停止，禁止 round/aggregate 拼 45 块
elif not alignment_possible (K_aligned<45 or per_source<15 or V55_domain_incompatible or pairing_mismatch or not replayable):
    V62 = COMPARISON_DATA_NOT_ALIGNED  # 停止，不进 decoder
elif nbldpc_not_yet_executed (本轮):
    V62 = PLAN_CANDIDATE__ALIGNMENT_SPIKE_DONE  # 仅 plan + spike
# 未来执行后（需 alignment PASS + 独立 plan ACCEPT + EXECUTE_AUTH）再判（主门禁为 verified_accept）：
# elif nbldpc_overall_verify >= polar_overall_verified_accept -2  ∧ per_source nbldpc_verify >= polar per_source -1  ∧ nb_undetected==0  ∧ rank/nested/verification/记账通过
#      ∧ (若两侧均有逐帧 exact truth 则附加 exact paired 审计否则跳过)
#        → V62_COMPETITIVE
# elif nbldpc_has_signal (any exact>0 or rescued>0 or residual improved) but not COMPETITIVE → V62_CORRECTION_WORKS_BUT_NOT_COMPETITIVE
# else → V62_NO_RETAINED_SIGNAL
```

- **COMPETITIVE 容差冻结（R62-03）**：`overall NB verify_final ≥ Polar_block_verified_accept -2` (容差 2/45) 且 `per-source NB verify_final ≥ Polar per-source -1` (容差 1/15) 且 `NB undetected==0` 且 `rank/nested/verification/记账` 通过；若两侧均有逐帧 `exact` truth 再附加 `exact` paired 审计，否则**不得用 accepted/exact 直比**；`disclosure/PIE proxy` 仅报告不作硬门禁，但需语义一致性校验通过。
- `Wilson 95%`/`rescue_rate`/`runtime`/`PIE proxy` 仅报告，不作门禁；`exact` 仅审计。

## 7. O3 配对语义与预注册统计（分层，paired）

- 同源同 `block` 的 paired 样本 `(frame_ids[4], alice, bob)` 每块确定性一次（Polar 复用与 NB-LDPC 同 `frame_ids`），`L1` 单次生成 `q_i` 与 `P_i(U2)`，`base` → `stage1`（仅 `!verify_base`）→ `stage2`（仅 `!verify_after_stage1`）条件递进，同 `bob`/`P_i(U2)`/`s` 的嵌套前缀，`exact` 仅 oracle 统计。
- 跨块 `Polar vs NB-LDPC` outcome 差异为诊断量，永不作完整性失败。
- `PIE/SKR proxy` 的 `shadow` 参数需与 Polar 侧完全一致（`beta_eff_empirical` 的 `leak/n_bits/raw_ber` 同源），否则该次对比的次级排序失效。

## 8. 科学 preflight、守卫序、执行偏差防复发（已冻结，未来执行前）

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `6a3b873e` + data SHA `84d62779`）；四文件 SCOPED dirty（含 `v62` 模块、`v62` CLI、`v38`、`v35`、`polar_existing_bridge`）；G1-G5 未过即拒（当前探针已 PASS 才可）；输出根已存在即拒；任一拒绝零 calls 不建文件。
2. **科学 preflights（decoder-free, write-free，未来执行前）**：G1-G5 全检 + `H_base` 三矩阵与 committed v38 常量 `rank/support` 比对 + `H_inc1/H_inc2` 确定性重建与 `rank_total==m2+16 / nested / independence==8 / row≤16 / col≤1 / E≈96 / leak+40+40` 校验 + TRAIN counts 形态校验 + paired `frame_ids/ordinal` 每源 `15` 块分散校验 + 每源首块哨兵 `L1→P_i(U2)` 通路 + `Polar vs NB-LDPC` `alice/bob hash` 抽检相等。
3. **执行偏差防复发（冻结）**：
   - 不使用 600s 外部 timeout；建议 `--timeout` 至少 `3600s` 或不设外部 timeout（decoder 内部 `90/1.0` 早停已限时）
   - 若执行返回 `session/cell ID`，只轮询同一 `session/cell ID` 进程状态，禁止 `restart`/`recreate` 新 session
   - 中断保留 raw partial 不聚合、不自动重跑
4. **Preflight 失败** → 写 `v62_invalid_notice.json` + 空 records + `v62_summary.json` (terminal `V62_EVIDENCE_INVALID` 或 `V62_COMPARISON_DATA_NOT_ALIGNED` 分层) 后零 decoder calls 停止。
5. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前。

## 9. 记录、聚合、summary（预冻结，未来执行，paired 分层）

每 L2 call record schema（含 `tag_scope=l2_only, arm∈{base,stage1,stage2}, source, Polar counterpart`）：

```
call_id, source(1M/1p5M/2M), block_id, arm(base/stage1/stage2), pass_index(1/2/3), used_inc1(bool), used_inc2(bool),
matrix_id(base/joint1/total), h1_matrix_id, frame_ids[4] (identical Polar/NB-LDPC), held_out_ordinal_start/end, pairs_count 1024, sampling_mode(paired),
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or 1104/1134/1144 or 1144/1174/1184), leak_stage1, leak_stage2, status, runtime_s,
Polar: polar_source_path, polar_commit, polar_n_frames_success, polar_leak_EC_actual_bits, polar_runtime_s, polar_beta_eff_empirical, polar_verification, polar_pie_proxy, polar_skr_proxy
```

Summary 含：Polar `overall/per-source success/FER, leak, runtime, verification, beta_eff_empirical`；NB-LDPC `base/stage1/final exact_full` 与 `verify` 分别计数（per source & overall）、`rescued_stage1/stage2`、`N_stage1_attempted/N_stage2_attempted`（per source & overall）、`rescue_rate_stage1/stage2` per source、`per_source_avg` 与 `overall_avg` 与 `per accepted`、`Wilson 95%` per source & overall、`total_disclosed_bits`；`Δleak_per_source`，`Δleak_overall`；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance；L1 诊断；四类计数；`undetected==0`；门禁明细（`final` 的 per-source 容差与 overall 容差数值与 `V62_*` 终态）；`PIE/SKR proxy` 仅排序；paired `Polar vs NB-LDPC final` per block 描述性；`Polar provenance` 完整 `file/function/key`。

## 10. 证据写出（预冻结，未来执行，不在本轮）

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v62_nbldpc_polar_benchmark/run_01/
```

文件：`v62_records.json/.csv` (45 块对应 `45-135` L2行：`45 base + ≤45 stage1 + ≤45 stage2`；总 calls `90-180` 硬帽180)、`v62_summary.json`（分层，含 Polar vs NB-LDPC 对比）、`v62_paired_registry.json` (45-block authoritative paired)、`v62_polar_reference.json` (Polar 机械提取 provenance)、`v62_invalid_notice.json`（失败时）、`v62_data_readiness.json`（G1-G5）。CSV/JSON 行对等；禁写 NPZ. **本轮 P0 不创建上述输出**，仅在 `docs/research_cycles/V62P0/v62_alignment_spike_report.json` + `v62_polar_reference.json` 紧凑记录 G1-G5 与 paired 冻结。

## 11. 实现草图（后继轮次，当前未授权，需 alignment PASS + 独立 plan ACCEPT + EXECUTE_AUTH）

- `comparison_bench/src/comparison_bench/formal_ir/v62_nbldpc_polar_benchmark.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现确定性 `H_inc1 det1` 复用 + `H_inc2 det2` 新增 + paired `45-block` 冻结 (per source `15` 块分散，frame_ids 已冻，with Polar 同输入) + 二阶段条件 runner (per block `base 1+条件 stage1 ≤1+条件 stage2 ≤1`，总 `90-180` 硬帽180，分层预算) + Polar 复用分支（零 decoder）。
- `scripts/execute_v62_benchmark.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan `6a3b873e` + data SHA `84d62779` + paired registry `hash`）；四文件 SCOPED dirty；G1-G5 全 PASS 已验；budget 硬帽 `45` 块二阶段条件执行 90-180；执行偏差防复发；任一 gate 失败非零退出。
- 仅 fake-runner 测试通过后才可进入正式配对基准；不以 outcomes 定增量或调 `Δm`；不改 Polar Release。

## 12. 自由裁量 D1–D8（修订至 PLAN_CANDIDATE）

- D1 完全冻结 V54 方法（H1/L1-APP/Lane C/H_inc1/H_inc2/decoder/prior/verification 零改），V62 不新增矩阵/标签/prior/阈值。
- D2 单一二阶段 `Δm=8+8` per source 嵌套 rescue，`45-block` `base vs stage1 vs final` 三阶段配对 vs Polar `final`（未来执行，分层 paired）。
- D3 Polar reference 只读机械提取，`POLAR_REFERENCE_PROXY` 不升级，`beta_eff_empirical` 派生。
- D4 paired `45-block` 注册算法：每源 `15` 块，若 Polar 超集更大则 `index_j=floor(j*(K-1)/14)` 分散，否则判 `V62_COMPARISON_DATA_NOT_ALIGNED`，frame_ids 已冻，禁换块。
- D5 预算 `90-180` 硬帽180 (`45+45+≤45+≤45`)，`L2 45-135`，`base` 兼 old 不重复。
- D6 预注册五终态：`EVIDENCE_INVALID > COMPARISON_DATA_NOT_ALIGNED > COMPETITIVE > CORRECTION_WORKS_BUT_NOT_COMPETITIVE > NO_RETAINED_SIGNAL`，`COMPETITIVE` 需 `overall -2 且 per-source -1 且 undetected==0`。
- D7 哨兵每源首块单 L1 通路（未来执行）+ `hash` 抽检 `alice/bob` 相等。
- D8 本轮仅交付四工件+对齐探针脚本/报告，`45-block` 配对开发基准规模，未来执行仍仅开发基准证据，不扩大为 qualification。

