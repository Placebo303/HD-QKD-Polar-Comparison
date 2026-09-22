# D7-E Verify Provenance R18 Closeout A1 Prompt

在仓库 `HD-QKD_Polar_Comparison`、分支 `formal-ir-v72p1-addendum-clean` 中执行：

`.workbuddy/tasks/D7_E_VERIFY_PROVENANCE_R18_CLOSEOUT_A1_TASK_PACKET.md`

完整读取任务包、仓库根 `AGENTS.md`、未提交的 `D7_E_OPERATOR_RETURN_R1.md`、原 `D7_E_PRE_RESULT_REVIEW_R1.md` 和 D7-E cycle state。严格按 A1.1→A1.5 执行，只回 delta。

这是纯记录修订，不是科学执行授权。绝对禁止第二次运行 `--verify`、decoder、pytest、compile、dry-run、sentinel、RSS probe 或任何 scientific recomputation。不要编辑原 operator return 或原 BLOCKED review；只能新建 transcript appendix 和 R18-only addendum。原 review 的 R01–R17/R19–R22 已冻结，不得扩大重审。

appendix 只能逐字转录任务包给出的 `VERIFY_OK ...` 和 reported exit 0，并标注 `AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN`、无 standalone log、无独立 timestamp、不能单独证明 verifier 执行。不得伪造更强 provenance。

只有 R18 addendum 得到唯一 PASS token，才允许按任务包精确 manifest 固化七个 immutable root 文件、两份原件、两份新增文件和 cycle state；这仍不是结果接受。FAIL/BLOCKED 则不 stage、不 commit、不修复。全程不得 push、broad-stage 或清理脏树。
