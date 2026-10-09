# C 批预注册修订（A1，2026-10-09）

> 任务包 `docs/SOFTWARE_NOW_20261009.md` A1：按该包 §0 修订
> `docs/C_BATCH_PREREG_20261008.md` 的 §0、§1、§7；文献换成已核对的 DOI（任务包 §D）；
> 新增 R17（措辞规则）。
> 原文保留为准；本修订仅替换下述节，冲突处以本修订为准。
> Track：documentation-only（无 track gate），本身不授权执行。

## 修订 §0（替代原 §0）——论文定位：以实测为主

- 暂定标题：*Measured, not assumed: information reconciliation for arrival-time
  HD-QKD on real SPDC data*。
- 主张全部落在"测量"上：(1) 真实信道测量；(2) 用标准码测得的协调成本；
  (3) 理论预测与实测的对照；(4) 给实验者的实践建议。
- **不声称**：新码、"首次"、"理论错了"（R17）。
- 时延不对称解读（R17）：标准抖动模型 + 残余时延偏移 μ，一阶定量解释观测结果，
  即 p ≈ E|Δ|/bw；未校准时约为 |μ|/bw，误差方向由 μ 的符号决定。
  偏移最可能来自旧对准流程的 100 ps 直方图分辨率（取 bin 中心，无插值），
  属流程量化误差，不是理论缺陷（A2 已确认，`A2_AUDIT.md`）。
- 可能真正需要补充理论模型的，是实测抖动形状与高斯的偏差：
  σ≈25 ps 时校准后预测 p≈0.10、实测 0.06；C-2 的 κ 比亦落在带外。待 B1 确认。
- 原 §0 中"核心论点：到达时间编码的高维协调本质上不是高维问题"等结构论述保留，
  但正文措辞须符合 R17（只写测到的东西 + 适用范围）。

## 修订 §1（替代原 §1 第 1、4 项内的一处措辞，其余保留）

- 第 3 项"真实数据上的系统对比"保留；凡涉及"首次""新码"字样的理解一律以 R17 为准：
  不声称首次在真实数据上做协调（Zhong 2015、Liu 2019 已做过），见修订 §7。
- 其余条目（信道刻画、结构感知协议、系统后果）不变。

## 修订 §7（替代原 §7）——文献定位（已核对，DOI 来自检索结果）

- Boutros & Soljanin, IEEE TCOM 2023 — 10.1109/tcomm.2023.3302135；arXiv 2301.00486
- Birnie, Cheng, Soljanin, IEEE TCOM 2023 — 10.1109/tcomm.2023.3244244；arXiv 2207.04146
- Brougham, Wildfeuer, Barnett, Gauthier, EPJ D 2016 — 10.1140/epjd/e2016-70357-4；arXiv 1506.04420
- Yang, Sarihan, Chang, Wong, Dolecek, Asilomar 2019 — 10.1109/ieeeconf44664.2019.9048898；arXiv 2001.00611
  （能量-时间纠缠 QKD 的信道统计与图码提案，必须引用并说明区别）
- Zhong et al., New J. Phys. 2015 — 10.1088/1367-2630/17/2/022002
- Liu et al., Appl. Phys. Lett. 2019 — 10.1063/1.5089784
- Mueller et al., Quantum Inf. Process. 2024 — 10.1007/s11128-024-04395-w
- Dolecek & Soljanin, IEEE BITS 2023（综述）— 10.1109/mbits.2023.3262237
- Morozov et al., IEEE Access 2025 — 10.1109/access.2025.3648803
- Kanitschar & Huber, Phys. Rev. Applied 2025（DOI 待核，不引用DOI，只列标题占位）
- Müller et al. 2023, ISTC — 10.1109/istc57237.2023.10273570（保留原条目）
- Lee, Park, Heo 2018, QIC — 10.26421/qic18.9-10-5；
  Kiktenko et al. 2021, IEEE Commun. Lett. — 10.1109/lcomm.2020.3021142
  （Polar 用于协调，保留原条目）

## 新增 R17（措辞规则，与 R1–R16 并列生效）

- R17：不写"首次"（Zhong 2015、Liu 2019 已在真实数据上做过协调）；
  不写"理论错误"（时延不对称按"标准抖动模型 + 残余偏移 μ"解读）；
  结论句只写测到的东西 + 适用范围（重申 R9）。
