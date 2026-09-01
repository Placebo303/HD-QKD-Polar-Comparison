# OpenSpec Spec: formal-ir-v72p1-soft-joint-binary-adapter

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Change**: `formal-ir-v72p1-soft-joint-binary-adapter` (`V72P1-ADP`) `formal-ir-mainline` **Implementation** `TBD (freeze-time git rev-parse HEAD)` **Data** `84d62779 synthetic_v72p1`
**Predecessor**: `V72P0-SYN 5591e16b` + `V71-SJK e038114d` + `V70-BSJ 9bc34be6`

## 1. 变更类型与生命周期
- **Type**: `SYNTHETIC_ADAPTER_MINIMAL` `10步 S1-S10 + 3类型 Config/Result/Adapter + P1A plumbing / P1B tiny 64/512 8trials tree-only 1e-9 c3观测 / P1C full-size 9036×10240 1/3/10 smoke / P1D small loopy n12 k3 描述性 + 边内存复杂度`
- **Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` 止于 4 工件+合成复杂度探针+双报告+小测试，不创 run_01 不启 V72
- **Branch**: `formal-ir-mainline` **EXTERNAL_BINDING until Pre-RESULT** `TBD / synthetic_v72p1`
- **Data**: `84d62779 synthetic_v72p1` `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false used_test false`
- **f**: `1.3 NOT_MEASURED` 仅参照，`leak_r = r·1+64`
- **V72**: `NOT_STARTED`

## 2. 冻结方法
- `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false tag64b exact SHA256 LE col sym*10+bit bit_i(s)=(s>>i)&1`
- `LF 去self Σ_{j≠i} T_LF01-08 1e-12/1e-9 logsumexp`
- `mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036 info 3-4 H_p2 nnz≈49698 zero0 dup0 pivot 160/168/176/9036 Rs r0 160 Δ8`
- `adapter pack / syndrome / tag / prefix / incremental 纯函数`
- `10 步 S1-S10: S1 bits → S2 prior → S3 LF → S4 pack → S5 mother → S6 syndrome → S7 leak → S8 tag → S9 edges/memory → S10 5-state`
- `3 类型: AdapterConfig / AdapterResult / Adapter`
- `P1A plumbing 确定性/前缀/增量/tag / P1B tiny 64/512 8trials c3_obs 1e-9 / P1C 1/3/10 smoke wall<1/5/30s / P1D loopy n12 k3 descriptively`
- `5-state ADAPTER_PLAN_READY 需 KERNEL∧P1A∧P1B∧P1C wall≤30`
- `T0-T3` 已验

### 2.2 禁止
禁改冻结量、新增披露、MET/2M/V72、字符串 `"ADAPTER_PLAN_READY"` 直判（须 `IntEnum`）、改 `src`/V70/V72P0、创建 run_01。

## 3. 数据角色

| 集合 | 规模 | 说明 |
|---|---|---|
| P1A plumbing | 4 probes 1024态 + 9036前缀 | 确定性/前缀/增量/tag wall≤30s |
| P1B k2 n6 | 64 exh ×8 trials | c3 observed_zero&&observed_one c5 1e-9 tree |
| P1B k3 n9 | 512 exh ×8 trials | 同上 |
| P1C smoke | 9036×10240 ×1/3/10 iter | C1-C6 + pivot + wall<1/5/30s |
| P1D loopy | n12 k3 12bits ×8 trials | 单环 descriptively capacity_warning |
| P0B re-validate | 9036×10240 sparse | C1-C6 pivot 复用校验 |
| 2M/TEST | 密封不读 | used_2m false used_test false |

注册表 `v72p1_data_registry_synthetic.json` `schema v72p1_synthetic_v1` `head TBD` `reused_from v72p0_synthetic_v1` `successor_v72_not_started true`

### 3.2 就绪门
`Q1024 N1024 M9036 f1.3 NOT_MEASURED used_2m false used_test false successor_v72_not_started` 且 `P1A 4 probes` 且 `P1B 64/512 8trials` 且 `P1C 1/3/10 smoke` 且 `P1D n12 k3` 且 `mother rank9036 zero0 dup0 pivot4` 否则 `EVIDENCE_INCOMPLETE`

## 4. 输入合同
`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 col sym*10+bit bit_i去self LF T_LF01-08 tag64b exact leak r·1+64 f NOT_MEASURED mother 9036×10240 adapter S1-S10 10步 3类型` 落 `AdapterConfig`。

## 5. Phase C/D/E/F/G

### 5.2 去self LF (S3, 10步之三)
`log_post_excl_i = log_prior + Σ_{j≠i} bits_j·llr_j - logZ` `T_LF01-08` `1e-12/1e-9` `i∈{0,5,9}` 三点探针

### 5.3 T_LF01-08
`01 completeness 02 normalization 1e-12 03 marginal 1e-12 04 delta 1e-9 05 self_exclusion 1e-12 06 stability K1e6 isfinite 07 determinism==0 08 brute 1e-12`

### 5.4 Adapter 3 类型
`AdapterConfig {Q,N,Nbit,M,r0,Δ,max,f,tag,col,seed_mother,used_2m,successor}` `AdapterResult {T_LF,P1A,P1B,P1C,P1D,edges,memory,wall,class,overall}` `Adapter {pack,syndrome,tag,prefix,incremental}` 纯函数无 I/O/随机

### 5.5 S1-S10 10 步
`S1 b[10240]合成 → S2 log_prior[1024] → S3 LF去self → S4 bit_llr[10240] sym*10+bit → S5 H_mother 9036×10240 H_r prefix → S6 s_r=H_r·b mod2 增量 s_{r+8}=s_r∪new8 → S7 leak r·1+64 f NOT_MEASURED → S8 tag SHA256 LE 64 samples → S9 edges/memory nnz≈49698 CSR≈235KB peak<2GiB → S10 5态分流`

### 5.6 P1A plumbing
`pack_determinism==0 ∧ prefix_nested ∀r∈{160,168,176,9036} H_r==H_mother[0:r] ∧ incremental s_{r+8} 异或一致 ∧ tag LE exact 64 samples ∧ wall≤30s ⇒ P1A_PASS`

### 5.7 P1B tiny
`for (k2,n6)64 (k3,n9)512 8trials exhaustive tree forest: c1 isfinite / c2 brute isfinite / c3 observed_zero&&observed_one fail-closed + 负向测试 observed_one==false⇒c3 false / c4 brute exists / c5 max|Δ|<1e-9 tree-only / c6 tree / c7 total≤9 ∧ syndrome_ok ∧ tag_ok ∧ worst<1e-9 ∧ wall≤30s ⇒ P1B_PASS`

### 5.8 P1C smoke + P0B re-validate
`H_mother 9036×10240 sparse CSR IRA dual-diagonal C1 rank9036 C2 row_min>0 C3 dup0 C4 prefix C5 incremental C6 tag pivot 160/168/176/9036 全PASS ∧ 1 iter wall<1s ∧ 3 iter <5s ∧ 10 iter ≤30s ∧ peak≤2048MiB ∧ syndrome增量/tag exact 三档全PASS ⇒ P1C_PASS`

### 5.9 P1D loopy
`n12 k3 total12 8trials 含单环: syndrome_ok ∧ tag_ok ∧ cycle_count==1 ∧ BP_residual 描述性 ∧ wall ⇒ P1D_descriptive, capacity_warning=(cycle>0||residual>1e-9) 正交不过硬门禁`

### 5.10 边内存复杂度
`nnz≈49698±1% row_min>0 row_max≤6 zero0 dup0 CSR≈235KB LLR≈80KB peak≤2048MiB per_invocation_ns 已落盘 O(nnz+Q·1024) ponytail ceiling 已标`

## 6. 分流 5-state + overall 2-state

```
if !synthetic_bits_ok or !H_mother_exists → EVIDENCE_INCOMPLETE
elif !T_LF01_02_PASS → KERNEL_FAIL
elif !P1A_PASS or !P1B_PASS → PLUMBING_TINY_FAIL
elif !P0B_revalidate_PASS or !P1C_PASS → MATRIX_SMOKE_FAIL
elif T_LF01-08∨P1A∧P1B∧P1C∧wall≤30∧peak≤2048 → ADAPTER_PLAN_READY (需 4 hard PASS，P1D 仅描述)
else → MATRIX_SMOKE_FAIL
overall = ADAPTER_PLAN_READY iff ∀cases READY else NOT_READY
# P1D capacity_warning 正交不过硬门禁
# 5 counts {EVIDENCE/KERNEL/PLUMBING_TINY/MATRIX_SMOKE/ADAPTER_PLAN_READY: n}
```

## 7. 报告与表
`v72p1_table.csv/.json` 行含 `{case/Q/N/M/r/T_LF/P1A/P1B c3_obs worst/P1C iter1/3/10 wall/peak/edges/CSR/syndrome_inc/tag/P1D cycle/capacity/wall/class/overall}` 与 json 行对等
`V72P1_SYN_REPORT.md` (T_LF/P1A plumbing/P1B 64/512 worst/P1C 1/3/10 smoke edges/CSR/wall/P1D loopy capacity_warning + overall 2态 + S1-S10 3类型) 与 json 一致
`V72P1_BACKEND_AUDIT_REPORT.md` (3类型/10步/5态 IntEnum) 与 json 一致

## 8. 守卫 R72P1-01~10
`01 冻结+2M禁+10步3类型+V72禁 / 02 去self8test 1e-12 / 03 P1A plumbing确定性前缀增量tag / 04 P1B tiny 64/512 c3观测负向1e-9 / 05 P1C 9036×10240 1/3/10 smoke C1-C6 pivot wall<1/5/30s / 06 P1D loopy描述性capacity_warning / 07 边内存复杂度 nnz≈49698 CSR≈235KB O / 08 5态2态wall / 09 四件双报告 / 10 SYNTHETIC_ONLY不创run_01不改V70/V72P0不启V72`

## 9. 脚本与证据
`scripts/v72p1_soft_joint_binary_adapter.py` `S1-S10 → T_LF→P1A→P1B 64/512 c3观测→P1C 9036×10240 1/3/10 smoke→P1D loopy→edges/memory→5态` `rg decode_ 0` `py_compile PASS` 产 `results/table/manifest/SYN_REPORT`
`scripts/v72p1_backend_audit.py` `AdapterConfig/Result/Adapter 3类型 + S1-S10 + 5态 IntEnum` `rg "\"ADAPTER_PLAN_READY\"" 0` `py_compile PASS` 产 `audit_report/BACKEND_REPORT`
证据 `registry+results+table+manifest+双报告+test` `head TBD` `EXTERNAL_BINDING` `no_run_01` `V72_not_started`

## 10. 验收
`py_compile PASS` `rg decode_ 0` `rg "\"ADAPTER_PLAN_READY\"" 0` `git diff src==0` `git diff V70==0` `git diff V72P0==0` `used_2m false used_test false` `T_LF01-08 1e-12` `P1A pack/prefix/incremental/tag wall≤30` `P1B 64/512 8trials c3 observed_zero&&observed_one 负向测试 worst<1e-9 tree wall≤30` `P1C rank9036 zero0 dup0 pivot4 1/3/10 wall<1/5/30s syndrome增量tag exact` `P1D n12 k3 cycle1 capacity_warning 描述性` `edges nnz≈49698 CSR≈235KB peak<2GiB O` `5-state first-match 4 hard PASS && wall≤30 && P1D不过门禁` `overall ADAPTER_PLAN_READY/NOT_READY 5counts` `T0-T3 true` `S1-S10 10步 3类型` `V72_not_started` `TBD 0` `报告与json一致` `四工件+registry+探针+双报告 已单独提交推送 新Plan SHA`
