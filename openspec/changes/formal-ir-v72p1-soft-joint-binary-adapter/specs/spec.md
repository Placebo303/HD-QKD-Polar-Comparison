# OpenSpec Spec: formal-ir-v72p1-soft-joint-binary-adapter

**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`
**Change**: `formal-ir-v72p1-soft-joint-binary-adapter` (`V72P1-ADP`) `formal-ir-mainline` **Baseline** `b1b2e9c51f60bcf4ecd6b41e17ca12e0e617e4b2` **Data** `84d62779 synthetic_v72p1` **本轮只四工件**
**Predecessor**: `V72P0-SYN 5591e16b` + `V71-SJK e038114d` + `V70-BSJ 9bc34be6` 精确复用 V72P0 mother

## 1. 变更类型与生命周期
- **Type**: `SYNTHETIC_ADAPTER_MINIMAL` `10步 S1-S10 + 11 arrays + 5 equations + prefix1111 checkpoint72`
- **Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` 止于 4 工件修订，不跑 decoder，不创 run_01 不启 V72
- **Branch**: `formal-ir-mainline`
- **Data**: `84d62779 synthetic_v72p1` `Q1024 N1024 Nbit10240 M9036 f_planning 1.3`

## 2. 冻结配置 — Strict Separation

### FrozenMotherSpec (9 fields, tag_bits NOT here)
```
FrozenMotherSpec:
  Q = 1024
  N = 1024
  Nbit = 10240
  M = 9036
  r0 = 160
  delta = 8
  max_rows = 9036
  f_planning = 1.3
  column_mapping = "sym*10+bit"
```

### SoftJointConfig (exactly 8 fields)
```
SoftJointConfig:
  checkpoint_rows = {160,288,...,8992,9032,9036}
  max_iter_per_checkpoint = 10
  max_total_iterations = 720
  llr_clip = <float>
  convergence_tol = <float>
  warm_start = true
  dtype = "float64"
  tag_bits = 64
```
Exactly 8 fields. tag_bits only in SoftJointConfig. warm_start=true, dtype="float64", tag_bits=64.
Old adapter config type removed; only above two configs exist.

## 3. 核心数组 — Exactly 11 Working Arrays

| # | name | dtype | shape |
|---|---|---|---|
| 1 | prior_logp | float64 | [N,Q] (1024,1024) |
| 2 | bit_to_factor | float64 | [N,10] |
| 3 | factor_to_bit | float64 | [N,10] |
| 4 | variable_to_check | float64 | [nnz] |
| 5 | check_to_variable | float64 | [nnz] |
| 6 | app_llr | float64 | [Nbit] |
| 7 | hard_bits | uint8 | [Nbit] |
| 8 | hard_symbols | uint16 | [N] |
| 9 | syndrome_target | uint8 | [active_rows] |
| 10 | syndrome_observed | uint8 | [active_rows] |
| 11 | factor_workspace | float64 | [Q] |

Prior is prior_logp float64[N,Q] (1024,1024).
Prohibit:
- shape [Nbit] for variable_to_check
- duplicate app_llr
- extrinsic[N,Q,10]
- extra binary LLR
- var_belief

## 4. 数据流 — Five-Equation Dataflow COMPLETE and IDENTICAL

```
bit_to_factor[sym,b] = sum(check_to_variable[e] for e incident to variable(sym,b))
factor_to_bit[sym,b] = local_factor_extrinsic(prior_logp[sym,:], bit_to_factor[sym,other_bits_excluding_b])
variable_to_check[e=(v,c)] = factor_to_bit[v] + sum(check_to_variable[e2] for e2 incident to v if e2.check != c)
check_to_variable[e=(c,v)] = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c])
app_llr[v] = factor_to_bit[v] + sum(check_to_variable[e] for e incident to v)
```

8 semantic notes:
1. prior only once in local factor
2. bit_to_factor only aggregates check_to_variable
3. local factor self-exclusion other_bits_excluding_b
4. variable_to_check must include factor_to_bit
5. app_llr must include factor_to_bit
6. check update must depend on syndrome_target
7. no extra binary channel prior/LLR
8. forbid:
   app_llr
   must not be computed as prior plus sum(c2v)

## 5. 内存 — Unified Memory Table Authoritative

| array | bytes | note |
|---|---|---|
| prior_logp | 8,388,608 B = 8 MiB | 1024*1024*8 |
| bit_to_factor | 81,920 B = 80 KiB | 1024*10*8 |
| factor_to_bit | 81,920 B = 80 KiB | 1024*10*8 |
| variable_to_check | 396,960 B ≈ 388 KiB | 49620*8 |
| check_to_variable | 396,960 B ≈ 388 KiB | 49620*8 |
| app_llr | 81,920 B = 80 KiB | 10240*8 |
| hard_bits | 10,240 B = 10 KiB | 10240*1 |
| hard_symbols | 2,048 B = 2 KiB | 1024*2 |
| syndrome_target | 9,036 B ≈ 9 KiB | 9036*1 |
| syndrome_observed | 9,036 B ≈ 9 KiB | 9036*1 |
| factor_workspace | 8,192 B = 8 KiB | 1024*8 |

11 arrays total: 9,466,840 B ≈ 9.03 MiB
CSR: indptr 36,148 B ((9037*4)), indices 198,480 B (49620*4), data 49,620 B, CSR total 284,248 B ≈ 278 KiB
Grand total 9,751,088 B ≈ 9.30 MiB, plus temp still <2 GiB

## 6. 前缀与检查点

- Disclosure prefixes {160,168,...,9032,9036} count 1111 (regular +8 count 1110, tail 4)
- Decoder checkpoints {160,288,...,8992,9032,9036} count 72

## 7. 数据角色与就绪门

SYNTHETIC_ONLY, P1A plumbing indptr/indices相等, P1B 64/512 8trials, P1C 9036x10240 1/3/10 iter finite/maxLLR/residual, P1D n12 k3 loopy, 2M/TEST sealed.

## 8. Phase C/D/E/F/G Details

Same as design/tasks but referencing five-equation dataflow and 11 arrays and memory table above.

## 9. 分流 5-state first-match AND + overall 2-state

```
if !synthetic_bits_ok or !H_mother_exists → EVIDENCE_INCOMPLETE
elif !T_LF01_02_PASS → KERNEL_FAIL
elif !P1A_PASS or !P1B_PASS → PLUMBING_TINY_FAIL
elif !P0B_revalidate_PASS or !P1C_PASS → MATRIX_SMOKE_FAIL
elif T_LF01_08_PASS and P1A_PASS and P1B_PASS and P1C_PASS and wall≤30 and finite==true → ADAPTER_PLAN_READY
else → MATRIX_SMOKE_FAIL
overall = ADAPTER_PLAN_READY iff ∀cases READY else NOT_READY
```

## 10. Acceptance Tests — Semantic (future-implementation)

- T-DATAFLOW-1: factor_to_bit non-zero, all check_to_variable zero, assert variable_to_check equals factor_to_bit
- T-DATAFLOW-2: same condition
  app_llr must equal factor_to_bit
  not
  prior
  (assert app_llr[v] equals factor_to_bit[v] when check_to_variable zero)
- T-DATAFLOW-3: flip syndrome_target[c] only, check_to_variable must show sign/coset change
- T-DATAFLOW-4: change prior_logp only via local_factor_extrinsic, not direct add in variable/check/APP
- T-DATAFLOW-5: self-exclusion: changing incoming bit_to_factor of target bit must not affect its factor_to_bit; changing other bits should
- T-CONFIG-1: FrozenMotherSpec vs SoftJointConfig field sets exactly equal, no cross/duplicate (tag_bits only in SoftJointConfig)
- T-MEMORY-1: mechanical recompute per dtype/shape matches frozen table (11 arrays 9466840, CSR 284248, grand 9751088)

Future-implementation tests, acceptance criteria covering semantics not just strings.

## 11. 守卫 R72P1-01~10 本轮只四工件
01 exact mother reuse 49620, 02 five-equation, 03 SoftJointConfig 8 fields, 04 Δ8 vs checkpoint72 1111/72, 05 P1C 1/3/10 finite/maxLLR/residual, 06 memory 9466840/284248/9751088, 07 first-match AND, 08 no tolerance, 09 four-artifact only, 10 SYNTHETIC_ONLY no run_01.

## 12. 验收 本轮只四工件 保持未完成
`py_compile PASS` `used_2m false` `T_LF01-08 1e-12` `SoftJointConfig 8 fields` `11 arrays` `five-equation identical` `memory 9466840 CSR 284248 grand 9751088` `prefix1111 checkpoint72` `T-DATAFLOW-1..5 T-CONFIG-1 T-MEMORY-1` `no forbidden patterns` `all required patterns` `PLAN_REVISE_REQUIRED`.

# 权威合同校验行 max_total_iterations 720 warm_start true dtype float64 prior_logp[N,Q] local_factor_extrinsic other_bits_excluding_b syndrome_aware_spa syndrome_target factor_to_bit[v] checkpoint_rows FrozenMotherSpec SoftJointConfig 11 arrays 5 equations
