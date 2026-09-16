# Prompt — D5 decomposition successor closeout A3

执行最终修订件：

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_DECOMPOSITION_SUCCESSOR_CLOSEOUT_A3_TASK_PACKET.md`

主线程已重新提供 exact pytest command 和完整 stdout/wrapper errors；直接按包逐字写入 appendix，来源标为 `AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN`。绝对不重跑 pytest，不推定 exit 0，不估算时间。

原22文件pre/post表值正式豁免：保留操作员“前后一致”的attestation，同时执行一次获准的fresh post-only names/sizes/mtime_ns采集。DS13按“attestation + fresh cutoff + zero path touch”关闭，明确披露旧表未保留。

只新建 `workspace/d5_decomposition_successor_r1_c765e3010674/TEST_EVIDENCE_APPENDIX.log`，单文件stage、单文件commit、不push。不得编辑任何既有文件，不得运行pytest/decoder/任何`--phase`，不得读或hash保护文件内容，不得开始graph/mother successor。

fresh stat若发现目录、尺寸、mtime cutoff或G2偏差则立即STOP；否则完成A3并只回delta。

