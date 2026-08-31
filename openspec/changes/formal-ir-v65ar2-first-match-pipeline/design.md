# OpenSpec Design: formal-ir-v65ar2-first-match-pipeline

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **decoder-free first-match/stop-on-failure 流水线冻结：Phase R additive sidecar → Stage0 4+4 首 PASS → Stage1 256/64 → Stage2 1024/256+TEST32，候选顺序与 tier 冻结，不按统计换候选**
**Cycle**: `V65AR2` (first-match-pipeline), predecessor `V65` `formal-ir-v65-new-session-channel-compatibility` `9625afb4 PLAN_REVISE_REQUIRED`
**Branch**: `formal-ir-mainline` HEAD `9625afb4... → 新 SHA` (`git rev-parse HEAD == origin/formal-ir-mainline` 重核) data SHA `84d62779` (1024/200ps/nearest/legacy_v1 单点，V65AR2 仅增 Phase R additive 重建)
**Feasibility**: `V65` 已冻结 `H1-16+L1APP+Lane C m2 184/190/192+Δ8+Δ8+full-tag` 方法与 `A/B/C tier` contract 语义；`V56` 已固化 `ttbin→pair→symbol` 权威算法可只读复用；`V64 22/24 PASS` 已证 full-tag 单 64b 可行；`V65AR2` 仅将分散的 `decoder-free metadata recovery + Stage0/1/2` 合并为**确定性定序**，零 `decode_*` 调用闭环
**Key judgement**: **分散的阶段验证会诱发“按统计换候选/复用冲突 sidecar/搜 channel pair”三类静默偏差**；必须冻结顺序与 tier、Phase R 仅 additive 重建、流水线 first-match/stop-on-failure 不可达语义、速率不 cap 显式分支，才能使 научной结论可复现且不与 V65 冲突

## 1. 科学问题与关键判断

> 在**完全冻结 `162148→2500K→160254` 与 `A/B/C` tier** 下，能否以 **decoder-free** 方式从候选自身 raw TTBin 与 routing contract 重建可信 provenance，并按 **Phase R PASS → Stage0 4+4 首 PASS → Stage1 256/64 → Stage2 1024/256+TEST32** 的**确定性定序**验证通道兼容性与速率可行性，且 `m_req=ceil(1.3*1024*CE_i/5)` 不 cap 地显式分支 `RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER`，`TEST32` 全程仅 identity？

- **对照**：`V65` 的 `CAL 4096+VAL512+TEST120` 是单候选多源验证；`V65AR2` 的 `4+4 / 256+64 / 1024+256+TEST32` 是**多候选 first-match 流水线**，阶段样本量递增，任一步 FAIL 即 STOP，不回退选“CE 最优亚军”。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame 256 A=32U1+U2 B=32V1+V2 / acquisition routing contract` 为跨阶段算法不变量；`delay/peak/sigma/gate/threshold` 为 Phase R 按 contract 独立重建量（additive）。
- **兼容性性质**：纯 **decoder-free**，每阶段独立 `C_ab → P_global → P_λ* → CE1/CE2 → m_req + 泛化统计 → G1-8`，`VAL` 独立于 `CAL`，`TEST` 全程不参与估计。

## 2. 冻结语义 — 候选、tier 与处理点零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| 候选顺序 | `162148 → 2500K → 160254` first-match 定序 | V65AR2 本变更冻结 |
| Provenance tier | `A / B / C` per candidate 冻结，不按统计升降 | acquisition routing contract |
| 流水线语义 | `first-match` (Stage0 首 PASS 即 selected) `stop-on-failure` (FAIL→后续 UNREACHABLE) | V65AR2 本变更 |
| n/d | 1024 | V31/V54/V64/V65 |
| 处理点 | `d1024 bw200 nearest legacy_v1 A1/B5 200ps` 单点 `84d62779` | V55 authoritative + V56 contract |
| 速率公式 | `m_i_req = ceil(1.3*1024*CE_i/5)` 不 cap | V65 `CE` 门禁延续，V65AR2 显式分支 |
| 旧容量对照 | `m1 16 / m2 184/190/192 / m_total 200/206/208 (L2) / 216/222/224 (full)` | V64 冻结，仅对照不改 |
| Stage 样本 | `Stage0 4+4 blocks / Stage1 256/64 frames / Stage2 1024/256 + TEST32` | V65AR2 本变更 |
| 泄漏 | `leak=5*(16+m2)+64` 三档 `1144/1174/1184` (V65AR2 仅对照，超容量分支另计) | V64 |

**禁令**：`SHALL NOT` 按 `CE/H/ΔNLL/MAP` 重排候选、跨 tier 共享 sidecar、复用冲突 sidecar、改 raw、搜 channel pair、调用 `decode_*`、将 `RATE_ADAPTATION_REQUIRED` 误判为候选失败、将 `TEST32` 统计用于阈值选择、将 `m_total≤200/206/208` 当总量门禁。

## 3. Phase R — decoder-free metadata recovery（additive sidecar）

### 3.1 输入与输出

- **输入唯一来源**：
  - `raw TTBin`：候选自身 `raw/*.ttbin`（`TimeTagger` 原始 timetags，二进制，不可改）
  - `acquisition routing contract`：`acquisition_routing.yaml`（`source → session_id → channel_pair(A1/B5) → delay_sign → expected gate/threshold` 的权威契约，版本化 hash）
- **输出（additive，不覆盖 raw）**：
  - `sidecar_additive.json` per candidate：`{candidate_id, tier, contract_hash, raw_hash, delay_used_ps, peak_center, sigma, gate 200, threshold 40000, frame_anchor, mapping legacy_v1, reconstructed_at, reconstruction_rule="additive_only"}`
  - `v65ar2_phase_r.json`：`{per_candidate {status PASS/FAIL, provenance_additive, delay_peak_sign_ok, sigma_ok, gate_ok, threshold_ok, contract_consistent}, overall_phase_r PASS/FAIL}`
- **Additive 语义**：
  - 仅当 raw 缺少 `delay/peak/sigma` 时补充；若 raw 已含且与 contract 一致则校验通过不覆盖；
  - 若 raw 已含但与 contract 冲突→ `PHASE_R_FAIL`（`EVIDENCE_INVALID` 优先级更高时归入其），不复用旧冲突 sidecar 的字段；
  - 重建过程 `rg "decode_" 0 hits`，不调用 decoder，不改 raw 二进制。

### 3.2 校验（G1 前置，decoder-free）

| 阶段 | 参数 | 校验 | 门禁 |
|---|---|---|---|
| R1 | contract 存在性 | `contract_hash` 可回溯且 `tier ∈ {A,B,C}` per candidate | 缺失→`EVIDENCE_INVALID` |
| R2 | raw 完整性 | `raw_hash` 与 `candidate_id` 绑定且 `raw/*.ttbin` 可读 | 缺失→`PHASE_R_FAIL` |
| R3 | delay/peak 一致 | `sign(delay)==sign(peak) && |delay-peak|<50ps` | 失败→`G1 FAIL` 归入 Stage0 G1 |
| R4 | sigma/gate/threshold | `sigma∈[50,150] && gate==200 && threshold==40000` | 失败→`G1 FAIL` |
| R5 | 冲突 sidecar 禁复用 | `provenance_additive` 不含 `reused_conflicting_sidecar` 标记 | 违则 `EVIDENCE_INVALID` |
| R6 | 未改 raw | `raw_hash` 重算一致 | 违则 `EVIDENCE_INVALID` |
| R7 | 未搜 channel pair | `channel_pair` 仅取 contract 值，非扫描最优 | 违则 `EVIDENCE_INVALID` |

- **Phase R PASS 条件**：`R1..R7 全过` per candidate（`EVIDENCE_INVALID` 项任一违即 overall `EVIDENCE_INVALID`，否则按 candidate 独立 PASS/FAIL）。
- **Stop-on-failure**：任一候选 Phase R FAIL → 该候选后续 Stage0/1/2 标记 `UNREACHABLE_R`，但不影响其他候选 Phase R 判定（候选间 Phase R 独立）。

### 3.3 选取理由

- `additive sidecar` 避免“冲突 sidecar 复用”导致的静默 provenance 污染；Phase R 仅重建缺失元数据，不参与 `CE/m` 估计，符合 `DECODER_FREE` 与最小可信恢复原则。
- `contract_hash` 绑定使重建可复现、可审计，且禁止 `search channel pair` 引入的事后择优偏差。

## 4. 流水线 — first-match / stop-on-failure 定序

### 4.1 阶段样本定义

| 阶段 | 输入 | 帧/块 | pairs | 说明 |
|---|---|---|---|---|
| Stage0 | 每候选独立 | `4+4 blocks` = 8 blocks = 32 frames | 8192 | 小样本快速门禁，首 PASS 即 selected |
| Stage1 | 仅 selected | `CAL 256 frames + VAL 64 frames` = 320 frames = 80 blocks | CAL 65536 + VAL 16384 | 稳定性验证，独立重算先验 |
| Stage2 | 仅 Stage1 PASS 的 selected | `CAL 1024 + VAL 256 + TEST32` = 1312 frames = 328 blocks | CAL 262144 + VAL 65536 + TEST 8192(identity only) | 主估计 + seal TEST32 |

- **BLOCK / FRAME**：`FRAME=256 pairs`, `BLOCK=4×256=1024 symbols (=1024 pairs)`，`frame_id∈[0,F_s-1]` 连续但跳过 forbidden 后仍每帧 256 校验；`BLOCK` 仅 4 连续帧完整才计数。
- **独立重算**：每阶段 `C_ab/P_global/λ/CE` 均独立于前阶段重算，不共享 `λ*`，不缓存 `C_ab` 跨阶段。
- **TEST 隔离**：`TEST32` 仅 identity（`session_id, frame_ids[32], blocks 8, pairs 8192`），`assert not used_test_in_estimation` 每阶段校验。

### 4.2 定序状态机

```
                ┌─────────────┐
                │  Phase R    │  per candidate 独立
                │  additive   │
                └──────┬──────┘
                       │ PASS (candidate-wise)
                       ▼
                ┌─────────────┐   candidate_order 定序逐一
                │  Stage0 4+4 │──▶ FAIL → next candidate Stage0
                └──────┬──────┘    (三候选全 FAIL → STAGE0_NO_CANDIDATE)
                       │ 首个 PASS
                       ▼
                ┌─────────────┐   仅 selected
                │ Stage1 256/64│──▶ FAIL → STOP, Stage2 UNREACHABLE
                └──────┬──────┘
                       │ PASS
                       ▼
                ┌─────────────┐   仅 selected & Stage1 PASS
                │ Stage2 1024 │──▶ 分支 RATE_ADAPTATION / FULL_DISCLOSURE / READY
                │ +TEST32 seal│
                └─────────────┘

任一步 FAIL → 该分支后续标记 UNREACHABLE，不回退换候选，不以 CE 最优递补
```

- **First-match**：`selected = 首个 Stage0 PASS 的 candidate`，按 `162148→2500K→160254` 顺序，不按 `CE/m` 择优；若首候选 Stage0 PASS 即锁定，不评估后两候选 Stage0 的统计优劣。
- **Stop-on-failure**：`Phase R FAIL` → 该候选 `UNREACHABLE_R`；`Stage0 全 FAIL` → `overall = STAGE0_NO_CANDIDATE`，Stage1/2 整体 `UNREACHABLE`；`Stage1 FAIL` → Stage2 `UNREACHABLE`；`Stage2 FAIL` (G 门禁) → 终态按优先级落盘，不继续。
- **优先级**（高→低，互斥）：
  ```
  EVIDENCE_INVALID  (provenance伪造/frame 256/CE链式/改 raw/复用冲突 sidecar/搜 pair)
  > PHASE_R_FAIL
  > STAGE0_NO_CANDIDATE  (三候选 Stage0 全 FAIL)
  > STAGE1_FAIL
  > STAGE2_FAIL  (G1-8 含 G7-aux 失败且 m_req <1024 但容量内仍 FAIL 的 G1-5)
  > RATE_ADAPTATION_REQUIRED  (m_req 超旧容量但每层<1024)
  > FULL_DISCLOSURE_LAYER     (任一层≥1024)
  > READY  (全 G1-8 PASS 且 m_req within frozen budget)
  ```

## 5. 估计器 — 单一预注册 hierarchical (per stage 独立, CAL-only, λ Cal 内 4-fold)

### 5.1 联合计数与全局先验（per stage per candidate）

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, dtype int32
  Stage0: sum = 8192 (4+4 blocks, 但仅 CAL 4 blocks =4096? 注：Stage0 4+4 中 CAL 4 + VAL 4，各自独立)
  Stage1: sum = 65536 (CAL 256 frames)
  Stage2: sum = 262144 (CAL 1024 frames)
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal  shape 1024
Q=1024, n=1024, per plane log2Q=5
```

- `C_ab` 与 `P_global` **仅** `CAL` 产生，`VAL/TEST` 不得参与。
- **Stage0 特殊**：`CAL 4 blocks (4096 pairs) + VAL 4 blocks (4096 pairs)`，`C_ab` 仅 CAL 4 blocks，`VAL 4 blocks` 仅作 `G3/G4/G5 + CE` 验证。

### 5.2 分层条件分布

```
P_λ(a|b) = (C_ab + λ * P_global(a)) / (N_b + λ)  if N_b>0
           P_global(a)                           if N_b==0 (backoff)
P_λ(u1|b) = Σ_{u2=0..31} P_λ(32*u1+u2 | b)  32×1024
P_λ(u2|u1,b) = P_λ(32*u1+u2 | b) / P_λ(u1|b)  若分母>0 else 1/32
```

### 5.3 熵与分层交叉熵（CAL 描述性 + VAL 门禁性，链式双校验）

```
# CAL 描述性（不入 G6/G7）
H_cal(A|B; λ) = - Σ_b P_emp_cal(b) Σ_a P_λ(a|b) log2  bits/symbol
H_cal(U1|B; λ) = - Σ_b P_emp_cal(b) Σ_{u1} P_λ(u1|b) log2  0..5
H_cal(U2|U1B; λ) = H_cal(A|B) - H_cal(U1|B)  (|H-H1-H2|<1e-9 else EVIDENCE_INVALID)

# VAL 门禁性（G6/G7 实际阈）
CE_full(λ*) = - E_VAL[ log2 P_λ*(A|B) ]
CE1(λ*)     = - E_VAL[ log2 P_λ*(U1|B) ]
CE2(λ*)     = - E_VAL[ log2 P_λ*(U2|U1,B)]
CE 链式: |CE_full - CE1 - CE2| < 1e-9 else EVIDENCE_INVALID / G8 FAIL
m1_req = ceil(1.3*1024*CE1/5), m2_req = ceil(1.3*1024*CE2/5)  (不 cap, 显式 raw)
```

### 5.4 λ 搜索协议（预注册，不扩网格，触界即 MODEL_NOT_STABLE）

```
λ_search_domain = log10 λ ∈ [-2, 4]  连续  (λ ∈ [1e-2, 1e4])
Cal-CV: split CAL → k folds (Stage0: 4 frames→4 folds 各1 block; Stage1: 256→4 folds 各64; Stage2: 1024→4 folds 各256)
  for each fold k: C_ab^{(k_train)}, N_b^{(k)}, P_global^{(k)}
                  NLL_k(λ) = mean_{(a,b)∈ fold_k} [-log2 P_λ^{(k_train)}(a|b)]
  Cal-CV NLL(λ) = mean_k NLL_k(λ)
chosen λ* = argmin Cal-CV NLL(λ) via 50-point log grid + Brent refine
λ_at_boundary = (log10 λ* ≤ -2+ε) || (log10 λ* ≥ 4-ε) ε=1e-6 → G2 FAIL → MODEL_NOT_STABLE
search_trace = {λ_grid[50], CV_NLL_grid, λ*, CV_NLL*}
```

- **Val 不参与**：`λ` 选择目标仅 `Cal-CV NLL`，`Val NLL/CE` 仅作 G3/G4/G6/G7 验证。
- **触界不扩**：`λ*` 落边界直接 `G2 FAIL`，禁止扩展至 `[-3,5]`。
- **单估计器**：仅 `P_λ*` 一路为权威；禁第二 estimator。

## 6. 速率分支 — m_req 不 cap 显式语义

```
m1_req = ceil(1.3*1024*CE1/5)   # bits: n * f * CE / log2Q
m2_req = ceil(1.3*1024*CE2/5)
m_total_req = m1_req + m2_req
leak_req = 5*m_total_req +64
leak_frozen = 5*(16+184/190/192)+64 = 1144/1174/1184
```

| 条件 (per layer) | 分支 | 语义 |
|---|---|---|
| `m1_req≤16 && m2_req≤184/190/192 && m_total_req≤216/222/224` | `WITHIN_FROZEN_BUDGET` | 落在冻结构内，可直接用现有 H_total |
| `∃ i: m_i_req > frozen_i` 但 `∀ i: m_i_req <1024` | `RATE_ADAPTATION_REQUIRED` | 需增量冗余/母码重构，非候选失败 |
| `∃ i: m_i_req ≥1024` | `FULL_DISCLOSURE_LAYER` | 该层需全披露，当前码族不可行 |

- **禁止 cap 伪装**：先算 `m_req_raw` 显式 `>16/>192` 即对应分支，禁止 `min(16, ceil(...))` 截断后宣称 `WITHIN`。
- **每层独立**：`m1_req ≥1024` 或 `m2_req ≥1024` 任一即 `FULL_DISCLOSURE_LAYER`，不以总量平均。
- **候选失败隔离**：`RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER` 不作 `G6/G7 FAIL` 的候选失败混淆；候选失败仅由 `G1-5` 等门禁定义。

## 7. 门禁 G1-8（含 G7-aux，per candidate per stage 独立）

| 门 | 判定 (per candidate per stage) | 阈值 frozen |
|---|---|---|
| G1 | `materialization_contract_consistent` | `dimension 1024/bins pairing legacy_v1/channels/frame anchor/mapping 每帧256` 算法一致 且 `sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150] && gate==200 && threshold==40000` |
| G2 | `λ_at_boundary==False` | `log10 λ* ∈ (-2,4)` 开区间 |
| G3 | `ΔNLL ≤0.50` | `Val NLL - CV NLL ≤0.50` bits/symbol |
| G4 | `Val NLL ≤ H_cal+1.0 && isfinite` | bits/symbol (H_cal 仅此 bound 描述性) |
| G5 | `unseen ≤1%` | `q_mass_unseen ≤0.01` |
| G6 | `m1_req ≤16` (仅 Stage1/2 对照，Stage0 同阈) | `m1=ceil(1.3*1024*CE1/5)` raw 未 cap |
| G7 | `m2_req ≤200/206/208` (per source 三档, Stage1/2) | `m2=ceil(1.3*1024*CE2/5)` |
| G7-aux | `m_total_req ≤216/222/224` | `m_total=m1+m2` 辅助总量 |
| G8 | `provenance_zero_overlap && CE_chain_closed` | `CAL_key∩VAL_key==∅ && CAL∪VAL_key∩TEST_key==∅ && ∩(V13..V64)_key==∅ (key=(source,session,frame)) && |CE_full-CE1-CE2|<1e-9` |

- **Stage0 G6/G7 语义**：Stage0 小样本 `m_req` 仅作 early screening，不触发 `RATE_ADAPTATION` 分支（样本不足），仅 `G6/G7 FAIL → STAGE0 FAIL` 换下一候选。
- **Stage1/2 G6/G7 语义**：Stage1/2 的 `m_req` 同 `G6/G7` 阈，但超阈后按 §6 分支为 `RATE_ADAPTATION / FULL_DISCLOSURE`，不作 `STAGE1_FAIL` 的候选能力失败。

## 8. 终态机 — 五态+分支（优先级互斥，first-match/stop-on-failure）

```
if not materialization_ok or frame_256_violation or provenance_fabricated or CE_chain_not_closed or reused_conflicting_sidecar or modified_raw or searched_channel_pair:
    overall = V65AR2_EVIDENCE_INVALID  # 最高优
elif exists candidate: Phase R FAIL (provenance 不可重建):
    overall = V65AR2_PHASE_R_FAIL  # additive 重建失败，Stage0 不可达
elif forall candidates: Stage0 FAIL (G1-8 全验但首 PASS 不存在):
    overall = V65AR2_STAGE0_NO_CANDIDATE  # 三候选 4+4 全不通过
elif selected Stage1 FAIL (G1-5/G8, λ触界/ΔNLL/ValNLL/unseen 失败):
    overall = V65AR2_STAGE1_FAIL  # Stage2 UNREACHABLE
elif selected Stage2 FAIL (G1-5/G8):
    overall = V65AR2_STAGE2_FAIL  # 速率分支前失败
elif selected Stage1/2 m_req ≥1024 per layer:
    overall = V65AR2_FULL_DISCLOSURE_LAYER  # 该层全披露
elif selected Stage1/2 m_req > frozen but <1024:
    overall = V65AR2_RATE_ADAPTATION_REQUIRED  # 需增量冗余/母码
elif forall stages PASS && m_req within frozen:
    overall = V65AR2_READY  # 仅此态可进入后续 decoder 规划
```

- **UNREACHABLE 标记**：`Phase R FAIL` → 该候选 `Stage0 UNREACHABLE_R`；`Stage0 全 FAIL` → `Stage1/2 UNREACHABLE`；`Stage1 FAIL` → `Stage2 UNREACHABLE`，落盘 `per_phase {status PASS/FAIL/UNREACHABLE, reason}`。
- **First-match 不递补**：`STAGE0_NO_CANDIDATE` 不以 `CE` 最优亚军递补；`Stage1/2 FAIL` 不回退重选候选。

## 9. 数据角色 — 分阶段帧语义

| 阶段 | 集合 | 帧数 | pairs | blocks | 零重叠键 |
|---|---|---|---|---|---|
| Stage0 | CAL 4 blocks + VAL 4 blocks | 8 blocks =32 frames | 8192 | 8 | `CAL_key∩VAL_key==∅ && ∩(V13..V64)_key==∅` |
| Stage1 | CAL 256 + VAL 64 | 320 frames =80 blocks | 81920 | 80 | 同上，独立于 Stage0 |
| Stage2 | CAL 1024 + VAL 256 + TEST32 seal | 1312 frames =328 blocks | 327680+8192(seal) | 328 | 同上，`TEST32` 仅 identity 且与 CAL/VAL 不重叠 |

- **F_s 取决于候选 raw 导出**，若 `F_s < 所需帧` 则该阶段 `STAGE*_FAIL (insufficient frames)`，不跨候选拼接。
- **注册表**：`v65ar2_data_registry.json` (`schema v65ar2_v1, candidate_order [162148,2500K,160254], per_candidate {stage0{CAL_frames[32],VAL_frames[32]}, stage1{CAL[256],VAL[64]}, stage2{CAL[1024],VAL[256],TEST[32]} }`，禁止事后换帧。

## 10. 脚本与报告（decoder-free 守卫）

- **脚本 `scripts/v65ar2_pipeline.py`** (decoder-free):
  ```
  python scripts/v65ar2_pipeline.py --candidate-order 162148,2500K,160254 \
    --provenance-tier A,B,C --phase R [--raw-root ...] [--contract ...] [--out v65ar2_phase_r.json]
  python scripts/v65ar2_pipeline.py --phase 0 --candidate 162148 [--data-root ...] [--dry-run]
  python scripts/v65ar2_pipeline.py --phase 1 --candidate selected [--data-root ...]
  python scripts/v65ar2_pipeline.py --phase 2 --candidate selected [--seal-test]
  python scripts/v65ar2_pipeline.py --all --dry-run  # 框架自检，不读真实 raw
  ```
  → `Phase R additive → Stage0 4+4 first-match → Stage1 256/64 → Stage2 1024/256+TEST32 seal`，`rg "decode_" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile PASS`；任一 phase FAIL 后续标记 `UNREACHABLE`。
- **报告 `V65AR2_PIPELINE_REPORT.md`**：每候选 Phase R + Stage0 明细，selected 另 Stage1/2 明细，`CE1/CE2/CE_full + chain_delta + CV/Val/ΔNLL + MAP/unseen/effective + m_req + rate_branch + G1-8(含 G7-aux)`，`overall` 五态+分支，`TEST32` 仅附录 identity，不含统计，数据与 `json` 一致。
- **守卫**：流水线期 **零 decoder**、候选顺序 frozen、三阶段 `UNREACHABLE` 语义、**不创建 `run_01` decoder 执行**、**不改码参**（`git diff -- src/ ==0`）、`rg "decode_" 0 hits`。

## 11. 与 V65/V66 衔接

- V65 `CAL 4096+VAL512+TEST120` 与 V65AR2 `4+4/256/64/1024/256+TEST32` 为**正交验证维度**：V65 验证单候选多源容量，V65AR2 验证多候选 first-match 定序与速率分支；V65AR2 `READY` 不直接继承 V65 的 `READY_FOR_V66`，二者终态独立。
- `V65AR2_RATE_ADAPTATION_REQUIRED` 时需另起 mother-code / incremental-redundancy 变更（ΔH 增量），`FULL_DISCLOSURE_LAYER` 时需另起码族/调制变更；`V65AR2` 本身不产生新矩阵。
