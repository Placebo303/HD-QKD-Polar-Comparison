# F-1 Pre-EXECUTE — NB 完整符号链 E-2 工作点真实检验（DECIDE，用户已授权）

## 冻结先验源（看结果前写死）
- **T2-1M TRAIN only**。理由（零解码，用 P-d 已存计数）：4dB-vs-1M 差分 KL=0.0
  （形状一致），vs-1.5M/2M = 1.27/1.24；同偏移（4dB 段 −50 ps，既有表征）；
  SER 同量级（0.238 vs R1 0.238）。不用另两源（形状已知不同）；不合并。
- 偏差登记：4dB-1M 差分 KL 0.0（仅记录，不调参）。

## 冻结设计
- NB 完整符号链：u2 **A208 m200 base + 208 rescue（冻结 P1S1-R1 构建）**
  + corrected-diff bundle（T2-1M，修正尺度）+ plug-in 对照臂；
  u1 五面 SPC-10 + K16（链式条件，T2-1M 先验）；完整符号口径（R11）。
- 主测：4dB 段 112 超帧（115390 对，干净 OOS，从未用过）。
- 附测：0dB 段 260 超帧，标注"再检验"（D-4 已跑过 NB 链；本次为 E-2 工作点复测）。
- 输出根（验空后建）：`workspace/f1_oos/f1_20261007/`。
- 冻结命令：
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3prime_u1chain --f1 --proxy-root workspace/s1_proxy/s1_20261006 --output-root workspace/f1_oos/f1_20261007
```

## 一致带（代理预测）
- E-2 物理...代理（E-2 模块，diff 信道）：B=300 0 失败，f 点 1.379，upper 1.521。
- D-4 0dB 真实（m224 工作点）：主 f=1.537。E-2 降码率（m200/208）名义更低。
- 4dB 预测：FER 0–4%，f ~1.4–1.7（点）。

## 门、预算与上界声明
- 门：**G-1（f ≤ 1.40）按点估计记录**；G-1a 同时报点估计和上界。
- 事先声明：112 块全成功时 FER 上界约 3.2%（Wilson），f 上界会偏宽（预计 ~1.9）。
- 墙钟 ≤ 3600 s（池化；112+260 块 × ~8 s / 12 ≈ 5 min + 加载 ≈ 12 min）；只跑一次。

## 检查单（执行前）
- [x] 用户明确授权 F-1（含 4dB 主测 + 0dB 附测 + 门规则）
- [ ] 执行代码扩展（--f1）+ 接线测试（合成数组）
- [ ] 输出根验空；分支/树干净（执行前提交冻结代码）
- [ ] 跑后独立 Pre-RESULT（R13：u1+u2 覆盖）
