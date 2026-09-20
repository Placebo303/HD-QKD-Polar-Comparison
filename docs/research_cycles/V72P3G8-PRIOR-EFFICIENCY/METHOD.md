# G8 方法书 — 用结构化条件信道替换被"抹平"的先验（交另一 session 执行）

Track：S0 为 **EXPLORE**（只用已冻结产物 `counts_ab`，零真实数据、零解码器调用）；
S2 起按现有 D18/D19/G6 协议各自立项。本文件不授权任何执行。

分支 `formal-ir-v72p1-addendum-clean`；不 commit / push；不覆盖任何证据根。

---

## 0. 一句话结论

净收益为负**不是数据太脏，也不是高维不行**，而是生产先验
`P_F(A|B)` 被平滑成近似"全局边际"，导致解码器每符号要付
≈**4.34 bits**（GF(32) 上限 5）的不确定性；真条件熵只有 ≈**0.55–0.83 bits**。
修好先验，`m/n` 可从 ≈0.87 降到 ≈0.11–0.16，净收益转正。

## 1. 根因（代码级定位）

### 1.1 生产链路

```
v72p2d9.load_l1_channel(model_f_root)                 # v72p2d9_de_decoder_calibration.py:340
  → mfi.load_model_f_input(...)                       # 读 workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz
  → build_l1_channel_from_counts(counts_ab, p_b)      # :324
      → d5.prepare_model_f_prior_candidate(...)       # v72p2d5_gf32_rate_mother.py:2481
          → build_f_model_concentration(counts_ab, lam=LAMBDA_STAR)   # :275
      → d5.marginalize_f_to_p1(p_f)                   # :309   (L1 先验)
      → d5.conditionalize_f_to_p2(p_f)                # :324   (L2 先验)
```

`LAMBDA_STAR = 137.3823795883264`（`v72p2d5_gf32_rate_mother.py:46`）。

### 1.2 为什么先验被抹平

`build_f_model_concentration`：

```python
p = (counts + lam * p_global[:, None]) / (n_b[None, :] + lam)
```

- 表规模：1024×1024 = **1,048,576 格**，样本只有 **262,144**（CAL702..1725，
  每 Bob 列平均仅 **256** 个样本，即每格 0.25 个样本）；
- λ = 137.38 作为**每列总浓度** ⇒ 每列平滑占比
  `137.38 / (256 + 137.38) = 34.9%`，且这 35% 全部投向 **Bob 无关的全局边际
  `p_global`**；
- 非参 1024×1024 表在 0.25 样本/格下根本不可估，nested-CV 选出的 λ 必然把后验
  拉回"全局边际" ⇒ 先验退化为 **Bob 盲**，熵接近均匀。

对应实测：解码器 `belief_mean_entropy` 上界 **4.343407 bits**（GF(32) 上限 5，
见 D7_D operator return；R14 记为 session-blind 弱先验）。

### 1.3 与实测的自洽校验（说明这个解释是对的）

| 量 | 由 H_eff=4.343 预测 | 实测 |
|---|---|---|
| 收敛所需 `m_min/n ≈ H_eff/5` | 0.869 ⇒ m≈111 | m94: 0/128；m100: 1/128；m120 分级: 87/128 |
| 每块净收益 `N = 128(3−1.6H) − 102.4` | −607 bits | R9 −563 / R11 −612 / R12 −620 |

参考锚点：V19 实测 `H_full = 0.549955 bits/symbol`；V25 经验 delta 模型
holdout NLL ≈ **0.81–0.83 bits**（vs QSC 3.2 / V17 3.3）。即：同样一份数据，
**结构化条件模型能把每符号不确定性做到 1 bit 以下**，当前先验却在 4.3。

## 2. 修复方案（按优先级，均为加性改动）

### F1（主推）：用"位移/δ 结构化条件模型"替换非参表

用全部 262,144 样本估一个 **1024 维的位移分布**（每 bin 约 256 样本），
而不是 1M 格的非参表：

```
delta = (a - b) mod 1024
q[δ]  = Σ_b counts_ab[(b+δ) mod 1024, b] / N
P_F(a|b) ∝ q[(a-b) mod 1024]                      # 列内归一化，逐列和为 1
可选回退：P = (q_shift + eps * p_global) / (1 + eps)，eps ≪ 1
```

要点：

- **不要复用 `LAMBDA_STAR`**：它是"非参表 + 全局边际回退"语义下的 CV 值，
  在新模型类下必须**重新**用 nested-CV 选 eps（且不得在 confirmation 数据上选）。
- V25 已验证该模型类的有效性（NLL 0.81–0.83），并指出偏移方向随
  source/delay 变化（±1 相邻偏移）⇒ 进一步可按 session / delay 条件化。
- 下游**完全不用改**：`marginalize_f_to_p1` / `conditionalize_f_to_p2` /
  `build_l1_sampler` / `build_l2_oracle_sampler` 原样复用，只替换 `p_f` 的来源。
  保持"additive-only、默认值不变"的既有纪律（D7 先例）。

### F2（对照臂）：λ 契约与重新选择

- 历史函数 `build_f_model`（:247）是**逐格**伪计数（每列平滑 137×1024 ≈
  1.4e5 vs 观测 256 ⇒ 99.8% 平滑，近乎完全均匀），仅用于历史重建，不用于生产；
- 生产用 `build_f_model_concentration`（per-column，已修正契约），但 λ 仍过大；
- 对照臂：在同一契约下用 nested-CV 重选 λ，报告 H_eff。**预期不足以达标**
  （非参表本身不可估），保留作为对照证据。

### F3（若 S0 通过后再做）：per-session 化

当前 counts 仅来自 session `20260123_1M_600k_0dB`（1M）；G6/G7 池含
1M/1p5M/2M，权重 72.70/77.62/90.07。位移模型可迁移性远好于表，但 δ 分布仍可能
随 session 漂移 ⇒ 按 session 分别估 δ（需真实 pool 聚合，属 DECIDE）。

## 3. 会计口径与门槛（照抄，勿改）

- 泄漏 `L = 5m + 64`；毛密钥 `G = Â·5·(n−m)`，Â = 0.6，n = 128；
- 净 `N = 320 − 8m` ⇒ **净正 iff `m ≤ 39`**；
- 可解性 `5m + 64 ≥ n·H_eff` ⇒ **净正 iff `H_eff ≤ (5·39−64)/128 = 1.023
  bits/plane-symbol`**；
- 通式 `N = n[5Â − (1+Â)H_eff] − 64(1+Â)`；Â=0.6 时净正 iff `H_eff < 1.875`；
- 目标 `m`：`m = ceil((n·H_eff·(1+overhead) + 64)/5)`，overhead 取 1.2–1.5；
  H_eff≈0.8 ⇒ m ≈ 25–31 ⇒ N ≈ +72…+120 bits/帧（未计 FER 损耗，须实测）。

## 4. 执行步骤

### S0 — 三项 H_eff 测量（EXPLORE，零真实数据，零解码器调用）

输入：`workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz`
（`counts_ab` (1024,1024)、`p_b`）；只做数组运算，不读 pool、不调解码器。

输出（单一 additive 结果文件 + 一条日志）：

- `H_A`：当前 `build_f_model_concentration(counts_ab, LAMBDA_STAR)` → 经
  `marginalize_f_to_p1` / `conditionalize_f_to_p2` 后的**每 plane-symbol 熵**
  （预期复现 ≈4.34，作为口径自检；若与 4.34 差很多，先查口径再继续）；
- `H_B`：F1 位移模型（eps 先取 1e-3 与 1e-2 两档）→ 同样口径的每符号熵；
- `H_C`：F1 + 每 bin 条件化（δ 按 Bob 的 bin 分段，如按 b//64 分 16 段）的熵
  （可选，成本极低）。

口径定义（写死，避免歧义）：
`H_eff = Σ_b p_b[b] · ( -Σ_{u} P_plane(u|b) log2 P_plane(u|b) )`，
`P_plane` 分别取 `p1`（L1）与 `p2`（L2，对 u1 再求期望）。**两个都报**，
取较差者作为门槛判定值。

判据（冻结）：

- `min(H_B, H_C) ≤ 1.023` → 进 S1/S2（授权后才跑 DE/解码器）；
- `> 1.875` → 当前分帧下净正信息论不可达，路由转到"先对齐/条件化"，停止调码；
- 中间区间 → 单列决策点，不自动推进。

成本：秒级、零调用。

### S1 — 冻结新先验契约

把 F1 写成与 `build_f_model_concentration` **同签名**的纯函数
（输入 `counts_ab`，输出逐列和为 1 的 `p_f`），并在
`prepare_model_f_prior_candidate` 旁提供加性选择路径；保持旧函数不变。
配套：列和 1e-12 校验、零列回退、floor/renorm 与现有一致。

### S2 — DE 复扫（按 D18 协议）

以 S0 得到的 `H_eff` 定 `m` 网格（`m ∈ {ceil(...)-8 … ceil(...)+8}`），
跑 D18 协议的 DE 扫描，记录阈值/边沿。**预期：阈值 m 从 92|96 大幅下移。**

### S3 — 有限码验证（按 D19/G6 协议）

合成优先；真实数据必须单独走 DECIDE（prereg + 授权 + Pre-EXECUTE +
Pre-RESULT），遵守：undetected 隔离（永不并入 success/FER）、披露按最终前缀
计（不累加各 stage）、beta 只推导不手填、单授权单次执行、additive UUID 根、
`refuse_out_root` 拒绝已存在根。

### S4 — 重算净收益

按 §3 公式，用实测 `m` 与 FER 重算；同时报 gross/true-net 两个数（R9 先例）。

## 5. 陷阱与禁止项（写给执行 session）

1. **不要为了让测试变绿去删证据根或改断言**（D19/R9–R12 那批"根不存在"失败是
   执行后的预期状态，troubleshooting 已记录；转换需单独 scoped change）。
2. **不要把 `LAMBDA_STAR` 直接套到新模型类上**——语义不同，必须重选。
3. **不要在 confirmation/VAL 上选 eps 或调 λ**（CAL702..1725 才是 TRAIN）。
4. **不要改 `marginalize_f_to_p1` / `conditionalize_f_to_p2` / 采样器**，只换
   `p_f`；改动面越小越可审。
5. 不要碰冻结输入：`results/`、`comparison_bench/outputs_comparison/`、
   `v72p2d5_model_f_input/20260907_r1/` 只读。
6. 测试必须**逐文件**跑（多文件合并会触发 `PRODUCTION_ABSENT` 的
   `sys.modules` 污染）；WSL `.venv` 为权威环境（用 `-o addopts=""`），
   Windows 需外部 `--basetemp`。
7. 声明上限：S0 只是合成/产物层面的诊断，**不得**输出 FER/SKR/资格化/
   promotion/最优性结论。

## 6. 验收标准

- S0：三个 `H_eff`（L1/L2 各一）数值 + 样本口径 + 与 4.343 的自检说明；
- S1：新函数逐列和 ≤1e-12、零列回退正确、旧路径字节行为不变（回归测试通过）；
- S2：DE 阈值 m 明确下移，且给出新旧对照；
- S3：undetected=0 且单独隔离、披露口径与 R12 一致、verifier 通过；
- S4：`N = 320 − 8m` 用实测 m 计算，且同时给出 gross/true-net。

## 7. 关键文件索引

| 用途 | 路径:符号 |
|---|---|
| 先验平滑（历史/逐格） | `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py:247` `build_f_model` |
| 先验平滑（生产/逐列） | 同上 `:275` `build_f_model_concentration` |
| L1/L2 先验派生 | 同上 `:309` `marginalize_f_to_p1`、`:324` `conditionalize_f_to_p2` |
| 生产入口 | 同上 `:2481` `prepare_model_f_prior_candidate` |
| λ 常量 | 同上 `:46` `LAMBDA_STAR` |
| 信道装载 | `v72p2d9_de_decoder_calibration.py:324/340/346` |
| DE 绑定/通道构建 | `v72p2d17_descaling.py:1133/1297` |
| 输入产物 | `workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz` |
| 会计/门槛推导 | `docs/v72p3-progress-and-issues-report-2026-09-19.md` §4 |
| 预注册 | 本目录 `PREREG_AND_AUTH.md` |
