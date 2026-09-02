# OpenSpec Design: formal-ir-v72p1-soft-joint-binary-adapter

**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — 最小 adapter 衔接 1024 local factor 自排除 ↔ binary IRA mother 9036×10240 nnz=49620 prefix1111 tail4 精确复用 V72P0 mother
**Cycle**: `V72P1-ADP` predecessor `V72P0-SYN 5591e16b` + `V71-SJK` + `V70-BSJ` HEAD `b1b2e9c51f60bcf4ecd6b41e17ca12e0e617e4b2` data `84d62779` — SYNTHETIC_ONLY
**Branch**: `formal-ir-mainline`
**Baseline SHA**: `b1b2e9c51f60bcf4ecd6b41e17ca12e0e617e4b2`

## 1. Configuration Strict Separation

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
Exactly 9 fields.

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

All four artifacts consistent. Old adapter config type removed.

## 2. Core Arrays Strict Freeze — Exactly 11 Working Arrays

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

## 3. Five-Equation Dataflow — COMPLETE and IDENTICAL

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
3. local factor self-exclusion: other_bits_excluding_b
4. variable_to_check must include factor_to_bit
5. app_llr must include factor_to_bit
6. check update must depend on syndrome_target
7. no extra binary channel prior/LLR
8. forbid:
   app_llr
   must not be computed as prior plus sum(c2v)

## 4. Unified Memory Table — Authoritative Aperture

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
Single authoritative table.

## 5. Prefix / Checkpoint

- Disclosure prefixes {160,168,...,9032,9036} count 1111 (regular +8 count 1110, tail 4)
- Decoder checkpoints {160,288,...,8992,9032,9036} count 72

## 6. Data Role and 10-step S1-S10

S1 synthetic_bits b[10240] → S2 prior_logp[1024,1024] → S3 local factor self-exclusion → S4 extrinsic打包 → S5 mother前缀 Δ8 vs checkpoint → S6增量 syndrome → S7披露计费 → S8 exact tag → S9 edges/memory → S10 5-state分流. Detailed steps unchanged but must use five-equation dataflow above.

## 7. P1A/B/C/D Synthetic Layers

P1A plumbing deterministic, P1B tiny k2/3 n6/9 64/512 8trials, P1C 9036x10240 1/3/10 iter finite/maxLLR/residual, P1D small loopy n12 k3 — all unchanged, but underlying arrays/dataflow/memory per sections 2-4.

## 8. Acceptance Tests (Semantic)

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
- T-MEMORY-1: mechanical recompute per dtype/shape matches frozen table

Future-implementation tests, acceptance criteria.

## 9. Guards R72P1-01~10

01 exact mother reuse, 02 five-equation dataflow, 03 config 8 fields, 04 Δ8 vs checkpoint 72, 05 P1C 1/3/10, 06 memory table, 07 first-match AND, 08 no tolerance, 09 four-artifact only, 10 SYNTHETIC_ONLY.

## 10. No Code Implementation

This change is plan-only. No src/ modification, no decoder run.

# 权威合同校验行 max_total_iterations 720 warm_start true dtype float64 prior_logp[N,Q] local_factor_extrinsic other_bits_excluding_b syndrome_aware_spa syndrome_target factor_to_bit[v] checkpoint_rows FrozenMotherSpec SoftJointConfig 11 arrays 5 equations
