# Prompt — D7-C heavy readiness with D7-B interface-proposal prerequisite

当前 D7-B early-exit audit 已完成。按顺序完整读取并执行：

1. `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
2. `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_A1_TASK_PACKET.md`

A1 增加一个必须先完成的 Phase P；冲突处以 A1 为准，其余 R1 全部有效。

启动时核验 HEAD 包含 `212f69ba`，审计 verdict 为
`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`，主终类为
`D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`。先冻结并独立评审
`D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`，不得实现修复。只有取得
`D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING` 才继续 D7-C。

随后长期自主执行原重型包：D7-C OpenSpec/prereg、128-call matrix、runner/verifier、
C01–C20、回归、独立 implementation review、真实 WSL Pre-EXECUTE 和 scoped local
commits。不要按小步骤回来；仅在 A1-01–A1-10 + H01–H20 完成或硬 STOP 时返回。

D7-C 必须直接从 accepted joint model 定义四种单层 priors，严禁把 decoder
`final_beliefs` 喂给另一层。iteration-0/current belief 只能标
`PRIOR_ONLY_CURRENT_BELIEF`，不能叫 posterior/APP。接口实现仍 deferred，且在未来
sequential/alternating/joint route 前必须另行完成。

本任务仍不授权 D7-C scientific run，不读取真实 Model-F 内容，不调用 production
decoder，不生成 UUID，不翻授权；禁止 R1d、`--phase`、G1/G2、CAL/VAL/real/raw/VOID。
所有环境探针分步，逐路径 stage，本地 commit，不 push；包外脏树和 SOP/workbuddy
管理改动不得进入提交。

PASS 后停在 `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`。按 A1.6
及 R1 §12 仅报 delta，并使用 R1 的精确结束句。
