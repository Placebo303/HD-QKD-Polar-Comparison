# OpenSpec Design: formal-ir-v63-nbldpc-polar-shell-integration

**Lifecycle**: `PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED` — **仅 plan 四工件，未适配前禁止实现/运行 decoder，不改 Polar src，不继续 V61/V60**
**Cycle**: `V63P0`
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (`cb60c5dd48...`) 冻结二阶段 `Δ8+Δ8` NB-LDPC + `formal-ir-v62` 参考对比仅作 proxy 参数来源
**Freeze HEAD**: `fad33f4b935e73972b5be4d02ec7901214fa0046` (branch `formal-ir-mainline`, 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) — **data SHA** `84d62779` (`d=1024 bw=200 pairing=nearest rule=legacy_v1`, 同域单点)
**Feasibility**: V54 二阶段 `H_total 200/206/208 rank m2+16 nested True` 已在 V54 spike 三源实证 43/45 同域可重放；`comparison_bench/io` 的 `load_pairs_table→normalize→build_frame_batch` 对 held-out 可无损恢复 1024 symbols；唯一待验为**壳集成后 IR→PA 的 per-frame 实际泄漏传递与 proxy 产钥贯通**。

## 1. 科学问题与关键判断

> 在**保留 Polar pipeline 外壳**（TTBin→timing/pairing/binning→1024 symbols→参数估计/分层→verification/tag→泄漏统计→PA→key length/PIE/SKR）且**完全冻结 V54 NB-LDPC**（`H1-16+L1-APP+Lane C+Δ8+Δ8, leak 1064→1144/1174 1184`）的前提下，**将 IR 模块替换为 NB-LDPC** 后，能否在同域真实数据上端到端贯通并以**NB-LDPC 实际泄漏**驱动 PA 产钥？

- **对照**：单一替换臂为 `NbLdcShellIRAdapter`（V54 冻结方法），外壳对照为 Polar 原 IR（仅作 proxy 参数参考，不重跑）；Phase B/C 均为同域 development（smoke 9 / development 90），不跨域。
- **不改项**：不改 `H1-16/Lane C/H_inc1/H_inc2/m2/prior/decoder 90/1.0 poly37/verification L2-only +40/80` 任一部件；**不测新矩阵/标签/prior/阈值/decoder 参数**，新增即 `EVIDENCE_INVALID`；不重估先验（`V25 channel_counts.npz` 只读），新 session 仅重算 `m1/m2` 不调 LDPC。
- **贯通优先**：Phase B 9-block 使 `IR→PA` 泄漏传递、stage_used、decoder_calls、runtime、proxy yield 均可机械校验；预算 `18-36` 硬帽 36；Phase C 90-block 再量化门禁 `70/90 & 20/30`。
- **通过后的 claim 边界**：即使 `V63 development PASS`，仍仅为**同域 development 壳集成证据**（绑定 held-out `frame_ids` + `H provenance` + `shell registry` + `POLAR_REFERENCE_PROXY`），不等同阈值/SKR 泛化/资格/晋升/安全证明；报告显式标注 Polar 壳来源与处理点 `84d62779`，声明 `POLAR_REFERENCE_PROXY` 仅参考。

## 2. 冻结语义 — V54 方法与 Polar 外壳零改

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
- **V63 禁止任何新矩阵/标签/prior/阈值/decoder 参数变更**，违者 `EVIDENCE_INVALID`；`V61/V60` 数值不继续。

### 2.2 Polar 外壳只读语义（保留，不改）

| 外壳组件 | 机械来源 `file/function/key` | 语义 |
|---|---|---|
| TTBin读取/通道选择 | `src/` `experiments/run_e2e_pipeline.py` 的 `ttbin→pairs` 段 + `comparison_bench/io/pairs_loader.py:load_pairs_table` | 只读复用，不改 |
| delay/pairing | `src/` timing/pairing + `dataset_builder.py:build_frame_batch` (`dimension 1024, frame_len 1024`) | 只读，`pairing nearest legacy_v1` |
| symbol materialization | `pairs_loader→normalize_pair_columns→build_frame_batch` 的 `alice_symbol/bob_symbol ∈ [0,1024)` | 每块 `1024 symbols` |
| session/source/frame provenance | `frame_ids, held_out_ordinal_start/end, pairs_count 1024, sampling_mode` + `v54 BLOCK_WINDOWS` | 每块绑定 |
| 参数估计分层 | `nonbinary_v26_channel.py` 的 `H(A|B)` 估计（仅分层，不重估先验）| 只读 |
| verification/丢帧 | `v35 compute_tag_64` + `syndrome_ok&&tag_ok` + `reclassified` 四类 | `undetected` 单独 |
| PA/认证报告 | `src/reconciliation/` PA 组件 + `comparison_bench/pipeline` 报告 | 输入改为 NB `actual_disclosure_bits` |
| PIE/SKR 参数参考 | `polar_existing_bridge.py:benchmark_rows_from_polar_output` 的 `beta_eff_empirical, raw_ber, leak` 公式 | 仅 `POLAR_REFERENCE_PROXY` |

- `beta_eff_empirical` 必须由 `compute_beta_eff_empirical` 派生，永不手填。
- `finite-key/PIE/SKR` 仅 `POLAR_REFERENCE_PROXY`，不升级为 `composable`，不与 NB-LDPC `V61 ell` 混同。

### 2.3 数据裁决（同域 vs 新 session）

- **同域可直接运行**：`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816` 的 held-out 池，与 V54 同处理点 `84d62779` (`d1024 bw200 nearest legacy_v1`)，`43/45` 已实证 `alice/bob` 可重放（`hash` 相等），剩余 2 块经 `decoder-free 符号一致性校验`（`hash(alice||bob)` 比对）后纳入。
- **新 session 准入**：`decoder-free 信道域检查`（`P(B)` 分布 χ² / `H(A|B)` 均值漂移 > `τ=0.05 bits` 则 `out-of-domain`）→ `新 calibration P(U1|B) via get_l1_prior_p_u1_given_b + P(U2|B,U1) via factorize_f03` → `重算 m1/m2`（`m_total/m1 重算属后继 OpenSpec`, `m1=round(m_total*H1/H_total)`）后才可运行；**不调 LDPC**（矩阵/decoder/增量仍冻）。
- **未对齐停止**：若同域 `K_available<90` 或新 session 未通过域检查/未完成 calibration，则 `SHELL_DOMAIN_NOT_ALIGNED` 停止，不伪造。

### 2.4 合格比较样本（smoke 9 + development 90，冻结）

- **目标运行域声明（冻结）**：`D_target = { stratum_1M, stratum_1p5M, stratum_2M }`，处理点 `dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1` (**单点**，`84d62779`)，`source` 三源各一 held-out 区间（与 `V54` 已用区间零重叠可校验）。
- **Smoke 9**：`3/source=9 blocks`，若 held-out 超集 `K_heldout >9` 则 `index_j=floor(j*(K-1)/2) j=0..2` 分散选 `3/source`，否则取已验 43 中的 9；`v63_smoke_registry.json` 为 smoke authoritative。
- **Development 90**：`30/source=90 blocks`，枚举剩余非重叠四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916`），过滤与已用 `V48/V50/V51/V52/V53/V54` 重叠者得 `K2`，按 `ordinal` 排序后以 `index_j=floor(j*(K2-1)/29) j=0..29` 分散选 `30/源`；`v63_dev_registry.json` 为 development authoritative，禁换块/禁重采样。
- **标识**：`block_id, source, frame_ids[4], held_out_ordinal_start/end, pairs_count=1024, BLOCK_LENGTH=1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v63, held-out source_path, NB-LDPC H provenance`。
- **预算冻结**：`smoke 18-36 calls 硬帽36 (L2 9-27)`；`development 180-360 硬帽360 (L2 90-270)`。

### 2.5 IR 接口与 PA 泄漏传递（core replacement）

- **IR 接口替换**：Polar 原 `IRRunResult` 的 `leak_EC_actual_bits` 来源由 Polar 侧 `leak_EC` 改为 `NbLdcShellIRAdapter.actual_disclosure_bits`（per frame `leak_base/stage1/stage2` 按 `stage_used`），接口输出 `reconciled_symbols (full 32*u1_hat+u2_hat), accepted (=verify pass), rejected, exact (=exact_full), syndrome_ok, tag_ok, undetected, actual_disclosure_bits, decoder_calls, runtime_s, stage_used`。
- **PA 输入**：`PA.leak = actual_disclosure_bits per frame`（含 tag 64b，已计，不重复扣除），`PA.input = reconciled_symbols` 仅对 `accepted` 帧；`undetected` 帧虽 `accepted` 但 `!exact`，计入 `undetected` 单独表，永不并入 `accepted` 成功。
- **泄漏三档**：`base 1064/1094/1104 → stage1 1104/1134/1144 (+40) → stage2 1144/1174/1184 (+80)` per source，`per_source_avg[s]=leak_base[s]+40*N_stage1[s]/B+40*N_stage2[s]/B`，`overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/90`（三源 `leak_base` 不同禁单一公式）。
- **禁止**：复用 Polar `leak_EC_actual_bits` 作 NB-LDPC PA 输入；`leak_EC` 与 `actual_disclosure_bits` 语义混淆；`tag 64` 重复扣除。

## 3. 指标冻结（主/次分层，undetected 隔离）

### 3.1 主指标（门禁与价值判定，per-source 分层）

| 指标 | 定义 | 分层 | 门禁 (Phase C 90) |
|---|---|---|---|
| `accepted` / `exact_full` | `accepted = syndrome_ok&&tag_ok` per frame；`exact_full = exact_u1&&exact_l2` oracle；分别计数 | overall + per source (30) | `G1 final accepted≥70/90 且 exact≥70/90` （两者分别，禁假定相等） |
| `verify` 分别计数 | `verify_base / verify_stage1 / verify_final` (accepted per stage) | per stage per source | 完整性校验 |
| `undetected` | `syndrome_ok&&tag_ok && !exact_full` | 全局单独表 | `undetected==0` 全局，否则 `EVIDENCE_INVALID` 优先 |
| 四类 | `exact / detected(syndrome_fail) / decoder_non_syndrome(converged_no_syndrome) / undetected` | 全局 | 四类和为总帧 |
| `disclosure bits/block` | `leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184` 三档 + `per_source_avg + overall_avg + per accepted = total_disclosed_bits / accepted_count` | per source + overall | 仅报告，但需 `leak=5*m_total+64` 双校验 |
| `calls/rescue` | `N_stage1_attempted=count(!verify_base)`, `N_stage2_attempted=count(!verify_base&&!verify_stage1)`, `rescued_stage1 = count(verify_stage1&&exact_stage1&&!verify_base)`, `rescued_stage2 = count(verify_stage2&&exact_stage2&&!verify_after_stage1)`, `rescue_rate = rescued/attempted` (禁 `90-base_exact` 分母) | per source + overall | 仅报告 |
| `runtime/throughput` | `runtime_s per block + overall`；`throughput_input_bits_per_s = n_bits/runtime` | per source + overall | 仅报告，需可复现 |
| `stage_used` | `base/delta8/delta16` 分布 per source | per source + overall | 仅报告 |
| `Wilson 95%` | `overall 90 与 per-source 30` 的 Wilson 下界按 `accepted`（主）与 `exact`（审计）分别报告 | per source + overall | 仅报告 |
| `paired delta` | `per block base vs stage1 vs final (accepted/exact)` 差异 | per block | 诊断 |

- 四类 `exact/detected/decoder_non_syndrome/undetected` 需分别计数；`undetected` 永不并入 `success/FER`。
- 任意 `rank/nested/verification/记账/域检查` 失败 → `EVIDENCE_INVALID` 优先。

### 3.2 次级（仅排序，POLAR_REFERENCE_PROXY）

- 用 Polar 同一 `shadow` 参数（`benchmark_rows_from_polar_output` 的 `leak_EC_actual_bits, raw_ber, beta_eff_empirical`）计算 `PIE proxy = beta_eff_empirical * H_binary_shannon(raw_ber)` 与 `SKR proxy = accepted_fraction * (PIE - leak_per_block/n)` 类 `shadow`，三源独立，仅排序，不作门禁。
- 报告显式标注 `POLAR_REFERENCE_PROXY`，不升级为 `composable`，不与 `V61 ell` 混同。
- 禁止：泄漏分解语义不一致时跨方法 PIE/SKR 排序（`leak_actual_bits` 的 `tag` 与 `leak_other` 需显式校验一致）。

### 3.3 预注册统计（分层）

- Smoke 9 与 development 90 均为同域 development，不作独立 TEST qualification。
- `McNemar / binomial paired` 的 `p` 值可作为 `proxy yield` 的补充描述（`p>0.05` 视为不劣），但**不替代** `70/90 & 20/30` 硬门禁。

## 4. 数据就绪门（decoder-free，G1-G5 分层，shell 适配）

| 门 | 检查项 | 探针判定 |
|---|---|---|
| G1 | TTBin 可读且 held-out 池非空 | `load_pairs_table` 对 `v13r3fresh_pairs_20260816` 非空且 `pairs_count 1024` |
| G2 | 1042 symbols 可物化 | `normalize_pair_columns→build_frame_batch(q1024,frame_len1024)` 可恢复 `alice/bob ∈[0,1024)` |
| G3 | 1024-block 形态 | `dimension==1024, bin_width 200ps, pairing nearest legacy_v1, BLOCK_LENGTH 1024` per block |
| G4 | NB-LDPC 可重建 | `reconstruct_v54_matrices` 对 `H1/Lane C/H_inc1/H_inc2` `rank/nested/independence` 全 PASS |
| G5 | 域一致性 | 同域 `43/45` 已验 `hash_equal`，新 session 需 `domain_check + calibration` 完成 |

- Smoke 需 G1-G5 全 PASS 且 `K_available ≥9`；development 需 `K2 ≥90` 且 `per-source 30` 可分散，否则 `SHELL_DOMAIN_NOT_ALIGNED` 停止。
- 本轮 plan 仅冻结 G1-G5 定义，不执行 decoder（`rg "decode_"` 仅在冻结模块内）。

## 5. 预算（已冻结）

- **Smoke 9**：`L1 9` 固定 + `base 9` 固定 + `stage1 0-9` 条件 + `stage2 0-9` 条件 → 总 `18-36` 硬帽 36，`L2 9-27`，`per block 2-4 calls`。
- **Development 90**：`L1 90` 固定 + `base 90` 固定 + `stage1 0-90` 条件 + `stage2 0-90` 条件 → 总 `180-360` 硬帽 360，`L2 90-270`，`per block 2-4 calls`。
- `L1 共享`（同一 `q_i` 与 `P_i(U2)` 在三阶段间共享），`base` 兼 old 不重复。

## 6. 门禁与终态（已冻结）

对 `90-block` development 判定 (30/source)：

- **计数**：`accepted = verify pass (syndrome_ok&&tag_ok)` 与 `exact_full` 分别计数；`undetected` 单独表；`disclosure` 三档按实际 stage；`calls/rescue` 按 `!verify_base` / `!verify_base&&!verify_stage1` 分母。
- **分层**：各源各自 `base/stage1/final (accepted vs exact 分别)` 与 `leakage/rescue_rate/runtime/stage_used` 分别报告；`base/stage1` 仅分层报告不作主判；门禁仅 `final`。
- **泄漏**：三档 `leak_base/stage1/stage2` 分布 + `per_source_avg` + `overall_avg` + `per accepted (=total_disclosed / accepted_count)` + `Wilson 95%` per source & overall 的描述性；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance。
- **预注册终态（冻结，90-block，first-match）**：

```
if not shell_adapter_aligned or not alignment_metadata_complete or rank/nested/verification/记账/域检查失败:
    V63 = EVIDENCE_INVALID  # 优先
elif not domain_possible (K_available<90 or per_source<30 or not replayable or new_session_without_calibration):
    V63 = SHELL_DOMAIN_NOT_ALIGNED  # 停止，不进 decoder
elif nbldpc_not_yet_executed (本轮):
    V63 = PLAN_CANDIDATE__SHELL_INTEGRATION_DONE  # 仅 plan
# 未来执行后（需适配 PASS + 独立 plan ACCEPT + EXECUTE_AUTH）再判（主门禁为 accepted/exact）：
# elif final_accepted >=70/90 ∧ per_source final_accepted >=20/30 ∧ undetected==0 ∧ rank/nested/verification/记账通过
#      ∧ final_exact >=70/90 ∧ per_source final_exact >=20/30
#        → V63_SHELL_DEVELOPMENT_PASS
# elif final_accepted >=50/90 ∨ rescued>0  # 有信号但未过门禁
#        → V63_SHELL_CORRECTION_WORKS_BUT_NOT_PASS
# else → V63_SHELL_NO_RETAINED_SIGNAL
```

- **PASS 容差冻结**：`overall final accepted≥70/90` 且 `per-source ≥20/30` 且 `final exact≥70/90 且 per-source ≥20/30` 且 `undetected==0` 且 `rank/nested/verification/记账/域检查` 通过；`accepted` 与 `exact` 需分别达标（禁 `accepted==exact` 假定）；`disclosure/PIE proxy` 仅报告。
- `Wilson 95%`/`rescue_rate`/`runtime`/`stage_used`/`PIE proxy` 仅报告，不作门禁；`exact` 需单独达标。

## 7. O3 配对语义与预注册统计（分层）

- 同源同 `block` 的样本 `(frame_ids[4], alice, bob)` 每块确定性一次，`L1` 单次生成 `q_i` 与 `P_i(U2)`，`base` → `stage1`（仅 `!verify_base`）→ `stage2`（仅 `!verify_after_stage1`）条件递进，同 `bob`/`P_i(U2)`/`s` 的嵌套前缀，`exact` 仅 oracle 统计。
- 跨块 `accepted` 差异为诊断量，永不作完整性失败。
- `PIE/SKR proxy` 的 `shadow` 参数需与 Polar 侧完全一致（`beta_eff_empirical` 的 `leak/n_bits/raw_ber` 同源），否则该次对比的次级排序失效。

## 8. 科学 preflight、守卫序、执行偏差防复发（已冻结，未来执行前）

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `fad33f4b` + data SHA `84d62779`）；四文件 SCOPED dirty（含 `v63` adapter、`v63` pipeline、`v54`、`v38`、`v35`）；G1-G5 未过即拒；输出根已存在即拒；任一拒绝零 calls 不建文件。
2. **科学 preflights（decoder-free, write-free，未来执行前）**：G1-G5 全检 + `H_base` 三矩阵与 committed v38 常量 `rank/support` 比对 + `H_inc1/H_inc2` 确定性重建与 `rank_total==m2+16 / nested / independence==8 / row≤16 / col≤1 / E≈96 / leak+40+40` 校验 + TRAIN counts 形态校验 + `FrameBatch` 可物化校验 + shell registry `frame_ids/ordinal` 每源分散校验 + `Polar PA` 参数可读性校验。
3. **执行偏差防复发（冻结）**：
   - 不使用 600s 外部 timeout；建议 `--timeout` 至少 `3600s` 或不设外部 timeout（decoder 内部 `90/1.0` 早停已限时）
   - 若执行返回 `session/cell ID`，只轮询同一 `session/cell ID` 进程状态，禁止 `restart`/`recreate` 新 session
   - 中断保留 raw partial 不聚合、不自动重跑
4. **Preflight 失败** → 写 `v63_invalid_notice.json` + 空 records + `v63_summary.json` (terminal `V63_EVIDENCE_INVALID` 或 `V63_SHELL_DOMAIN_NOT_ALIGNED` 分层) 后零 decoder calls 停止。
5. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前。

## 9. 记录、聚合、summary（预冻结，未来执行，分层）

每 L2 call record schema（含 `tag_scope=l2_only, arm∈{base,stage1,stage2}, source, stage_used`）：

```
call_id, source(1M/1p5M/2M), block_id, arm(base/stage1/stage2), pass_index(1/2/3), used_inc1(bool), used_inc2(bool), stage_used(base/delta8/delta16),
matrix_id(base/joint1/total), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or 1104/1134/1144 or 1144/1174/1184), leak_stage1, leak_stage2, status, runtime_s,
shell: reconciled_symbols_hash, accepted, rejected, undetected, actual_disclosure_bits, decoder_calls, stage_used,
pa: pa_input_leak_bits, pa_output_key_length_proxy, pie_proxy, skr_proxy
```

Summary 含：`base/stage1/final accepted` 与 `exact_full` 分别计数（per source & overall）、`rescued_stage1/stage2`、`N_stage1_attempted/N_stage2_attempted`（per source & overall）、`rescue_rate_stage1/stage2` per source、`stage_used` 分布、`per_source_avg` 与 `overall_avg` 与 `per accepted`、`Wilson 95%` per source & overall、`total_disclosed_bits`；`Δleak_per_source`，`Δleak_overall`；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance；L1 诊断；四类计数；`undetected==0`；门禁明细（`final` 的 per-source 容差与 overall 容差数值与 `V63_*` 终态）；`PIE/SKR proxy` 仅排序；`PA` 泄漏输入明细；`Polar shell provenance`。

## 10. 证据写出（预冻结，未来执行，不在本轮）

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_smoke/    # Phase B 9-block
comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/       # Phase C 90-block
```

文件：`v63_records.json/.csv` (smoke `9-27` L2行 / dev `90-270` L2行；总 calls smoke `18-36` / dev `180-360` 硬帽)、`v63_summary.json`（分层，含 shell 贯通）、`v63_shell_registry.json` (authoritative)、`v63_invalid_notice.json`（失败时）、`v63_data_readiness.json`（G1-G5）。CSV/JSON 行对等；禁写 NPZ. **本轮 P0 不创建上述输出**，仅冻结计划。

## 11. 实现草图（后继轮次，当前未授权，需适配 PASS + 独立 plan ACCEPT + EXECUTE_AUTH）

- `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`：import `v54_two_stage_incremental_l2_rescue` 常量与 `v35.compute_tag_64`，实现 `NbLdcShellIRAdapter(IRMethod)` 的 `run(batch: FrameBatch) -> IRRunResult`（含 L1→P_i(U2)→三阶段条件 runner，`actual_disclosure_bits` 按 `stage_used`，`reconciled_symbols` 为 `x2_hat`），**仅当 shell 适配 PASS + 独立 plan ACCEPT + EXECUTE_AUTH 后才允许创建**。
- `comparison_bench/src/comparison_bench/pipeline/shell_integration.py`：`run_shell_pipeline(ttbin_root, source, block_ids) -> ShellResult`串联 `pairs_loader→FrameBatch→NbLdcShellIRAdapter→verification→leakage stats→PA(输入 NB 实际泄漏)→report`，`src/experiments` 仅读 PA/report 非 IR 部分。
- `scripts/execute_v63_shell_smoke.py` / `scripts/execute_v63_shell_development.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan `fad33f4b` + data SHA `84d62779` + shell registry `hash`）；四文件 SCOPED dirty；G1-G5 全 PASS 已验；budget 硬帽执行；执行偏差防复发；任一 gate 失败非零退出。
- 仅 fake-runner 测试通过后才可进入正式壳集成；不以 outcomes 定增量或调 `Δm`；不改 Polar src。

## 12. 自由裁量 D1–D8（修订至 PLAN_CANDIDATE）

- D1 完全冻结 V54 方法（H1/L1-APP/Lane C/H_inc1/H_inc2/decoder/prior/verification 零改），V63 不新增矩阵/标签/prior/阈值。
- D2 单一二阶段 `Δm=8+8` per source 嵌套 rescue，外壳仅替换 IR 段，`base vs stage1 vs final` 三阶段 per block 条件，PA 读 NB 实际泄漏。
- D3 Polar 外壳只读复用，`POLAR_REFERENCE_PROXY` 不升级，`beta_eff_empirical` 派生。
- D4 同域 smoke `3/source=9` 与 development `30/source=90` 注册算法：若超集更大则分散选，否则判 `SHELL_DOMAIN_NOT_ALIGNED`，frame_ids 已冻，禁换块。
- D5 预算 `smoke 18-36 / dev 180-360` 硬帽，`L2 9-27 / 90-270`，`base` 兼 old 不重复。
- D6 预注册终态：`EVIDENCE_INVALID > SHELL_DOMAIN_NOT_ALIGNED > SHELL_DEVELOPMENT_PASS > CORRECTION_WORKS_BUT_NOT_PASS > NO_RETAINED_SIGNAL`。
- D7 新 session 准入：new/incompatible session → DOMAIN_CALIBRATION_REQUIRED → 停止，校准属后继 OpenSpec，不调 LDPC。
- D8 本轮仅交付四工件，未来执行仍仅 development 证据，不扩大为 qualification。

## R63 Revisions (PLAN_REVISION_CANDIDATE, 2026-08-30, HEAD 5602f11c)

**R63 Lifecycle**: PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED revision of 5602f11c, decoder-free spike only.
- **R63-01 32*u1+u2+exact**: See proposal R63-01. In shell pipeline, FrameBatch stores full symbols s in [0,1023]; adapter decomposes u1_true = s //32, u2_true = s %32 for L1/L2 processing, then recomposes s_hat = 32*u1_hat + u2_hat. reconciled_symbols field is full s_hat (1024-length array of 0..1023). Verification exact_full checks both sub-symbols. GF32 operations only on u1/u2 5-bit planes.
- **R63-02 NbLdpcShellResult not change signature**: IRRunResult (base.py) fields frozen. New ShellResult dataclass: {ir_result: IRRunResult, reconciled_symbols: ndarray[1024], accepted, exact, undetected, actual_disclosure_bits, decoder_calls, stage_used, pa_leak, pa_proxy}. Adapter method signature run(batch: FrameBatch, source: str) -> ShellResult without mutating IRRunResult. Existing run_benchmark/compare_methods continue to accept IRRunResult.
- **R63-03 smoke INTEGRATION_REPLAY_SMOKE 90 fresh zero overlap**: As proposal R63-03. Generation reads only frame_ids/pairs_count from held-out pool metadata (no decoder). Smoke 9 uses V54-verified replay blocks; fresh 90 uses remaining windows with zero-overlap proof (sorted frame_ids, interval overlap check). Registries stored under （已移除临时路径，见 V63P0 权威 registry）/registries/ plus mirrored docs/research_cycles/V63P0/.
- **R63-04 DOMAIN_CALIBRATION_REQUIRED**: new/incompatible session → DOMAIN_CALIBRATION_REQUIRED → 停止，校准属后继 OpenSpec；同域 smoke 仅需域检查 PASS。

