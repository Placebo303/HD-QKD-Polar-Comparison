# OpenSpec Spec: formal-ir-v65-new-session-channel-compatibility

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + decoder-free spike，不改主候选/V64/src，不启动 V66
**Change**: `formal-ir-v65-new-session-channel-compatibility` (`V65`, branch `formal-ir-mainline`, HEAD `TBD`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v64-full-symbol-verification-correction` (`V64` full-tag 24-block) — V65 新增 new-session 两会话兼容性门

## 1. 变更类型与生命周期

- **Type**: `CHANNEL_COMPATIBILITY_VERIFICATION` — 新独立 session 上输入合同一致性 + hierarchical 先验稳定泛化 + 冻结速率兼容性预冻结，为 V66 decoder TEST 放行门，一次 `CAL 4096 + VAL 512` 同 CAL_SESSION + `TEST 120` 独立 TEST_SESSION 两会话验证（不跨 session 拼接，少两 session → DATA_NOT_READY，(TEST 密封仅 identity，λ 预注册 hierarchical 唯一，五态优先级）。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free readiness/estimation spike（`v65_data_readiness.py` + `v65_channel_compatibility.py`），**不实现 runner，不执行 decoder，不创建 `run_01`，不读 TEST 统计，不改主候选/V64/src**；正式 `run_01` 创建需独立 `PLAN_ACCEPT` + `V66 EXECUTE_AUTH`。
- **Branch**: `formal-ir-mainline`；`HEAD` `TBD` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞；本次推送新 Plan SHA 后停止。
- **Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200 pairing=nearest rule=legacy_v1`) — 新 session 同处理点单点；`CAL/VAL` 同一 `CAL_SESSION`、`TEST` 独立 `TEST_SESSION` 两会话隔离，少两 session 则 `DATA_NOT_READY`。

## 2. 冻结方法（主候选完全冻结，V65 零改）

### 2.1 主候选不变量（V64 完全冻结，V65 零改）

- `n =1024 symbols/block` (`4×256 frames`), `q =1024 (10-bit s=32*u1+u2, u1=s//32 0..31 high, u2=s%32 0..31 low)`, `log2 q =5 per plane`, `GF32 poly=37 (0b100101)`, `tag =64 bits/block 仍单 tag 仅 total 计一次`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`L1-APP`: `p_i(u1)=P(U1|B_i) → BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs → q_i=softmax(BP_i) → P_i(U2)=Σ q_i P(U2|B,u1)` (TRAIN prior `channel_counts.npz` via `load_v25_channel_counts()` 只读，V65 仅作 `NLL_V25` 对照，不重估 TRAIN)。
- `Lane C` ordinal-2 `s38310x`：`m2 =184 (1M) /190 (1p5M) /192 (2M)`，`support/标签/置换/MET图` 全冻。
- `H_inc1 8×1024 det1` + `H_joint1 192/198/200×1024` nested；`H_inc2 8×1024 det2` + `H_total 200/206/208×1024` nested；`rank_total==m2+16, independence_2==8, row≤16, col_inc≤1`。
- `decoder`: `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop`；`rescue 触发 = verification-only`。
- `leak`: `leak_frozen =5*m_total+64` 其中 `m_total = m1+m2 =16+184/190/192 =200/206/208`, `tag` 已含，不重复扣除，V65 不变（验证用）。
- `verification`: `full-symbol tag s_hat=32*u1_hat+u2_hat compute_tag_64(canonical) trunc64` (V64)，单64b，V65 同。
- `budget V66 预冻结`: `90 blocks 30/source, m_total 200/206/208 不变, leak 三档不变, tag 单64b`。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024消歧, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，三源一致处理但 per source provenance 分别记录 `delay/peak/sigma`。
- `TEST` 密封：`TEST_SESSION 120 frames` 仅 `session_id/frame_ids/blocks` identity，不计任何 `H/NLL/MAP` 统计；`C_ab/P_global/λ` 均 `CAL`-only。

### 2.3 禁止

- 禁改任一冻结量、新增矩阵/标签/`prior`/阈值/`decoder`、试 `Δm=4/12/16` 多档、跨 session 拼接凑 `4096+120`、将 `min(16,ceil)` cap 伪装当通过、改 `src/experiments/tools` 任何文件（只读复用）；禁读 `TEST` 统计；`λ` 触界禁扩网格；禁 `V55 90 / V48-V64 frames` 复用；未授 `V66 EXECUTE_AUTH` 前禁 `decode_*` 新增在 plan 侧。

## 3. Phase A — 数据角色 (CAL 4096 + VAL 512 同 CAL_SESSION, TEST 120 独立 TEST_SESSION, 两会话隔离，不跨 session 拼接)

### 3.1 角色与零重叠

| 集合 | 来源 | 帧数 | pairs | blocks | 零重叠要求 |
|---|---|---|---|---|---|
| CAL | `CAL_SESSION` (session A, 新) | 4096 | 1,048,576 | 1024 | `CAL∩VAL==∅` |
| VAL | 同 `CAL_SESSION` A，与 CAL 零重叠 | 512 | 131,072 | 128 | `CAL∪VAL∩TEST==∅` |
| TEST | `TEST_SESSION` (session B, 独立于 A) | 120 | 30,720 | 30 | `CAL∪VAL∪TEST ∩ (V13∪V48..V64)==∅` per source, `CAL_SESSION_id != TEST_SESSION_id`, `not cross_spliced` |

- **两会话判定**：
  ```
  available_new_sessions_s = distinct(session_id where source==s && pairs exist && not in V13..V64)
  if len(available_new_sessions_s) <2: overall = V65_DATA_NOT_READY
  ```
  `scripts/v65_data_readiness.py` 启动首检，不足则 `DATA_NOT_READY` 零估计，不伪造。
- **frame 定义**：`frame_id∈[0,F_s-1]`，`pairs_per_frame 256`，`BLOCK 4×256` 连续帧，`frame_ids exact` 与 `v55_authoritative_registry + v64_fresh_registry + V13 sidecars` 逐帧 `set∩==∅` 已验，`gap≥4` 为 `TEST 120` 内部连续性不要求但 `CAL 4096` 内建议连续，跨 session 拼接（单 session 内跨大 gap 硬凑 `4096+120`）显式 `EVIDENCE_INVALID`。
- **注册表**：`v65_data_registry.json` (`schema v65_data_v1`) per source `CAL_frames[4096] + VAL_frames[512] + TEST_frames[120]` 各自 provenance，禁止事后换帧。

### 3.2 数据就绪门失败→终态优先级 2

- `n_new_sessions<2` 或 `|CAL|!=4096/|VAL|!=512/|TEST|!=120` （含 `F_s` 不足）→ `V65_DATA_NOT_READY` (仅当 `EVIDENCE_INVALID` 未触发时)；`cross_spliced` 或 `frame 256` 违规 → `EVIDENCE_INVALID` 更优先。

## 4. Phase B — 输入合同 strict V56 (三源分别 provenance，不共享 sidecar)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, delay_used_ps, peak_center, sigma ∈[50,150], p2bg, gate 200, threshold 40000, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256 A=32U1+U2 B=32V1+V2` 三源分别落 `v65_manifest.json:contract_per_source`，与 `workspace/v13r3fresh_20260816/sidecars + V56 ttbin_pipeline` 实测逐项 `==` 已验。
- **权威链**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U1U2` 原样复用，不重写；溯源失败 `AUTHORITY_LINEAGE_INCOMPLETE → EVIDENCE_INVALID`。
- **G1**：`materialization_contract_consistent_s == (所有项逐项一致 && 每帧256 && A/B映射正确)` per source。

## 5. Phase C — 单一 hierarchical 估计 (CAL-only, λ Cal 内 4-fold log10[-2,4] 连续, 触界不稳定)

### 5.1 C_ab 与 P_global (CAL-only)

```
C_ab[s][a,b] = bincount2d(a_cal_s, b_cal_s)  1024×1024, sum 1,048,576
N_b[s][b] = Σ_a C_ab
P_global_s(a) = Σ_b C_ab / N_cal
Q=1024, n=1024, palette 0..1023
```

### 5.2 层级先验与熵 (CAL λ*, 链式)

```
P_λ(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  (N_b>0); P_global(a)  (N_b==0)
P_λ(u1|b) = Σ_{u2} P_λ(32*u1+u2 | b)  32×1024
H_λ(U1|B) = -Σ_b P_emp(b) Σ_{u1} P_λ(u1|b) log2
H_λ(A|B) = -Σ_b P_emp(b) Σ_a P_λ(a|b) log2
H_λ(U2|U1B) = H_λ(A|B) - H_λ(U1|B);  |H-H1-H2|<1e-9 else EVIDENCE_INVALID
m1_raw = ceil(1.3*1024*H(U1|B)/5), m2_raw = ceil(1.3*1024*H(U2|U1B)/5)  (不 cap, 显式 raw)
m_total = m1_raw + m2_raw,  Δm1=m1_raw-16, Δm2=m2_raw-{184,190,192}, Δleak=5Δm
```

- **P表**：同时齐备 `P(U1|B) 32×1024` 与 `P(U2|U1B) 32×32×1024 扁平` (或 `1024×32`) 供链式熵与未来 `L1-APP` 先验平替，不入 V65 门禁但落盘待 V66。
- **TEST 禁计**：`H/m` 均 `CAL λ*` 下算，`VAL` 上的 `H_val` 另计对照不参与 `λ`；`TEST` 不计任何。

### 5.3 λ 搜索 (预注册, 不扩网格, 触界→不稳定)

```
search_domain = log10 λ ∈ [-2, 4]  continuous  (λ∈[1e-2, 1e4])
Cal-CV: split CAL 4096 → 4 folds各1024 frames/262144 pairs
  CV_NLL(λ) = mean_{k=1..4} mean_{(a,b)∈fold_k} [-log2 P_λ^{(train_k)}(a|b)]
λ* = argmin_{λ∈[1e-2,1e4]} CV_NLL(λ) via 50-point log grid + bounded refine (e.g. minimize_scalar bounded)
trace = {logλ_grid[50], CV_NLL_grid, λ*, CV_NLL*}
at_boundary = (log10 λ* ≤ -2+ε) || (log10 λ* ≥ 4-ε)  ε=1e-6 or optimizer at bound → G2 FAIL
```

- `CV_NLL` 仅 `Cal` 内 `4-fold` 平均，`Val NLL` 不反哺；`λ*` 落两端边界直接 `MODEL_NOT_STABLE`，禁止扩展至 `[-3,5]` 或二次网格；第二 estimator (`MLE/Laplace α=1.0`) 禁止作门禁，违则 `EVIDENCE_INVALID`。
- `Val 泛化`：`Val NLL = mean_Val[-log2 P_λ*(a|b)]`, `ΔNLL = Val - CV`, `q_mass_unseen = P_val(b∉Cal_support)`, `MAP = mean[a==argmax P_λ*]`，分别落盘。

## 6. Phase D — 每源报告 (CAL/VAL, λ, 熵, NLL, MAP, unseen, effective, m diff, TEST 仅 identity)

- **报告 schema** per source `s`：
  ```
  sample: {N_cal 1048576/frames 4096, N_val 131072/512, N_test 30720/120 identity, effective_contexts= #{N_b>0}, zero_cells_cal}
  prior: {λ*, at_boundary, CV_NLL*, Val_NLL, ΔNLL, search_trace}
  entropy: {H, H1, H2, chain_delta, H_val}
  generalization: {MAP_acc_val, q_mass_unseen, effective_contexts, zero_frac}
  budget: {m1_raw, m2_raw, m_total, Δm1_vs_16, Δm2_vs_{184,190,192}, Δm_total_vs_{200,206,208}, Δleak, leak_frozen, leak_required}
  gates: {G1..G8, PASS_s}
  ```
- **TEST 仅 identity**：`TEST_session {id, TEST_frames[120], blocks 30, pairs 30720}` 不含 `H/NLL/MAP/unseen/m`，脚本内 `assert no_test_statistics_computed`。

## 7. Phase E — 门禁 G1-8 (per source 独立, 预注册阈, 不平均)

| 门 | 条件 (per source) | 阈值 frozen |
|---|---|---|
| G1 | `contract_consistent_s` | V56 逐项一致 |
| G2 | `λ_at_boundary_s==False` | `log10 λ* ∈ (-2,4)` 开区间 |
| G3 | `ΔNLL_s ≤0.50` | bits/symbol |
| G4 | `Val_NLL_s ≤ H_cal_s +1.0 && isfinite` | bits/symbol |
| G5 | `unseen_s ≤1%` | `q_mass_unseen ≤0.01` |
| G6 | `m1_raw_s ≤16` | 与 `H1-16` 等长 (raw 未 cap) |
| G7 | `m2_raw_s ≤ {184,190,192}? 等价 m_total_raw_s ≤ {200,206,208}` | `m_total = m1+m2 ≤ H_total rows` |
| G8 | `provenance_zero_overlap_s` | `CAL∩VAL==∅ && CAL∪VAL∩TEST==∅ && ∩V13..V64==∅ && CAL_SESSION!=TEST_SESSION && not_cross_spliced` |

- `PASS_s = G1..G8 全 True`，任一 `False` 则 `PASS_s=False`；`chain_delta>1e-9` 则 `EVIDENCE_INVALID` 更优先于 G1-8。

## 8. Phase F — 总体五态 (优先级高→低, exclusive, 不主观) 与 V66 预冻结

### 8.1 五态 (first-match)

```
if materialization/chain/frame256/cross_spliced/provenance fabricated:
    overall = V65_EVIDENCE_INVALID
elif n_new_sessions <2 or |CAL|!=4096 or |VAL|!=512 or |TEST|!=120 per source:
    overall = V65_DATA_NOT_READY
elif exists s: not G2_s or not G3_s or not G4_s:  # λ触界 或 ΔNLL>0.5 或 Val逸出
    overall = V65_MODEL_NOT_STABLE  # 不扩λ网格
elif exists s: not G6_s or not G7_s:  # m1_raw>16 或 m2_raw>200/206/208 (或 m_total>200/206/208)
    overall = V65_RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE  # 不改矩阵
elif forall s: PASS_s==True:
    overall = V65_CHANNEL_COMPATIBILITY_READY_FOR_V66
```

- 仅 `READY_FOR_V66` 允许 V66；其余 4 态 `DECODE_FORBIDDEN` 保持，`MODEL_NOT_STABLE` 不扩网格，`RATE_INCOMPATIBLE` 不换 `H_inc`。

### 8.2 V66 预冻结 (本轮仅声明, 未来执行)

- **规模**：`90 blocks =30/source`，`per block 1024 symbols (4×256 frames)`，`sampling_from_holdout_fresh` 相对于 `CAL 4096+VAL512+TEST120` 及 `V48-V64` 均 `frame_ids exact` 零重叠，`gap≥4` 不放松，`v66_fresh_registry.json` authoritative 固化实表，禁换块。
- **预算**：`m_total 200/206/208` 不变，`leak=5*m_total+64` 三档 `1064→1144/1174/1184`? V64 终局 `200/206/208 + tag64` 为 `1064/1094/1104 base →1144/1174/1184 final`，本预冻结同终局；`tag` 单64b 仅 `total` 计一次。
- **门禁**：`exact_full == (exact_u1 && exact_l2) ≥70/90 overall (77.78%) 且每源 ≥20/30 (66.67%) && undetected_full_tag==0 && all exact frames tag_ok_full==True && syndrome_ok`，`70/90` 等比 `V64 19/24` 且 `per source 20/30`，否则非 PASS；`undetected` 隔离永不并入 `success`；`disclosure/调用/m_total` 审计同 V64。
- **本轮不创建**任何 `.../v65_*/run_01` 或 `.../v66_*/run_01` decoder 输出；`V66` 正式执行需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 绑定到精确实现 SHA + `v66_fresh_registry.json`。

## 9. 脚本与证据写出 (预冻结, 未来执行, decoder-free)

- **固定脚本**（本轮仅冻结计划，spike 可 decoder-free dry-run）：
  - `scripts/v65_data_readiness.py`: session 数检测 + 零重叠 + `frame 256` + `session isolation` + `not cross_spliced`，输出 `v65_data_registry.json + v65_data_readiness.json`，`rg "decode_" 0 hits`。
  - `scripts/v65_channel_compatibility.py`: `CAL C_ab/P_global → λ CV → P_λ* → H/H1/H2 → m_raw → P(U1|B)/P(U2|U1B) → VAL NLL/ΔNLL/unseen/MAP → G1-8 → overall 五态 → V66 预冻结声明`，输出 `v65_channel_compatibility.json + v65_manifest.json + V65_CHANNEL_COMPATIBILITY_REPORT.md`，`rg "decode_" 0 hits`，`py_compile PASS`，`m_raw` 未 cap，`TEST` 未用，`λ` 触界不扩。
- **增量根**（未来实现，decoder 前建，fail-closed，**本轮 P0 不创建**，仅冻结计划）：
  ```
  openspec/changes/formal-ir-v65-new-session-channel-compatibility/  # 本轮 plan 四工件 + registries + report
  scripts/v65_data_readiness.py, scripts/v65_channel_compatibility.py  # decoder-free
  comparison_bench/outputs_comparison/formal_ir_methods/v65_channel_compatibility/  # 未来 V66 执行时 run_01 (本轮不建)
  ```
- **文件**：`v65_data_registry.json` (authoritative `CAL 4096+VAL512+TEST120` 实表，`session_id` 双会话，不同源分别) + `v65_data_readiness.json` (G8 前置) + `v65_channel_compatibility.json` (per source H/λ/NLL/MAP/m/G1-8 + overall) + `v65_manifest.json` (H provenance + λ轨迹 + m_raw 差额) + `V65_CHANNEL_COMPATIBILITY_REPORT.md` (分层，双会话，`TEST` identity 附录不含统计，`V57 negative control` 对比) + `v65_invalid_notice.json` (失败时)。CSV/JSON 行对等；本轮仅冻结计划，不创建正式 run_01 decoder 输出。

## 10. 守卫与验收

- **本轮 plan 自检 gate**：`py_compile PASS` 双脚本，`rg "decode_" 0 hits` 双脚本，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-4]/ ==0` (除本变更 + `scripts/` 外零改)，`TEST` 未读统计已验 (`used_test_in_estimation==False`)，`λ` 预注册 `[-2,4]` 且触界即 `MODEL_NOT_STABLE` 不扩已验 (`search_trace` 落盘)，`m_raw` 未 cap 伪装已验 (`m_raw` 显式且 `grep "min(16" 0 hits` 为 cap 伪装检查)，`G1-8` per source 已验，`overall` 五态优先级已验，`CAL 4096+VAL512+TEST120` 双会话隔离已验，`V66 90 30/src 70/90 & 20/30 undetected 0` 预冻结已声明，`DECODE_FORBIDDEN` 保持已验，`run_01` 不存在已验。
- **本轮仅 plan 四工件**，任何 fresh `CAL/VAL/TEST` 实估计需 `Plan SHA` 新 SHA + `v65_data_registry.json` 实表 + G1-8 全 PASS 已验后、且独立 `PLAN_ACCEPT` + `V66 EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODE_FORBIDDEN` 保持至授权。

