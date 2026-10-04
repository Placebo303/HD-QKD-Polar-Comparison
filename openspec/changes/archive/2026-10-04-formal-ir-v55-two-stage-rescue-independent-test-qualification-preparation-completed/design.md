# OpenSpec Design: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Lifecycle**: `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` — **intake 3/3 READY + authoritative 90-block 已冻 + G1-G7 全 PASS，等待独立 plan review。不实现 runner，不执行 decoder，不创建 run_01。**
**Cycle**: `V55P0`
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd1686049156540328bac264296b17fee546c`, branch `formal-ir-mainline`), **freeze HEAD** `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`) — **data SHA** `84d62779603e62de50ded5182ed65b65d3dc6084` (semantics `d=1024 bw=200 pairing=nearest rule=legacy_v1`, 单点)
**Feasibility**: V54 二阶段 `H_total m2+16 嵌套满秩` 已在 V54 spike 三源实证（rank 200/206/208, nested True, row≤16, col_inc≤1, E≈96, leak +40+40）；**Intake 侧**：三源 `2130/5125/5513` frames (≥120, prefer ≥160) 均 3/3 READY，`frames×256` 行数、0..1023 范围、排序无缺失已验，`K=F-3` 均 ≥30，`90-block authoritative` gap≥4 已冻；唯一 blocker 已从数据侧移除，等待独立 plan 评审后授权执行。
**Key judgement**: **算法主线已足够好（V54 二阶段在 held-out 上 rank/nested/泄漏/预算均已冻结可构造），intake 已就绪，当前为独立跨 session TEST 资格就绪态，非方法需再调参。**

## 1. 科学问题与关键判断

> 在**完全冻结 V54 二阶段完整方法**（首遍 `H1-16 + L1-APP + Lane C` 与泄漏 `1064/1094/1104` 等价起点，`H_inc1 8×1024 Δ8 + H_inc2 8×1024 Δ8` 二阶段 rescue 已冻结 `m2/m2+8/m2+16 嵌套满秩`）的**相同参数**下，**新增 intake 三源 (`1M_600k_0dB F=2130 / 1p5M F=5125 / 2M_1.2M_0dB F=5513` 均 200ps legacy_v1，非同分布 2026-01-21) 的 `90-block (30/source)` authoritative TEST 能否以预注册门禁（coverage 70/90 + per-source 20/30 + undetected==0）判定方法在未见数据上的独立跨 session 泛化？**

- **对照**：无新对照臂；`base` 即 `old Lane C` 单遍结果（同一次译码兼 old），`stage1` 为 `Δ8` 后结果，`final(stage2)` 为 `Δ16` 后结果；比较为 `base vs stage1 vs final` 配对（描述性，门禁仅 `final` 的 coverage 70/90 + per-source 20/30 + undetected==0，且 `base→Δ16` 完整主判，`base/stage1` 仅分层报告不作主判替代）。
- **不改项**：不改 support/标签/prior/MET图/`m2`/H1/`max_iter/damping`/`H_inc1/H_inc2`/泄漏公式；**不测新矩阵/标签/prior/阈值/decoder参数**，新增即 `EVIDENCE_INVALID`。
- **90-block 的规模**：每源 30 共90，使 `70/90` (77.8%) 的 Wilson 下界可区分于偶然性；预算 `180-360` 硬帽360；每源块数平衡，之后禁换块。
- **通过后的 claim 边界**：即使 `V55_INDEPENDENT_TEST_PASS`，仍仅为**独立跨 session TEST 在 intake 三源上的资格确认**（单次 90-block，绑定 `20260123_1M_600k_0dB / 20260107_PPLN_1p5M / 20260123_2M_1p2M_0dB` 三次实际 acquisition，非同分布 2026-01-21），不等同全域 FER/阈值/SKR/资格/晋升；报告显式标注三源标签/日期/物理条件与 `84d62779` 处理点，声明 independent cross-session qualification evidence。

## 2. 冻结语义 — V54 方法零改

### 2.1 固定不变项（冻结方法，零改，V54 complete method）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 | V31 |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | `m1=16`, tag 64b L2-only |
| 泄漏 stage1 | `leak_stage1=5*(m2+8)+80+64 → 1104/1134/1144 (+40)` | `Δm=8` |
| 泄漏 stage2 | `leak_stage2=5*(m2+16)+80+64 → 1144/1174/1184 (+80)` | `Δm=16` |
| H1 | `V31-H1-QC-16×1024 rank16 80b` 母矩阵 | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop` | V43/V52 同构 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64, `syndrome_ok && tag_ok` 双条件 | V35 |
| 四类/G3' | `exact / detected / decoder_non_syndrome / undetected`, `G3' undetected==0` 单独表 | V46/V52 |
| H_inc1/H_joint1 | `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` `8×1024` det1 + `h_joint1 192/198/200×1024` nested | V52 冻结 |
| H_inc2/H_total | `h_inc_1M_det2 / h_inc_1p5M_det2 / h_inc_2M_det2` `8×1024` det2 + `h_total 200/206/208×1024` nested | V54 冻结 |
| Prior | `TRAIN-only` via `load_v25_channel_counts()`，evaluation blocks 来自 intake 独立跨 session TEST（非 TRAIN） | V25 |
| Rescue触发 | `verification-only`：仅未通过 `verify` 才进入下一阶段，已通过帧不增加泄漏不重译 | V52/V53/V54 |
| Δm | `8+8=16` per source 冻结，`leak_stage1-leak_base=40` `leak_stage2-leak_stage1=40` | V54 |

- `exact_* = array_equal(x_hat, u2_true)` oracle 主判据，同时报告 `exact_u1/exact_l2`；`exact` 仅统计不触发增量。
- 相同 `bob`/`prior`/`P_i(U2)` 在 `base vs stage1 vs final` 间共享；仅 `H_L2/syndrome` 不同。
- **V55 禁止任何新矩阵/标签/prior/阈值/decoder 参数变更**，违者 `EVIDENCE_INVALID`。

### 2.2 数据裁决（当前：intake 已就绪，非 HOLD）

- V13 `60/20/20 (TRAIN/VAL/HOLD)`：`split_manifest.json` 将 `2000/2767/3645` 帧（1M/1p5M/2M）按 `60% TRAIN / 20% VAL / 20% HOLD` 划分，HOLD 已污染 (180 块开发使用)，**不复用 HOLD 作 TEST**。
- **Intake 冻结**：三源 intake `20260123_1M_600k_0dB (F2130) / 20260107_PPLN_1p5M (F5125) / 20260123_2M_1p2M_0dB (F5513)` 均 READY，`84d62779` 单点 200ps legacy_v1，非同分布 2026-01-21，独立跨 session TEST 资格已具备，等待 plan review 后执行；**不宣称同分布复现**。

### 2.3 合格 TEST 样本（authoritative 90-block，已冻结）

- **目标运行域声明（冻结）**：`D_target = { stratum_1M_600k_0dB, stratum_1p5M, stratum_2M_1p2M_0dB }`，三源标签冻结，非同分布 2026-01-21
- **处理点**：`dimension 1024, bin_width 200ps, pairing nearest, rule legacy_v1, channels A1/B5` (**单点**，`84d62779`)
- **Provenance**：每源 `.ttbin` + `.1.ttbin` 同源 (sha256/size/mtime 已记，FileReader auto-merge，fully materialize then judge，无 padding/resampling/cross-session stitching)
- **结构**：每帧 256 pairs (rows = frames×256，已验 545280/1312000/1411328)，符号 `0..1023`，`frame_id 0..F-1` × `pair_idx 0..255` 排序连续无缺失 (assert 已验)，无尾帧补齐
- **主样本 (authoritative)**：`B=30` 每源共 `90` blocks，`F=2130/5125/5513`，`K=F-3=2127/5122/5510`，`all_starts=0..F-4`，`index_j=floor(j*(K-1)/29) j=0..29` 分散选 `30/source`，`gap≥4`，与 V13 及 V48-V54 零重叠 per source；`v55_authoritative_registry.json` 为唯一合法块集
- **标识**：`selected_frame_ids[4]=[s,s+1,s+2,s+3]`，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative`，`pairs_count=1024, BLOCK_LENGTH=1024`，**禁换块/禁重采样** (自 authoritative 起)
- **Intake 输出**：`comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` (additive, 不覆盖 V13) 保存 parquet/npy，大型文件不进 Git，compact evidence 已记录生成命令 `python workspace/v55_intake_20260828/v55_decoder_free_intake.py`、路径、行数、重建方法

### 2.4 三阶段协议（条件 HARQ，verification-only，已冻结，等待授权执行）

```
per block authoritative 90 blocks (30/source):
  prior = TRAIN prior (shared, V25)
  H1 s1 via true u1, L1 decode → BP → q → P(U2)  // 90 次总计，per block 1
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
  // exact_* 仅 oracle 统计，触发仅 verification; base/stage1 仅分层报告，主判 base→Δ16 (final)
  // 每块 L1 1 + base L2 1 + 条件 stage1 ≤1 + 条件 stage2 ≤1；90 块总 L1 90+base 90+≤90 stage1+≤90 stage2=180-360 硬帽360，L2 90-270
```

- `exact_*` oracle；`tag_ok` 真实 L2-only 哈希；公开成功以 `tag_ok` 判，`exact` 仅作 oracle 统计但报告两者
- **预算冻结**：`90 块` 时 `L1 90+base 90+stage1≤90+stage2≤90=180-360 硬帽360，L2 90-270`，`base` 兼 old 不重复

## 3. 数据就绪门（已 PASS，decoder-free，G1-G7 分层，authoritative）

| 门 | 检查项 | 冻结结果 (2026-08-28 intake 3/3 READY) |
|---|---|---|
| G1 | 文件可读 | **PASS** per source — pairs.parquet 行数=frames×256 (545280/1312000/1411328) 已验，每列 uint8/uint16 合法 |
| G2 | provenance 完整 | **PASS** per source — session_id + date≠2026-01-21 + `.ttbin/.1.ttbin` 双文件 sha256/size/mtime 完整可追溯 |
| G3 | 各 stratum 明确 | **PASS** — D_target 三源各一 session (`1M_600k_0dB / 1p5M / 2M_1.2M_0dB`) 冻结标签，非同分布 2026-01-21 |
| G4 | 256/frame 1024/block | **PASS** per source — 每帧256 pairs 每块4连续帧1024 pairs `BLOCK_LENGTH=1024`，frame_id×pair_idx 排序无缺失，0..1023 范围 |
| G5 | 与 V13 及 V48-V54 完全独立 | **PASS** per source — 三源为 2026-01-23/2026-01-07 新采集 session，与 V13 全集及 V48-V54 已用区间零重叠 |
| G6 | V25 prior 只读 | **PASS** 全局 — `channel_counts.npz` 形态校验，不读新 TEST 做训练，`load_v25_channel_counts()` 可 import |
| G7 | 冻结 authoritative registry | **PASS** — K=2127/5122/5510 ≥30，`index_j` 分散选 30/source，两两 gap≥4，与已用零重叠，可机械校验；`v55_authoritative_registry.json` 已 freeze |

- 三源全 PASS ⇒ `QUALIFICATION_PLAN_READY` (已达成)，等待独立 plan review
- 本轮脚本 `workspace/v55_intake_20260828/v55_decoder_free_intake.py` 已执行 decoder-free 分支，零 `decode_*` 调用；`G1-G7` 已由 `intake_compact_evidence.md` 紧凑记录

## 4. 预算（已冻结，180-360 硬帽360，authoritative 90-block）

- `L1 90` 固定（每块 1 次 `H1→BP→P(U2)`，共享于三阶段）
- `base L2 90` 固定（每块 1 次 `H_base`）
- `stage1 L2 0–90` 条件（仅 `!verify_base` 者）
- `stage2 L2 0–90` 条件（仅 `!verify_base && !verify_stage1` 者）
- 总 `90 L1+90 base+0–90 stage1+0–90 stage2 =180–360 硬帽360，L2 90–270`，`per block 2-4 calls`，`base` 兼 old 不重复

## 5. 门禁与效应（已冻结，70/90 + 20/30 + undetected==0，主判 base→Δ16）

对 `90-block` authoritative 独立跨 session TEST 判定 (30/source)：

- **计数**：`base_exact_full` 与 `verify_base` 分别计数（禁止假定相等），`stage1_exact_full` 与 `verify_stage1` 分别，`final_exact_full` 与 `verify_final` 分别；`stage1_rescued = rescued_by_inc1`、`stage2_rescued = rescued_by_inc2`；`N_stage1_attempted=count(!verify_base)`、`N_stage2_attempted=count(!verify_base && !verify_stage1)`；分母禁止 `SB-base_exact`
- **分层**：各源各自 `base/stage1/final/rescued_stage1/rescued_stage2` 与 `leakage/rescue_rate`，主要报告按源分层 + coverage 汇总；`base/stage1` 仅分层报告不作主判
- **泄漏（三类+平均+总量，分层）**：`first_pass_success_leak=leak_base (1064/1094/1104)`；`stage1_success_leak=leak_stage1 (1104/1134/1144)`；`stage2_leak=leak_stage2 (1144/1174/1184)`（stage2 成功与最终失败同为 `leak_stage2`）；`per_source_avg[s]=leak_base[s]+40×N_stage1[s]/30+40×N_stage2[s]/30`，`coverage_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/90`；`failed_conditional=leak_stage2`；`avg_disclosure_per_attempted=coverage_avg/1024` 描述性；`total_disclosed_bits=Σ leak_total` 与 `disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null）`
- **矩阵**：每源 `base_rank==m2, joint1_rank==m2+8, total_rank==m2+16, nested_stage1==True, nested_stage2==True, independence_1==8, independence_2==8, row≤16`；`E_inc1/E_inc2` 报告
- **Tag**：`tag_ok` 真实接受率 per stage per source，`G3' undetected==0` 单独表（全局）
- **预注册门禁（冻结，authoritative 90-block）**：

```
QUALIFICATION_PLAN_READY 已达成 (G1-G7 全 PASS)
若 完整性/守卫/秩/嵌套/重叠/记账失败 → V55_EVIDENCE_INVALID 优先
else if coverage final_exact_full ≥70/90 (77.8%) ∧ 每源 final_exact_full ≥20/30 (66.7%)
        ∧ undetected==0 全局 ∧ rank/nested/verification/记账通过
     → V55_INDEPENDENT_TEST_PASS (仅称 independent cross-session qualification evidence)
else → V55_INDEPENDENT_TEST_FAIL (完整性通过但未过门禁)
```

- **主判**：完整 `base→Δ8→Δ16` (即 `final` base→Δ16)，`stage1 (Δ8)` 报告不取代最终；`base/stage1` 仅分层报告
- `Wilson 95%`/`rescue_rate`/`runtime`/`leakage` 仅报告（按源分层 + coverage），不作门禁
- 不扩大为 FER/阈值/SKR/安全/资格/晋升，不宣称同分布复现

## 6. O3 配对语义与预注册统计（分层，authoritative）

- 同源同 `block` 的 authoritative 样本 `(idx,alice,bob)` 每块确定性一次（4帧窗口 `frame_ids[4]`），`L1` 单次生成 `q_i` 与 `P_i(U2)`，`base` → `stage1`（仅 `!verify_base`）→ `stage2`（仅 `!verify_after_stage1`）条件递进，同 `bob`/`P_i(U2)`/`s` 的嵌套前缀，`exact` 仅 oracle 统计
- 跨块/跨臂 outcome 差异为诊断量，永不作完整性失败
- 预注册统计：coverage `70/90` 与 per-source `20/30` 的 Wilson 95% 下界将按 coverage 与 per-source 分别报告，但**不作门禁**；仅分层硬门禁作判定

## 7. 科学 preflight、守卫序、执行偏差防复发（已冻结，未来执行前）

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `efd34ef...` + authoritative registry `84d62779`）；四文件 SCOPED dirty（含 `v55` 模块、`v55` CLI、`v38`、`v35`）；G1-G7 未过即拒（当前已 PASS）；输出根已存在即拒（J7）；任一拒绝零 calls 不建文件
2. **科学 preflights（decoder-free, write-free，未来执行前）**：G1-G7 全检（authoritative 90-block 可达 `K≥30` 已验）+ `H_base` 三矩阵与 committed v38 常量 `rank/support` 比对 + `H_inc1/H_inc2` 确定性重建与 `rank_total==m2+16 / nested / independence==8 / row≤16 / col≤1 / E≈96 / leak+40+40` 校验 + TRAIN counts 形态校验 + authoritative `frame_ids/ordinal` 每源 `30` 块分散 gap≥4 校验 + 每源首块哨兵 `L1→P_i(U2)` 通路
3. **执行偏差防复发（冻结）**：
   - 不使用 600s 外部 timeout；建议 `--timeout` 至少 `3600s` 或不设外部 timeout（decoder 内部 `90/1.0` 早停已限时）
   - 若执行返回 `session/cell ID`，只轮询同一 `session/cell ID` 进程状态，禁止 `restart`/`recreate` 新 session
   - 中断保留 raw partial 不聚合、不自动重跑
4. **Preflight 失败** → 写 `v55_invalid_notice.json` + 空 records + `v55_summary.json` (terminal `V55_EVIDENCE_INVALID` 或 `V55_DATA_NOT_READY` 分层) 后零 decoder calls 停止
5. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前

## 8. 记录、聚合、summary（预冻结，未来执行，authoritative 分层）

每 L2 call record schema（含 `tag_scope=l2_only, arm∈{base,stage1,stage2}, stratum`）：

```
call_id, source/stratum(1M_600k_0dB/1p5M/2M_1p2M_0dB), block_id, arm(base/stage1/stage2), pass_index(1/2/3), used_inc1(bool), used_inc2(bool),
matrix_id(base/joint1/total), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode(authoritative),
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or 1104/1134/1144 or 1144/1174/1184), leak_stage1, leak_stage2, status, runtime_s
```

Summary 含：记账 `base_exact_full` 与 `verify_base` 分别计数（per source & coverage 90）、`stage1_exact_full` 与 `verify_stage1` 分别、`final_exact_full` 与 `verify_final` 分别、`stage1_rescued / stage2_rescued / final`、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_stage1&&!verify_base)`（per source & coverage）、`rescue_rate_stage1/stage2` per source、`per_source_avg` 与 `coverage_avg`、`Wilson 95%` per source & coverage、`total_disclosed_bits` 与 `disclosure_per_final_exact_block` 等描述性；`Δleak_per_source`，`Δleak_coverage`；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance；L1 诊断；四类计数；G3'；门禁明细（`final` 的 per-source 20/30 与 coverage 70/90 数值与 `V55_*` 终态）；`Wilson 95%`；paired `base vs stage1 vs final` per block 描述性；`intake` 三源仅背景描述

## 9. 证据写出（预冻结，未来执行，不在本轮）

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v55_two_stage_rescue_independent_test/run_01/
```

文件：`v55_records.json/.csv` (90 块对应 `90-270` L2行：`90 base + ≤90 stage1 + ≤90 stage2`；总 calls `180-360` 硬帽360)、`v55_summary.json`（分层）、`v55_invalid_notice.json`（失败时）、`v55_data_readiness.json`（G1-G7 已 PASS per source）。CSV/JSON 行对等；禁写 NPZ. **本轮 P0 不创建上述输出**，仅在 `intake_compact_evidence.md` + `v55_authoritative_registry.json` 报告 G1-G7 与 authoritative 90-block 冻结。

## 10. 实现草图（后继轮次，当前未授权，需独立 plan ACCEPT + EXECUTE_AUTH）

- `comparison_bench/src/comparison_bench/formal_ir/v55_two_stage_rescue_independent_test.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现确定性 `H_inc1 det1` 复用 + `H_inc2 det2` 新增 + authoritative `90-block` 独立跨 session 读取 (per source `30` 块分散，两两 gap≥4，frame_ids 已冻) + 三阶段条件 runner (per block `base 1+条件 stage1 ≤1+条件 stage2 ≤1`，总 `180-360` 硬帽360，分层预算)
- `scripts/execute_v55_independent_test.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan `efd34ef...` + authoritative `84d62779`）；四文件 SCOPED dirty；G1-G7 全 PASS 已验；budget 硬帽 `90` 块三阶段条件执行 180-360；执行偏差防复发（不设 600s timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑）；任一 gate 失败非零退出
- 仅 fake-runner 测试通过后才可进入正式 TEST；不以 outcomes 定增量或调 `Δm`

## 11. 自由裁量 D1–D11（修订至 QUALIFICATION_PLAN_READY）

- D1 完全冻结 V54 方法（H1/L1-APP/Lane C/H_inc1/H_inc2/decoder/prior/verification 零改），V55 不新增矩阵/标签/prior/阈值
- D2 单一二阶段 `Δm=8+8` per source 嵌套 rescue，`90-block` `base vs stage1 vs final` 三阶段配对（未来执行，分层 authoritative）
- D3 Intake 3/3 READY 已固化，G1-G7 全 PASS，authoritative 90-block 已冻，`QUALIFICATION_PLAN_READY` 已达成
- D4 authoritative `90-block` 注册算法：每源 `[0..F-4]` 枚举 `K=F-3`，`index_j=floor(j*(K-1)/29)` 分散选 30/source，gap≥4，frame_ids 已冻，禁换块
- D5 预算 `180-360` 硬帽360 (`90+90+≤90+≤90`)，`base` 兼 old 不重复，已冻结
- D6 预注册门禁：`coverage 70/90 ∧ per-source 20/30 ∧ undetected==0`，`base/stage1` 仅分层报告，最终 `base→Δ16` 主判；`Wilson/rescue/runtime/leakage` 仅报告；PASS 仅 independent cross-session qualification evidence
- D7 哨兵每源首块单 L1 通路（未来执行）
- D8 终态 `V55_EVIDENCE_INVALID / V55_INDEPENDENT_TEST_PASS / V55_INDEPENDENT_TEST_FAIL`，`QUALIFICATION_PLAN_READY` 为已就绪态 (此前 `DATA_NOT_READY` 已解决)
- D9 执行偏差防复发：不设 600s timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑
- D10 `90-block` 独立跨 session TEST 确认规模 (30/source，77.8% coverage 门禁)，通过仍仅独立跨 session 资格确认，不扩大为全域 FER，不宣称同分布复现
- D11 文件集条件行记录+聚合+效应+provenance，authoritative 90-block 分散 `K/index_j` 与 `frame_ids` 逐块冻结；本轮仅交付四工件+compact intake 证据
