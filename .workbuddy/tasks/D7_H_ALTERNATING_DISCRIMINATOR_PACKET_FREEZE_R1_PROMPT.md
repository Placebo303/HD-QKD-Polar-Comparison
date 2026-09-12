# D7-H Alternating Discriminator Packet Freeze R1 Prompt

在 `HD-QKD_Polar_Comparison`、分支 `formal-ir-v72p1-addendum-clean` 执行：

`.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_TASK_PACKET.md`
> R1A1 revision (authority: `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md` §2): 本对的 R1A1 修正与修正后冻结的提交由该包授权；本冻结自身不 commit。

本任务只做 docs-only 的 D7-H **任务包冻结**，不做实现、不授权、不执行。完成：
冻结任务包与 prompt、cycle 目录
`docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/`、
OpenSpec change `v72p2d7-alternating-discriminator`，并在 D7-G
`cycle_state.yaml` 追加一行 next_gate/status linkage。结束态必须是
`D7_H_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`。

冻结的科学范围：在已认证的 D7-G `CHECK_EXTRINSIC` 合同上，预注册**最小**
交替跨层判别器——冷启动，一次前向 code-extrinsic 传递，再一次后向传递
（这是被现有已接受合同唯一确定的最小 schedule：D7-E/F 明确将 >2-stage
alternating 阻塞至 cavity/extrinsic 合同出现，D7-G 已提供该合同）。后向
prior 只能由 L2 的 code-factor extrinsic 构造，**禁止 posterior 回传**；
iteration-0 与 warm-start 一律 fail closed。

硬边界：不得调用 decoder，不得读 Model-F/CAL/VAL/real/raw/VOID，不得运行
synthetic/formal/real 实验，不得产生结果或 promotion，不得生成 D7-H root/
UUID，不得修改冻结基线 `src/`、`experiments/`、`tools/`，本冻结自身不得 commit/push/
清理脏树（修正后冻结的提交由 R1A1 包 Phase A 授权），不得在清单外增删文件。所有执行授权字段保持 false；不得从本次冻结
推断未来执行授权。

STOP 规则：若任一候选文件已存在、与无关脏改动重叠、或已接受的 D7-G 合同
无法唯一确定最小 schedule，则在写入前停止并只返回一个精确 blocker。

返回：仅 delta。列出改动文件、冻结 schedule 及其推导、冻结的 label/terminal/
budget 集、候选路径缺失与无越界写入的证据、所有授权仍为 false 且无 D7-H root/
identifier、残余数学限制、以及下一个 gate（`D7_H_IMPLEMENTATION_PENDING`，
未授权）。
