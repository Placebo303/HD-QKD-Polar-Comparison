# OpenSpec Design: formal-ir-v72p1-soft-joint-binary-adapter

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — **最小 adapter 衔接 1024 local factor 自排除 ↔ binary IRA mother 9036×10240 增量 syndrome ↔ exact 64-bit tag，10 步 S1-S10 + 3 类型 Config/Result/Adapter，P1A plumbing / P1B tiny 端到端 64/512 8trials tree-only 1e-9 / P1C full-size 1/3/10 iter smoke 9036×10240 / P1D small loopy 描述性，边/内存/复杂度探针，5 态 2 态，不跑 decoder 不改 V70/V72P0 不启 V72**

**Cycle**: `V72P1-ADP` predecessor `V72P0-SYN 5591e16bf35b03c3df30a003bee12011a796d73e (V72P0 64ca2f1e)` + `V71-SJK e038114db5095a57158b0e1cd36884d6a1a5d8be` + `V70-BSJ 9bc34be6` + `V67-MAP` HEAD `TBD (freeze-time git rev-parse HEAD)` data `84d62779` 单点 `d1024 bw200 nearest legacy_v1` — **SYNTHETIC_ONLY 不读 2M，不创 run_01，不启 V72**

**Feasibility**: `V72P0` 已验证 `去self 8 测试 1e-12/1e-9 + P0A k2/3 n6/9 64/512 8trials c3观测 + P0B sparse CSR IRA 9036×10240 dual-diagonal rank9036 5-state ADAPTER_PLAN_READY (3 passes)`；`V72P1` 假设 **最小 adapter 以纯函数打包/增量 syndrome/exact tag 可无损衔接 local factor 与 mother**（`P1A 确定性 + P1B tiny 端到端 1e-9 + P1C 1/3/10 smoke 边/内存/C1-C6/pivot 全 PASS + P1D loopy 描述性`），则 adapter 可零改对接后续 V72 真 mother，需 SYNTHETIC_ONLY 验证 `S1-S10 + 3 类型 + P1A/B/C/D + 边内存 + 5态` 三重守卫。

**Key judgement**: **在 SYNTHETIC_ONLY 合成 bits（Q=1024 先验枚举 + 10-bit 位展开）上，验证最小 adapter 的 10 步数据流无损衔接**：`S3 去self LF 全零得 marginal delta 得确定值与 brute-force 1e-12` 且 `S4 打包 col sym*10+bit 双射` 且 `S5 母码 prefix 增量` 且 `S6 增量 syndrome 异或一致` 且 `S8 tag LE exact` 且 `S9 边内存估算` 且 `P1B tiny 1e-9 + P1C 1/3/10 smoke wall≤30s`，即判定 `ADAPTER_PLAN_READY`，否则 `PLUMBING_TINY/MATRIX_SMOKE FAIL`。

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 f1.3 NOT_MEASURED tag 64b exact 漏 Σw_i·m_i+64`，**不改 Q/N/M/f/tag/col/去self 语义**）下，**验证最小 adapter 的 10 步无损衔接 + P1A/B/C/D 四层合成 + 边内存复杂度**：定义 `S1 合成 bits → S2 prior → S3 去self LF → S4 extrinsic打包 → S5 mother前缀 → S6 增量syndrome → S7 披露计费 → S8 exact tag → S9 边内存 → S10 5态分流` + `3 类型 AdapterConfig/AdapterResult/Adapter` + `P1A plumbing / P1B tiny 64/512 c3观测 1e-9 / P1C full-size 9036×10240 1/3/10 smoke / P1D small loopy`，每 case 5 终端总体 2 态。全程 SYNTHETIC_ONLY，不跑 decoder，不启 V72。
- **对照**：`V72P0 T_LF/P0A/P0B` 基线作 `KERNEL/P0B re-validate` 对照；`ldpc_v5` 的 `caps/disclosure` 作 `A5/A6` 轻量对照（只读，不执行）；`1/3/10 smoke` 三档作复杂度路由。
- **不变量**：`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 f1.3 tag64 col sym*10+bit 去self Σ_{j≠i}` 全冻结；**本变更仅验证 adapter 衔接与复杂度**。
- **地图性质**：纯 SYNTHETIC_ONLY，`1024 枚举 log-domain + sparse CSR IRA + adapter pack/syndrome/tag + P1A/B/C/D + 边内存`，`2M/TEST` 密封不读，V72P0 复用校验，每 case 5 终端总体 2 态，不启 V72。

## 2. 冻结语义 — 主体与处理点零改（1024维 adapter 不重构）

| 项 | 冻结值 | 来源 |
|---|---|---|
| Q/N/Nbit/M | 1024 / 1024 / 10240 / 9036 | V72P0 |
| f | 1.3 NOT_MEASURED `used_2m false` | V72P0 |
| tag | 64b exact `SHA256(bits)[:8B] LE` | V72P0 |
| col | `sym*10+bit` `bit_i(s)=(s>>i)&1` `i 0..9 LSB→MSB` | V72P0 |
| LF | 去self `LLR_{→i}=logsumexp_{1}-logsumexp_{0} \| Σ_{j≠i}` | V72P0 |
| mother | `H_mother 9036×10240` `n_info 1204` `H_p dual-diagonal det1 rank9036` `info每行3-4` `nnz≈49698` `zero0 dup0` | V72P0 P0B |
| Rs | `r0 160 Δ8 →9036` `pivot 160/168/176/9036` `prefix_nested` | V72P0 |
| leak | `leak_r = r·1 +64` `f_actual NOT_MEASURED` | V27/V31 |
| adapter | `pack / syndrome / tag / prefix / incremental` 纯函数 | V72P1 新增 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` synthetic | V55→V72P1 |
| V72 | **禁止启动** — 任何 V72 预冻结/run_01 禁止 | V72P1 |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_*_business / gf_rank_business / nested_business` 业务码；`SHALL NOT` 调 `Q/N/M/f/tag/col/LF/mother/Rs/leak`；`SHALL NOT` 引 `MET/protograph/SC/Gray`（除 adapter 注释）；`SHALL NOT` 读 2M/TEST；`SHALL NOT` 启动 V72；`SHALL NOT` 执行 `run_ldpc_formal_v5`；`SHALL NOT` 改 `src/`。

## 3. 数据角色 — SYNTHETIC_ONLY 四层 P1A/B/C/D（零重叠，不读 2M）

### 3.1 合成集合与复用

| 集合 | 规模 | 说明 |
|---|---|---|
| P1A plumbing | 4 probes × 1024 态 + 9036 前缀 | `pack / syndrome / tag / prefix_nested / incremental` 确定性 |
| P1B tiny k2 n6 | 64 exhaustive ×8 trials | tree forest, `c3 observed_zero&&observed_one` `c5 1e-9` |
| P1B tiny k3 n9 | 512 exhaustive ×8 trials | 同上 |
| P1C full-size smoke | 9036×10240 CSR 1/3/10 iter | `wall<1s / <5s / ≤30s` `C1-C6 re-validate` `pivot 4` |
| P1D small loopy | n12 k3 total 12 bits ×8 trials | 含单环 descriptively `capacity_warning` |
| P0B re-validate | 9036×10240 sparse CSR | 复用 V72P0 `C1-C6 pivot` 校验 |
| 2M/TEST real | 密封不读 | `used_2m false used_test false` |

- **注册表**：`v72p1_data_registry_synthetic.json` (`schema v72p1_synthetic_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head TBD (freeze-time binding), reused_from v72p0_synthetic_v1, successor_v72_not_started true, frozen {Q1024,N1024,Nbit10240,M9036,r0 160,Δ8,max9036,tag f1.3,col sym*10+bit, seed_mother V72P1-ADP-MOTHER, P1A plumbing, P1B {k2/3 n6/9 64/512 8trials tree-only}, P1C {9036×10240 1/3/10 smoke}, P1D {n12 k3 loopy descriptive}, used_2m false}`)。
- **零改复用**：`V72P0` 的 `P0A/P0B` 仅复用校验，不重估计；`V70/V71` 的 Stage2 仅对照，不作先验来源。

### 3.2 数据就绪门（SYNTHETIC_ONLY）

```
assert Q==1024 && N==1024 && Nbit==10240 && M==9036 && r0==160 && Δ==8 && max==9036
assert f==1.3 && f_actual=="NOT_MEASURED" && used_2m==false && used_test==false
assert successor_v72_not_started==true && head==TBD (freeze-time)
assert P1A {plumbing probes 4} && P1B {64/512 8trials tree} && P1C {9036×10240 1/3/10} && P1D {n12 k3}
assert mother {rank9036 zero0 dup0 pivot 160/168/176/9036}
```

## 4. 输入合同 — 严格复用 V56 权威算法（仅新增 adapter 最小接口）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | Q/N/Nbit | 1024 / 1024 / 10240 |
| 2 | bin/pairing/rule | `nearest legacy_v1` synthetic |
| 3 | col | `sym*10+bit` |
| 4 | bit展开 | `bit_i(s)=(s>>i)&1` |
| 5 | LF 去self | `Σ_{j≠i} bits_j·llr_j logsumexp` |
| 6 | mother | `9036×10240 sparse CSR IRA dual-diagonal` |
| 7 | Rs | `r0 160 Δ8 max9036` |
| 8 | tag | `SHA256 LE 64b exact` |
| 9 | adapter | `pack / syndrome / tag / prefix / incremental` |
| 10 | 10步 S1-S10 | `S1 bits → S2 prior → S3 LF → S4 pack → S5 mother → S6 syndrome → S7 leak → S8 tag → S9 edge/memory → S10 5-state` |

## 5. 估计器 — 10 步 S1-S10 + 3 类型 + P1A/B/C/D + 边内存（SYNTHETIC_ONLY，不启 V72）

### 5.1 3 类型定义（最小 adapter）

```python
@dataclass(frozen=True)
class AdapterConfig:
    Q: int = 1024; N: int = 1024; Nbit: int = 10240; M: int = 9036
    r0: int = 160; delta: int = 8; max_r: int = 9036
    f: float = 1.3; f_actual: str = "NOT_MEASURED"
    tag_bits: int = 64; col: str = "sym*10+bit"
    seed_mother: str = "V72P1-ADP-MOTHER"  # SeedSequence 派生
    used_2m: bool = False; successor_v72_not_started: bool = True

@dataclass(frozen=True)
class AdapterResult:
    T_LF01_08: dict  # 8 tests PASS/FAIL per 1e-12/1e-9
    P1A: dict        # {pack_ok, prefix_ok, incremental_ok, tag_ok, deterministic_ok, wall}
    P1B: dict        # {k2_n6_64: {c1..c7, worst, wall}, k3_n9_512: {...}, overall P1B_PASS}
    P1C: dict        # {iter1 {wall,peak,edges,CSR,syndrome_inc,tag}, iter3 {...}, iter10 {...}, C1_C6, pivot, P1C_PASS}
    P1D: dict        # {n12_k3_loopy: {syndrome_ok, tag_ok, cycle_count, BP_residual, capacity_warning}}
    edges: dict      # {nnz, row_deg_min/max/mean, col_deg_min/max/mean, zero_cols, dup}
    memory: dict     # {CSR_bytes, indptr_bytes, LLR_bytes, peak_MiB}
    classification: str  # 5-state
    overall: str     # ADAPTER_PLAN_READY / NOT_READY

class Adapter:  # 纯函数接口（ponytail: 仅 pack/syndrome/tag/prefix，无状态）
    def pack(self, extrinsic_10x1024) -> bit_llr_10240: ...  # col sym*10+bit 双射
    def syndrome(self, bits_10240, H_r) -> syndrome_r: ...  # H_r·b mod2 sparse
    def tag(self, bits_10240) -> tag64: ...                 # SHA256 LE exact
    def prefix(self, H_mother, r) -> H_r: ...               # H_r = H_mother[0:r]
    def incremental(self, s_r, s_r8, new_rows): bool: ...   # s_{r+8} == s_r ∪ new8 异或一致
```

### 5.2 10 步 S1-S10 数据流（SYNTHETIC_ONLY，枚举 1024，log-domain，稀疏模 2）

```
S1 synthetic_bits: b[10240] ∈ {0,1}^{10240}, 合成种子0 deterministic，每 case 独立
    # P1A/B 固定 tiny bits；P1C 固定 synthetic_bits 10240 随机种子0；P1D n12 k3 12bits

S2 prior: log_prior[1024] = log P(a|b) synthetic（均匀 log(1/1024) 或固定 λ*，SYNTHETIC_ONLY）
    # 不读 2M，仅 dummy prior 用于 LF 去self 校验

S3 local_factor 去self: LLR_{→i} = logsumexp_{s:bit_i=1} Σ_{j≠i} bits_j·llr_j  -  logsumexp_{s:bit_i=0} Σ_{j≠i}
    # T_LF01-08: 01 completeness / 02 normalization 1e-12 / 03 marginal 1e-12 / 04 delta 1e-9
    #           / 05 self_exclusion 1e-12 / 06 stability K1e6 isfinite / 07 determinism==0 / 08 brute 1e-12
    # logsumexp 用 numpy.logaddexp.reduce 手写，无 numba

S4 extrinsic 打包: bit_llr[10240] where bit_llr[sym*10+bit] = extrinsic[bit][sym]
    # 双射校验: ∀sym ∀bit bit_llr[sym*10+bit] 的逆映射回 sym/bit 无丢，且 S3 的 LLR_out 与打包一致

S5 mother 前缀: H_mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036
    # SeedSequence "V72P1-ADP-MOTHER" 生成 info 每行3-4 列 + H_p dual-diagonal (diag+subdiag)
    # H_r = H_mother[0:r] for r in Rs = {160,168,...,9036} 前缀嵌套

S6 增量 syndrome: s_r = H_r · b mod2 (sparse 按行异或)
    # 增量一致性: s_{r+8} == s_r || (H_{r:r+8}·b mod2)，即 s_{r+8}[0:r]=s_r 且新增 8 行独立
    # 瞄点: r=160,168,176,9036 必验

S7 披露计费: leak_r = r·1 +64 bits (binary 符号 1 bit/行 +64 tag), f=1.3 frozen f_actual NOT_MEASURED
    # 仅 A6 disclosure 轻量对照参照，不入硬门禁，但落盘 leak_r 与 required(若有) 对比

S8 exact tag: tag = SHA256(b.tobytes())[:8B] LE
    # LE exact: tag == int.from_bytes(SHA256(b"bits")[:8], 'little')，verify tag==SHA256(s_hat)[:8B] 在合成成功时
    # 64 samples exact 校验 (C6)

S9 边/内存/复杂度估算:
    # edges: nnz = H_mother.nnz ≈ 9036*5.5 ≈49698 (±1%容差)，row_deg = H_mother.getnnz(axis=1) min>0 max≤6, col_deg 分布, zero_cols 0 dup 0
    # memory: CSR_bytes = nnz*4 (indices) + (M+1)*4 (indptr) + nnz*1 (data uint8) ≈235KB，LLR_bytes=10240*8≈80KB，peak_MiB 用 tracemalloc/resource 估 ≤2048MiB
    # complexity: per adapter call O(nnz) syndrome + O(Q·1024) LF (Q=1024 枚举 1024·10)，P1C 10 iter smoke 的 wall 取 median 3 次

S10 5 态分流: 见 §7，每 case first-match 优先级互斥，overall 需全部 case ADAPTER_PLAN_READY
```

- ponytail: `numpy` 向量化枚举 1024 + `scipy.sparse.csr_matrix` 模 2 异或手写；`K=1e6` 的 `exp` 溢出需 log域运算，报告显式 log域实现；`# ponytail: O(nnz + Q·1024) 复杂度足够，per-account locks if throughput matters 升级路径已标`。

### 5.3 P1A plumbing — 确定性与前缀增量 tag

```
P1A probes (SYNTHETIC_ONLY, deterministic seed0):
  - pack_determinism: adapter.pack 同输入二次 max|Δ|==0
  - prefix_nested: ∀r ∈ {160,168,176,9036} H_r == H_mother[0:r] (sparse 行切片全等)
  - incremental: s_{r+8} == s_r ∪ new8 异或一致 (逐行 mod2 验证)
  - tag_exact: tag == SHA256(b)[:8B] LE 且 64 samples 全 exact
  - wall≤30s peak≤2048MiB
P1A_PASS = all 5 true
```

### 5.4 P1B tiny 端到端 — k2/3 n6/9 64/512 各8 trials tree-only 1e-9

```
configs: (k=2,n=6)→total_bits 6 exhaustive 64 (k=3,n=9)→total_bits 9 exhaustive 512 各8 trials 种子0..7
  H_small tree forest (each var degree 1 无环) → BP exact 保证可用 brute 对照
  per trial:
    c1 isfinite: 所有消息 isfinite
    c2 brute exists isfinite: 穷举 64/512 态 posterior 存在且 isfinite
    c3 observed_zero&&observed_one: observed_zero=any(s==0) observed_one=any(s!=0) 的 c3=observed_zero && observed_one fail-closed（含负向测试：observed_one==false ⇒ c3 false 且数值不变）
    c4 brute exists: brute posterior 存在
    c5 exact posterior max|Δ|<1e-9 tree-only (BP-marg vs brute log-weights)
    c6 tree: H_small 无环校验
    c7 total≤9 exhaustive: 总比特≤9 可穷举
  P1B_PASS = ∀trials ∀m (k2,n6)/(k3,n9) c1..c7 全 true ∧ c3_obs true ∧ worst<1e-9 ∧ wall≤30s
  附加: tiny 经 adapter 的 syndrome+tag exact (S6/S8) 亦需 PASS，落盘 worst/wall/c3_observed
```

### 5.5 P1C full-size 1/3/10 iter smoke — 9036×10240 未收敛亦 PASS 的复杂度烟雾

```
H_mother 9036×10240 sparse CSR IRA dual-diagonal C1-C6 re-validate (复用 V72P0 F2/F3):
  C1 rank9036 (H_p det1 ⇒ rank9036，info 3-4 列不降秩)
  C2 row_min>0
  C3 dup0 (行间不重复，hash 校验)
  C4 prefix_nested (H_r == H_mother[0:r] ∀r)
  C5 incremental (s_{r+8} 异或一致)
  C6 tag64 exact (64 samples SHA256 LE exact)
  pivot 160/168/176/9036 Rs r0 160 Δ8→9036

P1C smoke 3 档 (SYNTHETIC_ONLY，不判收敛)：
  for iter in [1,3,10]:
    wall_s, peak_MiB, edges(nnz/row_deg/col_deg), CSR_bytes, syndrome_inc_ok, tag_ok = smoke(H_mother, synthetic_bits 10240, iter)
    # smoke 仅跑 1/3/10 次消息迭代，各计 wall/peak，不计 FER/熵；syndrome 增量与 tag exact 仍需 PASS
  阈: 1 iter wall<1s && 3 iter <5s && 10 iter ≤30s && peak≤2048MiB (任一超限 → MATRIX_SMOKE_FAIL)
  P1C_PASS = C1-C6全PASS && pivot4全PASS && 1/3/10三档 wall/peak/增量/tag 全PASS
  落盘 per iter {wall_s, peak_MiB, per_invocation_ns, nnz, row_deg, col_deg, CSR_bytes, syndrome_inc_ok, tag_ok}
```

### 5.6 P1D small loopy — n12 k3 含单环描述性

```
P1D: n=12 k=3 total_bits 12 (非 exhaustive，采 8 trials 随机种子0..7，图含单环非 tree)
  H_small_loopy 含环 (1 cycle) → BP 非 exact 仅描述性
  per trial 验证:
    syndrome_ok: s = H_loopy·b mod2 与直接异或一致
    tag_ok: SHA256(b)[:8B] LE exact
    cycle_count: 检测环数 1 (networkx 或手写 DFS 计数)
    BP_residual: BP 后残差（描述性，不判 1e-9）
  P1D_descriptive = {syndrome_ok, tag_ok, cycle_count, BP_residual, wall}
  capacity_warning: 若 cycle_count>0 或 BP_residual>1e-9 则正交旗标 true，仅描述不过硬门禁
  # ponytail: O(n·k) 环检测足够，精确环枚举 if loopy throughput matters 升级路径已标
```

### 5.7 边/内存/复杂度复杂度探针（估算，落盘）

```
edges:
  nnz = H_mother.nnz  (≈49698, 允许 ±1% 即 49200–50200)
  row_deg = H_mother.getnnz(axis=1) → min>0, max≤6, mean≈5.5
  col_deg = H_mother.getnnz(axis=0) → min≥0, max≤? , zero_cols==0
  dup ==0 (行 hash 去重)

memory:
  CSR_bytes = nnz*4 (indices int32) + (M+1)*4 (indptr) + nnz*1 (data) ≈235KB
  LLR_bytes = Nbit*8 (float64) ≈80KB
  peak_MiB = tracemalloc.get_traced_memory()[1] / 2**20  或 resource.getrusage, ≤2048MiB

complexity (ponytail: O(nnz + Q·1024) 已显式):
  per adapter syndrome O(nnz) (≈5e4 异或)
  per LF 1024态枚举 O(Q·10 + Q log Q) (≈1e4 + logsumexp)
  P1C 10 iter smoke wall median 3 次取 median，per_invocation_ns = wall*1e9 / calls (calls=1024 固定)
```

## 6. 分流判定（per-case 5 终端 + 总体 2 态，SYNTHETIC_ONLY 不启 V72）

### 6.1 Per-case 5 终端 first-match（优先级高→低，互斥）

```
if not synthetic_bits_ok or not log_prior_finite or not H_mother_exists:
    classification = EVIDENCE_INCOMPLETE; successor = recollect
elif not T_LF01_02_PASS:  # T_LF01 completeness / T_LF02 normalization 1e-12
    classification = KERNEL_FAIL; successor = v72p1_kernel_fix
elif not P1A_PASS or not P1B_PASS:  # P1A plumbing 任一 FAIL 或 P1B tiny 64/512 c3观测/1e-9/wall FAIL
    classification = PLUMBING_TINY_FAIL; successor = v72p1_plumbing_tiny_fix
elif not P0B_revalidate_PASS or not P1C_PASS:  # C1-C6/pivot FAIL 或 1/3/10 smoke wall/peak/增量/tag FAIL
    classification = MATRIX_SMOKE_FAIL; successor = v72p1_matrix_smoke_fix
elif T_LF01_08_PASS and P1A_PASS and P1B_PASS and P1C_PASS and wall≤30 and peak≤2048:
    classification = ADAPTER_PLAN_READY; successor = v72p1_adapter_integration  # 需 4 hard PASS，P1D 仅描述
else:
    classification = MATRIX_SMOKE_FAIL  # 兜底
# P1D loopy 仅 capacity_warning 正交旗标，不过硬门禁，但报告单独章节
```

- **阈值冻结**：`T_LF01-08 1e-12/1e-9`、`P1B worst<1e-9`、`P1C 1 iter<1s 3 iter<5s 10 iter≤30s peak≤2048`、`C1-C6 + pivot 4`、`c3 observed_zero&&observed_one`。

### 6.2 总体 2 态

```
case_count = #{cases | ADAPTER_PLAN_READY}  # cases = P1A + P1B(16 trials) + P1C(3 iters) 聚合为单 case 判定
smoke_counts = {EVIDENCE/KERNEL/PLUMBING_TINY/MATRIX_SMOKE/ADAPTER_PLAN_READY: n}
if all cases ADAPTER_PLAN_READY and smoke_counts[ADAPTER_PLAN_READY]==total_cases:
    overall = ADAPTER_PLAN_READY
else:
    overall = NOT_READY
# audit = {per_case_classification[total], overall, 5 counts, per_case P1A/P1B/P1C/P1D, edges, memory, wall, f1.3 NOT_MEASURED, P1D capacity_warning}
```

- 总体不设 `FAIL`，即便 `PLUMBING_TINY/MATRIX_SMOKE` 亦 `COMPLETE`（地图完成，结论为需修复）；`P1D loopy` 的 `capacity_warning` 正交，仅描述。
- 报告需附 `counts_per_classification (5 终端)` 与 `overall 2 态` + `edges/memory/wall` 审计表。

## 7. 脚本与报告（SYNTHETIC_ONLY 守卫，不启 V72）

- **脚本 `scripts/v72p1_soft_joint_binary_adapter.py`** (SYNTHETIC_ONLY): `python scripts/v72p1_soft_joint_binary_adapter.py [--out v72p1_results.json]` → `T_LF01-08 → P1A plumbing deterministic/prefix/incremental/tag → P1B tiny 64/512 8trials c3观测负向测试 → P1C 9036×10240 1/3/10 smoke C1-C6 pivot → P1D loopy descriptive → edges/memory/complexity → 5态2态`，`rg "decode_" 0 hits`，`rg -i "met|protograph|sc_coupling" 0 hits`，`rg -i "v72|qualification" 0 hits`（除 successor 注释），`py_compile PASS`；输出 `v72p1_results.json + v72p1_table.{csv,json} + v72p1_manifest.json + V72P1_SYN_REPORT.md` + 控制台 5 态/2 态摘要；校验 `used_2m false`、`f_actual NOT_MEASURED`、`T_LF 1e-12` 已验。
- **脚本 `scripts/v72p1_backend_audit.py`** (read-only): `python scripts/v72p1_backend_audit.py [--out v72p1_audit_report.json]` → `AdapterConfig/AdapterResult/Adapter 3 类型校验 + 10 步 S1-S10 完整性 + 5态枚举探针`，`rg "decode_" 0 hits`，`rg "\"ADAPTER_PLAN_READY\"" 0 hits`（枚举用 `IntEnum` 比较 `==BackendState.ADAPTER_PLAN_READY`），`py_compile PASS`；输出 `v72p1_audit_report.json + V72P1_BACKEND_AUDIT_REPORT.md`。
- **报告 `V72P1_SYN_REPORT.md`**：`per case T_LF01-08 / P1A plumbing / P1B 64/512 c3_obs worst / P1C 1/3/10 smoke edges/CSR/wall / P1D loopy capacity_warning + overall 2 态 + S1-S10 3 类型 + 10 步数据流 + 边内存复杂度` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `SYNTHETIC_ONLY used_2m false f1.3 NOT_MEASURED`。
- **报告 `V72P1_BACKEND_AUDIT_REPORT.md`**：`3 类型 / 10 步 / 5态` 枚举探针结果。
- **守卫**：SYNTHETIC_ONLY 期零 decoder、零业务矩阵构造、每 case 5 终端总体 2 态、**不创建 `run_01`**、不比较方法、不调 V72P1 以外码、**不启 V72**；**四工件+registry+探针 已单独提交推送，新 Plan SHA 已生成**。

## 8. 守卫 R72P1-01~10（SYNTHETIC_ONLY, 不构业务矩阵, 不创 run_01, 不改 V70/V72P0, 不启 V72, 10 步+3 类型+边内存+1/3/10 smoke）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R72P1-01 | 冻结主体 + 2M 禁 + 10 步 + 3 类型 + 不启 V72 | `Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 col sym*10+bit LF去self tag64 f1.3 NOT_MEASURED used_2m false successor_v72_not_started && S1-S10 10步完整 && AdapterConfig/Result/Adapter 3类型已定义 && git diff src==0 && git diff ldpc_v5*==0 && successor_v72_not_started && rg -i "v72|qualification" 0 hits` |
| R72P1-02 | 去self 8 测试 1e-12/1e-9 | `T_LF01 completeness / T_LF02 normalization 1e-12 / T_LF03 marginal 1e-12 / T_LF04 delta 1e-9 / T_LF05 self_exclusion 1e-12 / T_LF06 stability K1e6 isfinite / T_LF07 determinism==0 / T_LF08 brute 1e-12 正交全 PASS` |
| R72P1-03 | P1A plumbing 确定性前缀增量 tag | `pack deterministic==0 && prefix_nested H_r==H_mother[0:r] ∀r∈{160,168,176,9036} && incremental s_{r+8} 异或一致 && tag LE exact 64 samples && wall≤30s` |
| R72P1-04 | P1B tiny 64/512 c3 观测 1e-9 | `(k2,n6)64 (k3,n9)512 各8trials exhaustive tree forest c1..c7 全 true && c3 observed_zero&&observed_one 负向测试 && c5 worst<1e-9 && wall≤30s && syndrome+tag exact` |
| R72P1-05 | P1C full-size 1/3/10 smoke 9036×10240 C1-C6 pivot | `H_mother 9036×10240 sparse CSR IRA dual-diagonal rank9036 zero0 dup0 前缀增量 tag exact pivot 160/168/176/9036 全 PASS && 1 iter<1s && 3 iter<5s && 10 iter≤30s && peak≤2048MiB && syndrome增量/tag exact 三档全 PASS` |
| R72P1-06 | P1D small loopy 描述性 | `n12 k3 12bits 含单环 cycle_count==1 syndrome_ok tag_ok BP_residual 描述性 capacity_warning 正交旗标已落盘，不入硬门禁` |
| R72P1-07 | 边内存复杂度估算 | `nnz≈49698±1% row_min>0 row_max≤6 zero0 dup0 CSR_bytes≈235KB LLR≈80KB peak≤2048MiB per_invocation_ns 已落盘 O(nnz+Q·1024) ponytail ceiling 已标` |
| R72P1-08 | per-case 5 终端总体 2 态 wall | `per-case EVIDENCE>KERNEL>PLUMBING_TINY>MATRIX_SMOKE>ADAPTER_PLAN_READY 互斥 && overall ADAPTER_PLAN_READY (all cases READY) / NOT_READY 已落盘 && 5 counts + wall≤30s 已验` |
| R72P1-09 | 四工件+双报告完整 | `v72p1_data_registry + v72p1_results + v72p1_table.csv/json行对等 + V72P1_SYN_REPORT + V72P1_BACKEND_AUDIT_REPORT + v72p1_audit_report.json + test_v72p1_small.py py_compile+pytest PASS` |
| R72P1-10 | SYNTHETIC_ONLY 不构业务矩阵 + 不读 2M/TEST + 不创 run_01 + 不改 V70/V72P0 + 不启 V72 | `rg "decode_" 0 hits && rg "TEST" read 0 hits && used_2m==false && used_test==false && ls v72p1_*/run_01 不存在 && py_compile PASS && V72_not_started && git diff V70/V72P0 0` |

## 9. 与 V64/V67/V70/V71/V72P0/V72 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208` 冻结构及 `22/24 PASS` 已固化；V67 3 sessions 均 `NEAR_FULL` 证 natural 5+5；V69/V70/V71 作对照；V72P0 `合成 correctness P0 壁垒`（`T_LF 8test + P0A tiny + P0B sparse`）已 `PLAN_CANDIDATE/SYNTHETIC_ONLY`；V72P1 为**最小 adapter 衔接与复杂度地图**（`10 步 S1-S10 + 3 类型 + P1A plumbing / P1B tiny / P1C 1/3/10 smoke / P1D loopy + 边内存`），复用 V72P0 的 `C1-C6 pivot` 校验但独立 `P1A-D` 探针，SYNTHETIC_ONLY 不跑 decoder。
- 若 `V72P1_OVERALL_ADAPTER_PLAN_READY`（全部 case `KERNEL∧P1A∧P1B∧P1C` 全 PASS 且 `wall≤30s`）则 adapter 可零改对接后续 V72 真 mother 的增量 disclosure；若 `PLUMBING_TINY_FAIL` 则需修复打包/去self/小图；若 `MATRIX_SMOKE_FAIL` 则需重构 mother 或降 iter；若 `P1D capacity_warning` 仅描述 loopy 吞吐上限（另起优化）。本变更不创建 `run_01`，**不启动 V72**，任何 V72 真码需另起 `EXECUTE_AUTH`，V72 需独立 `OpenSpec` 且显式用户授权。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`Q/N/M/f/tag/col/LF/mother/Rs`），V72P1 仅验证 adapter 衔接与复杂度（SYNTHETIC_ONLY 10 步 + P1A-D），不启 V72。
- D2 单一估计器 `log_post_excl_i = log_prior + Σ_{j≠i} - logZ`，adapter 仅为 `sym*10+bit` 打包 + `H_r·b mod2` + `SHA256 LE`，不改 `s` 本身。
- D3 泄漏 `leak_r = r·1+64` 不 cap，`f_actual NOT_MEASURED`，仅 smoke 参照，不入硬门禁。
- D4 数据 SYNTHETIC_ONLY 合成 bits 确定性种子 0，不搜索多划分，2M/TEST 隔离，V72 不启；P1A-D 各 8 trials / 1/3/10 三档固定批量以控成本。
- D5 5 终端 per-case + 2 态 overall + T_LF/P1A/B/C/D/边内存/wall 正交审计，不以平均替代。
- D6 不产生新矩阵/码参数，仅 `T_LF/P1A/B/C/D/edges/memory/wall/5态` 与 successor 建议，`ADAPTER_PLAN_READY` 方可零改对接 V72 mother。
- D7 本变更为 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder/V72 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允。
