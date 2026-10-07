# Z-2 Pre-EXECUTE — (d, bw) 重分帧零解码统计（DECIDE，收尾指示已授权）

> 授权指针：用户 2026-10-08 收尾指示（`docs/CLOSEOUT_PLAN_20261008.md` §2 Z-2
> "DECIDE，用户已于本收尾指示中授权" + prompt 第 13 行"用户已在收尾指示中授权"）。
> M5 冻结链：`_pair_nearest_unique`（`window_ps=200`，即 `_m0.COIN_WINDOW_PS`）
> + `_frame_global` + `align_wrapper.require_alignment_passed`（与 S-5/D-4/F-1/G-3
> 同一调用序列；配对窗 200 ps，d=32 点配对窗不变）。

## 冻结输入（6 文件，变体写死）
- R1（2026.1.21，base 版，M0/M3C 先例）：
  `D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin`；
  `D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin`；
  `D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin`。
- 2026.1.23（.1 版，既有先例）：
  `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin`；
  `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin`；
  `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin`。

## 冻结设计
- bw ∈ {50, 100, 200, 400, 6400} ps，span 204800 ps → d ∈ {4096, 2048, 1024, 512, 32}。
- 宽窗规则（唯一定义）：符合窗（200 ps）大于 1 bin ⇒ `wide_window=true`。
  bw=50（bin 50 ps）与 bw=100（bin 100 ps）为宽窗；bw≥200（含 d=32，
  bin 6400 ps ≫ 窗）为非宽窗。d=32 点配对窗不变，只 bin 变宽。
- 每点：配对 + 零解码统计（误差支撑、p、p₋、lag-1、事件率、H(e)、H(A|B)）；
  只存计数 JSON，不解码。

## 公式（冻结口径）
- `H_e` = 经验误差分布熵；`H_AB` = 联合计数条件熵；`decomp` = h₂(p)+p·h₂(p−)，
  仅在支撑恰为 {0,±1} 时声称为闭合（宽窗行 decomp 为三值模型外推，不要求闭合）。
- d=4096/2048 熵估计欠采样声明：10dB d=4096 约 7.5 对/bin，只作描述性统计。

## 冻结命令
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_z2_reframe --full --output-root workspace/z2_reframe/z2_20261008
```

## 预算
- 预算 **3600 s**（30 点；实测总 wall 约 5 s计算 + 加载 ~10 min）。

## 检查单（执行前）
- [x] 用户在收尾指示中授权 Z-2（指针见顶）
- [x] 执行代码 + 接线测试（10dB bw200 p=0.229 vs G-1 p=0.23021，容差 ±0.002）
- [x] 输出根验空（运行前不存在）；分支干净（冻结提交见 git log）
- [ ] 跑后独立 Pre-RESULT（统计口径）

## 结论上限（绑定）
- 本产物只支持描述性零解码统计（支撑/p/p₋/lag-1/事件率/熵，宽窗行与欠采样
  点按声明降级）。不得由此直接得出 FER、协调效率、泄漏/净密钥、译码器选择、
  路线关闭或发表级 claim；此类结论需 Z-3 真实解码在其 DECIDE 门下另行给出。
