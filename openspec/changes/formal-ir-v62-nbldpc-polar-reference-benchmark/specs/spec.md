# OpenSpec Spec: formal-ir-v62-nbldpc-polar-reference-benchmark

**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 仅 plan + alignment spike，未对齐前禁止 decoder 实现/执行
**Change**: `formal-ir-v62-nbldpc-polar-reference-benchmark` (`V62P0`, branch `formal-ir-mainline`, HEAD `6a3b873e`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (`efd34ef318...`, V55 二阶段 `Δ8+Δ8` 性能候选) + `formal-ir-v61` (`7b476f62...`) 仅参考

## 1. 变更类型与生命周期

- **Type**: `DEVELOPMENT_BENCHMARK` — `Polar reference` 对比开发基准（paired 45-block, 90-180 calls 硬帽180），非 formal qualification/promotion/安全证明。
- **Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free 对齐探针 (`rg "decode_" 0 hits`)，未对齐 `V62_COMPARISON_DATA_NOT_ALIGNED` 前禁止任何 decoder 实现/执行与正式 `run_01` 创建。
- **Branch**: `formal-ir-mainline`；`HEAD` `6a3b873e` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞；本次推送新 Plan SHA 后停止。
- **Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200 pairing=nearest rule=legacy_v1`) — 仅 NB-LDPC 侧锚点；Polar 侧实际处理点以 Phase A 机械提取为准，Phase B 逐块 `pairing/dimension/bw` 一致性校验。

## 2. 冻结方法（NB-LDPC 完全冻结）

### 2.1 不变量

- `n =1024 symbols/block` (`4×256 frames`), `q =1024 (GF32 symbols 0..1023)`, `log2 q =5`, `GF32 poly=37 (0b100101)`, `tag =64 bits/block L2-only 仅 total 计一次`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`L1-APP`: `p_i(u1)=P(U1|B_i) → BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs → q_i=softmax(BP_i) → P_i(U2)=Σ q_i P(U2|B,u1)` (TRAIN prior `channel_counts.npz` via `load_v25_channel_counts()` 只读，不重估)。
- `Lane C` ordinal-2 `s38310x`：`m2 =184 (1M) /190 (1p5M) /192 (2M)`，`support/标签/置换/MET图` 全冻。
- `H_inc1 8×1024 det1` + `H_joint1 192/198/200×1024` nested；`H_inc2 8×1024 det2` + `H_total 200/206/208×1024` nested；`rank_joint1==m2+8`, `rank_total==m2+16`, `independence_1==8`, `independence_2==8`, `row≤16`, `col_inc≤1`, `E≈96`。
- `decoder`: `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop`；`verification`: `tag_scope=l2_only compute_tag_64(empty_uint8,x2) trunc64` + `syndrome_ok && tag_ok` 双条件；`rescue 触发 = verification-only`。
- `leak`: `leak_base=5*m2+5*16+64 →1064/1094/1104`, `leak_stage1=leak_base+40 →1104/1134/1144`, `leak_stage2=leak_base+80 →1144/1174/1184` (`tag` 已含，不重复扣除)。
- `prior = TRAIN-only`，evaluation blocks 来自冻结 paired held-out (非 TRAIN)。

### 2.2 禁止

- 禁改任一冻结量、新增矩阵/标签/`prior`/阈值/`decoder`、试 `Δm=4/12/16` 多档、引入第二候选择优、用 outcomes 选行、调 `row_degree` 上限；违者 `EVIDENCE_INVALID`。
- 禁改 `D:\Code\HD-QKD_Polar_Release` 任何文件（只读提取）；禁重跑 Polar decoder；禁把 `POLAR_REFERENCE_PROXY` 升级为 composable。
- 禁重估先验、禁用 V55 `domain-incompatible` 输入（`256/frame` 非 `1024-block legacy_v1`）。
- 探针脚本中禁 `decode_* / construct_* / import decoder` (`rg "decode_" 0 hits`, `py_compile PASS`)，未创建 `run_01`。

## 3. Phase A — Polar reference 只读机械提取（POLAR_REFERENCE_PROXY）

### 3.1 提取入口

- `comparison_bench/src/comparison_bench/io/polar_existing_bridge.py`:
  - `locate_existing_polar_outputs(search_roots: list[Path]|None) -> list[Path]` (对 `repo_root()/results`, `comparison_bench/outputs_comparison`, `DEFAULT_POLAR_RESULTS_ROOT` 的 `rglob("*.csv")` 按 `POLAR_OUTPUT_NAMES` + 通用 `polar/e2e/diag/results` 匹配)
  - `select_polar_output(candidates: list[Path]) -> Path|None` (按 `_score_candidate` 的 `PREFERRED_OUTPUT_ORDER + raw_ser/leak/status/PASS` 打分择优)
  - `benchmark_rows_from_polar_output(path: Path, dataset_id: str|None) -> pd.DataFrame` (逐行 `rows.append({...})` 含全部 §2.2 keys)
  - `_read_csv_header, _load_companion_supplements, _companion_paths, _score_candidate, _first_float/_first_value/_first_int, _ci_float` 均为机械提取子函数。
- `comparison_bench/src/comparison_bench/metrics/leakage.py:compute_beta_eff_empirical(leak, n_bits, raw_ber) -> float` 为 `beta_eff_empirical` 唯一派生入口。

### 3.2 逐项记录（file/function/key，零手填）

每项 Polar 提取记录 `symbol, meaning, unit, source(file:line:expr or data_path:provenance), authority=POLAR_REFERENCE_PROXY, readiness=reference`：

| 符号 | 含义 | 单位 | 来源 `file/function/key` |
|---|---|---|---|
| `polar_commit/polar_version` | Polar Release 版本/commit | — | `D:\Code\HD-QKD_Polar_Release: git rev-parse HEAD / git log -1 --oneline / experiments/run_real_polar_max_pie.py:__version__` |
| `polar_source_path` | 择优结果文件路径 | path | `polar_existing_bridge.py:resolve_polar_output_from_metadata / select_polar_output` |
| `processing_rule_version` | 处理规则版本 | — | `benchmark_rows_from_polar_output: _first_value(row, ["processing_rule_version"])` |
| `pairing_path_tag` | 配对路径标签 | — | `benchmark_rows_from_polar_output: _first_value(row, ["pairing_path_tag"])` |
| `threshold_ps/effective_pairing_window_ps` | 配对阈值/窗口 | ps | `benchmark_rows_from_polar_output: _first_value(row, ["threshold_ps"])` |
| `dimension` | 符号维度 | — | `benchmark_rows_from_polar_output: _first_int(row, ["dimension"])`, 必须 `1024` 才可对齐 |
| `bin_width_ps` | bin 宽度 | ps | `benchmark_rows_from_polar_output: _first_value(row, ["bin_width_ps"])`, 必须 `200` |
| `n_eff_pairs/n_pairs_actual` | 有效对数 | count | `benchmark_rows_from_polar_output: _first_float(row, ["n_eff_pairs","n_pairs_actual"])` |
| `frame_len_symbols` | 块长 | symbols | `benchmark_rows_from_polar_output: _first_int(row, ["frame_len_symbols",...])`, 必须 `1024` |
| `n_frames_total/success/failed_decode/failed_verify` | 帧计数 | count | `benchmark_rows_from_polar_output: _first_int/... + supp_float("n_frames_success") + companion by_key` |
| `accepted_frame_fraction` | 接受率 | 无量纲 | `n_success/n_frames_total` |
| `raw_ser/raw_ber` | 原始 SER/BER | 无量纲 | `_first_float(row, ["raw_ser","map_ser"])` / `bit_error_rate` 派生 |
| `leak_EC_actual_bits` | EC 泄漏 | bits | `_ci_float(row, "leak_EC_actual_bits")` + `supplement["leak_EC_actual_bits"]` |
| `beta_eff_empirical` | 经验效率 | 无量纲 | `compute_beta_eff_empirical(leak, n_bits, raw_ber)` ( `leakage.py` ) |
| `runtime_s/throughput` | 运行时长/吞吐 | s / bits/s | `_ci_float(row, "runtime_s")` + `n_bits/runtime` 派生 |
| `verification` | 验证口径 | — | `status/sidecar_verdict, n_frames_failed_verify, post_ir_ser/ber` |
| `PIE/SKR formula` | PIE/SKR 参考公式 | bits | `rg "pie|skr|finite.key" D:\Code\HD-QKD_Polar_Release --type py/csv -n` 的 `file:line:expr`，无则 `missing` 标 `POLAR_REFERENCE_PROXY` |

- `source_missing_fields` 与 `missing_after_companion_scan` 需显式记录（`SUPPLEMENT_FIELDS` 审计）。
- `beta_eff_empirical` 永不 hand-fill，`pie/skr/finite-key` 仅 `proxy` 不升级。

## 4. Phase B — 公平比较集冻结（逐帧对应优先，按序 first-match，未对齐停止）

### 4.1 处理点单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, channels A1/B5, frame_len 1024, pairs 1024, BLOCK_LENGTH 1024` — 单点，不泛化。
- 任何 `pairing/dimension/bw` 不一致 → `pairing_mismatch` 判不兼容，不纳入比较集。

### 4.2 可重放性（hash 比对）

- `comparison_bench/src/comparison_bench/io/pairs_loader.py:load_pairs_table(path) -> pd.DataFrame` + `normalize_pair_columns` (`REQUIRED_COLUMNS = frame_id/pair_idx/alice_symbol/bob_symbol`) + `dataset_builder.py:build_frame_batch(df, dataset_id, dimension=1024, frame_len=1024) -> FrameBatch` 必须对同一 `source_path` 可恢复 `alice_symbol/bob_symbol ∈ [0,1024)` 且 `n_complete == n_rows//1024` 且 `rows_used==n_keep`。
- 抽样 `sha256(alice.tobytes()+bob.tobytes())` 逐块比对 Polar 侧与 NB-LDPC 侧完全相等，记录 `hash_equal=true`。

### 4.3 V55 domain-incompatible 排除

- `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` 的 `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` 且 `256/frame` 非 `1024-block legacy_v1` 判 `V55_domain_incompatible=true`，禁止纳入 V62 比较集（探针 `rg "v55"` 显式排除日志）。

### 4.4 对齐判定（first-match）

```
if not polar_reference_mechanically_extracted or not alignment_metadata_complete:
    overall = V62_EVIDENCE_INVALID  # 优先
elif K_aligned<45 or per_source<15 or not replayable or V55_domain_incompatible or pairing_mismatch:
    overall = V62_COMPARISON_DATA_NOT_ALIGNED  # 停止，不伪造
else:
    overall = V62_ALIGNMENT_READY  # 可冻结 paired registry
```

- `K_aligned` 为 Polar 侧与 NB-LDPC 侧符号可重放的 `frame_ids` 完全相等的块数；`per_source` 为每源对齐块数。
- `V62_COMPARISON_DATA_NOT_ALIGNED` 时不创建正式 `v62_paired_registry.json`，报告仅记录缺口，不进 Phase D 执行。

### 4.5 Paired registry（若 ALIGNMENT_READY）

- `docs/research_cycles/V62P0/v62_paired_registry.json` (authoritative): `S=3, B=15, total 45`, 每块 `block_id, source(1M/1p5M/2M), Polar frame_ids[4]==NB-LDPC frame_ids[4] (identical), held_out_ordinal_start/end, pairs_count=1024, BLOCK_LENGTH=1024, sampling_mode=paired_polar_nbldpc_v62_development, Polar source_path+commit, NB-LDPC matrix_ids (H1/Lane C/H_inc1/H_inc2), hash(alice||bob)`。
- 若 Polar 侧超集 `K_polar>45` 则 `index_j=floor(j*(K-1)/14) j=0..14` 分散选 `15/source`，否则直接取 aligned 45（`K_aligned==45` 才合法）。
- `git diff -- ../HD-QKD_Polar_Release ==0` 已验，registry `禁换块`。

## 5. Phase C — 指标冻结

### 5.1 主指标（门禁与价值判定）

- `exact_full/accepted rate`: `exact_full = exact_u1 && exact_l2` per block 的 `overall 45` 与 `per-source 15` 计数与 `rate = count/45 或 /15`；`Polar_success_45 = round(accepted_frame_fraction*45)`, `per-source = round(frac*15)`。
- `verify` 分别计数：`verify_base, verify_stage1, verify_final` 与 `Polar n_frames_success` 分别计数（禁止 `exact==verify` 假定）。
- `undetected`: `syndrome_ok&&tag_ok && !exact_full` 全局单独表，永不并入 `success/FER`，`undetected>0` 则 `EVIDENCE_INVALID` 优先。
- `disclosure`: `leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184` 三档 (`leak=5*m_total+64` 双校验) + `per_source_avg[s]=leak_base[s]+40*N_stage1[s]/15+40*N_stage2[s]/15` + `overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/45` + `per accepted = total_disclosed_bits / final_exact_full_count (为0则null)`。
- `calls/rescue`: `N_stage1_attempted=count(!verify_base)`, `N_stage2_attempted=count(!verify_base&&!verify_stage1)`, `rescued_stage1 = count(verify_stage1&&exact_stage1&&!verify_base)`, `rescued_stage2 = count(verify_stage2&&exact_stage2&&!verify_after_stage1)`, `rescue_rate = rescued/attempted` (禁 `45-base_exact` 分母)。
- `runtime/throughput`: `runtime_s per block + overall`, `throughput = bits/runtime` (Polar 复用，NB-LDPC 未来实测)。
- `paired delta`: `per block NB-LDPC final vs Polar` 的 `exact/leak/runtime delta` 明细。
- `Wilson 95%` per source & overall 的 `exact/rate` 报告，不作门禁。

### 5.2 次级（仅排序，POLAR_REFERENCE_PROXY）

- `PIE proxy = beta_eff_empirical * H_shannon` 与 `SKR proxy = accepted_frame_fraction * (PIE - leak_per_frame)` 用 Polar 同一 `shadow` 参数（`leak_EC_per_input_bit, raw_ber, beta_eff_empirical`）计算，仅排序，不作门禁。
- 显式 `POLAR_REFERENCE_PROXY`，不升级为 composable，不与 `V61 ell` 混同；泄漏分解语义不一致时次级失效。

## 6. Phase D — 45-block paired 开发基准设计（硬帽180，未对齐前不执行 decoder）

### 6.1 规模

- `S=3, B=15, total 45`, 每块 `1024 symbols (4×256 frames)`；`K_aligned` 中若超集更大则 `index_j=floor(j*(K-1)/14)` 分散选 `15/source`。
- `paired registry` 禁换块，自 authoritative 起。

### 6.2 Polar 复用分支

- 直接复用 `n_frames_success/failed_* / leak/runtime/verify/beta/pie proxy`，不重跑，不新增泄漏，不调参。

### 6.3 NB-LDPC 三阶段协议（硬帽180, verification-only）

```
per paired block (45 blocks):
  prior = TRAIN prior (shared)
  base: H_base(m2) -> verify_base ; if pass leak_base else H_joint1(m2+8) -> verify_stage1 ; if pass leak_stage1 else H_total(m2+16) -> verify_stage2 leak_stage2
budget: L1 45 + base45 + stage1≤45 + stage2≤45 =90-180 硬帽180 (L2 45-135)
comp: exact_full=exact_u1&&exact_l2, verify=syndrome_ok&&tag_ok, tag=L2-only 64b
```

- `rank_total==m2+16 nested/independence==8 row≤16` 已验；`leak_base/stage1/stage2` 三档已验。
- 仅 `alignment PASS + 独立 plan ACCEPT + EXECUTE_AUTH` 后才允许创建正式实现并执行。

### 6.4 五终态（first-match，COMPETITIVE 容差冻结）

```
if not polar_reference_mechanically_extracted or not alignment_metadata_complete or rank/nested/verification/记账失败:
    overall = V62_EVIDENCE_INVALID  # 优先
elif not alignment_possible (K_aligned<45 or per_source<15 or V55_domain_incompatible or pairing_mismatch or not replayable):
    overall = V62_COMPARISON_DATA_NOT_ALIGNED  # 停止，不进 decoder
elif nbldpc_not_yet_executed (本轮):
    overall = V62_PLAN_CANDIDATE__ALIGNMENT_SPIKE_DONE
# 未来执行后:
# elif nbldpc_overall_exact >= polar_overall_success -2  ∧ per_source nbldpc >= polar per_source -1  ∧ undetected==0 ∧ rank/nested/记账通过 → V62_COMPETITIVE
# elif nbldpc_has_signal (any exact>0 or rescued>0 or residual improved) but not COMPETITIVE → V62_CORRECTION_WORKS_BUT_NOT_COMPETITIVE
# else → V62_NO_RETAINED_SIGNAL
```

- `COMPETITIVE`: `overall NB-LDPC exact_full ≥ Polar overall success -2` (容差 2/45) 且 `per-source NB-LDPC exact_full ≥ Polar per-source success -1` (容差 1/15) 且 `undetected==0` 且 `rank/nested/verification/记账` 通过；`disclosure/PIE proxy` 仅报告。
- `CORRECTION_WORKS_BUT_NOT_COMPETITIVE`: `exact>0` 或 `rescued>0` 或 `mean residual improved` 但未达 `COMPETITIVE`。
- `NO_RETAINED_SIGNAL`: `exact==0` 且 `rescued==0` 且无改善信号。
- `EVIDENCE_INVALID` 优先于 `COMPARISON_DATA_NOT_ALIGNED`；`COMPETITIVE` 前需 `ALIGNMENT_READY`。

## 7. 证据写出（预冻结，未来执行）

- 固定增量根（decoder 前建，fail-closed）：`comparison_bench/outputs_comparison/formal_ir_methods/v62_nbldpc_polar_benchmark/run_01/`。
- 文件：`v62_records.json/.csv` (`45-135` L2行)、`v62_summary.json` (分层含 Polar vs NB-LDPC 对比)、`v62_paired_registry.json`, `v62_polar_reference.json`, `v62_invalid_notice.json` (失败时)、`v62_data_readiness.json` (G1-G5)。CSV/JSON 行对等；禁写 NPZ。本轮仅在 `docs/research_cycles/V62P0/` 紧凑记录 `v62_alignment_spike_report.json/.csv` + `v62_polar_reference.json`。

## 8. 与 V55/V61 衔接与守卫

- `V55` 二阶段 `Δ8+Δ8` 为本对比的 NB-LDPC 唯一臂；不改 `V55 authoritative registry` 与终态，不继续 `V55 run_01`。
- `V61` 仅为安全测量规范参考，不改 `V61` 的 `composable:null` 判定；本对比的 `PIE/SKR proxy` 仅 `shadow` 排序，不升级。
- 守卫：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-1]/ ==0 && git diff -- ../HD-QKD_Polar_Release ==0` (除本变更外零改)，`rg "decode_" 0 hits` (探针侧)，`py_compile PASS`，`HEAD==origin (6a3b873e)` 已验，`run_01` 不存在，正式基准未触发已验。

