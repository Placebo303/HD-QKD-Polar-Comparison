# OpenSpec Proposal: formal-ir-v57-channel-recharacterization (Revised)

**Status**: `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN` — **decoder-free 信道重表征，不调 LDPC、不运行 decoder、不复用 V55 TEST 90 块。REVISE_REQUIRED 原因：前版 8192 pairs 估计 1024×1024=1M cell，99.35%零、val 59-74%落零cell、NLL 30bits 源于1e-15裁剪非信道失败，H_cal 2.3 vs NLL 30 分裂为稀疏过拟合。本次一次性修订：扩样至每源 ≥512+512、弃裸MLE引入平滑、门禁改为估计器门禁、MAP仅描述、m用ceil。**
**Domain**: Formal IR / V57 channel recharacterization (V56 唯一后继，V58 decoder TEST 前置门)
**Change ID**: `formal-ir-v57-channel-recharacterization`
**Cycle ID**: `V57` (channel-recharacterization), predecessor `V56` `formal-ir-v56-input-contract-reconstruction`
**Predecessor**: `formal-ir-v56-input-contract-reconstruction` (HEAD `49a415b8253c9c73da0013588d0c50c0e9d41dba` -> 修订前 `ea39a83d844ce60c86418b753cf95576416233f4`, branch `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点；结论 `DIAGNOSIS_RESULT_ACCEPTED` — 域不兼容已定位，`V54二阶段 43/45` 在 `2026-01-21` 域有效性保持，当前方向不否定)
**Branch**: `formal-ir-mainline`
**HEAD**: `ea39a83d844ce60c86418b753cf95576416233f4` (修订前；修订后以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准，本次修订推送新 SHA)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点不改；calibration/validation 帧亦同点)
**Lifecycle**: `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN` — 仅 decoder-free 信道估计与验证，不产生 `run_01` decoder 执行，不改 `H1/Lane C/H_inc/Δ/decoder 90/1.0/poly37`
**Method frozen**: `V54二阶段 H1-16(80b)+L1-APP via H1 BP(TRAIN channel_counts.npz)+Lane C m2 184/190/192+H_inc1/2 Δ8+8+decoder 90/1.0 poly37+L2-only tag` 完全冻结（重表征期零改，新 `m1/m2/Δ` 仅重算报告不写入码）
**Revision trigger**: `REVISE_REQUIRED / ESTIMATOR_UNDERSAMPLED / DECODE_FORBIDDEN` — 8192样本在1M cell上 99.35%零、val质量59-74%落零格、clamp 1e-15 产生30bits虚假NLL、H 2.3与NLL分裂，判定为稀疏过拟合而非信道难度；需扩样+平滑重估。

> ponytail lite: 本修订仅 4 OpenSpec 工件 + 1 decoder-free 重表征脚本（含平滑）+ 2 注册表 + 1 报告 + 1 negative-control归档；无 runner、无 decoder、无新矩阵、无新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: `numpy` 直算 `1024×1024` 计数/`pandas` 读 `parquet` 已覆盖，无需 `scipy` 或 LDPC 依赖；平滑为确定性 `+alpha` 算术，不引新库。

> **研究方向保持**：`V54` 在 `2026-01-21` 域 `43/45` 已证 `V54_DELTA8_ALREADY_SUFFICIENT` 方法有效性；`V55 0/90` 已定位为跨 session 输入域不兼容（非算法证伪），`V56` 诊断已排除 `1024置换/阈网格` 等假说；`V57` 仅以新 session 实测重估信道与泄漏，不否定既有码族与双阶段救援架构。本次修订保留前版8192结果为 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL` 对照，不覆盖。

## Goal

以最短 decoder-free 路径完成 **新 session 联合信道重表征（修订：大样本+平滑）**，为 `V58` decoder TEST 提供可验证的信道先验与泄漏预算，且满足 **三源独立、估计器门禁全过才放行** 的硬门槛。本次修订一次性解决 `ESTIMATOR_UNDERSAMPLED` 根因：

### 1. 扩大 calibration/validation 至每源至少 512 Cal +512 Val 零重叠，利用数千 frames（2130/5125/5513）

- **零重叠硬约束**（可机械校验，修订后）：
  ```
  set(Cal_s) ∩ set(Val_s) == ∅  per source
  set(Cal_s ∪ Val_s) ∩ set(V55_90×4) == ∅  per source  (V55 authoritative 30/source×4=120 frames/source)
  set(Cal_s ∪ Val_s) ∩ set(V56_fit∪val=[7,8,9,10,15,16,17,18]) == ∅
  set(Cal_s ∪ Val_s) ∩ set(V57_undersampled_64=[19..50,77..108]) == ∅  # 新增：与前版负对照零重叠
  |Cal_s| ≥512, |Val_s| ≥512  per source, pairs ≥131072 per split
  frame_id ∈ [0, F_s-1], F=2130/5125/5513, pairs_per_frame 256, 连续无缺失可选但允许稀疏跳过 V55/V56
  ```
  未通过则 `V57_EVIDENCE_INVALID`，不进入信道估计。

- **预注册帧（修订：每源独立、大样本、显式冻结）**：
  每源 `F` 不同，无法三源统一 512 连续块而不撞 `V55`（`V55` 密度 ~5.6%，512连续必撞 7-8 块）。故 **每源独立** 按确定性算法预注册：
  ```
  available_s = sorted(set(0..F_s-1) - V55_flat_s - {7,8,9,10,15,16,17,18} - {19..50,77..108})
  Cal_s = available_s[0:512]
  Val_s = available_s[512:1024]
  ```
  满足 `512+512=1024` frames/源 = `131072+131072` pairs/源，利用 `2130/5125/5513` 中数千帧（1M用约48%帧，1p5M/2M约20%/18%），三源 `Cal/Val` 各自零重叠且与 `V55/V56/前版` 均零重叠。具体 `selected_frame_ids` 落盘于 `v57_calibration_registry.json / v57_validation_registry.json`，算法可复现，禁止事后换帧。

  - 选取理由：`V55` 间隙平均 ~69 帧，512 连续不可行；按可用帧排序取前 1024 可确保确定性、最大早期覆盖、零重叠可机械证明，且样本从 `8192→131072` 扩大 `16×`，`1024×1024` 表从 `0.8%→~12.8%` 期望覆盖（按均匀近似），`q_mass` 预期从 `59-74%→<20%` 且NLL虚高消除。
  - 块语义：`512` frames = `128` blocks×`4` frames/块 = `131072` pairs/源，满足 `1024×1024` 平滑后可报告门限；`Val` 同。
  - 注册表：`v57_calibration_registry.json` 与 `v57_validation_registry.json` 分别落盘 `{per_source: {F,K,selected_frame_ids,blocks,provenance,processing_rule, zero_overlap_verified, sample_size}}`，禁止事后换帧。
  - **负对照保留**：前版 `Cal 19..50 / Val 77..108` 的 `v57_channel_recharacterization.json/report` 原地归档为 `v57_channel_recharacterization_undersampled_mle_negative_control.json/md`，状态 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL`，不覆盖，新结果写入 `v57_channel_recharacterization.json` 主文件。

### 2. 弃用裸MLE零概率，预注册 Dirichlet/Laplace 或 backoff 平滑，强度仅 Cal 内固定不用 Val 择优

- **问题**：前版 `P_hat(a|b)=C_ab/N_b` 对零格赋0，`Val` 59-74%落零格时 `clamp 1e-15 → -log2 ≈49.8bits` 主导 `NLL 30bits`，与 `H 2.3` 分裂，非信道失败而是估计器未正则化。
- **修订估计**（decoder-free，`numpy/pandas` 直算，平滑仅 Cal 内固定）：
  ```
  C_ab = bincount2d(a_cal,b_cal)  1024×1024  (N_cal=131072, 前版8192作负对照)
  N_b = Σ_a C_ab,  P_cal_smooth(a|b) = (C_ab + α) / (N_b + α*Q)  if N_b>0 else 1/Q
    where Q=1024, α=1.0  Laplace (Dirichlet α=1)  frozen, pre-registered, not tuned on Val
    alternative Dirichlet α=0.5 noted but primary α=1.0
  P(b)=N_b/N_cal
  H_smooth(A|B) = - Σ_b P(b) Σ_a P_smooth(a|b) log2 P_smooth(a|b)
  P_smooth(u1|b) = Σ_{u2} P_smooth(32*u1+u2|b), H_smooth(U1|B) similarly
  H_smooth(U2|B,U1) = H_smooth(A|B) - H_smooth(U1|B)  (链式闭合 |H-H1-H2|<1e-9)
  ```
  同时报告裸 `MLE H_mle` 与 `zero_cells_cal` 作对照，但 **NLL/熵/泄漏均以平滑版为准**，`α` 禁止用 `Val` 择优，固定 `1.0`。

### 3. 门禁改为估计器门禁：val NLL有限、与 cal CV NLL差受控、随样本增加 NLL/熵收敛、零支持质量不直接判失败

- 对每源 `s∈{1M,1p5M,2M}` 在 `Val_s` 上以 `P_cal_smooth` 测：
  - **EG1 NLL有限且改善**：`NLL_val_smooth = mean_{Val}[-log2 P_cal_smooth(a|b)]` 有限 (`<15 bits`) 且 `NLL_val_smooth < NLL_val_MLE_clamp -5`（消除clamp虚高）且 `NLL_val_smooth < NLL_V25_on_Val`（显著优于退化 prior 22-35）。
  - **EG2 CV一致性**：`|NLL_val_smooth - NLL_cal_self_smooth| ≤0.50` bits 且 `≤25%` 相对；且 `Cal` 内 2-fold CV `|NLL_cal_fold1 - NLL_cal_fold2| ≤0.50`（`Cal` 拆 `256+256`，同平滑），证明泛化受控。
  - **EG3 熵/NLL收敛**：`|H_val_smooth - H_cal_smooth| ≤0.20` 且 `≤25%`；且样本扩大后 `NLL_val_smooth` 较前版 `8192 MLE 30bits` 收敛下降 `>5bits`，`H_cal_smooth` 随 `32→512` 子采样序列单调稳定（报告 `32/128/256/512` 四点 `H/NLL` 曲线，方向收敛不硬阈但需呈现）。
  - **零支持质量仅描述**：`q_mass_on_p_zero_MLE = Σ_{C_ab_cal_MLE==0} P_val_emp` 与 `zero_frac` 仅报告，不设 `≤20%` 硬门（前版因稀疏必FAIL，已改 descriptive）。

  三门 **per source 均 PASS** 才记该源 `PASS_s=True`；任一门 `FAIL` 则 `PASS_s=False`。零覆盖/V3 不再直接判失败。

### 4. 单独报告信道难度 H(U1|B)/H(U2|U1,B)/H(A|B)/MAP 仅描述不设60%硬门

- 每源报告 `H_smooth(A|B), H_smooth(U1|B), H_smooth(U2|B,U1), MAP_acc_smooth = mean[a==argmax P_smooth(a|b)]` 仅作信道难度描述，**不设 `acc≥60%` 硬阈**（前版 `V2` 因稀疏 MAP 36-42% 必FAIL，现改为 descriptive，记录但不门禁）。

### 5. m1/m2 用 ceil 重算 floor((1.3*N*H-64)/5) → ceil，明确 tag 计入效率

- **泄漏重算**（`f_target=1.3, n=1024, tag=64 bits, log2q=5`，`source-adaptive` 同 `V27R`，**修订：ceil**）：
  ```
  m_total_required = ceil((f_target * n * H_smooth_total - tag) / 5)   # 修订：floor→ceil，确保泄漏不低估
  m1_required = ceil(m_total_required * H1_smooth / H_total)  # 修订：round→ceil，边界安全
  m2_required = m_total_required - m1_required  # 保持 m1+m2=m_total，可为0..m_total
  leak_total = 5*m_total_required + 64  # 明确 tag 64b 计入 total
  f_eff = leak_total / (n*H_smooth_total)  # 明确 tag 计入效率
  ```
  显式声明 **不沿用 `V25` 的 `m2 184/190/192` 与 `m1=16`**，新 `m_total/m1/m2` 仅为 `V58` 预算建议，不在 `V57` 实例化新矩阵；`V57` 仍 `DECODE_FORBIDDEN`；`tag` 明确仅 `total` 计一次，不在层间重复计费。

### 6. 本轮8192结果保留为 UNDERSAMPLED_MLE_NEGATIVE_CONTROL 不覆盖

- 前版 `v57_channel_recharacterization.json / V57_CHANNEL_RECHARACTERIZATION_REPORT.md` 原地更名为 `v57_channel_recharacterization_undersampled_mle_negative_control.json/md`，标记 `schema: v57_undersampled_mle_negative_control_v1, lifecycle: ESTIMATOR_UNDERSAMPLED`，保留 `H 2.27-2.64 vs NLL 30-37, q_mass 59-74%, zero 99.4%` 的分裂证据作负对照，不覆盖。
- 新 `131k` 平滑结果写入主 `v57_channel_recharacterization.json` 与主报告，并在报告中设 `Negative Control` 章节对比，证明稀疏过拟合已消除。

### 7. 三源分别判定，仅全过才 V58（`V57_PASS` 硬门，估计器语义）

```
per_source s: PASS_s = EG1_s && EG2_s && EG3_s && zero_overlap_s && counts_valid_s  # V3/ACC 不入 gate
overall:
  if 完整性/零重叠/计数无效 → V57_EVIDENCE_INVALID (最高优先)
  elif not all(PASS_s) → V57_CHANNEL_RECHARACTERIZATION_FAIL (含 MIXED_BY_SOURCE 子态，分源报告)
  else → V57_CHANNEL_RECHARACTERIZATION_PASS
```

仅 `V57_CHANNEL_RECHARACTERIZATION_PASS`（`1M && 1p5M && 2M` 三源均 `EG1-3` 通过）才允许另起 `V58` 走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH` 的 `decoder TEST`（`run_01`）；否则停留 `PENDING` 修 `Cal/Val` 或进一步扩样/调平滑，不进入 `decoder`。

### 8. 不改码参、不运行 decoder（`DECODE_FORBIDDEN` 冻结）

- `H1 16×1024 rank16 80b (V31-H1-QC poly37) / Lane C m2 184/190/192 ordinal-2 / H_inc1/2 8×1024 det1/det2 / H_joint1 192/198/200 / H_total 200/206/208 / decoder 90/1.0 early-stop / L2-only tag 64b / TRAIN-only prior` **全部零改**，`rg "decode_" 0 hits`，`py_compile` 必过；
- 不创建 `.../v57_*/run_01` decoder 执行；`V58` 新 `m1/m2` 矩阵与 `decoder TEST` 需另起 `OpenSpec` 与独立授权；
- `V55` 原 `90-block` 永久禁用（已揭盲 `0/90`），不在其上重跑任何 `corrected pipeline`。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用，`rg "decode_" 0 hits`）；不改 `H1-16/Lane C/H_inc1/2/Δ8+8/m2/leak/tag/prior/decoder 90/1.0 poly37` 任一冻结量；不试新 `Δm/degree/seed`，不新增矩阵。
- 不在原 `V55` authoritative `90-block` (`v55_authoritative_registry.json` 30/source) 上重跑任何 `corrected pipeline / offset-corrected` 重译；不将 `Cal/Val` 择优值回注为新 pipeline。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（`200ps legacy_v1 nearest 1024` 单点锚点）；`Cal` 估计仅单点 `512+512` + 平滑 `α=1.0` 固定，不择优。
- 不宣称 `LDPC` 证伪 / `FER` / 阈值 / `SKR` / 晋升；`V57` 止于信道重表征，不直接进入 qualification。
- 不创建正式 `.../v57_*/run_01` decoder 执行；`V58` decoder TEST 需另起 `OpenSpec` 与独立 `EXECUTE_AUTH`。
- 不改写/覆盖 `V38–V56` 任何已有输出与终态（只读）；前版 `8192` 结果已归档为 `negative_control` 不删除。
- 不以总体平均替代三源分别判定；不以 `V25` `H` 或 `184/190/192` 作为新域预算。
- 不用 `Val` 调 `α` 或选平滑方式；`α=1.0` 仅 `Cal` 内固定。

## Scope

1. **冻结方法零改**：`n=1024, m2 184/190/192 (对照), GF32 poly37, H1 16×1024 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz, 仅对照), Lane C ordinal-2, H_inc1/2 Δ8+8 (冻结对照), decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior (V57 不改 prior，仅重估 H 供 V58)` 全只读，**零 decoder**。
2. **预注册 Cal/Val（零重叠，可机械校验，修订扩样）**：每源 `Cal ≥512 + Val ≥512`（每源独立 `available_s[0:512] / [512:1024]`，`131072/131072` pairs/源，三源 `F=2130/5125/5513` 范围内，`assert` 四重零重叠（含前版64），`provenance` 记录 `V55/V56/undersampled` 排除集，落盘 `v57_calibration_registry.json / v57_validation_registry.json + v57_manifest.json`。
3. **Calibration 信道估计（decoder-free，弃裸MLE，平滑）**：每源 `Cal` 上算 `C_ab 1024×1024 → P_smooth(a|b)=(C+1)/(N_b+1024) → H_smooth(A|B), H_smooth(U1|B), H_smooth(U2|B,U1) (F03 5+5 natural, U1=>>5, U2=&31, 链式闭合 |H-H1-H2|<1e-9) → m_total/m1/m2/f_eff/leak_total (f_target1.3, n1024, tag64, log2q5, m_total/m1=ceil)`，**不沿用 `V25 184/190/192`**，新 `m` 仅报告。
4. **Validation 估计器门禁（decoder-free，三源分别，修订）**：每源 `Val` 上 `NLL_val_smooth / NLL_cal_self_smooth / CV / H_val_smooth`，三阈预注册（`EG1 NLL有限改善; EG2 CV差≤0.5; EG3 熵稳定≤0.20&25%且随样本收敛`），`q_mass-zero_frac` 与 `MAP/ACC` 仅描述不入硬门，**三源分别，不用总体平均**。
5. **三源判定与 V58 门**：`per_source PASS_s = EG1&&EG2&&EG3 && zero_overlap && counts_valid`；`overall PASS = all PASS_s` → `V57_CHANNEL_RECHARACTERIZATION_PASS` 才允许 `V58`；否则 `FAIL` (`MIXED_BY_SOURCE` 子态分源报告) 或 `EVIDENCE_INVALID`；不以单源或平均放行。
6. **脚本与报告交付（DECODE_FORBIDDEN）**：`v57_channel_recharacterization.py` (decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`) 输出 `v57_channel_recharacterization.json` (`per_source {H_smooth,H1,H2,NLL_smooth,acc_descriptive,q_mass_descriptive,zero_frac,m_total,m1,m2,f_eff, Δ, gate_pass} + overall`) 与 `V57_CHANNEL_RECHARACTERIZATION_REPORT.md`（含 `Negative Control` 对比），并产出 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL` 归档；**未创建 `run_01`，已推送新 SHA 并停留 `PENDING/DECODE_FORBIDDEN`，等待独立审核后才允 `V58`**。

## Impact Scope

- **新增/修订（本变更）**：`openspec/changes/formal-ir-v57-channel-recharacterization/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 1 decoder-free 脚本 `v57_channel_recharacterization.py` (本变更目录下, `rg "decode_" 0 hits`, 修订平滑+ceil) + 2 注册表 `v57_calibration_registry.json / v57_validation_registry.json` (pre-registered 512+512 frames) + `v57_channel_recharacterization.json` (131k平滑主结果) + `v57_channel_recharacterization_undersampled_mle_negative_control.json/md` (8192负对照归档) + `V57_CHANNEL_RECHARACTERIZATION_REPORT.md` + `v57_manifest.json` (provenance, HEAD/data SHA, zero_overlap 证明)。
- **只读依赖**：`v55_authoritative_registry.json (V55 90×4 frames)` + `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*.parquet` (`alice_symbol/bob_symbol` 1024) + `workspace/v13r3fresh_20260816/sidecars` (仅对照) + `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` (`V25 TRAIN prior` 仅作 `NLL_V25` 对照，不训) + `nonbinary_v25_gate.py` (`P(A|B)/熵定义` 仅参考) + `v38_architecture_triage.py` (Lane C 常量仅背景)。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录外）、`V38–V56` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01` decoder 执行，零码参**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN`，`HEAD ea39a83` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、**三源分别判定**、仅全过才 `V58`，且本次修订 `ESTIMATOR_UNDERSAMPLED` 根因已记录。
- [ ] **预注册零重叠可复现（扩样）**：每源 `Cal ≥512 + Val ≥512`（每源独立 `available_s[0:512]/[512:1024]`，`131072/131072` pairs/源），已 `assert` 四重零重叠（`Cal∩Val==∅`, `Cal∪Val ∩ V55 90×4==∅`, `∩ V56 [7,8,9,10,15,16,17,18]==∅`, `∩ 前版64==∅`），`frame_id∈[0,F-1]`、`pairs_per_frame 256`，注册表已落盘，负对照已归档不覆盖。
- [ ] **Calibration 估计可复现（平滑）**：每源 `Cal` 上 `C_ab 1024×1024 → P_smooth=(C+1)/(N_b+1024) α=1.0 → H_smooth(A|B), H_smooth(U1|B), H_smooth(U2|B,U1) (F03 5+5, U1>>5 &31, 链式 |H-H1-H2|<1e-9)` 已算，`H/H1/H2` 与 `V25` 差值、`zero_cells/q_mass` 已报告但不入硬门，**不沿用 `V25 184/190/192`**，新 `m_total/m1/m2/f_eff/leak` (`f_target1.3, n1024, tag64, log2q5, m/m1=ceil, tag计入`) 已重算且与 `json` 一致。
- [ ] **Validation 估计器门禁可复现**：每源 `Val` 上 `NLL_val_smooth有限改善`、`CV差|NLL_val-NLL_cal|≤0.5`、`熵稳定性|H_val-H_cal|≤0.20&25%且随样本收敛` 已算，三阈已逐源判定，`q_mass/zero_frac` 与 `MAP acc` 仅描述不入硬门，**三源分别，不用总体平均**，`per_source PASS_s` 已落盘。
- [ ] **三源独立判定可复现**：`overall = V57_CHANNEL_RECHARACTERIZATION_PASS` 当且仅当 `1M && 1p5M && 2M` 均 `PASS_s`，否则 `FAIL` (含 `MIXED_BY_SOURCE` 分源清单) 或 `EVIDENCE_INVALID`，**仅全过才允许 `V58`** 已声明。
- [ ] `v57_channel_recharacterization.py` 为 decoder-free 可运行脚本（`python v57_channel_recharacterization.py [--pairs-root ...] [--counts ...] [--out ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v57_channel_recharacterization.json` 与控制台摘要，**未创建 `run_01`**，且前版 `8192` 已归档为 `negative_control`。
- [ ] `V57_CHANNEL_RECHARACTERIZATION_REPORT.md` 已记录每源 `H_smooth/H1/H2/NLL_smooth/NLL_V25/acc_descriptive/q_mass_descriptive/zero_frac/H_val/m_total/m1/m2/f_eff/Δ`、估计器三门明细与总体终态，含 `Negative Control` 章节对比 `8192 MLE 30bits` 与新平滑 `~2-4bits`，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V55 90 已揭盲不可复用` + `V25 184/190/192 已废弃不沿用` + `仅全过才 V58`。
- [ ] 已推送新 `SHA` 并停留在 `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`，未创建任何 `.../v57_*/run_01` decoder 执行，不碰 `V55 90` 块，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`）。

## Tasks

见 `tasks.md`（Phase A 预注册 Cal/Val 512+512零重叠；Phase B Calibration 平滑H/m重算ceil；Phase C Validation 估计器三门；Phase D 三源总体判定与 V58 门；Phase E 脚本与报告交付至 `PENDING/DECODE_FORBIDDEN`；负对照归档；显式禁止清单与 decoder-free 守卫）。

## Lifecycle

`V56` 当前 `DIAGNOSIS_RESULT_ACCEPTED`（`HEAD 49a415b→ea39a83`, `V56_INPUT_CONTRACT_RECONSTRUCTION` 已固化校准验证与 5 选 1，`V54 43/45` 方法有效性保持，域不兼容已定位）；`V57` 前版 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL`（`8192 MLE, 30bits, 59-74% q_mass`）已归档；`V57` 修订本重表征 `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN`（仅 decoder-free 平滑信道估计与估计器门禁，不实现 runner，不执行 decoder，不创建 `run_01`，不改码参，三源分别）；`V57_PASS`（三源均估计器三门通过）后**另起 successor `V58`** 冻全新 `TEST` blocks（与 `Cal/Val` 及 `V55 90` 及 `undersampled` 零重叠，未揭盲）再走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH` 的 `decoder TEST`，`V57` 本身不直接进入 qualification；`V57_FAIL/INVALID` 则停留修划分或进一步扩样本/调平滑，不进入 `V58`。
