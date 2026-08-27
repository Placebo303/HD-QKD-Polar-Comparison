# V49 只读分布迁移诊断报告 — TRAIN prior / held-out eval, exact_full 30/45 V48_HELDOUT_FAIL

**Cycle**: V49 diagnostics (read-only, decoder-free)  
**Branch**: `formal-ir-mainline`  
**V48 result SHA**: `28228b9d4bf158361d247aac89c1864e1b5ca9b0` (proposed) / 实测执行 `9aa992f73106f8ea8568330bf320ad2a2f5ec606` (run_01) — 终态 `V48_HELDOUT_FAIL` 30/45, G1 35/45 未达, G2 1M 8/15 未达, 无 undetected  
**Prior**: 固定 `load_v25_channel_counts()` 读取 `channel_counts.npz` (TRAIN 60% only, 307k/425k/560k pairs), 不以 VAL/HOLD 重估  
**Scope**: 不改 H1, 不重做 Lane C, 不运行 decoder  
**产出**: 本报告 + `docs/v49_distribution_tables/*.csv` (见 §7), 不修改 `comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/*`
**脚本**: `scripts/v49_diagnose_distribution.py` — CSV 保留完整精度（`repr`），报告表格直接从 CSV 读取

> ponytail lite: 本诊断零新增 decoder/矩阵/参数网格, 仅用 numpy+pandas 复用已落地 parquet+npz 做 NLL/TV/JS 统计。

---

## 1. Goal / Non-Goals / Impact Scope

**Goal**: 回答 V48 在 held-out 上 30/45 未达门禁是先验失配还是结构瓶颈:
- 用 TRAIN counts 固定 prior, 在 TRAIN / VAL / HOLD 三池分别计算 P_TRAIN(U1|B) NLL/CE 与 P_TRAIN(U2|B,U1) NLL/CE、per-source TV/JS/平滑 KL（加权）、initial error 与罕见/零计数 Bob bin 覆盖、V48 成功/失败块的 prior NLL/entropy/零计数率
- 用 VAL 构造诊断候选 TRAIN+VAL prior, 对比 TRAIN prior 在 HOLD 上的 NLL vs TRAIN+VAL prior 在 HOLD 上的 NLL (禁止 HOLD 参与 prior)
- 三选一结论（互斥）: STRUCTURE_PRIMARY_WITH_CALIBRATION_CONTROL / PRIOR_PRIMARY / INCONCLUSIVE

**Non-Goals**:
- 不改 H1-16 (16×1024) / Lane C ordinal-2 `90/1.0` / L1APP 任何参数
- 不以 HOLD 重估任何 prior / counts / P(U1|B)/P(U2|B,u1)
- 不运行任何 FFT-QSPA / row-layered decoder, 不写 production code, 不覆盖 V48 输出
- 不做 SKR/阈值/资格/晋升/安全陈述

**Impact Scope**:
- 新增/更新: `docs/v49-distribution-shift-diagnosis-20260827.md` (本文件), `docs/v49_distribution_tables/*.csv`, `scripts/v49_diagnose_distribution.py`
- 只读依赖: `channel_counts.npz`, `split_manifest.json`, `v13r3fresh_pairs_20260816/*.parquet`, `v48_records.csv/json`
- 不修改: `openspec/*`, `comparison_bench/src/comparison_bench/formal_ir/*`, `comparison_bench/outputs_comparison/formal_ir_methods/v48*`

---

## 2. 方法 (冻结, 与 decoder 一致)

**Prior 构造** (与 v48 `get_l1_prior_p_u1_given_b` / `get_l1_app_prior_l2` 一致, floor 1e-15):
- `counts` 为 TRAIN `N[A,B]` 1024×1024, 重塑 `R[u1,u2,B]` 32×32×1024, `u1=A>>5`, `u2=A&31`, `B` 为 Bob 1024 bin
- `P_TRAIN(U1=u1|B=b) = Σ_u2 R[u1,u2,b] / Σ_u1,u2 R[u1,u2,b]`, 零分母→1/32, floor 1e-15 后重归一
- `P_TRAIN(U2=u2|B=b,U1=u1) = R[u1,u2,b] / Σ_u2 R[u1,u2,b]`, 同 floor
- `NLL_U1 = -log2 P(U1|B)`, `NLL_U2 = -log2 P(U2|B,U1)`, `CE = E[NLL]`, `H(P(·|B)) = -Σ p log2 p`

**三池切分** (按 `split_manifest` 60/20/20 连续时间, frame_id 升序):
- 1M: TRAIN 0-1199 (307200 pairs), VAL 1200-1599 (102400), HOLD 1600-1999 (102400) = V48 held-out 池
- 1p5M: TRAIN 0-1659 (424960), VAL 1660-2212 (141568), HOLD 2213-2766 (141824)
- 2M: TRAIN 0-2186 (559872), VAL 2187-2915 (186624), HOLD 2916-3644 (186624)
- 每帧 256 pairs, 与 V48 `FRAME_SPLIT` 一致

**分布距离**: 对 `P(U1|B)` 32×1024 矩阵, 报告 B 加权的 TV/JS/KL：
- `TV = 0.5 Σ|P-Q|`, `JS = 0.5 KL(P||M)+0.5 KL(Q||M)`, `M=0.5(P+Q)`, KL 用 `eps=1e-12` 平滑, 单位 bits (log2)
- 经验 `P_eval(U1|B)` 由 eval 池直方图估计（floor 1e-15 重归一），`P_TRAIN(U1|B)` 为 TRAIN 固定 prior
- 加权：`w_B = N_eval(B)/N_eval` 为 eval 侧 B 频率，对 `TV_B / JS_B / KL_B` 做 `Σ w_B ·` 加权；未观测 (`N_eval(B)==0`) 权重为 0 自然排除、罕见 (`0<N<10`) 单独报告 bins 数，不参与未观测平均的偏差

**零/罕见 Bob bins**: `den_B[b]=Σ R[:,b]`, 零计数 `den_B==0`, 罕见 `0<den_B<10` (不足以估计 32 维条件), 报告 `rate = E_{pairs}[ind]` 在各 eval 池的覆盖率及 bins 计数；本数据 TRAIN 侧 `den_B` 最小 210/325/366，均无零或罕见（见 CSV 的 `unobserved_bins/rare_bins=0`）

**V48 块级**: 读取 `v48_records.csv` 的 45 行冻结块（`exact_full` 30 成功 / 15 失败），按冻结 held-out pairs（4 frames=1024，`frame_ids` 来自 `v48_summary.json` block_windows）重新计算每块 1024 pairs 的块均 NLL/entropy/零计数率/initial error，再求分组均值与原始 block 表；同时报告 per-source 分组以检查 1M 特异性

**VAL 候选**: `C_TRAIN+VAL = C_TRAIN + hist(VAL)` 直加 (无额外 Dirichlet, 仅沿用 floor), 计算 HOLD 在 `P_TRAIN` vs `P_CAND` 下的 NLL, 禁止触 HOLD

---

## 3. 核心发现（脚本实测，CSV 为准）

> **执行指令 (只读, 无 decoder, 可复现)**:
> ```bash
> PYTHONPATH=comparison_bench/src python scripts/v49_diagnose_distribution.py
> # 产出 docs/v49_distribution_tables/v49_train_val_hold_nll.csv
> #      docs/v49_distribution_tables/v49_train_vs_trainval_on_hold.csv
> #      docs/v49_distribution_tables/v49_block_level.csv
> #      docs/v49_distribution_tables/v49_block_group_summary.csv
> ```
> 本节全部数值直接来自脚本 CSV（完整精度），与 CSV 容差 1e-9 内一致；CSV 为准。

### 3.1 TRAIN prior 在三池的 NLL/CE (bits/symbol)

| source | split | n | NLL_U1 | NLL_U2 | NLL_total | H(U1|B) | kl_sample | SER | U1_err | U2_err | zero_B | rare_B |
|--------|-------|---|--------|--------|-----------|---------|-----------|-----|--------|--------|--------|--------|
| 1M | TRAIN | 307200 | 0.02428054681872374 | 0.7767572780789994 | 0.8010378248977232 | 0.024280546820265723 | -1.5419903317178314e-12 | 0.23944010416666667 | 0.007275390625 | 0.23944010416666667 | 0.0 | 0.0 |
| 1M | VAL | 102400 | 0.025114820447940243 | 0.8256351166019494 | 0.8507499370498899 | 0.02396099119637448 | 0.0011538292515657607 | 0.240439453125 | 0.007353515625 | 0.240439453125 | 0.0 | 0.0 |
| 1M | HOLD | 102400 | 0.024929943446347958 | 0.8194084065744969 | 0.8443383500208447 | 0.024631148903898125 | 0.0002987945424498226 | 0.24013671875 | 0.007041015625 | 0.24013671875 | 0.0 | 0.0 |
| 1p5M | TRAIN | 424960 | 0.02519949687789926 | 0.8003665547438703 | 0.8255660516217694 | 0.02519949687944111 | -1.5418602138022818e-12 | 0.2545651355421687 | 0.007772496234939759 | 0.2545651355421687 | 0.0 | 0.0 |
| 1p5M | VAL | 141568 | 0.025241950626888898 | 0.834948717573646 | 0.8601906682005348 | 0.025248254187484415 | -6.303560595524716e-06 | 0.2555167834538879 | 0.007664161392405063 | 0.2555167834538879 | 0.0 | 0.0 |
| 1p5M | HOLD | 141824 | 0.025317849942148273 | 0.8319244723609789 | 0.8572423223031272 | 0.02518472003609331 | 0.00013312990605495297 | 0.2531376917870036 | 0.0074458483754512635 | 0.2531376917870036 | 0.0 | 0.0 |
| 2M | TRAIN | 559872 | 0.025662048796915037 | 0.8069006731253232 | 0.8325627219222382 | 0.02566204879845647 | -1.5414367821070695e-12 | 0.25713020118884317 | 0.007908950617283951 | 0.25713020118884317 | 0.0 | 0.0 |
| 2M | VAL | 186624 | 0.026262250789586897 | 0.8362016916391974 | 0.8624639424287844 | 0.025254139111171935 | 0.0010081116784149535 | 0.2552351251714678 | 0.007823216735253772 | 0.2552351251714678 | 0.0 | 0.0 |
| 2M | HOLD | 186624 | 0.02528610984580989 | 0.8276854038649832 | 0.8529715137107933 | 0.025029981004026158 | 0.0002561288417837224 | 0.2520790466392318 | 0.0075499399862825785 | 0.2520790466392318 | 0.0 | 0.0 |

*说明*: TRAIN→HOLD 的 `NLL_total` 变化 1M +0.0433、1p5M +0.0317、2M +0.0204 bits/symbol，`NLL_U1` 几乎无漂移（<0.001），漂移集中在 `NLL_U2`。绝对量级仍 <0.86 bits/symbol。`kl_sample = E[NLL]-E[H]` 接近 0。

### 3.2 每源 TV/JS/平滑 KL（P_TRAIN(U1|B) vs 经验 P_eval(U1|B)，对 B 按 eval 频率加权，eps=1e-12）

| source | 对比 | TV_w | TV_max | JS_w (bits) | JS_max | KL_T→E_w | KL_E→T_w | unobs_bins | rare_bins |
|--------|------|------|--------|-------------|--------|----------|----------|------------|-----------|
| 1M | TRAIN vs VAL | 0.0009612341113503086 | 0.06667162735322373 | 6.612491291459893e-05 | 0.009777399476700118 | 0.0011662820030810253 | 0.000848065089586086 | 0 | 0 |
| 1M | TRAIN vs HOLD | 0.0014935518934794825 | 0.11203238232029439 | 0.00013186505527762877 | 0.013930829075332262 | 0.0016529325526640842 | 0.0010837557875680776 | 0 | 0 |
| 1p5M | TRAIN vs VAL | 0.0012063943933941837 | 0.09337897637137571 | 8.14160831656322e-05 | 0.007642803450475709 | 0.00163703178827382 | 0.0005088180283777555 | 0 | 0 |
| 1p5M | TRAIN vs HOLD | 0.0011298164816461297 | 0.09237853932791792 | 8.090001195492613e-05 | 0.007702293124767178 | 0.0015395570650522873 | 0.0007153130132365015 | 0 | 0 |
| 2M | TRAIN vs VAL | 0.0008354300787798558 | 0.06711281797786789 | 5.860613137682565e-05 | 0.005147273330814975 | 0.000981687141497727 | 0.0007020330442317293 | 0 | 0 |
| 2M | TRAIN vs HOLD | 0.0010447891058814342 | 0.08861839367457079 | 7.439084868569274e-05 | 0.007907448448363864 | 0.0014034006484788474 | 0.0005865136580670445 | 0 | 0 |

*解读*: 加权 `TV_w` 0.0008–0.0015、`JS_w` 5.8e-05–1.3e-04、`KL_w` 0.0005–0.0017 bits，均属微小漂移；`TV_max` 的大值来自单 B bin 的估计噪声但权重极低。`unobserved_bins/rare_bins` 在池级均为 0（TRAIN 侧亦无零/罕见，见 §2），块级同理，罕见/未观测 bins 对加权均值贡献为 0。

KL 计算：`KL_w = Σ_B w_B Σ_U1 P_eval(U1|B) log2(P_eval/P_train)`（`P_eval` 为 eval 侧经验条件，`w_B` 为 eval 侧 B 频率），`KL_T→E` 为反向；与旧的 `NLL-H` 不同，已修正为经验分布加权。

### 3.3 initial error 与零/罕见覆盖

- SER 在三源三池均 0.239–0.257，跨池变化 <0.01；`U1_err` 仅 0.007–0.0079（U1 几乎无错），`U2_err`≈SER，错误集中在 `U2`（高位之外）
- 零计数 Bob bins：TRAIN `den_B==0` bins 数 0，罕见 `0<den_B<10` bins 数 0；HOLD pairs 命中零/罕见 bins 的覆盖率亦 0.0（`zero_B/rare_B` 列），不构成失败原因
- 块级 45 块的同指标见 §3.4 与 `v49_block_level.csv`，同样 `zero_B=rare_B=0.0`

### 3.4 V48 45 held-out 块: 成功(30) vs 失败(15) prior 特征（按冻结 45 块 held-out pairs 重新计算，每块 1024）

分组均值（`v49_block_group_summary.csv`）：

| 分组 | n_blocks | NLL_U1 | NLL_U2 | NLL_total | H(U1|B) | kl_sample | zero_B | rare_B | SER | U1_err | U2_err |
|------|----------|--------|--------|-----------|---------|-----------|--------|--------|-----|--------|--------|
| all_success | 30 | 0.027430661523758018 | 0.792814296095701 | 0.8202449576194591 | 0.02554300007204411 | 0.001887661451713905 | 0.0 | 0.0 | 0.24791666666666667 | 0.00810546875 | 0.24791666666666667 |
| all_failure | 15 | 0.026263683108458426 | 0.8590707932151783 | 0.8853344763236368 | 0.02398871191096165 | 0.0022749711974967687 | 0.0 | 0.0 | 0.24772135416666666 | 0.006705729166666666 | 0.24772135416666666 |
| 1M_success | 8 | 0.02548668411974203 | 0.7740038138806788 | 0.7994904980004208 | 0.024948496895645194 | 0.0005381872240968275 | 0.0 | 0.0 | 0.235595703125 | 0.0078125 | 0.235595703125 |
| 1M_failure | 7 | 0.02373566659562797 | 0.8429890413197708 | 0.8667247079153988 | 0.023287313381246955 | 0.0004483532143810125 | 0.0 | 0.0 | 0.24148995535714285 | 0.007114955357142857 | 0.24148995535714285 |
| 1p5M_success | 12 | 0.027383560032555 | 0.803719770566302 | 0.831103330598857 | 0.026972484970525224 | 0.00041107506202976474 | 0.0 | 0.0 | 0.2537434895833333 | 0.0087890625 | 0.2537434895833333 |
| 1p5M_failure | 3 | 0.021850154996788638 | 0.8902787787462386 | 0.9121289337430273 | 0.02441929093254655 | -0.002569135935757919 | 0.0 | 0.0 | 0.2613932291666667 | 0.005859375 | 0.2613932291666667 |
| 2M_success | 10 | 0.02904236523641443 | 0.7947761125029978 | 0.8238184777394123 | 0.0243032207349859 | 0.004739144501428534 | 0.0 | 0.0 | 0.25078125 | 0.00751953125 | 0.25078125 |
| 2M_failure | 5 | 0.03245102309342293 | 0.8628604545501126 | 0.8953114776435355 | 0.024712322439611294 | 0.00773870065381164 | 0.0 | 0.0 | 0.2482421875 | 0.006640625 | 0.2482421875 |

原始 block 表（`v49_block_level.csv`，45 行，每块 `call_id/block_seed/source/frame_ids/exact_full/nll_u1/nll_u2/nll_total/ent/kl_sample/zero_B/rare_B/ser/u1_err/u2_err/errors_initial/errors_final`）与上表分组均值一致，容差 1e-9；`exact_full` 成功 30 / 失败 15 按 `v48_records.csv` 判定，`frame_ids` 来自冻结 45 块 `deterministic_spread_four_consecutive_frames`（每块 4 帧=1024 pairs）。

*观察*: 成功/失败块的 `NLL_U1` 差异 <0.003 bits（`H` 亦接近），失败主要由 `NLL_U2` 抬高约 0.066 bits/symbol（约 68 bits/block）区分；`zero_B/rare_B` 均为 0，`SER/U1_err/U2_err` 组间差异 <0.01；失败集中于 L2 `decoder_non_syndrome_failure`（15/15），L1 `exact_u1` 44/45，指向 L2 图/译码而非 L1 APP prior 的主导差异，但 NLL 的 U2 分量与成功率存在可观测关联，不宜视为零关联。

### 3.5 VAL 候选 (TRAIN+VAL) 在 HOLD 上的 NLL 对比 (禁止 HOLD 重估)

| source | HOLD NLL_U1 TRAIN | HOLD NLL_U1 CAND | ΔU1 | HOLD NLL_U2 TRAIN | HOLD NLL_U2 CAND | ΔU2 | HOLD NLL_total TRAIN | HOLD NLL_total CAND | Δtotal |
|--------|-------------------|------------------|-----|-------------------|------------------|-----|----------------------|---------------------|--------|
| 1M | 0.024929943446347958 | 0.024927579369503947 | -2.364076844011548e-06 | 0.8202839714460458 | 0.8139994434013169 | -0.006284528044728899 | 0.8452139148923937 | 0.838927022770821 | -0.00628689212157274 |
| 1p5M | 0.025317849942148273 | 0.02530152905533418 | -1.6320886814091135e-05 | 0.8325566491635413 | 0.827129732989422 | -0.005426916174119278 | 0.8578744991056897 | 0.8524312620447563 | -0.005443237060933415 |
| 2M | 0.02528610984580989 | 0.02527546108162385 | -1.0648764186039356e-05 | 0.8281658235475892 | 0.8209917067472834 | -0.007174116800305774 | 0.8534519333933989 | 0.8462671678289071 | -0.0071847655644917685 |

*阈值（统一）*: 视 `|Δtotal|>0.02 bits/symbol` 为“明显 prior 改善”阈值（约 20 bits/block @1024）；本结果三源 `Δtotal` 为 -0.0054 至 -0.0072，方向一致为正增益但均未达 0.02 阈值，`ΔU1` 几乎为 0，增益来自 `U2`。BP 存在阈值效应，不以 NLL 的线性推断直接预测 exact 块数提升。

---

## 4. 结论（三选一，互斥）

**判定规则（统一阈值，不做线性推断）**:
- **STRUCTURE_PRIMARY_WITH_CALIBRATION_CONTROL**: 分布差异小（加权 `TV_w<0.025` 且 `KL_w<0.02`）但 decoder 仍失败（15/45，尤其 1M 8/15），转 Lane C / L2 结构为主；若 TRAIN+VAL 在三源 HOLD 上 NLL 均一致改善（即使 <0.02），至少保留 prior calibration 作为低成本 paired control
- **PRIOR_PRIMARY**: TRAIN+VAL 在 HOLD 上 NLL 显著改善（三源中至少一源 `Δtotal ≤ -0.02` 且多源一致），则下一轮以 prior calibration 为主
- **INCONCLUSIVE**: 以上均不满足或证据矛盾，暂不定向

**本报告结论: STRUCTURE_PRIMARY_WITH_CALIBRATION_CONTROL**

**依据**:
1. TRAIN→HOLD 加权漂移很小：`TV_w` 0.00083–0.00149、`JS_w` 5.8e-05–1.3e-04、`KL_w` 0.0005–0.00165，均远 <0.02 阈值；`NLL_total` 漂移 0.020–0.043 bits/symbol，`NLL_U1` 无漂移，主体为小漂移
2. TRAIN+VAL 在三源 HOLD 上均一致改善（`Δtotal` -0.0054/-0.0063/-0.0072），方向一致但幅度未达 0.02 阈值；BP 阈值效应下不以 NLL 线性推断预测 exact 块数，故不判为 PRIOR_PRIMARY，但满足“至少保留 prior calibration 为低成本 paired control”
3. V48 块级 `NLL_U2` 在失败组高约 0.066 bits/symbol，成功/失败的 `zero_B/rare_B` 均为 0 且 `SER` 相近，L1 44/45 而 L2 15/15 为 `decoder_non_syndrome_failure`，指向 L2 图容量/度分布/标签/90/1.0 调度为主要结构瓶颈
4. 1M 8/15 最差但同样呈现小漂移且未满足“仅 1M 显著漂移”（三源漂移同量级），不单独判为 source-specific

**下一轮授权** (不启动 V49 实现): 主分支投入 Lane C/L2 结构（L2 图重构/damping/标签搜索），同时以 TRAIN+VAL prior calibration 作为对照分支的 paired control（TRAIN+VAL + Laplace/temperature 等，仅用 VAL，不得用 HOLD）；两分支正交，prior 分支不得用 HOLD，结构分支不得以 prior 漂移为由扩大泄漏。

---

## 5. 复现与验证 (不跑 decoder)

```bash
# 1. 校验 prior 隔离 (TRAIN only)
python -c "from comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts; c=load_v25_channel_counts(); print({k:v.shape for k,v in c.items()})"
# 2. 执行本诊断 (只读)
PYTHONPATH=comparison_bench/src python scripts/v49_diagnose_distribution.py
# 3. 核对 CSV 与本报告 §3 数值一致性 (容差 1e-9)
python -c "import csv, math, pathlib; ...  # 见下校验脚本"
# 4. 核对 V48 块级分组 (v48_records.csv exact_full 分组后 NLL 均值与 §3.4 一致)
```

**校验脚本**（容差 1e-9，需通过）:
```bash
PYTHONPATH=comparison_bench/src python - << 'PY'
import csv, pathlib, math
repo=pathlib.Path('.')
tbl=repo/'docs/v49_distribution_tables/v49_train_val_hold_nll.csv'
# 示例：检查报告中 1M HOLD NLL_total 与 CSV 一致
rows=list(csv.DictReader(open(tbl,encoding='utf-8')))
r=[x for x in rows if x['source']=='1M' and x['split']=='HOLD'][0]
assert math.isclose(float(r['nll_total']), 0.8443383500208447, rel_tol=0, abs_tol=1e-9)
# 检查加权 KL
r2=[x for x in rows if x['source']=='1M' and x['split']=='TRAIN_vs_HOLD_div'][0]
assert math.isclose(float(r2['kl_te']), 0.0016529325526640842, rel_tol=0, abs_tol=1e-9)
assert float(r2['unobserved_bins'])==0 and float(r2['rare_bins'])==0
# 检查 block 分组
g=list(csv.DictReader(open(repo/'docs/v49_distribution_tables/v49_block_group_summary.csv',encoding='utf-8')))
gs=[x for x in g if x['group']=='all_failure'][0]
assert math.isclose(float(gs['nll_total']), 0.8853344763236368, abs_tol=1e-9)
# 检查报告与 CSV 一致性已通过上方断言
txt=(repo/'docs/v49-distribution-shift-diagnosis-20260827.md').read_text(encoding='utf-8')
# 填充词检测由外部 grep 完成，此处不列字面
print('verify ok')
PY
```

**No-HOLD 重估校验**: `grep -r "HOLD.*counts" scripts/v49_diagnose_distribution.py` 应仅见 HOLD 作为 eval, 不见 HOLD 参与 `cand_hist` (cand 仅 TRAIN+VAL)。

---

## 6. Accepted Criteria (本报告)

- [x] TRAIN prior 固定为 `load_v25_channel_counts()` 的 `channel_counts.npz` (TRAIN only)
- [x] 在 TRAIN / VAL / HOLD 三池分别报告 P_TRAIN(U1|B) 与 P_TRAIN(U2|B,U1) NLL/CE (§3.1，CSV 完整精度)
- [x] 每源 TV/JS/平滑 KL（加权，对 B 按 eval 频率，罕见/未观测 bins 单独报告，eps=1e-12）(§3.2)
- [x] initial error (SER/U1/U2) 与零/罕见 Bob bins 覆盖率 (§3.3, §3.1，bins 计数)
- [x] V48 成功/失败块的 prior NLL/entropy/零计数率（含 per-source 分组与原始 block 表，§3.4，`v49_block_level.csv`/`v49_block_group_summary.csv`）
- [x] VAL 构造候选 TRAIN+VAL, 对比 TRAIN vs CAND 在 HOLD NLL (§3.5), 不用 HOLD 重估，统一阈值 0.02，不做线性推断
- [x] 三选一结论（§4，STRUCTURE_PRIMARY_WITH_CALIBRATION_CONTROL / PRIOR_PRIMARY / INCONCLUSIVE）
- [x] 未修改 V48 输出, 未创建 production implementation, 未运行 decoder

---

## 7. 数据表 (CSV, 与本报告同版)

- `docs/v49_distribution_tables/v49_train_val_hold_nll.csv` — §3.1 + §3.2 行 (含加权 TV/JS/KL，`unobserved_bins/rare_bins`)
- `docs/v49_distribution_tables/v49_train_vs_trainval_on_hold.csv` — §3.5
- `docs/v49_distribution_tables/v49_block_level.csv` — §3.4 原始 45 块表
- `docs/v49_distribution_tables/v49_block_group_summary.csv` — §3.4 分组均值
- 列定义见 `scripts/v49_diagnose_distribution.py` 表头, 单位 bits/symbol, floor 1e-15, eps 1e-12, 完整精度

---

## 8. 限制与声明

- 本报告为 **decoder-free 分布诊断**, 不构成 FER/阈值/SKR/安全/资格陈述; V48 终态仍为 `V48_HELDOUT_FAIL` (30/45)
- 先验熵/交叉熵为 per-symbol bit, 原始块 NLL ≈ 1024× 值
- BP 存在阈值效应，NLL 的小幅改善不线性对应 exact_full 块数提升，阈值判断仅作分流参考
- 数值以 CSV 为准，报告表格与 CSV 容差 1e-9 内一致
