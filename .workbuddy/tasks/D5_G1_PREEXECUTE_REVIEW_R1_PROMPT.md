你是 D5 G1 的独立 Pre-EXECUTE 评审。你没有编写被评审实现，不得采信既有 PASS、测试数或实现者映射；必须读实际冻结包、提交 diff、current source/tests，并自行完成任务包允许的现场检查。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_PREEXECUTE_REVIEW_R1_TASK_PACKET.md`

基线：分支 `formal-ir-v72p1-addendum-clean`，文档冻结提交 `6494b623`，接受的实现为 `cf61ee63f5b76b0223838717b1344e0e7c3867ee`，当前门应为 `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`。完整读完任务包后按 §1→§8 执行；任何 STOP 条件触发即原样汇报，不修复、不重跑越界步骤。

结论只能是：

- `G1_PRE_EXECUTE_REVIEW_PASS`；或
- `G1_PRE_EXECUTE_REVIEW_FAIL`。

必须独立打穿以下四项，不能只做静态 grep：

1. exact 三文件 pytest 全集用 fresh `workspace/` basetemp 跑到零失败；
2. 无 monkeypatch 的 Windows `_rss_bytes()` 为正整数且 PMC sizeof=72；
3. 绝对路径 Git-for-Windows `timeout.exe -k 30 3` 演练杀死 10 秒 sleep 并返回 124；
4. 仓库外 Python 文件、仓库 cwd、无 sys.path/PYTHONPATH 插入的真实 Model-F consumer 可达性探针：普通 `import comparison_bench` 必须失败；不注入 counts/p_b，让生产 file-path consumer 读取已接受 Model-F 输入；注入唯一 first-call sentinel decoder，必须恰在第一次 decoder 调用抛出，calls=1，tmp 输出为空，新 G1/G2 根仍缺席。绝不绑定或运行历史 decoder。

逐字确认未来冻结命令，但绝对不要运行：

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

硬禁令：不许运行任何 `--phase` 或 production decoder；不许 prepare/verify；不许读 CAL/VAL/parquet/raw rows；不许读取或引用 VOID-G1 数字；不许改任何正式根、代码、既有文档、OpenSpec、状态、decision log 或 memory；不许任何 git 写操作；不许请求或自行制造授权；不许修复发现。测试仅能写自己的 basetemp，探针仅能写仓库外自建临时目录，二者必须验证绝对路径后只删自己。

唯一允许的新建持久文件：
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_REVIEW_R1.md`

PASS 只表示主线程随后可以单独向用户请求“一次尝试”的明确授权；PASS 本身不是授权、不是执行、不是结果接受、不是科研资格，也不许可 G2。报告不得提交、不得 push、不得改 `cycle_state.yaml`。

完成后按任务包 §8 汇报，并原样结束：

`G1 Pre-EXECUTE 评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。`
