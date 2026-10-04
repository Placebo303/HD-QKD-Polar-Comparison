# V68_RESULT_ACCEPTED — V68_OVERALL_STILL_HEAVY (固化，不重跑)

- **Change**: `formal-ir-v68-balanced-gf32-bit-partition`
- **Base HEAD**: `fcf3e457ecf45c58e23f91d750acd5267d541795` (V67_FEASIBILITY_MAP_ACCEPTED)
- **Provenance**: V68 无独立 plan commit，记为 `provenance deviation`，不借用 `520b51c4`。
- **Overall**: `V68_OVERALL_STILL_HEAVY` — 均衡重划分（252×5-bit 枚举，CAL-only max→sum→abs→lex 选 S*）后仍无 `S*` 使三 session 均 `m1<1024 && m2<1024 && raw<5120`，需更深表示。
- **Per-session**: 各 session `V68_STILL_HEAVY`（V67 natural 1024–1199 同域均衡未纠正），`MODEL_NOT_STABLE` 未触发为前提已验。
- **Frozen**: 数值不改，不重跑，不改 src/，不构矩阵，不跑 decoder，`TEST` 密封不读。
- **Artifacts**: `V68_FEASIBILITY_MAP_ACCEPTED.md` 已归位至 `formal-ir-v67-multisession-feasibility-map/V67_FEASIBILITY_MAP_ACCEPTED.md`；本文件为 V68 终态固化。
