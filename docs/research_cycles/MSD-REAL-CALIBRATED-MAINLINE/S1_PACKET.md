# S-1 EXPLORE packet — 失配感知合成代理 + G-0 校准门（2026-10-06）

> Track: **EXPLORE**（合成、已批准 TRAIN 聚合的再划分、无新数据源、有界、无资格/发表声称）。
> 授权：持续推进授权（S-1→S-4 明确在内）。G-0 校准靶子只用已有 M5 块级结果，不读新真实帧做靶子。
> 上位：R1–R13（R10 失配强制、R11 完整符号口径）。单日志 EXPLORATION_LOG.md。
> 结果根（唯一）：`workspace/s1_proxy/s1_20261006/`。

## R1–R13 本包满足方式

- **R1**：目标效应 = 代理上复现 M5 现象（MSD plane-1 大面积失败 + ≥1 valid-wrong；
  NB u2 FER 2.8–5.4% 量级；u1 残错 ~1/块）。G-0 是现象级门（存在性+量级），
  非精密测量；B=100/档（MSD N=16384）/100（NB N=1024），失败数≥5 即有分辨。
- **R2**：一句话——造出第一个"合成→真实可信"的代理，否则一切合成优化（S-2/S-3 码率）
  都可能在重复 M1 的 genie 乐观。这是 M0 以来合成→真实不可信的第一次正面修复。
- **R10**：信道与先验来自不同样本：Tier1 信道=TRAIN-a 直方图、先验=TRAIN-b 估计；
  Tier2 信道=全TRAIN、先验=1/8 子集（放大失配）。genie 对照（同表）仅标乐观上界。
- **R11**：所有臂按完整符号计成功/FER/f；NB 同时报告 u2 诊断列（禁入结论）。
- **R3**：统一 f（含 tag 64、kept 加权、undetected 隔离）+ valid-wrong 单列（syndrome
  通过但与真值不符，按面记录，永不计入成功）。
- **R4**：代理不复现 → 修代理，不做下游优化；不 KILL 任何路线。
- **R5**：数字全由 runner 算出；G-0  verdict 由独立复算脚本核对（现象计数 + f）。
- **R6/R8**：复用矩阵/先验/译码构建器；scoped 提交，禁 add -A；不删文件；不 push。
- **R7**：smoke（≤120 s，N=1024 MSD+NB 各 4 块）先行；全量上限 21600 s；逐块 JSONL。
- **R9**：只报测到的复现/未复现 + 范围（TRAIN 内再划分代理，非 OOS 证据）。

## 冻结设计

- TRAIN 按 acquisition frame 一分为二（manifest train_frames 区间中点）：TRAIN-a 前半、
  TRAIN-b 后半。重读 ttbin 用 M5 同款冻结链（仅 TRAIN 区，不碰 VAL/HOLD）。
- Tier1：信道=TRAIN-a plug-in 抽样，先验=TRAIN-b plug-in（nominal 失配）。
  Tier2：信道=全 TRAIN，先验=1/8 随机子集（frame 均匀子采样；放大失配）。
- 配置冻结 M5（MSD：plane-0 PEG m_0(C_0=2000 规则按**先验表**的 h 定)+K400 rescue，
  plane-1 m_1=600，SPC g=256，it200；NB：A208 R1/R2 + base/rescue，it300）。
  注意 m_0 按先验表 h 定（部署现实），不是按真信道 h——这正是失配的一部分。
- 点：T2-1M 试点先行（Tier1/Tier2 × MSD N=16384 B=100 + NB N=1024 B=60）；
  复现好再扩三源（G-0 判定后再定，不在本包全量内）。
- G-0 通过条件（三源展开后）：MSD plane-1 失败率显著高于同配置 genie 代理
  （≥5×）且 valid-wrong ≥1 事件；NB u2 FER 落在 2–6%（M5 的 2.8–5.4% 量级内）；
  u1 残错 0.5–1.5/块。任一条不满足 → 代理不可信，停。

## 冻结命令（qkd_env）

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy --build --output-root workspace/s1_proxy/s1_20261006
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy --smoke --output-root workspace/s1_proxy/s1_20261006
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy --full --output-root workspace/s1_proxy/s1_20261006
```

停规则：build 超时/断言失败 → 停（输入问题）；smoke 超 120 s → 降 B；全量投影超 cap → 先砍 Tier2。
一次工程修正额度（崩溃/落盘类，科学冻结不变）。
