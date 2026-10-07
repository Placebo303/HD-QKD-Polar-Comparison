# G-5 packet — methods bake-off (EXPLORE, credible synthetic, B>=300)

> Track: EXPLORE (parametric ternary channel, G-1 validated). Bounded,
> additive root `workspace/g5_bakeoff/`. No FER/SKR claims.
> R14: per-method ideal vs actual disclosure in results (A: N*h2 vs |F|/m_A;
> B: N*p*h2 vs m_B).

## 冻结设计
- 信道：无记忆 (p, p₋)=(0.2376, 0.0058)，a ~ T2-1M 经验 pa，d=1024。
- A 方法（三选一，同模型 LLR P(x0|b)，隔离码效应）：
  Polar-SCL8（|F|/N ∈ {0.85, 0.88}，DE-Bhattacharyya 冻结集，只读 sibling）；
  RA-LDPC（gap ∈ {0.08, 0.10, 0.12}，q=5 RA 结构）；
  PEG-LDPC（gap 0.15，对照）。
- B：margin 2.5 主 + 3.0 对照（PEG-BP + K2 rescue + 算术重建）。
- N ∈ {16384, 32768}；B=300/点；池化。完整符号 f（tag 64），und 隔离。
- Polar 行即同数据 Polar 对照列（ syndrome 披露口径）。

## MDE
先 N=16384 全网格；N=32768 随后。选 f 最低配置。
