# V71 Audit Report — A1-A6 ADAPTER_REQUIRED (A3_backend_model_binding_field_present, no READY)
Lifecycle: PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED, V72_not_started
Head: e8c44e6eeb2343e00f78f15a3d551f8d9793088e Data: 84d62779 (动态绑定 git rev-parse HEAD)

## A1-A6 per session (A3_backend_model_binding_field_present, A4 extrinsic false, A6 10240 false => ADAPTER_REQUIRED)
- 20260123_1M_600k_0dB: ADAPTER_REQUIRED checks {'A1_interface_presence': True, 'A2_policy_manifest_schema': True, 'A3_backend_model_binding_field_present': True, 'A4_extrinsic_interface': False, 'A5_runtime_caps': True, 'A6_disclosure_accounting': False, 'kernel_status': 'READY', 'backend_status': 'ADAPTER_REQUIRED', 'capacity_status': 'FEASIBLE'}
- 20260107_PPLN_1p5M: ADAPTER_REQUIRED checks {'A1_interface_presence': True, 'A2_policy_manifest_schema': True, 'A3_backend_model_binding_field_present': True, 'A4_extrinsic_interface': False, 'A5_runtime_caps': True, 'A6_disclosure_accounting': False, 'kernel_status': 'READY', 'backend_status': 'ADAPTER_REQUIRED', 'capacity_status': 'MARGINAL'}
- 20260123_2M_1p2M_0dB: ADAPTER_REQUIRED checks {'A1_interface_presence': True, 'A2_policy_manifest_schema': True, 'A3_backend_model_binding_field_present': True, 'A4_extrinsic_interface': False, 'A5_runtime_caps': True, 'A6_disclosure_accounting': False, 'kernel_status': 'READY', 'backend_status': 'ADAPTER_REQUIRED', 'capacity_status': 'NO_INFORMATION'}

## Overall 4-state (mechanical V70 thresholds FEASIBLE/MARGINAL/NO_INFORMATION)
V71_OVERALL_KERNEL_ADAPTER_OR_HEAVY ready 0 adapter 3 not_compatible 0

## Notes
A3 self-binding removed, backend_model_binding_field_present only; no READY, must ADAPTER_REQUIRED
f1.3 frozen f_actual NOT_MEASURED, benchmark only 1M 1/9/1024 wall<=30s peak<=2048MiB E only 1024
capacity FEASIBLE/MARGINAL/NO_INFORMATION mechanical reuse V70
V72_not_started
