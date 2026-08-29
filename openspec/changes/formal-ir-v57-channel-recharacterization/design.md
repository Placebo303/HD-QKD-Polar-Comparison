# OpenSpec Design: formal-ir-v57-channel-recharacterization

**Lifecycle**: `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN` — **decoder-free 信道重表征，不调码、不运行 decoder，三源独立 validation 全过才允 V58**
**Cycle**: `V57` (channel-recharacterization), predecessor `V56` `49a415b` `DIAGNOSIS_RESULT_ACCEPTED`
**Branch**: `formal-ir-mainline` HEAD `49a415b8253c9c73da0013588d0c50c0e9d41dba` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024, 单点)
**Feasibility**: `V54` 二阶段 `43/45` 在 `2026-01-21` 域已证方法有效，泄漏 `1064/1094/1104` 等价可行；`V55` 同方法新 session `0/90` 且 `U1/U2 76%→27-41%`、`NLL 0.82→22-28` 已证跨 session 域不兼容；`V56` 已以 `1024→32` 低维分解与 `fit/val CE/acc` 主证据完成分流，`V13` 合同回放已闭合，未否定码族；现仅需以新 session 实测在 **同处理点** 下重估 `C_ab/P/H/m` 并以 **独立 `Val` 四门** 验证泛化，零 `decode_*` 调用即可闭环，无需阈/方向网格或新矩阵。
**Key judgement**: **`0/90` 非算法证伪，新 session 信道已迁移，`V25` 的 `184/190/192` 与 `channel_counts.npz` 均不可复用；必须以新 session 独立 `Cal` 重算 `C_ab→H(U1|B)/H(U2|B,U1)→m1/m2/f`，并以独立 `Val` 在 `NLL/MAP/零覆盖/熵稳定性` 四门上三源分别验证，仅全过才允许 `V58` decoder TEST。**

## 1. 科学问题与关键判断

> 在**完全冻结 `V54` 二阶段完整方法**（`H1-16 + L1-APP via H1 BP + Lane C m2 184/190/192(对照) + H_inc1/2 Δ8+8(对照) + decoder 90/1.0 poly37 + L2-only tag`）与**相同处理点**（`d=1024 bw=200ps pairing=nearest rule=legacy_v1 channels A1/B5`）下，`V55` 新 session `0/90` 已定位为跨 session 域不兼容，`V25 TRAIN` 的 `H(A|B)~0.80` 与 `m2 184/190/192` 在新域上 `NLL 22-28` 严重失配。`V57` 需回答：**在新 session 独立 `Cal` 上重估的 `H(U1|B), H(U2|B,U1)` 与所需 `m1/m2/Δ` 为何？该新信道在独立 `Val` 上是否满足 `NLL/MAP/零覆盖/熵稳定性` 四门泛化？**

- **对照**：`V13 2026-01-21` 的 `V25` 联合计 `H~0.80` 与 `m2 184/190/192` 仅作对照，不作新域预算；`V57` 新估计基于同三 intake session（`20260123_1M_600k_0dB F2130 / 20260107_PPLN_1p5M F5125 / 20260123_2M_1p2M_0dB F5513`）的独立 `Cal` 切片。
- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256 / F03 5+5 natural` 为名义不变量；`V57` 不改变任一码参，仅重估信道与泄漏。
- **重表征性质**：纯 **decoder-free**（零 `decode_*` 调用），仅读 `pairs.parquet` 的 `alice_symbol/bob_symbol` 与 `V25 counts` 作 `NLL_V25` 对照，四门预注册阈不择优，三源分别判定，总体 `PASS` 才放行 `V58`。

## 2. 冻结语义 — V54 方法与 V55/V56 数据零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V55 |
| m2 per source (对照值) | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 (仅作 `Δ` 差值报告，新 `m` 另算) |
| GF | GF32 poly37 | GF2mField |
| H1 | V31-H1-QC-16×1024 rank16 80b | V31 |
| 泄漏对照 | base 1064/1094/1104 +40 +40 (旧) | m1=16+64b tag (仅对照) |
| 译码 (冻结禁用) | decode_row_layered_fftqspa 90/1.0 | V43/V52 — 重表征期禁用直至 V58 |
| L1-APP | p via H1 BP TRAIN channel_counts.npz (仅作 NLL_V25 对照，不训新 prior) | V25 |
| Intake 处理点 | d1024 bw200 nearest legacy_v1 A1/B5 单点 84d62779 | V55 authoritative |
| V56 frames | fit [7,8,9,10] val [15,16,17,18] (8 frames) | V56D4 预注册 (与 V57 Cal/Val 零重叠) |
| V57 Cal/Val | Cal 19..50 (32) Val 77..108 (32) per source (三源统一) | V57 预注册 (见 §3) |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder/prior/H1/Lane C/H_inc1/2`；**零 decoder 直至 V58**；原 `V55 90-block` 永久禁用；`V25 184/190/192` 废弃不沿用。

## 3. 新 session 信道模型与公式（decoder-free，Cal 估计，Val 验证）

### 3.1 输入与 F03 分解

- 每源 `pairs.parquet` 的 `alice_symbol/bob_symbol` (`0..1023`, `uint16`) 按 `F03 5+5 natural`：
  ```
  U1 = sym >>5   (0..31, 高5位)
  U2 = sym &31   (0..31, 低5位)
  a = 32*U1(a)+U2(a), b = 32*U1(b)+U2(b)   # a,b 0..1023 仍为原 symbol，不另做 bin 合并
  ```
  `Cal_s` 上 `N_cal=8192` pairs/源，`Val_s` 同；`frame_id` 切片保证 `Cal∩Val==∅`。

### 3.2 联合计数与条件分布（Cal 估计）

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, dtype int32, sum = N_cal
N_b = Σ_a C_ab   shape 1024,  P(b)=N_b/N_cal
P_hat(a|b) = C_ab / N_b  if N_b>0 else 1/1024   (列归一，零 N_b 时 uniform；log 时 clamp 1e-15)
zero_cells_cal = #{a,b: C_ab==0},  zero_frac = zero_cells/1M
```

- `ε` 仅为 `log` 守卫 (`1e-15`)，计数保持原始零格以报告 `q_mass`；不做 `α` 平滑改变 `H`，`H` 按上式零项 `0 log0=0` 直算。

### 3.3 熵与链式分解（Cal）

```
H(A|B) = - Σ_b P(b) Σ_a P_hat(a|b) log2 P_hat(a|b)   bits/symbol, 0..10
P_hat(u1|b) = Σ_{u2=0..31} P_hat(32*u1+u2 | b)   shape 32×1024 → 32×
H(U1|B) = - Σ_b P(b) Σ_{u1} P_hat(u1|b) log2 P_hat(u1|b)   bits/symbol, 0..5
H(U2|B,U1) = H(A|B) - H(U1|B)   # 链式闭合校验 |H-H1-H2|<1e-9， violation 则 EVIDENCE_INVALID
H_total = H(A|B), H1=H(U1|B), H2=H(U2|B,U1)
```

- 同步报告 `V13` 参考 `H_V13≈0.80` 与 `V25` 同 `Cal` 上的 `NLL_self` 仅作对照，不作阈。

### 3.4 泄漏重算（source-adaptive, f_target=1.3, n=1024, tag=64, log2q=5）

```
m_total = floor((f_target * n * H_total - tag) / 5)   # 整数码长，需 ≥0 且 <n
m1 = round(m_total * H1 / H_total)   # Python round, half even, frozen rule 同 V27R
m2 = m_total - m1
leak_total = 5*m_total + 64   bits/block,  f_eff = leak_total / (n*H_total)
Δ_m_total = m_total - m_total_V25_ref   # V25 ref 200/206/208 (按 H 0.80 算) 仅差值报告
Δ_leak = 5*Δ_m_total
```

- 约束：`m_total ∈ [0,1023]`, `m1∈[0,m_total]`, `f_eff<1.6` 报告但不硬门；`m_total/m1/m2` 仅为 `V58` 预算建议，不在 `V57` 实例化。
- **显式废弃**：`V25` `m2 184/190/192` 与 `m1=16` 不作为新域预算，报告中标注 `deprecated`。

### 3.5 自洽与对照量（Cal）

- `cal_NLL_self = mean_{Cal}[-log2 P_hat(a|b)]` (clamp 1e-15)  bits/symbol，仅自洽参考，`≈ H_total` 为健康。
- `cal_acc_self = mean_{Cal}[a == argmax P_hat(a|b)]` 报告。
- `V25_NLL_on_Cal = mean_{Cal}[-log2 P_V25(a|b)]` (`P_V25` 来自 `channel_counts.npz` 列归一)  bits/symbol，预期 `>>H` (20+) 为失配证据，仅对照。

## 4. 校准/验证注册表（预注册，零重叠，可机械校验）

### 4.1 帧定义（统一三源，显式冻结）

| 集合 | 帧范围 (per source) | 帧数 | 块数 | pairs | 说明 |
|---|---|---|---|---|---|
| Cal | 19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50 | 32 | 8 (=19-22/23-26/27-30/31-34/35-38/39-42/43-46/47-50) | 8192 | 首大空隙前段，`19..50` |
| Val | 77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108 | 32 | 8 (=77-80/81-84/85-88/89-92/93-96/97-100/101-104/105-108) | 8192 | 次空隙前段，`77..108` |

- 三源 `F` 分别 `2130/5125/5513`，`K=F-3` 为 `2127/5122/5510`，`pairs_per_frame 256`，`BLOCK_LENGTH 1024`，`frame_id∈[0,F-1]`。
- **零重叠证明**：
  ```
  assert set(Cal) ∩ set(Val) == ∅
  assert set(Cal∪Val) ∩ set(V55_90flat) == ∅  # V55 flat = 120 frames/source 见 v55_authoritative_registry.json selected_frame_ids 展开
  assert set(Cal∪Val) ∩ {7,8,9,10,15,16,17,18} == ∅
  assert all(0 <= fid < F_s for fid in Cal∪Val)
  ```
  脚本启动即校验，失败则 `V57_EVIDENCE_INVALID` 零 pairs 估计。

- **选取理由**：`19..50` 与 `77..108` 均位于 `V55` 稀疏采样 `floor(j*(K-1)/29)` 的空隙中（`1M` 空隙 `19..72` 长 `54`、`77..145` 长 `69`；`1p5M/2M` 空隙更大），与 `V55` 第二块 `73..76`/`176..179`/`189..192` 均无交集，且 `19` 避开 `V56` `15..18`；统一帧号简化三源对照，且均 `< min(F)=2130`。

### 4.2 注册表产出

- `v57_calibration_registry.json`: `{schema: "v57_cal/val_v1", lifecycle: "V57_CHANNEL_RECHARACTERIZATION_PENDING", data_sha: "84d62779", processing_rule: "legacy_v1", per_source: {1M: {F:2130, K:2127, selected_frame_ids: [19..50], blocks:8, pairs:8192, provenance:{provenance_note, v55_registry_sha, frame_period 204800}}, 1p5M:{F:5125,...}, 2M:{F:5513,...}}, overall_zero_overlap_verified: true}`
- `v57_validation_registry.json`: 同上 `Val 77..108`。
- `v57_manifest.json`: `{cal_registry_sha, val_registry_sha, zero_overlap_proofs: {cal∩val, cal∪val∩v55, ∩v56}, head: "49a415b", data_sha: "84d62779", created_at, command}`

## 5. Validation 四门（per source 分别，不用总体平均，预注册阈）

对每源 `s`，以 `P_cal` (Cal 列归一) 在 `Val` 上测：

**V1 NLL 一致性**：
```
NLL_val = mean_{pairs in Val}[ -log2 P_cal(a|b) clamp 1e-15 ]  bits/symbol
NLL_val_block = NLL_val * 1024
NLL_V25_on_Val = mean_{Val}[ -log2 P_V25(a|b) ]  bits/symbol  (V25 prior 对照)
PASS_V1 = (NLL_val <= H_cal + 0.50) && (NLL_val <= 1.50) && (NLL_val < NLL_V25_on_Val - 5.0)
# 需比 V25 在同 Val 上的退化 NLL (20-28) 低至少 5 bits，且接近 Cal 熵
```

**V2 MAP 准确率**：
```
acc_val = mean_{Val}[ a == argmax_{a'} P_cal(a'|b) ]   (1024 态全局 MAP, b 固定)
acc_cal = mean_{Cal}[ a == argmax P_cal(a|b) ]  (自测参考)
PASS_V2 = (acc_val >= 0.60) && (acc_val >= acc_cal - 0.10)
# 1024 态随机基线 1/1024≈0.1%，60% 为强信号；与 V56 60% 同阈
```

**V3 零计数覆盖**：
```
q_mass = Σ_{a,b: C_ab_cal==0} P_val_emp(a,b)   # Val 经验质量落入 Cal 未见格
P_val_emp(a,b)= C_ab_val / N_val
zero_frac_cal = #{C_ab_cal==0}/1M
PASS_V3 = (q_mass <= 0.20)   # ≤20%
# zero_frac 仅报告 (8192 样本下 ~99% 零格为预期)，不硬阈
```

**V4 熵稳定性**：
```
H_val = H(A|B)_Val  (同 §3.3 公式但用 Val 计数重算)
PASS_V4 = (|H_val - H_cal| <= 0.20) && (|H_val-H_cal|/H_cal <= 0.25)
```

- **per source 判定**：
  ```
  PASS_s = PASS_V1_s && PASS_V2_s && PASS_V3_s && PASS_V4_s && zero_overlap_s && counts_valid_s
  ```
  `counts_valid_s` 指 `C_ab` 计数有效、`H` 链式闭合、帧连续无缺失。

- **报告量**（per source）：
  ```
  H_cal, H1_cal, H2_cal, NLL_val, NLL_V25_on_Val, acc_val, acc_cal, q_mass, zero_frac, H_val,
  m_total, m1, m2, f_eff, Δ_m, leak_total, V1..V4 booleans, PASS_s
  ```

## 6. 三源总体判定与 V58 门

```
if not zero_overlap_all or not counts_valid_all:
    overall = V57_EVIDENCE_INVALID
elif PASS_1M && PASS_1p5M && PASS_2M:
    overall = V57_CHANNEL_RECHARACTERIZATION_PASS
    # 三源均四门通过 → 允许另起 V58 走 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT + EXECUTE_AUTH 的 decoder TEST
else:
    overall = V57_CHANNEL_RECHARACTERIZATION_FAIL
    # 含 MIXED_BY_SOURCE 子态：逐源 PASS_s 清单分源报告，需修 Cal/Val 划分或扩样本 (e.g., 32→64 帧) 后重审，不进入 decoder
```

- **仅 `PASS` 才允 `V58`**：`V58` 将冻结全新 `TEST` blocks（与 `Cal/Val` 及 `V55 90` 零重叠，未揭盲，`30/source` 量级）与新 `m1/m2`，走独立 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED → IMPLEMENTATION_CANDIDATE → EXECUTE_AUTH → run_01` 完整生命周期，双重 review 后方可 `ARCHIVED`；`V57_FAIL/INVALID` 时停留 `PENDING` 修划分或扩样本，不 entered `decoder`。
- **V55 90 永久禁用**：`v55_authoritative_registry.json` 的 `90×4` 已揭盲 `0/90`，禁止任何 `corrected pipeline` 在其上重跑；报告显式声明。
- **同 session 剩余帧 freshness**：`V57` 的 `Cal/Val` 同属 `20260123/20260107` 三 session 的已诊断 `pairs.parquet` 衍生，报告显式“已用于诊断与重表征，不宣称完全独立 cross-session 资格”，真正 `cross-session qualification` 放 `V58` 新采集或与 `Cal/Val` 零重叠的 `TEST`（`TEST` 与 `Cal/Val` 零重叠但仍同 acquisition，边界为 `fresh within-session confirmation`，`V58` 报告需显式边界）。

## 7. 脚本与报告（decoder-free 守卫）

- **脚本 `v57_channel_recharacterization.py`** (本变更目录下, decoder-free):
  ```
  python v57_channel_recharacterization.py \
    [--pairs-root comparison_bench/outputs_comparison/v55_intake_20260828/pairs] \
    [--counts comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz] \
    [--v55-registry openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json] \
    [--out v57_channel_recharacterization.json] [--report V57_CHANNEL_RECHARACTERIZATION_REPORT.md]
  → 零重叠校验 (set∩) → 按 Cal 19..50 切片算 C_ab/P/H/H1/H2/m1/m2/f → 按 Val 77..108 算 NLL/acc/q_mass/H_val → V1..V4逐源判定 → overall 5选？3选1 → 报告
  rg "decode_" 0 hits, 仅 numpy/pandas/pyarrow，py_compile PASS
  输出 v57_channel_recharacterization.json + V57_CHANNEL_RECHARACTERIZATION_REPORT.md + v57_manifest.json + 控制台摘要
  ```

- **报告 `V57_CHANNEL_RECHARACTERIZATION_REPORT.md`**：每源 `H/H1/H2/NLL_val/NLL_V25/acc/q_mass/zero_frac/H_val/m_total/m1/m2/f_eff/Δ`、四门明细与 `per_source PASS_s`、`overall` 终态与 `V58` 放行声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V55 90 已揭盲不可复用` + `V25 184/190/192 已废弃不沿用` + `仅全过才 V58` + `同 session 剩余帧仅 within-session` 边界。

- **守卫**：重表征期 **零 decoder**、原 `90` 已揭盲保护、**不创建 `run_01` decoder 执行**、**不做阈值/方向/frame-start 网格**（`rg "grid" 0 hits`）、**不改码参**（`git diff -- comparison_bench/src/comparison_bench/formal_ir/ 0` 且 `git diff -- src/ ==0`）。

## 8. 与 V56/V58 衔接

- `V56` `DIAGNOSIS_RESULT_ACCEPTED` 已固化校准验证与 `5` 选 `1`（`RECOVERED/TRUE_DOMAIN_SHIFT/MIXED/UNRESOLVED/EVIDENCE_INVALID`）的分流，`V54 43/45` 方法有效性保持；`V57` 在其上以 **独立 `Cal` 重估信道与 `m`** 补齐分布证据，以 **独立 `Val` 四门** 验证泛化，未否定 `V56` 终态。
- `V58` 为 `decoder TEST`：需新 `TEST` registry（`30/source`，与 `Cal 19..50 / Val 77..108 / V55 90` 均零重叠，未揭盲，例如 `1M 111..230` 等），冻结新 `H1/Lane C`? 不，仍 `H1-16` 不变，仅 `m_total/m1` 按 `V57` 新 `H` 实例化，新 `H_inc` 矩阵构造需另起 `OpenSpec` 详述，独立 `EXECUTE_AUTH` 绑定 `HEAD/data SHA/implementation SHA` 三方。

## 9. 自由裁量 D1-D7

- D1 `C_ab` 仅 `numpy` 直算 `bincount2d`，不引 `scipy`
- D2 `Cal/Val` 固定 `32/32` 帧统一三源，不搜索多划分（仅预注册一种，`32×256=8192` 已为最小可报告门限）
- D3 `F03 5+5` 分解固定 `natural`，不搜 `Gray`
- D4 `m` 公式固定 `f_target1.3 n1024 tag64 log2q5 + Python round`，不调 `f`
- D5 四门阈固定 `NLL H+0.5/1.5/MAP60%/q20%/熵0.2/25%`，不以总体平均替代三源分别
- D6 不产生新矩阵/码参数，仅估计与判定，最简闭环
- D7 本变更为 `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`，不产生 `TEST run_01`，`V58` 时才 decoder
