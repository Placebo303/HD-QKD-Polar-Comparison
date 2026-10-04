# OpenSpec Spec: formal-ir-v72p0-soft-joint-binary-synthetic

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Change**: `formal-ir-v72p0-soft-joint-binary-synthetic` (`V72P0-SYN`) `formal-ir-mainline` **Implementation** `5591e16bf35b03c3df30a003bee12011a796d73e` (EXTERNAL_BINDING) **Evidence** `64ca2f1e653f2386d870feff4d83f5bcc99db1e9` **Data** `84d62779 synthetic_v72p0`
**Predecessor**: `V71-SJK` + `V70-BSJ`

## 1. 变更类型与生命周期
- **Type**: `SYNTHETIC_CHAIN_CORRECTNESS_P0` `k2/3 n6/9 total6/9 64/512 8trials tree-only syndrome0/1 1e-9 sparse CSR IRA 5-state`
- **Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` 止于4工件+合成审计，不创run_01不启V72
- **Branch**: `formal-ir-mainline` **EXTERNAL_BINDING** `5591e16b / 64ca2f1e`
- **Data**: `84d62779 synthetic_v72p0` 不读2M
- **f**: `1.3 NOT_MEASURED` 仅参照
- **V72**: NOT_STARTED

## 2. 冻结方法
- `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false tag64b exact col sym*10+bit`
- `LF 去self Σ_{j≠i} T_LF01-08 1e-12/1e-9`
- `P0A k2/3 n6/9 64/512 8trials tree c3 observed_zero&&observed_one c5 1e-9 wall≤30s`
- `P0B sparse CSR IRA 9036x10240 dual-diagonal rank9036 zero0 dup0 pivot 160/168/176/9036 Rs r0 160 Δ8`
- `5-state ADAPTER_PLAN_READY需3passes`
- `T0-T3` 已验

### 2.2 禁止
禁改冻结量、新增disclosure、MET/2M/V72、字符串READY、改src、创建run_01。

## 3. 数据角色

| 集合 | 规模 | 说明 |
|---|---|---|
| P0A k2 n6 | 64 exh 8trials | observed_zero&&observed_one c3 |
| P0A k3 n9 | 512 exh 8trials | 1e-9 tree |
| P0B | 9036x10240 sparse | dual-diagonal |
| 2M | 密封 | used_2m false |

注册表 `v72p0_data_registry_synthetic.json` `head 5591e16b`

### 3.2 就绪门
`Q1024 N1024 M9036 f1.3 NOT_MEASURED used_2m false successor_v72_not_started` 且 `P0A 64/512 8trials` 且 `P0B 9036x10240 pivot4` 否则 EVIDENCE_INCOMPLETE

## 4. 输入合同
`Q1024 N1024 Nbit10240 M9036 col sym*10+bit bit_i去self tag64b f NOT_MEASURED`

## 5. Phase C/D

### 5.2 去self LF
`log_post_excl_i = log_prior+Σ_{j≠i} − logZ` `T_LF01-08` `1e-12/1e-9`

### 5.3 T_LF01-08
`01 completeness 02 normalization 1e-12 03 marginal 1e-12 04 delta 1e-9 05 self_exclusion 1e-12 06 stability K1e6 isfinite 07 determinism==0 08 brute 1e-12`

### 5.4 Q1-Q6 enum
`IntEnum PASS=0 FAIL=1 NOT_APPLICABLE=2` `READY=Q1-3 PASS∧Q4 PASS∧Q6 PASS` `ADAPTER=Q1-3 PASS` `NOT_COMPATIBLE=Q1/Q2 FAIL∨!T_LF01/02` `rg "READY" 0 hits`

### 5.5 P0A
`for (2,6)64 (3,9)512 8trials: c3=observed_zero&&observed_one 负向测试 c5 max|Δ|<1e-9 tree wall≤30s P0A_PASS=all7∀trials`

### 5.6 P0B
`H 9036x10240 sparse CSR dual-diagonal C1 rank C2 row C3 dup C4 prefix C5 inc C6 tag pivots 4点 P0B_PASS=C1-6∧piv`

## 6. 分流 5-state
```
if !T_LF01/02 → EVIDENCE_INCOMPLETE
elif !T_LF03-08 → KERNEL_FAIL
elif !P0A → TINY_FAIL
elif !P0B → MATRIX_FAIL
elif KERNEL∧P0A∧P0B∧wall≤30 → ADAPTER_PLAN_READY (3passes)
overall ADAPTER_PLAN_READY / NOT_READY counts 5
```

## 7. 报告与表
`v72p0_table.csv/.json` 行含 `synthetic_case/Q/N/M/T_LF01-08/KERNEL/P0A c3_obs worst/P0B C1-4 nnz/wall/class/overall` 与 json 行对等
`V72P0_SYN_REPORT.md` (c3_obs, 1e-9, sparse) `V72P0_BACKEND_AUDIT_REPORT.md` (Q1-Q6 enum) 一致

## 8. 守卫 R72-01~09
`01 冻结 02 去self8test 03 enum 04 P0A c3观测 05 P0B sparse 06 5state wall 07 T0-T3 08 四件双报告 09 SYNTHETIC_ONLY不创run_01`

## 9. 脚本与证据
`scripts/v72p0_soft_joint_binary_synthetic.py` `T_LF→P0A c3_obs→P0B sparse` `rg decode_ 0` `py_compile PASS`
`scripts/v72p0_backend_audit.py` `Q1-Q6 enum` `rg "READY" 0`
证据 `registry+results+table+manifest+双报告+test` `head 5591e16b` `EXTERNAL_BINDING` `no_run_01`

## 10. 验收
`py_compile PASS` `rg decode_ 0` `rg "READY" 0` `git diff src==0` `used_2m false` `T_LF01-08 1e-12` `P0A c3 observed_zero&&observed_one 负向测试 worst<1e-9 64/512 wall≤30` `P0B rank9036 zero0 dup0 pivot4` `5-state 3passes` `T0-T3 true` `V72_not_started` `TBD 0` `报告与json一致`
