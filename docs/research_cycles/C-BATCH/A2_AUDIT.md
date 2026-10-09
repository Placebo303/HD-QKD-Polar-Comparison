# A2 对准代码审计（只读 + 合成复现，2026-10-09）

> Track：实现/EXPLORE（只读冻结基线 + 合成时间戳复现；未读 `D:/Data`，未跑解码器）。
> 任务包 `docs/SOFTWARE_NOW_20261009.md` A2。

## 1. 代码事实（只读，均已现场打开）

- 对准直方图分辨率 **100 ps**（写死）：
  `comparison_bench/src/comparison_bench/io/align_wrapper.py:41`
  `ALIGN_BIN_WIDTH_PS = 100`，`ALIGN_MAX_LAG_PS = 819200`（16384 bins）。
  调用的是冻结函数 `src/qkd_io/ttbin_pipeline.py:252`
  `compute_cross_correlation_histogram`，未改动（`git status` 冻结目录零 diff）。
- 取 **bin 中心**，无插值、无抛物线拟合：
  `src/qkd_io/ttbin_pipeline.py:310`
  `centers = (edges[:-1] + edges[1:]) / 2.0`；
  `align_wrapper.py:99-105` `pk = argmax(counts)`，
  `offset_ps_derived = round(peak_center)`。注释第 13 行明文"No interpolation;
  bin centre only"。
- 符号约定：lag = t_B − t_A（`ttbin_pipeline.py:264/321`），offset **加到 A 侧**
  （`_pair_nearest_unique` 第 223 行 `a + offset_ps`；`align_wrapper.py:11-12` 注释一致），
  故 `offset = +peak_center`。
- R1/M0 对准路径：`m0_realframe_runner.py:85-86`（CH_A=1、CH_B=5、窗 200 ps）→
  `aw.derive_alignment(...)` → `require_alignment_passed` 门控（blocked 永不 fallback，
  `align_wrapper.py:213-228`）。Z-2/C-0/B123 均走同一路径。
- 量化界：真残余 μ 落在某 100 ps bin 内，估计只能取该 bin 中心 → 残差
  `resid = μ − centre ∈ [−50, +50] ps`。这是流程量化误差，不是理论缺陷。

## 2. 合成复现（已知 μ、σ，种子 20261009）

- 脚本：`comparison_bench/src/comparison_bench/formal_ir/msd_a2_align_audit.py`
  （新建，加法；与冻结直方图同边约定 `arange(-819200, +819200, 100)`）。
- 命令：
  `python -m comparison_bench.src.comparison_bench.formal_ir.msd_a2_align_audit
  --output-root workspace/swnow_20261009/a2_20261009`
- 结果（σ=25 ps，n=200k/格，`a2_repro.json`）：

| μ_true | offset（bin 中心） | 残差 |
|---|---|---|
| +1 ps | +50 ps | **−49 ps** |
| +37 ps | +50 ps | −13 ps |
| −73 ps | −50 ps | −23 ps |

- 符号检查：μ_true=+40 → offset=+50，A 侧修正后 lag 均值 −10.03 ps（|·|≤50，ok）。
- 初版脚本曾误用 1 ps 步长（`arange` 缺 step），残差只剩 ±1–2 ps；
  修正为 100 ps 步长后复现出 −49 ps（失败尝试保留在此，同日志）。

## 3. 审计结论

- **±50 ps 的来源确认**：旧对准流程 100 ps 直方图取 bin 中心、无插值，
  量化残差天然落在 ±50 ps 内；C-0 实测 δ*≈∓50 ps 正好是该量化界的边界值，
  方向与 offset 符号 6/6 对应（`C0_RESULT.md` §4）。
- 时延不对称解读（R17 措辞）：标准抖动模型 + 残余偏移 μ，
  p ≈ E|Δ|/bw，未校准时约 |μ|/bw（|μ|=50、bw=200 → 0.25，与标称 p≈0.24 一致）。
- 未改冻结基线：`git diff -- src/ experiments/ tools/` 为空（批末审查复核）。
