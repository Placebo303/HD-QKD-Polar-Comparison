你是 D5 G1 R2 候选接受与 L1 主线鉴别的自主高级研究工程代理。你可以在任务包边界内连续工作数小时，自行完成接受、预注册、CAL-only估计、development decoder研究、OpenSpec、实现、测试和多个本地提交；不要为普通工程选择或失败假设回来请示。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_R2_ACCEPT_AND_L1_DISCRIMINATE_TASK_PACKET.md`

基线 HEAD `1d4fa9124afd57ec5ce03a786a4cdc2b2f55cc1d`；R2 review 必须为 `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS`。先按六路径提交接受 additive backoff candidate，并把未勾 T5 做事实性收口；然后在读取新 CAL 分数或运行新 decoder 前，单独提交 L1 discriminator preregistration。

主问题：joint-F backoff 修正了lambda合同并让L2 square恢复，但L1 truth mass约0.096且到64行仍失败。你要用最多3个诚实 estimator、CAL-only held-out L1 NLL选择、paired n=64 disclosure frontier，判断L1是否能在 m<64 的非零率点恢复。禁止按decoder成功调lambda或筛seed。

若n64失败，可按预注册依次做n128/n256 development-only block scaling；这不是G2，也不得使用G2正式根/门限/授权。预算1500 calls、8小时、单call120s watchdog、RSS<2GiB，全写唯一非正式 workspace 根。

若诚实 estimator 在n64可恢复，先建 `v72p2d5-g1-l1-estimator-recovery-r1` OpenSpec，再实现最小 additive injected candidate、补测试并跑 focused+四文件D5套件。若只在更大块恢复，交 block-geometry successor；若CAL本身信息不足，交route-stop；不要为了代码diff而实现。

长期阈值、正式G1/G2、真实数据、结果接受仍归主线程。绝对禁止正式G1重跑/恢复、CLI phase、G2、VAL、正式根写入、VOID读取、改授权/正式结果/冻结阈值、seed search、修改frozen baseline、清理脏树或push/reset/stash/checkout/clean/rebase/amend/宽stage。

按任务包 L1-01–L1-12 连续执行，完成后只报delta并原样结束：

`L1 主线鉴别完成；正式 G1 负结果未改写、未重跑，G2 未授权；下一路线由证据终类决定。`
