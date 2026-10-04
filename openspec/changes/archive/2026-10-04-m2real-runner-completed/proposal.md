# M2REAL Runner — Proposal

- Change: `m2real-runner`
- Track: implementation-only（实现 change 本体；`AGENTS.md` §1.2 适用性矩阵 "Implementation-only changes" 行）。**零真实执行**：本 change 只落盘 runner 代码 + fake-only 测试 + 本三文件；**不跑 M0、不跑真实解码、不 commit/push，不产生 FER/SKR/资格化/发表主张，不做 acceptance**。
- Scope: T3 R0..R9 实现合一 — 单一新文件 `comparison_bench/src/comparison_bench/cli/m2real_runner.py` + 两 fake 测试 + `openspec/changes/m2real-runner/` 三文件。
- Frozen predecessors (read-only, numbers never copied except frozen literals restated):
  - `docs/research_cycles/M2-REALCOMP/PREREG_AND_AUTH.md` (G-M2-REALCOMP, NOT GRANTED) + `M2-REALCOMP-PROMPT.md`；
  - `docs/research_cycles/M0-REALFRAME/RESULT.md`（NB 列 artifact 指针，不重跑）；
  - decision-log 2026-09-24 条（含 F9(i) 裁定 + M2 D2 三分支预注册阈值裁定）；
  - `openspec/changes/m2-honest-baselines/design.md`（T0 M2 design；Müller 待澄清表 open 状态延续）；
  - `docs/research_cycles/M2-HDCASCADE-SYNTH/PACKET.md` + `M2-LAYEREDBIN-SYNTH/PACKET.md`（合成臂 thờ, 真实臂只读复用其 helper）。
- 用户已冻（本 change 实现输入，不重议）: 16 分块 assumed + 递增种子 + Müller 继续 assumed-v1（待核对）。

## Goal

M2-REALCOMP 执行面前置的**唯一新增可执行面**：在 M0 同一批真实 eval 超帧上跑两新方法臂（HD-Cascade × {m1,m2} + 分层二元 × {m1,m2}，逐源调用），输出 A-CMPE 全列 + D2 输入 + F9(i) 标注 + claim 禁句产物，供未来 GRANT 后的 DECIDE 执行使用。本 change 落盘后 `<m2real_runner>` 路径占位解除（PROMPT §3 `____` 可填）。

## Non-Goals

- 不授权、不执行、不 Pre-EXECUTE、不 Pre-RESULT（PREREG §6 仍全 BLANK；一次授权覆盖冻结臂表，执行面只认未来 grant）。
- 不重跑 M0、不复制 M0 数值（NB 列只留 artifact 指针字符串，不抄数）。
- 不改 `src/`、`experiments/`、`tools/`、`m0`、`m2hdc`、`m2lb`、`methods/` 任一冻结模块（只读复用，零改）。
- 不写 `results/`、`comparison_bench/outputs_comparison/`、既有 workspace 证据根。
- 不填 Müller 真值、不发明 1024→64 之外的新映射、不发明种子外规则（遇任一即 STOP，回主线程）。
- 不做 acceptance（本 change 实现后不签收，留主线程里程碑评审）。

## What (frozen scope)

1. `m2real_runner.py`：`--source {1M,1p5M,2M}` + `--root workspace/m2real_<uuid8>`，双旗缺一 rc2 + 根门；`execute(source, root, series_fn=m0.load_real_series, bundle_fn=m0.load_bundle, ...)` 默认真实链，测试注入覆盖。
2. 真实切片：超帧 205/287/383、余数 407/405/529 记录；每超帧 16×64 连续块；超帧 success = 16 全 exact（leak 求和）；FER 分母块数 3280/4592/6128；超帧数另列。
3. 种子：ARM seed + 全局块序号递增，`o1_blk:{seed}`（HDC 5701 系 / LB 5601 系各自基址，与合成族区分）。
4. HDC 臂：`provisional_block_table` assumed-v1（[8,4]/cross1/floor1/max_passes4）+ `run_hd_cascade` 只读。
5. LB 臂：`allocation_for` / `blind_table_for` verbatim + `LayeredParams` 300/3（单 full-m 解码；盲增量不跑，盲表 report-only 记录）。
6. 预算：每源 5400 s / 单解码 300 s / RSS 4 GiB / 1 CPU。
7. 会计 A-CMPE 全列 + D2 口径（输入 + 规则复述 + DEFERRED）+ F9(i) 标注 + claim 禁句。
8. 两 fake 测试（真实切片 mock 小数组 + mock bundle + fake decode/construct；生产核 raise；零真实读；A-CMPE 列断言）。

## Affected specs

- None pending delta.（本 proposal 不改 `openspec/specs/` 现有文件；新契约即代码 + 测试本身。）
