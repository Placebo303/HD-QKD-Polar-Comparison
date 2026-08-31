# OpenSpec Spec: formal-ir-v65ar2-first-match-pipeline

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + decoder-free 流水线框架，不改主候选/V64/src，不运行真实流水线
**Change**: `formal-ir-v65ar2-first-match-pipeline` (`V65AR2`, branch `formal-ir-mainline`, HEAD `9625afb4...→新SHA`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v65-new-session-channel-compatibility` (`V65` `9625afb4 PLAN_REVISE_REQUIRED`) — V65AR2 将分散的 Phase R + Stage0/1/2 合并为确定性 first-match/stop-on-failure 流水线，候选顺序与 tier 冻结，速率不 cap 分支

## 1. 变更类型与生命周期

- **Type**: `PIPELINE_FREEZE` — decoder-free metadata recovery 与三阶段验证合并为确定性定序流水线（Phase R additive → Stage0 4+4 first-match → Stage1 256/64 → Stage2 1024/256+TEST32 seal，first-match/stop-on-failure，不按统计换候选，速率不 cap 分支）。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + `scripts/v65ar2_pipeline.py` 框架（`rg "decode_" 0 hits`, `py_compile PASS`），**不实现 runner，不执行 decoder，不创建 `run_01`，不读真实 raw TTBin，不跑真实流水线**；正式流水线执行需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`；**推送新 SHA 后停止等待审核**。
- **Branch**: `formal-ir-mainline`；`HEAD` `9625afb4...` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞；本次推送新 SHA 后停止不自行进入 EXECUTE。
- **Data SHA**: `84d62779` (`d=1024 bw=200 pairing=nearest rule=legacy_v1`) — V65AR2 延续单点，仅新增 Phase R additive 重建逻辑，不换处理点。

## 2. 冻结语义 — 候选、tier 与处理点零改

### 2.1 候选与 tier 冻结（V65AR2 完全冻结）

- `candidate_order = ["162148", "2500K", "160254"]` 定序 first-match 冻结，禁止按 `CE/H/ΔNLL/MAP/m_req` 统计重排、跳序、回退、递补亚军。
- `provenance_tier = {A,B,C}` per candidate 冻结，与 `candidate_id` 一一绑定，不按阶段统计升降级，不跨 tier 共享 sidecar。
- `selected = 首个 Stage0 PASS 的 candidate`，三候选全 FAIL → `STAGE0_NO_CANDIDATE`，不以 `CE` 最优递补。
- `n=1024, q=1024, log2Q=5 per plane, f_target=1.3, FRAME=256, BLOCK=4×256=1024, period 204800ps, threshold 40000ps, gate 200ps` 全冻。
- `m_frozen = 16 / 184/190/192 / 200/206/208(L2)/216/222/224(full)` 仅对照，V65AR2 不改；`leak_frozen=1144/1174/1184` (5*(16+m2)+64) 同。
- `V65` 单候选多源验证与 `V65AR2` 多候选 first-match 流水线正交，终态独立，不继承 `READY_FOR_V66`。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024消歧, rule legacy_v1, channels A1/B5, threshold/gate/period` 单点，三候选一致处理但 per candidate provenance 分别记录 `delay/peak/sigma`（Phase R additive 独立重建）。
- `TEST32` 密封：`32 frames 8192 pairs 8 blocks` 仅 identity，不计任何 `H/CE/NLL/MAP` 统计；`C_ab/P_global/λ` 均 `CAL`-only；`used_test_in_estimation==False` 每阶段校验。
- `V64 22/24` 与 `V65` 结论：仅作背景对照，V65AR2 独立验证不复用其统计。

### 2.3 禁止

- 禁按统计重排候选、跨 tier 共享 sidecar、复用冲突 sidecar、改 raw、搜 channel pair、调 `decode_*`、将 `RATE_ADAPTATION_REQUIRED` 误判为候选失败、将 `FULL_DISCLOSURE_LAYER` 误判为 `RATE_ADAPTATION`、将 `TEST32` 统计用于阈值、将 Stage1 FAIL 后仍进 Stage2、将 second estimator 作门禁、将 `m_total≤200/206/208` 当总量门禁、改 `src/experiments/tools` 任何文件（只读复用）；禁读 `TEST32` 统计；`λ` 触界禁扩网格；禁 `V55 90 / V48-V65 (source,session,frame)` 复用；未授 `EXECUTE_AUTH` 前禁真实流水线与 `decode_*`。

## 3. Phase R — decoder-free metadata recovery（additive sidecar）

### 3.1 输入输出（additive，不覆盖 raw）

| 集合 | 来源 | 帧/块 | pairs | 说明 |
|---|---|---|---|---|
| Raw TTBin | `candidate_raw_root/*.ttbin` | per candidate 可变 | per candidate 可变 | 候选自身原始 timetags，二进制不可改 |
| Routing contract | `acquisition_routing.yaml` | per candidate 1 contract | — | `source→session→channel_pair→delay_sign→gate/threshold` 契约，含 `contract_hash` |

- **输出**：
  - `sidecar_additive.json` per candidate：`{candidate_id, tier A/B/C, contract_hash, raw_hash, delay_used_ps, peak_center, sigma, gate 200, threshold 40000, frame_anchor, mapping legacy_v1, channel_pair, reconstructed_at, reconstruction_rule="additive_only", reused_conflicting_sidecar=False, raw_untouched=True}`
  - `v65ar2_phase_r.json`：`{per_candidate {status PASS/FAIL, guards {reused, modified, searched, decoded}}, overall_phase_r, contract_hash, raw_hashes}`
- **Additive 语义**：仅缺失字段补充；已含且与 contract 一致则校验通过不覆盖；已含但与 contract 冲突→ `PHASE_R_FAIL`（`EVIDENCE_INVALID` 更高优先级时归入其）；`rg "decode_" 0 hits`，不调用 decoder，不改 raw 二进制（`raw_hash` 重算一致）。

### 3.2 Phase R 校验（decoder-free，G1 前置）

| 门 | 校验 | 失败归属 |
|---|---|---|
| R1 | `contract_hash` 可回溯且 `tier∈{A,B,C}` per candidate | 缺失→`EVIDENCE_INVALID` |
| R2 | `raw_hash` 与 `candidate_id` 绑定且 `raw/*.ttbin` 可读 | 缺失→`PHASE_R_FAIL` |
| R3 | `sign(delay)==sign(peak) && |delay-peak|<50ps` | 失败→`G1 FAIL` (计入 Stage0 G1) |
| R4 | `sigma∈[50,150] && gate==200 && threshold==40000` | 失败→`G1 FAIL` |
| R5 | `reused_conflicting_sidecar==False` | 违则 `EVIDENCE_INVALID` |
| R6 | `raw_untouched==True` (hash 重算一致) | 违则 `EVIDENCE_INVALID` |
| R7 | `channel_pair==contract.channel_pair` (非扫描最优) | 违则 `EVIDENCE_INVALID` |

- **Phase R PASS**：`R1..R7 全过` per candidate（`EVIDENCE_INVALID` 项任一违即 overall `EVIDENCE_INVALID`）。
- **Stop-on-failure**：`PHASE_R_FAIL` 的候选 → `Stage0 UNREACHABLE_R`，但不影响其他候选 Phase R 独立判定；若 `overall_phase_r` 无任一候选 PASS → `overall = V65AR2_PHASE_R_FAIL`，Stage0/1/2 整体 `UNREACHABLE`。

## 4. 流水线 — first-match / stop-on-failure 定序

### 4.1 阶段样本定义

| 阶段 | 输入 | 帧/块 | pairs | 零重叠键 |
|---|---|---|---|---|
| Stage0 | 每候选 `CAL 4 blocks + VAL 4 blocks` | 8 blocks =32 frames | 8192 | `CAL_key∩VAL_key==∅ && ∩(V13..V65)_key==∅` |
| Stage1 | 仅 selected `CAL 256 + VAL 64` | 320 frames =80 blocks | CAL 65536 + VAL 16384 | 同上，独立于 Stage0 |
| Stage2 | 仅 Stage1 PASS 的 selected `CAL 1024 + VAL 256 + TEST32 seal` | 1312 frames =328 blocks (+8 seal) | CAL 262144 + VAL 65536 + TEST 8192(seal) | 同上，`TEST32` 仅 identity |

- `FRAME=256 pairs, BLOCK=4×256=1024 symbols (=1024 pairs)`，`frame_id∈[0,F_s-1]` 连续但跳过 forbidden 后仍每帧 256 校验；`BLOCK` 仅 4 连续帧完整才计数。
- 每阶段 `C_ab/P_global/λ/CE` 独立重算，不共享 `λ*`，不缓存 `C_ab` 跨阶段；`F_s` 不足则该阶段 `STAGE*_FAIL (insufficient frames)`。
- `TEST32` 仅 identity（`session_id, frame_ids[32], blocks 8, pairs 8192`），`assert not used_test_in_estimation` 每阶段校验。

### 4.2 定序状态机与优先级

```
Phase R (per candidate 独立)
  │ PASS
  ▼
Stage0 4+4 (按 candidate_order 定序) ──▶ FAIL → next candidate Stage0
  │ 首个 PASS = selected                    (三全 FAIL → STAGE0_NO_CANDIDATE)
  ▼
Stage1 256/64 (仅 selected) ──▶ FAIL → STOP, Stage2 UNREACHABLE
  │ PASS
  ▼
Stage2 1024/256+TEST32 (仅 Stage1 PASS) ──▶ 分支 RATE_ADAPTATION / FULL_DISCLOSURE / READY
任一步 FAIL → 该分支后续 UNREACHABLE，不回退，不以 CE 最优递补
```

**总体优先级（高→低，exclusive）**：
```
EVIDENCE_INVALID  (provenance伪造/frame 256/CE链式/复用冲突 sidecar/改 raw/搜 pair)
> PHASE_R_FAIL
> STAGE0_NO_CANDIDATE
> STAGE1_FAIL
> STAGE2_FAIL  (G1-5/G8)
> FULL_DISCLOSURE_LAYER  (∃ layer m_req≥1024)
> RATE_ADAPTATION_REQUIRED (∃ layer m_req> frozen && ∀ layer m_req<1024)
> READY  (全 G1-8 PASS && m_req within frozen)
```

## 5. 估计器 — 单一预注册 hierarchical (per stage 独立, CAL-only, λ 4-fold)

### 5.1 C_ab 与 P_global (per stage per candidate, CAL-only)

```
C_ab[stage][a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum = N_cal
  Stage0: N_cal=4096 (CAL 4 blocks)
  Stage1: N_cal=65536 (CAL 256 frames)
  Stage2: N_cal=262144 (CAL 1024 frames)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, n=1024, per plane log2Q=5
```

### 5.2 层级先验与熵/CE (CAL 描述性 + VAL 门禁性，链式双校验)

```
P_λ(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  (N_b>0); P_global(a)  (N_b==0)
P_λ(u1|b) = Σ_{u2} P_λ(32*u1+u2 | b)  32×1024
H_λ(U1|B)_cal = -Σ_b P_emp_cal(b) Σ_{u1} P_λ(u1|b) log2  (描述性)
H_λ(A|B)_cal = -Σ_b P_emp_cal(b) Σ_a P_λ(a|b) log2  (描述性)
H_λ(U2|U1B)_cal = H_λ(A|B)_cal - H_λ(U1|B)_cal;  |H-H1-H2|<1e-9 else EVIDENCE_INVALID

CE1(λ*) = -E_VAL[ log2 P_λ*(U1|B) ]  (门禁性, VAL 上)
CE2(λ*) = -E_VAL[ log2 P_λ*(U2|U1,B)] (门禁性)
CE_full(λ*) = -E_VAL[ log2 P_λ*(A|B)] (门禁性)
CE 链式: |CE_full - CE1 - CE2| < 1e-9 else EVIDENCE_INVALID / G8 FAIL

m1_req = ceil(1.3*1024*CE1/5), m2_req = ceil(1.3*1024*CE2/5)  (不 cap, raw)
m_total_req = m1_req + m2_req, Δm1=m1-16, Δm2=m2-{184,190,192}
```

### 5.3 λ 搜索 (预注册, 不扩网格, 触界→MODEL_NOT_STABLE)

```
search_domain = log10 λ ∈ [-2, 4]  continuous  (λ∈[1e-2,1e4])
Cal-CV: split CAL → 4 folds
  Stage0: 4 blocks → 4 folds 各1 block (1024 pairs/fold)
  Stage1: 256 frames → 4 folds 各64 frames (16384 pairs/fold)
  Stage2: 1024 frames → 4 folds 各256 frames (65536 pairs/fold)
  CV_NLL(λ) = mean_k mean_{(a,b)∈fold_k} [-log2 P_λ^{(train_k)}(a|b)]
λ* = argmin CV_NLL(λ) via 50-point log grid + bounded refine
trace = {logλ_grid[50], CV_NLL_grid, λ*, CV_NLL*}
at_boundary = (log10 λ* ≤ -2+ε) || (log10 λ* ≥ 4-ε) ε=1e-6 → G2 FAIL
```

- `CV_NLL` 仅 `Cal` 内 `4-fold` 平均，`Val NLL/CE` 不反哺；`λ*` 落边界直接 `STAGE*_FAIL (MODEL_NOT_STABLE)`，禁扩至 `[-3,5]`；第二 estimator 禁止作门禁。

## 6. 速率分支 — m_req 不 cap 显式语义（非候选失败）

```
m_i_req = ceil(1.3*1024*CE_i/5)  # n=1024, f=1.3, log2Q=5
# 不经 min(16,..)/min(192,..)/min(1024,..) 截断，显式 m_req_raw
```

| 条件 (per layer) | 分支 | 语义 |
|---|---|---|
| `m1_req≤16 && m2_req≤184/190/192 && m_total≤216/222/224` | `WITHIN_FROZEN_BUDGET` | 落在冻结构内 |
| `∃ i: m_i_req> frozen_i` 且 `∀ i: m_i_req<1024` | `RATE_ADAPTATION_REQUIRED` | 需增量冗余/母码重构，非候选失败 |
| `∃ i: m_i_req≥1024` | `FULL_DISCLOSURE_LAYER` | 该层全披露，当前码族不可行 |

- **禁止 cap 伪装**：`m_req_raw` 显式 `>16/>192` 即对应分支，禁 `min(16, ceil(...))` 截断后宣称 `WITHIN`；每层独立 `≥1024` 即 `FULL_DISCLOSURE`，不以总量平均。
- **候选失败隔离**：`RATE_ADAPTATION / FULL_DISCLOSURE` 不作 `G6/G7 FAIL` 的候选失败混淆；候选失败仅由 `G1-5/G8` 定义；Stage0 小样本 `m_req` 仅 early screening 不触发速率分支。

## 7. 每阶段报告 (per stage, TEST 仅 identity)

- **报告 schema** per stage per candidate（Stage1/2 仅 selected）：
  ```
  sample: {N_cal/frames, N_val/frames, N_test identity 32 frames (=8 blocks) 仅 Stage2, effective_contexts, zero_cells_cal}
  prior: {λ*, at_boundary, CV_NLL*, Val_NLL/CE_full, ΔNLL, search_trace}
  entropy_descriptive: {H_cal, H1_cal, H2_cal, chain_delta_H}
  cross_entropy_gating: {CE1, CE2, CE_full, chain_delta_CE}
  generalization: {MAP_acc_val, q_mass_unseen, effective_contexts, zero_frac}
  budget_gating: {m1_req=ceil(1.3*1024*CE1/5), m2_req=ceil(1.3*1024*CE2/5), m_total_req, Δm1_vs_16, Δm2_vs_{184,190,192}, rate_branch per layer, leak_req=5*m_total_req+64}
  gates: {G1..G8, G7_aux, PASS/FAIL/UNREACHABLE, fail_gate}
  ```
- **TEST32 仅 identity**：`TEST32 {session_id, TEST_frames[32], blocks 8, pairs 8192, sealed_at} (= Stage2 seal)` 不含 `H/CE/NLL/MAP/unseen/m`，`assert not used_test_in_estimation` 且 `assert seal_not_used_in_threshold`。

## 8. 门禁 G1-8 (per candidate per stage 独立, 预注册阈, 不平均)

| 门 | 条件 (per candidate per stage) | 阈值 frozen |
|---|---|---|
| G1 | `contract_consistent (算法+sign/50ps)` | `dimension 1024/bins/pairing legacy_v1/channels/frame anchor/mapping 每帧256` 算法一致 且 `sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150] && gate==200 && threshold==40000` |
| G2 | `λ_at_boundary==False` | `log10 λ* ∈ (-2,4)` 开区间 |
| G3 | `ΔNLL ≤0.50` | bits/symbol |
| G4 | `Val_NLL ≤ H_cal+1.0 && isfinite` | bits/symbol (H_cal 仅此 bound) |
| G5 | `unseen ≤1%` | `q_mass_unseen ≤0.01` |
| G6 | `m1_req ≤16` (Stage0 early screening; Stage1/2 对照但超阈入速率分支) | `m1=ceil(1.3*1024*CE1/5)` raw 未 cap |
| G7 | `m2_req ≤200/206/208` (per source 三档) | `m2=ceil(1.3*1024*CE2/5)` |
| G7-aux | `m_total_req ≤216/222/224` | `m_total=m1+m2` 辅助总量 |
| G8 | `provenance_zero_overlap && CE_chain_closed` | `CAL_key∩VAL_key==∅ && CAL∪VAL_key∩TEST_key==∅ && CAL∪VAL∪TEST_key∩(V13..V65)_key==∅ (key=(source,session,frame)) && |CE_full-CE1-CE2|<1e-9` |

- `PASS_stage = G1..G8(含 G7-aux) 全 True`，任一 `False` 则 `PASS_stage=False`；Stage1/2 的 `G6/G7` 超阈不判 `PASS=False` 而入速率分支（`G6/G7` 对照分支），`G1-5/G8` 失败才判 `STAGE*_FAIL`。
- `H 链式差>1e-9` → `EVIDENCE_INVALID`，`CE 链式差>1e-9` → `G8 FAIL`。

## 9. 总体终态与 UNREACHABLE 语义

```
if materialization/chain/frame256/provenance fabricated or reused_conflicting_sidecar or modified_raw or searched_channel_pair:
    overall = V65AR2_EVIDENCE_INVALID
elif not exists candidate: Phase R PASS:
    overall = V65AR2_PHASE_R_FAIL
elif forall candidates: Stage0 FAIL:
    overall = V65AR2_STAGE0_NO_CANDIDATE
elif selected Stage1 FAIL (G1-5/G8):
    overall = V65AR2_STAGE1_FAIL
elif selected Stage2 FAIL (G1-5/G8):
    overall = V65AR2_STAGE2_FAIL
elif exists layer: m_req≥1024:
    overall = V65AR2_FULL_DISCLOSURE_LAYER
elif exists layer: m_req> frozen && m_req<1024:
    overall = V65AR2_RATE_ADAPTATION_REQUIRED
elif forall stages PASS && m_req within frozen:
    overall = V65AR2_READY
```

- `UNREACHABLE` 标记：`Phase R FAIL → Stage0 UNREACHABLE_R`；`Stage0 全 FAIL → Stage1/2 UNREACHABLE`；`Stage1 FAIL → Stage2 UNREACHABLE`，落盘 `per_phase {status PASS/FAIL/UNREACHABLE, reason, rate_branch}`。
- `selected` 不以 `CE` 最优递补；`Stage1/2` 速率分支不回退重选候选。
- `TEST32` 与 Stage2 同生死：Stage2 `UNREACHABLE` 时 `TEST32` 亦 `UNREACHABLE`，不 seal。

## 10. 脚本与证据写出 (预冻结, decoder-free)

- **固定脚本**（本轮仅冻结计划，框架可 `dry-run`）：
  - `scripts/v65ar2_pipeline.py`: `Phase R additive → Stage0 4+4 first-match → Stage1 256/64 → Stage2 1024/256+TEST32 seal`，`rg "decode_" 0 hits`，`py_compile PASS`，`m_req_raw` 未 cap，`TEST` 未用，`λ` 触界不扩，`CE 链式` 已验，`UNREACHABLE` 语义已验。
- **增量根**（未来实现，`--dry-run` 已可框架自检，正式执行前需 `EXECUTE_AUTH`）：
  ```
  openspec/changes/formal-ir-v65ar2-first-match-pipeline/  # 本轮 4 工件 + registries + report 模板
  scripts/v65ar2_pipeline.py  # decoder-free 流水线框架
  comparison_bench/outputs_comparison/formal_ir_methods/v65ar2_pipeline/  # 未来正式执行时 run_01 (本轮不建)
  ```
- **文件**：`v65ar2_data_registry.json` (authoritative per candidate Stage0/1/2 帧表，含 `candidate_order`, `tier`, `zero_overlap_verified`) + `v65ar2_test_registry.json` (Stage2 `TEST32` seal identity) + `v65ar2_phase_r.json` (Phase R guards) + `v65ar2_pipeline_result.json` (per candidate per stage H/CE/λ/NLL/MAP/m_req/G1-8 + overall 五态+分支+UNREACHABLE) + `v65ar2_manifest.json` (H provenance + λ轨迹 + m_req 差额 + CE 链式 + rate_branch + contract_hash) + `V65AR2_PIPELINE_REPORT.md` (分层，TEST32 仅附录，不含统计) + `v65ar2_invalid_notice.json` (失败时)。CSV/JSON 行对等；本轮仅冻结计划，不创建正式 run_01 decoder 输出。

## 11. 守卫与验收

- **本轮 plan 自检 gate**：`py_compile PASS` 脚本，`rg "decode_" 0 hits`，`rg "reuse.*sidecar|search.*channel" 0 hits` 为冲突复用/搜 pair，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0` (除本变更 + `scripts/` 外零改)，`TEST` 未读统计已验 (`used_test_in_estimation==False`)，`λ` 预注册 `[-2,4]` 且触界即 `MODEL_NOT_STABLE` 不扩已验 (`search_trace` 落盘)，`m_req_raw` 未 cap 伪装已验 (`grep "min(16" 0 hits` 且 `m_req≥1024→FULL_DISCLOSURE 层<1024超旧→RATE_ADAPTATION` 已验)，`G1-8(含 G7-aux)` per candidate per stage 已验（含 `sign/50ps` + 零重叠 + `CE 链式 |CE_full-CE1-CE2|<1e-9`），`overall` 优先级 + `UNREACHABLE` 已验，`candidate_order 162148→2500K→160254` 冻结已验 (`rg "sort.*CE" 0 hits`)，`tier A/B/C` 冻结已验，`Phase R additive` + 禁令三项已验，`DECODE_FREE` 保持已验，`run_01` 不存在已验。
- **本轮仅 plan 四工件**，任何 fresh 流水线实估计需新 SHA + `v65ar2_data_registry.json` 实表 + `CE1/CE2` 速率分支已验后、且独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODE_FREE` 保持至授权。
