# Decision Log

本文件记录对基线科学口径有影响的调查结论与决定。新增条目时按时间倒序排列，并引用当时的具体文件与行号（行号随重构可能漂移，以内容为准）。

---

## 2026-08-14：码率搜索修复（分支 `codex/fix/rate-search-leak`）——已实现并验证

### 背景

条目 #2 定位到低维 leak 高的两大策略来源：(1) 码率离容量 gap 0.14–0.20 bits/bit/层；(2) 负净收益层未丢弃。本条目处理 (1) 的第一阶段：**修码率搜索**。

### 代码改动（`experiments/run_real_polar_max_pie.py`，分支 `codex/fix/rate-search-leak`，未提交）

1. `_N_FRAMES` 100 → **300**（Wilson 95% 单侧 < 0.05 下允许错误数 1 → 8，接受真实 FER ≤ ~0.03–0.04 的码率，原规则只允许 ≤ ~0.01）。
2. 候选阶梯由 `{1.0,0.95,0.90,0.85,0.80,0.70,0.60,0.50}` 改为**细阶梯** `_RATE_STEP=0.02` 从 1.0 步进到 `_RATE_MIN_FACTOR=0.50`（26 档）。
3. 新 CLI：`--frames`（默认 300）、`--rate-step`（默认 0.02）、`--rate-min-factor`（默认 0.50）；`_worker_init` 增加对应参数。

### 验证（`results/diagnostics/rate_search_fix_validation_20260814/validate_rate_search.py`）

方法：用冻结 V3 的逐层 BER/容量，以旧参数（100 帧+粗阶梯）复现冻结 k_best（确定性种子，同代码路径），再以新参数重搜。操作要点：沙箱下 numba `@njit(cache=True)` 写缓存会挂起，须设 `NUMBA_CACHE_DIR`（临时目录）并 `NUMBA_DISABLE_CACHING=1`（动态加载模块无法反序列化缓存）。

结果（20 dB, bw=150 采样层）：

| 层 | BER | 容量 | 冻结 k（mode） | 旧参数复现 | 新参数 k | 增益 |
|---|---|---|---|---|---|---|
| d=4 L0 | 3.8% | 0.767 | 2348 (sc) | ✓ | 2348 | 0 |
| d=4 L1 | 7.4% | 0.617 | 1712 (scl) | ✓ | 1712 | 0 |
| d=64 L0 | 0.20% | 0.980 | 3340 (scl) | ✓ | 3426 (sc) | **+0.047** |
| d=64 L1 | 0.44% | 0.959 | 3351 (scl) | ✓ | 3351 | 0 |
| d=64 L2 | 0.94% | 0.923 | 3145 (scl) | ✓ | 3040 (sc) | **+0.044** |
| d=64 L3 | 1.9% | 0.866 | 2945 (scl) | ✓ | 2673 (sc) | 0 |
| d=64 L4 | 3.8% | 0.767 | 2348 (scl) | ✓ | 2348 | 0 |
| d=64 L5 | 7.4% | 0.617 | 1712 (scl) | ✓ | 1712 | 0 |

- **保真度：SC/SCL 两条路径在全部 10 个采样层均精确复现冻结 k/mode（确定性种子验证成立）**，即验证装置忠实于冻结口径。
- **增益仅出现在粗阶梯"跳过了边界"的中间层**（d=64 L0/L2，+0.044–0.047 bits/bit）；干净层（边界本就精确落在阶梯上）与高噪声层（0 增益）不受影响。

### 结论（重要）

- 码率搜索修复**正确且已落地**，但收益局限于搜索量化分量（预计全网格平均每层 +0.01–0.03 bits/bit）。
- **高噪声层（BER≥3.8%）的 gap 不是搜索量化造成的**：即使细阶梯 + 300 帧 + SCL-4，边界仍精确落在 0.418/0.573。该 gap 来自**信道无关固定 PW 冻结序 + SCL-4 + n=4096 的解码能力上限**（`docs/POLAR_PAPER_GRADE_AUDIT_V2.md` 将 PW 序冻结为工程选择）。要吃掉这 0.14–0.20 的主 gap，需要信道自适应冻结序（Tal-Vardy/GA per layer）或更长块长——属后续更大改动。

### 待办（下一步，需授权）

1. 全链重跑：以新参数重跑 candidate 生成（`run_real_polar_max_pie.py --frames 300 --rate-step 0.02`，需 a_eff/b_eff sidecar + grid/src 表）→ round1b replay → stage2（`routeA_build_formal_stageC.py`）→ 新输出目录。预计耗时数小时。
2. 重跑后按条目 #2 的记账规则重算净率；预期低维净率小幅转正/提升，但幅度受解码能力上限约束。
3. 若需更大收益：立项"信道自适应冻结序"（影响正确性基线，需 V2 级资格重新审查）。

---

## 2026-08-14：低维 leak 分解 + 负净收益层（key-sifting）记账修正（只读分析）

### 问题

为什么低维（d=4/8/16）的 `leak_EC_actual_bits` 相对 IAB 特别大？d=4 主口径（`PIE_reconciled_net`）在多数 bw 下恰好为 0，是物理极限还是策略缺陷？

### leak 的构成（已逐层证实）

`leak/pair = Σ_l (1 − r_l) + verification_bits/pair`，其中 r_l 为第 l 层 Polar 码率、冻结位 (n−k) 即 syndrome（`pipelines/current/round1b_run_actual_ir_replay.py` L517–518：`total_leak = syndrome_bits + verification_bits`）。验证位仅 ~0.03 bits/pair（64-bit tag × 14 块 / 30104 pairs），可忽略。

物理下限：每层至少漏条件熵 H(p_l)。实测（20 dB, bw=150）：d=4 下限 0.62 vs 实际 0.99；d=64 下限 0.89 vs 实际 1.89；d=4096 下限 0.91 vs 实际 2.31。**低维"显得多"一半是摊薄效应**（符号位数少），**一半是策略 gap（每层 0.14–0.20 bits/bit）**。

### 策略 gap 来源（代码依据，`experiments/run_real_polar_max_pie.py`）

1. 验收极严 + 仿真样本少：`_N_FRAMES=100`、Wilson 95% 单侧 < `_FER_THRESH=0.05` → 100 帧最多 1 个错误（L520–524、L636–640）。
2. 码率阶梯粗：候选 = `k_base×{1.0,0.95,0.90,0.85,0.80,0.70,0.60,0.50}`（L592–600），`k_base=N×(cap−0.05)` 起跳（L650）——高噪声层一次掉 10–30% 码率。
3. 冻结序为信道无关固定 PW 序（L561；`docs/POLAR_PAPER_GRADE_AUDIT_V2.md` L38 自认 low-complexity approximation）；n=4096 短块 + SC 无 CRC-aid（`crc_bits=0`）。
4. 逐层 BSC 模型保守：Σ容量 < IAB_est（d=4: 1.384 < 1.499；d=64: 5.113 < 5.171）。

### 决定性发现：负净收益层未丢弃

层净贡献 = kept−leak = (2r−1)·n。**r<0.5 的层净亏损**：d=4 层 1、d=64 层 5、d=4096 层 11 均为 −0.164 bits/pair，但全部被计入密钥。d=4/bw=150 主口径恰好为 0 的精确算术：+0.146（层 0）− 0.164（层 1）− 0.030（验证）≈ −0.048。代码无任何层丢弃逻辑（grep `drop/discard/skip_layer` 无命中；`rescue` 仅层内 SC→SCL）。

### 记账修正（key-sifting 语义，只读重算，不动冻结数据）

脚本与输出（新目录，不覆盖任何冻结结果）：`results/diagnostics/leak_negative_layer_accounting_20260814/`（`run_accounting.py`、`per_point_layer_net.csv`、`corrected_point_table.csv`、`accounting_summary.txt`）。

- 校验：由冻结 Q3 块表（`results/paper_grade_v2/four_loss_parts_tag64/`）逐块聚合的 kept/leak 与冻结 V3 审计表 **484/484 点完全一致（0 个 mismatch）**。
- 规则：丢弃 net_layer < 0 的层（含其验证位），重算 `PIE_reconciled_net`/`SKR_reconciled_net_bps`。
- 结果（484 点 × 4 损耗）：

| 损耗 | 转正点数（0→+） | 正点数 修正前→后 | 平均 SKR 修正前→后 (bps) |
|---|---|---|---|
| 6 dB | 23 | 83→106 | 317,698 → 413,096 |
| 10 dB | 26 | 82→108 | 159,482 → 207,793 |
| 16 dB | 22 | 84→106 | 155,240 → 196,665 |
| 20 dB | 21 | 88→109 | 19,618 → 24,120 |
| 合计 | **92** | **337→429** | 总 SKR 提升 **+29.1%** |

- 维度分布：d=4 有 10/11 行转正，d=8: 13，d=16: 27，d=32: 23，d=64: 17，d=128: 2；d≥256 无转正（本就为正）。
- 示例（20 dB, bw=150）：d=4 PIE 0→0.125（SKR 0→1,227 bps）；d=64 1.930→2.101；d=4096 6.864→7.035。**484/484 点都至少有一个净负层（最深层码率恒为 0.418）**。

### 决定（2026-08-14）

1. **记账层面修正成立**：key-sifting（丢弃净负层）是标准做法，修正结果 +29.1% 总 SKR、92 点由 0 转正，属于"重新解释已有数据"，不改变 replay 结果，可安全用于论文口径讨论。
2. **代码层面修复暂缓**：改码率搜索（细阶梯/FER 帧数/CRC-aid SCL/信道自适应冻结序）或把层丢弃写入 replay 汇总，会改变冻结基线语义与历史输出，需显式授权 + 新输出目录全链重跑（candidate→replay→stage2）+ 本文档记录。
3. 本文档第二条与 `results/diagnostics/leak_negative_layer_accounting_20260814/` 为本次固化的溯源载体。

---

## 2026-08-14：确认 `post_selection_correction` 为单位混淆 + 重复计入（只读复查）

### 结论

`post_selection_correction` 把**无量纲的接受帧比例**（0.88–0.999，纯概率）当作 bits/symbol，从旧版 `PIE_secure_actual_ir` / `PIE_secure_beta_baseline` 公式里以**减法**扣除。该比例本已通过两处**正确**方式计入（乘性速率因子与有限长有效样本数），此减法项是第三处、多余的、量纲错误的应用。它方向保守（只会压低数值），但不是有推导依据的安全界，也不是有据可查的刻意保守设计。

### 证据链（2026-08-14 复核，全部只读）

1. 产生处 `tools/security_reports/round2_build_finite_key_audit_table.py`：
   - L232 `post_sel = float(accepted_frame_fraction)`（值域 [0,1]，无量纲）；
   - L262 写入 `post_selection_correction` 列。
2. 消费处（均为 `− post_selection_correction` 的加法减法项，其余项均为 bits/symbol）：
   - `tools/security_reports/round2_build_actual_ir_finite_key_shadow.py` L43–50；
   - `tools/security_reports/round2_build_beta_baseline_shadow.py` L30–36；
   - `pipelines/archive/_minrerun_common.py` L273 / L282 / L290。
3. 同一比例已经正确计入的两处（证明重复）：
   - `accepted_rate_proxy = coincidence_rate × accepted_frame_fraction × block_success_rate`（audit L203）→ `SKR = PIE × accepted_rate_proxy`（乘性后选择因子，正确）；
   - `n_eff_pairs = n_pairs × layer_fraction × accepted × block_rate`（audit L89–92、L217）→ 进入 `DeltaFK` 分母（接受帧少 → 有限长惩罚变大，正确）。
4. 历史对照：旧版 `tools/security_reports/build_actual_ir_finite_key_shadow.py` L57 的公式为 `pie = max(0, iab − leak − chi − delta_fk)`，无此项。round2 家族凭空加入；`git log -S "post_sel = float(accepted_frame_fraction)"` 显示该行自文件进入 git（commit `0e4f735`，布局重构）起未再修改；代码无注释、此前无任何文档记录。
5. 逻辑倒置：若要惩罚后选择成本，应减 `1 − accepted`（≈0.001–0.12，小量）；代码减的却是**接受**比例——接受率越高（数据越好）扣得越多，只能解释为把 0–1 比例误当成每符号损失比特数。
6. `tools/security_reports/round3_build_proof_gap_matrix.py` L17 将 `frame_level_post_selection_observables` 标为 `partial`，说明该层本就无严格推导。

### 影响量化（冻结 V3 数据，`results/paper_grade_v3/reconciled_stage2_20260812_final_v3/`，484 行 × 4 损耗）

- 去掉该项后：**90 行** `PIE_secure_actual_ir` 由 0 转正；**110 行**去掉后仍为 0（leak/χ_E/ΔFK 已压零）；**284 行**正值每行被低估约 `accepted_frame_fraction`（≈0.90–0.999 bits/sym）。
- 单点示例（20 dB，bw=150）：d=4：PIE_secure 0 → 0.093（≈918 bps）；d=64：1.791 → 2.790；d=4096：6.793 → 7.786。
- beta 对比敏感性：`PIE_secure_beta_baseline` 同样被扣且此前**未**打 blocked 标签；去掉该项后 beta-vs-main 符号在 **53/484 行**翻转。
- **对当前主口径无影响**：`PIE_main/SKR_main_bps = PIE_reconciled_net/SKR_reconciled_net_bps` 的公式不含此项。当前低维主口径为 0 是由实际 replay 泄漏（d=4 的 leak ≈ 0.99–1.57 bits/sym ≥ IAB）造成，与此项无关。

### 与既有结论的对齐

`docs/POLAR_RECONCILED_RESULT_V3.md` L16（2026-08-12）已独立记录同一问题："The previous calibrated `PIE_secure_actual_ir` formula mixed an accepted-frame fraction with bits-per-pair terms and also applied acceptance in the rate. It is retained only for compatibility and is blocked from scientific reporting." 冻结输出中该列已带 `scientifically_blocked_dimensional_inconsistency` / `diagnostic_only` 标签。

### 决定（2026-08-14）

1. **不做数值修正**：`PIE_secure_actual_ir` / `SKR_secure_actual_ir_bps` 保持 blocked/diagnostic，`composable_security_claim_flag = 0` 不变；论文不得引用。
2. **beta baseline 补标签口径**：`PIE_secure_beta_baseline` 同为量纲错误产物，解读对比时须注明存在约 `accepted_frame_fraction`（~1 bit/sym）的系统性下偏；role 保持 comparison_only。
3. **不修改公式代码**：在补齐 protocol-specific phase-error / parameter-estimation observables 并决定重启 secure 口径之前，不改动三处减法公式（`tools/` 为基线，改动需显式授权并记录）。
4. 本文档与相关代码注释即为本次固化的溯源载体。

### 重启条件（将来若做 Phase 2）

- 正确修法：删除三处 `− post_selection_correction` 减法（保留 audit 列作溯源），乘性 `accepted_rate_proxy` 与 `n_eff_pairs` 两处不动；或新增独立 corrected-shadow 工具输出 `post_selection_correction_removed` 标签列。
- 必须写入**新输出目录**重跑，不得覆盖冻结 V3 与 `results/authoritative/`；同步 validator 断言与本文档。

### 相关文件

- 证据代码：`tools/security_reports/round2_build_finite_key_audit_table.py`、`round2_build_actual_ir_finite_key_shadow.py`、`round2_build_beta_baseline_shadow.py`、`build_actual_ir_finite_key_shadow.py`、`round3_build_proof_gap_matrix.py`、`pipelines/archive/_minrerun_common.py`
- 口径文档：`docs/POLAR_RECONCILED_RESULT_V3.md`、`AGENT_HANDOFF.md`、`docs/SECURITY_MODEL.md`、`docs/CURRENT_MAINLINE.md`、`docs/RESULTS_INTERPRETATION.md`
