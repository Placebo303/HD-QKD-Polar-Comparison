## Historical implemented scope — formal-ir-v72p2d3-gf32-contrast

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v72p2d3-gf32-contrast-completed/specs/spec.md -->

## S-R2：真实输入适配（prepare-only，additive）

- **S-R2-01**：registry SHALL 为 `v72p2d3_real_registry_v1`（session 冻结 1M，
  CAL702..1725/VAL1726..1729 disjoint，禁 1730+，`used_2m=false`，列恰 4 列）；
  SHALL NOT 读或计算 checksum/hash/tag。
- **S-R2-02**：parquet SHALL 仅受限 4 列读（`frame_id/pair_idx/alice_symbol/bob_symbol`），
  SHALL 校验 CAL1024x256+VAL4x256 几何；数据行 SHALL NOT 落盘。
- **S-R2-03**：prepare summary SHALL 仅标量（`v72p2d3_prepare_summary_v1`，
  `formal=false`，`decoder_calls=0`，`published_bits=0`）；SHALL NOT 含 Alice/Bob 数组、
  prior/syndrome/matrix 值、candidate/messages；缺输入 SHALL 为 `PREP_FAILED`，
  预算超限 SHALL 为 `BLOCKED`；输出 SHALL 恰一文件且 SHALL NOT 为 `run_01`，
  SHALL NOT 在生产根下。
- **S-R2-04**：R3 SHALL 绑定 `r3_implementation_sha=1deb0fd8`（首次真核绑定，非 retry；`implementation_sha` 旧值与 R2 BLOCKED 不动）；`--execute-real` SHALL 仅放行精确预注册根，其余生产路径与 workspace 路由仍拒绝。
