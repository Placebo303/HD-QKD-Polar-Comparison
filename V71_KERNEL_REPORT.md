# V71 Kernel Report — 1024-state pure factor kernel 5FUNC D1-D10 1M 1/9/1024 30s/2GiB f1.3 NOT_MEASURED
Lifecycle: PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED, V72_not_started
Head: e8c44e6eeb2343e00f78f15a3d551f8d9793088e Data: 84d62779 (动态绑定 git rev-parse HEAD)

## Frozen body
n1024 q1024 GF32 poly37 H1 16x1024 rank16 10-bit bit_i(s)=(s>>i)&1 extrinsic ext=log_post-log_prior log-domain Lane C 184/190/192 H_inc Delta8 decoder 90/1.0 disabled full-tag canonical leak sum w_i*m_i+64

## 5 functions pure brute 1e-12
- log_prior_from_posterior: pure True
- bit_factor_from_llr: pure True
- soft_joint_factor_kernel: pure True
- extrinsic_from_logs: pure True
- validate_kernel: pure True
brute_maxDelta all_zero 0.0 delta_a0 0.0 a511 0.0 a1023 0.0 <1e-12 PASS

## D1-D10 per session
- 20260123_1M_600k_0dB: D1 True D2 True D3 True D4 True D5 True D6 True D7 True D8 True D9 True D10 True
- 20260107_PPLN_1p5M: D1 True D2 True D3 True D4 True D5 True D6 True D7 True D8 True D9 True D10 True
- 20260123_2M_1p2M_0dB: D1 True D2 True D3 True D4 True D5 True D6 True D7 True D8 True D9 True D10 True

## Benchmark 1M 1/9/1024 block wall/peak
- 20260123_1M_600k_0dB 1 wall 4.0625s peak 0.09MiB per 61989ns
  9 wall 0.4530s peak 0.09MiB per 62208ns
  1024 wall 0.0044s peak 0.09MiB per 69196ns E_PERF_PASS True

## f1.3 freeze f_actual NOT_MEASURED
CE_full_1M 7.150001 required_1M 9519 f_actual NOT_MEASURED

## Per-session classification 6-terminal
- 20260123_1M_600k_0dB V71_KERNEL_READY_FEASIBLE successor v71_ldpc_v5_integration required 9519 D True
- 20260107_PPLN_1p5M V71_KERNEL_READY_FEASIBLE successor v71_ldpc_v5_integration required 10047 D True
- 20260123_2M_1p2M_0dB V71_KERNEL_READY_FEASIBLE successor v71_ldpc_v5_integration required 11169 D True

## Overall 4-state
V71_OVERALL_KERNEL_READY counts {'ready': 3, 'adapter': 0, 'heavy': 0, 'not_compatible': 0, 'evidence': 0, 'model': 0} ready 3 adapter 0 heavy 0 not_compatible 0 evidence 0 model 0

TEST isolation used_test False used_val_in_selection False PASS
1024-state frozen verification PASS, V72_not_started
