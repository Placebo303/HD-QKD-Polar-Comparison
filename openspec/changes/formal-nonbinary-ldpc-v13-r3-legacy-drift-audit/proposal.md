# Proposal: formal-nonbinary-ldpc-v13-r3-legacy-drift-audit

> 状态：COMPLETE —— 2026-08-16 用户明确决定使用三份 `2026-01-21` 已采集
> Type2 数据继续执行；生产执行一次 + verify OK，claim boundary
> 仅 `legacy_drift_audit`。本 change 的 claim boundary **仅限** `legacy_drift_audit`，
> 不构成、不声明、不替代 fresh-confirmation / promotion / qualification。

## What

在 D0 已判定 `data_intake_rejected_for_fresh_confirmation`、D5 已判定
`drift_exceeded` 的前提下，对三份 `2026-01-21` Type2 源的预注册完整帧，
用 **完全不变** 的 V13 R3 候选 `nbldpc_v13_r3_code_v1`（QSC p=.20、
flooding FFT-QSPA、max_iter=100）各执行一次解码，量化漂移数据上的精确
纠错表现。所有失败原样保留。

- 数据：D4 已产出的三份 pairs.parquet
  - `type2_1p5M_20260121_183806`（2767 完整帧）
  - `type2_1M_20260121_184040`（2000 完整帧）
  - `type2_2M_20260121_183657`（3645 完整帧）
- 规模：每源取 **前 64 个完整帧**（按 `frame_id` 升序，0..63），共 192 帧，
  与 V13 fresh 规划 canary+confirmation 的 192 帧规模对应，但角色为
  `legacy_audit`，不是 canary/confirmation。
- 执行：每帧一次，无重试、无调参、无帧替换、无候选替换。

## Why

用户确认纠错算法对具体采集数据的要求没有 fresh 准入设计假设得那么高，并明确
要求使用这三份已有数据继续。冻结规则不允许把它们作为 fresh 证据，但允许
另开独立 change 做 `legacy_drift_audit`。该审计回答唯一问题：**在已知漂移
（raw SER≈0.240–0.256，高于 V13 D01 参考 0.0771）的 legacy 数据上，不变 R3
候选还能精确纠正多少帧。**

## Scope

- 新建本 OpenSpec change，不复用 fresh-acquisition 执行身份，不写入任何
  `fresh-confirmed`、`promoted`、`qualified` 状态。
- 实现最小执行/只读验证工具；生产输出 additive 于
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`。
- 不修改 R3 码本、先验、迭代上限、解码器接口；不修改 frozen Polar baseline。

## Out of scope

- fresh-confirmation 及其后续 prepare/execute/verify；
- promotion / qualification / 效率结论（f≈12 不变）；
- 用本次结果替代 V13 `ready_for_fresh_confirmation` 的证据边界；
- V15/V16 重启；效率路线新 change。

## Success criteria

- 工具经测试验证；生产执行一次，192 帧全部有结果行，失败原样保留。
- 产出 `audit_report.json` 且 `claim_boundary=legacy_drift_audit`、
  `fresh_confirmed=false`、`promotion=false`、`qualification=false`。
- 只读 verify 通过；结果仅用于 legacy drift audit，不改变 P1 frozen failure。
