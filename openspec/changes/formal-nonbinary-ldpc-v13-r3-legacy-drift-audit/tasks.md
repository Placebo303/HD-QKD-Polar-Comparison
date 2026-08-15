# Tasks: formal-nonbinary-ldpc-v13-r3-legacy-drift-audit

Status: **COMPLETE — 64-frame + full-data extension executed 2026-08-16**

## L — 规划与冻结

- [x] **L01** 新建本 change，冻结 claim boundary / 数据源 / 帧选择 / decoder 不变式。
- [x] **L02** 冻结输出 schema 与 additive root。

## I — 实现与测试

- [x] **I01** 实现 `formal_ir/nonbinary_v13r3_legacy_audit.py`（pairs 校验、
  预注册帧选择、R3 单次解码、报告/manifest）。
- [x] **I02** 实现 CLI `cli/run_v13r3_legacy_drift_audit.py`（execute / verify）。
- [x] **I03** 测试：contract 校验、选择规则、stub 解码包 schema、verify 只读。

## X — 单次生产执行

- [x] **X01** 用三份 legacy parquet 各 64 帧执行一次，写 additive 包。（Done 2026-08-16：192 帧，188 exact_correct / 4 decode_failed。）
- [x] **X02** 检查 claim boundary：任何 fresh/promotion/qualification 字样都不得
  出现在报告状态字段中。

## V — 只读验证

- [x] **V01** `verify` 只读复核行数/选择规则/claim/frozen binding/文件字节不改动。（Done：verify OK。）

## XF — Full-data extension

- [x] **XF01** 启动全量审计（`--all-frames`，三源全部完整帧 8412 帧），以 8 chunk 并行执行完成。
- [x] **XF02** 全量完成后再执行只读 verify。（8/8 chunk verify OK，合并 8412 帧。）
- [x] **XF03** 更新全量证据包、decision-log、CURRENT_TASK/AGENT_HANDOFF；本地提交。

## C — 收尾

- [x] **C01** 更新 decision-log / memory / CURRENT_TASK / AGENT_HANDOFF；本地提交，不 push。（Done：本地提交，不 push。）
