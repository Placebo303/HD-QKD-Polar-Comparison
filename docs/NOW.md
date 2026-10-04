# NOW — 当前入口（2026-10-05）

先完整阅读 [唯一交接权威](REBOOT_HANDOFF_20261004.md)、[AGENTS](../AGENTS.md) 和本页；现场重测分支、HEAD、git status。本页是导航摘要，不替代交接规则或执行授权。

- 当前工作：S1–S8 仓库整理已完成；工程验证与实际提交记录见组织归档。
- 项目关闭 Ponytail，委派使用 luna_worker；本仓是 formal IR/LDPC 研究主线，姊妹 Polar 仓库只读，不合并。
- 主度量已裁决为带期望良率的 f；严格遵守交接 R1–R9。口径及泄漏/tag/失败惩罚、单位和独立复算要求见 §2 R3/R5、§4 D-1。
- GF32 128 符号单旋钮探针线已正式停止。其他按第四处置归档的历史项只是目前不推进；每项原因、已知状态和缺失记录见各 archive.md。这不表示永久放弃或科学 KILL。
- 历史结论仍限于原始已测范围。移动、归档、import/collection smoke 都不增加科学接受或授权。

阅读 [INDEX](INDEX.md) 查现行入口；[PATH_MAP](archive/PATH_MAP.md) 查旧/新路径；[隔离清单](archive/QUARANTINE_MANIFEST.md) 查保留待决定的未跟踪杂项。

当前 session 状态、实现边界、失败留存及可粘贴启动提示词见 [2026-10-05 续接交接](SESSION_HANDOFF_20261005_MSD_P2.md)；它是导航补充，不替代唯一 reboot 交接权威。

续推检查点（2026-10-05）：本对话曾设置 03:50:10 额度恢复后续跑、04:10–06:10 每20分钟续推。用户随后已自行重置并取消自动兑换，卡辅助任务已停用；06:32:10 任务仅继续研究。MSD 的 C1–C6 sparse accumulator 候选及 D/E 精确先验机制已通过各自固定测试与独立限定审查，I1–I3 连接测试从额度中断处恢复；尚未接受逐层码率或生产解码。后继先读单日志最新记录，不能只按旧 session 交接快照重做。workspace 中保留的卡 helper 不再授权执行。

现行组织规则见 [repository-organization](../openspec/specs/repository-organization/spec.md)。历史 OpenSpec 原文件及处置记录在 openspec/changes/archive/，无 delta 处置的旧条款必须经后继明确采纳才可恢复为现行。

2026-10-05 用户授权按 P1→P2/P3→P4 持续推进。P1 已完成已有 R1 TRAIN 联合直方图的零译码条件熵/预算核对和独立复算，见 [结果](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/RESULT.md)。CQ 原根仅保存摘要，不能重建全量联合计数。未启动解码、DE、新 raw、资格化或发表；真实帧具体墙钟预算须在其 DECIDE 运行前落实。

P2 条件软先验、syndrome 接口与稀疏 accumulator 结构候选已通过数学测试和独立限定审查；生产 backend 尚未构造或执行。自然二进制 LSB-first 条件处理及正态模型分配已完成限定核对，实用逐层码率仍未接受，主线短块的完整符号配对对照口径尚待落实；现有长块结构候选尚无实用码隙/性能接受。[P1 表](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P1_TABLE.md) 仅为 TRAIN/正态近似假设场景，实用码隙和 OOS FER 未测。解码写包前的 [功效算术](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P2_POWER.json) 已独立复算，但实际样本与成本仍待落实；并行 P3 内核候选尚未启用或测得加速。科学接受、具体成本和运行预算随阶段冻结，证据见同一路线 [日志](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/EXPLORATION_LOG.md)。

D1–D4 整层精确零误差先验旁路已通过固定 fake 测试和独立只读审查，主线程仅接受该模型/接口行为。它默认关闭，仍校验 syndrome 并计全部已发送行；不增加 OOS、verified success 或效率证据。此前卡 helper 的准备已被用户手动重置及取消自动兑换的指令取代，不得执行。

组织实施及验证记录见 [组织归档](../openspec/changes/archive/2026-10-04-reboot-repository-organization-20261004-completed/archive.md)。整理的八个提交已普通 push，远端核对为 8f2f313a；后续 push 另需确认。

额度续推（2026-10-05）：用户已手动重置并明确取消自动兑换。Windows 一次性卡任务 Codex-ResetCard-20261005-0630-4973b0ac 已现场停用为 Disabled，consume_0630_attempt.log 不存在；本对话没有发出消费请求。06:32:10 对话任务已改为仅续推研究，不执行任何卡 helper/consume。不得再次启用该卡任务、换卡或购买。现场额度查询确认 ordinaryUsageAllowed=true，原指定到期卡已不在可用列表。I1–I3 测试文件在额度中断前已写入但未运行，由同一 Luna 从实际文件状态恢复。

E1–E5 部分精确零误差变量条件化已通过固定 fake 测试与独立只读审查，主线程仅接受标准 prior builder 下的模型/接口范围。失败测试尝试与只改期望的修正均留在单日志。后继 I1–I3 也已完成；生产 backend、实验及逐层实用码率仍未接受。

I1–I3 已完成并由独立只读审查接受其固定代数连接范围：完整1024字母表、长块CSR、两种先验处理和首级冲突停止。它不增加信道、FER、实用码率或性能证据。后继 J/K 的模型算术及接口核对见下，禁止据此推断生产解码收益。

J1–J5 已完成 TRAIN 摘要下的连续正态错误预算分配及每个数字/显示表格的独立复算，整数取整/裁剪另列；[新表](research_cycles/MSD-REAL-CALIBRATED-MAINLINE/ERROR_ALLOCATION_TABLE.md) 仅接受模型算术。K1–K3 已修正两处尾分位数的补数消减并通过固定测试/独立增量审查，没有重跑或改写旧 J 产物。历史预算来自 O1 synthetic genie-u1 单层结果，不能作为实测完整符号对照；下一步落实完整两层重构、实际 tag 验证、失败与 accepted-wrong 的同块口径以及样本/成本可行性。实用码隙和真实 f 增益仍未知，不据此声称超越真实基线。

后继只读库存核对已记录在同一日志：v28 receiver 的完整 Bob/实际前缀编排可复用，现有 runner 的输出 digest 自核对不能代替独立 sender tag 验证。R1 历史角色按 acquisition frame index 划分，不能把维度参数当 reconciliation block 长度，也不能证明角色后来未使用。主线程计划同一家族的 MSD 短/长块完整符号对照，显式计 native tag 与部分保留；该方案尚不是 decoder packet。下一步可推进固定 fake 的 outcome 账本实现；当前完整配对库存、码率/degree、实际 cost 与执行预算仍待落实。

L1–L5 原生块 outcome/期望良率账本已通过固定 fake 测试与独立只读审查，主线程仅接受数学口径：独立 sender reference、accepted-wrong 隔离、实际 tag/泄漏和逐块加权失败惩罚、同体量/熵分母配对。首次导入失败及唯一修正均保留。下一步冻结当前角色 metadata 库存范围及新的共同体量功效/成本口径；旧 P2_POWER 的同长度/共享 tag 数量不能直接用于短长块方案。未读取新的真实数据或执行解码。
