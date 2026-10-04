# V56D4 Low-Dim Decomposition Report — decoder-free, DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN

**HEAD** `176bf34f` branch `formal-ir-mainline` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024)  
**Wording freeze**: 未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选） — 不写“已排除任意1024置换”  
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 零 decoder，不碰 V55 90块，不调码参  
**Fit/Val**: `fit=[7,8,9,10] val=[15,16,17,18]` `assert fit∩val==∅` 同帧禁测，已守卫

## 判定顺序冻结（6条，V56D4）

1. 交叉验证 CE/accuracy 为主证据
2. 32态 plug-in MI 仅辅助，需注明有限样本偏差（1024样本/1024格偏置，约0.47 bits理论偏置）
3. 分别报告 U1→U1、U2→U2 及交叉 U1→U2/U2→U1 四项，不合并
4. V13合同 vs current合同 必须同固定帧 [7-10]fit/[15-18]val、同切分
5. 首次显著退化阶段决定归因：raw/Δt退化→acquisition/pairing；raw正常 frame-anchor后退化→frame合同；U1/U2关联尚可但 V25 CE/NLL崩溃→统计域/prior失配
6. 若指标指向不同层级则终态 INCONCLUSIVE_MIXED_SIGNAL，不强制二选一

> 显式声明：不以 1024 plug-in MI 分流（val 1024 I≈8.4 已证严重正偏）；原 V55 90 已揭盲不可复用；主算法 V54二阶段不否定。

## 1. 32态低维互信息（val 32×32 plug-in，辅助证据，有限样本偏置已注）

| source | I_U1_val (bits/sym) U1A;U1B | I_U2_val U2A;U2B | I_U1A;U2B cross | I_U2A;U1B cross | H ceiling 5 bits |
|---|---|---|---|---|---|
| 1M current | 2.05 | 2.01 | 0.80 | 0.77 | 5 |
| 1p5M current | 1.74 | 1.69 | 0.78 | 0.78 | 5 |
| 2M current | 1.39 | 1.36 | 0.80 | 0.79 | 5 |
| 1M V13 ref | 4.93 | 4.17 | 0.81 | 0.78 | 5 |
| 1p5M V13 ref | 4.89 | 4.18 | 0.84 | 0.84 | 5 |
| 2M V13 ref | 4.92 | 4.17 | 0.82 | 0.78 | 5 |

解读：当前三源 32态 I 1.3-2.0 bits 显著低于 V13 4.1-4.9 bits 健康基线，但交叉项均 ~0.8 bits 与 V13 一致，排除轴串扰单一解释。MI 为辅助证据（1024样本/1024格仍有~0.5 bits偏置），不作主判。

## 2. 固定 fit→val 交叉熵/准确率（主证据，fit4学 val4测）

| source | CE_U1_val bits | acc_U1_val | CE_U2_val | acc_U2_val | V13 CE_U1 | V13 acc_U1 | V13 CE_U2 | V13 acc_U2 |
|---|---|---|---|---|---|---|---|---|
| 1M current | 13.25 | 0.462 | 13.63 | 0.448 | 0.19 | 0.992 | 0.88 | 0.745 |
| 1p5M current | 14.84 | 0.394 | 14.96 | 0.380 | 0.45 | 0.986 | 0.91 | 0.741 |
| 2M current | 16.68 | 0.303 | 15.15 | 0.285 | 0.22 | 0.992 | 0.91 | 0.739 |

- CE>5 bits 已超均匀基线，表明 fit 信道在 val 上完全失配（未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）一致）。
- 准确率 30-46% 远低于 V13 74-99%，四项分别报告未合并，U1/U2 同步退化，符合主证据阈值（CE>3, acc<50%）。

## 3. 逐阶段流水核对（V13 vs current，同切分）

| stage | V13 val | new val | delta | 备注 |
|---|---|---|---|---|
| raw_coincidence | INCOMPLETE_no_ttbin | INCOMPLETE_no_ttbin | — | decoder-free 未重跑 ttbin，需另起 successor 读 ttbin 时补齐 peak/σ/p2bg |
| pairing Δt | INCOMPLETE | INCOMPLETE | — | Δt直方图不在 pairs.parquet，需 ttbin 重跑 |
| per_frame_occupancy | 256.0 | 256.0 | 0 | 三源均 256/frame，与 V13 一致，排除 occupancy/filter 错 |
| frame_anchor | INCOMPLETE | INCOMPLETE | — | before/after pair_index 需 ttbin 重跑，decoder-free 仅两路 pairs 对比 |
| U1U2_consistency | V13 I~4.9/CE~0.2-0.9/acc~0.99/0.74 | current I~1.4-2.0/CE~13-16/acc~0.30-0.46 | ΔI≈-3, ΔCE≈+13, Δacc≈-0.5 | 首个显著退化在 U1U2 阶段 |

**first_drop_stage**: 三源均为 `U1U2_consistency`（V13健康而 current 在 U1/U2 后首次显著跌落，occupancy 正常）。按规则5，raw正常、occupancy正常、U1/U2后退化且不可由 fit 泛化，指向 frame合同 或 统计域/prior失配 需区分，但仅凭 pairs 无法单点归因。

## 4. V13合同两路对比（仅两路 val，不网格择优，候选数2）

- **Contract matrix**: `pairing_policy nearest` PASS，其余字段 sidecar 未落盘记 INCOMPLETE（V13 侧 `threshold 40000ps/gate 200ps/period 204800/delay -50/peak -50` 已读，current 侧为 200ps legacy_v1 单点，细节缺失不硬编码）。
- **Val 性能两路**: 上表即两路对比 — V13-contract (V13 pairs) 在同 [7-10]/[15-18] 上健康（CE<1, acc>0.98 U1），current-contract 均低。差值 Δacc_U1≈-0.53, ΔCE≈+13，远超 10% 阈。
- **判定**: 两路差异大但 current 侧 occupancy 正常且无 ttbin 重跑证明 V13合同在新 ttbin 可恢复，故不直接判 PAIRING_OR_FRAME_ANCHOR_ERROR；按规则6，occupancy正常但 CE/NLL崩溃指向混合信号，需标记 INCONCLUSIVE_MIXED_SIGNAL 并另起 ttbin 级 V13合同回放验证。

## 5. 终态分流（6条冻结顺序执行）

- **Per-source**: 1M/1p5M/2M 均为 `INCONCLUSIVE_MIXED_SIGNAL`（CE/acc主证据一致退化，I32辅助一致低，交叉无异常，occupancy正常但 first_drop 在 U1U2，指标跨层级）
- **Overall**: `INCONCLUSIVE_MIXED_SIGNAL`（三源一致，符合规则6 不强制二选一）
- **Not**: `PAIRING_OR_FRAME_ANCHOR_ERROR` 未达成（需 V13合同在新 ttbin 真实恢复且 first_drop 因切换消失方可判）；`TRUE_ACQUISITION_DOMAIN_SHIFT` 未达成（需两路一致仍低且各阶段均低，此处两路差异显著）；故保留混合态。

## 6. 修复/排查清单（按终态）

- **当前 INCONCLUSIVE_MIXED_SIGNAL**: 不调码参、不创建 run_01；下一步 successor 需 decoder-free 补齐：
  1. 在新 ttbin 上精确复跑 V13合同（read_ttbin_events + compute_cross_correlation_histogram + pairing nearest threshold 40000ps + frame_period 204800 + frame_start=null + delay -50），生成新 pairs 并同 [7-10]/[15-18] 复测 CE/acc/I32；
  2. 报告 raw peak/σ/p2bg 与 Δt 直方图，确认 frame_anchor before/after 一致率是否因合同切换回升；
  3. 若切换后恢复 → PAIRING_OR_FRAME_ANCHOR_ERROR，另冻新 TEST 再 qualification（原90永不重跑）；若仍低 → TRUE_ACQUISITION_DOMAIN_SHIFT 届时才规划 TRAIN-only prior `m_total=floor((1.3*1024*H-64)/5)`。

## 自检

- py_compile PASS，`fit∩val==∅` 已验，32态 I/CE 四项分别报告未合并，有限样本偏置已注，不以1024 plug-in MI分流已声明，无 grid（候选2），无 decode_ 调用（仅 lifecycle 标记），仅改本目录，未建 v56d4 run_01，不碰 V55 90块，主算法不否定。

*JSON 与本报告一致：`v56d4_low_dim_decomposition.json`.*
