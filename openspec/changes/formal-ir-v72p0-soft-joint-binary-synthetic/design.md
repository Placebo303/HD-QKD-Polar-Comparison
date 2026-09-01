# OpenSpec Design: formal-ir-v72p0-soft-joint-binary-synthetic

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Cycle**: `V72P0-SYN` predecessor `V71-SJK` + `V70-BSJ`
**Implementation**: `5591e16bf35b03c3df30a003bee12011a796d73e` (EXTERNAL_BINDING) **Evidence**: `64ca2f1e653f2386d870feff4d83f5bcc99db1e9`
**Data SHA**: `84d62779` `synthetic_v72p0`

## 1. 科学问题
冻结 `Q1024 N1024 Nbit10240 M9036 f1.3` 下验证 `去self local factor ↔ 增量 syndrome ↔ exact tag` synthetic correctness，P0A tiny k2/3 6/9 + P0B sparse IRA 5-state。

## 2. 冻结语义

| 项 | 值 |
|---|---|
| Q/N/Nbit/M | 1024 / 1024 / 10240 / 9036 |
| f | 1.3 NOT_MEASURED used_2m false |
| tag | 64b exact SHA256 LE |
| col | sym*10+bit |
| LF | 去self Σ_{j≠i} |
| P0A | k2/3 n6/9 total 6/9 64/512 8trials tree-only syndrome0/1 1e-9 |
| P0B | sparse CSR IRA 9036x10240 dual-diagonal rank9036 |
| state | 5-state ADAPTER_PLAN_READY需3passes |

禁：decode_ / 改冻结量 / MET / 读2M / 字符串READY / 启V72 / 改src。

## 3. 数据角色 SYNTHETIC_ONLY

| 集合 | 规模 | 说明 |
|---|---|---|
| P0A k2 n6 | 64 exhaustive 8trials | tree, c3 observed_zero&&observed_one, c5 1e-9 |
| P0A k3 n9 | 512 exhaustive 8trials | 同上 |
| P0B | 9036x10240 sparse CSR | nnz~49620 dual-diagonal pivot4 |
| 2M real | 密封不读 | used_2m false |

注册表 `v72p0_data_registry_synthetic.json` `schema v72p0_synthetic_v1` `head 5591e16b`

## 4. 输入合同
`Q1024 N1024 Nbit10240 M9036 col sym*10+bit bit_i(s) 去self tag64b f1.3 NOT_MEASURED` 落 manifest。

## 5. 估计器

### 5.2 去self LF (枚举1024, log-domain)
```
log_post_excl_i[a]=log_prior[a]+Σ_{j≠i} bits_j·llr_j − logZ_excl
llr_out_i=logsumexp_{1}−logsumexp_{0}
brute: Σ_{j≠i} 逐项枚举 max|Δ|<1e-12
```
`T_LF01 completeness / T_LF02 normalization 1e-12 / T_LF03 marginal 1e-12 / T_LF04 delta 1e-9 / T_LF05 self_exclusion 1e-12 / T_LF06 stability K1e6 isfinite / T_LF07 determinism==0 / T_LF08 brute 1e-12`

### 5.4 P0A tiny
```
configs (2,6)→64 (3,9)→512 各8trials exhaustive tree
observed_zero = any(s==0) ; observed_one = any(s!=0)
c3 = observed_zero && observed_one (fail-closed, 负向测试)
c5 BP-marg vs brute log-weights max|Δ|<1e-9
c6 tree-only, c7 total≤9 exhaustive, wall≤30s
P0A_PASS = all 7 true ∀trials ∀m ∧ c3_obs ∧ worst<1e-9
```

### 5.5 P0B sparse IRA
```
H_mother 9036x10240 n_info1204 H_p dual-diagonal det1⇒rank9036
C1 rank9036 C2 row_min>0 C3 dup0 C4 prefix_nested C5 incremental C6 tag64 exact
pivot 160/168/176/9036, Rs r0=160 Δ8→9036
```

## 6. 分流 5-state
```
if !T_LF01/02 → EVIDENCE_INCOMPLETE
elif !T_LF03-08 → KERNEL_FAIL
elif !P0A (c3_obs或1e-9或wall) → TINY_FAIL
elif !P0B (C1-C6或pivot) → MATRIX_FAIL
elif KERNEL∧P0A∧P0B∧wall≤30 → ADAPTER_PLAN_READY (需3 passes)
overall ADAPTER_PLAN_READY / NOT_READY
```

## 7. 脚本与报告
- `scripts/v72p0_soft_joint_binary_synthetic.py` SYNTHETIC_ONLY `rg decode_ 0 hits` 产 `results/table/manifest/SYN_REPORT`
- `scripts/v72p0_backend_audit.py` read-only `IntEnum` `rg "READY" 0 hits` 产 `audit_report/BACKEND_REPORT`
- `V72P0_SYN_REPORT.md` `V72P0_BACKEND_AUDIT_REPORT.md` 与 json 一致

## 8. 守卫 R72-01~09
`01 冻结+2M禁 / 02 去self8test / 03 Q1-Q6 enum / 04 P0A k2/3 c3观测 / 05 P0B sparse / 06 5state wall / 07 T0-T3 / 08 四件双报告 / 09 SYNTHETIC_ONLY不创run_01不启V72`

## 9. 衔接
V72P0为P0壁垒，`ADAPTER_PLAN_READY`后可进V72 real mother设计，不在本变更启V72。 provenance EXTERNAL_BINDING 5591e16b/64ca2f1e。
