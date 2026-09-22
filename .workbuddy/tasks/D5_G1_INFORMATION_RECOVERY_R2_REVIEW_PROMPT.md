你是 D5 G1 information-recovery R2 的独立科学与代码评审。不要采信实现者的 terminal class、公式、测试数或 PASS；直接读 D4R2 源码、R2 OpenSpec/diff、CAL-only 证据脚本/JSON 和当前候选，自行复算决定性结论。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_INFORMATION_RECOVERY_R2_REVIEW_TASK_PACKET.md`

基线 HEAD `1d4fa9124afd57ec5ce03a786a4cdc2b2f55cc1d`；候选链 `88053563 → a93106f5 → 21576add → 1d4fa912`；当前 gate `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`。完整读包后按 C01–C12 执行，结论只能为 `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS` 或 `..._FAIL`。

必须从实际 D4 builder 证明 lambda*=137.3823795883264 的语义，而不是从 R2 文档反推。独立核对 old consumer 的逐格 pseudo-mass、candidate total-concentration backoff、axis、population、held-out vs in-sample CE、MI/truth mass，以及 D4 7.162347 与 candidate 7.5094 为何不应强行相等。

除静态审查外，在独立非正式 review root 内最多做3次 paired decoder calls：同一 seed/square 下 old accepted prior vs candidate prior，再做 candidate+frozen H2 的诊断。必须显式注入 decoder/prior/matrix/output、每call 120s watchdog；绝不调用 CLI phase 或写正式根。

随后 fresh 跑 compile、focused 和 exact 三文件套件，要求零失败。审查8个新测试是否真的能杀死错误实现，也审查 `1d4fa912` 的生命周期 guard 修复。T5 checkbox 若仅是已完成但未勾的文档滞后可列非阻塞，不能掩盖实质未完成项。

硬禁令：不许正式 G1 重跑/恢复、G2、VAL、真实IR、正式根写/hash/删移、VOID读取、修复或改任何现有文件、授权/状态变化、git写/push/cleanup。CAL-TRAIN只可用于复算既有主张。唯一新建持久文件是 `G1_INFORMATION_RECOVERY_R2_REVIEW_R1.md`，不提交。

PASS 只说明 additive candidate 和归因可进入候选 Model-F 准备/验收链；绝不代表 production wiring、Model-F替换、G1修复、正式重跑许可或G2 readiness。

按任务包 §8 汇报并原样结束：

`R2 信息恢复候选评审完成；正式 G1 负结果未改写、未重跑，G2 未授权。`
