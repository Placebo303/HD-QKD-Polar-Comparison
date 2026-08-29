# OpenSpec Tasks: formal-ir-v57-channel-recharacterization — V57 decoder-free 信道重表征

**Lifecycle**: `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN` — **decoder-free 信道重表征，不调码、不运行 decoder，三源独立 validation 全过才允 V58**
**HEAD**: `49a415b8253c9c73da0013588d0c50c0e9d41dba` (branch `formal-ir-mainline`, 实际以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v56-input-contract-reconstruction` `V56` `DIAGNOSIS_RESULT_ACCEPTED` (域不兼容已定位，V54 43/45 方法有效性保持，方向不否定)
**Method frozen**: `V54二阶段 H1-16/Lane C m2 184/190/192(对照)/H_inc1/2 Δ8+8/decoder 90/1.0 poly37/L2-only tag/TRAIN prior` 零改直至 V58；`m 184/190/192` 仅对照，新 `m1/m2` 仅重算报告
**Boundary**: `V55` 原 `90-block` 永久禁用；`Cal 19..50 / Val 77..108` 均与 `V55 90×4` 及 `V56 [7,8,9,10,15,16,17,18]` 零重叠；三源分别四门，仅全过才 V58；不网格择优；`DECODE_FORBIDDEN`

## Phase A — 校准/验证预注册与零重叠校验（decoder-free，可机械校验）

- [ ] **A1 定义 Cal/Val 帧（统一三源，显式冻结）**：每源 `Cal 19..50 (32 frames, 8 blocks×4: 19-22/23-26/27-30/31-34/35-38/39-42/43-46/47-50, 8192 pairs)` + `Val 77..108 (32, 8×4: 77-80/81-84/85-88/89-92/93-96/97-100/101-104/105-108, 8192)`，三源 `F=2130/5125/5513` 范围内，`pairs_per_frame 256`, `frame_id∈[0,F-1]`，连续无缺失，写入 `v57_calibration_registry.json` 与 `v57_validation_registry.json` (`per_source {F,K,selected_frame_ids,blocks=8,pairs=8192, provenance:{v55_registry_sha, frame_period 204800, processing_rule legacy_v1}}`)，`overall_zero_overlap_verified` 初始 `false`
- [ ] **A2 零重叠机械校验（硬门）**：脚本启动即 `assert set(Cal)∩set(Val)==∅` per source, `assert set(Cal∪Val)∩set(V55_90flat)==∅` (V55 flat = `v55_authoritative_registry.json: selected_frame_ids` 展开 `120` frames/source), `assert set(Cal∪Val)∩{7,8,9,10,15,16,17,18}==∅`, `assert all(0<=fid<F_s)`，落盘 `v57_manifest.json: zero_overlap_proofs {cal∩val, cal∪val∩v55, ∩v56}` 全 `true`，失败则 `V57_EVIDENCE_INVALID` 零估计
- [ ] **A3 注册表落盘**：`v57_calibration_registry.json + v57_validation_registry.json + v57_manifest.json` 含 `schema v57_cal/val_v1, lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING, data_sha 84d62779, head 49a415b, provenance_note, created_at, command`，`git diff` 仅本目录

## Phase B — Calibration 联合计与信道/熵/泄漏重算（decoder-free，不沿用 V25 184/190/192）

- [ ] **B1 读 Cal 切片**：`--pairs-root comparison_bench/outputs_comparison/v55_intake_20260828/pairs` 的 `alice_symbol/bob_symbol` 按 `frame_id` 切 `Cal 19..50` (每源 `8192` rows)，`F03 5+5 natural` 分解 `U1=>>5, U2=&31`，校验 `alice/bob ∈[0,1023]` 且 `frame 256` 连续
- [ ] **B2 算 C_ab/P/H**：每源 `C_ab = bincount2d(a_cal,b_cal) 1024×1024 int32 sum8192` → `N_b, P(b), P_hat(a|b)=C_ab/N_b (N_b>0 else uniform)` → `H(A|B)=-Σ_b P(b)Σ_a P log2 P` → `P(u1|b)=Σ_{u2} P(32*u1+u2|b) → H(U1|B)` → `H(U2|B,U1)=H-H1`，校验 `|H-H1-H2|<1e-9` 否则 `EVIDENCE_INVALID`，落盘 `per_source {C_shape, N_cal, zero_cells, zero_frac, H, H1, H2, delta_check}`
- [ ] **B3 泄漏重算（source-adaptive）**：`f_target=1.3, n=1024, tag=64, log2q=5` → `m_total=floor((1.3*1024*H -64)/5)`, `m1=round(m_total*H1/H)` (Python round half even), `m2=m_total-m1`, `leak=5*m_total+64`, `f_eff=leak/(1024*H)`, `Δ_m=m_total-m_total_V25ref (200/206/208)`, `Δ_leak=5*Δ_m`，**显式不沿用 `V25 184/190/192`**，新 `m` 仅报告不写入码，落盘 `per_source {m_total,m1,m2,f_eff,leak,Δ_m,Δ_leak}`，`m_total` 越界或 `H<0.1` 则 `EVIDENCE_INVALID`
- [ ] **B4 自洽/对照量**：`cal_NLL_self=mean_{Cal}[-log2 P_hat(a|b) clamp1e-15] ≈H`, `cal_acc_self=mean[a==argmax P_hat]`, `V25_NLL_on_Cal=mean_{Cal}[-log2 P_V25(a|b)]` (P_V25 来自 `channel_counts.npz` 列归一)  bits/symbol & bits/block，报告 `V25 NLL` 退化 `20-28` 的回落幅度

## Phase C — Validation 四门独立校验（decoder-free，三源分别，不用总体平均）

- [ ] **C1 读 Val 切片**：同 `B1` 按 `Val 77..108` 切 `8192` rows/源，校验 `Val∩Cal==∅` 已过
- [ ] **C2 V1 NLL 一致性**：`NLL_val=mean_{Val}[-log2 P_cal(a|b) clamp1e-15]` bits/symbol (P_cal 来自 Cal)，`NLL_val_block*1024`，`NLL_V25_on_Val=mean_{Val}[-log2 P_V25(a|b)]`，`PASS_V1 = (NLL_val <= H_cal+0.50) && (NLL_val<=1.50) && (NLL_val < NLL_V25_on_Val-5.0)` per source
- [ ] **C3 V2 MAP 准确率**：`acc_val=mean_{Val}[a==argmax_{a'} P_cal(a'|b)]` (1024态全局MAP)，`acc_cal` 同，`PASS_V2=(acc_val>=0.60) && (acc_val>=acc_cal-0.10)` per source
- [ ] **C4 V3 零计数覆盖**：`C_ab_val` 同，`P_val_emp=C_ab_val/N_val`，`q_mass=Σ_{C_ab_cal==0} P_val_emp`，`zero_frac_cal=#{zero}/1M`，`PASS_V3=(q_mass<=0.20)` per source (zero_frac 仅报告)
- [ ] **C5 V4 熵稳定性**：`H_val=H(A|B)_Val` (同 B2 公式但用 Val 计数)，`PASS_V4=(|H_val-H_cal|<=0.20) && (|H_val-H_cal|/H_cal<=0.25)` per source
- [ ] **C6 per source 四门汇总**：`PASS_s = PASS_V1&&V2&&V3&&V4 && zero_overlap_s && counts_valid_s`，落盘 `per_source {NLL_val,NLL_V25,acc_val,acc_cal,q_mass,zero_frac,H_val, V1..V4 booleans, PASS_s}`，**三源分别，不用总体平均**，`rg "mean("` 总体平均仅报告不作门

## Phase D — 三源总体判定与 V58 门（互斥 3 选 1，按优先级，不主观）

- [ ] **D1 总体判定（优先级高→低，互斥）**：
  ```
  if not zero_overlap_all or not counts_valid_all or |H-H1-H2|>=1e-9:
      overall = V57_EVIDENCE_INVALID
  elif PASS_1M && PASS_1p5M && PASS_2M:
      overall = V57_CHANNEL_RECHARACTERIZATION_PASS  # 三源均四门通过
  else:
      overall = V57_CHANNEL_RECHARACTERIZATION_FAIL  # 含 MIXED_BY_SOURCE 子态：逐源 PASS_s 清单
  ```
  落盘 `overall` 与 `shunt_per_source {PASS_s, V1..V4}` 至 `v57_channel_recharacterization.json:verdict`
- [ ] **D2 仅全过才允 V58**：`PASS` 时报告显式声明“**允许另起 V58 走 QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH 的 decoder TEST** (需冻结全新 TEST blocks 30/source 与 Cal/Val/V55 零重叠，未揭盲)”；`FAIL/INVALID` 均显式“**不允许 decoder TEST**”，需修 `Cal/Val` 划分或扩至 `64` 帧后重审，不进入 `decoder`，`V58` 仍 `PENDING`
- [ ] **D3 边界固化**：报告与 spec 显式声明 `V55 90` 永久禁用（已揭盲 `0/90`）；`Cal/Val` 同属 `20260123/20260107` 已诊断 `pairs.parquet` 衍生，**不宣称完全独立 cross-session 资格**，真正 `cross-session qualification` 放 `V58` 新 `TEST`（`TEST` 与 `Cal/Val` 零重叠但仍同 acquisition，边界为 `fresh within-session confirmation`，`V58` 报告需显式边界）；`V25 184/190/192` 废弃不沿用已声明

## Phase E — 脚本与报告交付（V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN）

- [ ] **E1 编写 `v57_channel_recharacterization.py`** (decoder-free, 本变更目录下): `python v57_channel_recharacterization.py [--pairs-root ...] [--counts ...] [--v55-registry ...] [--out v57_channel_recharacterization.json] [--report V57_CHANNEL_RECHARACTERIZATION_REPORT.md]` → A零重叠 → B Cal `C_ab/H/H1/H2/m1/m2/f` → C Val 四门 → D 总体判定，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow` (+ `src/nonbinary` 仅 `H` 公式参考不调码)，`py_compile` PASS，输出 `v57_channel_recharacterization.json + V57_CHANNEL_RECHARACTERIZATION_REPORT.md + v57_manifest.json` + 控制台摘要，校验 `set(Cal)∩set(Val)==∅` 且 `∩V55==∅ && ∩V56==∅`
- [ ] **E2 撰写 `V57_CHANNEL_RECHARACTERIZATION_REPORT.md`**：每源 `H/H1/H2/NLL_val/NLL_V25/acc_val/acc_cal/q_mass/zero_frac/H_val/m_total/m1/m2/f_eff/Δ_m/Δ_leak + V1..V4明细` + 总体 `PASS/FAIL/INVALID` 与 `V58` 放行声明，数据与 `json` 一致，含 `V55 90 已揭盲不可复用` + `V25 184/190/192 已废弃不沿用` + `仅全过才 V58` + `同 session 剩余帧仅 within-session` 边界，结论不扩大为 `FER/阈值/SKR/晋升`，明确 `Cal 19..50 / Val 77..108` 统一
- [ ] **E3 自检**：`py_compile` PASS, `rg "decode_" 0 hits`, `git diff -- src/ ==0` 且 `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0` (未改码), `set(Cal)∩set(Val)==∅ && ∩V55==∅ && ∩V56==∅` 已验, `|H-H1-H2|<1e-9` 已验, `per_source PASS_s` 三源分别已报告, `overall` 互斥 `PASS/FAIL/INVALID` 已落盘, `V57` 新 `m1/m2` 已重算且未写入码, `V25 184/190/192` 废弃声明已写, 报告与 json 一致
- [ ] **E4 推送新 SHA 并停留 `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`**，未创建任何 `.../v57_*/run_01` decoder 执行，不碰 `V55 90` 块，不运行 decoder，仅改本目录文件与脚本，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS/四门阈预注册不调`），`V58` 仍 `PENDING`

## 本变更显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 offset/mapping-corrected 重译)；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior/H_inc` 任一冻结参数或新增矩阵；**沿用 V25 184/190/192 或 V25 channel_counts.npz 作新域预算**（仅作 NLL_V25 对照）；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v57_*/run_01` decoder 执行；任意 `bin_width/dimension/pairing` 网格或阈网格（Cal仅单点 32/32 帧，不择优）；`I` 总体平均替代三源分别判定；将 Cal 择优值回注为新 pipeline；**重发明 TTBin pairing 近似物化**；同帧 `Cal/Val` 评价；覆盖已有输出；`V55 90` 永久禁用違反；**主观“显著恢复”替代四门硬阈**。

## 验收

- proposal/design/tasks/specs 一致 HEAD 49a415b 84d62779 lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING DECODE_FORBIDDEN 终态 3 选 1 按优先级互斥明确（`EVIDENCE_INVALID > PASS(全过) > FAIL(含 MIXED)`），显式三源分别、四门硬阈、`V55 90` 永久禁用、仅全过才 V58、不沿用 184/190/192
- 预注册 `Cal 19..50 (32,8192)` + `Val 77..108 (32,8192)` 统一三源已验 `Cal∩Val==∅ && Cal∪Val∩V55==∅ && ∩V56==∅`, `frame_id∈[0,F-1]`, `pairs 256/frame`, 注册表已落盘
- Calibration `C_ab 1024×1024 → H/H1/H2 (F03 5+5, U1>>5 &31) → 链式 |H-H1-H2|<1e-9 → m_total/m1/m2/f_eff/leak/Δ (f1.3 n1024 tag64 log2q5 round)` 已重算，三源分别 `8192` 样本，不沿用 184/190/192
- Validation `NLL_val (≤H+0.5 & ≤1.5 & <V25-5) / acc≥60% / q_mass≤20% / |H_val-H_cal|≤0.20&25%` 四门已逐源判定，`per_source PASS_s` 三源分别，不用总体平均，`overall` 仅全过才 PASS 已落盘
- 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA PENDING/DECODE_FORBIDDEN 仅改本目录（`src/` 零改），原 90 未碰，`V25 184/190/192` 废弃声明已写，推送后等待独立审核，`V58` 仍 PENDING
