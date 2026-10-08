# C-2 拟合包（冻结，2026-10-08）

> Track：EXPLORE（只用已落盘统计量：Z-2 `z2_summary.json` 30 格 + C-0 `c0_summary.json`；
> 不读 `D:/Data`，不跑解码器）。设计见 `C2_DESIGN.md`（§1 公式、§2 估计量、§3 验证、§4 边界）。
> 注意：C-0 数字在独立 Pre-RESULT PASS 前为暂定；若 Pre-RESULT FAIL，
> 主线程会发返工信号，本包 C-0 相关部分以返工后数字为准（拟合集切分与方法不变）。

## 1. 冻结输入（只读）
- `workspace/z2_reframe/z2_20261008/z2_summary.json`（30 格：6 源 × bw{50,100,200,400,6400}）
- `workspace/c0_delayscan/c0_20261008/c0_summary.json`（495 行：δ–p 曲线 + 重配对对照）
- `docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/G1_TERNARY.md`（三值锚点）
- 公式实现自写（高斯 Φ 用 `math.erf`，禁新增重型依赖；`numpy` 可用）。

## 2. 文件范围
- 新建：`comparison_bench/src/comparison_bench/formal_ir/msd_c2_fit.py`
- 新建：`comparison_bench/tests/test_c2_fit.py`（T0/T1：无条件式退化检查——δ=0
  对称性 P₊₁=P₋₁、bw→∞ p→floor、大σ极限行为、A(a)数值微分自洽；合成小算例拟合回收）
- 机器根：`workspace/c2_fit/c2_20261008/`（拟合 JSON + 图表数据 CSV，不存大图二进制则附 CSV）
- 单一 append-only 日志：`docs/research_cycles/C-BATCH/C2_LOG.md`
  （尝试、修正、最终证据；修一次则同日志保留失败尝试）。
- 禁区：`D:/Data`、冻结基线、已有 outputs；不得改动 C-0/Z-2 产物。

## 3. 冻结拟合（与 C2_DESIGN.md §2–§3 一致，数值如下游执行填实）
1. 每源独立：估计量A（p200+p400 联立 → σ̂A,δ̂A，6400 holdout）、估计量B
   （H(e) 拟合 → σ̂B,δ̂B；H 由落盘 top_errors 分布重算，方法写死）、
   估计量C（p+H 联合加权 → 报告值）。
2. 一致性 T1–T4（α=0.05）：σ一致性z、χ²/dof、δ符号检验、熵闭合t；
   任一失败该源不跨源合并，只报分源值+失败项。
3. 分层验证：非宽窗层（18 格）RMSE/MAE/平均相对误差/最大残差/χ²/dof + 熵RMSE；
   宽窗层（12 格）同样指标单独列表 + support_pred vs 9/5 对照 + 尾质量数量级对照
   （只报告不设门）；6400 holdout残差 + ε_acc 估计。
4. floor 分支：先报"无floor纯高斯残差"（拒绝证据）；按 §1.7判别 (i)/(ii)，
   至多一次预注册修正（同一日志保留失败尝试，科学输入/假设不变则允许重跑一次）。
5. C-0 δ 维度检验（σ̂C 冻结、无新自由参数）：最优点 Δδ*（参考线 min(10ps,0.1·bw)）、
   曲率比 κ_obs/κ_pred（参考带 0.7–1.3）+ 曲线RMSE、方向单调性；
   宽窗不适用（C-0 只有 bw200/400 非宽窗，直接注明）。

## 4. 通过参考（设计建议，非已验证结论）
非宽窗 RMSE<0.005 且平均相对误差<5% 且 χ²/dof<3 → "core-consistent"；
否则走 floor/重尾分支，不得放宽门限。宽窗无通过线。

## 5. 验收 ID
- C2-FIT-01：每源 (σ̂A,δ̂A)/(σ̂B,δ̂B)/(σ̂C,δ̂C) + T1–T4 表。
- C2-VALID-01：分层指标表 + holdout + 宽窗外报表。
- C2-DELTA-01：C-0 δ检验三项（最优点/曲率/方向）。
- C2-LOG-01：单一日志完整（尝试、修正如有、最终证据、claim上限声明）。
- C2-CLEAN-01：`git status` 仅本包新增；冻结目录零 diff。

## 6. 返回条件（二选一）
完成：逐 ID 报命令与结果（含拟合表关键行；失败计数不适用——拟合无失败计数，
χ²/残差如实报数）；或阻塞：失败命令、traceback、已试补救、需主线程的一个决定。
结论上限：只报"模型与实测的吻合程度"分层结果；不得声称 FER/SKR/路线 qualified。
