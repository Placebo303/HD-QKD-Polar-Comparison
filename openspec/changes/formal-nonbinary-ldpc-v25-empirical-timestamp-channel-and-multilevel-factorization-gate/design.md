# Design: formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate

## 0. Status and lifecycle boundary

DRAFT_PENDING_P0_AUDIT_AND_FREEZE_REVIEW. 执行前需：P0 只读审计 + 独立 freeze
review ACCEPT。生命周期四层分离：engineering pass ≠ DE pass ≠ finite success ≠
qualification/promotion。V25 只停在架构选择（M4），不进入 DE。

## 1. Frozen science background

- V24 只排除冻结 V17 聚合信道 / GF(1024) / bounded single-edge 空间；不排除
  GF(512)/GF(256)、multilevel NB-LDPC、source-conditioned 信道、Bob-full 分层、
  local/global 混合图、true MET、重新校准 delay 的经验信道。
- V19 只说明“公开 LSB”恶化泄漏账本；未测试所有低位也被编码的 multilevel
  reconciliation。
- 现有 q512 probe 只是极小的诊断预算，不能作为 GF(512) 不可行证据。
- V17 联合信道 = 十个 Gray 位面边缘 BER 的 product-of-marginals，不是从完整
  P(A|B) 拟合的经验联合信道。

## 2. Definitions (frozen)

- A,B ∈ {0..1023}：Alice/Bob 每 frame 原始 time-bin symbol（真实物理 1024-bin）。
- Z = (source, file, acquisition block, bin width, delay setting, boundary class, …)
  只允许公共配置或可由公共数据确定的量进入解码器。
- 解码信道：P(A|B,Z)。诊断量（不混用为解码信道）：
  Δ_signed=A−B；Δ_mod=(A−B) mod 1024；M=L(A)⊕L(B)。
- 条件熵下界：H(A|B,Z)；leakage 归一化为每 1024-bin 符号公开 bit；f=leak_IR/H。

## 3. Encoding layering vs physical binning (must be separated)

- 编码分层：保持 200 ps bin 与 1024-bin frame，只对 10-bit 标签可逆分解。示例
  GF(512)+GF(2)：C=⌊A/2⌋, R=A mod 2, A=2C+R；GF(256)+GF(4)：A=4⌊A/4⌋+A mod 4。
  不是有限域同构，是 10-bit 标签可逆分块；每层用各自有限域运算。
- 物理 bin 合并（200→400/800 ps）会改变字母表/bin 数/pairing/边界/SER/每帧原始
  信息量；只能作单独物理粗粒化对照，需同一 .ttbin、同 frame period、锁 delay、
  分别物化、additive output、不覆盖。V25 默认不授权重型 raw pipeline。

## 4. Candidate factorizations and labelings (strictly pre-registered)

| ID | 位宽分解 | 纠错层 |
|---|---|---|
| F01 | 9+1 | GF(512)+GF(2) |
| F02 | 8+2 | GF(256)+GF(4) |
| F03 | 5+5 | GF(32)+GF(32) |
| F04 | 4+4+2 | GF(16)+GF(16)+GF(4) |
| F05 | 3+3+3+1 | GF(8)x3+GF(2) |

- F01/F02 主高维候选；F03 低复杂度非二元对照；F04/F05 文献优先中小域对照。
- L01 natural（L_N(A)=A）；L02 Gray（L_G(A)=A⊕(A>>1)）。每个 factorization 都要
  分别报 natural/Gray。禁止 holdout 后发明第三种 mapping。

## 5. Layer-wise conditional channel and chain rule

- Bob 输入必须保留完整 B（不要只留 coarse layer）。
- 第 i 层只用：完整 B + 公共 Z + 已 Bob-only 解码并通过验证的前层。
- residual 层不得直接公开；每层 syndrome 进入总 leakage。
- 必须验证 chain rule：H(A|B,Z) = Σ_i H(U_i|B,Z,U_<i)，同一联合计数器/estimator
  浮点误差内闭合。
- 禁止推导“coarse 条件熵更低 ⇒ 总泄漏更低”；coarse 减少部分进入 residual。

## 6. Data roles and split (frozen)

- D01/V17：冻结 aggregate 对照、SER/BER/entropy 核对；不得重建完整 P(A|B)（无 raw
  joint arrays）。
- Legacy pairs：characterization / model comparison / factorization gate / drift
  分析；不得用于 fresh qualification / promotion / 最终 FER。
- 切分：每 source/file 时间序 60% train / 20% validation / 20% sealed holdout。
  禁止随机拆 symbol、frame 跨 train/holdout、holdout 上估 delay、按 holdout 选
  mapping、混合 source 后随机切。frame 太少则报告并停该 source 正式 gate。

## 7. M0-M4 stages

- M0 时间戳误差图谱：raw SER、signed/modular delta hist、|Δ| 分位、
  -1/0/+1 质量、正负不对称、parity、coarse boundary crossing、frame boundary、
  Gray mask/popcount、位面共同错误矩阵、run-length（不跨 source/file/frame）、
  相邻自相关、delay drift、occupancy。旧错误实现与 corrected 实现区分。
- M1 模型：C01 QSC；C02 V17 product；C03 pooled additive signed-delta；
  C04 source-conditioned；C05 source+parity/boundary-conditioned；
  C06 local-jitter+global-background mixture。保留完整 sparse N[A,B]/P(A|B,Z)；
  smoothing/backoff 若需要必须预注册。每个模型在 validation/holdout 上报告 NLL、
  条件熵、calibration、zero-prob count、per-source；pooled 仅补充。
- M2 delay 门：每 source 只用 train 估 delay→锁死→validation/holdout 上算 signed
  delta；比较 SER/±1 mass/offset sign/条件熵/time drift。±1 校准后消失→归为
  calibration/materialization 问题；source-dependent calibration 必须记录，禁止
  平均成全局参数。
- M3 分解门：F01–F05 × L01–L02。顺序规则固定（每步选当前条件熵最小层，tie 用
  layer ID）；train 定顺序、validation 选候选、holdout 看验证；每层 H_i；chain
  rule 闭合；R_i_ref=1−1.3 H_i/a_i（仅参考）；复杂度代理（field size、消息长、
  Q log Q、层数、独立 H 数量、条件概率表规模）。
- M4 终态：pass_ready_for_de_change / fail_no_stable_factorization /
  blocked_insufficient_joint_data / blocked_alignment_unresolved。

## 8. Output schema (additive)

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_YYYYMMDD/run_<ts>/`
最低文件：data_inventory.json、split_manifest.json、channel_summary.json、
delta_by_source.csv、gray_joint_masks.csv、channel_counts.npz、
model_holdout_scores.csv、factorization_layers.csv、chain_rule_check.json、
alignment_report.json、gate_summary.json、readonly_verify.json。
报告：`docs/nbldpc-v25-empirical-channel-and-factorization-report-YYYYMMDD.md`。
不加 checksum/原子写/DB/cache/并发/重试/通用抽象。

## 9. Verification

- 测试 T01–T12（见 tasks）：labeling 可逆、分层可逆、重构 0–1023、切分无重叠、
  signed/modular 不混淆、run 不跨边界、chain rule tiny 闭合、公开 residual 负例、
  Bob-full vs Bob-coarse 不可混用、Alice oracle 检测、holdout 不写回 train、
  verifier 从原始统计重算 terminal gate。
- 独立 verifier：只读、不调生产执行器、不改 evidence、从 counts+frozen config
  重算主要指标与终态，输出 ok=true/false + 问题列表。
