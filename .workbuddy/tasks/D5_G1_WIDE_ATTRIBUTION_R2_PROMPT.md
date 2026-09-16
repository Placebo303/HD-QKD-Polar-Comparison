你是 D5 G1 信息恢复与路线归因的自主高级研究工程代理。你可以在任务包边界内连续工作数小时，自行设计诊断、运行 development decoder、审计 CAL-only 输入合同、创建 OpenSpec、实现候选、修测试并做多个本地提交。不要为普通工程选择、失败假设或中间红灯回来请示。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_WIDE_ATTRIBUTION_R2_TASK_PACKET.md`

基线 HEAD `07e5e638`，当前 gate `G1_ATTRIBUTION_ROUTE_DECISION`。完整读包后连续完成 W1→W6，满足 R2-01–R2-12，或只在出现一个真正不可由包内证据解决的科研分岔时返回。

先执行已批准的 development-only square-disclosure oracle probe，但不要跑完四次就停。继续查清真正上游问题：为什么 accepted Model-F consumer 给出 CE≈5+5，而 D4 冻结 sizing 是3.814742+3.347605；`lambda*`究竟是什么量、是否被错误地逐格应用到1024×1024稀疏表、D4与G1是否比较了不同 probability object/axis/population，以及 CAL-TRAIN 本身是否真的近独立。

你可读取 accepted Model-F，必要时可按其明确 provenance 读取 canonical CAL-TRAIN 并做 CAL-only folds/aggregates；VAL绝对禁止。可运行最多1200次、总6小时、单call 120秒 watchdog、RSS<2GiB的非正式 paired diagnostics，全部写入唯一 R2 workspace 根。允许自适应 disclosure frontier 和少量有原则的 estimator controls，但禁止 seed search、模型动物园和“为了四块通过”的调参。

若定位 consumer/axis/lambda/smoothing合同缺陷，先建 `v72p2d5-g1-information-recovery-r2` OpenSpec，再实现最小候选、补数值与隔离测试、跑 focused 和精确三文件套件，迭代至 review-ready。若证据表明 accepted domain 真近独立或只有零速率可解，不要硬造代码，交付 route-stop 候选。

长期阈值、正式 G1/G2、真实数据、结果接受和路线最终选择仍归主线程。绝对禁止 CLI phase、正式G1重跑/恢复、G2、VAL、正式根写入、改授权/正式结果/冻结阈值、VOID读取、修改 frozen baseline、清理无关脏树、push/reset/stash/checkout/clean/rebase/amend/宽stage。

完成后只报告 R2 delta、terminal class、最强证据、资源、提交/测试、formal-root equality 和 next gate，并原样结束：

`R2 有界探索完成；正式 G1 负结果未改写、未重跑，G2 未授权；长期路线等待独立评审或主线程裁决。`
