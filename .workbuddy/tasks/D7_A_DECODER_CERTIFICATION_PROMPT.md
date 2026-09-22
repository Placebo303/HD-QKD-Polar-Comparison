# Prompt — D7-A GF32 decoder ground-truth certification

在仓库 `D:/Code/HD-QKD_Polar_Comparison`、分支
`formal-ir-v72p1-addendum-clean` 中执行完整任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_A_DECODER_CERTIFICATION_TASK_PACKET.md`

你是强执行模型，可自主完成包内 T0→T8：基线核验、OpenSpec/prereg、独立参考实现、
认证测试、数值归因、独立 correctness review、文档/记忆收口与 scoped local commits。
不要每完成一个小步骤就回来询问；只有命中硬 STOP、需要改变冻结科学要求，或完成全部
任务时才返回。返回只报 delta。

核心研究裁决：NB-LDPC 继续作为主线；D6 R1d 虽已冻结且 Pre-EXECUTE PASS，但现在
暂停为 `R1D_PAUSED_PENDING_DECODER_CERTIFICATION`，不得运行。当前任务只认证历史
GF32 row-layered FFT-QSPA 与 D5 L1→soft-APP→L2 接口。

必须严格遵守：

- 起始 HEAD 期望 `dfab1ed8`；提交存在性是 provenance，不是执行授权。
- 先完整读取任务包、`AGENTS.md`、`AGENT_PROJECT_MEMORY.md`、路线图 §12 和相关源码。
- 路线图现有 §12 是主线程已写但未提交的真内容改动；核对一致后按包白名单原样落地，
  不得用 broad clean/reset/checkout 处理脏树。
- 独立 reference 不得复用生产 GF32 派生表、FFT/permutation/check-update/
  syndrome-offset 逻辑；用 primitive polynomial 的独立 bitwise reduction 与直接枚举。
- tree 比 full posterior；loopy 比相同 row-layered recurrence 的逐 sweep 状态，绝不把
  有限轮 loopy BP 与 exact MAP 相等作为要求。
- 明确查清 `final_beliefs` 的数学表示；独立验证 `_run_layered_block` 中 softmax 与
  `app_fed_l2_prior`，重点排查已经归一化概率被再次 softmax、轴序或 Bob/U1 条件错误。
- 只允许 tiny synthetic in-memory correctness-unit calls；零正式/claim-bearing decoder，
  零 Model-F/CAL/VAL/real/raw/VOID 读取，零 `--phase`，零 R1d/G1/G2。
- 若发现任何 correctness mismatch，只完成最小反例、报告和独立 FAIL review；不要在
  同一任务顺手修历史 decoder，也不要继续下游性能归因。
- 只逐路径 stage，local commit，不 push；保护根不变、G2 absent、全部授权位 false。
- 已知 CRLF/包外脏树原样保留；scope 用显式 manifest 与 `git diff --numstat`，不要要求
  全局 porcelain 干净。

评审必须由未编写 reference 核的独立 reviewer context 完成，并真正查看源码、独立
重算代表性样本；不能只引用测试绿色。最终 verdict 只能取任务包 §5 T7 所列值之一。

若 PASS，只能推进到 `D7_B_EASY_REGIME_PACKET_FREEZE`，不执行 D7-B；若 FAIL，推进到
`D7_A_SCOPED_CORRECTNESS_REWORK_PROPOSAL`，不修复、不运行 R1d；若 BLOCKED，给出唯一
具体 blocker。按任务包 §8 汇报并使用对应的精确结束句。
