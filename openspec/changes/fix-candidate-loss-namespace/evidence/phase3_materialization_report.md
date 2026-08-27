# Phase 3 全量物化 + 门校验报告 — fix-candidate-loss-namespace（T3.1–T3.4）

**状态：D1/D2/D4 完成；D3 中 G2/G4 完成、G3 按修订语义执行后 FAIL（10/83 序违例）——按停止规则就地停止，未进入 Phase 4。**
任务工作根：`workspace/fix-candidate-loss-namespace/p3_20260825_232345/`（PID/日志/脚本全存）。
全程增量写入；未触碰 20dB 及任何既有产物；旧候选只读。

---

## 0. 范围裁决记录（现场修订）

- 任务包原文"16dB 受影响 56 格"与 `affected_cells.csv` 冲突：CSV 中涉及 16dB 的格 = **83**
  （仅10∩16=27 + 仅16∩6=27 + 三档共享=29；56 仅为单对 10∩16 计数）。
  **用户于 2026-08-25 现场裁决取 83 格清单**（否则 16∩6 的 27 个 16dB 格保留污染字节，修复不完整）。
- D0 门语义修订（design §4 G3 2026-08-25 主线修订）已实现并通过 self-test + pytest（见 §5）。

## 1. T3.1 全量物化（done）

分离进程模式：`Start-Process -PassThru`（python -u），stdout/stderr 重定向至任务根，PID 落盘
（`run_<tier>_pid.txt` / `run_<tier>_log.txt` / `run_<tier>_err.txt`），轮询至退出。
参数钉死不变：`pairing_v2-nearest_occ0_maxpairs0_thr40000_aligndebug0`，无任何改参重跑。

| 档 | 格数 | ok | fail | 启动→结束 | 耗时 | 备注 |
|---|---|---|---|---|---|---|
| 10dB | 121（全网格） | **121** | **0** | 23:24:08→23:47:09 | 23m01s | PID 7156 |
| 6dB | 121（全网格） | **115** | **0** | 23:47:43→00:11:32 | 23m49s | PID 50144；--resume 跳过试点 6 格（materialize_ok=1） |
| 16dB | 83（受影响清单） | **83** | **0** | 00:12:08→00:24:40 | 12m32s | PID 52160 |

物化总计 **59m22s**，单格约 10–13 s（预算 ≤4h 内）。失败格：无。

## 2. T3.2 chan_ll_table.npy 与溯源字段（done）

- 全格扫描（强于抽查）：6dB 121、10dB 121、16dB 83 —— `chan_ll_table.npy` 全部存在且非零；
  sidecar blk 目录与池目录一一对应。
- 每档深检前 5 格（≥要求）：`materialize_ok=1`、`materialize_out_dir` 指向
  `results/real_sequences_ns/<src_tag>/…` 命名空间池、metrics/joint 指纹非空、
  `source_ttbin_paths` 含本档原始记录目录名、`sequence_is_sampled=0` —— 全部通过。
  脚本与输出：`d2_chan_ll_provenance_check.py` → `[D2] OK`。

## 3. T3.3 门校验

### G2 跨档字节唯一性

**新档互检（修复有效性主门）**：新 6dB×10dB×16dB 三根同跑，
比较 **574 组**（121×2 + 121×2 + 83×2 + 83×2 + 83×2），碰撞 **0** ⇒ **PASS**。

**任务书指定的旧参照对（6 对）**：

| 比较对 | 比较数组数 | 碰撞 | 结论 |
|---|---|---|---|
| 新6 vs 旧20 | 242 | 0 | PASS |
| 新10 vs 旧20 | 242 | 0 | PASS |
| 新16 vs 旧20 | 166 | 0 | PASS |
| 新6 vs 旧16 | 242 | 14 数组 / 7 格 | 归因见下 |
| 新6 vs 旧10 | 242 | 6 数组 / 3 格 | 归因见下 |
| 新10 vs 旧16 | 242 | 70 数组 / 35 格 | 归因见下 |

**碰撞归因（`g2_collision_attribution.py`，全部闭环）**：
45 个碰撞格全部 ∈ `affected_cells.csv`；且 90/90 数组满足"旧X == 旧Y"签名——即该池键
在旧数据中持有的是**新 X 档的真源字节**，旧 Y 档当年借用了它（污染方向证据）。
碰撞格清单：
- 新6 vs 旧16 (7)：d1024_bw30, d8_bw20, d8_bw30, d8_bw40, d8_bw50, d8_bw60, d8_bw80
- 新6 vs 旧10 (3)：d64_bw60, d8_bw20, d8_bw30
- 新10 vs 旧16 (35)：d128_bw20/30/40/50/60/80, d16_bw120/150/180/200, d256_bw20/30/40/50/60/80/100/120/150, d32_bw20/30/40/50/60/80/100/120/150, d4_bw60/80, d64_bw100/120/150/180/200

判定：**旧参照对碰撞不构成重建缺陷**——它们恰好逐格确认了事件取证结论（共享池双向借用）；
真正的修复有效性由新档互检 574 组零碰撞保证。对干净参照 old20 的三对全部零碰撞。

### G3 物理合理性（修订语义）— **FAIL，就地停止**

门条件 = 可比格跨档序 ser(6)>ser(10)>ser(16)>ser(20)（83 个四档全覆格，--min-cells 83）：

- **新重建数据：10/83 违例 ⇒ FAIL**。违例格全部位于 d512–d2048 高维区，
  6/10/16 三档 ser 近简并（差值在第 3 位小数量级，如 d1024_bw150: 0.2319 vs 0.2372 vs 0.2330），
  20dB 明显更低（0.06–0.11）；无精确相等。
- **关键对照——旧四档数据同门跑：95/121 违例**，其中大量为**精确相等**（如 d1024_bw20 三档
  ser 完全相同 0.41168——正是共享池字节污染的直接签名）。
  即严格逐格全序在该网格上**新旧都不成立**；旧数据的"序表现更差"，其部分违例恰是本变更要修的污染本身。
- isolation 清单（verdict≠PASS，非门条件，仅记录）：6dB 109/121、10dB 102/121、16dB 67/83、
  20dB(旧参照) 77/121；合计 355 条，明细见 `g3_isolation_flips.csv`（kind=isolation 行）。
  对照旧档 FAIL 率（94/89/89/77 每121）：新数据 FAIL 率略升（污染曾使部分格"看起来更好"）。

### G4 溯源完整性 — PASS

446 个 sidecar（含 old20 参照 121）全查：metrics/joint 指纹、source_ttbin_path 与各档原始
记录目录匹配、processing_rule_version=pairing_v2、sequence_is_sampled=0、params 快照齐备。

## 4. T3.4 MANIFEST.csv 定稿（done）

- 表头新增第 10 列 `chan_ll_sha256`（驱动脚本同步写入；试点期 6 行已回填）。
  驱动行格式变更属本变更自身产物的追加式扩展，无既有消费方。
- `results/real_sequences_ns/MANIFEST.csv`：**325 行**（loss6dB 121 + loss10dB 121 + loss16dB 83）。
- 全量对账（`finalize_manifest.py`）：每行 ttbin 路径存在性 + a_eff/b_eff/chan_ll sha256
  逐一从盘重算比对 —— **全部一致**；各档行数符合预期。

## 5. D0 门脚本修订与自检（done）

- `tools/verify_candidate_namespace_gates.py` gate_g3 重写：
  序校验（可比格、含 verdict=FAIL 格的有限 ser）为唯一门 FAIL 条件；
  verdict=FAIL 格入 isolation 清单（非门控）；新增 `reference_roots` 做 PASS↔FAIL 翻转检测
  （needs-explanation 清单，非门控）；`--min-cells` 保留；`detail_csv` 导出两清单全量。
- MANIFEST_HEADER 增加 `chan_ll_sha256`；CLI 新增 `--g3-reference-roots`、G3 复用 `--out`。
- self-test 同步：序颠倒仍 FAIL ✓；单 verdict=FAIL 不再 FAIL 且必现于 isolation ✓；
  翻转必被列出 ✓。（self-test 曾抓出翻转查询的 tier/cell 键序 bug，已修。）
- workspace pytest：**4 passed**（A3 断言 / A5 tamper / A6 回路 / self-test CLI）。

## 6. 翻转格清单（35 格，全部 new=FAIL old=PASS）

方向单一（无一例 FAIL→PASS），机制与试点 C4 解释一致：污染池使这些格旧 ser 偏低越过
0.1 判据呈 PASS；真源重建后 ser 回归真实值越过判据呈 FAIL。属"修复揭示真实质量"而非退化。

- 6dB (15)：d1024_bw180, d1024_bw200, d128_bw150, d2048_bw150, d2048_bw180, d2048_bw200,
  d256_bw180, d256_bw200, d4096_bw180, d4096_bw200, d4_bw150, d512_bw180, d512_bw200,
  d64_bw150, d8_bw150
- 10dB (13)：d1024_bw150, d1024_bw180, d1024_bw200, d2048_bw150, d2048_bw180,
  d2048_bw200, d256_bw180, d256_bw200, d512_bw180, d512_bw200, d64_bw150, d8_bw150, d8_bw80*
  *（以 `g3_isolation_flips.csv` kind=flip 行为准）
- 16dB (7)：详见 `g3_isolation_flips.csv`

## 7. BLOCKER（单一决策需求）

G3 修订门在新数据上 FAIL（10/83 序违例）。诊断结论：

1. 严格逐格全序 ser(6)>ser(10)>ser(16)>ser(20) 在**旧数据上违反更重**（95/121，含大量污染性
   精确相等）⇒ 该判据作为逐格硬门从未被本网格满足过；
2. 新数据违例集中于高维近简并区（三档 ser 差 <1%），20dB 层清晰分离；无精确相等、无污染签名；
3. 非脚本 bug（self-test/pytest 全绿；同门旧数据同样 FAIL 证明判据本身过严）。

按停止规则未调参、未绕过、未进入 Phase 4。需主线裁决（示例选项，非提案）：
(a) 将 G3 序条件改为容差判据（如允许近简并 δ<ε 的反序，或仅要求 20dB 显著低于 6/10/16 带）；
(b) 改为聚合统计检验而非逐格全序；(c) 维持严格门并接受该 10 格为已知例外白名单。
裁决后仅需重跑 G3 校验（毫秒级），无需重新物化。

## 8. 产物清单（本次新增/修改）

新增/修改（代码）：
- `tools/verify_candidate_namespace_gates.py`（G3 修订 + MANIFEST 表头 + CLI）
- `tools/materialize_loss_namespaced_candidates.py`（MANIFEST 行加 chan_ll_sha256）
- `openspec/changes/fix-candidate-loss-namespace/evidence/phase3_materialization_report.md`（本文件）
- `openspec/changes/fix-candidate-loss-namespace/tasks.md` 勾选更新（T3.1–T3.4）

新增（产物，均为追加）：
- `results/real_sequences_ns/{loss10dB,loss16dB}/…` ×121+83 格 + `MANIFEST.csv` 325 行定稿
- `results/authoritative_nsfix/e2e_{10dB,16dB}_fullgrid_pairing_v2_candidate_lossfix_v1/sidecars/…`
  ×121+83 格（6dB 目录在试点期已有 121 格中的 6 格，本次补足至 121）
- `workspace/fix-candidate-loss-namespace/p3_20260825_232345/`（PID、日志、points_16dB.txt、
  finalize_manifest.py、d2_chan_ll_provenance_check.py、g2_collision_attribution.py、
  g3_isolation_flips.csv）

未触碰：`results/authoritative/**`（只读参照）、`results/real_sequences/**`（残余隔离待 T5.3）、
20dB 一切产物、既有事件证据。
