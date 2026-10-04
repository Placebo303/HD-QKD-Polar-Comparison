# OpenSpec Spec: formal-ir-v66-single-segment-adaptive-nbldpc

**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + decoder-free spike，不改主体/V64/src，不启动 EVAL decoder，已收缩为单 session 单源 72，m1<1024&&m2<1024，已删 per-source 6/8
**Change**: `formal-ir-v66-single-segment-adaptive-nbldpc` (`V66-ADAPT`, branch `formal-ir-mainline`, HEAD `832e5394bb366927c779414ee5a08427bd740a2d`, data `84d62779`, 单 session `20260123_1M_600k_0dB`)
**Predecessor**: `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) + `formal-ir-v65-new-session-channel-compatibility` — V66 新增单 session 单源自适应门，A-E 全约束，spike 已回填无 TBD

## 1. 变更类型与生命周期

- **Type**: `SINGLE_SEGMENT_ADAPTIVE_VERIFICATION` — 单连续数据段单源内 `CAL 重估 P + VAL CE自适应冗余 (+8 家族, m1/m2 分别) → 密封 EVAL 19/24 overall verified exact` 闭环，为后续独立授权的 EVAL decoder 度量放行门，一次 `CAL24+VAL24+EVAL24=72 overall` 单 session 单源验证（不跨 session 拼接，少 72→DATA_NOT_READY，可复用旧数据但标记 `development_replay`，VAL CE 门禁，**m1<1024 && m2<1024** 满秩嵌套披露 constructibility 先验，EVAL 密封 **19/24 overall 无 per-source**）。
- **Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free spike（`v66_data_readiness.py` + `v66_spike.py` 已回填无 TBD），**不实现 runner，不执行 decoder，不创建 `run_01`，不读 EVAL 统计，不改主体/V64/src**；正式 `run_01` 需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`；`DEVELOPMENT_BENCHMARK` 表示可复用旧单 session 但显式标记且不作 qualification，**m1/m2 分别判，不用 m_total**。
- **Branch**: `formal-ir-mainline`；`HEAD` `832e5394bb366927c779414ee5a08427bd740a2d` 重核，不一致阻塞；本次推送新 Plan SHA 后停止。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) — 单 session 单源复用该处理点；`CAL/VAL/EVAL` 各 24 overall 单源；可复用 `v55_intake_20260828` 单 session `20260123_1M_600k_0dB` 但 `development_replay=true`。
- **Single-source**: 仅 `20260123_1M_600k_0dB`，**已删其余两源**。
- **Rate feasibility**: **m1<1024 && m2<1024**，不用 `m_total<1024`。

## 2. 冻结方法（主体完全冻结，V66 零改，单源）

### 2.1 主体不变量（V64 完全冻结，V66 零改，22/24 PASS，单源）

- `n=1024 symbols/block` (`4×256 frames`), `q=1024 (10-bit s=32*u1+u2, u1=s>>5 0..31, u2=s&31 low)`, `log2 q per plane 5`, `GF32 poly37`, `tag=64 bits/block 仍单 tag 仅 total 计一次`。
- `H1 = V31-H1-QC 16×1024 rank16 80b` 母矩阵；`U =32*U1+U2, F03 5+5 natural` (`U1>>5, U2&31`)。
- `Lane C` ordinal-2 `s38310x`：`m2=184` 单源 base，`support/标签/置换/MET图` 全冻，**不引 MET/protograph/SC**。
- `H_inc1 8×1024 + H_joint1 192×1024` nested；`H_inc2 8×1024 + H_total 200×1024` nested；`H_total_full 216` (`16+m2`)；`rank_total==m2+16, independence_2==8, row≤16, col_inc≤1` 单源。
- `decoder`: `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop` (禁用至 EVAL 授权)；`rescue=verification-only`。
- `leak`: `leak=5*(m1+m2)+64` 其中 `m1,m2` 分别 adapted，`tag` 已含，不重复，V66 不变，**m_total 仅衍生**。
- `verification`: `full-symbol tag s_hat=32*u1_hat+u2_hat compute_tag_64 canonical trunc64` (V64 22/24 PASS)，单64b。
- `budget 自适应预冻结`: `72 overall =24+24+24` 单 session 单源，`EVAL 24` 密封，`m1,m2` 由 `VAL CE` + `+8 家族化` 决定，但需 `m1<1024 && m2<1024` 且满秩嵌套 constructible。
- `V64 终态`: `22/24 full-tag PASS 双口径无 discordance`，`H_total 200 / 216` 单源已固化。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，单源单 session provenance。
- `EVAL` 密封：`EVAL 24 overall` 单源仅 `session_id/frame_ids/blocks` identity，不计 `CE/m`；`C_ab/P/CE/m` 均 `CAL/VAL` 测，`EVAL` 不读。
- `V64 22/24` 结论已作 V66 前提。
- **单源**: 仅 `20260123_1M_600k_0dB`。

### 2.3 禁止

- 禁改任一冻结量、新增矩阵/标签/prior/阈值/decoder、试 `Δ8` 外 degree/seed 网格、跨 session 拼接凑 `72`、将 `min(1024,ceil)` cap 伪装当通过、将 `+8` 外家族当自适应、将 EVAL 另选新 session、将零重叠仅比 `frame_id`、引 `MET/protograph/SC`、改 `src/experiments/tools` 任何文件；禁读 `EVAL` 统计；**m1>=1024 或 m2>=1024** 禁不验而过（**不用 m_total**）；禁 `V55 90` 复用（除 `development_replay` 显式标记单源外永久禁用）；未授 `EXECUTE_AUTH` 前禁 `decode_*`；**禁 per-source 6/8 门禁**。

## 3. Phase A — 数据角色 (单 session 单源 CAL24+VAL24+EVAL24=72 overall)

### 3.1 角色与零重叠（键为 `(source, session_id, frame_id)`，development_replay，单源）

| 集合 | 来源 | overall blocks | 帧数 overall | 说明 |
|---|---|---|---|---|
| CAL | `20260123_1M_600k_0dB` 前 24 | 24 | 96 | `C_ab → P` |
| VAL | 同 session 中间 24，与 CAL 零重叠 | 24 | 96 | `CE → m_raw → m_family → 满秩嵌套` |
| EVAL | 同 session 后 24，与 CAL/VAL 零重叠 | 24 | 96 | 密封 `19/24 overall undetected0` |

- **单 session 单源判定**：`CAL_session_id == VAL_session_id == EVAL_session_id == "20260123_1M_600k_0dB"`，`K=F_s//4=532`，若 `K<72` 或任段 `!=24` 则 `V66_DATA_NOT_READY`。
- **零重叠**：`CAL_key∩VAL_key==∅ && CAL∪VAL_key∩EVAL_key==∅ && CAL∪VAL∪EVAL_key∩(V13∪V48..V64)_key==∅` (键 `(source,session,frame)`)，单源。
- **注册表**：`v66_data_registry.json` (`schema v66_data_v1`) 单源 `20260123_1M_600k_0dB CAL_blocks[24]+VAL_blocks[24]+EVAL_blocks[24]` provenance（键含 `session_id`, `development_replay`），禁止事后换段。
- **可复用旧数据**：复用 `v55_intake_20260828/pairs/20260123_1M_600k_0dB` 单 session `K=532` 前 72 blocks，则 `development_replay=true, replay_source=v55_intake_20260828`，与 fresh 区分，本轮仍 `DEVELOPMENT_BENCHMARK` 不作 qualification。

### 3.2 数据就绪门失败→终态优先级 2

- `K<72` 或 `|CAL|!=24/|VAL|!=24/|EVAL|!=24` → `V66_DATA_NOT_READY` (仅当 `EVIDENCE_INVALID` 未触发时)；`cross_spliced` 或 `frame 256` 违规或 `CE 链式不闭合` → `EVIDENCE_INVALID` 更优先。
- **单源 72 已验**：`F_s=2130 K=532 ≥72`。

## 4. Phase B — 输入合同 strict V56 (U=32*U1+U2, Lane C, 冻结，单源)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, U=32*U1+U2, U1>>5 U2&31, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256` 单源落 `v66_manifest.json`。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U1U2` 原样复用，不重写。
- **G1 隐含**：`materialization_contract_consistent == (算法逐项一致 && 每帧256 && U 映射正确)`。

## 5. Phase C — 单一重估 (CAL-only) + VAL CE 门禁 + 同家族 +8 + 先验校验（单源，m1/m2 分别）

### 5.1 C_ab 与 P_global (CAL-only, 24 blocks 24576 pairs 单源)

```
C_ab[a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum 24576
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, n=1024
```

### 5.2 层级先验与熵/CE (CAL 描述性 + VAL 门禁性，链式双校验，单源)

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  (N_b>0); P_global(a)  (N_b==0)
P(u1|b) = Σ_{u2} P(32*u1+u2 | b)  32×1024
CE1 = -E_VAL log2 P(U1|B)  (VAL 上 单源)
CE2 = -E_VAL log2 P(U2|U1,B)
CE_full = -E_VAL log2 P(A|B)
CE 链式: |CE_full - CE1 - CE2| <1e-9 else EVIDENCE_INVALID
m1_raw = ceil(1.3*1024*CE1/5), m2_raw = ceil(1.3*1024*CE2/5)  (不 cap, 显式 raw, m1/m2 分别)
m_total_raw = m1_raw + m2_raw  # 仅报告，不判 feasibility
m1 = ceil_to_family(m1_raw, +8), m2 = ceil_to_family(m2_raw, +8), m_total=m1+m2  # 族不能覆盖则 MATRIX_NOT_CONSTRUCTIBLE
Δm1 = m1 - m1_raw, Δm2 = m2 - m2_raw
```

- **P表**：同时齐备 `P(U1|B) 32×1024` 与 `P(U2|U1B) 32×32×1024` 扁平供链式 CE 与未来 L1-APP 待用，单源。
- **EVAL 禁用**：`CE/m` 均 `CAL/VAL` 测，`EVAL` 不计任何。

### 5.3 同家族 +8 (预注册，不扩网格，EVAL 隔离，m1/m2 分别)

- `m_family` 在 `H_inc Δ8` 家族中取 `≥m_raw` 的 `+8` 最小档；`m_raw` 显式，不 cap 伪装；第二 estimator 禁止作门禁，违则 `EVIDENCE_INVALID`；族不能覆盖则 `MATRIX_NOT_CONSTRUCTIBLE`。
- `VAL` 测 `CE`，`EVAL` 不反哺；`m` 选择不读 `EVAL`。

### 5.4 先验校验 (decoder-free, m1<1024 && m2<1024 满秩嵌套 disclosure constructibility)

```
m1 <1024 && m2 <1024  # 已改，不用 m_total<1024
rank_m1 = gf_rank(H1(m1)) == m1  (GF32 poly37)
rank_m2 = gf_rank(H2(m2)) == m2
nested = H(m1)⊇H_base_m1 && H(m2)⊇H_base_m2 && 增量 Δ8 行独立
disclosure = 5*(m1+m2)+64
constructible = (m1 in family && m2 in family)  # Δ8 可覆盖 else MATRIX_NOT_CONSTRUCTIBLE
if any fail => V66_RATE_NOT_FEASIBLE  # 含 MATRIX_NOT_CONSTRUCTIBLE
```

## 6. Phase D — EVAL 密封门禁 (24 blocks overall 单源，未执行前仅框架，已删 per-source)

- **报告 schema** 单源：
```
sample: {N_cal 24576/96 frames, N_val 24576/96, N_eval 24576/96 identity, effective_contexts}
prior: {P(U1|B) 32×1024, P(U2|U1B), CE1,CE2,CE_full, chain_delta}
budget: {m1_raw,m2_raw,m_total_raw, m1,m2,m_total, Δm1,Δm2, disclosure 5*(m1+m2)+64, leak_frozen}
code_feasibility: {m1<1024, m2<1024, rank_m1==m1, rank_m2==m2, nested, disclosure_ok, constructible, feasible bool}
eval_identity: {EVAL blocks 24, session_id 20260123_1M_600k_0dB, frame_ids 96, not used in estimation}
gates_future: {exact_full ≥19/24 overall, undetected==0, tag_ok, disclosure}  # 无 per-source
```
- **EVAL 仅 identity**：`EVAL {blocks 24, frames 96}` 不含 `CE/m`，脚本内 `assert not used_eval_in_estimation`。
- **无 per-source**：仅 overall。

## 7. Phase E — 门禁与终态 (EVAL 未执行前仅前三态可判定，已删 per-source)

| 门 | 条件 (overall 单源) | 阈值 frozen |
|---|---|---|
| G_data | `K≥72 && |CAL|=|VAL|=|EVAL|=24 && 单 session 单源 && 零重叠` | 72/24 |
| G_chain | `|CE_full-CE1-CE2|<1e-9` | 1e-9 |
| G_m_raw | `m_raw 未 cap 显式` | `m_raw=ceil(1.3*1024*CE/5)` |
| G_m_family | `m_family = +8 家族化 m1/m2 分别` | `Δ8` |
| G_rank | `m1<1024 && m2<1024 && rank_m1==m1 && rank_m2==m2` | `m<1024 分别 && 满秩` |
| G_nested | `nested` | true |
| G_disclosure | `disclosure==5*(m1+m2)+64` | 5*(m1+m2)+64 |
| G_constructible | `constructible (family +8覆盖)` | true else MATRIX_NOT_CONSTRUCTIBLE |
| G_eval_exact | `exact_full ≥19/24 overall` | 79.17% **无 per-source** |
| G_undetected | `undetected==0` | 0 |

- `G_eval_*` 仅授权执行后验；`DEVELOPMENT_BENCHMARK` 期仅 `G_data..G_constructible` 可判定。

## 8. Phase F — 总体五态 (优先级高→低, exclusive) 与 DEVELOPMENT_BENCHMARK（已删 per-source，已改 m1/m2）

```
if materialization/chain/frame256/cross_spliced/provenance fabricated:
    overall = V66_EVIDENCE_INVALID
elif K<72 or |CAL|!=24 or |VAL|!=24 or |EVAL|!=24:
    overall = V66_DATA_NOT_READY
elif m1>=1024 or m2>=1024 or rank_m1!=m1 or rank_m2!=m2 or not nested or disclosure!=5*(m1+m2)+64 or not constructible or no family H:
    overall = V66_RATE_NOT_FEASIBLE  # 含 MATRIX_NOT_CONSTRUCTIBLE
elif EVAL executed && (exact_full<19/24 or undetected!=0 or not tag_ok):
    overall = V66_ADAPTIVE_EVAL_FAIL  # 仅 overall
elif EVAL executed && exact_full>=19/24 && undetected==0 && disclosure ok:
    overall = V66_ADAPTIVE_EVAL_PASS
else: # EVAL 未执行但前三态已过
    overall = V66_DEVELOPMENT_BENCHMARK_READY
```

- 仅 `ADAPTIVE_EVAL_PASS` 为后续 `EXECUTE_AUTH` 后的成功；其余 `FAIL/INVALID/NOT_READY/RATE_NOT_FEASIBLE（含 MATRIX_NOT_CONSTRUCTIBLE）` 均不进入 qualification；`V66_DEVELOPMENT_BENCHMARK_READY` 表示可申请执行度量 EVAL。

## 9. 脚本与证据写出 (预冻结, 未来执行, decoder-free，已回填无 TBD)

- **固定脚本**（本轮已冻结且 spike 已回填）：
  - `scripts/v66_data_readiness.py`: 单 session 单源 72 检测 + 零重叠（键 `(source,session,frame)`）+ `frame 256` + `单 session 单源` + `development_replay` 标记，输出 `v66_data_registry.json + v66_data_readiness.json`，`rg "decode_" 0 hits`。
  - `scripts/v66_spike.py`: `CAL C_ab/P_global → P(U1|B)/P(U2|U1B) → VAL CE1/CE2/CE_full 链式 → m_raw ceil → m1/m2 +8 aligned → m1<1024 && m2<1024 rank nested disclosure constructibility` 校验，输出 `v66_spike_summary.json + v66_manifest.json + V66_ADAPTIVE_REPORT.md`，`rg "decode_" 0 hits`，`py_compile PASS`，`m_raw` 未 cap，`EVAL` 未用，`CE 链式` 已验，**无 TBD**。
- **证据已回填**：
```
openspec/changes/formal-ir-v66-single-segment-adaptive-nbldpc/  # 本轮 plan 四工件 + registries + report 已回填无 TBD
scripts/v66_data_readiness.py, scripts/v66_spike.py  # decoder-free 已执行
comparison_bench/outputs_comparison/formal_ir_methods/v66_adaptive/  # 未来 EVAL run_01 (本轮不建)
```
- **文件**：`v66_data_registry.json` (authoritative `CAL24+VAL24+EVAL24` 单源 72 实表，`development_replay`) + `v66_data_readiness.json` (G_data) + `v66_spike_summary.json` (CE1/CE2/m1_raw/m2_raw/m1/m2/rank/nested/disclosure/constructibility + overall **无 TBD**, **m1/m2 分别**) + `v66_manifest.json` (H provenance + m差额 + CE 链式 + leak) + `V66_ADAPTIVE_REPORT.md` (分层，单源，`EVAL` identity 附录，不含统计，**无 TBD**) + `review/V66_REVIEW_PACKET.md` 占位；CSV/JSON 行对等；本轮仅冻结计划，不创建正式 run_01，**已单独提交推送新 Plan SHA**。

## 10. 守卫与验收

- **本轮 plan 自检 gate（A-E 已闭合，已回填）**：`py_compile PASS` 双脚本，`rg "decode_" 0 hits` 双脚本，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-5]/ ==0` (除本变更+scripts 外零改)，`EVAL` 未读统计已验 (`used_eval_in_estimation==False`)，`m_raw` 未 cap 伪装已验 (`grep "min(1024" 0 hits` 且 `m_family +8` 显式)，**`m1<1024 && m2<1024 && rank_m1==m1 && rank_m2==m2 && nested && disclosure && constructible`** 已验否则 `RATE_NOT_FEASIBLE`/`MATRIX_NOT_CONSTRUCTIBLE`，`G_data 24/段 72 overall 单 session 单源零重叠 (source,session,frame)` 已验，`development_replay` 已标记，`EVAL 19/24 overall undetected0` 预冻结已声明（**无 per-source**），`DECODE_FORBIDDEN` 保持已验，`run_01` 不存在已验，**无 TBD**。
- **本轮仅 plan 四工件+registry+spike 已回填**，任何 EVAL 实度量需 `Plan SHA 832e5394bb366927c779414ee5a08427bd740a2d` + `v66_data_registry.json` 实表 + `m1<1024 && m2<1024 rank/nested constructible` 已验后、且独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 后才允许创建正式实现并执行；`DECODE_FORBIDDEN` 保持至授权。
