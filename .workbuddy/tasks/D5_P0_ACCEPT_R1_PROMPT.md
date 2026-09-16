# Paste-ready prompt — D5-P0-ACCEPT-R1 (docs only, no execution)

Copy everything between the two `=====` lines into a fresh session opened in
`D:/Code/HD-QKD_Polar_Comparison`.

=====

本次任务是**纯文档 + 一次本地提交**，零执行。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_ACCEPT_R1_TASK_PACKET.md`

先完整读完，再按 STEP 1 → STEP 7 顺序执行，不要重排、不要合并、不要跳步。

任务是：把 P0 成本预检的结果**按"仅成本测量"的口径接受**，把四份未跟踪的评审文件
落盘，记录全部遗留限制，并把 `next_gate` 从 `P0_PACKET_REVIEW` 推到
`G1_PACKET_REVIEW`。

你需要的每一个数字都在任务包 §3 里给全了。**不许自己推导、重算或"改进"任何数值**；
缺什么就 STOP 上报。

几条最要紧的：

1. **不许设任何 `*_execution_authorized` 为 true**，九个全部保持 `false`。
   `cycle_state.yaml` 只许改 `next_gate` 那一行，外加新增
   `p0_cost_result_accepted: true` 与 `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`
   两个键。别的一个字都不许动。
2. **接受的是成本，不是科学结论。** 任务包 §3 里"P0 并未确立什么"的清单要**逐字抄进**
   文档——不许说 FER、`exact_failure_fraction`、泄漏、密钥率、资格、方法结论，也不许
   说 G1 或 G2 会通过、会跑完、会符合预算。这一条是整份文档存在的意义。
3. **七条遗留限制要逐字抄，并各自标 `MUST_CARRY_INTO_G1_PACKET`**：L1 深度盲区、
   L2 T1_23 覆盖窄、L3 T1_22 未做实弹验证、L4 STATUS=63 记录更正、L-RSS（Windows 无
   `resource`，`rss_bytes` 全为 null，2 GiB 预算无从核）、L-SCALE（外推不随宽度/行数
   缩放，`projected_g2_s` 与 `projection_blocked: false` **对 G2 毫无许可力**）、
   L-ITER（12 次解码全部跑满 `MAX_ITER=90`，无一提前收敛，成本信号是饱和上界）。
4. **不许冻结、规划或授权 G1。** 那是下一个包的事。也不许解读那两个外推数字。
5. `workspace/` 下一律只读——不许创建/删除/移动/改名/覆盖/规范化/算 hash；六个正式
   根是证据；不许让 `workspace/v72p2d5_g2/20260906_r1` 出现。
6. 不许改任何 `.py`；`docs/decision-log.md` 与 `AGENT_PROJECT_MEMORY.md` **只许追加**，
   既有行一字不动；不许改 OpenSpec。
7. **跑 pytest 时 basetemp 必须放 `workspace/` 下**（STEP 2），放到仓库外会让 D4 那批
   audit 测试假失败。期望 `201 passed`，任何失败就 STOP。跑完删掉自建 basetemp。
8. 不许 `git push`、`add -A`、`add .`、`commit -a`、`reset`、`stash`、`checkout`、
   `clean`、`rebase`、`amend`、`add --renormalize`。只提交一次，提交前用
   `git diff --cached --name-only` 核对——**必须恰好 8 个路径**，多一个少一个都 STOP，
   且不许自己 unstage 去凑。

任何门禁不过就 STOP，报步骤号和原始输出，不要自行修复、不要绕过。

最后按 STEP 7 汇报，结尾写：

**P0 仅以成本测量口径被接受。未作任何正确性、码率或资格主张。G1 既未冻结也未授权；
`next_gate` 现为 `G1_PACKET_REVIEW`。**

不要提议 G1 的参数，不要解读外推数字。

=====
