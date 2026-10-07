# G-2 packet — two-level binary IR (EXPLORE, credible synthetic proxy)

> Track: EXPLORE (parametric synthetic validated as memoryless ternary on real
> data; R10 mismatch = 2-param estimation error only). Bounded, reversible,
> additive root `workspace/g2_twolevel/`. No FER/SKR claims.
> R14: level A ideal N·h2(p) vs actual m_A + rescue; level B ideal
> N·p·h2(p₋/p) vs actual m_B + rescue (numbers in results).

## 冻结设计
- 信道：无记忆 (p, p₋) = (0.2376, 0.0058)，a ~ T2-1M 经验边际（d=1024，d 无关），
  e=0 w.p. 1−p；+1 w.p. p−p₋；−1 w.p. p₋；b=(a+e) mod d。
- 级 A（LSB）：二元 PEG dv3（复用 msd_peg_code.binary 路径），min-sum/BP
  （复用 make_bp_decoder），N ∈ {16384, 65536}（N=4096 在 p=0.24 下低于 BP
  有限长阈值，gap 0.15 仍 0/10，已砍），gap ∈ {0.10, 0.15}
  （阈值实测：dv3 在 p=0.24 下需要 gap≈0.12，与 M1 的 C0=2000 一致；
  均匀先验不够，必须用三值模型的全符号条件先验 P(x₀|b)；更高 dv 更差），
  m_A = ceil(N·(h2(p)+gap)）；失败则 K=400 定向 rescue（先验有信息量）。
- 级 B（符号位）：bit1 全平面 syndrome，m_B = ceil(N·0.0122·margin)，
  margin ∈ {2.0, 3.0}；先验：marked 面 p=0.0058（相对 b1^a0），unmarked 精确 pin
  （结构恒等式，非估计）；PEG-BP，失败则 K2=64 rescue。
- 高位：算术重建 a_rec = b − delta(mark, sign)，逐符号验 exact。
- 口径：完整符号 exact + 期望良率 f（tag 64 + kept 惩罚），undetected 隔离，
  B=300/配置，池化 x12。
- MSD 平台核对（附带，解析对照）：level-B（符号位译码）vs S-1 MSD plane-1
  （m₁=600，100% 失败）——同信息量不同路径；若两级无平台，记录 MSD 实现缺陷位。

## MDE/预算
12 配置 × 300 块池化；上限 21600 s。成功：任一配置 f 显著低于 NB 链 1.376。
