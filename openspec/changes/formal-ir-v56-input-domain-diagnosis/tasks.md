# OpenSpec Tasks: formal-ir-v56-input-domain-diagnosis

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 根因诊断，不运行 L1/L2 decoder，不改方法，不重跑原 90 块。**
**Execution status**: 本轮仅完成 `proposal/design/tasks` + `diagnosis_v55_domain.py` (decoder-free) + `DIAGNOSIS_REPORT.md` (per-source 统计/NLL/offset/分流结论) 的诊断交付；不创建 `run_01`，不冻新 registry。
**HEAD**: `cf8b098047cf64aa1e0426e2ea2e62b680430bd6` (branch `formal-ir-mainline`, V55 固化后最新) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation` (`3d7c63eefe655c9f25d199af3f7f4ea311ac454b`, `v55_authoritative_registry.json` 90-block 已冻, 0/90 已揭盲)
**Method frozen**: `H1-16/Lane C m2 184/190/192/H_inc1/2 Δ8+8/decoder 90/1.0 poly37/L2-only tag/TRAIN prior` 零改，诊断期间禁止调任一参数

## Phase A — 元数据只读审计（decoder-free，不跑 decoder）

- [ ] **A1** 只读核对 V13 2026-01-21 三源元数据：**读取实际** `build_manifest.json` + `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 及 `ttbin_metrics` 的 `used_params` 实际字段（`delay_used_ps/peak_center/peak_sigma/corr_argmax/frame_start/mapping/pairing` 等），缺失如实报告 `INCOMPLETE`，不硬编码 `-50/+50` 等权威值；仅当文件/字段存在才记 `PASS` 并记录 `_value`
- [ ] **A2** 只读核对 V55 三候选 2026.1.23/2026.1.07 三源元数据：读取实际 `v55_intake_20260828/intake_report.json` + `sidecars/*/sidecar_meta.json` 的实际 `materialize_params/used_params` 字段 + `v55_authoritative_registry.json`，逐项标记 `PASS/INCOMPLETE` 按实际文件内容，缺 `delay_used_ps / peak_center / peak_sigma / corr_argmax / frame_start_ps / mapping / pairing_window` 如实记 `INCONCLUSIVE_METADATA_INCOMPLETE` 前置条件（不自动判 Path A/A2）
- [ ] **A3** 生成元数据对比矩阵（`V13 vs V55` 实际读取表，见 design §2.2），结论写入 `DIAGNOSIS_REPORT.md §2`，明确指出 V55 sidecar 缺失需 `actual raw peak/delay/channel` 证据才可判 `A2`，否则仅 `INCONCLUSIVE`；该矩阵为后续 `A1-only` offset 的先验证据

## Phase B — 逐源统计对比（decoder-free，仅 parquet + V25 counts）

- [ ] **B1** 逐源计算 `A==B 率 / SER`：基于 `pairs.parquet` 的 `alice_symbol/bob_symbol` 列，`rate_eq = mean(a == b)`，per source 全量与 per frame 分布，复现 `V13 ~76% (≈0.76) → V55 27-41%` 的跌落，报告每源 `rate_eq / SER / frame 级 rate_eq 直方图`
- [ ] **B2** 逐源计算 `U1/U2 一致率`：F03 `5+5` split (`u1 = a>>5, u2 = a &31` natural；或 `gray_label` 若需对照)，`U1_eq = mean(u1_a==u1_b)`, `U2_eq = mean(u2_a==u2_b)`，报告 `U1/U2/联合` 三率与 V13 差值（设计预期 `V13 76% → V55 27-41%` 复现）
- [ ] **B3** 逐源计算 `Bob-conditioned NLL`：基于 `nbldpc_v25_20260818/run_04/channel_counts.npz` 的 `P(A|B)=N_ab/colsum` (column-normalized, `1e-15` 平滑)，`NLL = mean(-log2 P(a|b))`，报告 `bits/symbol` 与 `bits/block (×1024)` 双单位，同时报告 `q_mass_on_p_zero` (empirical mass 落于 `N_ab_train==0` 格) 与 `zero_prob_count`，对比 V13 的 `≈0.81-0.83 bits/symbol` 基线，预期 V55 显著升高
- [ ] **B4** 逐源计算 `边缘分布 / 零-罕见 bins / frame 相关率 / modular delta`：
  - 边缘 `P(A), P(B)` 1024-bin 直方图与 `KL` 近似、`top_a/b_frac`、`n_unique`
  - 零/罕见 `N_ab==0` 格数占比、`rare <5` 占比、`nonzero/1M` 稀疏度
  - frame 级 `rate_eq` 分布与 `±1` 邻bin质量、`delta=(a-b) mod 1024` 直方图 `mass_0/mass_±1/other` 与 `direction_asymmetry = frac[+1]-frac[-1]`，对比 `channel_summary.json` 的 `modular_delta_frac_top`
- [ ] **B5** 汇总 `V13 vs V55` 差值表（per source）：`Δrate_eq / ΔU1/ΔU2 / ΔNLL / Δq_mass / Δdelta_mass` 等，写入 `DIAGNOSIS_REPORT.md §3` 与 `diagnosis_v55_domain.json` 的 `per_source_stats`，零 `decode_*` 调用可验证 (`rg "decode_" 0 hits`)

## Phase C — 固定相对 offset 扫描诊断（A1-only，不等价 raw time-delay，仅作证据）

- [ ] **C1** 实现 `A1-only` 扫描：由已有 1024-bin `delta=(a-b) mod 1024` histogram 直接得全 `k` 的 `rate_eq(k)=hist[k mod 1024]`（`b'=(b+k)%1024` 仅 parquet symbol/mapping shift (A1)，与 raw TTBin delay/peak/pairing contract (A2) 分离）；仅对 `k=0` 与主峰 `k*` 算 `NLL(k)` / `delta_hist(k)`，其余 `k` 不算 NLL；报告 `k vs 相关率/NLL` 曲线与峰值 `k* = argmax rate_eq(k)`、`Δrate = rate_eq(k*)-rate_eq(0)`、`ΔNLL = NLL(0)-NLL(k*)`，并注明不等价 raw time-delay 扫描
- [ ] **C2** 判定 offset 证据类型（A1 专用）：
  - 若 `k*≠0` 且 `Δrate>20pp` 且 `NLL(k*)` 回落至 `~0.8-1.0 bits/symbol` 且 `hist[k*]` 峰回 `0` → 记为**A1 单峰系统性偏移**（支持 parquet symbol/mapping 错误假设，与 A2 分离）
  - 若曲线平坦/多峰弥散或峰值仍 `<50%` 或 `NLL` 仍 `>1.5 bits/symbol` → 记为**排除 A1**（需再判 A2/B）
  - 显式标注“A1-only，不等价 raw time-delay，仅诊断、不择优、不用于资格”，写入 `DIAGNOSIS_REPORT.md §4` 与 `diagnosis_v55_domain.json` 的 `offset_scan`
- [ ] **C3** 守卫：扫描以 `V25 P(A|B)` 为参考，不重估 `P(A|B)`；不对 `a` 做偏移；不试 `a/b` 联合二维偏移；不将 `k*` 回注为新 pipeline；注明 A1 与 raw time-delay 不等价

## Phase D — 逐源分流与总体终态（A1/A2/B 拆分，四态互斥）

- [ ] **D1** 综合 `Phase A` 元数据审计 + `Phase B` 逐源统计 + `Phase C` A1-only offset 扫描，给出**逐源三判定**与**总体四态**（`PATH_A_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE` 含 `INCONCLUSIVE_METADATA_INCOMPLETE`，非单一 Path A/B，二选一已废）：
  - **A1 与 A2 分离**：`b'=(b+k)%1024` 仅为 parquet symbol/mapping shift (A1)；raw TTBin delay/peak/pairing contract (A2) 需 actual raw peak/delay/channel 证据；`B` 为排除 `A1/A2` 后物理域迁移。
  - **逐源**：`PATH_A1_PARQUET_SYMBOL_SHIFT` 若 offset 单峰显著 (k*≠0 Δrate>20pp NLL 回落)；`INCONCLUSIVE_METADATA_INCOMPLETE` 若缺 metadata 但无 actual raw 证据（不自动判 Path A/A2）；`PATH_B_DOMAIN_SHIFT` 若排除 A1/A2 后仍 `27-45%` 相关、NLL 仍高；否则 `INCONCLUSIVE`。
  - **总体**：三源逐源判定聚合为 `PATH_A_ALL`（全 A1/A2）/ `PATH_B_ALL`（全 B）/ `MIXED_BY_SOURCE`（源间不一致）/ `INCONCLUSIVE`（含 `INCONCLUSIVE_METADATA_INCOMPLETE`）。
  - 缺 metadata 本身只能 `INCONCLUSIVE_METADATA_INCOMPLETE`，不能自动判 `Path A/A2`，需 actual raw peak/delay/channel 证据；阈启发（`20pp/60%/1.0 bits` 仅描述）写入 `DIAGNOSIS_REPORT.md §5`
- [ ] **D2** 若某源 `PATH_A1`，输出 **A1 修复建议**（sidecar mapping/bin_origin 必填、FileReader 符号化显式绑定、G1'-G3'），见 design §3.1；若需判 `A2`，需先补 actual raw 证据
- [ ] **D3** 若某源 `PATH_B`，输出 **重估清单**（`N_ab → H(A|B) → F03 H(U1|B),H(U2|U1,B) → m_total/f` source-adaptive 重算，见 design §3.2），并声明当前 `m2/leak` 预算缺口；`MIXED_BY_SOURCE` 时按源分别给建议
- [ ] **D4** 无论何种总体终态，均冻结**校准优先原则**：必须先用**独立 calibration frames**（与原 90 零重叠、未揭盲、每源 8-16 frames 小批量）验证基础相关性（健康参考 `A==B>60% NLL<1.0` 仅作描述），通过后再另冻新 blocks 进入 qualification；本诊断不直接冻结新 blocks

## Phase E — 诊断脚本与报告交付（DIAGNOSIS_PLAN_READY）

- [ ] **E1** 实现 `diagnosis_v55_domain.py` (decoder-free, 本变更目录下)：
  - 接口 `python diagnosis_v55_domain.py [--pairs-root ...] [--sidecar-root ...] [--counts ...] [--registry ...] [--out ...]`，默认读取 `v55_intake_20260828/pairs + sidecars` 与 `v13r3fresh_pairs_20260816` 与 `channel_counts.npz`
  - 产出 `diagnosis_v55_domain.json` (含 `head cf8b09... / data SHA 84d62779 / per_source_stats / offset_scan / metadata_matrix / shunt_decision`) + 控制台摘要
  - 守卫：`rg "decode_" 0 hits`, `rg "import.*v55.*decode" 0`, 仅 `numpy/pandas/pyarrow`，零 `construct_*` 调用；`py_compile` PASS
- [ ] **E2** 撰写 `DIAGNOSIS_REPORT.md`：记录每源统计、NLL、offset 扫描结果与分流结论，数据与 `diagnosis_v55_domain.json` 一致，含 `V13 vs V55` 差值表、offset 曲线表、分流判定与修复/重估建议，显式声明不扩大为 FER/阈值/SKR/晋升、不宣称 LDPC 证伪
- [ ] **E3** 自检与交付：`python diagnosis_v55_domain.py --help` 可运行，`rg` 守卫 0 命中，`DIAGNOSIS_REPORT.md` 与 json 数值一致，`proposal/design/tasks` 与报告结论一致，已达 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`
- [ ] **E4** 推送并停留 `DIAGNOSIS_PLAN_READY`，未创建任何 `.../v56_*/run_01` 或新 registry，等待 successor `calibration` / `contract-fix` / `entropy-reestimation` 的独立授权

## 本诊断期间显式禁止

decoder 调用（任何 `decode_*` / `construct_lane_c_prototype` / `sample_uniform_gf32_nonzero` 等）；在原 V55 authoritative 90-block 上重跑任何 corrected pipeline（含 offset-corrected 重译）；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数；宣称 LDPC/NB-LDPC 证伪或 FER/阈值/SKR/晋升结论；创建正式 `.../v56_*/run_01` 或新 registry/新校准 blocks（校准需 successor）；以 offset 扫描择优值回注为新 pipeline；将 `0/90` 记为算法失败；自授 `EXECUTE_AUTH` 或伪造 `DIAGNOSIS_PLAN_READY`。

## 验收（本诊断）

- `proposal.md/design.md/tasks.md` 与 `diagnosis_v55_domain.py` + `DIAGNOSIS_REPORT.md` 5 文件齐全一致，`HEAD cf8b09... + 84d62779` 已绑定，lifecycle `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 明确
- 元数据审计矩阵 `PASS/MISMATCH/INCOMPLETE` 已生成且指出 V55 sidecar 缺 10+ 字段
- 逐源统计 `A==B/U1/U2/NLL/edge/zero/frame/delta` 已复现 `76%→27-41%` 跌落且 NLL 显著升高，零 decoder 调用可验证
- Offset 扫描 `k∈[-8,+8]` 曲线与峰值 `k*` 已报告且标注仅诊断
- 唯一分流判定 `Path A` vs `Path B` 已互斥给出且与证据链闭合，含修复/重估建议与已揭盲保护、校准优先硬约束
- 脚本 `rg` 守卫 0 命中、`py_compile` PASS、`DIAGNOSIS_REPORT.md` 与 json 一致、未创建新 registry/run_01，已推至 `DIAGNOSIS_PLAN_READY`
