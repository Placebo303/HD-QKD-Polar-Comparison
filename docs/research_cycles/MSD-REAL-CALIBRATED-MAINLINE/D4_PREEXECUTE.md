# D-4 Pre-EXECUTE — 0 dB 干净 OOS 仲裁（DECIDE，用户已附条件批准，条件满足即生效）

> 先验只用 R1 训练；0 dB 段（266638 对，SER 0.248，偏移 −50）只作测试。

## 冻结先验源（看 0dB 结果前写死）
- **T2-1M TRAIN only**。理由（零解码距离，用 P-d 已存计数，无新读取）：
  0dB-vs-1M 差分 KL = 0.0003（形状一致），vs-1.5M/2M = 1.32/1.29（形状不同）；
  同时间偏移（−50 ps）；SER 同量级（0.248 vs 0.238）。
- 不用 1.5M/2M（形状已知不同，P-b KL~1.23）；不合并（会稀释匹配形状）。
- 偏差登记：0dB-1M 差分 KL 0.0003（仅作偏差记录，不得用于调参）。

## 冻结设计
- NB 完整符号链：u1 五面 SPC-10 + K16（链式条件，T2-1M TRAIN 先验），
  u2 m=224 base + 232 rescue（S-3'''最优点 fresh 构建；0dB SER≈R1，沿用 m，
  假设已声明），完整符号口径（R11）。
- 两臂：修正差分主臂（T2-1M 拟合，D-3 NB 0/100，upper 3.7%）+ plug-in 对照臂。
- 输入：0dB 段超帧（~260 × 1024，冻结 M5 式分帧配对）；先验/bundle 全 T2-1M 派生。
- 输出根（验空后建）：`workspace/d4_oos/d4_20261007/`。
- 冻结命令：
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3prime_u1chain --oos --proxy-root workspace/s1_proxy/s1_20261006 --output-root workspace/d4_oos/d4_20261007
```

## 一致带（代理预测）
- D-3 物理代理 corrected-diff NB：0/100（upper 3.7%）；plug-in 23/100。
- S-5 R1 真实类比：FER 3–5%，f 1.6–1.9。0dB 预测：FER 0–5%，f ~1.6–1.9。

## 预算与门
- 预算 **3600 s**（池已根治：260×2 臂 × ~8 s / 12 ≈ 6 min + 加载/构建 ≈ 15 min）。
- 门 **G-1a（三源...单源 f ≤ 1.55）**；G-1（1.40）保留为目标，不放宽。

## 检查单（执行前）
- [x] 用户明确确认本 Pre-EXECUTE（附条件批准，条件满足）
- [x] 执行代码扩展 + 接线测试（合成数组）
- [ ] 输出根验空；分支/树干净
- [ ] 跑后独立 Pre-RESULT（R13：u1+u2 覆盖）
