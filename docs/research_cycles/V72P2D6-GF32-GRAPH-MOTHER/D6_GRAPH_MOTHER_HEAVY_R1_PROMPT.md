# Prompt — V72P2D6 GF32 graph/mother heavy R1

在 `D:\Code\HD-QKD_Polar_Comparison` 的 `formal-ir-v72p1-addendum-clean` 分支，完整执行：

`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_HEAVY_R1_TASK_PACKET.md`

这是一个可长时间自动托管的主线 research+implementation 任务。你有权在包内连续完成 OpenSpec、prereg、实现、测试、独立代码评审、独立 Pre-EXECUTE、开发 decoder 执行、独立 Pre-RESULT、证据和本地提交；不要为常规工程判断或中间进度询问主线程。只在全部 A01–A20 完成，或遇到会改变冻结科研契约的具体 blocker 时返回。

用户转发本 prompt 即明确授权：在独立 `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_PASS` 后，执行任务包限定的 development-only decoder cells，最多 2500 calls、总 wall 12h、单 call 120s、RSS<2GiB、每 cell 最多一次。这个授权不包含任何 CLI `--phase`、正式 G1 重跑、G2、VAL、真实数据、资格或推广。

核心方向只有一个：保持当前 decomposition、E2 prior、rows、GF32 decoder、schedule 和语义不变，只改变 graph/mother。严格实现包内 B0/B1、T1–T4、M1/M2；结构盲选后才跑 n64 canary，使用互斥 confirmation seeds；n64 无信号才按包条件扩到 development n128/n256。不得增加候选、窗口、degree distribution、seed 或调参轴。

实现前必须 OpenSpec+prereg 单独提交。decoder 前必须有独立代码评审 PASS 和独立 Pre-EXECUTE PASS。结果提交前必须有独立 Pre-RESULT PASS。reviewer 只审不改；普通代码问题可在首次 decoder 前自主返工并重新评审，最多两轮。decoder calls 开始后不得改生产代码并混用证据。

工作区有已知 CRLF porcelain 噪声；只用 baseline、exact allowlist、`diff --numstat` 和 staged manifest 判 scope，不 clean/reset/stash/checkout。所有任务提交本地，不 push。

硬禁令：不得运行任何 `--phase`；不得碰正式根或读 VOID；不得执行/创建 G2；不得读 VAL/real/raw；不得搜索 graph seeds、block seeds、coefficients、rows、decoder parameters；不得修改 D5 production wiring/constants/results/authorization；不得开始下一 decoder-dynamics 路线。

完成后只回 delta；若 blocker，给失败 A-ID、原始输出、已试包内补救和唯一待裁决问题。
