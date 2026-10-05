# M2 EXPLORE packet — plane-0 targeted incremental disclosure（2026-10-05）

> Track: **EXPLORE**（合成、已批准 TRAIN 聚合输入、加法结果根、有界、无资格/发表声称）。
> 授权：用户持续推进授权（M1 批）＋「往下推进…直接进行」。真帧/新 raw/发表/push 不在本包。
> 上位：AGENTS.md §1.2、R1–R9、ROADMAP §2-M2。单日志 EXPLORATION_LOG.md（M2 条目）。
> 结果根（唯一）：`workspace/m2_synthetic/m2_20261005/`。Seeds：M1′b seeds +5000
> （合成语境下的 disjoint 轮数标定流；DECIDE 级样本外在 M4/M5）。

## R1–R9 本包满足方式

- **R1**：目标效应 = rescue 后 f 比 M1′b operating（1.262–1.274）下降 ≥0.02。
  MDE：B=300，base FER~0.02–0.27 → 失败数 7–80，rescue 率 ±10–35%；
  最终 FER~0 → f 精度由 Wilson 上界给（~+0.14 保守），point 差 ≥0.02 即判分辨。
- **R2**：一句话——把 kept·p_fail 惩罚换成少量 rescue 披露，实测 M2 的 f 增益，
  决定 M4 冻结设计是否采用增量结构；这是 P-3 推导（FER 1% ↔ Δf 0.11）的直接兑现。
- **R2 信道**：同 M1′b（TRAIN plug-in i.i.d. 符号抽样），不读 VAL/HOLD/raw/真帧。
- **R3**：`f = (E[L] + tag + (N·H_A − E[L])·FER_final) / (N·H(A|B))`，
  `E[L] = L_base + K·P(rescue)`，tag=64，H 取 P1 冻结行；undetected 单列永不并入。
- **R4**：rescue 不佳只说明该轮设计，不关闭 MSD/增量路线。
- **R5**：数字全由 runner 算出；结论性数字（各点 E[L]/f）由 m1_independent_recompute.py
  复算（已覆盖 E[L] 公式？——复算脚本只覆盖固定 L_EC！本包要求先扩展复算脚本支持
  E[L] 行再跑全量，顺序冻结：先改脚本+测试，后全量）。
- **R6**：无新 OpenSpec change；收尾给结论+下一步+收益+成本。
- **R7**：smoke（≤120 s，N=1024，6 块）先行定 s/块；全量上限 21600 s；
  N=16384 PEG 构建 ~180–290 s/点已在 M1′b 实测；逐块 JSONL 落盘。
- **R8**：scoped 提交，禁 add -A；不删文件；push 另需确认；仓库根无新增杂项。
- **R9**：只报测到的 rescue 率/E[L]/f+范围（TRAIN 标定合成）。

## 冻结设计（探针已测得，非假设）

- 仅 plane-0 增量，其余面冻结 M1′b operating（plane-1 PEG m_1、SPC g=64/256）。
- Base：N=16384 C_0 ∈ {1500, 2000}；N=1024 C_0=160。Backend：make_bp_decoder it200。
- Rescue 轮（失败才触发）：披露 Alice plane-0 在 K 个最弱先验位的真值
  （K 公开 bits），固定后重跑 base BP；单轮（探针：单轮全救，无需多轮）。
  K_1024=100（43/43）；K_16384=400（10/10，T2-2M/C_0=2000）。
- 探针否定项（保留）：免费 serial/minsum 重试 0/43；通用扩展行 +119 仅救 21%。
- 点：N=16384 3 源 × 2 base + N=1024 3 源 × 1 base = 9 点 × B=300 = 2700 块。
- 成功：rescue 后 f < M1′b operating 且 point 差 ≥0.02（至少一源一 N）。

## 冻结命令（qkd_env）

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental --smoke --output-root workspace/m2_synthetic/m2_20261005
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental --full --output-root workspace/m2_synthetic/m2_20261005
D:\software\Anaconda3\envs\qkd_env\python.exe docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/m1_independent_recompute.py --result-root workspace/m2_synthetic/m2_20261005 --summary m2_summary.json --output workspace/m2_synthetic/m2_20261005/independent.json
```

停规则：smoke 超 120 s → 降 B；全量投影超 21600 s → 先砍 N=16384 C_0=1500 臂。
一次工程修正额度：runner 崩溃/落盘类，科学输入/seed/阈值不变，失败保留同日志。
