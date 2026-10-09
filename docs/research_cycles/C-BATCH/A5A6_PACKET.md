# A5/A6 第三轮冻结设计（B2 门控，2026-10-09）

> 任务包 `docs/SOFTWARE_NOW_20261009.md` A5、A6。**执行门**（事先写死，
> `B123_PREEXECUTE.md` §5）：B2 软信息增益 G 在主要 bw（200 ps）上
> ≥ 0.02 bit/符号或 ≥ H(A|B) 的 3% → 做 A5 和 A6；低于阈值 → 只做 A5，
> A6 记为负结果并写明数值。结论写清样本量和置信区间。
> 本文件只冻结设计，不执行；门判定由主线程在 B123 落盘后做出并记录。

## A5 理论速率预测工具（实现 + 合成自检，无真实解码）

- 新建：`comparison_bench/src/comparison_bench/formal_ir/msd_a5_soft_rate.py`
  （加法；numpy + math only）。
- 输入：实测 Δ 分布（B1 直方图 / 高斯拟合参数 σ̂、μ̂ + 经验尾）。
- 口径（Birnie 等 / Boutros & Soljanin 的口径，不声称新公式）：
  - hard 可达协调速率：`R_hard = H(A|B_bin)`（Slepian–Wolf 界，plug-in H(e)；
    另报有限长 backoff 列，B≥300/B≥1000 两档正态近似，仅作参照）。
  - soft 可达协调速率：`R_soft = H(A|B_fine) = E_fine[H(e|fine)]`（B2 同口径，
    子 bin 数 8，可配）。
- 自检（合成零真实数据）：BSC(p) 下 R_hard = h₂(p)（与闭式一致到 1e-9）；
  fine 与误差独立时 R_soft == R_hard；σ≪bw 高斯下 R_soft < R_hard 且方向为正；
  用 B2 实测 (σ̂≈25, bw=200) 的合成复现与 B2 经验 G 交叉一致（±2SE 内）。
- 测试：`comparison_bench/tests/test_a5_soft_rate.py`（T0/T1 级）。
- 机器根：`workspace/swnow_20261009/a5_20261009/`（工具输出 + 自检表）。
- 上限：只报可达速率界，不报译码器可实现性（那是 A6 的事）。

## A6 软时间信息译码接口（实现 + 合成验证，无真实解码）

- 改动（加法为主）：两级二元链第一级接受逐符号 LLR 向量
  （`LLR_i = log[P(a0=0|b,fine_i)/P(a0=1|b,fine_i)]`，由 Bob 按 bin 内精细位置
  + Δ 分布算出）；复用既有二元 BP 译码（`make_bp_decoder` 同族接口，
  不改冻结基线；新 wrapper 放在 formal_ir 加法文件中）。
- 合成验证：参数化 (p, p₋) 无记忆信道 + 高斯 Δ（σ=25, bw=200）；
  对比同码率下 hard（bin 级统一 LLR）vs soft（逐符号 LLR）的 FER–披露曲线
  （B≥300，种子冻结）；增益方向须与 Boutros & Soljanin 一致
  （soft 所需披露 ≤ hard，同 FER 下）。
- 负结果条件：若合成验证显示 soft 无增益或为负，如实记录数值并判 A6 负结果
  （不调参、不换信道、不开第二波；科学输入/假设不变的一次工程修正除外）。
- 机器根：`workspace/swnow_20261009/a6_20261009/`。
- 上限：只做实现和合成验证；真实数据验证不在本轮范围。

## 返回条件（二选一）

完成：A5 工具 + 自检表、A6 接口 + 合成 FER–披露曲线（含种子/样本量/CI）；
或 B2 低于阈值 → 只做 A5，A6 记负结果并写明 B2 数值。
