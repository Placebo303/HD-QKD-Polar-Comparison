# OpenSpec Tasks: formal-ir-v72p0-soft-joint-binary-synthetic

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Implementation**: `5591e16bf35b03c3df30a003bee12011a796d73e` (EXTERNAL_BINDING) **Evidence**: `64ca2f1e653f2386d870feff4d83f5bcc99db1e9`
**Data**: `84d62779 synthetic_v72p0` `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false`

## Phase A — 合成注册表
- [x] **A1 冻结合成注册表 `v72p0_data_registry_synthetic.json`**：`schema v72p0_synthetic_v1 head 5591e16b Q1024 N1024 M9036 f1.3 used_2m false successor_v72_not_started P0A {k2/3 n6/9 64/512 8trials tree-only} P0B {9036x10240 sparse_CSR_IRA r0 160 Δ8}` 已验 `rg -i "2M" 0 hits`
- [x] **A2 列序与去self冻结**：`bit_i(s)=(s>>i)&1 col sym*10+bit Σ_{j≠i}` 已验 `V72_not_started`

## Phase B — 冻结主体零改
- [x] **B1 主体明文化 `v72p0_manifest.json:frozen_body`**：`Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED tag64b exact` `git diff -- src/ ==0` 已验
- [x] **B2 合成权威算法复用**：legacy_v1 synthetic bits→H syndrome→tag→LF→wall 不读2M
- [x] **B3 守卫**：`rg decode_ 0 hits` `rg "READY" 0 hits` `rg v72.*run_01 0 hits` `py_compile PASS`

## Phase C — 去self 8测试
- [x] **C1 去self定义**：`log_post_excl_i = log_prior+Σ_{j≠i} − logZ` 已落盘
- [x] **C2 纯函数 log-domain**：`validate_local_factor` `T_LF01-08` `1e-12/1e-9` `i=0,5,9` 已验
- [x] **C3 落盘**：`v72p0_results.json:local_factor T_LF01-08 KERNEL_PASS` 已验

## Phase D — Backend 6问三态 enum
- [x] **D1 Q1-Q3**：`IntEnum PASS/FAIL/NOT_APPLICABLE` AST探针 已验
- [x] **D2 Q4-Q6**：`Q4 self_excl Q6 9036` 已验 `rg "READY" 0 hits`
- [x] **D3 分流**：`READY/ADAPTER/NOT_COMPATIBLE` enum `==BackendState.READY` 已验

## Phase E — P0A tiny k2/3 total6/9 64/512 8trials tree-only syndrome 0/1 1e-9
- [x] **E1 P0A执行**：`(2,6)64 (3,9)512 各8trials exhaustive tree BP vs brute c3 observed_zero&&observed_one c5 1e-9 wall≤30s` 已验 `worst<1e-9`
- [x] **E2 tag exact + incremental**：`wall/peak` 已落盘
- [x] **E3 负向测试**：`observed_one==false ⇒ c3 false` 不变数值 (64/512, wall, delta 保持) 已验

## Phase F — P0B sparse CSR IRA 9036x10240
- [x] **F1 mother生成**：`SeedSequence V72P0-SYN-MOTHER` sparse CSR dual-diagonal `nnz≈49620` 已验
- [x] **F2 C1-C4**：`rank9036 row_min>0 dup0 prefix_nested` `pivot 160/168/176/9036` 已验
- [x] **F3 C5-C6**：`incremental tag64 exact 64 samples` `P0B_PASS` 已验

## Phase G — 5-state
- [x] **G1 5终态**：`EVIDENCE>KERNEL>TINY>MATRIX>ADAPTER_PLAN_READY (需3passes)` 已验
- [x] **G2 overall**：`ADAPTER_PLAN_READY / NOT_READY` +5计数 已验
- [x] **G3 审计表**：`per_k/m/n/total/exhaustive/c3_observed/worst/wall` 已落盘

## Phase H — 四件双报告 + T0-T3
- [x] **H1 `scripts/v72p0_soft_joint_binary_synthetic.py`**：`rg decode_ 0 hits` `py_compile PASS` 产 results/table/manifest/SYN_REPORT
- [x] **H2 `scripts/v72p0_backend_audit.py`**：`rg decode_ 0 hits` `rg "READY" 0 hits` `IntEnum` 产 audit/BACKEND_REPORT
- [x] **H3 T0-T3**：T0 compile/tiny-math 1e-12 T1 8test+enum T2 fake replay T3 regression 已验 `T0_T3 true`
- [x] **H4 双报告**：`V72P0_SYN_REPORT.md` (T_LF/P0A c3_obs/P0B sparse/wall) `V72P0_BACKEND_AUDIT_REPORT.md` (Q1-Q6 enum) 与 json 一致
- [x] **H5 自检 R72-01~09**：`py_compile rg0 git diff src==0 used_2m false T_LF P0A P0B wall f NOT_MEASURED V72_not_started` 已验 无TBD
- [x] **H6 小测试**：`pytest -p no:cacheprovider -q test_v72p0_*.py` PASS `c3 observed` `negative` `5-state`

## Phase I — 守卫 + 推送
- [x] **I1 R72-01~09**：9守卫 true 已落盘
- [x] **I2 提交推送 provenance 5591e16b/64ca2f1e EXTERNAL_BINDING**：`git add openspec/changes/formal-ir-v72p0-soft-joint-binary-synthetic/ scripts/v72p0_*.py v72p0_*.json/csv/md test_v72p0_*.py && git commit && git push origin formal-ir-mainline` 待执行
- [x] **I3 停留 PLAN_CANDIDATE 不创run_01 不启V72**：`ls run_01 不存在` 已验 等待 Pre-RESULT 审核

## 禁止
`decode_/construct_business/2M/MET/V72/run_01/字符串READY` 均 `0 hits` 已验
