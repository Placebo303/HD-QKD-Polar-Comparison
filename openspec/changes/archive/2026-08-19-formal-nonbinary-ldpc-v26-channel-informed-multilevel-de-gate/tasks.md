# Tasks: formal-nonbinary-ldpc-v26-channel-informed-multilevel-de-gate

Status: **RUN_COMPLETE — 终态 `pass_target_f13`（2026-08-19）。A02（F03, GF32+GF32）在
f=1.3 下全部 layer × source × confirm-seed 收敛（final mean entropy 0.00000
bits/symbol）。A01（F01, GF512+GF2）f=1.3 失败（GF2 residual 层无法在 degree-2 系综
下收敛），但 f=1.6 通过。**

## V26R closeout（2026-08-19，本地提交并归档，不 push）
- [x] P1-1 修正效率定义（proposal/design/spec/report/code）：`f_i=leak_i/H_i`、
      `leak_i=(1-R_i)log2(q_i)`、`R_i=1-f_i·H_i/log2(q_i)`。
- [x] P1-2 独立只读 verifier `verify_run`：重算 72 screen + 60 confirmation +
      A02@f=1.3 30/30 + rate/rho/seed/熵轨迹/终态；run_01/run_02 均 0 mismatch、
      ok=true；持久化 `readonly_verify.json`（canonical run_02）。
- [x] P1-3 修正 M1 弱参考：`adapter_input_entropy_matches_iter0` 真实进入 MC-DE
      首轮（`record_channel_entropy`，err_replay=0）；`gf2_bsc_reference` 明确判定
      （noiseless 收敛 / 可行性率收敛 / 容量附近判负）。
- [x] P2-1 24h 资源门实现（`RESOURCE_LIMIT_SECONDS`，`_run_gated_stage` →
      `resource_blocked`；V26 未触发）。
- [x] P2-2 source↔delay 显式元数据（`SOURCE_METADATA` → adapter / M0 detail /
      `RUN_MANIFEST.json`）。
- [x] P2-3 run_01=deterministic_repeat、run_02=canonical（`RUN_MANIFEST` + README）；
      run_01 `readonly_verify.json` 已写；更新状态文档；本地 commit；归档 V26。

## P0 — frozen inputs & V25 addendum
- [x] 写 V25 closeout addendum（C03 pooled == C04；F01/F03 为预选探索点；verifier 边界）。
- [x] 修正 V25 tasks.md P001/P002/P102 状态与顶部 ACCEPT 一致性。
- [x] 冻结 F01/F03、natural labeling、MSB→LSB 顺序；三个 source 独立 priors；
      不把 source 平均成主信道；source/delay 作为已知公共条件；不读 `.ttbin`；
      不改变 V25 holdout。

## M0 — layer-channel adapter 语义门
- [x] 实现逐样本层条件 posterior `P(U_i|B,source,delay,U_<i)`（从 train `N_ab`/C04）。
- [x] 验证每个 posterior 非负、归一化；GF512/GF32/GF2 域名正确。
- [x] 验证 adapter entropy 与 V25 `H_i` 在 `1e-3` bits/symbol 内一致（实测 maxerr≈5e-9）。
- [x] ±1 正负方向分别保留；1M 与 1p5M/2M posterior population 不静默合并。
- [x] natural factorization 可逆；第 2 层条件真正包含已知第 1 层。

## M1 — NB-LDPC MC-DE 内核
- [x] 任意 posterior population 注入 + GF(2)/GF(32)/GF(512)。
- [x] 随机非零 edge coefficient（GF 乘法 permutation）+ true-symbol centering。
- [x] entropy 用 bits/symbol（`entropy_base_q * log2(q)`），不同 q 可比。
- [x] 机制参考测试全过：GF4/GF8 brute-force check-node（maxerr≈1e-17）；all-one 退化
      （GF4/GF8 对 brute force，GF32/GF512 对 V14 kernel）；adapter 输入熵==iter0；
      固定 seed 重放一致；GF2 BSC 与 V14 QSC 收敛一致 + noiseless 退化。
- [x] 复用冻结 `nonbinary_field.py`，不重写域运算。

## M2 — 固定系综 screen（不做搜索）
- [x] 只使用 `lambda={2:1.0}` + harmonic-exact concentrated checks。
- [x] screen：2 arch × 2 layer × 3 source × 3 f × 2 seeds = 72 DE calls。
- [x] 参数：n_samples=400 / max_iter=100 / seeds=[26001,26002] / tol=0.01 bits / streak=20。
- [x] screen 结果：A02 全通过 f∈{1.3,1.6,2.0}；A01 L1(GF512) 全通过，A01 L2(GF2) 仅
      f=1.6/2.0 通过（f=1.3 不收敛）。

## M3 — 确认门
- [x] 对每个架构最低通过 f 做确认：A02@f=1.3、A01@f=1.6（因 A02 通过时 A01 的边界
      一并确认）。n_samples=2000 / max_iter=200 / seeds=[26101..26105]。
- [x] A02@f=1.3：30/30（2 layer × 3 source × 5 seed）收敛，final mean entropy 0.00000。
- [x] A01@f=1.6：30/30 收敛。
- [x] 每层单独留证（confirmation_results.json）。

## M4 — 终态
- [x] **pass_target_f13**：A02 在 f=1.3 下所有 layer/source/confirm-seeds 全部收敛。
- [x] 输出每 architecture/layer/source/seed 的 entropy trace、rate、f 与终态
      （screen_results.json / confirmation_results.json / calls_summary.json / gate.json）。

## 结果解读（不越界）
- `pass_target_f13` 仅允许提出 A02（GF32+GF32 / F03）的有限码/构造 change；仍无
  FER/qualification/promotion。
- A01 的 f=1.3 失败点集中在 GF2 residual（L2），L1(GF512) 本身在 f=1.3 收敛；固定
  degree-2 系综对低码率 binary residual 距离目标有差距（非路线失败；下一步可做
  bounded degree optimization 或在 L2 上改构）。
- V26 全程未做 degree 随机搜索、有限码、FER、MET、fresh qual、raw `.ttbin`、
  public residual、Alice-oracle、holdout 调参、push。

## Stop rules
- 无阻塞；M0/M1/M2/M3 全过，终态 `pass_target_f13`。
