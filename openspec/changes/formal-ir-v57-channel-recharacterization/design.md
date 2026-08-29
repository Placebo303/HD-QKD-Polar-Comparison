# OpenSpec Design: formal-ir-v57-channel-recharacterization (Revised)

**Lifecycle**: `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN` — **decoder-free 平滑信道重表征，不调码、不运行 decoder，三源独立估计器门禁全过才允 V58**
**Cycle**: `V57` (channel-recharacterization), predecessor `V56` `ea39a83` `DIAGNOSIS_RESULT_ACCEPTED` + `ESTIMATOR_UNDERSAMPLED` 触发一次性修订
**Branch**: `formal-ir-mainline` HEAD `ea39a83d844ce60c86418b753cf95576416233f4` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024, 单点)
**Feasibility**: `V54` 二阶段 `43/45` 在 `2026-01-21` 域已证方法有效；`V55` 新 session `0/90` 已证跨 session 域不兼容；`V56` 已完成分流；`V57` 前版 `8192 MLE` 在 `1024×1024` 上 `99.4%`零格、`q_mass 59-74%`、`NLL 30bits clamp` 虚高、`H 2.3` 分裂，确诊为 `ESTIMATOR_UNDERSAMPLED` 稀疏过拟合；仅需以同处理点扩大样本至 `131k` 并引入 `Dirichlet/Laplace` 平滑，以独立 `Val` 估计器门禁验证泛化，零 `decode_*` 调用闭环。
**Key judgement**: **`0/90` 非算法证伪，新 session 信道需重估；前版 `8192 裸MLE` 因样本≪状态数导致零概率主导 NLL，未反映信道难度；必须扩大至每源 `≥512+512` frames（131k pairs/split）并以 `α=1.0` 平滑重算 `C_ab→H_smooth→m_ceil`，以 `Val NLL有限/CV一致/熵收敛` 三门验证，仅报告 `MAP/q_mass` 不硬门；前版归档为 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL`。**

## 1. 科学问题与关键判断（修订）

> 在**完全冻结 `V54` 二阶段完整方法**与**相同处理点**（`d=1024 bw=200ps pairing=nearest rule=legacy_v1 channels A1/B5`）下，`V55` 新 session `0/90` 已定位为跨 session 域不兼容。`V57` 前版以 `8192` 样本在 `1024×1024` 上裸 `MLE` 估计 `H 2.3` 却得 `Val NLL 30-37bits`（`clamp 1e-15` 虚高）且 `q_mass 59-74%`，形成 `H_cal 2.3 vs NLL 30` 分裂，`zero 99.35%`，`MAP 19-42%`，判定为 **估计器欠采样稀疏过拟合**，非信道本身 `22-28` 失配可解释。本次修订需回答：**在每源 `131072` 样本 + `α=1.0` 平滑下重估的 `H_smooth(U1|B), H_smooth(U2|B,U1)` 与 `ceil` 后的 `m1/m2` 为何？该平滑信道在独立 `Val` 上是否满足 `NLL有限/CV一致/熵收敛` 估计器门禁？`MAP/q_mass` 仅描述的难度如何？**

- **对照**：`V13 2026-01-21` 的 `V25` 联合计 `H~0.80` 与 `m2 184/190/192` 仅作对照；`V57` 前版 `8192 MLE` 作为 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL` 负对照，证明虚高消除。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256 / F03 5+5 natural` 为名义不变量；`V57` 不改变任一码参，仅重估信道与泄漏。
- **重表征性质**：纯 **decoder-free**，`α=1.0` 仅 `Cal` 内固定不择优，`Val` 独立估计器三门验证，三源分别判定，总体 `PASS` 才放行 `V58`。

## 2. 冻结语义 — V54 方法与 V55/V56 数据零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V55 |
| m2 per source (对照值) | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 (仅作 `Δ` 差值报告，新 `m` 另算 ceil) |
| GF | GF32 poly37 | GF2mField |
| H1 | V31-H1-QC-16×1024 rank16 80b | V31 |
| 泄漏对照 | base 1064/1094/1104 +40 +40 (旧 floor) | m1=16+64b tag (仅对照，新 ceil) |
| 译码 (冻结禁用) | decode_row_layered_fftqspa 90/1.0 | V43/V52 — 重表征期禁用直至 V58 |
| L1-APP | p via H1 BP TRAIN channel_counts.npz (仅作 NLL_V25 对照，不训新 prior) | V25 |
| Intake 处理点 | d1024 bw200 nearest legacy_v1 A1/B5 单点 84d62779 | V55 authoritative |
| V56 frames | fit [7,8,9,10] val [15,16,17,18] (8 frames) | V56D4 预注册 (与 V57 Cal/Val 零重叠) |
| V57 undersampled (负对照) | Cal 19..50 (32) Val 77..108 (32) 8192/split | V57 v1 已归档，不覆盖 |
| V57 Cal/Val (修订) | per-source `available_s[0:512]` / `[512:1024]` 131072/split | V57 revised 预注册 (见 §4) |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder/prior/H1/Lane C/H_inc1/2`；**零 decoder 直至 V58**；原 `V55 90-block` 永久禁用；`V25 184/190/192` 废弃不沿用；`α` 禁止用 `Val` 择优。

## 3. 新 session 信道模型与公式（decoder-free，Cal 平滑估计，Val 验证）

### 3.1 输入与 F03 分解

- 每源 `pairs.parquet` 的 `alice_symbol/bob_symbol` (`0..1023`, `uint16`) 按 `F03 5+5 natural`：
  ```
  U1 = sym >>5   (0..31, 高5位)
  U2 = sym &31   (0..31, 低5位)
  a = 32*U1(a)+U2(a), b = 32*U1(b)+U2(b)   # a,b 0..1023 仍为原 symbol
  ```
  `Cal_s` 上 `N_cal=131072` pairs/源（`512*256`），`Val_s` 同；`frame_id` 切片保证 `Cal∩Val==∅`。

### 3.2 联合计数与平滑条件分布（Cal 估计，修订：弃裸MLE）

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, dtype int32, sum = N_cal=131072 (前版8192作负对照计数)
N_b = Σ_a C_ab   shape 1024,  P(b)=N_b/N_cal
# 裸MLE仅作对照
P_mle(a|b) = C_ab / N_b  if N_b>0 else 1/1024
# 平滑主路径（预注册 Dirichlet α=1.0 Laplace，强度仅 Cal 内固定，不用 Val 择优）
P_smooth(a|b) = (C_ab + α) / (N_b + α*Q)  if N_b>0 else 1/Q
  where Q=1024, α=1.0  frozen, alternative α=0.5 noted but not gated
zero_cells_mle = #{a,b: C_ab==0},  zero_frac_mle = zero_cells/1M  (报告，~87% at 131k vs 99.4% at 8192)
```

- `ε` 仅为 `log` 守卫 (`1e-15`) 保留于 `MLE NLL` 负对照；`P_smooth` 零概率已消除，无需 clamp，`NLL_smooth` 有限。

### 3.3 熵与链式分解（Cal，平滑）

```
H_smooth(A|B) = - Σ_b P(b) Σ_a P_smooth(a|b) log2 P_smooth(a|b)   bits/symbol, 0..10
P_smooth(u1|b) = Σ_{u2=0..31} P_smooth(32*u1+u2 | b)   shape 32×1024
H_smooth(U1|B) = - Σ_b P(b) Σ_{u1} P_smooth(u1|b) log2 P_smooth(u1|b)   bits/symbol, 0..5
H_smooth(U2|B,U1) = H_smooth(A|B) - H_smooth(U1|B)   # 链式闭合校验 |H-H1-H2|<1e-9 else EVIDENCE_INVALID
H_total = H_smooth(A|B), H1=H_smooth(U1|B), H2=H_smooth(U2|B,U1)
# 对照
H_mle(A|B) similarly with P_mle (report, expected higher than smooth? actually MLE underestimates entropy due to sparsity)
```

- 同步报告 `V13` 参考 `H_V13≈0.80` 与前版 `MLE H 2.27-2.64` 的平滑后 `H_smooth` 对比。

### 3.4 泄漏重算（source-adaptive, f_target=1.3, n=1024, tag=64, log2q=5,  **修订2 分层直算 纠正总量上界错误**）

```
# 修订2：实际两层 GF32 各 0≤m_i≤1024 总 0≤2048，删 m_total≤1024 单门
m1 = min(1024, ceil(f_target * n * H1_smooth / 5))  # 层1由H1直算
m2 = min(1024, ceil(f_target * n * H2_smooth / 5))  # 层2由H2直算，不先算总量再按比例
FULL_DISCLOSURE_LAYER_1 = (ceil(f_target*n*H1_smooth/5) > 1024)  # 饱和记 FULL_DISCLOSURE_LAYER
FULL_DISCLOSURE_LAYER_2 = (ceil(f_target*n*H2_smooth/5) > 1024)
m_total = m1 + m2  # 0..2048
leak_total = 5*m_total + 64   bits/block,  f_eff = leak_total / (n*H_smooth_total)  # tag明确计入，重算真实 f_eff（含截断）
Δ_m_total = m_total - m_total_V25_ref   # V25 ref 200/206/208 按 H 0.80 floor算 仅差值报告
Δ_leak = 5*Δ_m_total
```

- 约束：`m1 ∈ [0,1024] && m2 ∈ [0,1024]` **双门**（`m_total ∈ [0,2048]`），`f_eff` 报告但不硬门；`m_total/m1/m2` 仅为 `V58` 预算建议，不在 `V57` 实例化。`FULL_DISCLOSURE_LAYER` 饱和时落盘标记并重算 `f_eff`，不判 `EVIDENCE_INVALID`。
- **显式废弃**：`V25` `m2 184/190/192` 与 `m1=16` 不作为新域预算，报告中标注 `deprecated`。
- **tag语义**：`64b` 仅 `total` 计一次（L2-only tag），层间不重复，`f_eff` 含 tag。

### 3.5 自洽与对照量（Cal，修订）

- `cal_NLL_self_smooth = mean_{Cal}[-log2 P_smooth(a|b)]`  bits/symbol，预期 `≈ H_smooth + small bias` 为健康，取代前版 `2.27 vs 30` 分裂。
- `cal_NLL_self_mle_clamp = mean_{Cal}[-log2 P_mle clamp1e-15]` 仅负对照，保留 `~2.27` 自洽但非主。
- `cal_acc_self_smooth = mean_{Cal}[a == argmax P_smooth(a|b)]` 仅描述，不门禁。
- `V25_NLL_on_Cal = mean_{Cal}[-log2 P_V25(a|b)]`  bits/symbol，预期 `>>H` (20-35) 为失配证据，仅对照。
- **收敛序列**：对 `Cal` 子采样 `32,128,256,512` frames 分别算 `H_smooth/NLL_smooth`，报告曲线证明随样本增加 `NLL` 从负对照 `30` 向 `H` 收敛。

## 4. 校准/验证注册表（预注册，零重叠，可机械校验，修订扩样）

### 4.1 帧定义（每源独立，大样本，显式冻结）

| 集合 | 帧选取算法 (per source) | 帧数 | 块数 | pairs | 说明 |
|---|---|---|---|---|---|
| Cal | `available_s[0:512]` where `available_s = sorted(set(0..F_s-1) - V55_flat_s - {7,8,9,10,15,16,17,18} - {19..50,77..108})` | 512 | 128 (=512/4) | 131072 | 首段可用帧，前版64排除后首512 |
| Val | `available_s[512:1024]` | 512 | 128 | 131072 | 次段可用帧，与Cal零重叠 |

- 三源 `F` 分别 `2130/5125/5513`，`K=F-3` 为 `2127/5122/5510`，`pairs_per_frame 256`，`BLOCK_LENGTH 1024`，`frame_id∈[0,F-1]`。
- **零重叠证明**（修订四重）：
  ```
  assert set(Cal_s) ∩ set(Val_s) == ∅  per s
  assert set(Cal_s∪Val_s) ∩ set(V55_90flat_s) == ∅  per s
  assert set(Cal_s∪Val_s) ∩ {7,8,9,10,15,16,17,18} == ∅ per s
  assert set(Cal_s∪Val_s) ∩ {19..50,77..108} == ∅ per s
  assert |Cal_s|==512 && |Val_s|==512 && all(0 <= fid < F_s for fid in Cal_s∪Val_s)
  ```
  脚本启动即校验，失败则 `V57_EVIDENCE_INVALID`。

- **选取理由**：`512` 连续在 `V55` 密度下不可行；按可用帧排序取前 `1024` 确保确定性、最早覆盖、零重叠可机械证明，且样本 `16×` 扩大使 `zero_frac` `99.4%→~87%`（`131k/1M` 期望），`q_mass MLE` `59-74%→` 平滑后 `NLL` 有限；1M 消耗 `1024/2130≈48%` 帧，1p5M/2M 分别 `20%/18%`，仍留 `1106/4101/4489` 帧供 `V58 TEST`。

### 4.2 注册表产出

- `v57_calibration_registry.json`: `{schema: "v57_cal/val_v2", lifecycle: "V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED", data_sha: "84d62779", processing_rule: "legacy_v1", smoothing: "Dirichlet α=1.0 Laplace (P=(C+1)/(N_b+1024))", per_source: {1M: {F:2130, K:2127, selected_frame_ids: [512 ints Cal], blocks:128, pairs:131072, provenance:{v55_registry_sha, excluded_64, frame_period 204800}}, 1p5M:{...}, 2M:{...}}, overall_zero_overlap_verified: true, negative_control: "v57_channel_recharacterization_undersampled_mle_negative_control.json"}`
- `v57_validation_registry.json`: 同上 `Val`。
- `v57_manifest.json`: `{cal_registry_sha, val_registry_sha, zero_overlap_proofs: {cal∩val, cal∪val∩v55, ∩v56, ∩undersampled}, head, data_sha, smoothing, ceil_formula, command}`
- **负对照归档**：前版 `v57_channel_recharacterization.json/report` 原地更名为 `v57_channel_recharacterization_undersampled_mle_negative_control.json/md`，`schema v57_undersampled_mle_negative_control_v1`。

## 5. Validation 估计器三门（per source 分别，不用总体平均，预注册阈，修订）

### 5.1 门定义（弃旧四门，改为 EG1-3 估计器门禁，q_mass/MAP仅描述）

对每源 `s`，以 `P_cal_smooth (α=1.0)` 在 `Val` 上测：

**EG1 NLL有限且改善**：
```
NLL_val_smooth = mean_{Val}[-log2 P_smooth(a|b)]  bits/symbol
NLL_val_mle_clamp = mean_{Val}[-log2 P_mle clamp1e-15]  # 负对照，预期 30-37
NLL_V25_on_Val = mean_{Val}[-log2 P_V25(a|b)]  # 22-35 退化
PASS_EG1 = (NLL_val_smooth < 15.0) && isfinite(NLL_val_smooth) \
           && (NLL_val_smooth < NLL_val_mle_clamp - 5.0) \
           && (NLL_val_smooth < NLL_V25_on_Val)  # 平滑消除虚高且优于 prior
```

**EG2 CV一致性**：
```
NLL_cal_self_smooth = mean_{Cal}[-log2 P_smooth(a|b)]  # 同Cal上自测
# Cal内2-fold CV：Cal拆前后256 frames各131072/2=65536 pairs
NLL_cal_fold1 = mean_{Cal_fold2}[-log2 P_smooth_fold1(a|b)]  # fold1训fold2测
NLL_cal_fold2 = mean_{Cal_fold1}[-log2 P_smooth_fold2(a|b)]
PASS_EG2 = (|NLL_val_smooth - NLL_cal_self_smooth| <= 0.50) \
           && (|NLL_val_smooth - NLL_cal_self_smooth|/NLL_cal_self_smooth <= 0.25) \
           && (abs(NLL_cal_fold1 - NLL_cal_fold2) <= 0.50)
# 需泛化受控，Val与Cal自测接近，Cal内两折稳定
```

**EG3 熵稳定性与收敛**：
```
H_val_smooth = H_smooth(A|B)_Val  (同 §3.3 公式但用 Val 计数 + 同α平滑)
H_cal_smooth = H_smooth(A|B)_Cal
# 收敛序列：H_32_mle vs H_512_smooth 趋势
PASS_EG3 = (|H_val_smooth - H_cal_smooth| <= 0.20) && (|H_val-H_cal|/H_cal <= 0.25)
# 另报告：H_cal_512_smooth vs H_cal_32_mle 差、NLL_512_smooth vs NLL_32_mle_clamp 下降 >5bits 作为收敛证据描述
```

**Descriptive only（不入 gate）**：
```
q_mass_mle = Σ_{C_ab_cal_mle==0} P_val_emp(a,b)  # 仅描述，预期 131k下仍 ~30-50%但NLL不再虚高
zero_frac_mle = #{C_ab==0}/1M  # ~87% at 131k
acc_smooth = mean_{Val}[a==argmax P_smooth(a|b)]  # 仅描述，不设60%硬阈
acc_mle = mean_{Val}[a==argmax P_mle(a|b)]  # 对照
```

- **per source 判定**：
  ```
  PASS_s = PASS_EG1_s && PASS_EG2_s && PASS_EG3_s && zero_overlap_s && counts_valid_s
  # zero_overlap_s含四重，counts_valid指C_ab计数有效、H链式闭合、帧连续无缺失（允许跳过 forbidden但Cal/Val内帧各256校验）
  ```

- **报告量**（per source）：
  ```
  H_cal_smooth, H1_cal_smooth, H2_cal_smooth, NLL_val_smooth, NLL_cal_self_smooth, NLL_fold1/2,
  NLL_val_mle_clamp(负对照), NLL_V25_on_Val, acc_smooth/descriptive, q_mass/descriptive, zero_frac,
  H_val_smooth, H_convergence_series[32,128,256,512], m_total_ceil, m1_ceil, m2, f_eff, Δ_m, leak_total,
  EG1..EG3 booleans, PASS_s
  ```

## 6. 三源总体判定与 V58 门（修订2：FAIL_NOSTABLE，删m_total单门）

```
# 修订2：删 m_total≤1024 单门，改为 m1≤1024&&m2≤1024 双门，饱和仅 FULL_DISCLOSURE 不判 INVALID
if not zero_overlap_all or not counts_valid_all or not chain_ok_all:  # 仅硬完整性→INVALID
    overall = V57_EVIDENCE_INVALID
elif PASS_1M && PASS_1p5M && PASS_2M:  # EG1-3 均通过
    overall = V57_CHANNEL_RECHARACTERIZATION_PASS
    # 三源均估计器三门通过 → 允许另起 V58 走 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT + EXECUTE_AUTH 的 decoder TEST
else:
    overall = V57_CHANNEL_RECHARACTERIZATION_FAIL  # 含 MIXED_BY_SOURCE + PREDICTIVE_MODEL_NOT_STABLE
    # 当前 Cal self NLL 4.6-5.5 vs Cal-fold/Val NLL 8-10 且 λ三源均上界10 → EG2三源fail 说明预测模型未稳定
    # → 终态 V57_CHANNEL_RECHARACTERIZATION_FAIL / PREDICTIVE_MODEL_NOT_STABLE，不判 EVIDENCE_INVALID，不扩λ网格
    # FULL_DISCLOSURE_LAYER 饱和时已落盘标记并重算 f_eff，仅描述不入 INVALID
```

- **仅 `PASS` 才允 `V58`**：`V58` 将冻结全新 `TEST` blocks（与 `Cal/Val` 及 `V55 90` 及 `undersampled 64` 均零重叠，未揭盲，`30/source` 量级）与新 `m1/m2_ceil`（分层 `min(1024,ceil(f N H_i/5))`），走独立 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED → IMPLEMENTATION_CANDIDATE → EXECUTE_AUTH → run_01` 完整生命周期，双重 review 后方可 `ARCHIVED`；`V57_FAIL/INVALID` 时停留 `PENDING` 修划分或扩样本，不 entered `decoder`。`FAIL` 含 `PREDICTIVE_MODEL_NOT_STABLE` 子态时显式报告不稳定性且不扩 `λ` 网格。
- **V55 90 永久禁用**：`v55_authoritative_registry.json` 的 `90×4` 已揭盲 `0/90`，禁止任何 `corrected pipeline` 在其上重跑；报告显式声明。
- **同 session 剩余帧 freshness**：`V57` 的 `Cal/Val` 同属 `20260123/20260107` 三 session 的已诊断 `pairs.parquet` 衍生，报告显式“已用于诊断与重表征，`131k` 平滑后仍为 within-session 估计，真正 `cross-session qualification` 放 `V58` 新 `TEST`”边界。
- **负对照边界**：前版 `8192 MLE` 的 `H 2.27-2.64 vs NLL 30-37` 分裂已归档为 `ESTIMATOR_UNDERSAMPLED` 证据，新平滑 `H_smooth~? vs NLL_smooth~?` 的收敛在报告 `Negative Control` 章节对比呈现。

## 7. 脚本与报告（decoder-free 守卫，修订）

- **脚本 `v57_channel_recharacterization.py`** (本变更目录下, decoder-free, **修订2 分层m_i+双门+FULL_DISCLOSURE+FAIL_NOSTABLE**):
  ```
  python v57_channel_recharacterization.py \
    [--pairs-root comparison_bench/outputs_comparison/v55_intake_20260828/pairs] \
    [--counts comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz] \
    [--v55-registry openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json] \
    [--alpha 1.0] [--out v57_channel_recharacterization.json] [--report V57_CHANNEL_RECHARACTERIZATION_REPORT.md]
  → 四重零重叠校验 (set∩) → 按 Cal 512 切片算 C_ab/P_smooth/H_smooth → **分层 m_i=min(1024,ceil(f N H_i/5)) + FULL_DISCLOSURE_LAYER 标记 + f_eff重算 + m1≤1024&&m2≤1024 双门** → 按 Val 512 算 NLL_smooth/CV/H_val → 子采样 32/128/256/512 收敛序列 → EG1-3逐源判定（含 EG2三源fail+λ上界10→PREDICTIVE_MODEL_NOT_STABLE） → overall 3选1 (INVALID仅硬完整性, 否则 FAIL_NOSTABLE) → 归档负对照 → 报告
  rg "decode_" 0 hits, 仅 numpy/pandas/pyarrow，py_compile PASS，不扩λ网格
  输出 v57_channel_recharacterization.json (+ FULL_DISCLOSURE_LAYER, PREDICTIVE_MODEL_NOT_STABLE) + V57_CHANNEL_RECHARACTERIZATION_REPORT.md + v57_manifest.json + registries + 负对照归档 + 控制台摘要
  ```

- **报告 `V57_CHANNEL_RECHARACTERIZATION_REPORT.md`**：每源 `H_smooth/H1/H2/NLL_smooth/NLL_mle_clamp负对照/NLL_V25/acc_descriptive/q_mass_descriptive/zero_frac/H_val/m_total_ceil/m1_ceil/m2/f_eff/Δ`、估计器三门明细与 `per_source PASS_s`、`overall` 终态与 `V58` 放行声明、`Negative Control` 章节对比 `8192 MLE` vs `131k smooth`、`收敛序列` 表，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V55 90 已揭盲不可复用` + `V25 184/190/192 已废弃不沿用` + `仅全过才 V58` + `同 session 剩余帧仅 within-session` 边界。

- **守卫**：重表征期 **零 decoder**、原 `90` 已揭盲保护、**不创建 `run_01` decoder 执行**、**不做阈值/方向/frame-start 网格**（`rg "grid" 0 hits`）、**不改码参**（`git diff -- comparison_bench/src/comparison_bench/formal_ir/ 0` 且 `git diff -- src/ ==0`）。

## 8. 与 V56/V58 衔接

- `V56` `DIAGNOSIS_RESULT_ACCEPTED` 已固化校准验证与 `5` 选 `1` 的分流，`V54 43/45` 方法有效性保持；`V57` 前版 `UNDERSAMPLED` 已归档；`V57` 修订以 **大样本平滑重估信道与 `ceil m`** 补齐估计器证据，以 **估计器三门** 验证泛化，未否定 `V56` 终态。
- `V58` 为 `decoder TEST`：需新 `TEST` registry（`30/source`，与 `Cal 512/Val 512` 及 `V55 90` 及 `undersampled 64` 均零重叠，未揭盲），冻结新 `m_total/m1_ceil` 按 `V57` 新 `H_smooth` `ceil` 实例化，新 `H_inc` 矩阵构造需另起 `OpenSpec` 详述，独立 `EXECUTE_AUTH` 绑定 `HEAD/data SHA/implementation SHA` 三方。

## 9. 自由裁量 D1-D7（修订）

- D1 `C_ab` 仅 `numpy` 直算 `bincount2d`，平滑为 `(C+α)/(N_b+αQ)` 确定性算术，不引 `scipy`
- D2 `Cal/Val` 每源 `512/512` 按可用帧排序确定性切分，不搜索多划分（仅预注册一种，`131072` 已为 `1M cell` 的最小平滑可报告门限，`8192` 版保留作负对照）
- D3 `F03 5+5` 分解固定 `natural`，不搜 `Gray`，平滑 `α=1.0` 固定不择优
- D4 `m` 公式固定 **分层** `m_i=min(1024,ceil(f_target n H_i/5))` + `m_total=m1+m2 0..2048` + `FULL_DISCLOSURE_LAYER` 饱和标记 + `m1≤1024&&m2≤1024` 双门（删总量单门），`f` 不调
- D5 三门阈固定 `EG1 NLL<15&<MLE-5&<V25 / EG2 CV≤0.5 / EG3熵≤0.20&25%`，q_mass/acc 仅描述，不以总体平均替代三源分别
- D6 不产生新矩阵/码参数，仅估计与判定，最简闭环
- D7 本变更为 `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN`，不产生 `TEST run_01`，`V58` 时才 decoder
