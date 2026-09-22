# V72P0 SYN REPORT

head 5591e16bf35b03c3df30a003bee12011a796d73e data 84d62779 synthetic_v72p0 Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false V72_not_started

LOCAL_FACTOR_KERNEL_PASS True T_LF01 True T_LF02 True T_LF03 True T_LF04 True T_LF05 True maxDelta 3.1086244689504383e-15 T_LF06 True T_LF07 True T_LF08 True maxDelta 0.0

P0A tiny k=2/3 n=6/9 exhaustive 2^n syndrome 0/1 flip LLR exact posterior 1e-9 marginal tree-only {'2': {'m': 2, 'n': 6, 'total_bits': 6, 'trials': 8, 'exhaustive_total': 64, 'checks_per_trial': [[True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True]], 'worst_marginal_delta': 1.3322676295501878e-15, 'tree_flags': [True, True, True, True, True, True, True, True], 'loopy_descriptive_count': 0, 'per_m_pass': True, 'observed_zero': True, 'observed_one': True, 'c3_observed': True}, '3': {'m': 3, 'n': 9, 'total_bits': 9, 'trials': 8, 'exhaustive_total': 512, 'checks_per_trial': [[True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True], [True, True, True, True, True, True, True]], 'worst_marginal_delta': 2.1094237467877974e-15, 'tree_flags': [True, True, True, True, True, True, True, True], 'loopy_descriptive_count': 0, 'per_m_pass': True, 'observed_zero': True, 'observed_one': True, 'c3_observed': True}} P0A_PASS True wall 0.109s peak 0.0MiB worst_delta 2.11e-15

P0B mother sparse CSR IRA 9036x10240 nnz 49620 row_deg {'row_mean': 5.49136786188579, 'row_min': 4, 'row_max': 6, 'col_mean': 4.845703125, 'col_min': 1, 'col_max': 47} zero_cols 0 dup_rows 0 rank 9036 pivot {160: True, 168: True, 176: True, 9036: True} dual_diagonal H_p dual-diagonal => det=1 => rank=m, verified pivots at 160/168/176/9036 prefix_nested True C1 True C2 True C3 True C4 True C5 True C6 True P0B_PASS True

classification V72P0_ADAPTER_PLAN_READY successor v72_mother_adapter_design overall OVERALL_ADAPTER_PLAN_READY five_state

2M not read, Q1024 frozen, V72_not_started
