# Prompt — D5 decomposition successor closeout A2

继续当前 blocker，只执行：

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_DECOMPOSITION_SUCCESSOR_CLOSEOUT_A2_TASK_PACKET.md`

作者裁决：绝对不重跑 pytest。已有完整终局 `259 passed, 1 warning in 55.22s` 足以证明 assertion result PASS；wrapper 的时间/exit 标签输出失败作为 provenance gap 原样记录。

必须写：START/END local/UTC 和 PYTEST_EXIT_CODE 全部为 `NOT_CAPTURED`，不得推定 exit 0，不得估算时间。DS12 关闭为 `PASS_WITH_PROVENANCE_GAP`。

使用当前 session 已保留的 A1.3 保护根前后元数据表完成 DS13；若实际表值未保留，立即 STOP，不得用新采 post 值伪装原表。

只允许新建 `workspace/d5_decomposition_successor_r1_c765e3010674/TEST_EVIDENCE_APPENDIX.log`，单文件 stage、单文件 commit、不 push。不得改 report/state/log/memory/code/tests/OpenSpec，不得运行 decoder、pytest 或任何 `--phase`，不得开始 graph/mother successor。

完成后只回 A2 delta。

