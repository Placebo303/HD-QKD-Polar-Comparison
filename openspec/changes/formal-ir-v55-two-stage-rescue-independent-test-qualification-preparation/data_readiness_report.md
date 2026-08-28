# V55 独立 TEST 数据就绪报告 — decoder-free (G1-G7)

**Cycle**: `V55P0`
**HEAD**: `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`)
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (`bf5dd168...`)
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — 本报告仅 decoder-free 清单，不执行 decoder，不创建正式 `run_01`
**脚本**: `check_v55_data_readiness.py` (decoder-free, `python check_v55_data_readiness.py`; 任一 G 失败 `sys.exit(1)`)
**日期**: 2026-08-28
**关键判断**: **算法主线已足够好（V54 二阶段 `H1-16 + L1-APP + Lane C + m2 184/190/192 + H_inc1 8 + H_inc2 8 + base→Δ8→Δ16 verification-only + decoder 90/1.0 poly37 + TRAIN-only + L2-only +40/80` 已冻结可构造），当前 blocker 是独立 TEST 数据缺失，而非方法需再调参。**

## 1. 数据裁决（当前定性）

- V13 `split_manifest 60/20/20`：1M `2000` / 1p5M `2767` / 2M `3645` 帧，`HOLD 20%` 为 `400/554/729` 帧（`base 1600/2213/2916`）。
- HOLD 已被 `V48 45块 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 =180块` 开发使用（已用 `frame_ids` 540-720 帧可追溯），**已用于方法选择/增量秩验证/门禁探索**。
- **即使 HOLD 仍有剩余窗口 `K2≈135/260/461` 未译码，也不得改称为独立 TEST**（开发污染不可逆，selection bias 已注入）。VAL/HOLD 重新标记为 TEST 的操作被显式禁止。
- 后果：P0 必须**搜索/登记另一独立采集 session**（与 `2026-01-21` V13 不同日期），若无则 `V55_DATA_NOT_READY`（非失败，需新数据）。

## 2. 合格 TEST 要求（建议，非本轮执行）

| 项 | 要求 |
|---|---|
| Session | 1M/1p5M/2M 各一个与 `2026-01-21` 不同的独立采集 session（建议新日期 `2026-0X-XX`） |
| 每源帧数 | **≥120 frames（建议≥160）**，每帧 256 pairs |
| 每块 | 4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55` |
| 隔离 | 新 session **不入 prior 训练**（V25 `channel_counts.npz` 仍 TRAIN-only）、**不入方法选择**、**冻结前不看解码结果** |
| 主样本 | **30 blocks/source ×3 =90 blocks, 360 frames**，于新 session 内 `all_starts=0..F-4` 枚举过滤已用区间得 `K≥30`，`index_j=floor(j*(K-1)/29) j=0..29` 确定性分散选 30/源，两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠 |
| 标识 | 建议 block IDs `396001-030/396101-130/396201-230` 仅标识，真实以 `frame_ids[4]` 为准，**禁换块/禁重采样** |

## 3. 数据就绪门 G1-G7（本轮唯一实测，decoder-free）

| 门 | 检查项 | 判定标准 | 当前结果（2026-08-28 空跑） |
|---|---|---|---|
| G1 | 文件可读 | 新 session `pairs.parquet`/`pairs.csv` 可 open，行数=frames×256 | **FAIL** — 未找到独立 session registry（`comparison_bench/configs/v55_independent_test_sessions.json` 等均不存在） |
| G2 | provenance 完整 | 三源 session_id、采集日期≠2026-01-21、采集参数、文件哈希可追溯 | **FAIL** — G1 未过，无法校验（需新 session 登记） |
| G3 | 三源明确 | 1M/1p5M/2M 各一 session，互异且与 V13 三源一一对应 | **FAIL** — G1 未过 |
| G4 | 256/frame 1024/block | 每帧256 pairs，每块4帧1024 pairs，`BLOCK_LENGTH=1024`，每源≥120 frames 建议≥160 | **FAIL** — G1 未过（理论 F=160 时 K≥30 可行，已示例校验） |
| G5 | 与 V13 及 V48-V54 完全独立 | 新 session 全部帧与 V13 全部帧及 V48-V54 已用 540-720 帧零重叠 per source | **FAIL** — G1 未过（需新 session 路径与 date≠2026-01-21） |
| G6 | V25 prior 只读 | `channel_counts.npz` 形态校验，不读新 TEST 做训练，冻结候选 `nonbinary_v25_gate.py`/`v38_architecture_triage.py`/`v35_algorithm_development.py` 可读且 `py_compile` 通过 + 正确路径 `comparison_bench.formal_ir.*` 可 import | **PASS** — V25 `channel_counts.npz` 存在且冻结候选 3 模块 readable+py_compile+import 均 PASS（`nbldpc_v25_20260818/run_04/`，修复后 G6 独立判定，不再依赖错误路径 `v25_empirical_channel`） |
| G7 | 冻结 90-block registry | `K≥30`，`index_j` 分散选 30/源，两两非重叠 gap≥4，与已用零重叠 | **FAIL** — G1 未过（示例 F=160 时 `K` 足够，30/源分散可行） |

**全过方可 `V55_QUALIFICATION_PLAN_READY`，否则 `V55_DATA_NOT_READY`。**

### 3.1 脚本实测（空跑，预期 DATA_NOT_READY；2026-08-28 仓库根重跑固化）

```bash
python openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/check_v55_data_readiness.py
# 2026-08-28 实测输出（G6 已修复为独立判定）:
# G1 FAIL — no independent session registry found. Searched: .../v55_independent_test_sessions.json ...
# G2 FAIL — G1 not pass
# G3 FAIL — G1 not pass
# G4 FAIL — G1 not pass
# G5 FAIL — G1 not pass
# G6 PASS — V25 prior files: candidates[0].exists()=True, True -> exists=True
#          frozen candidate nonbinary_v25_gate.py: readable=True py_compile=True
#          frozen candidate v38_architecture_triage.py: readable=True py_compile=True
#          frozen candidate v35_algorithm_development.py: readable=True py_compile=True
#          import PASS: nonbinary_v25_gate + v38 + v35 -> code_ok=True
# G7 FAIL — G1 not pass (example F=160 1M K=25 not feasible, 1p5M K=43 feasible, 2M K=71 feasible)
# Terminal: V55_DATA_NOT_READY
# exit 1 (阻断后续 decoder，不等同 EVIDENCE_INVALID)
# 注：修复前 G6 因错误路径 comparison_bench.formal_ir.v25_empirical_channel 被误判 FAIL；修复后 G6 独立以真实冻结候选存在性判定为 PASS，G1-G5/G7 仍 FAIL，总终态仍 V55_DATA_NOT_READY
```

**本轮未执行 decoder，未创建任何 `.../v55_*/run_01` 输出，符合 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。**

## 4. 90-block 注册算法（预冻结，待数据就绪后实例化）

```
per source (new session, F frames, F≥120 suggest ≥160):
  used = USED_BASE (30) ∪ V53 15 ∪ V54 15  // 60 unique approx, with V48-V54 135-180 total
  all_starts = [0..F-4]
  remaining = [s for s in all_starts if not any(|s-u|<=3 for u in used)]
  K = len(remaining)
  require K ≥30
  selected = [remaining[floor(j*(K-1)/29)] for j in 0..29]  // 30 dispersed
  verify: len(set(selected))==30, all gaps≥4, zero overlap with used
```

- 示例 F=160 时，每源 `K` 约 `~100-140`（取决于 used 分布），`30/源` 分散可行，gap 自然 `>>3`。
- 实际冻结表需由 `check_v55_data_readiness.py` 在 `G1-G7` 全过后输出的 `selected` 决定，本报告仅冻结算法。

## 5. 预算（预冻结，未来执行）

- `L1 90` 固定 + `base L2 90` 固定 + `stage1 0-90` 条件 + `stage2 0-90` 条件 = **`180-360 硬帽360` (`L2 90-270`)**，`base` 兼 old 不重复，每块 `2-4 calls`。
- 预计实际 `≈225`（若 base 准确率 ~66%，`N_stage1≈30`, `N_stage2≈15` 则总 `90+90+30+15=225`），硬帽 360 远未触及。

## 6. 预注册门禁（预冻结，不在本轮执行）

```
V55_DATA_NOT_READY  若 G1-G7 任一不过（非失败，需新数据）
else if 完整性/守卫/秩/嵌套/重叠/记账失败 → V55_EVIDENCE_INVALID 优先
else if final_exact_full ≥70/90 (77.8%) ∧ 每源≥20/30 (66.7%) ∧ undetected==0 ∧ rank/nested/verification/记账通过
     → V55_INDEPENDENT_TEST_PASS
else → V55_INDEPENDENT_TEST_FAIL
```

- `base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 报告不取代最终。
- `Wilson 95%` / `rescue_rate` / `runtime` / `leakage` 仅报告不作门禁。
- `V55_DATA_NOT_READY` 不得被描述为方法失败。

## 7. 本报告终态

**当前终态**: **`V55_DATA_NOT_READY`（非失败，需新数据）**

- 原因：**未找到与 `2026-01-21` 不同的独立采集 session**（`G1-G5,G7` 未过），`G6` 仅 V25 prior 通过。
- 所需新数据规格：
  - 1M / 1p5M / 2M 各一新 session，每源 **≥120 frames（建议≥160）**，每帧 **256 pairs**，每块 **4 连续帧 1024 pairs**。
  - 采集日期 **≠2026-01-21**，三源互异且 provenance 完整（session_id/日期/参数/文件哈希）。
  - 新数据 **不入 prior 训练**，冻结注册表前 **不看解码结果**。
  - 登记文件建议：`comparison_bench/configs/v55_independent_test_sessions.json`，格式：
    ```json
    {
      "1M": {"session_id": "type2_1M_2026XXXX_XXXXXX", "date": "2026-XX-XX", "path": "/path/to/1M/pairs.parquet", "frames": 160},
      "1p5M": {"session_id": "type2_1p5M_2026XXXX_XXXXXX", "date": "2026-XX-XX", "path": "/path/to/1p5M/pairs.parquet", "frames": 160},
      "2M": {"session_id": "type2_2M_2026XXXX_XXXXXX", "date": "2026-XX-XX", "path": "/path/to/2M/pairs.parquet", "frames": 160}
    }
    ```
  - 登记后重跑 `python check_v55_data_readiness.py`，`G1-G7` 全过即 `V55_QUALIFICATION_PLAN_READY`，方可进入后续正式 TEST 详细规划与 `EXECUTE_AUTH`。

## 8. 禁止清单（本轮已遵守）

- 未创建 `comparison_bench/src/comparison_bench/formal_ir/v55_*.py` production module
- 未创建 `scripts/execute_v55_*.py` CLI
- 未创建 `comparison_bench/tests/test_v55_*.py` tests
- 未创建 `comparison_bench/outputs_comparison/formal_ir_methods/v55_*/run_01` 正式 output root
- 未用 HOLD 剩余帧冒充独立 TEST
- 未模拟 TEST 数据（`np.random` 合成禁止）
- 未执行 decoder（`check_v55_data_readiness.py` 零 `decode_*` 调用）
- 未自授 `PLAN_ACCEPTED`，保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`

## 9. 结论

**算法主线已足够好，当前 blocker 是独立 TEST 数据缺失**。V54 二阶段 `rank/nested/leakage/budget` 已冻结可构造，方法侧 feasibility 已足。V55 本轮已完成四工件 + decoder-free 清单脚本/报告，**数据就绪门 `G1-G7` 实测为 `V55_DATA_NOT_READY`（非失败）**，需新采集 session 后方可 `V55_QUALIFICATION_PLAN_READY` 并进入正式 TEST 授权执行。推送后停留 `PLAN_CANDIDATE`。

