# OpenSpec Proposal: formal-ir-v72p1-soft-joint-binary-adapter

**Status**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal IR / soft-joint binary adapter (V72P0 synthetic successor)
**Change ID**: `formal-ir-v72p1-soft-joint-binary-adapter`
**Cycle ID**: `V72P1-ADP` predecessor `V72P0-SYN (5591e16bf35b03c3df30a003bee12011a796d73e)` + `V71-SJK` + `V70-BSJ`
**Branch**: `formal-ir-mainline`
**Implementation**: `TBD (git rev-parse HEAD on freeze; EXTERNAL_BINDING until Pre-RESULT)` 
**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1` synthetic only, `used_2m false`)
**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + 合成 adapter 复杂度探针 + P1A/B/C/D 四层 synthetic，不跑 decoder，不创 `run_01`，不改 V72P0，不启 V72

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 合成探针 (`numpy` 1024 log-domain + `scipy.sparse CSR` 精确复用 V72P0 mother 9036×10240 nnz=49620 prefix1111 tail4 indptr/indices相等 + 最小 adapter pack/syndrome/tag, 不引 `numba/sklearn` 额外) + 1 审计探针 + 双报告 + 1 小测试；零 decoder/业务矩阵，最短科学路径。laziest alternative: `numpy` + `logsumexp` + `scipy.sparse` 已装，复用 V72P0 的 tree-only 与 sparse IRA，不新增依赖。

> **科学问题（冻结）**：于完全冻结主体（`Q=1024 N=1024 Nbit=10240 M=9036 f=1.3 NOT_MEASURED used_2m false, tag 64b exact SHA256(bits)[:8B] LE, col sym*10+bit bit_i(s)=(s>>i)&1`）下，**验证最小 adapter 能否无损衔接 `1024-state local factor 自排除` ↔ `binary IRA mother 9036×10240 增量 syndrome` ↔ `exact 64-bit tag`**：定义 **10 步数据流**（合成 bits → prior → 自排除因子 → extrinsic 打包 → mother 前缀 → 增量 syndrome → 披露计费 → exact tag → 边/内存估算 → 5 态分流），冻结 **3 类型**（`AdapterConfig 8字段 / AdapterResult / Adapter`）与 **4公式**，以 **SYNTHETIC_ONLY 四层 P1A plumbing / P1B tiny 端到端 / P1C 真消息传递 1/3/10 iter 报告finite/maxLLR/residual / P1D small loopy** 验证衔接正确性与复杂度，明确 **Δ8 与 decode checkpoint schedule 分离（Δ8=8 增量粒度 vs checkpoint r=160 72批量 末端9036 max上限 报告disclosed）**，每 session 5 终端总体 2 态，不跑 decoder，不改 V72P0，不启 V72。

## Goal

以最短 SYNTHETIC_ONLY 路径完成 **1024 local factor 自排除 ↔ binary IRA mother 9036×10240 增量 syndrome ↔ exact 64-bit tag 的最小 adapter 衔接可行性与复杂度地图**，为 V72P0 的 `去self 8 测试 + P0A tiny + P0B sparse` 之后是否可零改对接 `ldpc_v5` / 后续 V72 提供可验证的 adapter 证据：

### 1. 冻结最小 adapter 衔接 `local factor 自排除 ↔ IRA mother 增量 ↔ exact tag`，SYNTHETIC_ONLY 不跑 decoder 精确复用 V72P0 mother
- **冻结主体零改**：`Q=1024 N=1024 Nbit=10240 M=9036 f=1.3 NOT_MEASURED used_2m false tag 64b exact SHA256(bits)[:8B] LE col sym*10+bit bit_i(s)=(s>>i)&1 local factor 去self Σ_{j≠i} bits_j·llr_j logsumexp` 全只读（`git diff -- src/ ==0 && git diff -- comparison_bench/src/comparison_bench/formal_ir/ldpc_v5* ==0`），处理点 `84d62779` 单点 synthetic，不读 2M，不改 V70/V72P0 已冻结量。
- **Adapter 定义**：纯函数 `adapter_pack(extrinsic_10×1024 → bit_llr_10240) / adapter_syndrome(bits_10240, H_r) → syndrome_r / adapter_tag(bits_10240) → tag64`，无 I/O/随机/全局状态，枚举 1024 态 log-domain + 稀疏 CSR 模 2，前缀嵌套 `H_r = H_mother[0:r]`。
- **R72P1-01 精确复用 V72P0 mother**：删 `V72P1新seed` 新 seed，精确复用 `V72P0-SYN-MOTHER` 生成的 `H_mother 9036×10240 nnz=49620`，校验 `H_mother.indptr` 与 `H_mother.indices` 与 V72P0 落盘母码 byte-equal（`np.array_equal(indptr, v72p0_indptr) && np.array_equal(indices, v72p0_indices)`），`nnz=49620` 精确值，无容差，不重生成。

### 2. 定义 10 步数据流（S1-S10）+ 3 类型（Config 8字段/Result/Adapter）+ 4公式 + 5 终态
- **10 步 S1-S10**（见 Design §5）：
  1. `S1 synthetic_bits: b[10240]` 合成 bits（每符号 10 bits，`sym*10+bit` 列序）
  2. `S2 prior: prior[1024,1024]` 合成先验（SYNTHETIC_ONLY 均匀或固定 λ*，不读 2M）
  3. `S3 local_factor 自排除: LLR_{→i}=logsumexp_{bit_i=1} Σ_{j≠i} bits_j·llr_j - logsumexp_{bit_i=0} Σ_{j≠i}`（`T_LF01-08` 1e-12/1e-9）
  4. `S4 extrinsic 打包: bit_llr[10240] col=sym*10+bit` 4消息数组打包
  5. `S5 mother 前缀: H_mother 9036×10240 sparse CSR IRA dual-diagonal, H_r = H_mother[0:r] r∈Δ8序列 160,168,...,9032,9036 且 checkpoint72 checkpoint 160,288,...,8992,9036`
  6. `S6 增量 syndrome: s_r = H_r·b mod2, s_{r+8}=s_r ∪ 8 new rows`（异或增量，Δ8 粒度）
  7. `S7 披露计费: leak_r = r·1 +64 bits, f=1.3 frozen f_actual NOT_MEASURED，checkpoint r 上报告disclosed=r+64`
  8. `S8 exact tag: tag=SHA256(b)[:8B] LE, verify tag==SHA256(s_hat)[:8B]`
  9. `S9 边/内存估算: nnz=49620 / row_deg / col_deg / CSR bytes / peak wall + 10数组分项 float`
  10. `S10 5 态分流: EVIDENCE > KERNEL > PLUMBING_TINY > MATRIX_SMOKE > ADAPTER_PLAN_READY`（需 KERNEL∧P1A∧P1B∧P1C 4硬 AND）+ overall 2 态
- **3 类型**（Design §5）：
  - `AdapterConfig 8字段 {Q,N,M,r0,delta,max_r,f,tag_bits}` — 冻结配置 8字段精确冻结，不含 seed/used_2m/successor
  - `AdapterResult {T_LF01-08, P1A c3_obs, P1B tiny, P1C 真消息1/3/10 finite/maxLLR/residual, P1D loopy_descriptive, edges, memory10, wall, classification}` — 每 synthetic case 结果
  - `Adapter {pack, syndrome, tag, prefix_nested, incremental}` — 最小接口，纯函数
- **4公式**（Design §5.2，R72P1-02）：
  1. `prior[1024,1024] = log(1/1024)` 均匀先验
  2. `extrinsic_llr[i][n] i=0..9 n=0..1023` 去self 外信息 `LLR_{→i}[n] = logsumexp_{s:bit_i=1} (log_prior[s]+Σ_{j≠i} bit_j(s)·llr_j[n]) - logsumexp_{s:bit_i=0}(...)`
  3. `bit_llr[10240] : bit_llr[sym*10+bit]=extrinsic_llr[bit][sym]` 打包双射
  4. `c_llr[10240]` 信道/合成 dummy 先验（SYNTHETIC_ONLY 0）
  5. `msg_v2c[nnz] float64 max_iter 10 total720 warm_start true` 变量→校验 消息
  6. `msg_c2v[nnz] float64` 校验→变量 消息
  7. `var_belief[10240] float64` 变量后验 `belief = c_llr + Σ_{c∈N(v)} msg_c2v`
  8. `check_residual[9036] float64` 校验残差 `residual_c = tanh` 迭代差
  9. `syndrome_r[ r ] uint8` `s_r = H_r·b mod2`
  10. `app_llr[10240] float64` 最终 APP `app = c_llr + Σ msg_c2v` 报告 `finite/maxLLR`
- **5 终态 per synthetic case**（Design §7，R72P1-07 first-match）：
  1. `EVIDENCE_INCOMPLETE` — 输入缺失/非有限/frame 非法
  2. `KERNEL_FAIL` — `T_LF01-08` 任一 FAIL（去self 8 测试不通过）
  3. `PLUMBING_TINY_FAIL` — `P1A plumbing` 或 `P1B tiny` FAIL（含 `c3 observed_zero&&observed_one` 或 `1e-9` 或 `wall>30s`）
  4. `MATRIX_SMOKE_FAIL` — `P1C 真消息传递 1/3/10` 或 `P0B re-validate C1-C6/checkpoint` FAIL
  5. `ADAPTER_PLAN_READY` — 需 `KERNEL∧P1A∧P1B∧P1C` 全 PASS 且 `wall≤30s`（`P1D loopy` 仅描述性，不入硬门禁，AND gate 精确）
  - `overall ∈ {ADAPTER_PLAN_READY, NOT_READY}` 需全部 case `ADAPTER_PLAN_READY`；`P1D loopy` 在报告中单独 `capacity_warning` 正交旗标。

### 3. 三层（实四层）SYNTHETIC_ONLY P1A/B/C/D
- **P1A plumbing**：纯函数 adapter 探针（不含 BP 环），验证 `pack ↔ syndrome 增量 ↔ tag` 的确定性与前缀嵌套，`wall≤30s`。
- **P1B tiny 端到端**：`k∈{2,3} n∈{6,9} total_bits 6/9 exhaustive 64/512 各 8 trials, tree forest` 经 adapter 到 `syndrome+tag` 端到端，`c5 1e-9` 复用（tree 上 BP exact），`c3 observed_zero&&observed_one` 负向测试保留。
- **P1C 真消息传递 1/3/10 iter**：`Nbit=10240 H_mother 9036×10240` 精确复用 mother `nnz=49620 indptr/indices相等` 上 `1/3/10 iter` 真消息传递（belief propagation 真迭代，非 smoke 空转），每档报告 `wall_s / peak_MiB 双向 streaming / finite / maxLLR / residual / edges / CSR bytes / syndrome 增量一致性 / tag exact`，`1 iter <1s, 3 iter <5s, 10 iter ≤30s`，超限 `MATRIX_SMOKE_FAIL`。
- **P1D small loopy**：`n=12 k=3` 含单环 small graph adapter 正确性探针（syndrome/tag 仍 exact，BP 非 exact 仅描述），不入 `ADAPTER_PLAN_READY` 硬门禁，仅 `descriptive_diagnostics` 与 `capacity_warning`。

### 4. 估算 edge / memory（复杂度探针 10数组分项 float）
- **Edge**：`nnz=49620` 精确值（`V72P0 mother` 精确复用，无1pct容差容差），`row_deg min>0 max≤6, col_deg` 分布已落盘，`zero_cols 0 dup 0`，`CSR indptr/indices byte-equal` 。
- **Memory 10数组分项 float**（Design §5.7，R72P1-06）：`CSR = nnz*4 + (M+1)*4 ≈ 49620*4+9037*4=234628B≈229KB + overhead`，10消息数组分项：`log_prior 1024*8=8KB + extrinsic_10x1024 10240*8=80KB + bit_llr 80KB + c_llr 80KB + msg_v2c 49620*8≈387KB + msg_c2v 387KB + var_belief 80KB + check_residual 9036*8≈70KB + syndrome 9036*1≈9KB + app_llr 80KB = 合计≈prior 8MiB`，`peak≤2048MiB` 报告显式 `CSR bytes / 10数组分项 / peak_MiB`
- **Complexity**：`O(nnz + N*Q*10)`（`N=1024 Q=1024 10bit 枚举 10,485,760 + 稀疏模 2 nnz=49620`，每 iter 10数组更新），`ponytail:` 已标 ceiling。

### 5. 四工件，不跑 decoder 不改 V70/V72P0 本轮只四工件
- 产出 `proposal/design/tasks/specs` 四工件（R72P1-09 本轮只四工件，不含脚本/registry/报告/测试，脚本与双报告为下一轮）；`v72p1_data_registry_synthetic.json`（`schema v72p1_synthetic_v1 head TBD, Q1024 N1024 M9036 f1.3 used_2m false successor_v72_not_started`）为后续轮占位；本轮不产 `scripts/` 不创 `run_01`。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_H*_business / gf_rank_business / nested_business` decoder 或业务矩阵构造的收敛性判定（`P1C` 为真消息传递 `1/3/10 iter` 报告 `finite/maxLLR/residual`，不判 FER/阈值；脚本内 `rg "decode_" 0 hits`）；不改 `H1/Lane C/m2/H_total/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不以 `required/margin` 构造业务 H。
- 不读密封 `TEST` 或 `2M real` 的任何 `H/CE/NLL/MAP` 统计作 adapter 选择，`used_2m false` 且 `used_test false`，违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；不扩 `λ` 或 `r0/Δ` 搜索（`r0=160 Δ8 max9036` 冻结，checkpoint 72批量冻结）。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank，不以 `ADAPTER_PLAN_READY` 宣称码可译。
- 不改写/覆盖 `V13/V48–V72P0` 任何已有输出与终态（只读）；`V72P0` 的 `P0A 64/512 8trials + P0B sparse 9036×10240` 仅复用校验（精确复用 mother `nnz=49620 indptr/indices相等`），不重构 V72P0，不改 `src/` baseline，不调 `TEST`，不启动 V72。
- 不以总体平均替代 per-case 分流；不以 `V25 H` 作新域门禁，门禁用 `T_LF 1e-12/1e-9 + P1A/B/C hard 阈 + wall≤30s + 增量/前缀/Tag exact`。
- 不创建正式 `.../v72p1_*/run_01` decoder 执行；正式 decoder 需另起 OpenSpec + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单 adapter 内 SYNTHETIC_ONLY 探查，不作跨方法 rank。
- **不启动 V72**：任何 V72 `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结均禁止在本变更内声明或执行；V72P1 报告仅以 `successor ∈ {v72p1_adapter_integration, v72_mother_refine, recollect}` 指向，不创建 V72 目录或产出。
- **本轮只四工件**：不产脚本/registry/报告/测试，仅四工件修订（R72P1-09）。

## Scope

1. **冻结主体与处理点零改（1024维符号 adapter 扩展，仅衔接验证，精确复用 V72P0 mother）**：`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 f1.3 NOT_MEASURED used_2m false tag64b exact SHA256(bits)[:8B] LE col sym*10+bit bit_i=(s>>i)&1 去self Σ_{j≠i}` 全只读；`84d62779 legacy_v1` 单点；精确复用 `V72P0 mother 9036×10240 nnz=49620 indptr/indices相等`，删 `V72P1新seed` 新 seed；不引 V72P1 新码本以外的表示。
2. **10 步数据流 S1-S10 + 3 类型 Config 8字段/Result/Adapter + 4公式**：`S1 synthetic_bits → S2 prior → S3 去self LF → S4 extrinsic打包（10数组 sym*10+bit） → S5 mother前缀（Δ8 vs checkpoint分离） → S6 增量syndrome → S7 披露计费 checkpoint disclosed → S8 exact tag → S9 边/内存10数组分项 float → S10 5态分流 first-match`，`AdapterConfig 8字段 {Q,N,M,r0,delta,max_r,f,tag_bits} 精确冻结`，落盘 `v72p1_manifest.json`。
3. **R72P1-02 4公式**：`prior[1024,1024] / extrinsic_llr[10][1024] / bit_llr[10240] / c_llr[10240] / msg_v2c[nnz] / msg_c2v[nnz] / var_belief[10240] / check_residual[9036] / syndrome_r / app_llr[10240]` 各公式显式，`O(nnz+N*Q*10)` 复杂度来源10数组。
4. **R72P1-04 分离Δ8 与 decode checkpoint schedule**：`Δ=8` 为增量 syndrome 粒度 `r∈{160,168,...,9032,9036}`；`checkpoint schedule` 为真解码触发点 `r_checkpoint ∈ {160,288,416,...,8992,9036}`（72批量，起始160，末端9036 max上限），`disclosed=r_checkpoint·1+64` 报告，`max=9036` 为上限。
5. **P1A plumbing（SYNTHETIC_ONLY 确定性，精确复用 mother）**：`adapter_pack / syndrome / tag / prefix_nested / incremental` 纯函数探针，校验 `indptr/indices相等` 前缀 `H_r==H_mother[0:r]`、`s_{r+8}=s_r ∪ new8` 异或一致性、tag LE exact，`wall≤30s`。
6. **P1B tiny 端到端（k2/3 n6/9 64/512 各8 trials tree-only）**：`64 exhaustive (k2,n6) + 512 exhaustive (k3,n9) 各8 trials` 经 adapter 到 `syndrome+tag` 端到端，`c3 observed_zero&&observed_one fail-closed + 负向测试`，`c5 BP-marg vs brute max|Δ|<1e-9 tree-only`，`wall≤30s peak≤2048MiB`。
7. **P1C 真消息传递 1/3/10 iter（10240×9036 精确复用 mother）**：`H_mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036 nnz=49620 indptr/indices相等` 上 `1 iter / 3 iter / 10 iter` 三档真消息传递，各计 `wall_s/peak_MiB/finite/maxLLR/residual/edges/CSR bytes/syndrome增量/tag exact`，`C1-C6 re-validate`（`rank9036 row_min>0 dup0 prefix inc tag`）+ `checkpoint 160,288,416,9036 disclosed`，超限判 `MATRIX_SMOKE_FAIL`。
8. **P1D small loopy（n12 k3 含环描述性）**：`n=12 k=3 total 12 bits` 含单环 small graph adapter `syndrome/tag exact` 验证，BP 非 exact 仅 `descriptive_diagnostics` 与 `capacity_warning` 正交旗标，不入硬门禁。
9. **边/内存/复杂度 10数组分项 float**：`nnz=49620 精确 zero0 dup0 CSR≈229KB 10数组≈prior 8MiB peak<2GiB` 显式落盘，`per invocation ns = wall·1e9 / calls`，`O(nnz + N*Q*10)` 复杂度注释 `ponytail:` 标 ceiling。
10. **终态 per-case 5 态 first-match + 总体 2 态 + 预算/复杂度审计**：每 case `EVIDENCE > KERNEL(T_LF01-02) > PLUMBING_TINY(P1A/P1B) > MATRIX_SMOKE(P1C/P0B) > ADAPTER_PLAN_READY(KERNEL∧P1A∧P1B∧P1C∧wall≤30 4硬 AND)` first-match 互斥；总体 `ADAPTER_PLAN_READY (all cases READY) / NOT_READY` + `5 counts + edges/memory10/wall` 审计；`P1D loopy` 正交 `capacity_warning` 仅描述不过门禁。删除 `1pct容差` 容差，AND gate 机械修正。
11. **四工件交付（SYNTHETIC_ONLY，本轮只四工件）**：`proposal.md/design.md/tasks.md/specs/spec.md` 四工件修订，`py_compile PASS`，`rg "V72P1新seed" 0 hits`，`rg "decode_" 0 hits`，本轮不产脚本/registry/报告，仅四工件。
12. **守卫 R72P1-01~10**：见 Design §8 / Spec §10，覆盖 `精确复用 mother nnz49620 indptr/indices相等 / 4公式 / Config8字段 / Δ8与checkpoint分离72批量9036 max disclosed / 真消息传递1/3/10 finite/maxLLR/residual / 10数组memory O(nnz+N*Q*10) / 5态first-match AND / 机械修正无1pct容差 保持未完成 / 本轮只四工件`。

## Impact Scope

- **修订（本变更四工件）**：`openspec/changes/formal-ir-v72p1-soft-joint-binary-adapter/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` 修订：R72P1-01 删 `V72P1新seed` 精确复用 `V72P0 mother nnz=49620 indptr/indices相等`；R72P1-02 明确4公式；R72P1-03 冻结 Config 8字段 `{Q,N,M,r0,delta,max_r,f,tag_bits}`；R72P1-04 分离Δ8与 checkpoint 160 72批量 末端9036 max上限 报告disclosed；R72P1-05 P1C真消息传递 1/3/10 iter 报告finite/maxLLR/residual；R72P1-06 内存重算10数组分项 float 复杂度 `O(nnz+N*Q*10)`；R72P1-07 修正5终态 first-match AND；R72P1-08 机械修正删除`1pct容差`等保持未完成；R72P1-09 本轮只四工件。
- **只读依赖**：`v72p0_data_registry_synthetic.json / v72p0_results.json`（`P0A/P0B` 精确复用 mother 校验，不重跑 V72P0）+ `comparison_bench/src/comparison_bench/formal_ir/ldpc_v5*.py`（只读探针，不执行 `run_ldpc_formal_v5`）+ `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照；`src/` 零改。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录四工件外）、`V38–V72P0` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 decoder，不构业务矩阵，不重估计 V72P0，不启动 V72，本轮只四工件**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD TBD (freeze-time git rev-parse HEAD)` + `data 84d62779 synthetic_v72p1` + `predecessor V72P0 5591e16b / V71 e038114d / V70 9bc34be6` 已绑定，显式声明 SYNTHETIC_ONLY、零 decoder/业务矩阵、最小 adapter 10 步数据流 3 类型 5 终态、4消息数组、Config8字段、Δ8与checkpoint分离、四层 P1A/B/C/D、边/内存10数组、first-match 5态、四工件产出已声明。
- [ ] **R72P1-01 精确复用 V72P0 mother **：`rg "V72P1新seed" 0 hits`，`H_mother 9036×10240 nnz=49620` 精确值，`indptr/indices byte-equal` 校验已定义，`git diff -- src/ ==0 && git diff -- comparison_bench/src/comparison_bench/formal_ir/ldpc_v5* ==0`，无新 seed。
- [ ] **R72P1-02 4公式**：`prior[1024,1024] / extrinsic_llr[10][1024] / bit_llr[10240] / c_llr[10240] / msg_v2c[nnz] / msg_c2v[nnz] / var_belief[10240] / check_residual[9036] / syndrome_r / app_llr[10240]` 10数组枚举与公式 `LLR_{→i}=logsumexp_{1}-logsumexp_{0}|Σ_{j≠i}` 已显式，`py_compile PASS`。
- [ ] **R72P1-03 Config 8字段冻结**：`AdapterConfig` 仅 8字段 `{Q,N,M,r0,delta,max_r,f,tag_bits}` 精确冻结，多一少一即 FAIL，`seedMother 0 hits` 在 Config 定义内。
- [ ] **R72P1-04 Δ8与 checkpoint 分离**：`Δ=8` 增量粒度 `r∈{160,168,...,9032,9036}` 与 `checkpoint schedule {160,288,416,...,8992,9036} 72批量 max=9036 上限 报告disclosed=r+64` 分离已显式，`leak_r` 与 `disclosed` 一致。
- [ ] **去self 8 测试 T_LF01-08 **：`log_post_excl_i=log_prior+Σ_{j≠i} - logZ`，`T_LF01 completeness / T_LF02 normalization 1e-12 / T_LF03 marginal 1e-12 / T_LF04 delta 1e-9 / T_LF05 self_exclusion 1e-12 / T_LF06 stability K1e6 isfinite / T_LF07 determinism==0 / T_LF08 brute 1e-12` 正交 `8test` 全 PASS。
- [ ] **P1A plumbing **：`adapter_pack deterministic && prefix_nested H_r==H_mother[0:r] indptr/indices相等 && incremental s_{r+8} 异或一致 && tag LE exact && 二次调用 max|Δ|==0`，`wall≤30s` 。
- [ ] **P1B tiny 端到端**：`(k2,n6)64 (k3,n9)512 各8 trials exhaustive tree forest` 经 adapter 到 `syndrome+tag` 端到端，`c1 isfinite / c2 brute exists isfinite / c3 observed_zero&&observed_one fail-closed + 负向测试 / c4 brute exists / c5 max|Δ|<1e-9 tree-only / c6 tree / c7 total≤9 exhaustive` 7 checks 全 PASS，`worst<1e-9 wall≤30s peak≤2048MiB` 。
- [ ] **R72P1-05 P1C 真消息传递 1/3/10 iter **：`H_mother 9036×10240 nnz=49620 indptr/indices相等 sparse CSR IRA dual-diagonal rank9036` 上 `1 iter / 3 iter / 10 iter` 真消息传递，各报告 `wall_s/peak_MiB/finite/maxLLR/residual/edges/CSR bytes/syndrome增量/tag exact`，`C1-C6 re-validate` 且 `checkpoint 160/288/416/9036 disclosed` ，`1 iter wall<1s / 3 iter <5s / 10 iter ≤30s` 三档全 PASS。
- [ ] **P1D small loopy 描述性**：`n=12 k=3 total 12 bits` 含单环 small graph `syndrome/tag exact` ，BP 非 exact 仅 `descriptive_diagnostics {loopy_graph, cycle_count, BP_residual, syndrome_ok, tag_ok}` + `capacity_warning` 正交旗标，不入硬门禁。
- [ ] **R72P1-06 10数组 memory/复杂度**：`nnz=49620 精确 zero0 dup0 CSR≈229KB 10数组≈prior 8MiB (log_prior 8KB+extrinsic80KB+bit_llr80KB+c_llr80KB+msg_v2c387KB+msg_c2v387KB+var_belief80KB+check_residual70KB+syndrome9KB+app_llr80KB) peak<2GiB per_invocation ns` 已显式，`O(nnz+N*Q*10)` = `O(49620+1024*1024*10)` 复杂度注释 `ponytail:` 已标 ceiling，无 `1pct容差`。
- [ ] **R72P1-07 5终态 first-match **：每 case `classification ∈ {EVIDENCE_INCOMPLETE, KERNEL_FAIL, PLUMBING_TINY_FAIL, MATRIX_SMOKE_FAIL, ADAPTER_PLAN_READY}` 按 `EVIDENCE > KERNEL(T_LF01-02) > PLUMBING_TINY(P1A/P1B) > MATRIX_SMOKE(P1C/P0B) > ADAPTER_PLAN_READY(KERNEL∧P1A∧P1B∧P1C∧wall≤30 4硬 AND)` first-match 已判定，无 `OR_SYM` 误用；总体 `overall ∈ {ADAPTER_PLAN_READY (all cases READY), NOT_READY}` 基于 `5 orthogonal counts` 已判定。
- [ ] **R72P1-08 机械修正**：AND gate 已修正为 `∧`（无 `OR_SYM`），删除 `1pct容差` 容差表述，删除 `≈旧nnz` 误值，保持 `未完成`（`[ ]` 未勾选，`TBD` 保留，`lifecycle PLAN_CANDIDATE`）。
- [ ] **R72P1-09 本轮只四工件**：仅 `proposal/design/tasks/specs` 四工件修订，未创建 `scripts/`/`registry`/`results`/`reports`/`tests`，`ls scripts/v72p1_*` 不存在。
- [ ] 已停留在 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v72p1_*/run_01`（`ls` 不存在）且未创建任何 `.../v72_*/run_01`，不比较，不碰 `V48-V72P0` 块外，未转 qualification，未启动 V72，**四工件已修订，保持未完成，等待复核**。

## Tasks

见 `tasks.md`（Phase A 合成注册表占位；Phase B 冻结主体零改精确复用 mother；Phase C 去self 8 测试；Phase D P1A plumbing；Phase E P1B tiny 端到端 64/512 8 trials 含负向测试；Phase F P1C 真消息传递 1/3/10 iter 49620 72批量 checkpoint + P0B re-validate；Phase G P1D small loopy 描述性；Phase H 5态 first-match AND + 10数组 memory O(nnz+N*Q*10)；Phase I 四工件修订 + 守卫 R72P1-01~10 + 本轮只四工件 保持未完成）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` new-session 对照；`V66` 单 session `72` 自适应 `RATE_NOT_FEASIBLE`；`V67-MAP` 已 `V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL`（natural 5+5）；`V68-BAL` 为均衡 5+5 均衡性地图；`V69-3L` 为三层表示可行性地图；`V70-BSJ` 为二进制 soft-joint 因子完整性地图；`V71-SJK` 为 1024-state 纯因子核 5 函数 D1-D10 地图；`V72P0-SYN` 为合成 correctness P0 壁垒（`T_LF 去self 8test + P0A k2/3 6/9 64/512 8trials tree-only c3观测 1e-9 + P0B sparse 9036×10240 nnz=49620 5-state`，`PLAN_CANDIDATE/SYNTHETIC_ONLY/EXECUTE_NOT_AUTHORIZED`，`5591e16b/64ca2f1e`）；`V72P1-ADP` 为**最小 adapter 衔接可行性与复杂度地图**合成探针（`10 步 S1-S10 + 3 类型 Config8字段/Result/Adapter + 4消息数组 + P1A plumbing / P1B tiny 端到端 / P1C 真消息1/3/10 finite/maxLLR/residual / P1D small loopy + 10数组 memory O(nnz+N*Q*10) + 5态 first-match`，`PLAN_CANDIDATE/SYNTHETIC_ONLY/EXECUTE_NOT_AUTHORIZED`，精确复用 V72P0 mother，不跑 decoder，不启 V72）；`V72P1` 本身不直接进入 V72 qualification；任何 decoder / 真码率 V72 需另起 `EXECUTE_AUTH`。
