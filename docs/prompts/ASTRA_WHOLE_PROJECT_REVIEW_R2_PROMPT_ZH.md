# 可直接复制给 GPT-6 Astra 的全项目审查 Prompt

你上一轮对 D19 的审查很有价值，但本轮请不要继续把整个项目收缩成
“是否接受联合准入总体”这一个局部决策。

请先阅读：

1. `ASTRA_D19_REVIEW_CONSOLIDATED_ZH.md`（你上一轮的完整输出）；
2. `ASTRA_D19_REPLY_AND_PROJECT_EXPANSION_ZH.md`（我们对缺失信息的回答及范围扩展）；
3. `ASTRA_WHOLE_PROJECT_REVIEW_R2_TASK_PACKET_ZH.md`（本轮权威任务包）；
4. 其余上传的项目路线、数学方法、D7/D14–D19 和治理证据。

你的角色是项目首席科学架构审查者。请用最强推理能力回答整个
HD-QKD information-reconciliation 项目中最难、最有价值的问题，而不仅是当前
D19 blocker。

核心目标是实际 HD-QKD 数据上的高性能、低泄漏、可接受错误风险和净产出。
NB-LDPC 是当前主线；binary Polar 是冻结基线；NB-Polar 是隔离的高风险旁线；
Cascade 不是当前自动转向。

严格遵守任务包的 G1–G8、portfolio 评分、返回格式和 R2-A1–A9 验收标准。
特别要求：

- 找出项目因果链最薄弱的三条边；
- 判断下一单位研究预算花在哪里最可能改变路线；
- 比较 fixed-code refinement 与 rate-adaptive mother-code 的价值；
- 给出 DE、finite graph、decoder、real data 之间最小可证伪桥梁；
- 给出跨层 extrinsic/cavity 的 no-double-counting invariant；
- 设计最小真实数据 DECIDE，但不要授权它；
- 指出哪些流程可以删除或降频，哪些科学 gate 绝不能删；
- 给出 Top 5 和一个 70/20/10 三个月研究组合；
- 最后只选择一个近期主决策，并说明它服务于哪个最终目标。

所有事实和建议继续标记 `OBSERVED / DERIVED / PROPOSED / UNKNOWN`。
不要请求运行新实验来完成本轮审查；优先利用现有材料。不要生成代码或把任何
建议解释为执行、真实数据、资格、发表或安全主张授权。
