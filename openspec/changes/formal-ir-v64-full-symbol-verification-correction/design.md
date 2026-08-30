# OpenSpec Design: formal-ir-v64-full-symbol-verification-correction

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅 plan 四工件，Phase A 未分流前禁止实现/运行 decoder，不改 V63 工件，不改纠错参数**
**Cycle**: `V64P0`
**Predecessor**: `formal-ir-v63-nbldpc-polar-shell-integration` (`5602f11c`, V63 二阶段 `H1-16+Lane C+Δ8+Δ8` 壳集成) — V64 继承其全部纠错参数，仅修正 verification 语义
**Freeze HEAD**: `TBD` (branch `formal-ir-mainline`, 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) — **data SHA** `84d62779` (`d=1024 bw=200 pairing=nearest rule=legacy_v1`, 同域单点)
**Feasibility**: V54/V63 二阶段 `H_total 200/206/208 rank m2+16 nested True` 已在同域 43/45 可重放；`compute_tag_64` canonical 已在 V35/V63 验证仅改输入不增泄漏；唯一待验为 **Phase A 能否将 v63_dev_1M_0133 定位为 U1-only tag 缺口** 与 **Phase B 改 full-symbol tag 后是否拦截该类 undetected**

## 1. 科学问题与关键判断

> 在**完全冻结 V63 纠错能力**（`H1-16+L1APP+Lane C+Δ8+Δ8, leak 1064→1144/1174 1184`）且**泄漏不增**的前提下，V63 的 `L2-only tag( U2 )` 是否导致 `U1 wrong + U2 exact` 的帧被误判为 `syndrome_ok && tag_ok` 而形成 `undetected/L2-only 假通过`？若是，则将 verification 改为 `tag(32*U1+U2)` 全符号单 64-bit tag 能否在 fresh 36 blocks 上使门禁 `exact_full≥28/36 & per-source≥8/12 & undetected_full_tag==0` 成立？

- **对照**：单一纠错臂不变（`NbLdpc Two-Stage Δ8+Δ8`），仅 verification 输入变量：`L2-only (V63)` vs `full-symbol (V64)` 双口径同一次 decode 对照；Phase A 为只读归因分流，Phase B 为 fresh 独立验证（非同块重跑）。
- **不改项**：不改 `H1-16/L1APP/Lane C/H_inc1/H_inc2/m2/prior/decoder 90/1.0 poly37/verification-only/+40/+80` 任一纠错部件；**不测新矩阵/标签/prior/阈值/decoder 参数**，新增即 `EVIDENCE_INVALID`；不重估先验（`V25 channel_counts.npz` 只读）。
- **归因优先**：Phase A 零 decoder 只读核查 `v63_dev_1M_0133` 的 `exact_u1/l2, syndrome_ok_l1/l2, tag_ok_l2, U1/U2 errors`，first-match 分流；`U1 wrong+U2 exact → Phase B 修正验证`，`U2 wrong+tag_ok → 暂停调查`，`ATTRIBUTION_INCOMPLETE → 不重跑 v63_dev_1M_0133，但允许进入 Phase B fresh instrumentation confirmation（最小修订新增路径，不预设根因）`。
- **验证/仪器化优先**：Phase B 36 fresh 12/source **不预设根因**，一次 decode 内**同时保存** `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak` 并同时算 `tag_ok_l2` 与 `tag_ok_full`（仍只计一个 64-bit tag，不增 calls/泄漏），以 `full` 为门禁口径；并按 fresh 三规则解释 — `U1 wrong+U2 exact+old accept+full reject→确认 verification-scope`；`U2 wrong+tag_ok→停止转 tag/canonical investigation`；`无 discordance→仅 full-tag performance signal，不得称已解释 V63 那例`。
- **通过后的 claim 边界**：即使 `V64 PASS`，仍仅为**同域 fresh development 证据**（绑定 `v64_fresh_registry.json` + `H provenance` + `tag 64 全符号` + `84d62779`），不等同阈值/SKR 泛化/资格/晋升/安全证明；报告显式标注 `L2-only (V63) vs full (V64)` 对照差异。

## 2. 冻结语义 — V63 纠错零改，仅 verification 输入修正

### 2.1 固定不变项（纠错完全冻结，零改，V63→V64 继承 V54）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 symbols/block (`4×256 frames`) | V31/V54 |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` `v35_algorithm_development` |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop` | V43/V52 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` `load_v25_channel_counts()` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | `m1=16`, tag 64b |
| 泄漏 stage1 | `leak_stage1=5*(m2+8)+80+64 → 1104/1134/1144 (+40)` | `Δm=8` det1 |
| 泄漏 stage2 | `leak_stage2=5*(m2+16)+80+64 → 1144/1174/1184 (+80)` | `Δm=8` det2, `H_total 200/206/208` |
| H_inc1/H_joint1 | `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` `8×1024` det1 + `h_joint1 192/198/200×1024` nested | V52 冻结 |
| H_inc2/H_total | `h_inc_1M_det2 / h_inc_1p5M_det2 / h_inc_2M_det2` `8×1024` det2 + `h_total 200/206/208×1024` nested | V54 冻结 |
| Prior | `TRAIN-only` via `load_v25_channel_counts()`，comparison blocks 来自冻结 held-out (非 TRAIN) | V25 |
| Rescue触发 | `verification-only`：仅未通过 `verify` 才进入下一阶段 | V52/V53/V54 |
| Δm | `8+8=16` per source, `leak_stage1-leak_base=40` `leak_stage2-leak_stage1=40` | V54 |

- `exact_full = exact_u1 && exact_l2` oracle（`u1_hat==u1_true && u2_hat==u2_true`），`exact_u1/exact_l2` 分别报告；`exact` 仅统计不触发增量。
- 相同 `bob`/`prior`/`P_i(U2)` 在 `base vs stage1 vs final` 间共享；仅 `H_L2/syndrome` 不同。
- **V64 禁止任何新矩阵/标签/prior/阈值/decoder 参数变更**，违者 `EVIDENCE_INVALID`。

### 2.2 Verification 修正（V64 唯一变量，泄漏不增，单 tag 仪器化不变性）

| 维度 | V63 (before) | V64 (after) |
|---|---|---|
| tag_scope | `l2_only` | `full_symbol` |
| tag_input | `x2 = u2_hat[1024]` (GF32 5-bit plane, L2-only) | `s_hat = 32*u1_hat + u2_hat` (full 1024 symbols 0..1023, 10-bit) |
| compute | `compute_tag_64(empty_uint8, x2) trunc64` | `compute_tag_64(canonical, s_hat_packed) trunc64` 复用同一 `compute_tag_64` |
| 泄漏 | `5*m_total+64` 含单 tag 64b | **不变**，仍单 64-bit tag，`leak_base/stage1/stage2` 数值不变，不因双算而增 |
| verify | `syndrome_ok && tag_ok_l2` | `syndrome_ok && tag_ok_full` (门禁口径) |
| 双口径 | — | **同次 decode** 并列算 `tag_ok_l2` vs `tag_ok_full` 作对照，**同时保存** `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak` |

- `s_hat` 打包：`32*u1+u2 ∈ [0,1023]` 10-bit 自然序，按 V35 `compute_tag_64` canonical MSB-first 打包（与 V63 `x2` 打包一致，仅输入源扩大），`seed` 仍 64-bit Toeplitz，输出仍 64-bit trunc。
- `leak/calls` 不增证明：`tag` 始终 1×64b 仅 `total` 计一次，不因输入从 5-bit 扩到 10-bit 而增；`m_total` 未变，故 `5*m_total+64` 不变；**双口径为同次 decode 的纯计算对照，不新增 syndrome/tag 轮次或泄漏比特**。
- 禁止：第二 tag、重复计 tag、改 `m_total`、改 `tag 长度`、双算计两次泄漏/两次 calls。
- **fresh 解释不变性**：Phase B 不预设根因；`U1 wrong+U2 exact+old accept+full reject→确认 verification-scope`，`U2 wrong+tag_ok→转 tag/canonical investigation`，`无 discordance→仅 full-tag performance signal`。

### 2.3 Phase A 只读归因输入（v63_dev_1M_0133）与新增仪器化分流

- **数据来源**：`comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/` 下 `v63_dev_1M_0133` 块（`source=1M`），含 `v63_records.json/.csv` (含 per-call `exact_u1, exact_l2, exact_full, syndrome_ok_l1, syndrome_ok_l2, tag_ok_l2, wrong_codeword, tag_input_hash, U1/U2 error counts`) + `v63_summary.json` + `v63_shell_registry.json` + `frame_ids/held_out_ordinal` provenance。
- **只读语义**：Phase A 仅 `Read` 上述已落盘 JSON/CSV，不调用 `decode_*`，不读 raw `pairs.parquet` 做重解码，不写任何 `run_01`，不改 V63 目录；`rg "decode_"` 在 Phase A 脚本内 0 hits（除 import 冻结模块的常量读取）。
- **核查字段**：`exact_u1 (=array_equal(u1_hat,u1_true))`, `exact_l2 (=array_equal(u2_hat,u2_true))`, `exact_full (=exact_u1&&exact_l2)`, `syndrome_ok_l1 (=H1*u1_hat==s1)`, `syndrome_ok_l2 (=H_L2*u2_hat==s_L2)`, `tag_ok_l2 (=tag_l2==tag_true_l2)`, `U1_errors (=count(u1_hat!=u1_true))`, `U2_errors`, `L1 posterior 可用性`, `tag_scope 标注`。
- **新增分流（最小修订）**：若字段缺失/口径矛盾 → `ATTRIBUTION_INCOMPLETE` 不重跑 `v63_dev_1M_0133`，但**允许**进入 Phase B **fresh instrumentation confirmation**；该路径**不预设根因**，仅在 36 fresh blocks 上做仪器化对照，需同次 decode 同时保存 `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak` 且双算 `tag_ok_l2/tag_ok_full` 仍只计一个 64-bit tag 不增 calls/泄漏；直接继续沿用 `U1 wrong+U2 exact → verification-scope` 的旧假设而不经 fresh 仪器化则违冻结分流。

### 2.4 Phase B fresh 36 blocks 数据就绪（同域 84d62779）

- **目标运行域声明（冻结）**：`D_target = { stratum_1M, stratum_1p5M, stratum_2M }`，处理点 `dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1` (**单点**，`84d62779`)，`source` 三源各一 held-out 区间（与 `V54/V63` 已用区间零重叠可校验）。
- **规模**：`36 blocks = 12/source ×3`，每块 `1024 symbols (4×256 frames)`，枚举剩余非重叠四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916` 与 V63 一致的 held-out 超集），过滤与已用 `V48/V50/V51/V52/V53/V54/V63`（含 `v63_smoke 9 + v63_dev 90`）重叠者得 `K2`，按 `ordinal` 排序后以 `index_j=floor(j*(K2-1)/11) j=0..11` 分散选 `12/源`；`v64_fresh_registry.json` 为 fresh authoritative，禁换块/禁重采样。
- **标识**：`block_id, source, frame_ids[4], held_out_ordinal_start/end, pairs_count=1024, BLOCK_LENGTH=1024, sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v64, held-out source_path, H provenance`。
- **预算冻结**：`36 blocks: L1 36 + base36 + stage1≤36 + stage2≤36 =72–144 硬帽144 (L2 36–108)`，`per block 2–4 calls`。

### 2.5 数据裁决（同域 vs 新 session）

- **同域可直接运行**：`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816` 的 held-out 池，与 V63 同处理点 `84d62779`，Phase B 所需 `K2≥36` 且 `per-source≥12` 才合法；Phase A 对 `v63_dev_1M_0133` 不做域检查（已落盘）。
- **新 session 准入**：本变更不新增新 session 采集；若未来 fresh 池 `K2<36` 则 `EVIDENCE_INVALID` 停止，不伪造，不以 `SER/vis` 代理冒充。
- **未对齐停止**：若 `K_available<36` 或 `pairing/dimension/bw` 不一致或 `H 矩阵校验失败`，则 `EVIDENCE_INVALID` 停止，不伪造。

## 3. 指标冻结（主/次分层，undetected 隔离，双口径对照）

### 3.1 主指标（门禁与价值判定，per-source 分层）

| 指标 | 定义 | 分层 | 门禁 (Phase B 36) |
|---|---|---|---|
| `exact_u1 / exact_l2 / exact_full` | `exact_u1 = u1_hat==u1_true`；`exact_l2 = u2_hat==u2_true`；`exact_full = exact_u1&&exact_l2` oracle；分别计数 | overall + per source (12) | `exact_full ≥28/36 overall ∧ 每源 ≥8/12` |
| `syndrome_ok / tag_ok_l2 / tag_ok_full` | `syndrome_ok = H_L2*u2_hat==s_L2`；`tag_ok_l2 = tag(U2)==tag_true`；`tag_ok_full = tag(32*U1+U2)==tag_true_full` | per frame | 完整性校验 |
| `accepted_l2 / accepted_full` | `accepted_l2 = syndrome_ok&&tag_ok_l2`；`accepted_full = syndrome_ok&&tag_ok_full` | overall + per source | 门禁以 `accepted_full` vs `exact_full` 对照 |
| `undetected_l2 / undetected_full` | `syndrome_ok&&tag_ok_l2&&!exact_full` vs `syndrome_ok&&tag_ok_full&&!exact_full` | 全局单独表 | `undetected_full_tag==0` 全局，否则 FAIL；`undetected_l2` 仅对照 |
| `被拦截 U1-only wrong` | `count(!exact_u1 && exact_l2 && tag_ok_l2 && !tag_ok_full)` | overall + per source | 仅报告，诊断 L2-only 漏洞 |
| `disclosure bits/block` | `leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184` 三档 + `per_source_avg[s]=leak_base[s]+40*N_stage1[s]/12+40*N_stage2[s]/12` + `overall_avg=(Σ leak_base+40*N_stage1+40*N_stage2)/36` + `per accepted = total_disclosed / accepted_full_count` | per source + overall | 仅报告，但需 `leak=5*m_total+64` 双校验 |
| `calls/rescue` | `N_stage1_attempted=count(!verify_full_base)`, `N_stage2_attempted=count(!verify_full_base&&!verify_full_stage1)`, `rescued_stage1/2` 以 `verify_full` 为准 | per source + overall | 仅报告 |
| `runtime/throughput` | `runtime_s per block + overall`；`throughput_input_bits_per_s = n_bits/runtime` | per source + overall | 仅报告，需可复现 |
| `stage_used` | `base/delta8/delta16` 分布 per source (以 full verification 触发计) | per source + overall | 仅报告 |
| `Wilson 95%` | `overall 36 与 per-source 12` 的 Wilson 下界按 `exact_full`（主）与 `accepted_full`（审计）分别报告 | per source + overall | 仅报告 |
| `L2-only vs full 差异` | `Δ_accepted = accepted_l2 - accepted_full`, `Δ_undetected = undetected_l2 - undetected_full`, `Δ_tag_ok` per source | per source + overall | 仅报告，诊断修正效果 |

- `undetected_full` 永不并入 `success/FER`；`exact_full` 与 `accepted_full` 分别计数。
- 任意 `rank/nested/verification/记账/域/预算/重叠` 失败 → `EVIDENCE_INVALID` 优先。

### 3.2 次级（仅报告，full-symbol 仍单 tag）

- `tag` 仍单 64b `≈2^-64` 工程近似，`epsilon_ec=2^-64` 不变；`finite-key/PIE/SKR` 不作门禁，Phase B 仅报告 `leakage` 分布。
- 禁止：跨方法泄漏分解语义不一致时排序（`leak_actual_bits` 的 `tag` 与 `leak_other` 需显式校验一致）。

### 3.3 预注册统计（分层）

- Phase B 36 blocks 为 fresh development，不作独立 TEST qualification。
- `McNemar / binomial paired` 的 `p` 值可作为 `L2-vs-full` 差异的补充描述（`p>0.05` 视为不劣），但**不替代** `28/36 & 8/12` 硬门禁。

## 4. 数据就绪门（decoder-free，G1-G5 分层）

| 门 | 检查项 | 探针判定 |
|---|---|---|
| G1 | Phase A 输入可读 | `v63_dev_1M_0133` records/summary/registry 非空且含 `exact_u1/l2, syndrome_ok_l1/l2, tag_ok_l2` 字段 |
| G2 | 1024 symbols 可物化 | `normalize_pair_columns→build_frame_batch(q1024,frame_len1024)` 可恢复 `alice/bob ∈[0,1024)` （仅 Phase B prep） |
| G3 | 1024-block 形态 | `dimension==1024, bin_width 200ps, pairing nearest legacy_v1, BLOCK_LENGTH 1024` per block |
| G4 | NB-LDPC 可重建 | `reconstruct_v63_matrices` 对 `H1/Lane C/H_inc1/H_inc2` `rank/nested/independence` 全 PASS |
| G5 | 域一致性 | fresh `K2≥36` 且 `per-source≥12` 且与 `V48–V63` `frame_ids` 零重叠 |

- Phase A 仅需 G1 PASS 即可归因；Phase B 需 G1-G5 全 PASS 且 `K2≥36`，否则 `EVIDENCE_INVALID` 停止；**`ATTRIBUTION_INCOMPLETE` 不再直接终止 Phase B fresh instrumentation** — 已记录缺失字段清单后允许进入 Phase B 仪器化对照（不预设根因，claim 受限）。
- 本轮 plan 仅冻结 G1-G5 定义，不执行 decoder（`rg "decode_"` 仅在冻结模块内）；`DECODE_FORBIDDEN` 直至实现后授权前保持。

## 5. 预算（已冻结）

- **Phase A**：`0 calls` (decoder-free 只读)。
- **Phase B 36 blocks**：`L1 36` 固定 + `base 36` 固定 + `stage1 0-36` 条件 + `stage2 0-36` 条件 → 总 `72–144` 硬帽144，`L2 36–108`，`per block 2–4 calls`。
- `L1 共享`（同一 `q_i` 与 `P_i(U2)` 在三阶段间共享），`base` 兼 old 不重复。

## 6. 门禁与终态（已冻结，ATTRIBUTION_INCOMPLETE fresh 仪器化修订）

对 `36-block` fresh `12/source` 判定：

- **计数与同次保存**：`exact_full = exact_u1&&exact_l2` 与 `accepted_full = syndrome_ok&&tag_ok_full` 分别计数；每 block 的**同次 decode 同时保存** `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak`；`undetected_full = syndrome_ok&&tag_ok_full&&!exact_full` 单独表；`undetected_l2` 仅对照；`disclosure` 三档按实际 `stage_used` (以 full verification 触发计)；`calls/rescue` 按 `!verify_full_base` / `!verify_full_base&&!verify_full_stage1` 分母；双口径仍只计一个 64-bit tag 不增 calls/泄漏。
- **分层**：各源各自 `base/stage1/final (accepted_full vs exact_full 分别 + L2-vs-full Δ)` 与 `leakage/rescue_rate/runtime/stage_used/被拦截U1-only` 分别报告；`base/stage1` 仅分层报告不作主判；门禁仅 `final` full 口径。
- **泄漏**：三档 `leak_base/stage1/stage2` 分布 + `per_source_avg` + `overall_avg` + `per accepted` + `Wilson 95%` per source & overall 的描述性；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance。
- **fresh 解释规则（不预设根因）**：`U1 wrong+U2 exact+old accept+full reject` 才确认 verification-scope 假设；`U2 wrong+tag_ok` 则停止转 `tag/canonical investigation`；`无 old vs new discordance` 则仅 `full-tag performance signal` 不得称已解释 `v63_dev_1M_0133`。
- **预注册终态（冻结，36-block，first-match，最小修订）**：

```
if rank/nested/verification/记账/域/预算/重叠/tag_input_correct checks fail:
    V64 = EVIDENCE_INVALID  # 优先（不因 attribution 绕过）
elif attribution_result == ATTRIBUTION_INCOMPLETE and fresh_instrumentation_not_yet_executed:
    V64 = PLAN_CANDIDATE__ATTRIBUTION_INCOMPLETE_FRESH_INSTRUMENTATION_DESIGN_DONE  # 仅 plan，允许 fresh 仪器化
elif not domain_possible (K2<36 or per_source<12 or not registry_zero_overlap):
    V64 = EVIDENCE_INVALID  # 域不足，不伪造
elif nbldpc_not_yet_executed (本轮 PLAN):
    V64 = PLAN_CANDIDATE__ATTRIBUTION_AND_FRESH_DESIGN_DONE  # 仅 plan，DECODE_FORBIDDEN
# 未来执行后（需 Phase A 归因记录完成（含 ATTRIBUTION_INCOMPLETE 的 fresh 仪器化声明）+ 独立 plan ACCEPT + EXECUTE_AUTH）再判：
# elif exact_full >=28/36 ∧ per_source exact_full >=8/12 ∧ undetected_full_tag==0 ∧ all exact frames tag_ok_full==True ∧ rank/nested/预算/泄漏通过
#        → V64_FULL_SYMBOL_VERIFICATION_PASS  # 仍需同次保存与双口径对照满足，且若 attribution==INCOMPLETE 则 claim 限为 full-tag performance signal 除非 fresh 出现 U1-only 拦截确认
# elif fresh shows U2 wrong+tag_ok (exact_l2==False && tag_ok_full==True):
#        → V64_PAUSE_TAG_CANONICAL_INVESTIGATION  # 停止，不判 PASS/FAIL，转 tag/canonical 调查
# elif exact_full >0 but (exact_full<28/36 or per_source<8/12 or undetected_full_tag!=0) and corrected_has_signal:
#        → V64_CORRECTION_WORKS_VERIFICATION_STILL_FAILS  # 纠错有信号但 full verification 未全过
# elif exact_full <28/36 or per_source<8/12 and no_corrected_signal:
#        → V64_CORRECTION_PERFORMANCE_FAIL
# else → V64_EVIDENCE_INVALID
```

- **PASS 容差冻结**：`overall exact_full≥28/36 (77.78%)` 且 `per-source ≥8/12 (66.7%)` 且 `undetected_full_tag==0` 且 `所有 exact_full 帧 tag_ok_full==True` 且 `rank/nested/verification/记账/预算/泄漏` 通过；`exact_full` 需单独达标（`accepted_full` 与 `exact_full` 分别计数，禁相等假定）；`leakage` 仅报告。
- `Wilson 95%`/`rescue_rate`/`runtime`/`stage_used`/`被拦截U1-only`/`L2-vs-full Δ` 仅报告，不作门禁。

## 7. O3 配对语义与预注册统计（分层）

- 同源同 `block` 的样本 `(frame_ids[4], alice, bob)` 每块确定性一次，`L1` 单次生成 `q_i` 与 `P_i(U2)`，`base` → `stage1`（仅 `!verify_full_base`）→ `stage2`（仅 `!verify_full_after_stage1`）条件递进，同 `bob`/`P_i(U2)`/`s` 的嵌套前缀，`exact` 仅 oracle 统计。
- 跨块 `accepted`/`exact` 差异为诊断量，`L2-only vs full` 的 `Δ` 为验证修正效果的诊断量，永不作完整性失败。
- `tag` 输入可追溯：`tag_ok_full` 的 `s_hat = 32*u1_hat+u2_hat` 需与 `reconciled_symbols` 完全一致，否则 `EVIDENCE_INVALID`。

## 8. 科学 preflight、守卫序、执行偏差防复发（已冻结，未来执行前）

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `84d62779` data SHA）；`v64_fresh_registry.json` 的 `frame_ids` 与 `V48–V63` 零重叠已验；G1-G5 未过即拒；输出根已存在即拒；任一拒绝零 calls 不建文件。
2. **科学 preflights（decoder-free, write-free，未来执行前）**：
   - Phase A: `v63_dev_1M_0133` records 字段完整性校验 + `exact_u1/l2/syndrome_ok_l1/l2/tag_ok_l2` 一致性校验 + `U1/U2 errors` 可计算校验
   - Phase B: G1-G5 全检 + `H_base` 三矩阵与 committed `v63` 常量 `rank/support` 比对 + `H_inc1/H_inc2` 确定性重建与 `rank_total==m2+16 / nested / independence==8 / row≤16 / col≤1 / E≈96 / leak+40+40` 校验 + TRAIN counts 形态校验 + `FrameBatch` 可物化校验 + fresh registry `frame_ids/ordinal` 每源分散校验
3. **执行偏差防复发（冻结）**：
   - 不使用 600s 外部 timeout；建议 `--timeout` 至少 `3600s` 或不设外部 timeout（decoder 内部 `90/1.0` 早停已限时）
   - 若执行返回 `session/cell ID`，只轮询同一 `session/cell ID` 进程状态，禁止 `restart`/`recreate` 新 session
   - 中断保留 raw partial 不聚合、不自动重跑
   - Phase A 零 calls 保证：`rg "decode_row_layered_fftqspa|decode_error_domain"` 在 Phase A 脚本内 0 hits
4. **Preflight 失败** → 写 `v64_invalid_notice.json` + 空 records + `v64_summary.json` (terminal `V64_EVIDENCE_INVALID` 或 `V64_ATTRIBUTION_INCOMPLETE` 分层) 后零 decoder calls 停止。
5. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前。

## 9. 记录、聚合、summary（预冻结，未来执行，分层，双口径）

每 L2 call record schema（含 `tag_scope=full_symbol + l2_only对照, arm∈{base,stage1,stage2}, source, stage_used`，**同次 decode 同时保存**）：

```
call_id, source(1M/1p5M/2M), block_id, arm(base/stage1/stage2), pass_index(1/2/3), used_inc1(bool), used_inc2(bool), stage_used(base/delta8/delta16),
matrix_id(base/joint1/total), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_u1, exact_l2, exact_full, errors_u1, errors_u2,
syndrome_ok_l1, syndrome_ok_l2, tag_ok_l2, tag_ok_full, tag_scope_l2(l2_only), tag_scope_full(full_symbol), tag_input_l2_hash, tag_input_full_hash,
wrong_codeword, target_tag_l2, candidate_tag_l2, target_tag_full, candidate_tag_full,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p,
leak_total (1064/1094/1104 or 1104/1134/1144 or 1144/1174/1184), leak_stage1, leak_stage2, status, runtime_s,
shell: reconciled_symbols_hash (full 32*u1+u2), accepted_l2 (=syndrome_ok&&tag_ok_l2 old), accepted_full (=syndrome_ok&&tag_ok_full new), undetected_l2, undetected_full, actual_disclosure_bits, decoder_calls, stage_used,
delta: delta_tag_ok (tag_ok_l2 - tag_ok_full), intercepted_u1_only (bool: !exact_u1&&exact_l2&&tag_ok_l2&&!tag_ok_full), same_decode_double_tag_single_cost (bool True: 同次 decode 双算仍单 64b tag 不增 calls/leak)
```

Summary 含：`base/stage1/final accepted_full/accepted_l2` 与 `exact_u1/exact_l2/exact_full` 分别计数（per source & overall）、`undetected_full==0` 主判 + `undetected_l2` 对照、`L2-vs-full Δ` 明细、`被拦截U1-only wrong` 计数、`rescued_stage1/stage2`、`N_stage1_attempted/N_stage2_attempted`（per source & overall 以 full verification 为准）、`rescue_rate_stage1/stage2` per source、`stage_used` 分布、`per_source_avg` 与 `overall_avg` 与 `per accepted`、`Wilson 95%` per source & overall、`total_disclosed_bits`；`Δleak_per_source`，`Δleak_overall`；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance；L1 诊断；四类计数；门禁明细（`final` 的 per-source 容差与 overall 容差数值与 `V64_*` 终态）；`PA` 泄漏输入明细；`L2-vs-full` 对照 provenance。

## 10. 证据写出（预冻结，未来执行，不在本轮）

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_attribution/  # Phase A 0 calls
comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_fresh_36/    # Phase B 36-block
```

文件：`v64_attribution.json` (Phase A 归因报告, 0 decoder calls) + `v64_records.json/.csv` (Phase B `36–108` L2行；总 calls `72–144` 硬帽144)、`v64_summary.json`（分层，含双口径对照）、`v64_fresh_registry.json` (authoritative 36)、`v64_invalid_notice.json`（失败时）、`v64_data_readiness.json`（G1-G5）。CSV/JSON 行对等；禁写 NPZ. **本轮 P0 不创建上述输出**，仅冻结计划。

## 11. 实现草图（后继轮次，当前未授权，需 Phase A 归因记录完成 + 独立 plan ACCEPT + EXECUTE_AUTH，DECODE_FORBIDDEN 直至授权）

- `comparison_bench/src/comparison_bench/formal_ir/v64_full_symbol_verification.py`：import `v54_two_stage_incremental_l2_rescue` 常量与 `v35.compute_tag_64`，实现 `verify_full(s_hat) = compute_tag_64(canonical, s_hat)` 与 `verify_l2(x2) = compute_tag_64(empty, x2)` **同次 decode 双口径同时保存** `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak` 且仍单 64b tag 不增 calls/泄漏，**仅当 Phase A 归因记录完成（含 ATTRIBUTION_INCOMPLETE 的 fresh instrumentation 声明）+ 独立 plan ACCEPT + EXECUTE_AUTH 后才允许创建**。
- `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py` 补丁：`tag_input` 从 `x2` 改为 `32*u1_hat+u2_hat`，输出 `tag_ok_full` 与 `tag_ok_l2` 双字段同次保存，`actual_disclosure_bits` 三档不变，`single_tag_instrumentation` 断言。
- `scripts/execute_v64_attribution.py`：默认拒绝；只读 `v63_dev_1M_0133`，零 decoder calls，输出 `v64_attribution.json` 与 `ATTRIBUTION_INCOMPLETE → fresh instrumentation` 分流判定。
- `scripts/execute_v64_fresh_verify.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan data SHA `84d62779` + fresh registry `hash`）；SCOPED dirty；G1-G5 全 PASS 已验；budget 硬帽执行；同次双算单 tag 断言；执行偏差防复发；任一 gate 失败非零退出；fresh 解释按三规则（`U1-intercept→confirm` / `U2+tag_ok→investigate` / `无 discordance→仅 performance signal`）落盘。
- 仅 fake-runner 测试通过后才可进入 Phase B fresh verification；不以 outcomes 定增量或调 `Δm`；不改 V63 工件；`DECODE_FORBIDDEN` 保持至授权。

## 12. 自由裁量 D1–D8（修订至 PLAN_CANDIDATE）

- D1 完全冻结 V63 纠错方法（H1/L1-APP/Lane C/H_inc1/H_inc2/decoder/prior/泄漏零改），V64 仅改 verification 输入为 `32*u1+u2`，仍单 tag 64b。
- D2 单一全符号 tag 修正，单次 decode 双口径对照，外壳仅改 verification 输入，`base vs stage1 vs final` 三阶段 per block 条件（以 full verification 触发计），PA 读 NB 实际泄漏不变。
- D3 泄漏不增，`leak=5*m_total+64` 双校验，`+40/+80` 不变。
- D4 Phase A 零 decoder 只读归因三分支分流**新增 ATTRIBUTION_INCOMPLETE → Phase B fresh instrumentation confirmation（不预设根因）**，Phase B `12/source=36` 注册算法：若超集更大则分散选，否则判 `EVIDENCE_INVALID`，frame_ids 已冻，禁换块，零重叠；同次 decode 同时保存 `exact_u1/l2/full、syndrome_ok_l1/l2、tag_ok_l2/tag_ok_full、errors_u1/u2、old/new accepted、stage/calls/leak` 且双算仍单 tag。
- D5 预算 `Phase A 0 / Phase B 72–144` 硬帽，`L2 36–108`，`base` 兼 old 不重复，**双口径不增 calls/泄漏**。
- D6 预注册终态：`EVIDENCE_INVALID > ATTRIBUTION_INCOMPLETE（plan 态，允许 fresh 仪器化）> FULL_SYMBOL_VERIFICATION_PASS > PAUSE_TAG_CANONICAL_INVESTIGATION（fresh 现 U2+tag_ok）> CORRECTION_WORKS_VERIFICATION_STILL_FAILS > CORRECTION_PERFORMANCE_FAIL` first-match；`ATTRIBUTION_INCOMPLETE 下的 fresh 无 discordance 仅 performance signal`。
- D7 fresh 36 需 `K2≥36` 且 `frame_ids zero overlap`  with `V48–V63`，否则 `EVIDENCE_INVALID` 停止；Phase A `U2 wrong+tag_ok` 暂停调查 tag/encoding，fresh 中再现 `U2 wrong+tag_ok` 亦转 `tag/canonical investigation`。
- D8 本轮仅交付四工件，未来执行仍仅 fresh development 证据，不扩大为 qualification；V63 工件只读不覆写；`DECODE_FORBIDDEN` 直至实现后授权。
