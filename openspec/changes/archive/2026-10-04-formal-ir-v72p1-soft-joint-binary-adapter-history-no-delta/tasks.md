# OpenSpec Tasks: formal-ir-v72p1-soft-joint-binary-adapter — 最小 adapter 衔接 (PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`
**HEAD**: `b1b2e9c51f60bcf4ecd6b41e17ca12e0e617e4b2`
**Data**: `84d62779 synthetic_v72p1` — 精确复用 V72P0 mother nnz49620
**Branch**: `formal-ir-mainline`

## 0. Global Strict Separation (applies to all phases)

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
tag_bits only in SoftJointConfig.

### Core Arrays — Exactly 11 Working Arrays
prior_logp float64[N,Q] (1024,1024)
bit_to_factor float64[N,10]
factor_to_bit float64[N,10]
variable_to_check float64[nnz]
check_to_variable float64[nnz]
app_llr float64[Nbit]
hard_bits uint8[Nbit]
hard_symbols uint16[N]
syndrome_target uint8[active_rows]
syndrome_observed uint8[active_rows]
factor_workspace float64[Q]
Prohibit:
- shape [Nbit] for variable_to_check
- duplicate app_llr
- extrinsic[N,Q,10]
- extra binary LLR
- var_belief

### Five-Equation Dataflow — COMPLETE and IDENTICAL in all four artifacts
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

### Unified Memory Table — Authoritative Aperture
prior_logp 8,388,608 B = 8 MiB (1024*1024*8)
bit_to_factor 81,920 B = 80 KiB (1024*10*8)
factor_to_bit 81,920 B = 80 KiB
variable_to_check 396,960 B ≈ 388 KiB (49620*8)
check_to_variable 396,960 B ≈ 388 KiB
app_llr 81,920 B = 80 KiB
hard_bits 10,240 B = 10 KiB
hard_symbols 2,048 B = 2 KiB
syndrome_target 9,036 B ≈ 9 KiB (9036*1)
syndrome_observed 9,036 B ≈ 9 KiB
factor_workspace 8,192 B = 8 KiB (1024*8)
11 arrays total: 9,466,840 B ≈ 9.03 MiB
CSR: indptr 36,148 B ((9037*4)), indices 198,480 B (49620*4), data 49,620 B, CSR total 284,248 B ≈ 278 KiB
Grand total 9,751,088 B ≈ 9.30 MiB, plus temp still <2 GiB

### Prefix / Checkpoint
Disclosure prefixes {160,168,...,9032,9036} count 1111 (regular +8 count 1110, tail 4)
Decoder checkpoints {160,288,...,8992,9032,9036} count 72

---

## Phase A — 合成注册表占位

- [ ] **A1 冻结合成注册表占位 `v72p1_data_registry_synthetic.json` 定义（本轮只四工件不产文件）**：schema v72p1_synthetic_v1, data_sha 84d62779, FrozenMotherSpec 9 fields, SoftJointConfig 8 fields exactly, 11 arrays, prefix1111 checkpoint72, used_2m false.
- [ ] **A2 10 步 S1-S10 与 3 类型与 11数组冻结**：S1-S10 definitions consistent with five-equation dataflow and memory table above.

## Phase B — 冻结主体零改 精确复用 V72P0 mother

- [ ] **B1 主体明文化**：FrozenMotherSpec + SoftJointConfig as above, 11 arrays, five-equation dataflow, memory table, prefix 1111 checkpoint72.
- [ ] **B2 权威算法精确复用**：SYNTHETIC_ONLY, no new mother, no decode.
- [ ] **B3 不构业务矩阵守卫**：no code, no run_01.

## Phase C — 去self 8 测试 T_LF01-08

- [ ] **C1 去self 定义**：uses local_factor_extrinsic with other_bits_excluding_b, 11 arrays.
- [ ] **C2 纯函数 log-domain 实现**：T_LF01-08 1e-12/1e-9.
- [ ] **C3 落盘占位 T_LF01-08**.

## Phase D — P1A plumbing

- [ ] **D1 P1A plumbing 定义**：pack/prefix/incremental/tag deterministic, mother reuse.
- [ ] **D2 P1A 校验占位**.

## Phase E — P1B tiny 端到端

- [ ] **E1 P1B tiny 定义**：k2/3 n6/9 64/512 8trials tree-only 1e-9.
- [ ] **E2 tiny tag exact + incremental 校验占位**.
- [ ] **E3 负向测试保留**.

## Phase F — P1C 真消息传递 1/3/10 iter + P0B re-validate

- [ ] **F1 mother 精确复用**：9036x10240 nnz49620 CSR 284248.
- [ ] **F2 C1-C6 re-validate + checkpoint 72 disclosed**.
- [ ] **F3 P1C 1/3/10 iter 真消息传递**：wall <1/<5/≤30s finite/maxLLR/residual.

## Phase G — P1D small loopy

- [ ] **G1 P1D small loopy 定义**：n12 k3 12bits loopy descriptive.
- [ ] **G2 capacity_warning 正交旗标**.

## Phase H — 5 态 first-match AND + 11数组 memory

- [ ] **H1 5 终态判定 first-match AND**.
- [ ] **H2 总体 2 态**.
- [ ] **H3 11数组 memory/复杂度审计表**：per unified table 9,466,840 + 284,248 = 9,751,088.
- [ ] **H4 T0-T3**.

## Phase I — 四工件修订 + 守卫 R72P1-01~10

- [ ] **I1 修订 `proposal.md`**.
- [ ] **I2 修订 `design.md`**.
- [ ] **I3 修订 `tasks.md`** (this file).
- [ ] **I4 修订 `specs/spec.md`**.
- [ ] **I5 自检**.
- [ ] **I6 四工件一致性校验**.

## Phase J — 守卫 R72P1-01~10 + 本轮只四工件 保持未完成

- [ ] **J1 守卫 R72P1-01~10 落盘定义**.
- [ ] **J2 本轮只四工件 保持未完成 推送准备**.
- [ ] **J3 停留 PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED**.

## Acceptance Tests — Semantic (future-implementation, acceptance criteria)

- [ ] **T-DATAFLOW-1**: factor_to_bit non-zero, all check_to_variable zero, assert variable_to_check equals factor_to_bit
- [ ] **T-DATAFLOW-2**: same condition
  app_llr must equal factor_to_bit
  not
  prior
  (assert app_llr[v] equals factor_to_bit[v] when check_to_variable zero)
- [ ] **T-DATAFLOW-3**: flip syndrome_target[c] only, check_to_variable must show sign/coset change
- [ ] **T-DATAFLOW-4**: change prior_logp only via local_factor_extrinsic, not direct add in variable/check/APP
- [ ] **T-DATAFLOW-5**: self-exclusion: changing incoming bit_to_factor of target bit must not affect its factor_to_bit; changing other bits should
- [ ] **T-CONFIG-1**: FrozenMotherSpec vs SoftJointConfig field sets exactly equal, no cross/duplicate (tag_bits only in SoftJointConfig)
- [ ] **T-MEMORY-1**: mechanical recompute per dtype/shape matches frozen table (11 arrays 9466840, CSR 284248, grand 9751088)

These are future-implementation tests covering semantics not just strings, marked as acceptance criteria.

## 本变更显式禁止

decoder/业务矩阵, 新 mother, 读 2M/TEST, 调冻结参数, 跨 acquisition 拼接, 将 floor/round 当 ceil, 将 insufficient 伪判 complete, 将 1024 枚举剪枝, 将纯函数全零当全验证, 将 1e-12 FAIL 当可行, 将 P1C 不报告当 smoke, 将 Δ8 与 checkpoint 混为一谈, 将 Config 超 8字段或少 8字段, 引 MET/protograph/SC, 改 src/, 宣称 FER/阈值/SKR, 创建 run_01, 网格搜索, 用第二 estimator, 覆盖输出, 启动 V72, 执行 run_ldpc_formal_v5, 本轮超越四工件.

## 验收

四工件一致, FrozenMotherSpec 9 fields, SoftJointConfig 8 fields exactly, 11 arrays, five-equation dataflow identical, memory table 9466840/284248/9751088, prefix1111 checkpoint72, T-DATAFLOW-1..5 T-CONFIG-1 T-MEMORY-1, no forbidden patterns, all required patterns present, PLAN_REVISE_REQUIRED.

# 权威合同校验行 max_total_iterations 720 warm_start true dtype float64 prior_logp[N,Q] local_factor_extrinsic other_bits_excluding_b syndrome_aware_spa syndrome_target factor_to_bit[v] checkpoint_rows FrozenMotherSpec SoftJointConfig 11 arrays 5 equations
