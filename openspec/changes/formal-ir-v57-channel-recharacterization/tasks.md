# OpenSpec Tasks: formal-ir-v57-channel-recharacterization — V57 decoder-free 平滑信道重表征（Revised）

**Lifecycle**: `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN` — **decoder-free 扩样+平滑重表征，不调码、不运行 decoder，三源独立估计器三门全过才允 V58**
**HEAD**: `ea39a83d844ce60c86418b753cf95576416233f4` (branch `formal-ir-mainline`, 修订后以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v56-input-contract-reconstruction` `V56` `DIAGNOSIS_RESULT_ACCEPTED` + 前版 `V57 8192 MLE ESTIMATOR_UNDERSAMPLED` 触发修订
**Method frozen**: `V54二阶段 H1-16/Lane C m2 184/190/192(对照)/H_inc1/2 Δ8+8/decoder 90/1.0 poly37/L2-only tag/TRAIN prior` 零改直至 V58；`m 184/190/192` 仅对照，新 `m1/m2_ceil` 仅重算报告
**Boundary**: `V55` 原 `90-block` 永久禁用；新 `Cal/Val` 每源 `512+512` 与 `V55 90×4` 及 `V56 [7,8,9,10,15,16,17,18]` 及前版 `V57 64 [19..50,77..108]` 四重零重叠；平滑 `α=1.0` 仅 Cal 内固定；三源分别估计器三门，仅全过才 V58；`MAP/q_mass` 仅描述；`m ceil`；不网格择优；`DECODE_FORBIDDEN`；前版 `8192` 归档为 `negative_control` 不覆盖

## Phase A — 校准/验证预注册与零重叠校验（decoder-free，扩样，可机械校验）

- [ ] **A1 定义 Cal/Val 帧（每源独立，大样本，显式冻结）**：每源 `Cal = available_s[0:512]` + `Val = available_s[512:1024]`，其中 `available_s = sorted(set(0..F_s-1) - V55_flat_s - {7,8,9,10,15,16,17,18} - {19..50,77..108})`，`F=2130/5125/5513`, `pairs_per_frame 256`, `Cal/Val 各131072 pairs/源 (=512*256), 128 blocks×4`, `frame_id∈[0,F-1]`，三源独立但算法确定性，可复现，写入 `v57_calibration_registry.json` 与 `v57_validation_registry.json` (`per_source {F,K,selected_frame_ids[512],blocks=128,pairs=131072, provenance:{v55_registry_sha, excluded: {V56_8, undersampled_64}, frame_period 204800, processing_rule legacy_v1, smoothing α=1.0}}`)，`overall_zero_overlap_verified` 初始 `false`，前版 `8192` 注册表归档
- [ ] **A2 零重叠机械校验（硬门，四重）**：脚本启动即 `assert set(Cal)∩set(Val)==∅` per source, `assert set(Cal∪Val)∩set(V55_90flat)==∅` (120 frames/source), `assert set(Cal∪Val)∩{7,8,9,10,15,16,17,18}==∅`, `assert set(Cal∪Val)∩{19..50,77..108}==∅`, `assert |Cal|==512 && |Val|==512 && all(0<=fid<F_s)`，落盘 `v57_manifest.json: zero_overlap_proofs {cal∩val, cal∪val∩v55, ∩v56, ∩undersampled} 全 true`，失败则 `V57_EVIDENCE_INVALID` 零估计
- [ ] **A3 注册表落盘与负对照归档**：`v57_calibration_registry.json + v57_validation_registry.json + v57_manifest.json` 含 `schema v57_cal/val_v2, lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED, data_sha 84d62779, head ea39a83→新SHA, smoothing α=1.0 Laplace, ceil formula, provenance_note, created_at, command`；前版 `v57_channel_recharacterization.json/report` 原地归档为 `v57_channel_recharacterization_undersampled_mle_negative_control.json/md` with `schema v57_undersampled_mle_negative_control_v1, lifecycle ESTIMATOR_UNDERSAMPLED`，`git diff` 仅本目录不含 `src/`

## Phase B — Calibration 平滑联合计数与信道/熵/泄漏重算（decoder-free，弃裸MLE，ceil）

- [ ] **B1 读 Cal 切片（扩样）**：`--pairs-root comparison_bench/outputs_comparison/v55_intake_20260828/pairs` 的 `alice_symbol/bob_symbol` 按 `frame_id` 切新 `Cal` 每源 `512` frames (`131072` rows)，`F03 5+5 natural` 分解 `U1=>>5, U2=&31`，校验 `alice/bob ∈[0,1023]` 且每帧 `256` 连续（跳过 forbidden但Cal内每帧校验）
- [ ] **B2 算 C_ab/P_smooth/H_smooth**：每源 `C_ab = bincount2d(a_cal,b_cal) 1024×1024 int32 sum131072` → `N_b, P(b), P_mle=C/N_b` (对照) → `P_smooth(a|b)=(C_ab+1)/(N_b+1024)` (`α=1.0` Laplace, `Q=1024`) → `H_smooth(A|B)=-Σ_b P(b)Σ_a P_smooth log2` → `P_smooth(u1|b)=Σ_{u2} P_smooth(32*u1+u2|b) → H_smooth(U1|B)` → `H_smooth(U2|B,U1)=H_smooth-H1_smooth`，校验 `|H-H1-H2|<1e-9` 否则 `EVIDENCE_INVALID`，落盘 `per_source {C_shape, N_cal=131072, zero_cells_mle, zero_frac_mle, H_smooth, H1_smooth, H2_smooth, H_mle_contrast, delta_chain}`
- [ ] **B3 泄漏重算（source-adaptive，ceil修订）**：`f_target=1.3, n=1024, tag=64, log2q=5, H=H_smooth` → `m_total=ceil((1.3*1024*H -64)/5)` (修订 floor→ceil), `m1=ceil(m_total*H1/H)` (修订 round→ceil), `m2=m_total-m1`, `leak=5*m_total+64` (tag明确计入total), `f_eff=leak/(1024*H)` (含tag), `Δ_m=m_total-m_total_V25ref (200/206/208 floor refs)` 及 `Δ_leak=5*Δ_m`，**显式不沿用 `V25 184/190/192`**，新 `m` 仅报告不写入码，落盘 `per_source {m_total_ceil,m1_ceil,m2,f_eff,leak,Δ_m,Δ_leak, formula: ceil}`，`m_total` 越界或 `H<0.1` 则 `EVIDENCE_INVALID`
- [ ] **B4 自洽/对照/收敛序列**：`cal_NLL_self_smooth=mean_{Cal}[-log2 P_smooth]` (≈H)、`cal_NLL_self_mle_clamp` (负对照)、`cal_acc_self_smooth` 描述、`V25_NLL_on_Cal` (对照) bits/symbol；另对 `Cal` 子采样 `32,128,256,512` frames 分别算 `H_smooth/NLL_smooth` 序列，报告 `NLL_30→~3` 收敛趋势，落盘 `convergence: {32: {H,NLL},128...,256...,512...}`

## Phase C — Validation 估计器三门独立校验（decoder-free，三源分别，q_mass/MAP仅描述）

- [ ] **C1 读 Val 切片（扩样）**：同 `B1` 按新 `Val 512` 切 `131072` rows/源，校验 `Val∩Cal==∅` 及四重零重叠已过
- [ ] **C2 EG1 NLL有限且改善**：`NLL_val_smooth=mean_{Val}[-log2 P_cal_smooth]` (P_cal_smooth来自Cal，平滑)、`NLL_val_mle_clamp` (裸MLE clamp负对照)、`NLL_V25_on_Val`，`PASS_EG1 = (isfinite && NLL_val_smooth <15.0) && (NLL_val_smooth < NLL_val_mle_clamp -5.0) && (NLL_val_smooth < NLL_V25_on_Val)` per source
- [ ] **C3 EG2 CV一致性**：`NLL_cal_self_smooth` 同，`Cal` 内2-fold `NLL_cal_fold1`= `P_smooth_fold1` 在 `fold2` 上测，`NLL_cal_fold2` 对称，`PASS_EG2=(|NLL_val_smooth - NLL_cal_self_smooth| <=0.50 && rel<=0.25) && (|fold1-fold2| <=0.50)` per source
- [ ] **C4 EG3 熵稳定性与收敛**：`H_val_smooth=H_smooth(A|B)_Val` (同B2但用Val计数+同α平滑)，`PASS_EG3=(|H_val_smooth-H_cal_smooth|<=0.20) && (|H_val-H_cal|/H_cal<=0.25)` per source；另报告收敛：`NLL_val_smooth` 较前版 `8192 MLE 30` 下降>5bits 且 `H` 序列单调稳定（描述）
- [ ] **C5 Descriptive only**：`q_mass_mle=Σ_{C_ab_cal_mle==0} P_val_emp` 与 `zero_frac_mle` 仅描述（预期131k下 `zero~87%` 但NLL不再虚高）、`acc_smooth=mean[a==argmax P_smooth]` 仅描述不设60%硬阈，落盘所有 descriptive 量
- [ ] **C6 per source 三门汇总**：`PASS_s = PASS_EG1&&EG2&&EG3 && zero_overlap_s && counts_valid_s`，落盘 `per_source {NLL_val_smooth,NLL_val_mle_clamp,NLL_V25,acc_descriptive,q_mass_descriptive,zero_frac,H_val_smooth, convergence_series, EG1..EG3 booleans, PASS_s}`，**三源分别，不用总体平均**

## Phase D — 三源总体判定与 V58 门（互斥 3 选 1，按优先级，估计器语义）

- [ ] **D1 总体判定（优先级高→低，互斥）**：
  ```
  if not zero_overlap_all or not counts_valid_all or |H-H1-H2|>=1e-9:
      overall = V57_EVIDENCE_INVALID
  elif PASS_1M && PASS_1p5M && PASS_2M:  # EG1-3均通过
      overall = V57_CHANNEL_RECHARACTERIZATION_PASS
  else:
      overall = V57_CHANNEL_RECHARACTERIZATION_FAIL  # 含 MIXED_BY_SOURCE 子态
  ```
  落盘 `overall` 与 `shunt_per_source {PASS_s, EG1..EG3}` 至 `v57_channel_recharacterization.json:verdict`
- [ ] **D2 仅全过才允 V58**：`PASS` 时报告显式声明“**允许另起 V58 走 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH 的 decoder TEST** (需冻结全新 TEST blocks 30/source 与 Cal512/Val512/V55 90/undersampled 64 均零重叠，未揭盲)”；`FAIL/INVALID` 均显式“**不允许 decoder TEST**”，需进一步扩样本或检查平滑，不进入 `decoder`，`V58` 仍 `PENDING`
- [ ] **D3 边界固化**：报告与 spec 显式声明 `V55 90` 永久禁用；`Cal/Val` 同属 `20260123/20260107` 已诊断 `pairs.parquet` 衍生，**131k平滑后仍不宣称完全独立 cross-session 资格**，真正 `cross-session qualification` 放 `V58` 新 `TEST`；`V25 184/190/192` 废弃不沿用；前版 `8192 MLE` 已归档为 `UNDERSAMPLED_MLE_NEGATIVE_CONTROL` 且 `H 2.27-2.64 vs NLL 30-37` 分裂作为负对照对比，`MAP/q_mass` 仅描述已声明，`ceil+tag` 语义已声明

## Phase E — 脚本与报告交付（V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN）

- [ ] **E1 编写 `v57_channel_recharacterization.py`** (decoder-free, 本变更目录下, 修订平滑+ceil): `python v57_channel_recharacterization.py [--pairs-root ...] [--counts ...] [--v55-registry ...] [--alpha 1.0] [--out v57_channel_recharacterization.json] [--report V57_CHANNEL_RECHARACTERIZATION_REPORT.md]` → A四重零重叠 → B Cal `C_ab/P_smooth/H_smooth/m_ceil` + 收敛序列 → C Val EG1-3 + descriptive → D 总体判定 → 归档负对照，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v57_channel_recharacterization.json + V57_CHANNEL_RECHARACTERIZATION_REPORT.md + v57_manifest.json + registries` + 负对照归档 + 控制台摘要，校验 `Cal∩Val==∅ && ∩V55==∅ && ∩V56==∅ && ∩undersampled==∅` 及 `|H-H1-H2|<1e-9`
- [ ] **E2 撰写 `V57_CHANNEL_RECHARACTERIZATION_REPORT.md`**：每源 `H_smooth/H1/H2/NLL_smooth/NLL_mle_clamp负对照/NLL_V25/acc_descriptive/q_mass_descriptive/zero_frac/H_val_smooth/m_total_ceil/m1_ceil/m2/f_eff/Δ_m + EG1..EG3明细` + 总体 `PASS/FAIL/INVALID` 与 `V58` 放行声明 + **`Negative Control` 章节**对比前版 `8192 MLE` (`H 2.27/2.40/2.64, NLL 30/32/37, q_mass 59/64/74%, zero 99.4%, acc 36/29/19%`) 与新 `131k smooth` + **收敛序列** `32→512` 表，数据与 `json` 一致，明确 `Cal 512/Val 512` 每源独立及 `α=1.0` 平滑、`ceil+tag`、仅描述语义
- [ ] **E3 自检**：`py_compile` PASS, `rg "decode_" 0 hits`, `git diff -- src/ ==0` 且 `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0` (未改码), 四重零重叠已验, `|H-H1-H2|<1e-9` 已验, `α=1.0` 固定未择优已验, `ceil` 公式已验, `per_source PASS_s` 三源分别已报告, `overall` 互斥 `PASS/FAIL/INVALID` 已落盘, `V57` 新 `m1/m2_ceil` 已重算且未写入码, `V25 184/190/192` 废弃声明已写, 负对照已归档不覆盖, 报告与 json 一致
- [ ] **E4 推送新 SHA 并停留 `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN`**，未创建任何 `.../v57_*/run_01` decoder 执行，不碰 `V55 90` 块，不运行 decoder，仅改本目录文件与脚本，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS/估计器三门预注册不调/α固定/ceil`），`V58` 仍 `PENDING`

## 本变更显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 offset/mapping-corrected 重译)；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior/H_inc` 任一冻结参数或新增矩阵；**沿用 V25 184/190/192 或 V25 channel_counts.npz 作新域预算**（仅作 NLL_V25 对照）；**用 Val 择优 α 或平滑方式**（α=1.0 仅 Cal 内固定）；**将 floor/round 当 ceil**；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v57_*/run_01` decoder 执行；任意 `bin_width/dimension/pairing` 网格或阈网格（Cal仅单点 512+512+α=1.0，不择优）；用 `q_mass≤20%` 或 `acc≥60%` 硬门直接判失败（已改描述）；`I` 总体平均替代三源分别判定；将 Cal 择优值回注为新 pipeline；覆盖前版 `8192` 结果（已归档为 negative_control）；`V55 90` 永久禁用違反；**主观“显著恢复”替代估计器三门硬阈**。

## 验收

- proposal/design/tasks/specs 一致 HEAD ea39a83→新SHA 84d62779 lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED DECODE_FORBIDDEN 终态 3 选 1 按优先级互斥明确（`EVIDENCE_INVALID > PASS(全过) > FAIL(含 MIXED)`），显式三源分别、估计器三门、`V55 90` 永久禁用、仅全过才 V58、不沿用 184/190/192、α固定、ceil+tag、负对照不覆盖
- 预注册 `Cal 512 (131072)` + `Val 512 (131072)` 每源独立 `available_s` 可验四重零重叠 (`Cal∩Val==∅ && Cal∪Val∩V55==∅ && ∩V56==∅ && ∩undersampled64==∅`), `frame_id∈[0,F-1]`, `pairs 256/frame`, 注册表已落盘，负对照已归档
- Calibration `C_ab 1024×1024 → P_smooth=(C+1)/(N_b+1024) α=1.0 → H_smooth/H1/H2 (F03 5+5) → 链式 |H-H1-H2|<1e-9 → m_total/m1/m2/f_eff/leak/Δ (f1.3 n1024 tag64 log2q5 ceil, tag计入)` 已重算且含收敛序列，三源分别 `131k` 样本，不沿用 184/190/192
- Validation `EG1 NLL有限改善(<15 & <MLE-5 & <V25) / EG2 CV≤0.5 / EG3熵≤0.20&25%+收敛` 三门已逐源判定，`q_mass/zero_frac` 与 `acc` 仅描述，不入硬门，`per_source PASS_s` 三源分别，不用总体平均，`overall` 仅全过才 PASS 已落盘，前版 `8192 MLE 30bits` 已作负对照
- 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA PENDING/DECODE_FORBIDDEN 仅改本目录（`src/` 零改），原 90 未碰，`V25 184/190/192` 废弃声明已写，推送后等待独立审核，`V58` 仍 PENDING
