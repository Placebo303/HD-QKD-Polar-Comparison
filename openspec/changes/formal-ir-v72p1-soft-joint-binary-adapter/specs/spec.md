# OpenSpec Spec: formal-ir-v72p1-soft-joint-binary-adapter

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Change**: `formal-ir-v72p1-soft-joint-binary-adapter` (`V72P1-ADP`) `formal-ir-mainline` **Implementation** `TBD (freeze-time git rev-parse HEAD)` **Data** `84d62779 synthetic_v72p1` **本轮只四工件**
**Predecessor**: `V72P0-SYN 5591e16b` + `V71-SJK e038114d` + `V70-BSJ 9bc34be6` 精确复用 V72P0 mother 删新 seed

## 1. 变更类型与生命周期
- **Type**: `SYNTHETIC_ADAPTER_MINIMAL` `10步 S1-S10 + 3类型 Config8字段/Result/Adapter + 5公式 + P1A plumbing / P1B tiny 64/512 8trials tree-only 1e-9 c3观测 / P1C 真消息传递 1/3/10 iter 报告finite/maxLLR/residual 9036×10240 nnz49620 精确复用 / P1D small loopy n12 k3 描述性 + 11数组 memory O(nnz+N*Q*10) + 5态 first-match AND`
- **Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` 止于 4 工件修订，本轮只四工件，不产 registry/脚本/报告，不创 run_01 不启 V72
- **Branch**: `formal-ir-mainline` **EXTERNAL_BINDING until Pre-RESULT** `TBD / synthetic_v72p1`
- **Data**: `84d62779 synthetic_v72p1` `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED nnz49620 used_2m false used_test false 精确复用 V72P0 mother indptr/indices相等`
- **f**: `1.3 NOT_MEASURED` 仅参照，`leak_r = r·1+64` `disclosed=r_checkpoint+64`
- **V72**: `NOT_STARTED` `本轮只四工件`

## 2. 冻结方法
- `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false tag64b exact SHA256 LE col sym*10+bit bit_i(s)=(s>>i)&1`
- `LF 去self Σ_{j≠i} T_LF01-08 1e-12/1e-9 logsumexp 11数组 llr_ext[10][1024]`
- `mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036 nnz=49620 prefix1111 tail4 精确值 indptr/indices与V72P0 byte-equal 零容差 删V72P1 新seed 新 seed`
- `Rs_Δ r0 160 Δ8 max9036 r∈{160,168,...,9032,9036} 与 checkpoint 72批量 r_checkpoint∈{160,288,...,8992,9036} max9036 上限 分离 报告disclosed`
- `adapter pack / syndrome / tag / prefix / incremental 纯函数 11数组`
- `10 步 S1-S10: S1 bits → S2 prior → S3 LF 11数组 → S4 pack → S5 mother Δ8 vs checkpoint → S6 syndrome → S7 leak disclosed → S8 tag → S9 11数组 memory O(nnz+N*Q*10) → S10 5-state first-match AND`
- `3 类型: AdapterConfig 8字段 {checkpoint_rows, max_iter_per_checkpoint, max_total_iterations, llr_clip, convergence_tol, warm_start, dtype, tag_bits} / AdapterResult / Adapter 11数组`
- `P1A plumbing indptr/indices相等 / P1B tiny 64/512 8trials c3_obs 1e-9 / P1C 真消息 1/3/10 finite/maxLLR/residual 报告 / P1D loopy n12 k3 descriptively`
- `5-state ADAPTER_PLAN_READY 需 KERNEL∧P1A∧P1B∧P1C 4硬 AND wall≤30 finite==true 本轮只四工件`
- `T0-T3`  本轮只四工件

### 2.2 禁止
禁改冻结量、新增 mother 新 seed（删 `V72P1 新seed`）、`1 pct容差` 容差、`OR SYM` 误用、新增 disclosure、MET/2M/V72、字符串 `"ADAPTER_PLAN_READY"` 直判（须 `IntEnum`）、改 `src`/V70/V72P0、创建 run_01、本轮超越四工件。

## 3. 数据角色

| 集合 | 规模 | 说明 |
|---|---|---|
| P1A plumbing | 4 probes 1024态 + 9036前缀 nnz49620 精确 | 确定性/前缀/增量/tag indptr/indices相等 wall≤30s |
| P1B k2 n6 | 64 exh ×8 trials 11数组 | c3 observed_zero&&observed_one c5 1e-9 tree |
| P1B k3 n9 | 512 exh ×8 trials 11数组 | 同上 |
| P1C 真消息 | 9036×10240 nnz49620 ×1/3/10 iter 真消息 | C1-C6 + checkpoint 72批量 + wall<1/5/30s finite/maxLLR/residual |
| P1D loopy | n12 k3 12bits ×8 trials 11数组 | 单环 descriptively capacity_warning |
| P0B re-validate | 9036×10240 nnz49620 精确复用 | C1-C6 checkpoint 复用校验 indptr/indices相等 |
| 2M/TEST | 密封不读 | used_2m false used_test false |

注册表占位 `v72p1_data_registry_synthetic.json` `schema v72p1_synthetic_v1` `head TBD` `reused_from v72p0_synthetic_v1` `successor_v72_not_started true` `mother精确复用 V72P0 nnz49620 indptr/indices相等 删新 seed` `Config8字段` `11数组` 本轮只定义不产文件

### 3.2 就绪门
`Q1024 N1024 M9036 nnz49620 f1.3 NOT_MEASURED used_2m false used_test false successor_v72_not_started` 且 `indptr==v72p0_indptr && indices==v72p0_indices` 且 `P1A 4 probes indptr/indices相等` 且 `P1B 64/512 8trials` 且 `P1C 1/3/10 真消息 finite/maxLLR/residual checkpoint disclosed` 且 `P1D n12 k3` 且 `mother rank9036 zero0 dup0 checkpoint 72批量` 且 `Config8字段` 且 `11数组` 否则 `EVIDENCE_INCOMPLETE` 本轮只四工件

## 4. 输入合同
`Q1024 N1024 Nbit10240 M9036 nnz49620 r0 160 Δ8 max9036 checkpoint72 col sym*10+bit bit_i去self LF T_LF01-08 11数组 tag64b exact leak r·1+64 disclosed r+64 f NOT_MEASURED mother 9036×10240 nnz49620 indptr/indices相等 adapter S1-S10 10步 3类型 Config8字段 11数组` 落 `AdapterConfig 8字段`。（更正：checkpoint 128→72；71 vs 72：71为V71因子核历史值、72为V72批量72本变更正值）

## 5. Phase C/D/E/F/G

### 5.2 去self LF (S3, 10步之三，11数组核心)
`log_post_excl_i = prior + Σ_{j≠i} bits_j·llr_j - logZ` `llr_ext[10][1024]` 11数组 `T_LF01-08` `1e-12/1e-9` `i∈{0,5,9}` 三点探针

### 5.3 T_LF01-08
`01 completeness 02 normalization 1e-12 03 marginal 1e-12 04 delta 1e-9 05 self_exclusion 1e-12 06 stability K1e6 isfinite 07 determinism==0 08 brute 1e-12`

### 5.4 Adapter 3 类型 Config8字段 11数组
`AdapterConfig 8字段 {checkpoint_rows, max_iter_per_checkpoint, max_total_iterations, llr_clip, convergence_tol, warm_start, dtype, tag_bits} 精确冻结 多一少一即 FAIL` `AdapterResult {T_LF,P1A,P1B,P1C 真消息 finite/maxLLR/residual,P1D,edges nnz49620, memory 11数组分项 float, wall,class,overall}` `Adapter {pack,syndrome,tag,prefix,incremental} 纯函数 11数组 无 I/O/随机`

### 5.5 5公式（R72P1-02）
`1 prior_logp[1024,1024] log(1/1024) | 2 llr_ext[10][1024] LLR_{→i}=logsumexp_{1}-logsumexp_{0}|Σ_{j≠i} | 3 bit_llr[10240] sym*10+bit | 4 obs_llr[10240] | 5 msg_v2c[49620] v2c | 6 msg_c2v[49620] c2v 2*atanh(Π tanh) | 7 belief_accum[10240] ch+Σc2v finite | 8 check_residual[9036] |residual| maxLLR | 9 syndrome_r[r] H_r·b mod2 | 10 app_llr[10240] | workspace_buf[720] ch+Σc2v maxLLR` 各 float 公式显式 `O(nnz+N*Q*10)`

### 5.6 S1-S10 10 步 精确复用 mother Δ8 vs checkpoint 分离
`S1 b[10240]合成 → S2 prior_logp[1024,1024] → S3 LF去self 11数组 → S4 bit_llr[10240] sym*10+bit → S5 H_mother 9036×10240 nnz49620 indptr/indices相等 H_r prefix Δ8 {160,168,...,9032,9036} vs checkpoint {160,288,...,8992,9036} 72批量 max9036 → S6 s_r=H_r·b mod2 增量 s_{r+8}=s_r∪new8 Δ8 → S7 leak r·1+64 disclosed checkpoint+64 f NOT_MEASURED → S8 tag SHA256 LE 64 samples → S9 edges/memory 11数组分项 nnz49620 CSR 278192B 11数组9.2MiB peak<2GiB O(nnz+N*Q*10) → S10 5态分流 first-match AND`

### 5.7 P1A plumbing 精确复用 mother
`pack_determinism==0 ∧ prefix_nested ∀checkpoint∈{160,288,416,9036} H_r==H_mother[0:r] indptr/indices相等 ∧ incremental s_{r+8} 异或一致 Δ8 ∧ tag LE exact 64 samples ∧ indptr_indices_equal byte-equal ∧ wall≤30s ⇒ P1A_PASS AND`

### 5.8 P1B tiny
`for (k2,n6)64 (k3,n9)512 8trials exhaustive tree forest 11数组: c1 isfinite 11数组 / c2 brute isfinite / c3 observed_zero&&observed_one fail-closed + 负向测试 observed_one==false⇒c3 false / c4 brute exists / c5 max|Δ|<1e-9 tree-only / c6 tree / c7 total≤9 ∧ syndrome_ok ∧ tag_ok ∧ worst<1e-9 ∧ wall≤30s ⇒ P1B_PASS AND`

### 5.9 P1C 真消息传递 + P0B re-validate 精确复用 mother
`H_mother 9036×10240 nnz49620 精确 indptr/indices相等 sparse CSR IRA dual-diagonal C1 rank9036 C2 row_min>0 C3 dup0 C4 prefix indptr相等 C5 incremental Δ8 C6 tag pivot checkpoint72 checkpoint 160,288,416,8992,9036 72批量 disclosed 全PASS ∧ 1 iter wall<1s finite==true ∧ 3 iter <5s ∧ 10 iter ≤30s ∧ peak≤2048MiB ∧ syndrome增量/tag exact 三档全PASS 报告 finite/maxLLR/residual ⇒ P1C_PASS AND`

### 5.10 P1D loopy
`n12 k3 total12 8trials 含单环 11数组: syndrome_ok ∧ tag_ok ∧ cycle_count==1 ∧ BP_residual/maxLLR/finite 描述性 ∧ wall ⇒ P1D_descriptive, capacity_warning=(cycle>0||residual>1e-9||!finite) 正交不过硬门禁`

### 5.11 边内存复杂度 11数组分项 float O(nnz+N*Q*10)
`nnz=49620 精确 zero0 dup0 indptr_equal&&indices_equal CSR≈278192B (indices+indptr 234KB+data48192B) 11数组≈9.2MiB (prior_logp8192B+llr_ext80KB+bit_llr80KB+obs_llr80KB+msg_v2c388192B+msg_c2v388192B+belief_accum80KB+check_residual71KB+syndrome9KB+app_llr80KB) peak≤2048MiB per_invocation_ns 已落盘 O(nnz+N*Q*10)=O(49620+1024*1024*10) ponytail ceiling 已标 无1 pct容差`

## 6. 分流 5-state first-match AND + overall 2-state

```
if !synthetic_bits_ok or !H_mother_exists or !indptr_indices_equal → EVIDENCE_INCOMPLETE
elif !T_LF01_02_PASS → KERNEL_FAIL
elif !P1A_PASS or !P1B_PASS → PLUMBING_TINY_FAIL
elif !P0B_revalidate_PASS or !P1C_PASS → MATRIX_SMOKE_FAIL
elif T_LF01_08_PASS and P1A_PASS and P1B_PASS and P1C_PASS and wall≤30 and peak≤2048 and finite==true → ADAPTER_PLAN_READY (需 4 硬 AND 全 PASS，P1D 仅描述，无 OR SYM)
else → MATRIX_SMOKE_FAIL
overall = ADAPTER_PLAN_READY iff ∀cases READY else NOT_READY
# P1D capacity_warning 正交不过硬门禁 无 OR SYM AND gate 精确 无 1 pct容差
# 5 counts {EVIDENCE/KERNEL/PLUMBING_TINY/MATRIX_SMOKE/ADAPTER_PLAN_READY: n}
```

## 7. 报告与表（本轮只四工件占位，下一轮落盘）
`v72p1_table.csv/.json` 行含 `{case/Q/N/M/r/nnz49620/T_LF/P1A indptr/indices相等/P1B c3_obs worst/P1C iter1/3/10 wall/peak/finite/maxLLR/residual/edges/CSR/11数组/syndrome_inc/tag/disclosed 72批量/P1D cycle/capacity/wall/class/overall}` 与 json 行对等
`V72P1_SYN_REPORT.md` (T_LF/P1A plumbing indptr/indices相等/P1B 64/512 worst/P1C 1/3/10 真消息 finite/maxLLR/residual edges/CSR/11数组/wall/disclosed checkpoint/P1D loopy capacity_warning + overall 2态 + S1-S10 3类型8字段 + 11数组 + Δ8 vs checkpoint + 11数组 memory O(nnz+N*Q*10)) 与 json 一致 本轮只四工件占位
`V72P1_BACKEND_AUDIT_REPORT.md` (3类型8字段/10步/11数组/5态 first-match IntEnum) 与 json 一致

## 8. 守卫 R72P1-01~10 本轮只四工件
`01 精确复用 mother nnz49620 indptr/indices相等 删新 seed / 02 5公式 / 03 Config8字段 / 04 Δ8与 checkpoint 分离 72批量 9036 max disclosed / 05 P1C 真消息 1/3/10 finite/maxLLR/residual / 06 11数组 memory 分项 float O(nnz+N*Q*10) / 07 5态 first-match AND 无OR SYM / 08 机械修正 无1 pct容差 保持未完成 / 09 本轮只四工件 / 10 SYNTHETIC_ONLY不创run_01不改V70/V72P0不启V72 精确复用`

## 9. 脚本与证据 本轮只四工件
后续 `scripts/v72p1_soft_joint_binary_adapter.py` `S1-S10 → T_LF→P1A indptr/indices相等→P1B 64/512 c3观测→P1C 9036×10240 nnz49620 1/3/10 真消息 finite/maxLLR/residual→P1D loopy→11数组 memory→5态 first-match AND` `rg "V72P1 新seed" 0 hits` `rg "旧 nnz" 0 hits` `rg "1 pct容差" 0 hits` `rg "decode" 0 hits` `py_compile PASS` 产 `results/table/manifest/SYN_REPORT` 下一轮
后续 `scripts/v72p1_backend_audit.py` `AdapterConfig8字段/Result/Adapter 3类型 + S1-S10 + 11数组 + 5态 IntEnum` `rg "\"ADAPTER_PLAN_READY\"" 0` `py_compile PASS` 产 `audit_report/BACKEND_REPORT` 下一轮
本轮证据 `proposal/design/tasks/specs` 四工件已修订 `head TBD` `EXTERNAL_BINDING` `no_run_01` `V72_not_started` `本轮只四工件`

## 10. 验收 本轮只四工件 保持未完成
`py_compile PASS` `rg "V72P1 新seed" 0 hits` `rg "旧 nnz" 0 hits` `rg "1 pct容差" 0 hits` `rg "OR SYM" 0 hits` `rg "decode" 0 hits` `rg "\"ADAPTER_PLAN_READY\"" 0` `git diff src==0` `git diff V70==0` `git diff V72P0==0` `used_2m false used_test false` `T_LF01-08 1e-12` `Config8字段 {checkpoint_rows, max_iter_per_checkpoint, max_total_iterations, llr_clip, convergence_tol, warm_start, dtype, tag_bits}` `P1A pack/prefix/incremental/tag indptr/indices相等 wall≤30` `P1B 64/512 8trials c3 observed_zero&&observed_one 负向测试 worst<1e-9 tree wall≤30 11数组` `P1C nnz49620 indptr/indices相等 zero0 dup0 checkpoint 160,288,416,8992,9036 disclosed 1/3/10 wall<1/5/30s finite==true syndrome增量tag exact 报告finite/maxLLR/residual` `P1D n12 k3 cycle1 capacity_warning 描述性` `edges nnz49620 精确 CSR≈278192B 11数组≈9.2MiB peak<2GiB O(nnz+N*Q*10)` `5-state first-match 4 硬 AND wall≤30 finite==true P1D不过门禁 无OR SYM` `overall ADAPTER_PLAN_READY/NOT_READY 5counts` `T0-T3 true` `S1-S10 10步 3类型8字段 11数组` `Δ8 vs checkpoint 72批量 disclosed` `V72_not_started` `TBD 0` `报告与json一致` `四工件已修订 保持未完成 本轮只四工件`

max_iter 10 total720 warm_start true float64

内存 9.2MiB workspace streaming 双向 edge

# 权威合同校验行 max10 total720 warm_true float64 9.2MiB prefix1111 tail4 checkpoint72 prior_logp[1024,1024] 11数组 5公式 Config8字段 workspace streaming 双向 edge
