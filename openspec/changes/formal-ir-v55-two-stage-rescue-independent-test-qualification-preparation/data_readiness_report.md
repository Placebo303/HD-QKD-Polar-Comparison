# V55 独立 TEST 数据就绪报告 — decoder-free 分层 G1-G7（stratified）

**Cycle**: `V55P0`
**HEAD**: `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`, 分层修订)
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (`bf5dd168...`)
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — 本报告仅 decoder-free 分层清单，不执行 decoder，不创建正式 `run_01`
**脚本**: `check_v55_data_readiness.py` (decoder-free stratified, `python check_v55_data_readiness.py`; 任一目标域 stratum G 失败 `sys.exit(1)`，分层 partial 允许)
**日期**: 2026-08-28 (分层修订)
**关键判断**: **算法主线已足够好（V54 二阶段 `H1-16 + L1-APP + Lane C + m2 184/190/192 + H_inc1 8 + H_inc2 8 + base→Δ8→Δ16 verification-only + decoder 90/1.0 poly37 + TRAIN-only + L2-only +40/80` 已冻结可构造），当前 blocker 是分层独立 TEST 数据缺失，而非方法需再调参。**

## 1. 数据裁决（当前定性，分层）

- V13 `split_manifest 60/20/20`：1M `2000` / 1p5M `2767` / 2M `3645` 帧，`HOLD 20%` 为 `400/554/729` 帧（`base 1600/2213/2916`）。
- HOLD 已被 `V48 45块 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 =180块` 开发使用（已用 `frame_ids` 540-720 帧可追溯），**已用于方法选择/增量秩验证/门禁探索**。
- **即使 HOLD 仍有剩余窗口 `K2≈135/260/461` 未译码，也不得改称为独立 TEST**（开发污染不可逆，selection bias 已注入）。VAL/HOLD 重新标记为 TEST 的操作被显式禁止。
- 后果：P0 必须**搜索/登记另一独立采集 session 集合**（与 `2026-01-21` V13 不同日期，按物理条件分层），若无则 `V55_DATA_NOT_READY`（分层，非失败，需新数据）。
- **目标运行域声明（冻结）**：`D_target = {1M, 1p5M, 2M}` 三主 stratum 为资格目标域；超出目标域的新物理条件（新地点/器件/信道参数）为 exploratory stratum，仅泛化探索不计入门禁。

## 2. 库存清单 — 可用独立数据集及其物理条件（先列后检）

| 库存项 | 采集日期 | 地点 | 器件 | 信道参数（延迟/功率/率/衰减/温度等） | 文件路径 | 帧数 | 状态 |
|---|---|---|---|---|---|---|---|
| （待登记） | ≠2026-01-21 | — | — | 延迟 ±50ps 等 | `.../pairs.parquet` | ≥120 (建议≥160) | 未找到 — 需新采集 |

- 脚本 `check_v55_data_readiness.py` 先在 `PROJECT_DATA_ROOT` / `comparison_bench/configs/` / 外部采集目录搜索所有可用的其他独立数据集，形成 `available_independent_datasets` 库存表（per stratum `session_id / date / location / device / channel_params / file hash / frames`）。
- 当前实测：未找到独立 session registry（`comparison_bench/configs/v55_independent_test_sessions.json` 等均不存在），库存为空，`G1-G5,G7` 按 strata 均 FAIL，符合预期 `DATA_NOT_READY`。

## 3. 合格 TEST 要求（分层，建议，非本轮执行）

| 项 | 要求 |
|---|---|
| 库存 | 先列所有可用独立数据集及其物理条件，按物理条件分 strata，形成 `available_independent_datasets` 库存 |
| 目标域 | `D_target = {1M,1p5M,2M}` 三主 stratum（各对一物理条件类型），目标域全覆盖才判 qualification |
| 每 stratum 帧数 | **≥120 frames（建议≥160）**，每帧 256 pairs |
| 每块 | 4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_stratified` |
| 隔离 | 新 session **不入 prior 训练**（V25 `channel_counts.npz` 仍 TRAIN-only）、**不入方法选择**、**冻结前不看解码结果** |
| 主样本（平衡） | **每主 stratum `B=15 或 30` blocks 平衡**，`S=3→45 或 90` blocks，`S×B×4` frames；于新 session 每 stratum 内 `all_starts=0..F-4` 枚举过滤已用区间得 `K≥B`，`index_j=floor(j*(K-1)/(B-1)) j=0..B-1` 确定性分散选 B/ stratum，两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠；不足 `K<B` 仅 exploratory 不强行凑 `S×B` |
| 标识 | 建议 block IDs 按 stratum 延续（`B=30` 时 `396001-030/396101-130/396201-230`；`B=15` 时 `397001-015` 等）仅标识，真实以 `frame_ids[4]` 为准，**禁换块/禁重采样** |
| 预算成比例 | `S×B=45→90-180 (L2 45-135)`；`S×B=90→180-360 (L2 90-270)`；一般 `2SB-4SB` 硬帽 |
| explorer | 数据不足的 stratum 仅 exploratory generalization，不计入门禁分母 |

## 4. 数据就绪门 G1-G7（本轮唯一实测，decoder-free，分层按 strata）

| 门 | 检查项 | 判定标准 | 当前结果（2026-08-28 分层空跑，预期 DATA_NOT_READY） |
|---|---|---|---|
| G1 | 文件可读 | 每 stratum 新 session `pairs.parquet`/`pairs.csv` 可 open，行数=frames×256 | **FAIL per stratum** — 未找到独立 session registry（`comparison_bench/configs/v55_independent_test_sessions.json` 等均不存在） |
| G2 | provenance 完整 | 各 stratum session_id、采集日期≠2026-01-21、采集参数（地点/器件/延迟±50ps/功率/率）、文件哈希可追溯 | **FAIL per stratum** — G1 未过，无法校验（需新 session 按 strata 登记物理条件） |
| G3 | 各 stratum 明确 | `D_target` 各 stratum 各一 session，互异且与 V13 对应物理条件一一对应；exploratory 额外列出 | **FAIL per stratum** — G1 未过 |
| G4 | 256/frame 1024/block | 每 stratum 每帧256 pairs，每块4帧1024 pairs，`BLOCK_LENGTH=1024`，每 stratum ≥120 frames 建议≥160 | **FAIL per stratum** — G1 未过（理论 `F=160` 时 per stratum `K≥B` 可行，已示例校验） |
| G5 | 与 V13 及 V48-V54 完全独立 | 新 session 各 stratum 全部帧与 V13 全部帧及 V48-V54 已用 540-720 帧零重叠 per stratum | **FAIL per stratum** — G1 未过（需新 session 路径与 date≠2026-01-21 按 strata） |
| G6 | V25 prior 只读 | `channel_counts.npz` 形态校验，不读新 TEST 做训练，冻结候选 `nonbinary_v25_gate.py`/`v38_architecture_triage.py`/`v35_algorithm_development.py` 可读且 `py_compile` 通过 + 正确路径 `comparison_bench.formal_ir.*` 可 import | **PASS** (全局) — V25 `channel_counts.npz` 存在且冻结候选 3 模块 readable+py_compile+import 均 PASS |
| G7 | 冻结 per-stratum registry | 每目标域 stratum `K≥B`，`index_j` 分散选 B/ stratum，两两非重叠 gap≥4，与已用零重叠；`K<B` 则该 stratum `G7_FAIL → DATA_NOT_READY` 但允许 partial | **FAIL per stratum** — G1 未过（示例 `F=160` 时 per stratum `K` 足够，`B=15/30` 分散可行；`B=15` 更易满足） |

**目标域全 strata 全过方可 `V55_QUALIFICATION_PLAN_READY`，否则 `V55_DATA_NOT_READY`（分层，partial 允许）。**

### 4.1 脚本实测（分层空跑，预期 DATA_NOT_READY；2026-08-28）

```bash
python openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/check_v55_data_readiness.py
# 预期输出（分层）:
# Inventory: no registry -> G1 FAIL per stratum
# G1 1M: FAIL, 1p5M: FAIL, 2M: FAIL
# G2 1M: FAIL, 1p5M: FAIL, 2M: FAIL
# G3 global FAIL
# G4 per stratum FAIL
# G5 per stratum FAIL
# G6 PASS (global)
# G7 per stratum FAIL (example F=160 K feasible but no data)
# Terminal: V55_DATA_NOT_READY (stratified partial) 0/3 strata READY
# exit 1 (阻断后续 decoder，不等同 EVIDENCE_INVALID)
```

**本轮未执行 decoder，未创建任何 `.../v55_*/run_01` 输出，符合 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。**

### 4.2 按 strata 的 `K/index_j` 示例

```
per stratum (new session, F frames, F≥120 suggest ≥160):
  used = USED_BASE (30) ∪ V53 15 ∪ V54 15  // per source
  all_starts = [0..F-4]
  remaining = [s for s in all_starts if not any(|s-u|<=3 for u in used)]
  K = len(remaining)
  require K ≥ B (B=15 or 30 balanced)
  selected = [remaining[floor(j*(K-1)/(B-1))] for j in 0..B-1]  // B dispersed
  verify: len(set(selected))==B, all gaps≥4, zero overlap with used per stratum
```

- `F=160` 时 per stratum `K≈100-140`，`B=15` 与 `B=30` 分散均可行，`B=15` 更宽松；实际冻结表需由脚本在 `G1-G7` 全过后输出 per stratum `selected` 决定。

## 5. 预算（预冻结，未来执行，分层成比例）

- `L1 S×B` 固定 + `base L2 S×B` 固定 + `stage1 0–S×B` 条件 + `stage2 0–S×B` 条件 = **`2SB–4SB 硬帽 (L2 SB–3SB)`**。
- `S=3,B=15 → 45+45+≤45+≤45=90-180 硬帽180 (L2 45-135)`。
- `S=3,B=30 → 90+90+≤90+≤90=180-360 硬帽360 (L2 90-270)`。
- `base` 兼 old 不重复，每块 `2-4 calls`；每 stratum `2B-4B`。
- 预计实际 `≈ S×B×(1 + base pass率 + rescue)`，硬帽远未触及。

## 6. 预注册门禁（预冻结，不在本轮执行，分层）

```
V55_DATA_NOT_READY  若任一目标域 stratum G1-G7 不过（分层，非失败，需新数据；exploratory partial 不阻塞 READY 但该 stratum 仅探索）
else if 完整性/守卫/秩/嵌套/重叠/记账失败 → V55_EVIDENCE_INVALID 优先
else if per_stratum final_exact_full ≥ (B==15?10:20)/B 每目标域 stratum 均满足
        ∧ coverage_exact_full ≥ ceil(0.778×S×B) (S=3,B=15→35/45; S=3,B=30→70/90)
        ∧ undetected==0 全局 ∧ rank/nested/verification/记账通过
     → V55_INDEPENDENT_TEST_PASS
else → V55_INDEPENDENT_TEST_FAIL
```

- **主要报告**：各 stratum 分别报告 `exact_full` / `verify` / `rescue_rate_stage1/2` / 泄漏三档与 `per_stratum_avg`；不混成单一总分作首要结论。
- 只有覆盖目标域 `D_target`（`{1M,1p5M,2M}`）时才判 qualification；`base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 报告不取代最终。
- `Wilson 95%` / `rescue_rate` / `runtime` / `leakage` 仅报告不作门禁（按 strata）。
- `V55_DATA_NOT_READY`（含 partial）不得被描述为方法失败；不足 strata 仅 exploratory，不计入门禁分母。
- **undetected 仍 0 全局**（任一 stratum 出现即 FAIL）。

## 7. 本报告终态（分层）

**当前终态**: **`V55_DATA_NOT_READY`（分层，非失败，需新数据；0/3 目标域 strata READY，partial）**

- 原因：**未找到与 `2026-01-21` 不同的分层独立采集 session**（各 stratum `G1-G5,G7` 未过），`G6` 仅 V25 prior 通过；库存为空。
- 所需新数据规格（按 strata）：
  - 先列 `available_independent_datasets` 库存：所有可用的其他独立数据集及其物理条件（日期/地点/器件/延迟/功率/率/信道参数）。
  - 目标域 `D_target={1M,1p5M,2M}` 各一新 session，每 stratum **≥120 frames（建议≥160）**，每帧 **256 pairs**，每块 **4 连续帧 1024 pairs**，平衡 `B=15 或 30`（推荐 30，`S=3` 时共 45 或 90 blocks）。
  - 采集日期 **≠2026-01-21**，各 stratum 互异且 provenance 完整（session_id/日期/地点/器件/参数/文件哈希）。
  - 新数据 **不入 prior 训练**，冻结注册表前 **不看解码结果**。
  - 登记文件建议：`comparison_bench/configs/v55_independent_test_sessions.json`（分层格式）：
    ```json
    {
      "strata": {
        "1M": {"session_id": "type2_1M_2026XXXX_XXXXXX", "date": "2026-XX-XX", "location": "labA", "device": "detectorX", "channel_params": {"delay_ps": -50, "rate_M": 1}, "path": "/path/to/1M/pairs.parquet", "frames": 160},
        "1p5M": {"session_id": "type2_1p5M_2026XXXX_XXXXXX", "date": "2026-XX-XX", "location": "labA", "device": "detectorX", "channel_params": {"delay_ps": 50, "rate_M": 1.5}, "path": "/path/to/1p5M/pairs.parquet", "frames": 160},
        "2M": {"session_id": "type2_2M_2026XXXX_XXXXXX", "date": "2026-XX-XX", "location": "labA", "device": "detectorX", "channel_params": {"delay_ps": 50, "rate_M": 2}, "path": "/path/to/2M/pairs.parquet", "frames": 160}
      },
      "target_domain": ["1M","1p5M","2M"],
      "blocks_per_stratum": 30
    }
    ```
    兼容旧扁平 `{"1M":{...},"1p5M":{...},"2M":{...}}`，但推荐分层 `strata` 格式；exploratory strata 可额外加入 `strata` 下。
  - 登记后重跑 `python check_v55_data_readiness.py`，目标域 `G1-G7` 全过即 `V55_QUALIFICATION_PLAN_READY`，方可进入后续正式 TEST 详细规划与 `EXECUTE_AUTH`；`K<B` 的 stratum 仅 exploratory。

## 8. 禁止清单（本轮已遵守，分层）

- 未创建 `comparison_bench/src/comparison_bench/formal_ir/v55_*.py` production module
- 未创建 `scripts/execute_v55_*.py` CLI
- 未创建 `comparison_bench/tests/test_v55_*.py` tests
- 未创建 `comparison_bench/outputs_comparison/formal_ir_methods/v55_*/run_01` 正式 output root
- 未用 HOLD 剩余帧冒充独立 TEST（分层校验）
- 未模拟 TEST 数据（`np.random` 合成禁止，按 strata）
- 未执行 decoder（`check_v55_data_readiness.py` 零 `decode_*` 调用，分层）
- 未自授 `PLAN_ACCEPTED`，保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- 未将不足 strata 强行凑足 `S×B` 混算总分（分层 partial 允许）

## 9. 结论（分层）

**算法主线已足够好，当前 blocker 是分层独立 TEST 数据缺失**。V54 二阶段 `rank/nested/leakage/budget` 已冻结可构造，方法侧 feasibility 已足。V55 本轮已完成四工件分层修订 + decoder-free 分层清单脚本/报告，**数据就绪门分层 `G1-G7` 实测为 `V55_DATA_NOT_READY`（分层，0/3 READY，非失败）**，需分层新采集 session 后方可 `V55_QUALIFICATION_PLAN_READY`（目标域全 READY）并进入正式 TEST 授权执行。推送后停留 `PLAN_CANDIDATE`。
