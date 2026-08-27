# design — fix-candidate-loss-namespace

**DRAFT — 待用户授权后方可实施。**

## 1. 调查结论摘要（P1–P4）

### P1 物化工具链考古

- **入口**：`experiments/run_e2e_pipeline.py`。CLI `--ttbin/--ttbin-override`（L1139-1146）
  设置 `HDQKD_TTBIN_FILE_OVERRIDE`（L1175），配合
  `--materialize-processing-rule-version pairing_v2`、`--out-root results/e2e_<tier>_fullgrid_pairing_v2_candidate`。
  repair 路径以 `materialize_missing_real_seq=1, joint_source_mode="from_ttbin"` 调用
  （run_e2e_pipeline.py L255-268）。
- **核心函数**：`src/workflow/export_joint_sequence_sidecar.py::materialize_real_sequences_for_point`
  （L963-1372）。池路径硬编码于 L1483：
  `REPO_ROOT/"results"/"real_sequences"/f"d{d}_bw{bw}"/f"blk{block_index}"` —— **命名空间缺陷就在这一行**。
- **chan_ll_table.npy**：同文件 `_build_chan_ll_table`（L393-404），由 joint sparse 决定性生成。
- **工具仍在仓内可用**（冻结基线，只读使用无需改动；池根参数化属本变更覆盖的最小修改）。
- sidecar 的 `source_fingerprints.metrics_file` 指向 `workspace\override_points\<d>_<bw>\results\attempt_0\ttbin_parsing\ttbin_metrics.json`；
  该 workspace 目录已删除，但 **全量 121 格归档存在于 `results/archive/workspace_override_points/`**。
  注意：归档内 `resolved_config.json` 已被 2026-04-26 之后的运行覆盖（现指向 ASENoise 源），
  归档 ttbin_metrics.json 是否仍为 2026-03-18 原件**须以 sha256 对账 sidecar 指纹后才能采信**。

### P2 原始 ttbin 可用性（逐档，已逐一验证目录与文件存在）

| 档 | 记录目录（`D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\` 下） | 主文件 | 判定 |
|---|---|---|---|
| 20dB | `Type2_5s_20dB_2026-01-30_224943\` | `Type2_5s_20dB_2026-01-30_224943.ttbin`（+`.1` 分片） | 可得（本档无需重建） |
| 16dB | `Type2_5s_16dB_2026-01-30_224900\` | `Type2_5s_16dB_2026-01-30_224900.ttbin`（+`.1` 分片） | **可得** |
| 10dB | `Type2_5s_10dB_2026-01-30_224808\` | `Type2_5s_10dB_2026-01-30_224808.ttbin`（+`.1` 分片） | **可得** |
| 6dB | `Type2_5s_6dB_2026-01-30_224719\` | `Type2_5s_6dB_2026-01-30_224719.ttbin`（+`.1` 分片） | **可得** |

证据来源：各候选档全部格的 `sidecar_meta.json → used_params.source_ttbin_paths` 与
`symbolization_snapshot.ttbin_file` 字段一致指向上述路径；WSL 侧经
`wsl-env.sh` 的 `PROJECT_DATA_ROOT=/mnt/d/Data` 等价可达。
四档原始数据**无缺失** ⇒ 无需降级备选策略；design §6 的备选条款仅作应急预案保留。

### P3 确定性评估

**结论：同一 ttbin + 同 (d,bw) + 同参数重跑，a_eff/b_eff/chan_ll_table.npy 预期字节级复现。**

依据（export_joint_sequence_sidecar.py 全链通读）：

1. 提取路径无随机源：ttbin 读取 → `np.sort` 分通道 → `_pair_timetags_with_delay_window`
   （nearest/greedy/two_pointer/peak_gated 全部为确定性排序扫描）→ `floor_divide`/`mod` 分箱 →
   按 `block_index*n_take` 定长切片（L1239-1253）。
2. 唯一 RNG 在 `_sample_sequences_from_joint_sparse`（L365-390），仅 `allow_sampling` 回退模式使用，
   且种子固定（1000003+block_index）；本次物化 `sequence_source_mode="strict"`、
   `sequence_is_sampled=0`，未经过该路径。
3. peak 对齐统计（直方图估计 peak_center_ps）为数据决定性函数。
4. `.npy` 保存对同 dtype/shape/values 字节确定。

**须钉死的自由度**（重跑时显式固定，写入自检清单）：
- `pairing_mode=nearest`、`processing_rule_version=pairing_v2`、`occupancy_filter=0`、
  `max_pairs=0`（高维不封顶）、delay/offset/frame_start 不设 override；
- 环境变量 `HDQKD_NEAREST_FRAME_THRESHOLD_PS`（默认 40000）与 `HDQKD_ALIGN_DEBUG=0` 保持默认；
- JSON meta 含 `created_at` 时间戳 ⇒ **字节比对仅限 .npy 数组，不含任何 json**。

**自检锚点成立**：干净重建应满足 G1/G2（下文），任何不符即停。

### P4 重建范围

- 受影响格集精确清单：实现阶段用现有 sidecar 的 `joint_fingerprint.sha256` /
  `source_fingerprints.metrics_file.sha256` 跨档对账即可枚举（零重算成本），
  与事件记录（10∩16=56、6∩16=56、6∩10=40、6dB 并集≈61）交叉核对。
- **建议范围（推荐案 A）**：10dB、6dB 各全网格 121 格重物化到新命名空间；
  16dB 待用户决策（选项见 §7-Q1）；20dB 不动。
  理由：无法先验证明未共享格未被陈旧池污染过，全量重建消除部分溯源混合风险，
  且提取成本远低于 Polar 解码成本。
- 备选范围（最小案 B）：仅受影响格（10dB≥56、6dB≈61）。省时但保留"档内新旧混源"。
- 重跑范围：10dB、6dB 全链 stage0→stage1→stage2（frames300 配置不变，参数不动）。

## 2. 命名空间布局（新）

```
results/real_sequences_ns/<src_tag>/d{d}_bw{bw}/blk{b}/
    a_eff.npy, b_eff.npy, materialize_meta.json
```

- `<src_tag> ∈ {loss20dB_t15, loss16dB, loss10dB, loss6dB}`，
  取自 ttbin 记录目录名（`Type2_5s_<tag>` 规范映射），禁止缺省回退到无标签池。
- 新增 `results/real_sequences_ns/MANIFEST.csv`：
  `src_tag,d,bw,blk,ttbin_path,ttbin_sha256,a_eff_sha256,b_eff_sha256,params_tag`。
- 池 key = (src_tag, d, bw, blk)。旧的无标签池路径不再写入。

## 3. 最小代码改动（冻结基线触碰面）

- `export_joint_sequence_sidecar.py`：
  `materialize_real_sequences_for_point(...)` 及其调用点增加可选参数
  `pool_root: str | None = None`；L1483 改为
  `base = Path(pool_root) if pool_root else REPO_ROOT/"results"/"real_sequences"`，
  其余不变。**默认行为逐字节兼容旧调用**。
- `experiments/run_e2e_pipeline.py`：新增 `--real-seq-pool-root` 旗标透传。
- 新增 `tools/materialize_loss_namespaced_candidates.py`（驱动：按档循环设 override+pool_root+out_root）
  与 `tools/verify_candidate_namespace_gates.py`（自检门 G0–G4）。
- 不改 Polar 解码、不改安全分析、不改既有 CLI 默认值。

## 4. 自检门（全部必须 PASS 才进入重跑）

| 门 | 内容 | 失败处置 |
|---|---|---|
| G0 预检 | 四档 ttbin 存在且 >0 字节；记录 sha256 入 MANIFEST；归档 override 点指纹抽验（对账 sidecar `source_fingerprints`，不一致仅记录不阻断——归档已被后续运行覆盖属已知） | 中止，报用户 |
| G1 确定性锚点 | 每档抽 ≥3 格双跑物化，a_eff/b_eff/chan_ll_table 逐字节相同 | 中止：工具链非确定，禁止继续 |
| G2 跨档字节唯一性 | 对全部重建格：任意两档之间 a_eff/b_eff sha256 无一相同 | 中止：命名空间修复无效 |
| G3 物理合理性 | **（2026-08-25 三次修订，终版）** 硬条件仅两项：① 可比格跨档 ser **零精确相等**（哈希级一致=污染签名；实测新数据 0/574，旧数据 152 例——判据区分度实证）；② 档均值 ser 严格有序 6>10>16>20（实测 0.2408>0.2255>0.2076>0.1725）。**取消逐格倒置门控**：独立测量无逐格单调的物理必然，任何百分比阈值均属武断（2% 阈值下最大倒置 2.23% 仅差 0.23pp，无自然聚类）；残留异常检测由 ①（字节级）、G2（跨档唯一性）、G4（溯源）承担。逐格倒置全部记入诊断清单（含相对差），其中 ≥2% 格附 n_pairs 等统计背景说明（非门控） | ①或②破坏 ⇒ 门 FAIL 中止；verdict=FAIL 格入 isolation 清单（历史网格属性）；倒置诊断清单随证据归档 |
| G4 溯源完整性 | 每个 sidecar 记录 source_ttbin 路径+sha256、params、processing_rule_version、src_tag | 补齐后才可进入 stage0 |

## 5. 输出落盘（增量命名，不覆盖）

- 新候选目录：`results/authoritative_nsfix/e2e_<tier>_fullgrid_pairing_v2_candidate_lossfix_v1/`
  （最终名待用户确认 §7-Q4）。
- 重跑产物：`results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300_lossfix_v1/`
  （结构沿用 267 文件/档约定；旧 `four_loss_parts_frames300` 整体只读留证）。
- 事件证据、launch 记录、旧日志一律不动。

## 6. 失败处置 / 备选策略（应急条款）

P2 判定四档原始数据全部可得，以下仅在执行期意外触发时生效：

- 若某档原始 ttbin 在执行时发现损坏/缺失：该档降级为**仅档内结论**
  （不参与任何跨损失对比，master 表标注 `raw-data-missing`），其余档照常；
  同时向用户请求归档原始数据后再补建。
- 若 G1 失败（不可复现）：冻结现场，报告差异格与首个分歧字节偏移，交用户决策，
  不得以"调参使其一致"方式掩盖。
- 若归档 override 点指纹全部失配且用户要求强溯源：以原始 ttbin 直提为准
  （本设计主路线即直提，归档仅作旁证），在 MANIFEST 标注 `archive_fingerprint_mismatch`。

## 7. 待用户拍板问题

- **Q1**：16dB 共享 56 格是否复验？（选项：a. 仅复验 56 格序列并重跑受影响点；
  b. 接受"16dB 档内可用、禁跨损失"结论，不重建 16dB）
- **Q2**：重建范围取推荐案 A（10/6dB 全网格 121 格）还是最小案 B（仅受影响格）？
- **Q3**：残余共享池 `results/real_sequences/d1024_bw{150,180,200}/` 重建完成后处置方式
  （隔离改名 / 删除 / 原样保留）？涉及 results/ 保护政策，须明确授权。
- **Q4**：新输出目录命名是否采纳 §5 的 `*_lossfix_v1` 增量命名？

## 8. 测试分层（对齐 AGENTS §10.1）

- T0：新脚本 import/compile；pool_root 参数默认路径等价的单元断言（tmp 根内跑一个假 point）。
- T1：G1 双跑一致性、G2 唯一性校验逻辑的 tamper 测试（人为注入重复字节应 FAIL）。
- T2：试点档（先 6dB 小样 ≤6 格）端到端物化+门校验；通过后再全量。
- T3：全量物化 + 重跑后的跨档对比回归（对照 v3 reconciled 参考趋势，不作逐位要求）。
