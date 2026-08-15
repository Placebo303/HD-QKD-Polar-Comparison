# Design: formal-nonbinary-ldpc-v13-r3-legacy-drift-audit

## 0. Status

EXECUTED（2026-08-16）。用户已授权使用三份 `2026-01-21` legacy 数据继续；
生产执行一次 + verify OK；本 design 条款冻结。

## 1. Claim boundary（frozen）

- 最高状态：**`legacy_drift_audit`**。
- `fresh_confirmed`、`promotion`、`qualification`、`observed_fresh_correction`
  全部禁止。
- 本 change 不改变 P1 `no_eligible_frames` 冻结终态，也不改变 V13 历史证据
  边界。

## 2. Data sources（frozen）

三份 D4 pairs table（每行 `frame_id,pair_idx,alice_symbol,bob_symbol`）：

| source_tag | parquet |
|---|---|
| `type2_1p5M_20260121_183806` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet` |
| `type2_1M_20260121_184040` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet` |
| `type2_2M_20260121_183657` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet` |

D0/D5 状态以既有证据为准：
`data_intake_rejected_for_fresh_confirmation` + `drift_exceeded`。

## 3. Frame selection（frozen）

- 每源取 **前 64 个完整帧**：`frame_id` 升序，0..63。
- 每个完整帧必须正好 256 行、`pair_idx` 为 0..255 且符号 ∈ [0,1024)。
- 任何源不足 64 完整帧 → `insufficient_legacy_frames`，不缩小规模，不补帧。
- 不随机、不重排、不替换；选择规则在 manifest 中记录。

## 4. Decoder invariants（frozen）

- 码本：`nbldpc_v13_r3_code_v1`（`nonbinary_v13_r3_candidate.build_r3_codebook()`，
  seed 20260818，170 checks，168x3+2x4，rank 170）。
- 先验：QSC p=.20；接口：flooding FFT-QSPA；max_iter=100。
- 每帧一次 `decode_r3_frame(bob, syndrome, manifest, matrix, hook=True)`，
  其中 `syndrome = H * alice`。Alice 只用于公开 syndrome 与事后
  exact_correct 判定，绝不进入先验/停止/重试/排序。

## 5. Outcome semantics（frozen）

- `syndrome_consistent` 且 decoded == alice → `exact_correct`。
- `syndrome_consistent` 但 decoded != alice → `exact_mismatch`。
- `decode_failed` / `decoder_error` / 帧解码异常 → 原样保留对应 status/reason。
- 所有结果行保留；禁止状态改写、禁止把 failure 改为 ok。

## 6. Output package（additive）

Root:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`

Files:
- `audit_outcomes.csv` — 每帧一行（192 行）
- `decoder_telemetry.jsonl` — 每帧聚合 telemetry 一行
- `audit_report.json` — 三源汇总 + claim boundary + frozen binding
- `audit_run_manifest.json` — 命令、git HEAD、parquet sha256、选择规则

## 7. Stop rules（frozen）

- 工具测试未通过 → 不执行生产。
- 输入 contract 违反 / 码本 binding 漂移 / 不足 64 帧 → 停止并保留终止包。
- 生产执行一次；任何 failure 原样保留，不重跑、不调参、不替换。
- verify 为只读，不改任何字节。
