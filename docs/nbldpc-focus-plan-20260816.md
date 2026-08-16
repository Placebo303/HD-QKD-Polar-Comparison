# NBLDPC Focus Plan — 主攻 nonbinary LDPC，与已有 Polar / Binary LDPC 基线对比 (2026-08-16)

Status: PLAN — this is the executable contract for the next DSH conversation

## 0. 用户最新决策
- **Binary Polar MLC：已实现**，只读作为对比基线。
- **Binary LDPC MLC：已实现**，只读作为对比基线。
- **Nonbinary LDPC：尚未实现，是当前唯一主攻路线。**

## 1. 目标
实现 q-ary LDPC 信息协调（目标域 q=1024，Gray，256-symbol 帧），并与已有两路基线做同口径对比：
- 统一指标：syndrome bits、disclosed public bits、f、FER/exact_correct、runtime、status。
- 统一信道：V17 位面误差模型 / q=1024 Gray 结构化信道；合成帧先验，legacy real pairs 后验。
- 目标：**f ≤ 1.3**；达不到则诚实记录每路最佳 f 与 FER。
- 泄漏记账：`f = (syndrome_bits + public_bits) / H_full`，H_full=0.549955 bits/symbol。
- Claim boundary：`diagnostic_only` / `legacy_drift_audit`；不得声明 fresh/promotion/qualification。

## 2. 已有只读基线（不修改）
1. Binary Polar MLC
   - 已有实现；在需要时用最好配置重跑一遍，只生成对比证据。
2. Binary LDPC MLC
   - `codebook_v4` H1 + `codebook_v5_h2` fallback。
   - 已知：50 frames/plane × 10 planes 全过，平均 syndrome 587 bits/frame，f≈4.17。
   - 证据：`comparison_bench/outputs_comparison/nonbinary_diagnostics/v19_binary_mlc_prototype_20260816/`

## 3. NBLDPC 主攻路线（Route N）

### N0 — 合同冻结
- 先读取 `docs/three-way-ir-comparison-plan-20260816.md`、`docs/decoder-improvement-plan-20260816.md`
  与 `AGENT_PROJECT_MEMORY.md`，复用已有 NBLDPC 诊断结论。
- 确定输出根：`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_<date>/`。

### N1 — 信道模型
- 使用 `nonbinary_v18_b2_structured_de._V17_PER_PLANE_ERROR` 构造 q=1024 raw-XOR diff w，
  再 `build_folded_w(q_small)` 得到 q=16/32/64 代理。
- QSC 等熵对照保持可用：q=16, p=0.038, H≈0.3815（之前 16/16 收敛）。

### N2 — DE 搜索（先小 q，后大 q）
- 复用：
  - `nonbinary_v10_de.run_de_search` 及内部 DE/rand/1/bin
  - `nonbinary_v14_mcde` structured-channel MC-DE
  - `nonbinary_v18_b2_structured_de.run_structured_de_search`
- 已有关键结果：
  - q=16 folded plain DE：rate=0.60 收敛，f≈4.18；rate>0.60 全失败。
  - QSC 对照证明：限制是信道结构，不是搜索预算。
- 下一步：
  - N2a: q=16 上实现 **seeded / rate-ladder** DE，从 0.60 向 0.875 推进。
  - N2b: 若 plain 到墙，则试 channel-aware 机制（per-symbol-class puncture、LSB-public 两步法、
    structured edge labels），先做 diagnostic，不急着上 q=1024。
  - N2c: 在 v19 模块里扩展现有 DE 的 check-degree 上限（不修改 frozen V10/V14）。

### N3 — 有限码构造与解码（DE 过关后）
- PEG/QC 构造：`nonbinary_v10_peg.py`（frozen，可只读导入）。
- 解码：`nonbinary_v10_fftqspa.py` / `nonbinary_qspa.py`。
- 先 q=16 synthetic，再 q=1024 synthetic；N 先小后大（256/512/1024/2048）。

### N4 — 合成帧执行（execute-once）
- 确定性 seed，每路每配置跑一次。
- 记录 exact_correct / decode_failed / FER / syndrome bits / f / runtime。

### N5 — legacy real frames（可选，按边界）
- 只允许 claim `legacy_drift_audit`；不构成 fresh/promotion。

### N6 — 三路对比
- 生成 `comparison_table.csv` + `comparison_summary.json`：
  route, N, q, rate, syndrome_bits, public_bits, f, FER, runtime, status。
- 不 merge 不同路线的 status；不把 decode_failed 改成 ok。

## 4. 安全与输出纪律
- frozen `src/`、`experiments/`、`tools/`、`results/` 零修改。
- 新代码只放 `comparison_bench/`；scratch 放 `workspace/`。
- 官方输出仅 additive 目录；不覆盖既有证据。
- 本地 git commit；**不 push**。

## 5. 每轮必做
- 更新 `CURRENT_TASK.md`、`AGENT_HANDOFF.md`、`AGENT_PROJECT_MEMORY.md`。
- 若 context compact 发生，回到本文件与三份状态文档重建状态。

## 6. 关键文献锚点
- Müller et al., *Efficient information reconciliation for high-dimensional QKD*, Quantum Inf. Process. 2024：q-ary irregular DE + blind reconciliation，f≈1.078–1.14。
- Pacher 2016 两步法：公开 LSB + NB-LDPC syndrome 高位。
- Kasai / Martínez-Mateo & Elkouss：低 SNR 时乘法重复 NB-LDPC mother code。
