# M2-LAYEREDBIN-SYNTH BATCH-END REVIEW (独立评审, EXPLORE batch G-M2-LAYEREDBIN-SYNTH)

- 日期: 2026-09-24; 分支 `formal-ir-v72p1-addendum-clean`; 基线 HEAD `8e9c8526`。
- 范围: T2 12 臂合成执行 (LOG Entry3 启动 + Entry4 结果); PACKET §§0–9 + R1 修订 + fallback 附录为冻结依据。
- Claim 固定句（逐字）：“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”
- 性质: batch-end 独立 review (per-arm review 不适用); 本文件仅关闭文本/口径, 不做 promotion/选点/真实结论。

## 1. 独立评审结论

- B1 (PACKET §7 授权文本): 关闭。§7 标题已改为 FROZEN + R1 修订指针 (12 臂已执行见 LOG Entry3/4); §7-9 尾句“不执行”已删, 改为“已执行待 batch-end”; LOG Entry0 已加 supersede 指向 Entry3/4。
- B2 (claim 固定句): 关闭。`BACKEND_CORRECTION.md` §3 与 `REVISION_R1_RANK_FALLBACK.md` §与冻结包关系均已逐字补入固定句。
- B3 (后端错标): 关闭。12 臂 RESULT md `true binary SPA` 错标以各臂 `backend_used.sidecar.json` 为准纠正 (见 BACKEND_CORRECTION §1–§2); 旧三件未改 (见 HASH_MANIFEST)。
- B4 (本批数据定位): 转 retained-assumed 诊断, 禁 promotion/选点/真实结论。12 臂后端恒为 `numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)` (assumed 先验 + 非 ldpc 后端), 与真体 SPA 不可比、不可互换、不可合并; 不得用本批合成数做 promotion、operating-point 选点或任何真实 FER/效率/泄漏/SKR 结论。
- bar-12 FAIL 口径: 12 臂一致 `FAIL-early-stop` + CENSORED 系 G-A 门逐臂 verdict (包内预期行为), 非方法证伪, 永不外推至 240, 永不 pool。
- blind decodes>blocks 口径: blind 臂 decodes (132–154) > blocks-at-stop (58–80) 为多段累加口径 (初始段 + 已用增量段逐段译码计数), 非计数错误; matched 臂 decodes == blocks。
- 预算/repair: 总 wall 约 243s ≪ 21600s (每臂 wall≤1800s, 单 decode terminal≤300s, RSS<4GiB, 1 CPU); repair 使用 0 次 (`no repair path used` 同效); 无 INCOMPLETE-wall、无 FAIL(budget)、无 Refusal、无 STOP-BLOCKED、无第二次失败。

## 2. 证据指针 (12 根 × 3 件 + sidecar)

| # | 臂 | 根 | RESULT md | rows.json | block_accounting.csv | sidecar |
|---|---|---|---|---|---|---|
| 01 | M2LB-1M-197-matched | `workspace/m2lb_18eb57a9/` | `M2LB_RESULT_1M_197_matched.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 02 | M2LB-1M-201-matched | `workspace/m2lb_99d2bfef/` | `M2LB_RESULT_1M_201_matched.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 03 | M2LB-1.5M-203-matched | `workspace/m2lb_d4d24a1a/` | `M2LB_RESULT_1p5M_203_matched.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 04 | M2LB-1.5M-207-matched | `workspace/m2lb_2c09cb2d/` | `M2LB_RESULT_1p5M_207_matched.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 05 | M2LB-2M-204-matched | `workspace/m2lb_bb3120fc/` | `M2LB_RESULT_2M_204_matched.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 06 | M2LB-2M-208-matched | `workspace/m2lb_261d611c/` | `M2LB_RESULT_2M_208_matched.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 07 | M2LB-2M-204-blind | `workspace/m2lb_24f99582/` | `M2LB_RESULT_2M_204_blind.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 08 | M2LB-2M-208-blind | `workspace/m2lb_407d9236/` | `M2LB_RESULT_2M_208_blind.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 09 | M2LB-1.5M-203-blind | `workspace/m2lb_b9a4fdd7/` | `M2LB_RESULT_1p5M_203_blind.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 10 | M2LB-1.5M-207-blind | `workspace/m2lb_aae025fc/` | `M2LB_RESULT_1p5M_207_blind.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 11 | M2LB-1M-197-blind | `workspace/m2lb_84150bd6/` | `M2LB_RESULT_1M_197_blind.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |
| 12 | M2LB-1M-201-blind | `workspace/m2lb_fc719214/` | `M2LB_RESULT_1M_201_blind.md` | `rows.json` | `block_accounting.csv` | `backend_used.sidecar.json` |

- md5 见 `HASH_MANIFEST.md`; 逐臂 verdict/计数见 LOG Entry4。

## 3. Acceptance (2026-09-25 已签)

- 主线程 acceptance: 用户 2026-09-25 verbatim 授权“‘T2 已 CLOSEABLE 待签，T1/T3 未跑’，我都授权可以进行”—— T2 以 CLOSEABLE 关闭。
- R1 retro-acceptance: 同句追认 (R1 支撑映射 + rank 容忍 + fallback assumed 修订接受；B4 retained-assumed，禁 promotion/选点/真实结论)。

## 4. 2026-09-27 追补：合成批 sidecar 的事后手写性质与未解矛盾（不改既有处置）

- 本节为 2026-09-27 只读后端溯源（`docs/research_cycles/M2-REALCOMP/BACKEND_TRACE_REPORT.md` §§10–11、§13(5)）发现的新不一致的落档；§§1–3 的评审结论与 acceptance 一律不变。
- 12 个 `workspace/m2lb_*/backend_used.sidecar.json` 为运行后**手写**：其 mtime 为 2026-09-24 23:28，而对应 `rows.json` 为 23:16–23:18；`grep -rn "backend_used.sidecar" --include=*.py` over `comparison_bench/`、`tools/`、`src/` 返回**空**——没有任何代码写该文件。`BACKEND_CORRECTION.md:3-4` 自述日期 2026-09-24、性质为 additive correction record。因此合成批的所谓“已记录” fallback 标签是事后标注 `assumed` 的断言，不是测量。
- 该批存在**未解的 live 矛盾**：`m2lb_arm_runner.execute` 默认 `decode_fn` 为直接调用 `spa_decode_production` 的闭包（`m2lb_arm_runner.py:1084-1088`），**不是** fallback 包装；而 `spa_decode_production` 在 `ldpc` 缺席时**拒绝**（`:461`，"STOP-BLOCKED: ldpc backend absent … no bit-flip substitute"）。但 12 个合成根均含已译码块（`blocks_done` 58–80，`failures=13`，`verdict=FAIL-early-stop`）。因此要么 2026-09-24 时 `ldpc` 可导入——此时“恒为 numpy-minsum-fallback” sidecar 即为**错误**——要么某个仓外 driver 注入了 fallback `decode_fn`。`m2lb_arm_runner.py` mtime（2026-09-24 23:07）先于合成运行（23:16）。以上记为**开放的不一致，不是裁决**；mtime 不是证明。
- 对本批处置的影响：**无**。本批已处置为 retained-assumed / 禁 promotion，本发现只加强该处置——排除任何将其数字上调的诱惑，且排除以合成批为真实批未知后端做 backfill 的任何用法。本发现**不得**用于回填真实 M2 臂的 `backend_used`。
