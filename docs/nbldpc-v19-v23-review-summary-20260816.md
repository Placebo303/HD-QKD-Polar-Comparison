# NBLDPC V19→V23 科学结论汇总 (2026-08-16)

## 1. 总目标
q=1024、V17 结构化信道、f≤1.3 的信息协调。Polar / binary LDPC 只读基线。

## 2. V19/V20 工程与审查修正
- V19 完成 PEG/FFT-QSPA/OSD/MRB-OSD；V20 增加 bounded-weight ML 与 top-K。
- 审查确认：
  - `31/64` 是 oracle-aided best-of cascade 上界（不可执行）；
  - `40/96` 是 top-4 oracle coverage；
  - standalone bounded4 `30/64` 是未独立验证的 Bob-only 估计；
  - V01 仅为 counting-only。
- V20 已移入 archive 并附 audit addendum。

## 3. V21 Bob-only 验证（停止门）
64 个全新 n=64 帧：
- S0 BP-only：24/64，FER=0.625
- S1 bounded4-only：28/64，FER=0.5625
- S2 BP-first-fallback-bounded4：28/64，FER=0.5625
全部 ≥0.45 → 停止门触发，短块 OSD/top-K 分支冻结为 `scientific_not_ready`。

## 4. V22 结构化 DE
- SC-LDPC（V11）在 QSC p=0.05 可通过，但不在目标 rate；
- 结构化信道 rate=0.70 non-converged；rate=0.9375 原受 check-degree cap 限制；
- V22b 提升 degree cap 后 rate=0.9375 可运行，但 plain/SC 候选仍不收敛。

## 5. V23 Protograph/MET DE
- 扫描 regular protograph（2..8 × 32..128）与简单 irregular，全部 non-converged；
- entropy 下限 ~0.19–0.34，远高于 0.01；
- 结论：现有系综下 q=1024 结构化 f≤1.3 高 rate DE 不可达。

## 6. 与文献对照
- Müller et al. 2024（f≈1.078–1.14）依赖完整 DE 优化 + blind reconciliation；
  我们缺少完整结构化 DE 优化，且只有 oracle 上界，不能声称达到同等操作级 f。
- Pacher 2016 两步法已在 N2b 容量界否定（LSB-public 不降 f）。
- Kasai / Martínez-Mateo & Elkouss 盲协调需要公开验证位，已计入 f 预算限制
  （n64 最多 ~5 bits，n80 最多 ~7 bits）。

## 7. 最终状态
- `diagnostic_only` 全程；无 fresh qualification / promotion。
- 短块 OSD/top-K：scientific_not_ready。
- 结构化 DE 目标 f：not reachable with current ensembles。
- 下一步候选：完整结构化 DE 优化（Müller 风格）或调整目标/信道分解。

## 8. 关键证据根
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/n6_comparison_v6_q1024_v20_final/`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v20_20260816/audit_addendum_20260816.json`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v21_20260816/n64_64f_bob_only_summary.json`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v23_20260816/de_not_reachable_summary.json`
