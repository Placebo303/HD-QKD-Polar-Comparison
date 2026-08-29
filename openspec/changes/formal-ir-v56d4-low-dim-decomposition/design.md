# OpenSpec Design: formal-ir-v56d4-low-dim-decomposition

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 低维分解**
**Cycle**: `V56D4` (low-dim decomposition), predecessor `V56D3R1` `b332b8a4` `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT`
**Branch**: `formal-ir-mainline` HEAD `b332b8a4a51e94fb905023862b8aed3650bac126` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024)
**Feasibility**: `V56D3` 已证 `timing` 部分健康（`σ127ps p2bg 708/629/378`）但 `1024` 态 `val 1024` plug-in `I≈8.4` 严重正偏且 `MAP val < identity` 无泛化，已排除 `5` 族 + 固定 `1024` 置换，`V25 prior` 严重失配；`32` 态在 `1024` 样本下 `32×32=1024` 格（均 `1/格`）偏置远小于 `1024×1024=1M` 格（均 `0.001/格`），可用固定 `train/val CE/acc` 与 `V13` 合同两路回放闭环，无需 `1024` plug-in `MI` 分流或网格择优

## 1. 科学问题与关键判断

> V56D3 曾判 `PAIRING_OR_FRAME_ANCHOR_ERROR`，但 `val4=1024` 样本在 `1024×1024` 上 `plug-in H(A|B)` 被严重压低→`I≈8.4` 为伪高，且 `MAP val < identity (Δ≈-0.14)` 说明高 `I` 无泛化。已排除全局 `shift/XOR/轴交换/Gray/U1U2` 与任意 `1024` 单符号置换（`argmax` 上界亦失败），`V25 prior` `q_mass 57-72%` 严重失配，但 `pairing/frame anchor` 与真域迁移尚未区分。V56D4 必须用 **低维（32态）+ 固定 train/val 泛化指标 + 逐阶段 V13 对照** 才能分离。

- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256` 为名义不变量；`V13` 的 `pairing policy/direction/threshold/frame-start/wrap_rule/mapping` 为已知健康合同
- **去偏原理**：`32` 态 `I` 的 plug-in 偏差 `≈ (K-1)(L-1)/(2N ln2)` 量级，`K=L=32 → 961/(2*1024)≈0.47 bits` 远小于 `1024` 态的 `~1M/(2*1024)≈500 bits` 量级（实际受稀疏截断影响，但相对数量级差异稳健）；`1024` 样本下 `32` 态更可靠，可作健康对照
- **交叉验证**：`I(U1A;U1B)` 与 `I(U2A;U2B)` 分别检验 `F03 5+5` 两子层是否均坍塌；若 `U1` 健康而 `U2` 坍塌则 `Lane C` 子层差异，若两者皆低则全域退化；交叉 `I(U1A;U2B)` 高则提示轴串扰残留（但 `V56D3` 已排除固定轴交换，故交叉仅佐证，不作主判）
- **泛化分流**：`1024` plug-in `I` 不可信，改用 **固定 `fit→val` 交叉熵 `CE` 与准确率 `acc`**（`fit` 上学 `P(A|B)`，`val` 上测，禁同帧），`32` 态下每 `B` 约 `32` 样本，`CE` 估计方差远小于 `1024` 态每 `B` 约 `1` 样本
- **两路合同回放**：不做网格择优，仅 **`V13-contract` vs `current-contract` 两点**；若 `V13` 合同在 `val` 上恢复低维关联与 `NLL` → `pairing/frame` 错，若两者一致仍低 → 真域迁移

## 2. 冻结语义 — V54 方法零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V55 |
| m2 per source | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 |
| GF | GF32 poly37 | GF2mField |
| H1 | V31-H1-QC-16×1024 rank16 80b | V31 |
| 泄漏 | base 1064/1094/1104 +40 +40 | m1=16+64b tag |
| 译码 (冻结禁用) | decode_row_layered_fftqspa 90/1.0 | V43/V52 — 诊断期禁用 |
| L1-APP | p via H1 BP TRAIN channel_counts.npz | V25 |
| Intake | d1024 bw200 nearest legacy_v1 A1/B5 单点 84d62779 | V55 |
| V13 合同 | 从 `workspace/v13r3fresh_20260816/sidecars` 实时读 `pairing/frame` 诸字段 | V13 |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder`；**零 decoder**；原 V55 90-block 已揭盲禁止重跑；`prior` 仍 `TRAIN-only`，不读新 TEST 做训练；**不以 `1024` plug-in `MI` 分流**；不网格择优。

## 3. 32 态低维互信息分解（Phase A）— 去偏核心

- 输入：`comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*.parquet`（三源 `alice_symbol/bob_symbol`） + `workspace/v13r3fresh_20260816/.../pairs.parquet`（V13 参考） + `nbldpc_v25_20260818/run_04/channel_counts.npz`（仅对比，不训）
- 分解：`sym → U1 = sym >> 5 (0..31), U2 = sym & 31 (0..31)`（`F03 5+5` ，`U1` 高 5bit `U2` 低 5bit，与 `Lane C` 对应；若 `Gray` 序则已排除，但分解仍按 `binary` 序算，`V13` 同口径对比保证一致）
- 方法（decoder-free, `numpy` 直算，`32×32`）：
  ```
  C_U1(a,b) = #{U1A=a, U1B=b} (32×32), P= C/N, H(U1A)=-sum P log2 P, H(U1A,U1B)=-sum P log2 P, I(U1A;U1B)=H(U1A)+H(U1B)-H(U1A,U1B)
  同理 C_U2, C_cross1= C(U1A,U2B), C_cross2= C(U2A,U1B)
  熵上限 5 bits (log2 32)，与 V13 同口径对比
  ```
  `32` 态 `I` 仍对 `U1` 维内全局重标记不敏感，但维度降 `32` 倍，偏置显著减小。
- 产出：每源 `I_U1/I_U2/I_cross1/I_cross2`（`bits/symbol`，双报 `×1024` 仅参考）与 `V13` 同口径 `I_U1/I_U2` 对比；若新 session `I_U1/U2` 均 `<1 bit` 而 `V13` `~3-4 bits` 健康，则低维亦坍塌，支持域迁移；若 `I_U1/U2` 中至少一维仍 `>2 bits` 健康则支持 `pairing/frame` 局部错。

## 4. 固定 train/val 交叉熵/准确率（Phase B）— 泛化分流，不用 plug-in MI

- 定义（`32` 态）：
  ```
  C_fit_U1(a,b) = fit 4 frames 上的 U1 联合计数 (32×32)
  P_fit_U1(a|b) = C_fit(a,b) / sum_a C_fit(a,b)  (列归一，b 无观测时 P= uniform 或 delta_b，预注册一种)
  CE_U1_val = E_{val}[-log2 P_fit_U1(A|B)]  (bits/sym, val 上 1024 样本均值)
  acc_U1_val = mean_{val}(U1A == argmax_a P_fit_U1(a|U1B))
  同理 CE_U2/acc_U2
  ```
- 划分：`calibration 8 frames [7,8,9,10,15,16,17,18]` 预注册固定 `fit=[7,8,9,10] val=[15,16,17,18]`（与 `V56D3` 一致），`assert fit∩val==∅`，**fit 上学 `P_fit`，val 上测 `CE/acc`**；另报 `fit+val` 全量仅作稳定性参考，**不以同帧 CE 判恢复**。
- 意义：`CE` 与 `acc` 是泛化指标，不受 `val` 上 plug-in `Hc` 压低影响；`32` 态下每 `B` 约 `1024/32=32` 样本，估计方差 `∝1/32` 远小于 `1024` 态的 `∝1/1`；若 `CE_U1/U2` 从 `~3-4 bits`（高）向 `V13` 的 `~1-2 bits` 回落且 `acc>60%` 则恢复，若仍 `>3 bits` 且 `acc<50%` 则未恢复。
- 守卫：**显式禁止以 `1024` plug-in `I>5` 做分流**；本诊断分流仅用 `32` 态 `I + CE/acc + NLL/q_mass` 联合，不单独以 `I` 阈。

## 5. 逐阶段流水核对（Phase C）— V13 vs 新 session 首次坍缩定位

- 流水（decoder-free, 读 `pairs` 与 `ttbin`）：
  ```
  1. raw coincidence (ttbin events, cross-correlation peak_center/σ/p2bg/total_events/duration)
  2. pairing (policy nearest, direction, threshold_ps, Δt = t_B - t_A 配对后分布, 跨帧错配率)
  3. per-frame occupancy (pairs per frame, 256 期望, mean/median/zero_frame_fraction)
  4. frame anchor (frame_start = peak_center vs global min, wrap floor_div, period 204800, before/after pair index, anchor 切换前后 U1/U2 一致率)
  5. U1/U2 (symbol → U1/U2 via F03 5+5, U1 一致率/U2 一致率/交叉一致率)
  ```
- 每阶段算 `V13` 参考 vs 新三源的 `I_32(U1/U2)/CE/acc/occupancy/Δt`，报告 `per_stage {stage, V13_val, new_val, delta}` 与 `first_drop_stage`（`V13` 健康而新 session 在该阶段后 `I_32/CE/acc` 首次从健康跌至低值的阶段）。
- 定位：若 Stage 1 `raw` 已低（`p2bg` 差异或 `peak` 弥散）→ `raw` 域迁移；Stage 2 `pairing` 后 `Δt` 分布宽或 `I_32` 跌 → `pairing` 错；Stage 3 `occupancy` 异常（`zero_frame` 高或 `256` 远偏）→ `occupancy/filter` 错；Stage 4 `anchor` 切换前后 `pair index` 与 `U1/U2` 一致率骤变 → `frame anchor` 错；Stage 5 后低但前高且 `V13` 合同可回升 → `pairing/frame` 可修复。

## 6. V13 已知合同两路回放（Phase D）— 仅 V13-contract vs current-contract，不网格择优

| 合同 | 来源 | 字段 |
|---|---|---|
| `V13-contract` | `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` + `build_manifest.json` 实时读 | `pairing_policy/ pairing_direction/ pairing_threshold_ps/ gate_width_ps/ frame_start_ps/ frame_period_ps/ delay_used_ps/ peak_center_ps/ wrap_rule/ mapping/ occupancy_filter` |
| `current-contract` | `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/*/sidecar_meta.json` + `intake_report.json` | `200ps legacy_v1 nearest 1024` 单点（已落盘） |

- 方法：若已有两路 `pairs.parquet`（`V13` 侧 `workspace/.../pairs.parquet` 与 intake 侧 `v55_intake_.../pairs/*.parquet`）则直接读；否则在新 `ttbin` 上用 `src/qkd_io/ttbin_pipeline` 的 `V13` 已验证 `read_ttbin_events + compute_cross_correlation_histogram + pairing + bin + frame_anchor` 实现精确复跑 `V13` 合同（不重发明近似物化），生成 `V13-contract` 的 `pairs` 与 `current-contract` 对比。**仅两路，不做 `threshold/policy/direction/frame-start` 网格**（`rg "grid" 0 hits` 可验）。
- 报告：每路在 `val [15,16,17,18]` 上的 `I_U1/I_U2/I_cross/CE_U1/CE_U2/acc_U1/acc_U2/NLL_32/q_mass_32`（`NLL_32` via `channel_counts.npz` 的 `32×32` 列归一 `P(U1A|U1B)` 与 `P(U2A|U2B)` 近似，仅对比用，不重训 prior），以及 `pipeline_stage` 的 `first_drop` 是否因合同切换消失。
- 择优禁止：**不以 `val` 上 `acc`/`NLL` 最大者择优**，仅陈述两路差值；分流阈为预注册（`I_32` 回升至 `V13` 的 `>70%` 且 `CE` 回落且 `q_mass` 回落）。

## 7. 二选一分流（Phase E）— 互斥终态

```
if V13-contract 在 val 上 I_32 恢复至 V13>70% 且 CE 2-4→1-2 bits 且 acc>60% 且 NLL/q_mass 回落（且 first_drop 因合同切换消失）:
    overall = PAIRING_OR_FRAME_ANCHOR_ERROR
    # 需修复 pairing threshold/policy/direction 与 frame_start/sync/occupancy，另冻新 TEST 再 qualification（原 90 永不重跑）
elif V13-contract 与 current-contract 在 val 上一致仍低（两者 I_32 均低<1.5 bits，CE 均>3 bits，acc 均<50%，差值<10% 或 I_32 差<0.5 bits）且 pipeline 各阶段均低（first_drop 在 raw 或无单点坍缩）:
    overall = TRUE_ACQUISITION_DOMAIN_SHIFT
    # 非合同错，真域迁移，届时才规划新 TRAIN-only prior/leakage（m_total = floor((1.3*1024*H-64)/5)，source-adaptive，TRAIN-only，不读新 TEST 做训练）
else:
    overall = INCONCLUSIVE_NEED_DEEPER_EVIDENCE  # 证据不足或 MIXED_BY_SOURCE（分源不一致时逐源 INCONCLUSIVE）
```

- 三态互斥，逐源可 `MIXED_BY_SOURCE`（例 `1M pairing错 2M domain shift`），总体取 `MIXED` 或 `INCONCLUSIVE`，不扩大为算法否定；`TRUE_DOMAIN_SHIFT` 时才规划新 `prior/泄漏`，`PAIRING` 时仅修契约。
- 分流依据 **必须** 联合 `32` 态 `I + CE/acc + NLL/q_mass + pipeline first_drop + 合同两路差值`，**禁止单用 `1024` plug-in `MI`**。

## 8. 脚本与报告（decoder-free 守卫）

- 脚本 `v56d4_low_dim_decomposition.py` (本变更目录下, decoder-free): `python v56d4_low_dim_decomposition.py [--pairs-root ...] [--v13-root ...] [--counts ...] [--out v56d4_low_dim_decomposition.json]` → 固定 `fit=[7,8,9,10] val=[15,16,17,18]` 算 `32` 态 `I_U1/I_U2/I_cross + CE_U1/CE_U2/acc_U1/acc_U2 + 流水分段 + V13合同两路对比`，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow`，`py_compile` PASS；输出 `v56d4_low_dim_decomposition.json` + 控制台摘要
- 报告 `LOW_DIM_DECOMPOSITION_REPORT.md`: 每源 `I_32/CE/acc/NLL/q_mass/流水坍缩点/两路合同差值` 与总体二选一分流，数据与 json 一致，不扩大为 FER/阈值/SKR/晋升，显式 `原 90 已揭盲不可复用` 与 `主算法不否定`，显式 `不以 1024 plug-in MI 分流`
- 守卫：诊断期 **零 decoder**、原 90 已揭盲保护、**不创建 run_01 decoder 执行**、**不做阈值/方向/frame-start 网格**

## 9. 与 V56D3R1 衔接

- V56D3R1 已排除 `SYMBOL_MAPPING_CONTRACT_ERROR`（`5` 族 + 固定 `1024` 置换失败）但 `1024` plug-in `I` 偏置致 `PAIRING vs DOMAIN` 未分；V56D4 在其上用 `32` 态去偏 + `CE/acc` 泛化 + `V13` 合同回放完成分离；`V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 仍为对照，不重发明。

## 10. 自由裁量 D1-D6

- D1 `I_32/CE` 仅 `numpy` 直算，不引 `scipy`（ponytail: `numpy` 已装）
- D2 `fit/val` 固定 `[7,8,9,10]/[15,16,17,18]` 不搜索多划分（仅预注册一种）
- D3 `V13` 合同仅两路对比，不扩网格（`grid` 禁止）
- D4 交叉 `I(U1A;U2B)` 仅佐证，不作主分流阈
- D5 流水分段取 `raw/pairing/occupancy/anchor/U1U2` 五段，不做更细 `sync/occupancy` 网格
- D6 不产生新矩阵/码参数，仅分解与判定，最简闭环
