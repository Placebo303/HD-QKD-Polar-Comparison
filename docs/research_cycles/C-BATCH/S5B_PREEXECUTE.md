# S-5b Pre-EXECUTE — U 定义确认与 |e|≥2 率（DECIDE，零解码）

> Track: DECIDE（读已存原始 ttbin；零解码，只统计）。
> 授权：S-5 任务包（用户 2026-10-09 原话；S-5b 为其中一部分），仍先写本
> Pre-EXECUTE，事后做独立 Pre-RESULT。
> 背景：S-4d 的 U（okA 且 level-B ok 但 exact 失败）分源为 6–22/44/5/4，
> 规划 session 要求先确认 U 是否即含 |e|≥2 事件的块，并与 C-0 尾部质量对照。
> 上位：R1–R17。

## 1. 冻结输入（5 源，与 S-4d 同源：T2 三段 base + 0/4dB `.1`）

路径见 `B123_PREEXECUTE.md` §1（不复列）。

## 2. 冻结设计（与 S-4d 同链；无译码；U 定义 zero-decode 验证）

- 冻结链：`read_ttbin_events` → 对准门控（blocked 记 blocked）→ 标称配对 →
  `_frame_global`（span 204800，bw=200，d=1024）→ 校准位移 `pb+δ*`
  （δ* 与 S-4d 同值）→ kept 对 → N=4096 按时间切块。
- 统计（每源）：
  1. 每符号 |e_fold|≥2 率（e 对称折叠后），与 C-0 top_errors 尾质量对照。
  2. 含宽事件块数（块内 ≥1 个 |e|≥2）vs S-4d 落盘 U 计数（soft/plain 格）：
     量级一致（±50% 内）即确认 U 定义；偏离则另查。
  3. 窄子集（|e|≤1）重建闭合率（应 ≈1，S-4a 已见 1.0；复核）。
- R1：计数 CI（二项精确区间）随表附 n。

## 3. 冻结命令

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s5b_udef --full --output-root workspace/s5_udef/s5b_20261009
```

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s5b_udef --self-test
```

## 4. 预算与墙钟

- 预算 **3600 s（1 h）**。依据：S-4a 同链 8 源 1373 s；本任务 5 源更轻，
  预计 < 15 min。
- 输出根 `workspace/s5_udef/s5b_20261009`：执行前验证不存在。

## 5. 检查单

- [x] 用户 S-5 任务包授权（含 S-5b 确认 U 定义）
- [x] 代码 + 自检通过；统计项仅宽事件率/块数对照/窄闭合（+n、CI）
- [x] 输出根验空；分支正确；冻结基线未动（加法脚本）
- [ ] 跑后独立 Pre-RESULT（S5B_ACCEPTANCE.md，独立线程）

## 6. 结论上限

只确认 U 定义 + 量化宽事件率；修法选择由合成验证另行给出，不在本包声称。
