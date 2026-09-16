你是刚才 G1 readiness 独立代码评审的范围补遗 session。原评审把“完整三文件测试”误读成 core+两个测试文件，只跑了 189 项；现在只补跑冻结包明确列出的三个 pytest 文件，不重做其它评审，也不改任何代码。

任务包：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_CODE_REVIEW_SCOPE_ADDENDUM_A1_TASK_PACKET.md`

必须完整读完后执行。三个测试路径一个都不能少：

- `test_v72p2d5_gf32_rate_mother.py`
- `test_v72p2d5_model_f_input.py`
- `test_v72p2d4_cal_gf32_model_rate_audit.py`

使用新的唯一 `workspace/` basetemp。不要复用或删除 `workspace/d5_g1_main_verify_20260908a`，那是主线程留下的非正式临时目录。

禁止 decoder、任何 `--phase`、prepare/verify、CAL/VAL/parquet 行、正式根写入、代码/既有文档/OpenSpec/状态修改及所有 git 写操作。

只允许新建：
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md`

零失败且正式根前后不变才可写 `G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS`；否则写 FAIL 和精确失败 ID。不要提交，不要 push。

最后原样写：

`G1 代码评审测试范围已补齐；该补遗不构成授权，G1 未执行。`

