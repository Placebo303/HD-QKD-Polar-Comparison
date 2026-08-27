# Phase 3 门校验终版报告（G3 终版语义）— fix-candidate-loss-namespace（E2-final）

**状态：G2 / G3 / G4 全部 PASS（回填前后两次复跑均 PASS）⇒ 满足进入 F5/F6（Phase 4 启动）的前提。**
复跑时间：2026-08-26；门脚本：`tools/verify_candidate_namespace_gates.py`（G3 终版：仅两项硬门，逐格倒置全部入诊断清单）。
运行根：`workspace/fix-candidate-loss-namespace/p4_20260826_013824/gates_final/`。
sidecar 根：新 6/10/16 = `results/authoritative_nsfix/e2e_*_fullgrid_pairing_v2_candidate_lossfix_v1/sidecars`；20dB 参照 = `results/authoritative/e2e_20dB_fullgrid_pairing_v2_candidate_t15/sidecars`（只读）。

## 1. G3 终版语义落地（F1）

- 硬门仅两项：① 可比格跨档 ser 零哈希级精确相等（污染签名）；② 档均值 ser 严格有序 6>10>16>20。
- 逐格倒置：全部记入 diagnostic 清单（含对称相对差），不设阈值、不分级、不门控；
  相对差 ≥2% 的格额外输出统计背景段（各档 n_pairs_actual、小样本 σ=√(ser(1−ser)/n_pairs)、
  coincidence_rate_hz（取自候选目录 `_tmp_grid_table.csv`）、d512–d2048 高维近简并带标注），非门控。
- verdict≠PASS 格照旧入 isolation 清单（网格固有属性，非门控）。
- self-test 同步六场景 S0–S5（良序 PASS / 精确相等 FAIL / 均值序颠倒 FAIL /
  <2% 倒置 PASS+诊断 / ≥2% 倒置 PASS+诊断+统计背景 / 单点 verdict=FAIL PASS+isolation）：PASS。
- pytest（合成 ttbin 最小回路 4 用例）：**4 passed**（`-p no:cacheprovider --basetemp=<task root>`）。

## 2. 回填前复跑（既有 Phase 3 数据：16dB lossfix 仅 83 个重建格）

| 门 | 结果 | 判定 |
|---|---|---|
| G2 | 新三档互检+旧20参照共 **1224** 数组比较，碰撞 **0** | PASS |
| G3 | 可比格 **83**；① 精确相等 **0**；② 均值序 6dB=0.240816 > 10dB=0.225529 > 16dB=0.207552 > 20dB=0.172464 | PASS |
| G3 诊断 | 倒置 **13** 条全列清单；≥2% 共 2 格（d1024_bw150、d2048_bw150，rel_diff=2.2303%，[6dB>10dB]），已附统计背景 | 非门控 |
| G4 | **446** sidecar 溯源字段全过 | PASS |

≥2% 统计背景摘录（d1024_bw150）：n_pairs_actual 6dB=686206 / 10dB=284095 / 16dB=74285 / 20dB=30104，
小样本 σ 分别 5.1e-04 / 8.0e-04 / 1.55e-03 / 1.51e-03 —— 低符合档样本量小、σ 大，
叠加 d1024∈高维近简并带，与 2.23% 倒置量级相容；两格六数组 sha256 全互异（Phase 3 已证），无污染。

## 3. 16dB 候选补全（F4）

- 差集核对：旧 authoritative 16dB 121 格 − lossfix 已建 83 格 = **38** 格，与预期 121−83=38 一致；
  38 格 ∩ affected_cells(16dB) = **0**（口径自洽）。
- 38 格 sidecar 目录树逐字节复制（342 文件），每文件 sha256 与源一致（证明见
  `results/authoritative_nsfix/e2e_16dB_fullgrid_pairing_v2_candidate_lossfix_v1/backfill_from_old_authoritative_MANIFEST.csv`，
  source=old_authoritative_verbatim）。源只读未动。

## 4. 回填后复跑（最终候选状态，全档 121 格）

| 门 | 结果 | 判定 |
|---|---|---|
| G2 | 六个档对全比较 **1452** 数组，碰撞 **0**（回填的 38 个旧 16dB 格与新 6/10dB 及旧 20dB 无一相同——与其"未受影响"口径一致） | PASS |
| G3 | 可比格 **121**；① 精确相等 **0**；② 均值序 6dB=0.24727 > 10dB=0.233595 > 16dB=0.198166 > 20dB=0.17006 | PASS |
| G3 诊断 | 倒置 **25** 条全列清单；≥2% 共 4 格附统计背景（明细 `gates_final/g3_detail_post_backfill.csv`） | 非门控 |
| G4 | **484** sidecar 溯源字段全过（含 38 个 verbatim 格：source_ttbin 匹配 16dB 记录目录等） | PASS |

## 5. 结论

G3 终版判据在新数据上稳定成立且与旧数据（152 起精确相等）保持强区分度；
回填未引入任何跨档字节共享或精确 ser 相等。**全部门 PASS ⇒ 授权进入 F5/F6。**

原始输出：`workspace/fix-candidate-loss-namespace/p4_20260826_013824/gates_final/{g2,g3,g4}.txt`（回填前）、
`{g2,g3,g4}_post_backfill.txt`（回填后）、`g3_detail*.csv`。
