# NOW — 当前入口（2026-10-05）

先完整阅读 [唯一交接权威](REBOOT_HANDOFF_20261004.md)、[AGENTS](../AGENTS.md) 和本页；现场重测分支、HEAD、git status。本页是导航摘要，不替代交接规则或执行授权。

- 当前工作：S1–S8 仓库整理已完成；工程验证与实际提交记录见组织归档。
- 项目关闭 Ponytail，委派使用 luna_worker；本仓是 formal IR/LDPC 研究主线，姊妹 Polar 仓库只读，不合并。
- 主度量已裁决为带期望良率的 f；严格遵守交接 R1–R9。口径及泄漏/tag/失败惩罚、单位和独立复算要求见 §2 R3/R5、§4 D-1。
- GF32 128 符号单旋钮探针线已正式停止。其他按第四处置归档的历史项只是目前不推进；每项原因、已知状态和缺失记录见各 archive.md。这不表示永久放弃或科学 KILL。
- 历史结论仍限于原始已测范围。移动、归档、import/collection smoke 都不增加科学接受或授权。

阅读 [INDEX](INDEX.md) 查现行入口；[PATH_MAP](archive/PATH_MAP.md) 查旧/新路径；[隔离清单](archive/QUARANTINE_MANIFEST.md) 查保留待决定的未跟踪杂项。

当前 session 状态、实现边界、失败留存及可粘贴启动提示词见 [2026-10-05 续接交接](SESSION_HANDOFF_20261005_MSD_P2.md)；它是导航补充，不替代唯一 reboot 交接权威。

续推检查点（2026-10-05）：用户要求立即继续及额度恢复后的定时续跑；已设置本对话 03:50:10 续跑、04:10–06:10 每20分钟续推、06:30 处理最早到期卡。五小时额度恢复已由现场读数确认，工作持续推进。MSD 的 C1–C6 sparse accumulator 候选已通过结构测试与独立限定审查；尚未接受逐层码率或生产解码。后继先读单日志最新记录，不能只按旧 session 交接快照重做。重置卡 helper 另在 workspace 中准备，须指定卡资源/时间窗口核对，CLI 协议不暴露账户ID，不应声称核对了该字段；不能提前或换卡消费，定时配置不等于已兑换成功。

现行组织规则见 [repository-organization](../openspec/specs/repository-organization/spec.md)。历史 OpenSpec 原文件及处置记录在 openspec/changes/archive/，无 delta 处置的旧条款必须经后继明确采纳才可恢复为现行。

2026-10-05 用户授权按 P1→P2/P3→P4 持续推进。P1 已完成已有 R1 TRAIN 联合直方图的零译码条件熵/预算核对和独立复算，见 [结果](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/RESULT.md)。CQ 原根仅保存摘要，不能重建全量联合计数。未启动解码、DE、新 raw、资格化或发表；真实帧具体墙钟预算须在其 DECIDE 运行前落实。

P2 条件软先验、syndrome 接口与稀疏 accumulator 结构候选已通过数学测试和独立限定审查；生产 backend 尚未构造或执行。下一步冻结自然二进制 LSB-first 条件处理与逐层分配，保留主线短块为后续配对对照；现有长块结构候选尚无实用码隙/性能接受。[P1 表](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P1_TABLE.md) 仅为 TRAIN/正态近似假设场景，实用码隙和 OOS FER 未测。解码写包前的 [功效算术](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P2_POWER.json) 已独立复算，但实际样本与成本仍待落实；并行 P3 内核候选尚未启用或测得加速。科学接受、具体成本和运行预算随阶段冻结，证据见同一路线 [日志](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/EXPLORATION_LOG.md)。

D1–D4 整层精确零误差先验旁路已通过固定 fake 测试和独立只读审查，主线程仅接受该模型/接口行为。它默认关闭，仍校验 syndrome 并计全部已发送行；不增加 OOS、verified success 或效率证据。06:30 重置卡 helper 的只读核对和提前拒绝已通过，指定卡尚未消费；兑换结果须看当时日志。

组织实施及验证记录见 [组织归档](../openspec/changes/archive/2026-10-04-reboot-repository-organization-20261004-completed/archive.md)。整理的八个提交已普通 push，远端核对为 8f2f313a；后续 push 另需确认。

额度耗尽回退（2026-10-05）：06:30 指定卡兑换已注册 Windows 一次性任务 Codex-ResetCard-20261005-0630-4973b0ac，现场 NextRunTime 为 2026-10-05 06:30:00+08:00，Interactive/Limited、不保存密码、隐藏 PowerShell7、执行时限2分钟。动作是 workspace/reset_card_20261005/run_0630_reset.ps1，固定幂等 UUID 9988e116-e03b-4f52-9f94-825e3076e6ed，记录 consume_0630_attempt.log；它不需要模型生成。06:32:10 对话任务只核对该日志并续推，不另发消费请求。注册时日志不存在、尚未兑换。必须保持机器开机及当前用户登录；实际服务器资格/网络成功仍须当时结果确认，超时不能推断未消费。

E1–E5 部分精确零误差变量条件化已通过固定 fake 测试与独立只读审查，主线程仅接受标准 prior builder 下的模型/接口范围。失败测试尝试与只改期望的修正均留在单日志。I1–I3 全字母表/长块结构连接测试已冻结并进行中；生产 backend、实验及逐层实用码率仍未接受。
