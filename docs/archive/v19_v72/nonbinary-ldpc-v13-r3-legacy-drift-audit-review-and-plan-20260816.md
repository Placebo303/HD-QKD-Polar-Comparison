# V13-R3 Legacy Drift Audit — 数据审查、文献对照与后续方案 (2026-08-16)

Status: REVIEW COMPLETE; next routes are gated on user decision

## 1. 当前数据与结论（可核查证据）

### 1.1 全量 legacy audit（用户指定三份 2026-01-21 数据）

- 总帧数：8412
- 不变 R3 候选 `nbldpc_v13_r3_code_v1`（q=1024，n=256，m=170，
  168x3+2x4，rank=170，seed=20260818；QSC p=.20；flooding FFT-QSPA；
  max_iter=100）
- 结果：**8284 exact_correct / 128 decode_failed / 0 exact_mismatch**
  - 精确纠错率：98.4784%
  - 128 个失败全部为 `iteration_limit`（100 迭代未收敛）
  - 失败帧 raw SER：0.1875–0.3359，均值 0.2596（全量均值约 0.240–0.256）
- 分源：
  - type2_1p5M：2729/2767（38 失败）
  - type2_1M：1970/2000（30 失败）
  - type2_2M：3585/3645（60 失败）
- 8 个 chunk 与全量合并包均通过只读 verify；claim boundary
  `legacy_drift_audit` only。

### 1.2 漂移状态（D5 precheck）

- raw SER：0.2398 / 0.2545 / 0.2557（V13 D01 参考 0.0771）
- 条件熵 H：0.8066 / 0.8294 / 0.8334 bits/symbol（V13 参考 0.5470）
- bit-plane mismatch：仍 MSB→LSB 单调，幅度整体高于 V13 参考。

### 1.3 效率现状

固定 syndrome 开销 = m * log2(q) / n = 1700/256 = 6.640625 bits/symbol。

| 场景 | H(bits/symbol) | f = 6.640625 / H |
|---|---:|---:|
| V13 历史参考 | 0.5470 | **12.14** |
| legacy 1M | 0.8066 | 8.23 |
| legacy 1p5M | 0.8294 | 8.01 |
| legacy 2M | 0.8334 | 7.97 |

与文献对比：Müller et al. 2024 在 q=4/8 上 NB-LDPC 效率 f≈1.078–1.14
（QBER 3–15%），HD-Cascade q=4/8/32 f≈1.06–1.12。当前 R3 的 f≈8–12
说明它是以极高 syndrome 开销换取短帧精确纠错的 fixed-rate 设计，不是
容量逼近设计。

## 2. 关键文献与可借鉴点

1. **Müller, Bacco, Oxenløwe, Forchhammer**, "Information
   Reconciliation for High-Dimensional Quantum Key Distribution using
   Nonbinary LDPC codes", ISTC 2023, arXiv:2305.08631；扩展版
   "Efficient information reconciliation for high-dimensional QKD",
   Quantum Information Processing 23, 2024, DOI
   10.1007/s11128-024-04395-w。
   - q-ary symmetric channel 模型；MC-DE + Differential Evolution 优化
     degree distribution；concentrated check degree；dv,max=40；
     n=30000，PEG 构造；log-FFT-SPA；blind reconciliation
     （puncture/shorten，R = (n-m-s)/(n-p-s)）。
   - 直接指导：若要降低 f，需要 DE 优化 irregular ensemble + 率适配，
     而不是固定全 syndrome。
2. **Pacher, Martinez-Mateo, Duhme, Gehring, Furrer**, arXiv:1602.xxx
   (2016), "Information reconciliation for CV-QKD using non-binary
   LDPC codes"。
   - 两步法：先公开 LSB，再用 GF(2^m) NB-LDPC syndrome 纠正高位；
     GF(8/16/32/64) 上效率 0.94–0.98。
   - 与本文数据 MSB→LSB 单调失配高度吻合：LSB 错误率高，适合公开/
     分平面处理。
3. **Kasai, Declercq, Poulliat, Sakaniwa**, "Multiplicatively Repeated
   Non-Binary LDPC Codes" (arXiv:1012.3507? 2010)；
   **Martínez-Mateo & Elkouss**, EPJ Quantum Technology 2025。
   - (2,k)-regular NB-LDPC mother code 乘法重复得到率兼容低码率；
     短/中块长表现好；解码复杂度接近 mother code。
   - 适合低 SNR/强纠错备选；但当前问题在 f 太高而非太低。
4. **Potapova & Frolov**, "On Multilevel Coding Schemes Based on
   Non-Binary LDPC Codes" (arXiv:1702.xxxx)。
   - NB-LDPC-MLC over GF(16) 可达到 GF(64/256) 级性能；说明 q=1024
     不一定是必要字段阶数，可分层到小域降复杂度。
5. **Savin**, "Non binary LDPC codes over the BEC: density evolution
   analysis"；**Gorgoglione, Savin, Declercq**, "Optimized puncturing
   distributions for irregular non-binary LDPC codes"。
   - DE 中 edge-label distribution 是设计自由度；不规则 NB-LDPC
     puncture 可做率适配且离容量 0.2–0.5 dB。
6. **SC-LDPC threshold saturation 文献**（binary 为主，如 Kudekar et al.
   阈值饱和）。本项目 V11/V14/V17 已冻结相关路线；若重启需要先做
   非二元 SC-LDPC 的 DE 证据门。

## 3. 后续方案（按优先级，均需用户决策后才立项）

### Route A — 失败诊断 + 结构化信道建模（0 新 claim，推荐先做）

- A1 对 128 个失败帧做特征归因：raw SER、bit-plane mismatch、prior
   mismatch（实际 SER≈0.25 vs p=.20）、解码熵轨迹。
- A2 用全量 pairs 拟合结构化 q-ary 信道（复用 V17 product-of-marginals
  模型），量化 QSC 先验失配对收敛的影响；只做诊断，不改冻结候选。
- A3 诊断性试验（结果仅 diagnostic_only）：提高 max_iter、或按帧估计
  SER 设先验，观察失败是否消失；任何正式结论必须走新 change。

### Route B — 效率改进（新 change，先 DE 门后码设计）

- B0 新 OpenSpec change：以“结构信道 + q-ary DE”为门。
- B1 复现 Müller 2024 的 MC-DE + Differential Evolution 管线，先在小
  域（q=8/16/64）上对标其表 1 阈值，验证实现正确。
- B2 在本项目 V13 D01 信道统计上优化 irregular NB-LDPC ensemble：
  目标 f≤1.3、BER/FER 与纠错能力达标；候选码长先试 n=512/1024/2048
  （工程上分帧拼接，256-symbol 帧是物理边界）。
- B3 率适配：puncture/shorten 或 LSB 公开 + syndrome 组合（Pacher
  2016 两步法）；用 blind reconciliation 支持 QBER 15–30% 区间。
- B4 若低 SNR/强纠错需求出现：乘法重复 NB-LDPC mother code（Kasai；
  Martínez-Mateo & Elkouss）作为率兼容后备。

### Route C — 复杂度/工程化

- C1 分层小域方案：将 q=1024 拆为 bit-plane / GF(16) 层（Frolov MLC），
  降低 FFT-QSPA 的 q log q 复杂度。
- C2 评估 log-FFT-SPA 是否已是当前最短路径；与 EMS/reduced-complexity
  变体比较吞吐/损失（Wang 2013；Wu 2020 等）。
- C3 硬件/吞吐预研仅在前两条路线科学结论明确后启动。

### Route D — 结论边界与数据

- D1 当前 legacy 数据只能支撑 `legacy_drift_audit`；真正 fresh
  confirmation 仍需 fresh 数据重新 prepare→192 帧执行。
- D2 效率路线 V14/V17 冻结纪律保持：不重启 V15/V16、不扩大搜索、
  不 rerun/调参；新路线必须新 DE 门 PASS。
- D3 push 仍待用户单独授权。

## 4. 本次审查的即时结论

- R3 在 legacy 漂移数据上仍有 98.48% 精确纠错能力，证明候选对该类
  漂移具备鲁棒性，但不是 100%，且不构成 fresh/promotion 声明。
- 当前主要科学瓶颈是 **reconciliation efficiency f≈8–12**，文献路线
  明确：DE 优化的不规则 NB-LDPC + 率适配 + 结构化信道模型。
- 下一步建议：先做 Route A（诊断，不破坏冻结），再由用户决定是否
  立项 Route B（效率）或 Route C（复杂度）。
