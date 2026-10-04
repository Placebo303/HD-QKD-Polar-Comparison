# OpenSpec Design: formal-ir-v65a-alternative-typeii-working-point-scout — V65AR1 (intra-family rate-adaptive, NB-LDPC main frozen)

**Lifecycle**: `PLAN_CANDIDATE → IMPLEMENTATION_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **仅 decoder-free 勘探，固定顺序 162148→2500K→160254，4+4首个通过即停，256/64粗筛仅淘汰(不授RATE_READY)，1024/256正式+32 TEST规划，V65不动；真实 Stage0/Stage1 尚未运行；V65AR1 允许同家族内 `P(U1|B)/P(U2|U1B)` 重估计调 m1/m2**
**Cycle**: `V65A` / `V65AR1` (alternative-typeii-working-point-scout R1 intra-family rate adaptation), predecessor `V65` `DATA_NOT_READY` (非模型/码率失败，纯 session 未就绪；三源 qualification 不动)
**Branch**: `formal-ir-mainline` HEAD `0131313177a6f2a52319b6354cc62477f4685b49` (已核 `HEAD==origin/formal-ir-mainline`；推送前重核) data SHA `84d62779` (d1024 bw200 nearest legacy_v1 单点)
**Feasibility**: V65 仅因冻结 CAL/TEST session 仍为 `PENDING` 而停在 `DATA_NOT_READY`；当时 `λ/CE/m` 均为 null，未证明模型或码率失败。V65A 转向**单候选单 session Type-II 备用点**，以最小物化代价逐一验证 materialization 合同，若首候选 `4+4` 即通过则进入 `256/64` 粗筛淘汰明显不兼容者，最后以 `1024/256` 重表征密封 `32 TEST`。零 decoder 闭环。V65AR1 保持 NB-LDPC 主方向，仅同家族内码率适配：`m1=ceil(1.3*1024*CE1/5) m2 同` 无 cap/floor，分流 `MODEL_NOT_STABLE/FROZEN_RATE_COMPATIBLE/RATE_ADAPTATION_REQUIRED(<1024)/FULL_DISCLOSURE(≥1024)`，Stage1 永不 READY，Stage2 仍仅规划。

## 1. 科学问题与关键判断

> 在**完全冻结 V65 主候选**（`H1-16+Lane C m2 184/190/192+Δ8+Δ8+full-tag`）仍 `DATA_NOT_READY` 的前提下，是否存在**单 session Type-II 备用工作点**（三候选固定顺序 `162148→2500K→160254`）能在相同 `dimension 1024 / bin200 / nearest / legacy_v1 / 每帧256 A=32U1+U2 B=32V1+V2` 处理点下，通过 `sign(delay)==sign(peak) && |delay-peak|<50ps` 等 materialization 门禁，并在 `256/64` 粗筛不被淘汰、进而在 `1024/256` 正式重表征上 `CE门禁 m=ceil(1.3*1024*CE/5)` 落在冻结构内？本变更仅验证**物化合同**与**先验稳定性**的 decoder-free 前置，`READY` 需正式执行后独立判定。

- **对照**：V65 三源 `4096+512` hierarchical `λ∈[1e-2,1e4]` 未通过 `G6/G7` 容量；V65A 不重跑 V65 三源，仅以 `8` 帧最小代价先验证单 session 物化合同正确性，再以 `256/64` 快速淘汰 `CE` 明显过高者，减少 `1024/256` 无效重表征。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest double-pointer bin//1024消歧 / rule legacy_v1 / frame_period 204800ps / BLOCK 4×256 / F03 5+5 natural / frame anchor floor_div / mapping legacy_v1` 为跨 session 算法不变量；`delay/peak/sigma/gate/threshold/channels` 为候选 session 独立重算但算法一致量（`sign+50ps` 门禁）。
- **勘探性质**：纯 decoder-free，`V65A` 与 `V65` 解耦，`V65 DATA_NOT_READY` 保持，V65A 结论不 reinterpret V65。

## 2. 冻结语义 — V65 主候选与处理点零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64/V65 |
| m2 per source (frozen) | 184/190/192 (L2) → m_total 216/222/224 (full 16+m2) | Lane C ordinal-2 |
| m1 | 16 | V31-H1-QC 16×1024 |
| leak | `5*(16+m2)+64 =5*m_total+64 =1144/1174/1184` | V64/V65 |
| 处理点 | `d1024 bw200 nearest legacy_v1 200ps` 单点 `84d62779` | V55/V56/V65；通道与 timing 参数必须由候选 sidecar/raw 显式提供 |
| V56 contract | `dimension 1024 / bin200 / nearest legacy_v1 / channels/frame anchor/mapping per frame 256 A=32U1+U2 B=32V1+V2 + 峰/延时算法` | V56 权威 |
| V65 终态 | `DATA_NOT_READY` 三源 `4096+512+120` | V65 保持不动 |
| V65A 候选 | 固定三候选 `162148 → 2500K → 160254`，首个 `VERIFY_PASS` 即停 | 本变更冻结 |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder/prior`；零 decoder 直至正式执行；`V65` 目录零改；`TEST 32` 密封仅 identity 不读统计；批量物化三候选禁止；旧 outcome 禁读。

## 3. 候选与阶段 — 固定顺序首个通过即停（Batch 禁止）

### 3.1 候选定义（固定顺序，不可重排）

| 序 | 候选 session | 期望路径片段 (PROJECT_DATA_ROOT 下) | 备注 |
|---|---|---|---|
| 1 | `2026-01-13 162148` | `.../2026.1.13/SHG_Type2PPLN_3s_2_2026-01-13_162148/` | 首选；本地双 meta 的外部 provenance 冲突必须阻断 |
| 2 | `2026-01-07 2500K` | `.../2026.1.7/Type2PPLN_2500K_3s_2026-01-07_174324.1.ttbin` | 次选；本地 raw 已盘点，sidecar 待候选自带 |
| 3 | `2026-01-07 160254` | `.../2026.1.7/Type2PPLN_3s_2026-01-07_160254.1.ttbin` | 末选；本地 raw 已盘点，sidecar 待候选自带 |

- **顺序冻结**：`candidates_ordered[0] > [1] > [2]` 优先级高→低，不以数据可用性、历史性能、文件大小重排。脚本启动即 `assert candidates_ordered == frozen_order`。
- **停止规则**：`for cand in candidates_ordered: verify 8 frames; if PASS: selected=cand; break`。`selected` 后不再物化后续候选，`materialized_candidates_count == index(selected)+1`。
- **Batch 禁止**：脚本内仅对当前 `cand` 调用 `materialize_frames(cand, n=8)`，禁止循环外一次性 `for cand in candidates: load_all`。优先读取候选本地已有 pairs/sidecar；缺 path/sidecar 时不读 raw 补齐。守卫 `materialized_frames_total <= 8 * checked` 在 Stage0。

### 3.2 Provenance tier 与当前候选的 provisional 分类

| Tier | 定义 | 允许用途 |
|---|---|---|
| A | 未影响 V36–V64 NB-LDPC 的 prior、矩阵、标签、码率、门禁或解释 | 完成外部使用账本后可作未来独立 TEST |
| B | 早期用于 Polar、Cascade 或无关分析，但未影响当前 NB-LDPC | development/generalization，不直接作独立 TEST |
| C | 参与 V36–V64 当前 NB-LDPC 决策 | 仅回归/机制检查 |

仓库只读检索未发现三候选进入 V36–V64 NB-LDPC 注册表，因此当前均记为 **B-provisional**：`162148` 有早期 PIESKR 元数据，`2500K` 与 `160254` 有早期 Type-II raw inventory。该分类不是最终 A 资格；外部使用账本尚不完整，若发现当前 NB-LDPC 影响则立即改为 C，只有完成“不影响当前决策”的显式核对后才可改为 A。`162148` 的本地两个 meta 文件还指向 `D:\SPDC源测试`，与实际候选目录冲突，必须在 Stage0 阻断。

### 3.2 阶段递进（含物化预算）

| 阶段 | 输入 | 物化帧 | pairs | 产出 | 门禁性质 | 本轮是否执行 |
|---|---|---|---|---|---|---|
| Stage0 verify | 每候选单 session | 4+4 =8 | 2048 | `VERIFY_PASS/FAIL` per candidate | 硬门 (G-verify) | 🔒 脚本已实现，本轮未运行真实数据 |
| Stage1 coarse | selected only | 256 CAL +64 VAL =320 | 81920 | `REJECT / ELIGIBLE_FOR_FORMAL` | 仅淘汰，不能 READY | 🔒 脚本已实现，本轮未运行真实数据 |
| Stage2 formal | selected only | 1024 CAL +256 VAL +32 TEST =1312 | 335872 | `FORMAL_READY / RATE_INCOMPATIBLE / MODEL_NOT_STABLE` | 正式门禁 | 🔒 仅规划，本轮不执行全量计算 |

- **后续执行物化上限**：若 Stage0 在候选1即 PASS，则 Stage0+Stage1 最多 `8 + 320 =328 frames (83968 pairs)`；若候选1 FAIL 候选2 PASS，则 `16 +320=336 frames`；最差三候选均 FAIL 则 `24 frames` 即停。本轮只做编译与 focused fake 测试，不物化真实候选；Stage2 `1312 frames` 仅规划，不在本轮物化至 `READY`（需新 PLAN_ACCEPT）。
- **Frame 定义**：`FRAME=256 pairs`, `frame_id∈[0,F_s-1]` 连续，`BLOCK 4×256=1024 symbols`，`pairs_per_frame 256` 校验，`A=32U1+U2 B=32V1+V2` 每帧。

## 4. 输入合同 — 严格复用 V56 权威算法（逐项显式，sign/50ps 门禁）

### 4.1 合同清单（8帧验证逐项，候选单 session）

| 阶段 | 参数 | 冻结值 (V56 算法) | V65A 记录与门禁 |
|---|---|---|---|
| 1 | dimension | 1024 | per frame，算法一致 |
| 2 | bin_width | 200 ps | global，算法一致 |
| 3 | pairing | `nearest`, double-pointer `bin//1024` 消歧 | `pair_sequence a=binA%1024,b=binB%1024` 算法一致 |
| 4 | rule/mapping | `legacy_v1` | `sym → U1/U2` 算法一致 |
| 5 | channels | 候选 sidecar/raw 显式给出一对 distinct channels；不预设数值 | `counts per channel` 算法一致，落盘 `channels_used` |
| 6 | delay | `delay_used_ps` 候选独立重算 peak 后 `sign(delay)==sign(peak) && |delay-peak|<50ps` | `delay_used_ps` per candidate |
| 7 | peak/sigma/gate/threshold | `peak_center` 独立重算, `sigma 50-150ps, gate 200ps, threshold 40000ps` | 每 candidate 实测 |
| 8 | frame anchor | `frame_start_ps / period 204800ps / floor_div` | `204800=1024×200` 配对尺度 |
| 9 | mapping | `legacy_v1` symbol `0..1023` | `alice/bob symbols` |
| 10 | U1/U2 | `A=32U1+U2, B=32V1+V2, U1=sym>>5, U2=sym&31, 每帧256` | per pair |

- **只读复用**：优先读取候选目录内已有 pairs/sidecar；只有当前候选 provenance、channels、timing 与处理参数闭合后，才按需复用 `src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags/_bin_indices_sorted_for_binwidth/_pairs_from_sorted_bins` + `legacy_v1` mapping 的 V56 验证版算法，不重写近似版。sidecar 缺失、多个冲突、路径指向外部位置或 candidate-specific 参数缺失时，先报 `DATA_NOT_READY/INCOMPATIBLE`，不以默认值补齐。
- **8帧校验**：对 `4+4` 的 8 帧输出 `alice_symbols[8×256], bob_symbols[8×256]`，校验 `A/B ∈[0,1023]` 且 `F03 U1>>5 &31` 可分解，缺失/非 `256` 则 `VERIFY_FAIL`。
- **G-verify**：`VERIFY_PASS_s = (dimension==1024 && bin==200 && pairing==nearest && assignment==double_pointer_bin_div_dimension && rule==legacy_v1 && channels_explicit_and_distinct && provenance_matches_candidate && sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150] && gate==200 && threshold==40000 && period==204800 && 每帧256 A/B映射)`，任一 False 则 `VERIFY_FAIL` 进入下一候选；缺证据与显式冲突不能当作 PASS。

## 5. 估计器 — 单一 hierarchical（Stage1 粗筛与 Stage2 正式同算法，Stage2 仅规划）

### 5.1 联合计数与全局先验（Stage1 256 CAL / Stage2 1024 CAL）

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal  shape 1024, Σ=1
Q=1024, n=1024
Stage1: N_cal=256*256=65536, N_val=64*256=16384
Stage2: N_cal=1024*256=262144, N_val=256*256=65536, N_test=32*256=8192 (identity only)
```

### 5.2 分层条件分布与熵/CE（链式双校验，R65A-05/06）

```
P_λ(a|b) = (C_ab + λ P_global(a)) / (N_b + λ)  if N_b>0 else P_global(a)
P_λ(u1|b) = Σ_{u2} P_λ(32*u1+u2 | b)  32×1024
CE1(λ*) = -E_VAL[ log2 P_λ*(U1|B) ]  (门禁性, VAL上)
CE2(λ*) = -E_VAL[ log2 P_λ*(U2|U1,B)]
CE_full(λ*) = -E_VAL[ log2 P_λ*(A|B)]
CE 链式: |CE_full - CE1 - CE2| < 1e-9 else EVIDENCE_INVALID
m1 = ceil(1.3*1024*CE1/5), m2 = ceil(1.3*1024*CE2/5), m_total=m1+m2  (不 cap/floor/handfill, 禁 min(16,..) 伪装)
H_cal 描述性仅报告，不入粗筛硬门；CE 门禁性。
required rate 分流(与 Stage1/Stage2 阈正交，MODEL_NOT_STABLE 优先):
  MODEL_NOT_STABLE: λ触界或 ΔNLL/unseen 失败等模型失稳
  FROZEN_RATE_COMPATIBLE: 稳定且 m1≤16 && m2≤200 && m_total≤216 (冻结构内)
  RATE_ADAPTATION_REQUIRED: 稳定但超旧容量且 m1<1024 && m2<1024 && m_total<1024 (同家族内预注册相邻档位可调)
  FULL_DISCLOSURE_LAYER: 任一 m≥1024 (≥n, 需 full disclosure 层, 非 Lane C 家族内)
V65AR1 保持 Lane C 家族/L1APP/条件增量/full-tag 仅调 m1/m2，增量仅未来预注册相邻档位，本轮不创建后继 change。
```

### 5.3 λ 搜索协议

```
λ_search_domain = log10 λ ∈ [-2, 4]  continuous  (λ∈[1e-2,1e4])
Stage1 coarse: CAL 256 切 2 folds 各128 frames 或 4 folds各64 frames (二选一冻结为 2-fold 粗筛)，目标 Cal-CV NLL(λ)
Stage2 formal: CAL 1024 切 4 folds各256 frames/65536 pairs，目标 Cal-CV NLL(λ)
chosen λ* = argmin via 50-point log grid + Brent refine
λ_at_boundary = (log10 λ* ≤ -2+ε || ≥4-ε) → MODEL_NOT_STABLE (Stage1 粗筛触界→REJECT, Stage2触界→MODEL_NOT_STABLE)
单 hierarchical 一路为门禁，禁第二 estimator
```

- **粗筛阈（R65A-04/05，仅淘汰不授 READY/RATE_READY）**：`G2 λ不触界, G3 ΔNLL≤0.75(放宽 vs V65 0.50), G4 Val NLL≤H_cal+1.5(放宽), G5 unseen≤2%, G6 m1≤16, G7 m2≤200(按 Type-II 单点, 三档收敛为单阈), G7-aux m_total≤216, G8 provenance+CE链式` — 粗筛任一 FAIL → `REJECT`；粗筛全过 → `ELIGIBLE_FOR_FORMAL`（不为 READY/RATE_READY）；Stage1 永不 READY。
- **正式阈（R65A-07 仍仅规划，正式至少 CAL1024 VAL256 sealed TEST32 才判 FROZEN/ADAPTATION）**：`G2 λ不触界, G3 ΔNLL≤0.50, G4 Val NLL≤H_cal+1.0, G5 unseen≤1%, G6 m1≤16, G7 m2≤200, G7-aux m_total≤216, G8 provenance+CE链式` 全过才 `FORMAL_READY`（本轮仅规划，执行后判定）；`RATE_ADAPTATION_REQUIRED/FULL_DISCLOSURE` 仅正式判且 MODEL_NOT_STABLE 优先。

## 6. 每源报告与泄漏预算（Stage1 字段定义，Stage2 规划）

### 6.1 报告量（per selected candidate, Stage1 实测 + Stage2 规划）

```
样本: Stage0 8 frames/2048 pairs per candidate + Stage1 N_cal 65536/256, N_val 16384/64 + Stage2 planned N_cal 262144/1024, N_val 65536/256, N_test 8192/32 identity
先验: λ* coarse, λ_at_boundary, CV_NLL*, Val NLL, ΔNLL, CE1/CE2/CE_full + chain_delta
泛化: MAP_acc_val, q_mass_unseen, effective_contexts
预算(CE 门禁): m1=ceil(1.3*1024*CE1/5), m2=ceil(1.3*1024*CE2/5), m_total=m1+m2, Δm vs frozen (16/200/216, leak 1144)
TEST 仅 identity (Stage2 32 frames) 不计统计
```

### 6.2 32 TEST 密封（Stage2，仅规划）

- `TEST 32 frames =8192 pairs =8 blocks (4×256)`，`session_id` 与 `CAL/VAL` 同一候选 session 内但 `frame_ids` 零重叠（`CAL 1024 + VAL 256 + TEST 32` 互斥），不计 `H/CE/NLL`，仅 `frame_ids[32]/blocks 8` identity 落盘 `v65a_registry.json: sealed_test {session_id, frames[32], blocks 8, pairs 8192, provenance}`。

## 7. 门禁 — Stage0 G-verify 与 Stage1 粗筛、Stage2 正式（含 G7-aux）

| 门 | Stage0 G-verify (per candidate 8 frames) | Stage1 coarse (selected, 256/64, 仅淘汰) | Stage2 formal (selected, 1024/256, 仅规划) |
|---|---|---|---|
| G1 | `contract_consistent && sign/50ps && sigma/gate/threshold` | 同 G-verify 复用 | 同 |
| G2 | — | `λ_at_boundary==False` else REJECT | `λ_at_boundary==False` else MODEL_NOT_STABLE |
| G3 | — | `ΔNLL ≤0.75` else REJECT | `ΔNLL ≤0.50` else MODEL_NOT_STABLE |
| G4 | — | `Val NLL ≤ H_cal+1.5` else REJECT | `Val NLL ≤ H_cal+1.0` else MODEL_NOT_STABLE |
| G5 | — | `unseen ≤0.02` else REJECT | `unseen ≤0.01` else MODEL_NOT_STABLE |
| G6 | — | `m1 ≤16` else REJECT | `m1 ≤16` else RATE_INCOMPATIBLE |
| G7 | — | `m2 ≤200` else REJECT | `m2 ≤200` else RATE_INCOMPATIBLE |
| G7-aux | — | `m_total ≤216` else REJECT | `m_total ≤216` else RATE_INCOMPATIBLE |
| G8 | `provenance完整 && frame256` else VERIFY_FAIL | `provenance_zero_overlap && CE链式<1e-9` else REJECT | 同 Stage1 |

- **Stage0**：`VERIFY_PASS` 仅表示物化合同正确，不表示信道兼容；`VERIFY_FAIL` 含 `EVIDENCE_INVALID` 子类（`channel/peak/sigma/gate/threshold/frame anchor/mapping` 算法偏离或 `frame 256` 非 `A=32U1+U2`）。
- **Stage1**：`REJECT` 为终态之一，`ELIGIBLE_FOR_FORMAL` 仅放行至 Stage2 规划，不为 `READY`。
- **Stage2**：本轮仅 freeze 阈与计划，不执行全量判定；正式执行后五态 `EVIDENCE_INVALID > REJECT/MODEL_NOT_STABLE > RATE_INCOMPATIBLE > FORMAL_READY`。

## 8. 终态（V65A 独立，V65 不动）

```
if Stage0 all three VERIFY_FAIL:
    overall = V65A_NO_CANDIDATE_PASSED_VERIFICATION  # 8帧均未通过，无选定
elif Stage1 coarse REJECT (selected fails coarse):
    overall = V65A_COARSE_REJECTED  # 明显不兼容，不进正式
elif Stage2 planned (selected ELIGIBLE_FOR_FORMAL):
    overall = V65A_ELIGIBLE_FOR_FORMAL_RECHARACTERIZATION  # 本轮终态，仅规划，不为 READY
# 正式执行后（需新 PLAN_ACCEPT）才可能：
#   V65A_FORMAL_READY / V65A_MODEL_NOT_STABLE / V65A_RATE_INCOMPATIBLE / V65A_EVIDENCE_INVALID
```

- **仅 Stage2 正式执行后才允许 `FORMAL_READY`**；`V65 DATA_NOT_READY` 全程不变，`git diff -- v65 ==0`。
- **本轮终态上限**：`ELIGIBLE_FOR_FORMAL_RECHARACTERIZATION`，不直接 `FORMAL_READY`。

## 9. 脚本与报告（decoder-free 守卫）

- **脚本 `scripts/v65a_scout.py`** (decoder-free):
  `python scripts/v65a_scout.py [--stage verify|coarse|formal|all] [--candidate-root PROJECT_DATA_ROOT] [--out v65a_scout.json]`
  → `candidates_ordered 冻结 → Stage0 8帧逐一 verify (首个PASS即停, 守卫 materialized_frames_total) → Stage1 256/64 coarse (selected only, 仅淘汰) → Stage2 formal 1024/256+32 TEST 规划 (不读 TEST 统计) → overall 五态 → 报告`，`rg "decode_" 0 hits` `rg "old_outcome" 0 hits`，`py_compile PASS`；输出 `v65a_scout.json + V65A_SCOUT_REPORT.md + v65a_registry.json + v65a_manifest.json` + 控制台摘要；校验 `TEST 未参与` 及 `m_raw CE-based 未 cap` 及 `CE链式`。
- **报告 `V65A_SCOUT_REPORT.md`**：三候选 `VERIFY_PASS/FAIL` 明细（8帧 provenance 逐项）+ selected `Stage1 256/64` 实报（λ/CE/ΔNLL/unseen/m）+ Stage2 `1024/256` 规划与 `32 TEST` 密封 identity + `materialized_frames_total` 守卫 + `V65 不动` 声明 + `粗筛仅淘汰` 声明，不含 `FER/阈值/SKR`。
- **守卫**：`DECODE_FREE` 保持、`batch_materialization==false`、`old_outcome_not_read==true`、`run_01` 不存在、`TEST 未读统计`、`λ触界不扩`、`m_raw 未 cap`、`CE链式`、`固定顺序`、`首个通过即停`。

## 10. 与 V65 衔接（V65 保持 DATA_NOT_READY）

- V65 `DATA_NOT_READY` 三源 `4096+512+120` 语义与 `v65_frozen_session_binding.json` 全程零改，V65A 为独立 `alternative` 勘探，不复用 V65 outcome，不以 V65 失败调候选顺序。
- V65A 若达 `ELIGIBLE_FOR_FORMAL`，正式 `1024/256` 执行需另起 `PLAN_ACCEPT` + `Pre-RESULT` 复核后执行，不在本轮创建 `run_01`。

## 11. 自由裁量 D1-D7（V65A）

- D1 冻结三候选固定顺序与 8帧最小验证，不以数据可用性重排。
- D2 Stage1 256/64 粗筛阈放宽仅具淘汰权，不为 READY。
- D3 Stage2 1024/256 正式阈与 V65 一致（`0.50/1.0/1%/16/200/216/CE链式`），本轮仅规划。
- D4 32 TEST 密封仅 identity，不读统计。
- D5 单一 hierarchical λ，不引入第二 estimator。
- D6 泄漏 `m=ceil(1.3*1024*CE/5)` 不 cap，`m_total 216` 辅助。
- D7 本变更 `PLAN_CANDIDATE / DECODER_FREE`，不产生 `run_01`。
