# OpenSpec Proposal: formal-ir-v72p0-soft-joint-binary-synthetic

**Status**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal IR / soft-joint binary synthetic correctness
**Change ID**: `formal-ir-v72p0-soft-joint-binary-synthetic`
**Cycle ID**: `V72P0-SYN` predecessor `V71-SJK` + `V70-BSJ`
**Branch**: `formal-ir-mainline`
**Implementation**: `5591e16bf35b03c3df30a003bee12011a796d73e` (EXTERNAL_BINDING)
**Evidence**: `64ca2f1e653f2386d870feff4d83f5bcc99db1e9`
**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1`)
**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`

> ponytail lite: 4 OpenSpec + 1 synthetic spike (numpy 1024 log-domain, sparse CSR IRA) + 1 audit probe. Stdlib only.

## Goal

于冻结主体 `Q=1024 N=1024 Nbit=10240 M=9036 f=1.3 NOT_MEASURED` 下验证 synthetic correctness 链条 `local_factor去self ↔ mother增量 ↔ exact tag`，仅 synthetic，不跑 decoder，不启 V72。

### 冻结项
- `Q=1024 N=1024 Nbit=10240 M=9036 f=1.3 NOT_MEASURED used_2m false`
- `tag 64b exact SHA256(bits)[:8B]==SHA256(s_hat)[:8B] LE`
- `col sym*10+bit` `bit_i(s)=(s>>i)&1`

### local factor 去self + 8测试
`LLR_{→i}=logsumexp_{1}−logsumexp_{0} | Σ_{j≠i} bits_j·llr_j`，`T_LF01-08` 正交 `1e-12/1e-9`，`logsumexp` 实现，无 numba。

### P0A tiny k=2/3 total 6/9 64/512 8trials tree-only syndrome 0/1 1e-9
- `k∈{2,3} n∈{6,9} total_bits 6/9 exhaustive 64/512` 各 8 trials，`Q=1024` 不变
- `H_small` tree forest (each var degree 1) 保证无环，BP exact
- `syndrome 0/1 flip` 显式，`c3 = observed_zero && observed_one` fail-closed（两值均观测才 PASS），加负向测试
- `c5` exact posterior `max|Δ|<1e-9` tree-only，`wall≤30s peak≤2048MiB`
- `7 checks` fail-closed：`c1 isfinite / c2 brute exists isfinite / c3 observed_zero&&observed_one / c4 brute exists / c5 1e-9 / c6 tree / c7 total≤9 exhaustive`

### P0B sparse CSR IRA 9036x10240
- `H_mother 9036×10240` `n_info=1204` `H_p dual-diagonal` (diag+subdiag) `det=1 ⇒ rank=9036`，info 每行 3-4 列，`nnz≈5.5/m`，`zero_cols=0 dup=0`
- `r0=160 Δ8 →9036`，`pivot 160/168/176/9036`，`prefix_nested`，`C1-C6` 全 PASS

### 5-state
`EVIDENCE_INCOMPLETE > KERNEL_FAIL > TINY_FAIL > MATRIX_FAIL > ADAPTER_PLAN_READY` (需 3 passes: KERNEL ∧ P0A ∧ P0B)，`overall ADAPTER_PLAN_READY / NOT_READY`

### T0-T3
T0 compile/import/tiny-math 1e-12；T1 unit & tamper 8test+enum；T2 fake/test-only replay；T3 regression `decode_ 0 hits` `V70/V71` 只读。

## Non-Goals
不跑 decoder，不构业务 disclosure，不读 2M real，不改 Q/N/M/f/tag，不引 MET/protograph/SC/Gray，不启 V72，不创 run_01。

## Scope
1. 冻结主体零改
2. 去self 8测试
3. P0A k2/3 6/9 64/512 8trials tree-only syndrome 0/1 1e-9 c3 observed_zero&&observed_one
4. P0B sparse CSR IRA 9036x10240 5-state
5. T0-T3 + 双报告

## Impact Scope
新增 `scripts/v72p0_*.py` + `v72p0_*.json/csv/md` + `test_v72p0_*.py`；只读 `ldpc_v5.py`；不改 `src/`。

## Acceptance Criteria
- [x] 4 工件齐全 `5591e16b / 64ca2f1e` EXTERNAL_BINDING
- [x] `src/ git diff==0` `used_2m false` `f NOT_MEASURED` `run_01` 不存在
- [x] `T_LF01-08` 1e-12/1e-9 去self
- [x] `P0A k2/3 6/9 64/512 8trials` `c3 observed_zero&&observed_one` 负向测试 `worst<1e-9` tree-only wall≤30s
- [x] `P0B sparse CSR IRA` `rank9036 zero0 dup0 pivot 4点`
- [x] `5-state` `ADAPTER_PLAN_READY` 需 3 passes
- [x] `py_compile PASS` `pytest PASS` `rg decode_ 0 hits` `rg "READY" 0 hits`
- [x] 双报告与 json/csv 一致，无 TBD，不启 V72
