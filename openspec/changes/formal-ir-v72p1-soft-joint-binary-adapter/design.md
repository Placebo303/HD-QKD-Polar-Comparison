# OpenSpec Design: formal-ir-v72p1-soft-joint-binary-adapter

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — **最小 adapter 衔接 1024 local factor 自排除 ↔ binary IRA mother 9036×10240 nnz=49620 prefix1111 tail4 精确复用 V72P0 mother indptr/indices相等 ↔ exact 64-bit tag，10 步 S1-S10 + 3 类型 SoftJointConfig 8字段/Result/Adapter + 5公式，P1A plumbing / P1B tiny 端到端 64/512 8trials tree-only 1e-9 / P1C 真消息传递 1/3/10 iter 报告finite/maxLLR/residual 9036×10240 / P1D small loopy 描述性，11数组 memory O(nnz+N*Q*10)，5 态 first-match AND，不跑 decoder 精确复用 V72P0 mother 不启 V72**

**Cycle**: `V72P1-ADP` predecessor `V72P0-SYN 5591e16bf35b03c3df30a003bee12011a796d73e (V72P0 64ca2f1e)` + `V71-SJK e038114db5095a57158b0e1cd36884d6a1a5d8be` + `V70-BSJ 9bc34be6` + `V67-MAP` HEAD `TBD (freeze-time git rev-parse HEAD)` data `84d62779` 单点 `d1024 bw200 nearest legacy_v1` — **SYNTHETIC_ONLY 精确复用 V72P0 mother nnz=49620 indptr/indices相等，不读 2M，不创 run_01，不启 V72**

**Feasibility**: `V72P0` 证 `去self 8 测试 1e-12/1e-9 + P0A k2/3 n6/9 64/512 8trials c3观测 + P0B sparse CSR IRA 9036×10240 nnz=49620 dual-diagonal rank9036 5-state ADAPTER_PLAN_READY (3 passes)`；`V72P1` 假设 **最小 adapter 以纯函数打包/增量 syndrome/exact tag 可无损衔接 local factor 与 mother**（`P1A 确定性 + P1B tiny 端到端 1e-9 + P1C 真消息传递 1/3/10 finite/maxLLR/residual 边/内存/C1-C6/checkpoint 全 PASS + P1D loopy 描述性`），则 adapter 可零改对接后续 V72 真 mother，需 SYNTHETIC_ONLY 验证 `S1-S10 + 3 类型8字段 + 11数组 + P1A/B/C/D + 11数组 memory O(nnz+N*Q*10) + 5态 first-match` 三重守卫。**R72P1-01 删 V72P1 新seed 新 seed，精确复用 V72P0 mother。**

**Key judgement**: **在 SYNTHETIC_ONLY 合成 bits（Q=1024 先验枚举 + 10-bit 位展开）上，验证最小 adapter 的 10 步数据流无损衔接**：`S3 去self LF 全零得 marginal delta 得确定值与 brute-force 1e-12` 且 `S4 打包 col sym*10+bit 双射 11数组` 且 `S5 母码 prefix 增量 Δ8 vs checkpoint 72批量分离` 且 `S6 增量 syndrome 异或一致` 且 `S8 tag LE exact` 且 `S9 11数组 memory O(nnz+N*Q*10)` 且 `P1B tiny 1e-9 + P1C 真消息 1/3/10 finite/maxLLR/residual wall≤30s`，即判定 `ADAPTER_PLAN_READY`，否则 `PLUMBING_TINY/MATRIX_SMOKE FAIL`。

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 f1.3 NOT_MEASURED tag 64b exact 漏 Σw_i·m_i+64`，**不改 Q/N/M/f/tag/col/去self 语义，精确复用 V72P0 mother nnz=49620 indptr/indices相等**）下，**验证最小 adapter 的 10 步无损衔接 + 11数组 + SoftJointConfig 8字段 + Δ8与checkpoint分离 + P1A/B/C/D 真消息传递 + 11数组 memory 复杂度**：定义 `S1 合成 bits → S2 prior → S3 去self LF → S4 extrinsic打包 11数组 → S5 mother前缀 Δ8 vs checkpoint → S6 增量syndrome → S7 披露计费 checkpoint disclosed → S8 exact tag → S9 11数组 memory → S10 5态分流 first-match` + `3 类型 AdapterSoftJointConfig 8字段/AdapterResult/Adapter` + `5公式` + `P1A plumbing / P1B tiny 64/512 c3观测 1e-9 / P1C 真消息 9036×10240 1/3/10 finite/maxLLR/residual / P1D small loopy`，每 case 5 终端总体 2 态。全程 SYNTHETIC_ONLY，精确复用 V72P0 mother，不跑 decoder，不启 V72。
- **对照**：`V72P0 T_LF/P0A/P0B` 基线作 `KERNEL/P0B re-validate` 对照，母码 `nnz=49620 indptr/indices相等` 精确复用校验；`ldpc_v5` 的 `caps/disclosure` 作 `A5/A6` 轻量对照（只读，不执行）；`1/3/10 真消息传递` 三档作复杂度路由，报告 `finite/maxLLR/residual`。
- **不变量**：`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 f1.3 tag64 col sym*10+bit 去self Σ_{j≠i} H_mother 9036×10240 nnz=49620` 全冻结；**本变更仅验证 adapter 衔接与复杂度，不生成新 mother**。
- **地图性质**：纯 SYNTHETIC_ONLY，`1024 枚举 log-domain + sparse CSR IRA 精确复用 + adapter pack/syndrome/tag + 11数组 + P1A/B/C/D + 11数组 memory`，`2M/TEST` 密封不读，V72P0 复用校验，每 case 5 终端总体 2 态，不启 V72。

## 2. 冻结语义 — 主体与处理点零改（1024维 adapter 不重构，精确复用 V72P0 mother）

| 项 | 冻结值 | 来源 |
|---|---|---|
| Q/N/Nbit/M | 1024 / 1024 / 10240 / 9036 | V72P0 |
| f | 1.3 NOT_MEASURED `used_2m false` | V72P0 |
| tag | 64b exact `SHA256(bits)[:8B] LE` | V72P0 |
| col | `sym*10+bit` `bit_i(s)=(s>>i)&1` `i 0..9 LSB→MSB` | V72P0 |
| LF | 去self `LLR_{→i}=logsumexp_{1}-logsumexp_{0} \| Σ_{j≠i}` 11数组 | V72P0 |
| mother | `H_mother 9036×10240` `n_info 1204` `H_p dual-diagonal det1 rank9036` `info每行3-4` `nnz=49620 精确` `zero0 dup0` `indptr/indices与V72P0 byte-equal` | V72P0 P0B 精确复用，删 V72P1 新seed |
| Rs_Δ | `r0 160 Δ8 →9036` 增量粒度 `r∈{160,168,...,9032,9036}` | V72P0 Δ8 |
| checkpoint | `r_checkpoint ∈ {160,288,416,...,8992,9032,9036} 72批量 max9036 上限 报告disclosed=r+64` | V72P1 R72P1-04 分离 |
| leak | `leak_r = r·1 +64` `disclosed = r_checkpoint+64` `f_actual NOT_MEASURED` | V27/V31 |
| adapter | `pack / syndrome / tag / prefix / incremental` 纯函数 11数组 | V72P1 新增 |
| Config | `AdapterConfig 8字段 {checkpoint_rows, max_iter_per_checkpoint, max_total_iterations, llr_clip, convergence_tol, warm_start, dtype, tag_bits}` 精确冻结 | V72P1 R72P1-03 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` synthetic | V55→V72P1 |
| V72 | **禁止启动** — 任何 V72 预冻结/run_01 禁止 | V72P1 |

**禁令**：`SHALL NOT` 任何 `decode* / construct_*_business / gf_rank_business / nested_business` 业务码；`SHALL NOT` 调 `Q/N/M/f/tag/col/LF/mother/Rs/leak`；`SHALL NOT` 新生成 mother（删 `V72P1 新seed` 新 seed，必须精确复用 V72P0 `nnz=49620 indptr/indices相等`）；`SHALL NOT` 引 `MET/protograph/SC/Gray`（除 adapter 注释）；`SHALL NOT` 读 2M/TEST；`SHALL NOT` 启动 V72；`SHALL NOT` 执行 `run_ldpc_formal_v5`；`SHALL NOT` 改 `src/`；`SHALL NOT` 用 `1 pct容差` 容差（nnz 精确 49620）。

## 3. 数据角色 — SYNTHETIC_ONLY 四层 P1A/B/C/D（零重叠，精确复用 V72P0 mother，不读 2M）

### 3.1 合成集合与复用

| 集合 | 规模 | 说明 |
|---|---|---|
| P1A plumbing | 4 probes × 1024 态 + 9036 前缀 精确复用 mother | `pack / syndrome / tag / prefix_nested / incremental` 确定性 `indptr/indices相等` |
| P1B tiny k2 n6 | 64 exhaustive ×8 trials | tree forest, `c3 observed_zero&&observed_one` `c5 1e-9` |
| P1B tiny k3 n9 | 512 exhaustive ×8 trials | 同上 |
| P1C 真消息传递 | 9036×10240 CSR nnz=49620 1/3/10 iter 真消息 | `wall<1s / <5s / ≤30s` `finite/maxLLR/residual` `C1-C6 re-validate` `checkpoint72 checkpoint 160,288,...,9036 disclosed` |
| P1D small loopy | n12 k3 total 12 bits ×8 trials | 含单环 descriptively `capacity_warning` |
| P0B re-validate | 9036×10240 sparse CSR nnz=49620 精确复用 | 复用 V72P0 `C1-C6 checkpoint` 校验 `indptr/indices相等` |
| 2M/TEST real | 密封不读 | `used_2m false used_test false` |

- **注册表**：`v72p1_data_registry_synthetic.json` (`schema v72p1_synthetic_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head TBD (freeze-time binding), reused_from v72p0_synthetic_v1, successor_v72_not_started true, frozen {Q1024,N1024,Nbit10240,M9036,r0 160,Δ8,max9036,checkpoint 160 72批量 8992 9036 disclosed,max9036,tag f1.3,col sym*10+bit, mother精确复用 V72P0 nnz49620 indptr/indices相等, SoftJointConfig 8字段, 11数组, P1A plumbing, P1B {k2/3 n6/9 64/512 8trials tree-only}, P1C {9036×10240 nnz49620 1/3/10 真消息 finite/maxLLR/residual}, P1D {n12 k3 loopy descriptive}, used_2m false}`)。
- **零改精确复用**：`V72P0` 的 `P0A/P0B` 精确复用 `H_mother nnz=49620 indptr/indices相等`，不重估计；`V70/V71` 的 Stage2 仅对照，不作先验来源；删 `V72P1 新seed` 新 seed。

### 3.2 数据就绪门（SYNTHETIC_ONLY）

```
assert Q==1024 && N==1024 && Nbit==10240 && M==9036 && r0==160 && Δ==8 && max==9036
assert f==1.3 && f_actual=="NOT_MEASURED" && used_2m==false && used_test==false
assert successor_v72_not_started==true && head==TBD (freeze-time)
assert P1A {plumbing probes 4 indptr/indices相等} && P1B {64/512 8trials tree} && P1C {9036×10240 nnz49620 1/3/10 真消息 finite/maxLLR/residual} && P1D {n12 k3}
assert mother {nnz==49620 && indptr==v72p0_indptr && indices==v72p0_indices && rank9036 && zero0 && dup0 && checkpoint 160,288,416,8992,9032,9036 disclosed}
assert SoftJointConfig 8字段 {checkpoint_rows, max_iter_per_checkpoint, max_total_iterations, llr_clip, convergence_tol, warm_start, dtype, tag_bits} 多一少一即 FAIL
assert 11数组 {prior,extrinsic[10],factor_to_bit,variable_to_check,variable_to_check,check_to_variable,app_llr,syndrome_target,syndrome,app_llr} 已定义
```

## 4. 输入合同 — 严格复用 V56 权威算法（仅新增 adapter 最小接口，精确复用 mother）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | Q/N/Nbit | 1024 / 1024 / 10240 |
| 2 | bin/pairing/rule | `nearest legacy_v1` synthetic |
| 3 | col | `sym*10+bit` |
| 4 | bit展开 | `bit_i(s)=(s>>i)&1` |
| 5 | LF 去self 11数组 | `Σ_{j≠i} bits_j·llr_j logsumexp` `LLR_{→i}` 公式 |
| 6 | mother 精确复用 | `9036×10240 sparse CSR IRA dual-diagonal nnz=49620 indptr/indices相等` 删新 seed |
| 7 | Rs_Δ | `r0 160 Δ8 max9036 r∈{160,168,...,9032,9036}` |
| 8 | checkpoint | `r_checkpoint∈{160,288,...,8992,9032,9036} 72批量 max9036 报告disclosed=r+64` |
| 9 | tag | `SHA256 LE 64b exact` |
| 10 | adapter 11数组 | `pack / syndrome / tag / prefix / incremental` 11数组 |
| 11 | 10步 S1-S10 | `S1 bits → S2 prior → S3 LF 11数组 → S4 pack → S5 mother Δ8 vs checkpoint → S6 syndrome → S7 leak disclosed → S8 tag → S9 11数组 memory → S10 5-state first-match` |

## 5. 估计器 — 10 步 S1-S10 + 3 类型 SoftJointConfig 8字段 + 11数组 + P1A/B/C/D + 11数组 memory（SYNTHETIC_ONLY，精确复用 V72P0 mother，不启 V72）

### 5.1 3 类型定义（最小 adapter，Config 8字段冻结）

```python
@dataclass(frozen=True)
class AdapterConfig:
    Q: int = 1024
    N: int = 1024
    Nbit: int = 10240
    M: int = 9036
    r0: int = 160
    delta: int = 8          # Δ8 增量粒度
    max_r: int = 9036       # max上限
    f: float = 1.3
    tag_bits: int = 64
    col: str = "sym*10+bit" # bit_i(s)=(s>>i)&1  第8字段精确冻结
    # 8字段精确冻结，多一少一即 FAIL；seedMother/used_2m/successor/f_actual 不在 Config，在 registry/manifest

@dataclass(frozen=True)
class AdapterResult:
    T_LF01_08: dict  # 8 tests PASS/FAIL per 1e-12/1e-9
    P1A: dict        # {pack_ok, prefix_ok indptr/indices相等, incremental_ok, tag_ok, deterministic_ok, wall}
    P1B: dict        # {k2_n6_64: {c1..c7, worst, wall}, k3_n9_512: {...}, overall P1B_PASS}
    P1C: dict        # {iter1 {wall,peak,finite,maxLLR,residual,edges,CSR,syndrome_inc,tag,disclosed}, iter3 {...}, iter10 {...}, C1_C6, checkpoint, P1C_PASS}
    P1D: dict        # {n12_k3_loopy: {syndrome_ok, tag_ok, cycle_count, BP_residual, capacity_warning}}
    edges: dict      # {nnz=49620 精确, row_deg_min/max/mean, col_deg_min/max/mean, zero_cols, dup, indptr_equal, indices_equal}
    memory: dict     # {CSR_bytes, 11数组分项 {prior_logp 8192B, bit_to_factor 80KB, factor_to_bit 80KB, variable_to_check 80KB, variable_to_check 387KB, check_to_variable 387KB, app_llr 80KB, syndrome_target 70KB, syndrome 9KB, app_llr 80KB + factor_workspace 720*8=5760B}, total_11array≈9.2MiB, peak_MiB}
    classification: str  # 5-state first-match
    overall: str     # ADAPTER_PLAN_READY / NOT_READY

class Adapter:  # 纯函数接口（ponytail: 仅 pack/syndrome/tag/prefix，无状态）
    def pack(self, extrinsic_10x1024) -> factor_to_bit_10240: ...  # col sym*10+bit 双射 11数组打包
    def syndrome(self, bits_10240, H_r) -> syndrome_observed: ...  # H_r·b mod2 sparse 精确复用 mother
    def tag(self, bits_10240) -> tag64: ...                 # SHA256 LE exact
    def prefix(self, H_mother, r) -> H_r: ...               # H_r = H_mother[0:r] indptr/indices相等校验
    def incremental(self, s_r, s_r8, new_rows): bool: ...   # s_{r+8} == s_r ∪ new8 异或一致 Δ8
```

### 5.2 5公式（R72P1-02，SYNTHETIC_ONLY，枚举 1024，log-domain，稀疏模 2）

> **R72P1-02 5公式**（精确定义，复杂度 `O(nnz+N*Q*10)` 来源）：

| # | 数组名 | 形状 | dtype | 公式/语义 |
|---|---|---|---|---|
| 1 | `prior_logp` | `[1024,1024]` | float64 | `prior_logp[s,q]=log(1/1024)` 均匀先验 SYNTHETIC_ONLY |
| 2 | `bit_to_factor` | `[N,10]` | float64 | `bit_to_factor[n][i]=logsumexp_{bit_i=1} Σ_{j≠i} - logsumexp_{bit_i=0}` 去self 11数组核心 `i=0..9` |
| 3 | `factor_to_bit` | `[N,10]` | float64 | `factor_to_bit[n][i]` 打包后因子→比特 |
| 4 | `variable_to_check` | `[nnz]` | float64 | 变量→校验 消息 `v2c[e]` |
| 5 | `check_to_variable` | `[nnz]` | float64 | 校验→变量 消息 `c2v[e]=2*atanh(Π tanh(v2c/2))` |
| 6 | `app_llr` | `[Nbit]` | float64 | APP `app_llr[v]= Σ c2v + prior` 报告 `finite/maxLLR` |
| 7 | `hard_bits` | `[Nbit]` | uint8 | 硬判决 `hard_bits=(app_llr>0)` |
| 8 | `hard_symbols` | `[N]` | uint16 | 硬判决符号 `hard_symbols[sym]= Σ bit*2^i` |
| 9 | `syndrome_target` | `[active_rows]` | uint8 | 目标校验子 `s_target=H_r·b mod2` |
| 10 | `syndrome_observed` | `[active_rows]` | uint8 | 观测校验子 `s_obs=H_r·hard_bits mod2` |
| 11 | `factor_workspace` | `[Q]` | float64 | 因子工作区 `Q=1024` streaming |

- `O(nnz+N*Q*10)` 来源：`N*Q*10 = 1024*1024*10 = 10,485,760` 为 `bit_to_factor` 11数组枚举 `1024态×10bit`，`nnz=49620` 为稀疏消息 `variable_to_check/c2v` 每 iter 遍历；`ponytail: 11数组 float 已显式，per-account packs if throughput matters 升级路径已标`。

### 5.3 10 步 S1-S10 数据流（SYNTHETIC_ONLY，枚举 1024，log-domain，稀疏模 2，精确复用 mother）

```
S1 synthetic_bits: b[10240] ∈ {0,1}^{10240}, 合成种子0 deterministic，每 case 独立
    # P1A/B 固定 tiny bits；P1C 固定 synthetic_bits 10240 随机种子0；P1D n12 k3 12bits

S2 prior: prior_logp[1024,1024], factor_workspace[Q], syndrome_observed[active_rows], hard_symbols[N], hard_bits[Nbit] = log P(a|b) synthetic（均匀 log(1/1024) 或固定 λ*，SYNTHETIC_ONLY）
    # 不读 2M，仅 dummy prior 用于 LF 去self 校验，对应 11数组 #1

S3 local_factor 去self: LLR_{→i} = logsumexp_{s:bit_i=1} Σ_{j≠i} bits_j·llr_j  -  logsumexp_{s:bit_i=0} Σ_{j≠i}
    # T_LF01-08: 01 completeness / 02 normalization 1e-12 / 03 marginal 1e-12 / 04 delta 1e-9
    #           / 05 self_exclusion 1e-12 / 06 stability K1e6 isfinite / 07 determinism==0 / 08 brute 1e-12
    # logsumexp 用 numpy.logaddexp.reduce 手写，无 numba，生成 bit_to_factor[N,10] 11数组 #2

S4 extrinsic 打包: factor_to_bit[N,10] where factor_to_bit[sym*10+bit] = extrinsic[bit][sym]
    # 双射校验: ∀sym ∀bit factor_to_bit[sym*10+bit] 的逆映射回 sym/bit 无丢，且 S3 的 LLR_out 与打包一致，对应 #3

S5 mother 前缀: H_mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036 nnz=49620 精确复用 V72P0 indptr/indices相等
    # 精确复用 V72P0 mother，不生成新 mother；校验 indptr/indices byte-equal；Δ8 粒度 r∈{160,168,...,9032,9036} 前缀嵌套
    # checkpoint 72批量 r_checkpoint∈{160,288,...,8992,9032,9036} 为真解码触发点，max9036 上限

S6 增量 syndrome: s_r = H_r · b mod2 (sparse 按行异或) 对应 #9
    # 增量一致性: s_{r+8} == s_r || (H_{r:r+8}·b mod2)，即 s_{r+8}[0:r]=s_r 且新增 8 行独立 Δ8粒度
    # 瞄点: checkpoint 160,288,416,9036 必验（72批量）

S7 披露计费: leak_r = r·1 +64 bits (binary 符号 1 bit/行 +64 tag), f=1.3 frozen f_actual NOT_MEASURED disclosed=r_checkpoint+64
    # 报告disclosed 于 checkpoint 上，max9036 上限，仅 A6 disclosure 轻量对照参照，不入硬门禁，但落盘 leak_r 与 required(若有) 对比

S8 exact tag: tag = SHA256(b.tobytes())[:8B] LE 对应 syndrome/tag
    # LE exact: tag == int.from_bytes(SHA256(b"bits")[:8], 'little')，verify tag==SHA256(s_hat)[:8B] 在合成成功时
    # 64 samples exact 校验 (C6)

S9 边/内存/复杂度 11数组分项 float:
    # edges: nnz = H_mother.nnz =49620 精确值（无容差），row_deg = H_mother.getnnz(axis=1) min>0 max≤6, col_deg 分布, zero_cols 0 dup 0, indptr/indices相等
    # memory: CSR_bytes = nnz*4 (indices) + (M+1)*4 (indptr) + nnz*1 (data uint8) =49620*4+9037*4+49620*1≈284KB (229KB indices+indptr+49KB data)，11数组分项见 §5.7，peak_MiB 用 tracemalloc/resource 估 ≤2048MiB
    # complexity: per adapter call O(nnz) syndrome + O(N*Q*10) LF (N*Q*10=10,485,760 1024态枚举 10bit + 稀疏模2 nnz)，P1C 真消息 10 iter wall 取 median 3 次 对应 11数组更新
    # ponytail: O(nnz + N*Q*10) 复杂度足够，per-account locks if throughput matters 升级路径已标

S10 5 态分流 first-match: 见 §7，每 case first-match 优先级互斥 AND gate 精确，overall 需全部 case ADAPTER_PLAN_READY
```

- ponytail: `numpy` 向量化枚举 1024 + `scipy.sparse.csr_matrix` 模 2 异或手写 精确复用 V72P0 mother；`K=1e6` 的 `exp` 溢出需 log域运算，报告显式 log域实现；`# ponytail: O(nnz + N*Q*10) 复杂度足够，per-account locks if throughput matters 升级路径已标`。

### 5.4 P1A plumbing — 确定性与前缀增量 tag（精确复用 mother）

```
P1A probes (SYNTHETIC_ONLY, deterministic seed0, 精确复用 V72P0 mother nnz49620):
  - pack_determinism: adapter.pack 同输入二次 max|Δ|==0 (11数组打包双射)
  - prefix_nested: ∀r ∈ checkpoint {160,288,416,9036} H_r == H_mother[0:r] (sparse 行切片全等 indptr/indices相等)
  - incremental: s_{r+8} == s_r ∪ new8 异或一致 (逐行 mod2 验证 Δ8粒度)
  - tag_exact: tag == SHA256(b)[:8B] LE 且 64 samples 全 exact
  - indptr_indices_equal: H_mother.indptr==v72p0_indptr && H_mother.indices==v72p0_indices byte-equal
  - wall≤30s peak≤2048MiB
P1A_PASS = all 6 true
```

### 5.5 P1B tiny 端到端 — k2/3 n6/9 64/512 各8 trials tree-only 1e-9

```
configs: (k=2,n=6)→total_bits 6 exhaustive 64 (k=3,n=9)→total_bits 9 exhaustive 512 各8 trials 种子0..7
  H_small tree forest (each var degree 1 无环) → BP exact 保证可用 brute 对照，11数组 tiny 缩放版（N_small*Q_small*10）
  per trial:
    c1 isfinite: 所有11数组 isfinite（含 variable_to_check/c2v/app_llr/app_llr finite）
    c2 brute exists isfinite: 穷举 64/512 态 posterior 存在且 isfinite
    c3 observed_zero&&observed_one: observed_zero=any(s==0) observed_one=any(s!=0) 的 c3=observed_zero && observed_one fail-closed（含负向测试：observed_one==false ⇒ c3 false 且数值不变）
    c4 brute exists: brute posterior 存在
    c5 exact posterior max|Δ|<1e-9 tree-only (BP-marg vs brute log-weights)
    c6 tree: H_small 无环校验
    c7 total≤9 exhaustive: 总比特≤9 可穷举
  P1B_PASS = ∀trials ∀m (k2,n6)/(k3,n9) c1..c7 全 true ∧ c3_obs true ∧ worst<1e-9 ∧ wall≤30s
  附加: tiny 经 adapter 的 syndrome+tag exact (S6/S8) 亦需 PASS，落盘 worst/wall/c3_observed + 11数组 finite
```

### 5.6 P1C 真消息传递 1/3/10 iter — 9036×10240 精确复用 mother 真迭代 报告finite/maxLLR/residual

```
H_mother 9036×10240 sparse CSR IRA dual-diagonal nnz=49620 精确复用 indptr/indices相等 C1-C6 re-validate (复用 V72P0 F2/F3):
  C1 rank9036 (H_p det1 ⇒ rank9036，info 3-4 列不降秩)
  C2 row_min>0
  C3 dup0 (行间不重复，hash 校验)
  C4 prefix_nested (H_r == H_mother[0:r] ∀r indptr/indices相等)
  C5 incremental (s_{r+8} 异或一致 Δ8)
  C6 tag64 exact (64 samples SHA256 LE exact)
  checkpoint 160,288,416,8992,9032,9036 72批量 max9036 报告disclosed=r+64

P1C 真消息传递 3 档 (SYNTHETIC_ONLY，真消息传递，非空 smoke，不判收敛)：
  for iter in [1,3,10]:
    # 真迭代：更新 11数组 variable_to_check/check_to_variable/app_llr/syndrome_target/app_llr 逐 iter
    wall_s, peak_MiB, finite, maxLLR, residual, edges(nnz/row_deg/col_deg), CSR_bytes, 11数组 memory 分项, syndrome_inc_ok, tag_ok, disclosed = true_message_passing(H_mother, synthetic_bits 10240, iter)
    # finite= all(isfinite(variable_to_check) && isfinite(check_to_variable) && isfinite(app_llr) && isfinite(app_llr))
    # maxLLR= max|app_llr| 报告
    # residual= max|check_to_variable_new - check_to_variable_old|_∞ 报告
  阈: 1 iter wall<1s && 3 iter <5s && 10 iter ≤30s && finite==true && peak≤2048MiB (任一超限或 non-finite → MATRIX_SMOKE_FAIL)
  P1C_PASS = C1-C6全PASS && checkpoint全PASS && 1/3/10三档 wall/peak/finite/maxLLR/residual/增量/tag/disclosed 全PASS（finite 必须 true，maxLLR/residual 报告值）
  落盘 per iter {wall_s, peak_MiB, finite, maxLLR, residual, per_invocation_ns, nnz=49620, row_deg, col_deg, CSR_bytes, 11数组分项, syndrome_inc_ok, tag_ok, disclosed}
```

### 5.7 P1D small loopy — n12 k3 含单环描述性

```
P1D: n=12 k=3 total_bits 12 (非 exhaustive，采 8 trials 随机种子0..7，图含单环非 tree)
  H_small_loopy 含环 (1 cycle) → BP 非 exact 仅描述性，11数组 loopy 版
  per trial 验证:
    syndrome_ok: s = H_loopy·b mod2 与直接异或一致
    tag_ok: SHA256(b)[:8B] LE exact
    cycle_count: 检测环数 1 (networkx 或手写 DFS 计数)
    BP_residual: BP 后残差 max|Δ|（描述性，不判 1e-9，报告 finite/maxLLR/residual）
  P1D_descriptive = {syndrome_ok, tag_ok, cycle_count, BP_residual, finite, maxLLR, wall}
  capacity_warning: 若 cycle_count>0 或 BP_residual>1e-9 则正交旗标 true，仅描述不过硬门禁
  # ponytail: O(n·k) 环检测足够，精确环枚举 if loopy throughput matters 升级路径已标
```

### 5.8 边/内存/复杂度 11数组分项 float 复杂度探针（落盘，R72P1-06）

```
edges:
  nnz = H_mother.nnz = 49620 精确值（无1 pct容差容差，精确复用 V72P0 indptr/indices相等）
  row_deg = H_mother.getnnz(axis=1) → min>0, max≤6, mean≈5.5
  col_deg = H_mother.getnnz(axis=0) → min≥0, max≤? , zero_cols==0
  dup ==0 (行 hash 去重)
  indptr_equal == true && indices_equal == true (byte-equal)

memory 11数组分项 float64 (R72P1-06):
  CSR_bytes = nnz*4 (indices int32) + (M+1)*4 (indptr int32) + nnz*1 (data uint8) = 49620*4 + 9037*4 + 49620*1 = 198480+36148+49620=284248B≈278192B (indices+indptr 234KB + data 48192B)
  11数组分项 float:
    1 prior: 1024*8=8192B 8192B
    2 bit_to_factor 10×1024: 10240*8=81920B 80KB
    3 factor_to_bit 10240: 80KB
    4 variable_to_check 10240: 80KB
    5 variable_to_check nnz: 49620*8=396960B ≈388192B
    6 check_to_variable nnz: 388192B
    7 app_llr 10240: 80KB
    8 syndrome_target 9036: 9036*8=72288B ≈71KB
    9 syndrome 9036: 9036*1≈9KB (uint8)
    10 app_llr 10240: 80KB
  total_11array_float ≈ 9.2MiB (1.2MB) + CSR 278192B = ~9.2MiB workspace streaming 双向 edge 峰值 <2GiB
  peak_MiB = tracemalloc.get_traced_memory()[1] / 2**20  或 resource.getrusage, ≤2048MiB

complexity (ponytail: O(nnz + N*Q*10) 已显式):
  per adapter syndrome O(nnz) (49620 异或)
  per LF 1024态枚举 11数组 O(N*Q*10) = 1024*1024*10 = 10,485,760 logsumexp 操作
  total per iter O(nnz + N*Q*10) = O(49620 + 10,485,760) ≈ O(10.5M) 浮点 logadd
  P1C 10 iter 真消息 wall median 3 次取 median，per_invocation_ns = wall*1e9 / calls (calls=1024 固定)
  # ponytail: O(nnz + N*Q*10) 11数组 已显式，per-account packs if throughput matters 升级路径已标
```

## 6. 分流判定（per-case 5 终端 first-match AND + 总体 2 态，SYNTHETIC_ONLY 精确复用 mother 不启 V72）

### 6.1 Per-case 5 终端 first-match（优先级高→低，互斥，R72P1-07 AND gate 精确）

```
if not synthetic_bits_ok or not prior_logp_finite or not H_mother_exists or not indptr_indices_equal:
    classification = EVIDENCE_INCOMPLETE; successor = recollect
elif not T_LF01_02_PASS:  # T_LF01 completeness / T_LF02 normalization 1e-12
    classification = KERNEL_FAIL; successor = v72p1_kernel_fix
elif not P1A_PASS or not P1B_PASS:  # P1A plumbing 任一 FAIL（含 indptr/indices 不等）或 P1B tiny 64/512 c3观测/1e-9/wall FAIL
    classification = PLUMBING_TINY_FAIL; successor = v72p1_plumbing_tiny_fix
elif not P0B_revalidate_PASS or not P1C_PASS:  # C1-C6/checkpoint FAIL 或 1/3/10 真消息 finite/maxLLR/residual/wall/peak/增量/tag FAIL
    classification = MATRIX_SMOKE_FAIL; successor = v72p1_matrix_smoke_fix
elif T_LF01_08_PASS and P1A_PASS and P1B_PASS and P1C_PASS and wall≤30 and peak≤2048 and finite==true:
    classification = ADAPTER_PLAN_READY; successor = v72p1_adapter_integration  # 需 4 硬 AND 全 PASS，P1D 仅描述，AND gate 精确（非 OR SYM）
else:
    classification = MATRIX_SMOKE_FAIL  # 兜底 first-match
# P1D loopy 仅 capacity_warning 正交旗标，不过硬门禁，但报告单独章节；无 OR SYM，AND gate 精确；无 1 pct容差容差
```

- **阈值冻结**：`T_LF01-08 1e-12/1e-9`、`P1B worst<1e-9`、`P1C 1 iter<1s 3 iter<5s 10 iter≤30s finite==true peak≤2048`、`C1-C6 + checkpoint 160,288,416,8992,9032,9036 disclosed`、`c3 observed_zero&&observed_one`、`nnz=49620 精确`。

### 6.2 总体 2 态

```
case_count = #{cases | ADAPTER_PLAN_READY}  # cases = P1A + P1B(16 trials) + P1C(3 iters) 聚合为单 case 判定
smoke_counts = {EVIDENCE/KERNEL/PLUMBING_TINY/MATRIX_SMOKE/ADAPTER_PLAN_READY: n}
if all cases ADAPTER_PLAN_READY and smoke_counts[ADAPTER_PLAN_READY]==total_cases:
    overall = ADAPTER_PLAN_READY
else:
    overall = NOT_READY
# audit = {per_case_classification[total], overall, 5 counts, per_case P1A/P1B/P1C/P1D, edges nnz49620 indptr/indices相等, memory 11数组, wall, finite/maxLLR/residual, f1.3 NOT_MEASURED, P1D capacity_warning}
```

- 总体不设 `FAIL`，即便 `PLUMBING_TINY/MATRIX_SMOKE` 亦 `COMPLETE`（地图完成，结论为需修复）；`P1D loopy` 的 `capacity_warning` 正交，仅描述。
- 报告需附 `counts_per_classification (5 终端)` 与 `overall 2 态` + `edges/memory10/wall/finite/maxLLR/residual` 审计表。

## 7. 脚本与报告（SYNTHETIC_ONLY 守卫，精确复用 mother，不启 V72，本轮只四工件）

- **本轮只四工件**：`proposal/design/tasks/specs` 四工件修订，不产 `scripts/`，下一轮脚本需满足 `rg "decode" 0 hits`，`rg "V72P1 新seed" 0 hits`，`py_compile PASS`；输出为四工件一致性；`v72p1_data_registry_synthetic.json` 等 registry 为下一轮占位，本轮仅定义。
- **后续脚本 `scripts/v72p1_soft_joint_binary_adapter.py`** (SYNTHETIC_ONLY): `python scripts/v72p1_soft_joint_binary_adapter.py [--out v72p1_results.json]` → `T_LF01-08 → P1A plumbing indptr/indices相等 → P1B tiny 64/512 8trials c3观测负向测试 → P1C 9036×10240 nnz49620 1/3/10 真消息 finite/maxLLR/residual C1-C6 checkpoint → P1D loopy descriptive → 11数组 memory → 5态 first-match AND`，`rg "decode" 0 hits`，`rg "V72P1 新seed" 0 hits`，`rg -i "met|protograph|sc_coupling" 0 hits`，仅 `numpy/pandas/pyarrow/scipy.sparse/hashlib`，`py_compile PASS`；输出 `v72p1_results.json + v72p1_table.{csv,json} + v72p1_manifest.json + V72P1_SYN_REPORT.md` + 控制台 5 态/2 态摘要；校验 `used_2m false`、`f_actual NOT_MEASURED`、`T_LF 1e-12`、`nnz49620 indptr/indices相等`、`11数组`、`O(nnz+N*Q*10)` 。
- **后续脚本 `scripts/v72p1_backend_audit.py`** (read-only): `python scripts/v72p1_backend_audit.py [--out v72p1_audit_report.json]` → `AdapterSoftJointConfig 8字段/AdapterResult/Adapter 3 类型校验 + 10 步 S1-S10 完整性 + 11数组校验 + 5态枚举探针`，`rg "decode" 0 hits`，`rg "\"ADAPTER_PLAN_READY\"" 0 hits`（枚举用 `IntEnum` 比较 `==BackendState.ADAPTER_PLAN_READY`），`py_compile PASS`；输出 `v72p1_audit_report.json + V72P1_BACKEND_AUDIT_REPORT.md`。
- **报告 `V72P1_SYN_REPORT.md`**（下一轮）：`per case T_LF01-08 / P1A plumbing indptr/indices相等 / P1B 64/512 c3_obs worst / P1C 1/3/10 真消息 finite/maxLLR/residual edges/CSR/11数组/wall/disclosed / P1D loopy capacity_warning + overall 2 态 + S1-S10 3 类型8字段 + 11数组 + Δ8 vs checkpoint + 11数组 memory O(nnz+N*Q*10)` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `SYNTHETIC_ONLY used_2m false f1.3 NOT_MEASURED 精确复用 V72P0 mother nnz49620`。
- **报告 `V72P1_BACKEND_AUDIT_REPORT.md`**：`3 类型8字段 / 10 步 / 11数组 / 5态 first-match` 枚举探针结果。
- **守卫**：SYNTHETIC_ONLY 期零 decoder、零业务矩阵构造、每 case 5 终端总体 2 态 first-match AND、**不创建 `run_01`**、精确复用 mother、不比较方法、不调 V72P1 以外码、**不启 V72**、**本轮只四工件**。

## 8. 守卫 R72P1-01~10（SYNTHETIC_ONLY, 精确复用 V72P0 mother, 不构业务矩阵, 不创 run_01, 不改 V70/V72P0, 不启 V72, 10 步+3 类型8字段+11数组+checkpoint）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R72P1-01 | 冻结主体 + 2M 禁 + 精确复用 V72P0 mother + 不启 V72 | `Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 col sym*10+bit LF去self tag64 f1.3 NOT_MEASURED used_2m false successor_v72_not_started && H_mother 9036×10240 nnz=49620 精确 indptr/indices与V72P0 byte-equal && rg "V72P1 新seed" 0 hits && git diff src==0 && git diff ldpc_v5*==0` |
| R72P1-02 | 5公式 | `11数组 {prior_logp[1024,1024], bit_to_factor[N,10], factor_to_bit[N,10], variable_to_check[nnz], variable_to_check[nnz], check_to_variable[nnz], app_llr[Nbit], syndrome_target[active_rows], syndrome_observed, app_llr[Nbit]} 各公式显式 LLR_{→i}=logsumexp_{1}-logsumexp_{0}\|Σ_{j≠i} ` |
| R72P1-03 | Config 8字段冻结 | `AdapterConfig 仅 8字段 {checkpoint_rows, max_iter_per_checkpoint, max_total_iterations, llr_clip, convergence_tol, warm_start, dtype, tag_bits} 精确冻结，多一少一即 FAIL，rg "seedMother" 0 hits 在 Config 定义` |
| R72P1-04 | Δ8与 checkpoint 分离 72批量 9036 max disclosed | `Δ8 增量粒度 r∈{160,168,...,9032,9036} 与 checkpoint {160,288,...,8992,9032,9036} 72批量 max9036 上限 报告disclosed=r+64 分离已显式` |
| R72P1-05 | P1C 真消息传递 1/3/10 iter 9036×10240 finite/maxLLR/residual | `H_mother 9036×10240 nnz=49620 indptr/indices相等 sparse CSR IRA dual-diagonal rank9036 zero0 dup0 checkpoint disclosed 全 PASS && 1 iter wall<1s finite==true && 3 iter <5s && 10 iter ≤30s && peak≤2048MiB && syndrome增量/tag exact 三档全 PASS 报告 finite/maxLLR/residual` |
| R72P1-06 | 11数组 memory 分项 float 复杂度 O(nnz+N*Q*10) | `nnz=49620 精确 zero0 dup0 CSR≈278192B 11数组≈9.2MiB (prior_logp8192B+bit_to_factor80KB+factor_to_bit80KB+variable_to_check80KB+variable_to_check388192B+check_to_variable388192B+app_llr80KB+syndrome_target71KB+syndrome_observed[active_rows]9KB+app_llr80KB) peak≤2048MiB per_invocation_ns 已落盘 O(nnz+N*Q*10)=O(49620+1024*1024*10) ponytail ceiling 已标，无1 pct容差` |
| R72P1-07 | 5终态 first-match AND gate 精确 | `per-case EVIDENCE>KERNEL>PLUMBING_TINY>MATRIX_SMOKE>ADAPTER_PLAN_READY first-match 互斥 AND gate 精确 (∧ 非 OR SYM) overall ADAPTER_PLAN_READY (all cases READY) / NOT_READY 已落盘 && 5 counts + wall≤30s && finite==true ` |
| R72P1-08 | 机械修正 无1 pct容差 保持未完成 | `AND gate 已修正为 ∧，rg "1 pct容差" 0 hits，rg "旧 nnz" 0 hits，rg "OR SYM" 0 hits，保持 [ ] 未勾选 lifecycle PLAN_CANDIDATE 未完成` |
| R72P1-09 | 本轮只四工件 | `仅 proposal/design/tasks/specs 四工件修订，ls scripts/v72p1_* 不存在，ls v72p1_*.json 不存在` |
| R72P1-10 | SYNTHETIC_ONLY 不构业务矩阵 + 不读 2M/TEST + 不创 run_01 + 不改 V70/V72P0 + 不启 V72 | `rg "decode" 0 hits && rg "TEST" read 0 hits && used_2m==false && used_test==false && ls v72p1_*/run_01 不存在 && py_compile PASS && V72_not_started && git diff V70/V72P0 0 && rg "V72P1 新seed" 0 hits` |

## 9. 与 V64/V67/V70/V71/V72P0/V72 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208` 冻结构及 `22/24 PASS` 已固化；V67 3 sessions 均 `NEAR_FULL` 证 natural 5+5；V69/V70/V71 作对照；V72P0 `合成 correctness P0 壁垒`（`T_LF 8test + P0A tiny + P0B sparse nnz49620 精确复用`）已 `PLAN_CANDIDATE/SYNTHETIC_ONLY`；V72P1 为**最小 adapter 衔接与复杂度地图**（`10 步 S1-S10 + 3 类型8字段 + 11数组 + P1A plumbing / P1B tiny / P1C 真消息 1/3/10 finite/maxLLR/residual / P1D loopy + 11数组 memory O(nnz+N*Q*10) + 5态 first-match AND`），精确复用 V72P0 的 `C1-C6 checkpoint` 校验但独立 `P1A-D` 探针，SYNTHETIC_ONLY 不跑 decoder。
- 若 `V72P1_OVERALL_ADAPTER_PLAN_READY`（全部 case `KERNEL∧P1A∧P1B∧P1C 4硬 AND 全 PASS 且 wall≤30s 且 finite==true`）则 adapter 可零改对接后续 V72 真 mother 的增量 disclosure；若 `PLUMBING_TINY_FAIL` 则需修复打包/去self/小图；若 `MATRIX_SMOKE_FAIL` 则需重构 mother 或降 iter；若 `P1D capacity_warning` 仅描述 loopy 吞吐上限（另起优化）。本变更不创建 `run_01`，**不启动 V72**，任何 V72 真码需另起 `EXECUTE_AUTH`，V72 需独立 `OpenSpec` 且显式用户授权，本轮只四工件。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`Q/N/M/f/tag/col/LF/mother nnz49620 精确复用`），V72P1 仅验证 adapter 衔接与复杂度（SYNTHETIC_ONLY 10 步 + 11数组 + P1A-D 真消息），不启 V72。
- D2 单一估计器 `log_post_excl_i = prior + Σ_{j≠i} - logZ`，adapter 仅为 `sym*10+bit` 打包 + `H_r·b mod2` + `SHA256 LE`，11数组分项 float 支撑 `O(nnz+N*Q*10)`，不改 `s` 本身。
- D3 泄漏 `leak_r = r·1+64` `disclosed=r_checkpoint+64` 不 cap，`f_actual NOT_MEASURED`，仅真消息参照，不入硬门禁，但 checkpoint 72批量 max9036 上限必报告。
- D4 数据 SYNTHETIC_ONLY 合成 bits 确定性种子 0，不搜索多划分，2M/TEST 隔离，V72 不启；P1A-D 各 8 trials / 1/3/10 三档固定批量以控成本，精确复用 mother。
- D5 5 终端 per-case first-match AND + 2 态 overall + T_LF/P1A/B/C/D/11数组 memory/wall/finite/maxLLR/residual 正交审计，不以平均替代，无 1 pct容差。
- D6 不产生新矩阵/码参数，仅 `T_LF/P1A/B/C/D/edges/memory10/wall/5态` 与 successor 建议，`ADAPTER_PLAN_READY 4硬 AND` 方可零改对接 V72 mother。
- D7 本变更为 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder/V72 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允，本轮只四工件保持未完成。

# 权威合同校验行 max10 total720 warm_true float64 9.2MiB prefix1111 tail4 checkpoint72 prior_logp[1024,1024] 11数组 5公式 SoftJointConfig 8字段 workspace streaming 双向 edge
