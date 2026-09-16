# Prompt — D5 route-stop acceptance + decomposition successor R1

在仓库 `D:\Code\HD-QKD_Polar_Comparison`、分支 `formal-ir-v72p1-addendum-clean` 中，完整执行：

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_AND_DECOMPOSITION_SUCCESSOR_R1_TASK_PACKET.md`

你是强执行/研究 operator，可以在任务包边界内长时间自主推进，不要为日常实现选择或中间进度频繁询问主线程。主线程已经作出方向裁决：先正式收口已独立通过的当前 D5 路径停止结论，然后直接推进第一优先级后继——完整的 252 个可逆 10-bit→5+5 bit partitions 的 CAL-only、decoder-blind 选型与配对开发解码鉴别。这个任务是主线推进，不是横向发散。

严格按顺序：

1. 只读核对 baseline、review、state、保护根与 scope。
2. Phase A 落地 `D5_ROUTE_STOP_REVIEW_PASS` 与当前路径停止接受，精确五路径提交，不 push。
3. Phase B 在任何新分数或 decoder call 之前，单独提交 preregistration。
4. Phase C 穷举 252 partitions，按冻结 CAL-only lexicographic rule 选 top-3，加 current/swapped controls，冻结后才允许开发 calls。
5. 仅用显式注入、UUID 开发根、固定 seeds/rows，严格计数并遵守 600 calls / 6h / 120s / 2GiB。
6. 只有 `DECOMPOSITION_STRONG_N64_RECOVERY` 才能先建 OpenSpec 再实现加性非正式候选；weak/none/ineligible 不得自行转图搜索、mother 搜索或 BP 调度搜索。
7. 跑任务包规定的四文件套件，完成 evidence/report/state/log/memory 与精确提交，不 push。

硬禁令：不得运行任何 CLI `--phase`，不得重跑/恢复/改写正式 G1，不得执行或创建 G2，不得读 VAL/真实 IR/原始数据，不得读 VOID 根数字，不得改任何授权/科学推广/正式结果，不得修改 frozen baseline，不得 seed/hyperparameter 搜索，不得扩到一般 GL(10,2) 变换，不得清理或规范化无关脏树。

工作树有已知 CRLF porcelain 噪声。scope 判断使用 baseline + exact allowlist + `git diff --numstat`/`--cached --numstat`；不要因为无内容差异的 EOL churn 停止，也不要清理它。真正的科学状态、保护根、授权或 allowlist 偏差必须按包 STOP，贴原始输出，不自行修复或越权推进。

返回只允许两种：

- 全部 DS01–DS15 完成后的 delta 汇报；或
- 具体 blocker，含失败 ID、原始输出、已尝试的包内补救和唯一待裁决问题。

不要重述项目历史。最终必须明确：正式 G1 没有重跑，G2 未授权、未执行，所有正式证据根未改写，本轮结论仅是 CAL-only/开发级 successor routing。

