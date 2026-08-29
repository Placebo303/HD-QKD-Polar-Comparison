# OpenSpec Proposal: formal-ir-v57-channel-recharacterization

**Status**: `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN` — **decoder-free 信道重表征，不调 LDPC、不运行 decoder、不复用 V55 TEST 90 块。需三源独立 validation 全过后才允 V58 decoder TEST。**
**Domain**: Formal IR / V57 channel recharacterization (V56 唯一后继，V58 decoder TEST 前置门)
**Change ID**: `formal-ir-v57-channel-recharacterization`
**Cycle ID**: `V57` (channel-recharacterization), predecessor `V56` `formal-ir-v56-input-contract-reconstruction`
**Predecessor**: `formal-ir-v56-input-contract-reconstruction` (HEAD `49a415b8253c9c73da0013588d0c50c0e9d41dba`, branch `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点；结论 `DIAGNOSIS_RESULT_ACCEPTED` — 域不兼容已定位，`V54二阶段 43/45` 在 `2026-01-21` 域有效性保持，当前方向不否定)
**Branch**: `formal-ir-mainline`
**HEAD**: `49a415b8253c9c73da0013588d0c50c0e9d41dba` (实际以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准，proposal 冻结时绑定)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点不改；calibration/validation 帧亦同点)
**Lifecycle**: `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN` — 仅 decoder-free 信道估计与验证，不产生 `run_01` decoder 执行，不改 `H1/Lane C/H_inc/Δ/decoder 90/1.0/poly37`
**Method frozen**: `V54二阶段 H1-16(80b)+L1-APP via H1 BP(TRAIN channel_counts.npz)+Lane C m2 184/190/192+H_inc1/2 Δ8+8+decoder 90/1.0 poly37+L2-only tag` 完全冻结（重表征期零改，`m2 184/190/192` 仅作对照，新 `m1/m2/Δ` 仅重算报告不写入码）

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free 重表征脚本 + 2 注册表 + 1 报告；无 runner、无 decoder、无新矩阵、无新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: `numpy` 直算 `1024×1024` 计数/`pandas` 读 `parquet` 已覆盖，无需 `scipy` 或 LDPC 依赖；熵/泄漏公式为确定性算术，不引新库。

> **研究方向保持**：`V54` 在 `2026-01-21` 域 `43/45` (`base18→38 stage1→43 final`) 已证 `V54_DELTA8_ALREADY_SUFFICIENT` 方法有效性；`V55 0/90` 已定位为跨 session 输入域不兼容（非算法证伪），`V56` 诊断已排除 `1024置换/阈网格` 等假说并定位 `pairing/frame` 合同与分布失配信号；`V57` 仅以新 session 实测重估信道与泄漏，不否定既有码族与双阶段救援架构。

## Goal

以最短 decoder-free 路径完成 **新 session 联合信道重表征**，为 `V58` decoder TEST 提供可验证的信道先验与泄漏预算，且满足 **三源独立、四门全过才放行** 的硬门槛：

### 1. 每源互不重叠 calibration/validation 预注册（与 V55 90 及 V56 8帧零重叠，明确 frames）

- **零重叠硬约束**（可机械校验）：
  ```
  set(Cal_s) ∩ set(Val_s) == ∅  per source
  set(Cal_s ∪ Val_s) ∩ set(V55_90×4) == ∅  per source  (V55 authoritative 30/source×4=120 frames/source)
  set(Cal_s ∪ Val_s) ∩ set(V56_fit∪val=[7,8,9,10,15,16,17,18]) == ∅
  frame_id ∈ [0, F_s-1], F=2130/5125/5513, pairs_per_frame 256, 连续无缺失
  ```
  未通过则 `V57_EVIDENCE_INVALID`，不进入信道估计。

- **预注册帧（统一三源，显式冻结）**：
  |  stratum | F | Cal frames (32 frames = 8 blocks×4) | Val frames (32 frames = 8 blocks×4) | Cal pairs | Val pairs |
  |---|---|---|---|---|---|
  | 1M (20260123_1M_600k_0dB) | 2130 | 19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50 | 77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108 | 8192 | 8192 |
  | 1p5M (20260107_PPLN_1p5M) | 5125 | 同上 19..50 | 同上 77..108 | 8192 | 8192 |
  | 2M (20260123_2M_1p2M_0dB) | 5513 | 同上 19..50 | 同上 77..108 | 8192 | 8192 |

  - 选取理由：`19..50` 位于 `V55` 第二块 `73..76` 之前且 `V56` `7..10/15..18` 之后的首个大空隙 `19..72` 内（`54` 帧空隙）的前 `32` 帧；`77..108` 位于第二空隙 `77..145` (`69` 帧) 的前 `32` 帧；两区间均与 `V55` `0..3` 首块、`73..76` 次块零重叠，且 `Cal` 与 `Val` 互不重叠；三源统一便于对照，`frame_id` 均 `< min(F)=2130`。
  - 块语义：`32` 帧 = `8` 连续 blocks×`4` 帧/块 = `8192` pairs/源，满足 `1024×1024` 稀疏估计的最小可报告门限（`~8k` 样本在 `32×32` 分解后 `~8/格`）；若后续需更高精度可由 `V57` successor 扩至 `64` 帧，但本轮冻结为 `32/32`。
  - 注册表：`v57_calibration_registry.json` 与 `v57_validation_registry.json` 分别落盘 `{per_source: {F,K,selected_frame_ids,blocks,provenance,processing_rule, zero_overlap_verified}}`，禁止事后换帧。

### 2. Calibration 估计新 session 联合信道与泄漏重算（不沿用 V25 184/190/192）

- **输入**：每源 `Cal_s` 的 `pairs.parquet` 切片（`alice_symbol/bob_symbol` `0..1023`，`256/frame`，`F03 5+5` 分解 `U1=sym>>5 (0..31), U2=sym&31 (0..31)` `natural`）。
- **估计**（decoder-free，`numpy/pandas` 直算）：
  ```
  C_ab = bincount2d(a,b)  1024×1024  (N_cal=8192)
  N_b = Σ_a C_ab,  P(b)=N_b/N_cal,  N_ab_smooth = C_ab + ε (ε=1e-12 仅为 log 守卫，计数仍报告原始零格数)
  P_hat(a|b) = C_ab / N_b  if N_b>0 else uniform(1/1024)   (列归一，原始计数用于零覆盖统计)
  H(A|B) = - Σ_b P(b) Σ_a P_hat(a|b) log2 P_hat(a|b)   bits/symbol
  P_hat(u1|b) = Σ_{u2} P_hat(32*u1+u2|b),   H(U1|B) = - Σ_b P(b) Σ_{u1} P_hat(u1|b) log2 P_hat(u1|b)
  H(U2|B,U1) = H(A|B) - H(U1|B)   (链式闭合校验 |H-H1-H2|<1e-9)
  H_total = H(A|B), H1 = H(U1|B), H2 = H(U2|B,U1)   per source
  ```
  同时报告 `calibration_NLL_on_self = mean_{Cal}[-log2 P_hat(a|b) clamp 1e-15]` 仅作自洽参考，`zero_cells_cal = #{a,b: C_ab==0}` 与 `zero_cell_frac`。

- **泄漏重算**（`f_target=1.3, n=1024, tag=64 bits, log2q=5`，`source-adaptive` 同 `V27R`）：
  ```
  m_total_required = floor((f_target * n * H_total - tag) / 5)
  m1_required = round(m_total_required * H1 / H_total)  # Python round, half even, frozen rule
  m2_required = m_total_required - m1_required
  Δ = m_total_required - m_total_V25_reported  (V25 m_total 200/206/208 对应 H 0.80/0.80/0.80；仅作差值报告，不改码)
  leak_total = 5*m_total_required + 64,  f_eff = leak_total / (n*H_total)
  per_layer_leak: leak_U1 = 5*m1+ tag?  (tag 仅 L2-only 64b 计入 total，不在层间重复计费；层间仅报告 m1/m2 与 H1/H2)
  ```
  显式声明 **不沿用 `V25` 的 `m2 184/190/192` 与 `m1=16`**，新 `m_total/m1/m2` 仅为 `V58` 预算建议，不在 `V57` 实例化新矩阵；`V57` 仍 `DECODE_FORBIDDEN`。

### 3. Validation 四门独立校验（每源分别，不用总体平均）

对每源 `s∈{1M,1p5M,2M}` 在 `Val_s` 上测：

- **V1 NLL 一致性**：`NLL_val = mean_{Val}[-log2 P_cal(a|b) clamp 1e-15]` bits/symbol（`P_cal` 来自 `Cal` 列归一）。阈：`NLL_val ≤ H_cal + 0.50` 且 `NLL_val ≤ 1.50` 且 `NLL_val < NLL_V25_prior_on_Val`（`NLL_V25` 为同 `Val` 上 `channel_counts.npz TRAIN prior` 的 `NLL`，当前 `22-28` 退化值，需显著回落）。
- **V2 MAP 准确率**：`acc_val = mean_{Val}[a == argmax_{a'} P_cal(a'|b)]`（`1024` 态 `MAP`，`P_cal` 来自 `Cal`）。阈：`acc_val ≥ 0.60` 且 `acc_val ≥ acc_cal - 0.10`（`acc_cal` 为 `Cal` 自测 `MAP`，报告但不以自测为门）。
- **V3 零计数覆盖**：`q_mass_on_p_zero = Σ_{a,b: C_ab_cal==0} P_val_emp(a,b)` 即 `Val` 经验质量落入 `Cal` 未见格的比例；`zero_cells_cal_frac = #{zero}/1M`。阈：`q_mass_on_p_zero ≤ 0.20`（`≤20%`）且 `zero_cells_cal_frac` 如实报告（`8192` 样本下 `~99%` 零格为预期，不硬阈，但 `q_mass` 必过）。
- **V4 熵稳定性**：在 `Val` 上同样本外算 `H_val = H(A|B)_Val`（同公式，仅 `Val` 计数）。阈：`|H_val - H_cal| ≤ 0.20` bits/symbol 且 `|H_val-H_cal|/H_cal ≤ 0.25`。

四门 **per source 均 PASS** 才记该源 `PASS_s=True`；任一门 `FAIL` 则 `PASS_s=False`。

### 4. 三源分别判定，仅全过才 V58（`V57_PASS` 硬门）

```
per_source s: PASS_s = V1_s && V2_s && V3_s && V4_s && zero_overlap_s && calibration_counts_valid
overall:
  if 完整性/零重叠/计数无效 → V57_EVIDENCE_INVALID (最高优先)
  elif not all(PASS_s) → V57_CHANNEL_RECHARACTERIZATION_FAIL (含 MIXED_BY_SOURCE 子态，分源报告)
  else → V57_CHANNEL_RECHARACTERIZATION_PASS
```

仅 `V57_CHANNEL_RECHARACTERIZATION_PASS`（`1M && 1p5M && 2M` 三源均四门通过）才允许另起 `V58` 走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH` 的 `decoder TEST`（`run_01`）；否则停留 `V57_CHANNEL_RECHARACTERIZATION_PENDING` 修 `Cal/Val` 划分或扩样本，不进入 `decoder`。

### 5. 不改码参、不运行 decoder（`DECODE_FORBIDDEN` 冻结）

- `H1 16×1024 rank16 80b (V31-H1-QC poly37) / Lane C m2 184/190/192 ordinal-2 / H_inc1/2 8×1024 det1/det2 / H_joint1 192/198/200 / H_total 200/206/208 / decoder 90/1.0 early-stop / L2-only tag 64b / TRAIN-only prior` **全部零改**，`rg "decode_" 0 hits`，`py_compile` 必过；
- 不创建 `.../v57_*/run_01` decoder 执行；`V58` 新 `m1/m2` 矩阵与 `decoder TEST` 需另起 `OpenSpec` 与独立授权；
- `V55` 原 `90-block` 永久禁用（已揭盲 `0/90`），不在其上重跑任何 `corrected pipeline`。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用，`rg "decode_" 0 hits`）；不改 `H1-16/Lane C/H_inc1/2/Δ8+8/m2/leak/tag/prior/decoder 90/1.0 poly37` 任一冻结量；不试新 `Δm/degree/seed`，不新增矩阵。
- 不在原 `V55` authoritative `90-block` (`v55_authoritative_registry.json` 30/source) 上重跑任何 `corrected pipeline / offset-corrected` 重译；不将 `Cal/Val` 择优值回注为新 pipeline。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（`200ps legacy_v1 nearest 1024` 单点锚点）；`Cal` 估计仅单点 `32/32` 帧，不择优。
- 不宣称 `LDPC` 证伪 / `FER` / 阈值 / `SKR` / 晋升；`V57` 止于 `CHANNEL_RECHARACTERIZATION_PENDING` 的信道重表征，不直接进入 qualification。
- 不创建正式 `.../v57_*/run_01` decoder 执行；`V58` decoder TEST 需另起 `OpenSpec` 与独立 `EXECUTE_AUTH`。
- 不改写/覆盖 `V38–V56` 任何已有输出与终态（只读）；本轮不直接修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅预留 `V57` 条目占位）。
- 不以总体平均替代三源分别判定；不以 `V25` `H` 或 `184/190/192` 作为新域预算。

## Scope

1. **冻结方法零改**：`n=1024, m2 184/190/192 (对照), GF32 poly37, H1 16×1024 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz, 仅对照), Lane C ordinal-2, H_inc1/2 Δ8+8 (冻结对照), decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior (V57 不改 prior，仅重估 H 供 V58)` 全只读，**零 decoder**。
2. **预注册 Cal/Val（零重叠，可机械校验）**：每源 `Cal 19..50 (32 frames, 8 blocks×4) + Val 77..108 (32, 8×4)`，`pairs_per_frame 256`, `frame_id∈[0,F-1]`, `8192/8192` pairs/源，三源统一，`F=2130/5125/5513` 范围内，`assert set(Cal)∩set(Val)==∅ && set(Cal∪Val)∩set(V55 90×4)==∅ && ∩set([7,8,9,10,15,16,17,18])==∅`，落盘 `v57_calibration_registry.json / v57_validation_registry.json + v57_manifest.json`。
3. **Calibration 信道估计（decoder-free）**：每源 `Cal` 上算 `C_ab 1024×1024 → P_hat(a|b) 列归一 → H(A|B), H(U1|B), H(U2|B,U1) (F03 5+5 natural, U1=>>5, U2=&31, 链式闭合 |H-H1-H2|<1e-9) → m_total/m1/m2/f_eff/leak_total (f_target1.3, n1024, tag64, log2q5, m1=round)`，**不沿用 `V25 184/190/192`**，新 `m` 仅报告。
4. **Validation 四门（decoder-free，三源分别）**：每源 `Val` 上 `NLL_val (mean -log2 P_cal)`、`acc_val (MAP)`、`q_mass_on_p_zero (Val mass 落 Cal零格)`、`H_val vs H_cal` 稳定性，四阈预注册（`V1 NLL≤H+0.5 & ≤1.5 & <V25 NLL`；`V2 acc≥60%`；`V3 q_mass≤20%`；`V4 |H_val-H_cal|≤0.20 & ≤25%`），**三源分别判定，不用总体平均**。
5. **三源判定与 V58 门**：`per_source PASS_s = V1&&V2&&V3&&V4 && zero_overlap && counts_valid`；`overall PASS = all PASS_s` → `V57_CHANNEL_RECHARACTERIZATION_PASS` 才允许 `V58`；否则 `FAIL` (`MIXED_BY_SOURCE` 子态分源报告) 或 `EVIDENCE_INVALID`；不以单源或平均放行。
6. **脚本与报告交付（DECODE_FORBIDDEN）**：`v57_channel_recharacterization.py` (decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`) 输出 `v57_channel_recharacterization.json` (`per_source {H,H1,H2,NLL,acc,q_mass,zero_frac,m_total,m1,m2,f_eff, Δ, gate_pass} + overall`) 与 `V57_CHANNEL_RECHARACTERIZATION_REPORT.md`；**未创建 `run_01`，已推送新 SHA 并停留 `PENDING/DECODE_FORBIDDEN`，等待独立审核后才允 `V58`**。

## Impact Scope

- **新增/修订（本变更）**：`openspec/changes/formal-ir-v57-channel-recharacterization/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 1 decoder-free 脚本 `v57_channel_recharacterization.py` (本变更目录下, `rg "decode_" 0 hits`) + 2 注册表 `v57_calibration_registry.json / v57_validation_registry.json` (pre-registered frames) + `v57_channel_recharacterization.json` + `V57_CHANNEL_RECHARACTERIZATION_REPORT.md` + `v57_manifest.json` (provenance, HEAD/data SHA, zero_overlap 证明)。
- **只读依赖**：`v55_authoritative_registry.json (V55 90×4 frames)` + `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*.parquet` (`alice_symbol/bob_symbol` 1024) + `workspace/v13r3fresh_20260816/sidecars` (仅对照) + `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` (`V25 TRAIN prior` 仅作 `NLL_V25` 对照，不训) + `nonbinary_v25_gate.py` (`P(A|B)/熵定义` 仅参考) + `v38_architecture_triage.py` (Lane C 常量仅背景)。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录外）、`V38–V56` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01` decoder 执行，零码参**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`，`HEAD 49a415b` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 `H1/Lane C/Δ8/decoder`、**三源分别判定**、仅全过才 `V58`。
- [ ] **预注册零重叠可复现**：每源 `Cal 19..50 (32) + Val 77..108 (32)` 已 `assert` 三重零重叠（`Cal∩Val==∅`, `Cal∪Val ∩ V55 90×4==∅`, `∩ V56 [7,8,9,10,15,16,17,18]==∅`），`frame_id∈[0,F-1]`、`pairs_per_frame 256`、`Cal/Val 8192/8192` pairs/源，注册表已落盘，三源统一。
- [ ] **Calibration 估计可复现**：每源 `Cal` 上 `C_ab 1024×1024 → P_hat(a|b) 列归一 → H(A|B), H(U1|B), H(U2|B,U1) (F03 5+5, U1=>>5 &31, 链式 |H-H1-H2|<1e-9)` 已算，`H/H1/H2` 与 `V25` 差值、`zero_cells/q_mass` 已报告，**不沿用 `V25 184/190/192`**，新 `m_total/m1/m2/f_eff/leak` (`f_target1.3, n1024, tag64, log2q5, m1=round`) 已重算且与 `json` 一致。
- [ ] **Validation 四门可复现**：每源 `Val` 上 `NLL_val (mean -log2 P_cal)`、`acc_val (MAP)`, `q_mass_on_p_zero (Val mass→Cal零格)`, `H_val` 稳定性已算，四阈（`V1 NLL≤H+0.5 & ≤1.5 & <V25 NLL`; `V2 acc≥60%`; `V3 q_mass≤20%`; `V4 |H_val-H_cal|≤0.20 & ≤25%`）已逐源判定，**三源分别，不用总体平均**，`per_source PASS_s` 已落盘。
- [ ] **三源独立判定可复现**：`overall = V57_CHANNEL_RECHARACTERIZATION_PASS` 当且仅当 `1M && 1p5M && 2M` 均 `PASS_s`，否则 `FAIL` (含 `MIXED_BY_SOURCE` 分源清单) 或 `EVIDENCE_INVALID`，**仅全过才允许 `V58`** 已声明。
- [ ] `v57_channel_recharacterization.py` 为 decoder-free 可运行脚本（`python v57_channel_recharacterization.py [--pairs-root ...] [--counts ...] [--out ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v57_channel_recharacterization.json` 与控制台摘要，**未创建 `run_01`**。
- [ ] `V57_CHANNEL_RECHARACTERIZATION_REPORT.md` 已记录每源 `H/H1/H2/NLL/acc/q_mass/zero_frac/m_total/m1/m2/f_eff/Δ`、四门明细与总体终态，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V55 90 已揭盲不可复用` + `V25 184/190/192 已废弃不沿用` + `仅全过才 V58`。
- [ ] 已推送新 `SHA` 并停留在 `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`，未创建任何 `.../v57_*/run_01` decoder 执行，不碰 `V55 90` 块，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`）。

## Tasks

见 `tasks.md`（Phase A 预注册 Cal/Val 零重叠；Phase B Calibration 联合计与 H/m 重算；Phase C Validation 四门；Phase D 三源独立总体判定与 V58 门；Phase E 脚本与报告交付至 `PENDING/DECODE_FORBIDDEN`；显式禁止清单与 decoder-free 守卫）。

## Lifecycle

`V56` 当前 `DIAGNOSIS_RESULT_ACCEPTED`（`HEAD 49a415b`, `V56_INPUT_CONTRACT_RECONSTRUCTION` 已固化校准验证与 5 选 1，`V54 43/45` 方法有效性保持，域不兼容已定位）；`V57` 本重表征 `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`（仅 decoder-free 信道估计与验证，不实现 runner，不执行 decoder，不创建 `run_01`，不改码参，三源分别四门）；`V57_PASS`（三源均四门通过）后**另起 successor `V58`** 冻全新 `TEST` blocks（与 `Cal/Val` 及 `V55 90` 零重叠，未揭盲）再走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH` 的 `decoder TEST`，`V57` 本身不直接进入 qualification；`V57_FAIL/INVALID` 则停留修划分或扩样本，不进入 `V58`。
