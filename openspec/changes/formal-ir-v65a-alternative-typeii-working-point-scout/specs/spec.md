# OpenSpec Spec: formal-ir-v65a-alternative-typeii-working-point-scout

**Lifecycle**: `PLAN_CANDIDATE → IMPLEMENTATION_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 四工件 + decoder-free scout 已实现并通过 focused tests；真实 Stage0/Stage1 未运行，不改 V65/主候选/src，不启动正式执行
**Change**: `formal-ir-v65a-alternative-typeii-working-point-scout` (`V65A`, branch `formal-ir-mainline`, HEAD `TBD→新SHA`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v65-new-session-channel-compatibility` (`V65` `DATA_NOT_READY` 三源 qualification 保持不动)

## 1. 变更类型与生命周期

- **Type**: `ALTERNATIVE_WORKING_POINT_SCOUT` — 单候选单 session Type-II 备用工作点 decoder-free 勘探，固定顺序 `162148→2500K→160254` 逐一 `4+4` 验证首个通过即停，`256/64` 粗筛仅淘汰，`1024/256` 正式重表征 + `32 TEST` 密封仅规划（`V65 DATA_NOT_READY` 不动，不覆盖其三源语义）。
- **Lifecycle**: `PLAN_CANDIDATE → IMPLEMENTATION_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于四工件、decoder-free scout 脚本与 focused tests（`v65a_scout.py` `rg decode 0 hits`）；**不运行真实 Stage0/Stage1，不执行 decoder，不创建 `run_01`，不读 TEST 统计，不读旧 outcome，不批量物化**；正式 `1024/256` 执行需独立 `PLAN_ACCEPT` + `Pre-RESULT` 复核。
- **Branch**: `formal-ir-mainline`；`HEAD` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核；本次推送新 Plan SHA 后停止。
- **Data SHA**: `84d62779` (`d=1024 bw=200 pairing=nearest rule=legacy_v1`) — 三候选同处理点单点；`V65` 绑定不动；`V65A` 仅换候选 session，不换处理点。

## 2. 冻结方法（主候选完全冻结，V65/V65A 零改）

### 2.1 主候选不变量（V65 完全冻结，V65A 零改）

- `n =1024 symbols/block` (`4×256 frames`), `q =1024 (10-bit s=32*u1+u2)`, `log2 q =5 per plane`, `GF32 poly=37`, `tag=64 bits/block`。
- `H1 = V31-H1-QC 16×1024 rank16 80b`；`Lane C m2 184/190/192 → m_total 216/222/224`；`H_inc1/2 Δ8+Δ8`；`decoder 90/1.0 early-stop` (冻结禁用直至 V65A 正式执行后)。
- `leak =5*(16+m2)+64 =5*m_total+64 =1144/1174/1184` (V65A Type-II 单点按 `m_total 216 → leak 1144` 对齐)。
- `verification`: `full-symbol tag s_hat=32*u1_hat+u2_hat compute_tag_64 canonical trunc64`。
- `V65 终态`: `DATA_NOT_READY` 三源 `4096+512+120` 保持不动，`v65_frozen_session_binding.json` 零改。
- `V65A 候选`: 固定三候选 `2026-01-13 162148` → `2026-01-07 2500K` → `2026-01-07 160254` 首个 `VERIFY_PASS` 即停；相对路径分别为 `2026.1.13/SHG_Type2PPLN_3s_2_2026-01-13_162148/`、`2026.1.7/Type2PPLN_2500K_3s_2026-01-07_174324.1.ttbin`、`2026.1.7/Type2PPLN_3s_2026-01-07_160254.1.ttbin`。

### 2.2 处理点与物化单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024消歧, rule legacy_v1, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，V65A 三候选复用同一处理点；channels、delay、peak、sigma 必须由各候选真实 sidecar/raw 显式给出并独立重算，禁止默认通道值。

### Provenance tiers

- **A**：未影响 V36–V64 NB-LDPC 的 prior、矩阵、标签、码率、门禁或解释；完成外部使用账本后可作未来独立 TEST。
- **B**：早期用于 Polar、Cascade 或无关分析，但未影响当前 NB-LDPC；仅作 development/generalization。
- **C**：参与 V36–V64 当前 NB-LDPC 决策；仅作回归/机制检查。

仓库检索未发现三候选进入 V36–V64 NB-LDPC 注册表，当前均列 **B-provisional**，并保留 basis/uncertainty；这不是最终 A 结论。`162148` 的两个本地 meta 文件指向 `D:\SPDC源测试`，属于 Stage0 provenance blocker，不能通过。
- `TEST 32` 密封：`32 frames 8192 pairs 8 blocks` 仅 `session_id/frame_ids/blocks` identity，不计任何 `H/CE/NLL` 统计；`C_ab/P_global/λ` 均 `CAL`-only；旧 outcome 禁读。

### 2.3 禁止

- 禁改任一冻结量、新增矩阵/标签/prior/阈值/decoder、批量物化三候选、读旧 outcome、以粗筛宣称 READY、调 `m2/leak`、改 `src/experiments/tools` 任何文件（只读复用）；禁读 `TEST` 统计；`λ` 触界禁扩网格；禁 `V65` 语义 reinterpret；未授 `PLAN_ACCEPT` 前禁正式 `1024/256` 全量至 READY。

## 3. Phase A — 固定顺序与 4+4 最小验证（Batch 禁止，首个通过即停）

### 3.1 候选与验证（键为 `(candidate, frame_id)`）

| 候选 | session | 帧数 | pairs | 验证 |
|---|---|---|---|---|
| `2026-01-13 162148` (序1) | 单 session | 4+4=8 | 2048 | `G-verify` 首个候选 |
| `2026-01-07 2500K` (序2) | 单 session | 4+4=8 仅前一 FAIL 时物化 | 2048 | `G-verify` 次选 |
| `2026-01-07 160254` (序3) | 单 session | 4+4=8 仅前二 FAIL 时物化 | 2048 | `G-verify` 末选 |

- **固定顺序**：`candidates_ordered = ["2026-01-13 162148","2026-01-07 2500K","2026-01-07 160254"]` 冻结，不以数据可用性重排；脚本启动 `assert candidates_ordered == frozen_order`。
- **首个通过即停**：`selected = first cand where VERIFY_PASS else none`；`materialized_candidates_count == (index(selected)+1 if selected else 3)`；后续候选 `not_materialized`。
- **Batch 禁止**：仅对当前 `cand` `materialize_frames(cand, 8)`，禁止 `load_all_three`；守卫 `materialized_frames_total == 8 * materialized_candidates_count` 在 Stage0（`<=24`）。
- **Frame 定义**：`frame_id∈[0,F_s-1]`，`pairs_per_frame 256`，`BLOCK 4×256`，`frame_ids exact` 逐帧校验，`A=32U1+U2 B=32V1+V2`。

### 3.2 G-verify 门（per candidate 8 frames）

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, candidate-specific distinct channels, delay_used_ps, peak_center, sigma ∈[50,150], p2bg, gate 200, threshold 40000, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256 A=32U1+U2 B=32V1+V2` 逐项显式落盘，与 V56 权威算法逐项一致已验（`delay` 仅 `sign+50ps` 门禁，不强制等于 V65 数值）。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U1U2` 原样复用算法，不重写；候选 `peak` 独立重算，失败则 `VERIFY_FAIL → EVIDENCE_INVALID` 子类。
- **G-verify**：`VERIFY_PASS_cand = (dimension==1024 && bin==200 && pairing==nearest && assignment==double_pointer_bin_div_dimension && channels显式且不同 && provenance匹配候选 && rule==legacy_v1 && sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150] && gate==200 && threshold==40000 && period==204800 && 每帧256 A/B映射)`，否则 `VERIFY_FAIL` 进入下一候选；缺字段或冲突只报 `DATA_NOT_READY/INCOMPATIBLE`。
- **注册表**：`v65a_registry.json` per candidate `VERIFY_PASS/FAIL` + `provenance逐项 {session_id, delay_used_ps, peak_center, sigma, gate, threshold, frame_anchor, mapping, channels_used, provenance_path, fail_reason}` + `materialized_frames 8`。

## 4. Phase B — 256/64 粗筛（selected only，仅淘汰不能 READY）

### 4.1 粗筛切片（selected only）

- **输入**：`selected` 候选单 session 的 `256 frames CAL (65536 pairs) +64 frames VAL (16384 pairs)`，与 Stage0 8帧零重叠（`CAL 256 ∩ VAL 64 ∩ Stage0 8 ==∅` per candidate），不跨 candidate 拼接。
- **Stage1 阈（放宽，仅淘汰）**：`G2 λ不触界, G3 ΔNLL≤0.75, G4 Val NLL≤H_cal+1.5, G5 unseen≤0.02, G6 m1≤16, G7 m2≤200, G7-aux m_total≤216, G8 provenance+CE链式<1e-9`，任一 FAIL 或 CAL/VAL 样本不足 → `V65A_COARSE_REJECTED/DATA_NOT_READY` 终态，不进 Stage2；全过 → `V65A_ELIGIBLE_FOR_FORMAL` 仅放行规划，绝不为 READY。

### 4.2 估计器（Stage1 粗筛，同 Stage2 算法，粗筛阈放宽）

```
C_ab = bincount2d(a_cal,b_cal) 1024×1024 sum 65536 (Stage1) / 262144 (Stage2 planned)
P_global(a) = Σ_b C_ab / N_cal
P_λ(a|b) = (C_ab + λ P_global)/(N_b+λ) (N_b>0) else P_global
P_λ(u1|b) 32×1024, CE1=-E_VAL log P_λ(U1|B), CE2=-E_VAL log P_λ(U2|U1B), CE_full=-E_VAL log P_λ(A|B)
CE链式: |CE_full-CE1-CE2|<1e-9 else EVIDENCE_INVALID
m1=ceil(1.3*1024*CE1/5), m2=ceil(1.3*1024*CE2/5), m_total=m1+m2 (不 cap)
λ域 log10 [-2,4] (λ∈[1e-2,1e4]), Stage1 粗筛 50-point grid + Brent 或 2-fold CV 粗筛
```

- **λ 触界**：`λ_at_boundary → REJECT`（Stage1）/ `MODEL_NOT_STABLE`（Stage2），不扩网格；禁第二 estimator。
- **报告**：`per_selected {λ*, at_boundary, CV_NLL*, Val NLL=CE_full, ΔNLL, H_cal/H1/H2 chain_delta_H, CE1/CE2/CE_full chain_delta_CE, MAP, q_mass_unseen, effective_contexts, m1/m2/m_total Δm/Δleak, gates G1..G8 coarse, overall}`，`coarse_cannot_ready==true` 已验（`overall != READY`）。

## 5. Phase C — 1024/256 正式重表征与 32 TEST 密封（本轮仅规划）

### 5.1 正式切片（planned）

- **规模**：`CAL 1024 frames 262144 pairs + VAL 256 frames 65536 pairs + TEST 32 frames 8192 pairs 8 blocks`，同一 `selected` session 内互斥零重叠（`CAL 1024 ∩ VAL 256 ∩ TEST 32 ==∅`，且与 Stage0 8 / Stage1 320 已用帧零重叠），`session_id` 同一。
- **正式阈（与 V65 一致，仅规划）**：`G2 λ不触界, G3 ΔNLL≤0.50, G4 Val NLL≤H_cal+1.0, G5 unseen≤0.01, G6 m1≤16, G7 m2≤200, G7-aux m_total≤216, G8 provenance+CE链式<1e-9` 全过才 `FORMAL_READY`（本轮仅声明阈，执行后判定）。

### 5.2 TEST 密封（planned, 仅 identity）

- **密封**：`v65a_registry.json: sealed_test {session_id==selected, frames[32] exact (frame_ids, blocks 8, pairs 8192, provenance), zero_overlap_verified (key=(candidate, frame_id)), not_used_in_estimation}`，不计 `H/CE/NLL`，脚本内 `assert not used_test_in_estimation`。

### 5.3 终态（V65A 独立，V65 不动）

```
if none VERIFY_PASS in Stage0:
    overall = V65A_NO_CANDIDATE_PASSED_VERIFICATION
elif Stage1 coarse REJECT:
    overall = V65A_COARSE_REJECTED
elif Stage1 ELIGIBLE_FOR_FORMAL:
    overall = V65A_ELIGIBLE_FOR_FORMAL_RECHARACTERIZATION  # 本轮终态上限，not READY
# 正式执行后（需新 PLAN_ACCEPT）才可能：
#   V65A_FORMAL_READY / V65A_MODEL_NOT_STABLE / V65A_RATE_INCOMPATIBLE / V65A_EVIDENCE_INVALID
```

- **V65 不动**：`git diff -- openspec/changes/formal-ir-v65-new-session-channel-compatibility/ ==0`，`V65 DATA_NOT_READY` 保持，V65A 结论不 reinterpret V65。

## 6. 脚本与证据写出（预冻结，decoder-free）

- **固定脚本**（本轮仅冻结计划，spike 可 decoder-free dry-run）：
  - `scripts/v65a_scout.py`: `candidates_ordered 冻结 → Stage0 8帧逐一 verify (首个PASS即停, batch守卫) → Stage1 256/64 coarse (selected only, 仅淘汰, rg decode 0 hits, rg old_outcome 0 hits) → Stage2 formal 1024/256+32 TEST 规划 (不读 TEST 统计, 不创建 run_01)`，输出 `v65a_scout.json + v65a_manifest.json + V65A_SCOUT_REPORT.md`，`py_compile PASS`，`m_raw CE-based 未 cap`，`λ触界不扩`，`CE链式` 已验。
- **增量根**（未来正式执行，decoder 前建，fail-closed，**本轮不创建 run_01**，仅冻结计划）：
  ```
  openspec/changes/formal-ir-v65a-alternative-typeii-working-point-scout/  # 本轮四工件 + registries + report
  scripts/v65a_scout.py  # decoder-free
  comparison_bench/outputs_comparison/formal_ir_methods/v65a_scout/  # 未来 formal 执行时 run_01 (本轮不建)
  ```
- **文件**：`v65a_registry.json` (authoritative `candidates_ordered + Stage0 8帧 + Stage1 256/64 + formal 1024/256 + sealed 32 TEST identity`) + `v65a_scout.json` (per candidate/stage H/CE/λ/NLL/MAP/m/Gates + overall) + `v65a_manifest.json` (provenance, HEAD/data SHA, materialized_frames_total, batch_guard, order_guard, λ轨迹, CE链式, leak 1144) + `V65A_SCOUT_REPORT.md` (分层，`粗筛仅淘汰` + `首个通过即停` + `V65不动` 声明) + `v65a_invalid_notice.json` (失败时)。本轮仅冻结计划，不创建正式 run_01 decoder 输出。

## 7. 守卫与验收

- **本轮 plan 自检 gate**：`py_compile PASS`，`rg "decode_" 0 hits` 且 `rg "old_outcome|outcome\\.json" 0 hits`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v65-new-session-channel-compatibility/ ==0` (除本变更 + `scripts/` 外零改)，`TEST 未读统计` 已验 (`used_test_in_estimation==false`)，`λ` 预注册 `[-2,4]` 且触界即 `REJECT/MODEL_NOT_STABLE` 不扩已验 (`search_trace` 落盘)，`m_raw CE-based` 未 cap 已验 (`grep "min(16" 0 hits` 为 cap 伪装检查，且 `m_total 216` 辅助)，`G-verify + G1..G8 coarse` 已验（含 `sign/50ps` + `CE链式 |CE_full-CE1-CE2|<1e-9`），`overall` 互斥 `NO_CANDIDATE > COARSE_REJECTED > ELIGIBLE_FOR_FORMAL` 已落盘，`batch_materialization==false` (`materialized_frames_total ==8*checked + (selected?320:0)` 在本轮) 已验，`candidates_ordered` 固定且首个通过即停已验，`old_outcome_not_read==true` 已验，`DECODE_FREE` 保持已验，`run_01` 不存在已验。
- **本轮仅四工件**，任何 `1024/256` 正式执行需 `Plan SHA` 新 SHA + `v65a_registry.json` 实表 + `Stage1 ELIGIBLE_FOR_FORMAL` 已验后、且独立 `PLAN_ACCEPT` 后才允许创建正式实现并执行；`DECODE_FREE` 保持至授权。
