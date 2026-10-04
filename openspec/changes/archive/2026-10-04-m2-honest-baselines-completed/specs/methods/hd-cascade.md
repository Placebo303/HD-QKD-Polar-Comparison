# Spec delta: methods/hd-cascade (new contract only)

本文件为新增契约，不改 `openspec/specs/` 任何现有文件。

## S-HDC-01: 身份与增量边界

- `hd-cascade` SHALL 为 HD-Cascade 方法契约（Müller 2024 三改，并行版优先），增量起于 `comparison_bench/src/comparison_bench/methods/cascade_lite.py` 与 `comparison_bench/src/comparison_bench/methods/cascade/single_kernel.py`，只增不改既有逻辑/接口。
- SHALL NOT 预设 FER 胜负；SHALL NOT 改 schema/列名/键名/CLI/输出文件名（AGENTS §5.3）。

## S-HDC-02: 映射与块长

- 10-bit 符号 SHALL 经 Gray 映射（无原文依据，永标 assumed；原文为 map appropriate binary，见 `design.md` §2 表①行）后按位面分组进入 Cascade 块；块长表 SHALL 按位面分组冻结（表结构：位面 × pass → 初始块长/增长规则/封顶；真值 = QBER-自适应 k1..k6 公式，n=2^16 bits，见 `design.md` §2 表②行）。
- 剩余歧义（B3 + App 剩余）SHALL 标"待澄清表"经 `/opsx-explore` 冻结，SHALL NOT 猜数实现。

## S-HDC-03: 会计（A-CMPE-1..4）

- per-source 四计数 SHALL 独立（`attempted` / `exact_match`=success / `accepted` / `accepted_wrong`=undetected）；`undetected` SHALL NOT 并入 success/FER。
- `f_super` 与 `f_eff`（本臂 m 基）SHALL 双数并列。
- `leak_EC` + 64-bit tag + 控制轮次 SHALL 分列 ⇒ verification-aware `λ_total`。
- wall（总/每块/每译码）+ 峰值 RSS + 每帧交互消息数（Müller 446 口径）SHALL 报告。
