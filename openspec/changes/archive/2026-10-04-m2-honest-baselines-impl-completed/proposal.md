# M2 Honest Baselines (Implementation Record) — Proposal

- Change: `m2-honest-baselines-impl`
- Track: 无 gate (doc-only; `AGENTS.md` §1.2 适用性矩阵 "Documentation-only changes" 行)。本 change 只做实现记录，不写 `comparison_bench/` 代码，不跑任何执行，不 commit/push，不产生 FER/SKR/资格化/发表主张，不授权任何执行。
- Scope: 仅 `proposal.md` + `tasks.md` 两件；**不建 `design.md`/`specs/`，不改 `openspec/specs/` 主干**。
- Context: 为 M2 实现复审 MAJOR-2 另开的实现 change（实现侧记录载体）。

## Implementation under record (read-only reference, not modified here)

- 4 新文件（已存在实现，本 change 仅记录）：
  - `comparison_bench/src/comparison_bench/methods/hd_cascade.py`（387 行）
  - `comparison_bench/src/comparison_bench/methods/layered_binary.py`（387 行）
  - 对应 tests 2 件（fake-only 单测载体）。
- 只读复用、零签名改：`cascade_lite` / `bitops` / `metrics` / `PEG` / `types` 均为只读复用；未改既有函数签名与既有逻辑/接口。

## New metadata/frame keys (own namespace, provisional pending ratification)

- 新 metadata / frame 键均为两新方法自有命名空间，待 T10 追认：
  - `messages_per_frame_actual`（provisional，每帧消息数实测口径）；
  - `leak_EC` / `blind_stages` 分解列；
  - `f` 三数（本臂 m 基）；
  - `undetected` 隔离（禁并入 success/FER）；
  - Müller 446 / 3.14 分列（禁互相替代）。
- 在 T10 追认完成前不视为既有 schema 的一部分；不改既有列名/键名。

## Frozen pins still BLANK (grant-time fill)

- 种子 / 段表 / 块长表 pin 位仍为 BLANK，grant 时填：
  - HdCascade seed 占位（待 grant-time 填真值）；
  - layered `2026092001` 与 F4 一致（待 grant-time 确认/填入）。

## Relation to `m2-honest-baselines`

- `m2-honest-baselines` 为设计契约（方法契约与任务顺序冻结，spec-only）。
- 本 change 为实现记录（上述 4 文件实现事实的记录载体）。
- T10 schema 确认（新键追认 + pin 位 + MAJOR/MINOR 关闭确认）落此处，不回写彼 change。

## Affected specs

- None.

## Non-goals

- 不改现有 spec / 列名 / CLI / 输出文件名（`AGENTS.md` §5.3）。
- 不执行（含 benchmark/smoke/解码/真实数据访问）；不授权任何执行。
- 不改 `m2-honest-baselines` 既有文件 / M2 三包 / M0 / `docs/decision-log.md` / `AGENTS.md`。
- 不写代码；不 commit/push。
