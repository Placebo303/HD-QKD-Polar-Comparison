# OpenSpec Design: formal-ir-v65-new-session-channel-compatibility

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **decoder-free 新 session 通道兼容性预冻结，不调码、不运行 decoder、不读 TEST 统计，三源独立 G1-8 全过才允 V66**
**Cycle**: `V65` (new-session-channel-compatibility), predecessor `V64` `formal-ir-v64-full-symbol-verification-correction` `PLAN_CANDIDATE`
**Branch**: `formal-ir-mainline` HEAD `TBD` (`git rev-parse HEAD == origin/formal-ir-mainline` 重核) data SHA `84d62779` (200ps legacy_v1 nearest 1024 单点，新 session 同点不换处理点)
**Feasibility**: `V54` 二阶段 `43/45` 在 `2026-01-21` 域已证 `H1-16+L1APP+Lane C m2 184/190/192+Δ8+Δ8+full-tag` 方法有效；`V55 0/90` 已定位跨 session 域不兼容；`V56` 已固化 `dimension/bin/pairing/channels/delay/peak/frame/mapping` 权威链可只读复用；`V57` 已证 `8192→131k` 欠采样→平滑重估必要，但仍为旧 session within-session；`V64` 已冻结 `full-symbol tag` 单 64b 泄漏不增；`V65` 仅需以 **新独立 two-session (CAL_SESSION + TEST_SESSION)** 同处理点重审合同一致性、独立先验泛化、与冻结容量的速率兼容性，零 `decode_*` 调用闭环。
**Key judgement**: **`0/90` 与 `V57 131k` 均未回答新 session 兼容性**；必须以新 session 实测同时验证三事 — 合同不偏、先验稳定泛化、速率落在冻结构容量内 — 且 `λ` 预注册 hierarchical 谁贡献 `λ` 则 `MODEL_NOT_STABLE`、 `m_raw>16/200+` 则 `RATE_INCOMPATIBLE`，**不扩网格、不改矩阵、不读 TEST 统计**，方可放行 V66 decoder。

## 1. 科学问题与关键判断

> 在**完全冻结 `V64` 主候选**（`H1-16+L1APP(q via H1 BP, TRAIN prior)+Lane C m2 184/190/192 ordinal-2 s38310x + H_inc1/2 Δ8+Δ8 + full-tag compute_tag_64 canonical 32*U1+U2 单64-bit`）下，新独立 session 的 `P(A|B)` 是否与 V56/V64 合同处理一致、且以 `4096 frames CAL` 学得的 `hierarchical P(a|b)` 在独立 `512 frames VAL` 上 `ΔNLL≤0.5` 且 `unseen≤1%` 稳定泛化、且 `ceil(1.3*1024*H_i/5)` 恰落在 `m1≤16, m2≤200/206/208` 冻结构内？三者全过且 `TEST` 未揭盲才 `READY_FOR_V66`。

- **对照**：`V13 2026-01-21` 的 `V25 H~0.80, m2 184/190/192` 仅作容量对照；`V57 8192 MLE 30bits` 已归档作 `UNDERSAMPLED` 负对照；`V64 24-block` 仅作 `full-tag` 语义对照；`V65` 不沿用其统计，仅验证新 session 上相同合同+新先验+ frozen 速率三合一。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256 / F03 5+5 natural / channels A1/B5 / delay/peak/sigma/gate/threshold/frame anchor/mapping 每帧256 A=32U1+U2 B=32V1+V2` 为跨 session 不变量；`V65` 不改变任一码参，仅验证兼容性。
- **兼容性性质**：纯 **decoder-free**，`λ` 预注册 hierarchical 仅 `CAL` 内 `4-fold` 择优，`VAL` 独立 G1-8 验证，三源分别判定，总体 `READY` 才放行 `V66`。

## 2. 冻结语义 — V64 主候选与处理点零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| m2 per source (frozen) | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 `38310x` (V54→V64 继承，V65 仅容量比较不改) |
| m1 | 16 | `V31-H1-QC-16×1024 rank16 80b` 16 rows (V64 frozen) |
| H_total rows | 200 (1M) 206 (1p5M) 208 (2M) | `H_total = H1+H_inc1+H_inc2` `m1+m2` (V64) |
| GF | GF32 poly37 | GF2mField |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 |
| 泄漏 | base 1064/1094/1104 +40 +40 → 1144/1174/1184? V64 用 `5*m_total+64` 三档 (`m_total 200/206/208`) | V64 `leak=5*m_total+64` |
| 译码 (冻结禁用) | `decode_row_layered_fftqspa 90/1.0 early-stop` | V43/V52 — 兼容性期禁用直至 V66 |
| L1-APP | `p via H1 BP TRAIN channel_counts.npz` (仅作 `NLL_V25` 对照，不训新 prior 的 TRAIN 对照) | V25 |
| Intake 处理点 | `d1024 bw200 nearest legacy_v1 A1/B5` 单点 `84d62779` | V55 authoritative + V56 contract |
| V56 contract | `dimension 1024 / bin200 / nearest legacy_v1 / channels/delay/peak/sigma/gate/threshold/frame anchor/mapping per frame 256 A=32U1+U2 B=32V1+V2` | V56 权威 |
| Verification | `full-symbol tag 32*U1+U2 compute_tag_64 canonical trunc64` 单64b | V64 |
| V65 新 session | `CAL_SESSION 4096 + VAL 512` 同 session A, `TEST_SESSION 120` 独立 session B, per source | V65 预注册 |
| V66 规模 | `90 blocks 30/source 180-360 70/90 & 20/30 undetected 0` | V65 预冻结，不在本轮执行 |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder/prior/H1/Lane C/H_inc1/2/Δ/verification`；**零 decoder 直至 V66**；原 `V55 90-block` 与 `V48-V64 frames` 永久 `zero_overlap`；`V65 H/m` 仅验证兼容性，不写入码；`TEST` 未揭盲。

## 3. 数据角色 — CAL / VAL / TEST 新 session 两会话隔离

### 3.1 每源角色定义

| 集合 | 来源 | 帧数 | pairs | blocks (4×256) | 说明 |
|---|---|---|---|---|---|
| CAL | `CAL_SESSION` (session A, 新 session 1) | 4096 | 1,048,576 | 1024 | 主训练：`C_ab` + `P_global` + `λ` 搜索 |
| VAL | `CAL_SESSION` 同 session A，与 CAL 零重叠另 512 | 512 | 131,072 | 128 | 独立验证：`Val NLL / ΔNLL / unseen` 泛化 |
| TEST | `TEST_SESSION` (session B, 新 session 2, 独立于 A) | 120 | 30,720 | 30 | 预留：**仅 identity 密封**，不计任何统计，不参与先验/阈值 |

- **两会话隔离**：`CAL` 与 `VAL` 同一 `CAL_SESSION` 内零重叠（同域泛化）；`TEST` 必须来自**独立** `TEST_SESSION`（不同 `acquisition date/session_id`，`gap` 天级，`provenance.session_id` 不同），三源各自均需两 session 支撑，否则 `DATA_NOT_READY`。`CAL_SESSION` 4096 + `VAL 512` = 合计 `CAL_SESSION` 内 `4608 frames` 消耗；`TEST` 另起 session 120 frames。
- **BLOCK / FRAME**：`FRAME=256 pairs`, `BLOCK=4×256=1024 symbols (=1024 pairs)`, `frame_id∈[0,F_s-1]` 连续但跳过 forbidden 后仍每帧 256 校验；`BLOCK` 仅 `4` 联续帧完整才计数，不半块。
- **每源配额**：`1M / 1p5M / 2M` 分别 `4096+512+120` frames，不跨源平均，不跨 session 拼接凑数。

### 3.2 数据就绪门（decoder-free，G1-G8 前置）

```
assert |CAL_s|==4096 && |VAL_s|==512 && |TEST_s|==120  per source (>less → DATA_NOT_READY/dirty not enough)
assert set(CAL_s) ∩ set(VAL_s) == ∅  per s
assert set(CAL_s ∪ VAL_s) ∩ set(TEST_s) == ∅  per s
assert set(CAL_s ∪ VAL_s ∪ TEST_s) ∩ set(V13 ∪ V48..V64 已用 frame_ids) == ∅  per s  (exact frame_ids)
assert CAL_SESSION_id_s != TEST_SESSION_id_s  per s  (session_id 不同)
assert not is_cross_session_spliced(s)  (single session_id provenance, 禁单 session 内跨 gap 硬拼凑 4096+120)
```

- **session 数判定**：
  ```
  available_new_sessions = distinct(session_id where source==s && not in V13..V64)
  if len(available_new_sessions) <2: overall = V65_DATA_NOT_READY (per source 判定一致)
  ```
  否则才进入 G1-8。脚本 `v65_data_readiness.py` 启动即校验，失败则写 `v65_data_readiness.json` 后零估计停止，不伪造。
- **注册表**：`v65_data_registry.json` (`schema v65_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779`) 含 `per_source {CAL_session {id, F, CAL_frames[4096], VAL_frames[512]}, TEST_session {id, F, TEST_frames[120]}, blocks, pairs, provenance:{materialization_rule, zero_overlap_verified, session_gap}, session_count,不足两 session 标记}`。

### 3.3 选取理由

- `4096 frames =1024 blocks` 为主候选 `n=1024` 的千 block 级先验，可使 `1024×1024` 表在 `λ` 平滑后有效上下文 `effective_contexts = #{b: N_b>0}` 达 `~1k` 全覆盖，`unseen≤1%` 可证泛化；`512 VAL` 与 V57 一致作泛化探针；`TEST 120 =30 blocks =V66 1/3` 预留，`V66 90 blocks` 需 `30/source` 三倍于 `TEST 120/4` 的测试量，`120` 仅作密封 identity。
- `F_s` 取决于新 session 原始导出（若 `F_s < 4608+120+ forbid` 则 `DATA_NOT_READY`），不以旧 `pairs.parquet` 凑数。

## 4. 输入合同 — 严格复用 V56 权威链

### 4.1 合同清单（逐项显式，三源分别）

| 阶段 | 参数 | 冻结值 (V56) | V65 记录粒度 |
|---|---|---|---|
| 1 | dimension | 1024 | per frame |
| 2 | bin_width | 200 ps | global |
| 3 | pairing | `nearest`, double-pointer `bin//1024` 消歧 | `pair_sequence a=binA%1024,b=binB%1024` |
| 4 | rule/mapping | `legacy_v1` | `sym → U1/U2` |
| 5 | channels | `A:1 , B:5` (type2) | `counts per channel` |
| 6 | delay | `delay_used_ps` 每源固定 (V56 实测, 如 -50/+50 仅示例, 以 sidecar 为准) | `delay_used_ps` |
| 7 | peak/sigma/gate/threshold | `peak_center, sigma 50-150ps, gate 200ps, threshold 40000ps` | 每 session 实测 |
| 8 | frame anchor | `frame_start_ps / period 204800ps / floor_div` | `204800=1024×200` 配对尺度 |
| 9 | mapping | `legacy_v1` symbol `0..1023` | `alice/bob symbols` |
| 10 | U1/U2 | `A=32U1+U2, B=32V1+V2, U1=sym>>5, U2=sym&31, 每帧256` | per pair |

- **只读复用**：直接复用 `src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags/_bin_indices_sorted_for_binwidth/_pairs_from_sorted_bins` + `legacy_v1` mapping 的 `V56` 验证版，不重写近似版；`sidecar/build_manifest` 追溯失败则 `EVIDENCE_INVALID`。
- **三源分别**：`1M /1p5M /2M` 各自 `provenance.json` 含 `session_id, delay_used_ps, peak_center, sigma, p2bg, gate, threshold, frame_start_ps, period, bin_width`，不共享 sidecar。
- **帧级校验**：每帧输出 `alice_symbols[256], bob_symbols[256]` 各 `256` pairs，`A/B` 均 `32U1+U2` 分解后 `U1,V1,U2,V2 ∈[0,31]`，缺失/非 `256` 则 `EVIDENCE_INVALID`。

## 5. 估计器 — 单一预注册 hierarchical (CAL-only, λ Cal 内 4-fold log10[-2,4] 连续)

### 5.1 联合计数与全局先验

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, dtype int32, sum = N_cal = 1,048,576 (=4096*256)
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal  shape 1024, Σ P_global =1
Q=1024, n=1024
```

- `C_ab` 与 `P_global` **仅** `CAL 4096` 产生，`VAL/TEST` 不得参与。

### 5.2 分层条件分布

```
P_λ(a|b) = (C_ab + λ * P_global(a)) / (N_b + λ)  if N_b>0
           P_global(a)                           if N_b==0 (backoff)
P_λ(u1|b) = Σ_{u2=0..31} P_λ(32*u1+u2 | b)  32×1024
P_λ(u2|u1,b) = P_λ(32*u1+u2 | b) / P_λ(u1|b)  若分母>0 else 1/32
```

- **U1/U2 表齐备**：同时生成 `P(U1|B) 32×1024` 与 `P(U2|U1,B) 32×1024×32`（或 `1024*32` 扁平），供 `H(U1|B)/H(U2|U1B)` 链式计算；`N_b==0` 的上下文数即 `1024-effective_contexts`。

### 5.3 熵与链式分解

```
H_cal(A|B; λ) = - Σ_b P_emp(b) Σ_a P_λ(a|b) log2 P_λ(a|b)  bits/symbol  P_emp(b)=N_b/N_cal
H_cal(U1|B; λ) = - Σ_b P_emp(b) Σ_{u1} P_λ(u1|b) log2 P_λ(u1|b)  0..5
H_cal(U2|U1B; λ) = H_cal(A|B) - H_cal(U1|B)  (链式闭合 |H-H1-H2|<1e-9 else EVIDENCE_INVALID)
H_total = H_cal(A|B; λ*), H1=H_cal(U1|B; λ*), H2=H_cal(U2|U1B; λ*)  @ chosen λ*
MAP_acc_cal = mean_{CAL}[ a == argmax_a P_λ(a|b) ]  仅描述不入硬门但报告
```

- **TEST 禁计**：`H` 与 `P` 仅 `CAL λ*` 下算，`VAL` 上另算 `H_val` 作 `G4` 对照但不参与 `λ` 选择；`TEST` 不计任何。

### 5.4 λ 搜索协议（预注册，不扩网格，触界即不稳定）

```
λ_search_domain = log10 λ ∈ [-2, 4]  连续  (即 λ ∈ [1e-2, 1e4])
Cal-CV: split CAL 4096 frames → 4 folds各 1024 frames (262144 pairs/fold)
  for each fold k: C_ab^{(k_train)}  from 3 folds (3072 frames), P_global^{(k)}, N_b^{(k)}
                  NLL_k(λ) = mean_{(a,b)∈ fold_k} [-log2 P_λ^{(k_train)}(a|b)]
  Cal-CV NLL(λ) = mean_k NLL_k(λ)  4-fold 平均 (bits/symbol)
chosen λ* = argmin_{λ∈[1e-2,1e4]} Cal-CV NLL(λ) via scalar bounded minimization (e.g. Brent / 50-point log grid + refine)
λ_at_boundary = (log10 λ* ≤ -2+ε) || (log10 λ* ≥ 4-ε)  ε=1e-6 或优化收敛至边界 → MODEL_NOT_STABLE
search_trace = {λ_grid[50], CV_NLL_grid, optimum λ*, CV_NLL*}
```

- **Val 不参与**：`λ` 选择目标仅 `Cal-CV NLL`，`Val NLL` 仅作 `G3/G4` 独立泛化验证，不反哺 `λ`。
- **触界不扩**：`λ*` 落边界（`1e-2` 或 `1e4`）直接 `G2 FAIL → MODEL_NOT_STABLE`，**禁止**自动扩展至 `[-3,5]` 或二次网格；记录 `λ_search_trace` 证明触界。
- **单估计器**：全文仅 `P_λ*` 一路为权威；`MLE/Laplace α=1.0` 等第二估计仅作 `V57 negative control` 背景章节不入 G1-8。

## 6. 每源报告与泄漏预算（m_i 不 cap 伪装）

### 6.1 报告量（per source, CAL/VAL 分别，TEST 仅 identity）

```
样本: N_cal=1048576/4096, N_val=131072/512, N_test_identity=30720/120, effective_contexts
先验: λ*, λ_at_boundary, CV_NLL(λ*) (Cal-CV), Val NLL = mean_Val[-log2 P_λ*(a|b)], ΔNLL = Val - CV, H_cal(A|B), H_cal(U1|B), H_cal(U2|U1B), H_val(A|B) (同 λ* 下 Val 计数重算熵? 这里 H_val = -Σ P_val(b) Σ P_λ* log)
泛化描述: MAP_acc_val = mean_Val[a==argmax P_λ*(a|b)], q_mass_unseen = P_val(b: N_b_cal==0), zero_cells_cal = #{C_ab==0}
预算: m1_raw = ceil(1.3*1024*H(U1|B)/5), m2_raw = ceil(1.3*1024*H(U2|U1B)/5), m1_required=m1_raw, m2_required=m2_raw, m_total=m1+m2
      Δm1 = m1_raw -16, Δm2 = m2_raw - {200→16+? 184,190,192? 实际 G7 用 m_total 200/206/208: Δm2_vs_200等}, Δleak =5*Δm
      leak_frozen =5*m_total_frozen+64, leak_required =5*m_total_raw+64  (tag 64 已含, 三档)
```

- **公式冻结**：`m_i = ceil(1.3 * 1024 * H_i /5)` (`n=1024, f=1.3, log2q=5` channel coding `leak≈f*n*H`)，**不 cap 伪装**：先算 `m_raw` 显式 `>16/>200` 即 `G6/G7 FAIL`，禁止 `min(16, ceil(...))` 截断后宣称通过；`m_raw` 与 `m_required` 同值，未截断。
- **冻结容量差额**：`Δm1 = m1_raw -16`, `Δm2 = m2_raw - {184,190,192}` 或 `Δm_total = m_total_raw - {200,206,208}`，`Δleak =5*Δm`，负值表示有余量，正值表示超额。
- **TEST 隔离**：`TEST_SESSION` 仅报告 `session_id, TEST_frames[120], blocks 30, pairs 30720, gap≥4, provenance` identity，不计算 `H/NLL/MAP/q_mass/m` 任何统计；脚本内 `assert not used_test_in_estimation`。

### 6.2 示例（V57 旧域作参考，非新域预设）

- V57 旧域 `131k 1e-2` 下 `H~?` 但 V65 `1M` pairs 下 `Q=1024` 不再稀疏，预期 `ΔNLL≤0.5` 可达；若新 session 熵更高致 `m_raw>16/200` 则 `RATE_INCOMPATIBLE`，不得增 `Δ8`。

## 7. 门禁 G1-8（per source 独立，预注册阈，不平均）

| 门 | 判定 (per source s) | 说明 |
|---|---|---|
| G1 | `materialization_contract_consistent_s == True` | V56 逐项一致 (dimension/bin/pairing/legacy_v1/channels/delay/peak/sigma/gate/threshold/anchor/mapping 每帧256) |
| G2 | `λ_at_boundary_s == False` | `log10 λ* ∈ (-2,4)` 开区间，且 `CV_NLL` 在内部最小 |
| G3 | `ΔNLL_s = Val_NLL_s - CV_NLL_s ≤0.50` | bits/symbol，泛化漂移受控 |
| G4 | `Val_NLL_s ≤ H_cal_s +1.0` | bits/symbol，且 `isfinite` |
| G5 | `q_mass_unseen_s ≤0.01` | `P_val(b∉Cal_support) ≤1%` context 未见 |
| G6 | `m1_raw_s ≤16` | 与冻结 `H1-16` 等长 |
| G7 | `m2_raw_s ≤ {200-16,206-16,208-16}? 实际 V65 用 m_total 200/206/208 信封：m_total_raw_s ≤ {200,206,208}` | `m_total=H1+H2` 预算信封 |
| G8 | `provenance_zero_overlap_s == True` | `CAL∩VAL==∅ && CAL∪VAL∩TEST==∅ && ∩(V13..V64)==∅ && CAL_SESSION!=TEST_SESSION && not cross-spliced` |

- **每源独立**：`PASS_s = G1..G8 全 True`，任一 `False` 则 `PASS_s=False`；`MAP/链式差` 仅描述不入 G1-8（链式差>1e-9 则 `EVIDENCE_INVALID` 更高优先级）。
- **阈值冻结**：预注册于 `v65_manifest.json: thresholds {G3 0.5, G4 H+1.0, G5 0.01, G6 16, G7 200/206/208, λ [-2,4]}`，事后不调。

## 8. 终态五选一（优先级高→低，互斥，不主观）

```
if not materialization_contract_ok or frame_256_violation or cross_session_spliced or chain_not_closed or provenance_fabricated:
    overall = V65_EVIDENCE_INVALID  # 证据/物化/零重叠/拼接失败，最高优先级
elif n_new_sessions <2 or |CAL_s|!=4096 or |VAL_s|!=512 or |TEST_s|!=120 per source (缺帧):
    overall = V65_DATA_NOT_READY  # 数据不足，不伪造
elif exists s: G2_s FAIL or G3_s FAIL or G4_s FAIL:  # λ触界 或 ΔNLL>0.5 或 Val NLL逸出
    overall = V65_MODEL_NOT_STABLE  # 先验未稳定，不扩 λ，不进 V66
elif exists s: G6_s FAIL or G7_s FAIL:  # m1_raw>16 或 m2_raw>200/206/208
    overall = V65_RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE  # 速率不兼容，不改矩阵，不进 V66
elif for all s: PASS_s==True (G1..G8 全过):  # 三源均通过
    overall = V65_CHANNEL_COMPATIBILITY_READY_FOR_V66  # 仅此态允许 V66
```

- **仅第5态允许 V66**：报告显式“**允许另起 V66 走 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH 的 decoder TEST 90 blocks**”；其余 4 态均显式“**不允许 decoder TEST**”；`MODEL_NOT_STABLE` 止于不扩 `λ` 网格、`RATE_INCOMPATIBLE` 止于不换 `H_inc` 矩阵。

### V66 预冻结（本轮仅声明）

- **规模**：`90 blocks =30/source ×3`, `per block 1024 symbols (4×256 frames)`, `sampling_from_holdout_fresh` 相对于 `CAL/VAL/TEST` 及 `V48-V64` 均 `frame_ids exact` 零重叠，`gap≥4` 不放松，`v66_fresh_registry.json` authoritative 固化实表。
- **预算**：`m_total 200/206/208` 不变（`H1-16 + m2 184/190/192`），`leak=5*m_total+64` 三档 `1064/1094/1104 →1144/1174/1184`? V64 已用 `+40+40` 释为 `200/206/208` 终局，本预冻结同终局；`tag` 仍单64b。
- **门禁等比**：`exact_full == (exact_u1 && exact_l2) ≥70/90 overall (77.78%) 且每源 ≥20/30 (66.67%)`, `undetected_full_tag ==0` 全局，`syndrome_ok && tag_ok_full` 双验证，否则非 PASS。
- 本轮不启动 V66，不创建输出，不读 `TEST`。

## 9. 脚本与报告（decoder-free 守卫）

- **脚本 1 `scripts/v65_data_readiness.py`** (decoder-free):
  `python scripts/v65_data_readiness.py [--new-session-root ...] [--v13-registry ...] [--v48-v64-registry ...] [--out v65_data_registry.json]`
  → `session_count` 检测 (<2 → DATA_NOT_READY) + `CAL 4096 + VAL 512 + TEST 120` 帧切分与 `CAL∩VAL==∅ && CAL∪VAL∩TEST==∅ && ∩(V13..V64)==∅ && CAL_SESSION!=TEST_SESSION && not cross-spliced` 校验 + `frame 256 A/B mapping` 校验 + `provenance` 完整性，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS；输出 `v65_data_registry.json + v65_data_readiness.json` + 控制台 spike 摘要；不足两 session 直接 `DATA_NOT_READY` 不伪造。
- **脚本 2 `scripts/v65_channel_compatibility.py`** (decoder-free):
  `python scripts/v65_channel_compatibility.py [--cal-root ...] [--val-root ...] [--test-registry ...] [--out v65_channel_compatibility.json]`
  → `CAL C_ab/P_global → λ 4-fold CV [1e-2,1e4] 连续 → P_λ* → H/H1/H2 链式 → m_raw 不 cap → P(U1|B)/P(U2|U1B) 表 → VAL NLL/ΔNLL/unseen/MAP/effective_contexts → G1-8 per source →  overall 五态（优先级）→ V66 预冻结声明`，`rg "decode_" 0 hits`，`py_compile` PASS；输出 `v65_channel_compatibility.json` + 控制台摘要；校验 `TEST 未参与` (`used_test_in_estimation==False`) 及 `m_raw` 未 cap。
- **报告 `V65_CHANNEL_COMPATIBILITY_REPORT.md`**：每源 `Cal/Val pairs/frames + λ 是否触界 + H(U1|B)/H(U2|U1B)/H(A|B) + CV NLL/Val NLL/ΔNLL + MAP/q_mass/effective_contexts + m1_raw/m2_raw/m_total 相对冻结构差额` + `G1-8 明细` + `overall 五态 + V66 预冻结` + `TEST identity 附录（不含统计）` + `Negative Control (V57 8192 MLE)` 对比，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V55 90 已揭盲不可复用` + `TEST 未参与先验/阈值` + `仅第5态允 V66`。
- **守卫**：兼容性期 **零 decoder**、原 `90` 已揭盲保护、**不创建 `run_01` decoder 执行**、**不做阈值/方向/frame-start 网格**、**不改码参**（`git diff -- src/ ==0` 且 `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0` 除 `v35/v54` 只读）、`rg "decode_" 0 hits`。

## 10. 与 V64/V66 衔接

- V64 `full-symbol tag` 语义与 `H_total 200/206/208` 冻结构已固化，不重跑；`V65` 以**新 session 两会话**补齐 `合同一致性 + 独立先验泛化 + 冻结速率` 三合一证据，若 `V65_EVIDENCE_INVALID/ DATA_NOT_READY / MODEL_NOT_STABLE / RATE_INCOMPATIBLE` 则停留在 `PLAN_CANDIDATE / DECODER_FREE`，不进入 `V66`。
- `V66` 为 `decoder TEST`：需新 `TEST 90 blocks 30/source`（与 `CAL 4096+VAL512+TEST120` 及 `V48-V64` 均零重叠，未揭盲），冻结 `m_total 200/206/208` 按 `V65 H` 验证后仍同冻结构实例化，独立 `EXECUTE_AUTH` 绑定 `HEAD/data SHA/implementation SHA` 三方。

## 11. 自由裁量 D1-D7

- D1 完全冻结 V64 主候选（`H1-16 rank16 / L1APP q via H1 / Lane C m2 184/190/192 / H_inc1/2 Δ8+Δ8 / decoder 90/1.0 / full-tag 单64b / H_total 200/206/208`），`V65` 仅验证兼容性，不改任何。
- D2 单一 hierarchical `λ` 先验，不引入第二 estimator；同 `V57` `131k smooth` 对照仅作背景。
- D3 泄漏不增，`m_i=ceil(1.3*1024*H_i/5)` 分层，`tag` 已含，不重复，不 cap 伪装。
- D4 数据 `4096+512+120` 每源确定性切分，不搜索多划分（仅预注册一种，`1M` pairs 已为 `1M cell` 的稳定可报告门限，`TEST 120` 仅 identity）。
- D5 四载 `G1 authority, G2 λ边界, G3 ΔNLL 0.5, G4 H+1.0, G5 1%, G6 16, G7 200/206/208, G8 zero overlap` 预注册阈，不以总体平均替代。
- D6 不产生新矩阵/码参数，仅验证与判定，最简闭环。
- D7 本变更为 `PLAN_CANDIDATE / DECODER_FREE`，不产生 `TEST run_01`，`V66` 时才 decoder。
