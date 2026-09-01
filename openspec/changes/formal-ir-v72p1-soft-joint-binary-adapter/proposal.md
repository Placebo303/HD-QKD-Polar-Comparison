# OpenSpec Proposal: formal-ir-v72p1-soft-joint-binary-adapter

**Status**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal IR / soft-joint binary adapter (V72P0 synthetic successor)
**Change ID**: `formal-ir-v72p1-soft-joint-binary-adapter`
**Cycle ID**: `V72P1-ADP` predecessor `V72P0-SYN (5591e16bf35b03c3df30a003bee12011a796d73e)` + `V71-SJK` + `V70-BSJ`
**Branch**: `formal-ir-mainline`
**Implementation**: `TBD (git rev-parse HEAD on freeze; EXTERNAL_BINDING until Pre-RESULT)` 
**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1` synthetic only, `used_2m false`)
**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + 合成 adapter 复杂度探针 + P1A/B/C/D 四层 synthetic，不跑 decoder，不创 `run_01`，不改 V70/V72P0，不启 V72

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 合成探针 (`numpy` 1024 log-domain + `scipy.sparse CSR` IRA 9036×10240 + 最小 adapter pack/syndrome/tag, 不引 `numba/scipy/sklearn` 额外) + 1 审计探针 + 双报告 + 1 小测试；零 decoder/业务矩阵，最短科学路径。laziest alternative: `numpy` + `logsumexp` + `scipy.sparse` 已装，复用 V72P0 的 tree-only 与 sparse IRA，不新增依赖。

> **科学问题（冻结）**：于完全冻结主体（`Q=1024 N=1024 Nbit=10240 M=9036 f=1.3 NOT_MEASURED used_2m false, tag 64b exact SHA256(bits)[:8B] LE, col sym*10+bit bit_i(s)=(s>>i)&1`）下，**验证最小 adapter 能否无损衔接 `1024-state local factor 自排除` ↔ `binary IRA mother 9036×10240 增量 syndrome` ↔ `exact 64-bit tag`**：定义 **10 步数据流**（合成 bits → prior → 自排除因子 → extrinsic 打包 → mother 前缀 → 增量 syndrome → 披露计费 → exact tag → 边/内存估算 → 5 态分流），冻结 **3 类型**（`AdapterConfig / AdapterResult / Adapter`），以 **SYNTHETIC_ONLY 四层 P1A plumbing / P1B tiny 端到端 / P1C full-size 1/3/10 iter smoke / P1D small loopy** 验证衔接正确性与复杂度，每 session 5 终端总体 2 态，不跑 decoder，不改 V70/V72P0，不启 V72。

## Goal

以最短 SYNTHETIC_ONLY 路径完成 **1024 local factor 自排除 ↔ binary IRA mother 增量 syndrome ↔ exact 64-bit tag 的最小 adapter 衔接可行性与复杂度地图**，为 V72P0 的 `去self 8 测试 + P0A tiny + P0B sparse` 之后是否可零改对接 `ldpc_v5` / 后续 V72 提供可验证的 adapter 证据：

### 1. 冻结最小 adapter 衔接 `local factor 自排除 ↔ IRA mother 增量 ↔ exact tag`，SYNTHETIC_ONLY 不跑 decoder
- **冻结主体零改**：`Q=1024 N=1024 Nbit=10240 M=9036 f=1.3 NOT_MEASURED used_2m false tag 64b exact SHA256(bits)[:8B] LE col sym*10+bit bit_i(s)=(s>>i)&1 local factor 去self Σ_{j≠i} bits_j·llr_j logsumexp` 全只读（`git diff -- src/ ==0 && git diff -- comparison_bench/src/comparison_bench/formal_ir/ldpc_v5* ==0`），处理点 `84d62779` 单点 synthetic，不读 2M，不改 V70/V72P0 已冻结量。
- **Adapter 定义**：纯函数 `adapter_pack(extrinsic_10×1024 → bit_llr_10240) / adapter_syndrome(bits_10240, H_r) → syndrome_r / adapter_tag(bits_10240) → tag64`，无 I/O/随机/全局状态，枚举 1024 态 log-domain + 稀疏 CSR 模 2，前缀嵌套 `H_r = H_mother[0:r]`。

### 2. 定义 10 步数据流（S1-S10）+ 3 类型（Config/Result/Adapter）+ 5 终态
- **10 步 S1-S10**（见 Design §5）：
  1. `S1 synthetic_bits: b[10240]` 合成 bits（每符号 10 bits，`sym*10+bit` 列序）
  2. `S2 prior: log_prior[1024]` 合成先验（SYNTHETIC_ONLY 均匀或固定 λ*，不读 2M）
  3. `S3 local_factor 自排除: LLR_{→i}=logsumexp_{bit_i=1} Σ_{j≠i} - logsumexp_{bit_i=0} Σ_{j≠i}`（`T_LF01-08` 1e-12/1e-9）
  4. `S4 extrinsic 打包: bit_llr[10240] col=sym*10+bit`
  5. `S5 mother 前缀: H_mother 9036×10240 sparse CSR IRA dual-diagonal, H_r = H_mother[0:r] r∈{160,168,...,9036}`
  6. `S6 增量 syndrome: s_r = H_r·b mod2, s_{r+8}=s_r ∪ 8 new rows`（异或增量）
  7. `S7 披露计费: leak_r = r·1 +64 bits, f=1.3 frozen f_actual NOT_MEASURED`
  8. `S8 exact tag: tag=SHA256(b)[:8B] LE, verify tag==SHA256(s_hat)[:8B]`
  9. `S9 边/内存估算: nnz / row_deg / col_deg / CSR bytes / peak wall`
  10. `S10 5 态分流: EVIDENCE > KERNEL > PLUMBING_TINY > MATRIX_SMOKE > ADAPTER_PLAN_READY`（需 KERNEL∧P1A∧P1B∧P1C）+ overall 2 态
- **3 类型**（Design §6）：
  - `AdapterConfig {Q1024,N1024,Nbit10240,M9036,r0 160,Δ8,max9036,tag f1.3,seed,col,seed_mother}` — 冻结配置
  - `AdapterResult {T_LF01-08, P1A c3_obs, P1B tiny, P1C smoke, P1D loopy_descriptive, edges, memory, wall, classification}` — 每 synthetic case 结果
  - `Adapter {pack, syndrome, tag, prefix_nested, incremental}` — 最小接口，纯函数
- **5 终态 per synthetic case**（Design §7）：
  1. `EVIDENCE_INCOMPLETE` — 输入缺失/非有限/frame 非法
  2. `KERNEL_FAIL` — `T_LF01-08` 任一 FAIL（去self 8 测试不通过）
  3. `PLUMBING_TINY_FAIL` — `P1A plumbing` 或 `P1B tiny` FAIL（含 `c3 observed_zero&&observed_one` 或 `1e-9` 或 `wall>30s`）
  4. `MATRIX_SMOKE_FAIL` — `P1C full-size 1/3/10 smoke` 或 `P0B re-validate C1-C6/pivot` FAIL
  5. `ADAPTER_PLAN_READY` — 需 `KERNEL∧P1A∧P1B∧P1C` 全 PASS 且 `wall≤30s`（`P1D loopy` 仅描述性，不入硬门禁）
  - `overall ∈ {ADAPTER_PLAN_READY, NOT_READY}` 需全部 case `ADAPTER_PLAN_READY`；`P1D loopy` 在报告中单独 `capacity_warning` 正交旗标。

### 3. 三层（实四层）SYNTHETIC_ONLY P1A/B/C/D
- **P1A plumbing**：纯函数 adapter 探针（不含 BP 环），验证 `pack ↔ syndrome 增量 ↔ tag` 的确定性与前缀嵌套，`wall≤30s`。
- **P1B tiny 端到端**：`k∈{2,3} n∈{6,9} total_bits 6/9 exhaustive 64/512 各 8 trials, tree forest` 经 adapter 到 `syndrome+tag` 端到端，`c5 1e-9` 复用（tree 上 BP exact），`c3 observed_zero&&observed_one` 负向测试保留。
- **P1C full-size 1/3/10 iter smoke**：`Nbit=10240 H_mother 9036×10240` 上 `1/3/10 iter` 的消息传递 smoke（非收敛判定），仅计量 `wall_s / peak_MiB / edges / CSR bytes / syndrome 增量一致性 / tag exact`，`1 iter <1s, 3 iter <5s, 10 iter ≤30s`，超限 `MATRIX_SMOKE_FAIL`。
- **P1D small loopy**：`n=12 k=3` 含单环 small graph adapter 正确性探针（syndrome/tag 仍 exact，BP 非 exact 仅描述），不入 `ADAPTER_PLAN_READY` 硬门禁，仅 `descriptive_diagnostics` 与 `capacity_warning`。

### 4. 估算 edge / memory（复杂度探针）
- **Edge**：`nnz ≈ r·(info_deg 3-4 + parity 2) ≈ 9036×5.5≈49698`（`info 每行 3-4 列 + H_p dual-diagonal 2`），`row_deg min>0 max≤6, col_deg` 分布已落盘，`zero_cols 0 dup 0`
- **Memory**：`CSR = nnz·(int32 col + float64?/uint8) + indptr ≈ 49698·4 + 9037·4 ≈ 235KB + overhead <1MB`（`float LLR` 另 `10240·8≈80KB`），`peak≤2048MiB` 远未触阈，报告显式 `CSR bytes / peak_MiB`
- **Complexity spike**：`S1-S10` 单次 `O(nnz + Q·1024)`（`Q=1024` 先验枚举 `1024·10` + 稀疏模 2 `nnz`），`P1C 10 iter smoke` 的 `wall` 取 `1M VAL` 误用？—— SYNTHETIC_ONLY 不读 2M，固定 `synthetic_bits` 随机种子 0 批量 1024 次核调用，`wall` median。

### 5. 四工件 + complexity spike，不跑 decoder 不改 V70/V72P0
- 产出 `proposal/design/tasks/specs` 四工件 + `v72p1_data_registry_synthetic.json`（`schema v72p1_synthetic_v1 head TBD, Q1024 N1024 M9036 f1.3 used_2m false successor_v72_not_started`） + `scripts/v72p1_soft_joint_binary_adapter.py`（`rg "decode_" 0 hits, py_compile PASS`） + `scripts/v72p1_backend_audit.py`（`IntEnum READY/NOT_READY`） + `v72p1_results.json / v72p1_table.csv/.json / v72p1_manifest.json / V72P1_SYN_REPORT.md / V72P1_BACKEND_AUDIT_REPORT.md` + `test_v72p1_*.py`（`pytest -p no:cacheprovider -q`）+ 控制台 5 态/2 态摘要；**禁** `decode_/construct_business/2M/MET/V72/run_01`。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_H*_business / gf_rank_business / nested_business` decoder 或业务矩阵构造的收敛性判定（`P1C` 仅 `1/3/10 iter smoke` 计量 `wall/peak/edge/syndrome增量/tag`，不判 FER/阈值；脚本内 `rg "decode_" 0 hits`）；不改 `H1/Lane C/m2/H_total/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不以 `required/margin` 构造业务 H。
- 不读密封 `TEST` 或 `2M real` 的任何 `H/CE/NLL/MAP` 统计作 adapter 选择，`used_2m false` 且 `used_test false`，违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；不扩 `λ` 或 `r0/Δ` 搜索（`r0=160 Δ8 max9036` 冻结）。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank，不以 `ADAPTER_PLAN_READY` 宣称码可译。
- 不改写/覆盖 `V13/V48–V72P0` 任何已有输出与终态（只读）；`V72P0` 的 `P0A 64/512 8trials + P0B sparse 9036×10240` 仅复用校验，不重构 V72P0，不改 `src/` baseline，不调 `TEST`，不启动 V72。
- 不以总体平均替代 per-case 分流；不以 `V25 H` 作新域门禁，门禁用 `T_LF 1e-12/1e-9 + P1A/B/C hard 阈 + wall≤30s + 增量/前缀/Tag exact`。
- 不创建正式 `.../v72p1_*/run_01` decoder 执行；正式 decoder 需另起 OpenSpec + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单 adapter 内 SYNTHETIC_ONLY 探查，不作跨方法 rank。
- **不启动 V72**：任何 V72 `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结均禁止在本变更内声明或执行；V72P1 报告仅以 `successor ∈ {v72p1_adapter_integration, v72_mother_refine, recollect}` 指向，不创建 V72 目录或产出。

## Scope

1. **冻结主体与处理点零改（1024维符号 adapter 扩展，仅衔接验证）**：`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 f1.3 NOT_MEASURED used_2m false tag64b exact SHA256(bits)[:8B] LE col sym*10+bit bit_i=(s>>i)&1 去self Σ_{j≠i}` 全只读；`84d62779 legacy_v1` 单点；不引 V72P1 新码本以外的表示。
2. **10 步数据流 S1-S10 + 3 类型 Config/Result/Adapter（最小 adapter）**：`S1 synthetic_bits → S2 prior → S3 去self LF → S4 extrinsic打包 → S5 mother前缀 → S6 增量syndrome → S7 披露计费 → S8 exact tag → S9 边/内存估算 → S10 5态分流`，`AdapterConfig/AdapterResult/Adapter` 三类型落盘 `v72p1_manifest.json`。
3. **P1A plumbing（SYNTHETIC_ONLY 确定性）**：`adapter_pack / syndrome / tag / prefix_nested / incremental` 纯函数探针，每项 `PASS/FAIL`，含确定性二次调用 `max|Δ|==0`、前缀 `H_r==H_mother[0:r]`、`s_{r+8}=s_r ∪ new8` 异或一致性、tag LE exact，`wall≤30s`。
4. **P1B tiny 端到端（k2/3 n6/9 64/512 各8 trials tree-only）**：`64 exhaustive (k2,n6) + 512 exhaustive (k3,n9) 各8 trials` 经 adapter 到 `syndrome+tag` 端到端，`c3 observed_zero&&observed_one fail-closed + 负向测试`，`c5 BP-marg vs brute max|Δ|<1e-9 tree-only`，`wall≤30s peak≤2048MiB`。
5. **P1C full-size 1/3/10 iter smoke（10240×9036）**：`H_mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036` 上 `1 iter / 3 iter / 10 iter` 三档 smoke，各计 `wall_s/peak_MiB/edges/CSR bytes/syndrome增量/tag exact`，`C1-C6 re-validate`（`rank9036 row_min>0 dup0 prefix inc tag`）+ `pivot 160/168/176/9036`，超限判 `MATRIX_SMOKE_FAIL`。
6. **P1D small loopy（n12 k3 含环描述性）**：`n=12 k=3 total 12 bits` 含单环 small graph adapter `syndrome/tag exact` 验证，BP 非 exact 仅 `descriptive_diagnostics` 与 `capacity_warning` 正交旗标，不入硬门禁。
7. **边/内存/复杂度估算**：`nnz≈49698 row_deg/col_deg zero0 dup0 CSR≈235KB peak<2GiB` 显式落盘，`per invocation ns = wall·1e9 / calls`，`O(nnz + Q·1024)` 复杂度注释 `ponytail:` 标 ceiling（若需后续真码率自适应，需另起 OpenSpec）。
8. **终态 per-case 5 态 + 总体 2 态 + 预算/复杂度审计**：每 case `EVIDENCE > KERNEL(c3之前) > PLUMBING_TINY(P1A/P1B) > MATRIX_SMOKE(P1C/P0B) > ADAPTER_PLAN_READY(KERNEL∧P1A∧P1B∧P1C∧wall≤30)`；总体 `ADAPTER_PLAN_READY (all cases READY) / NOT_READY` + `5 counts + edges/memory/wall` 审计；`P1D loopy` 正交 `capacity_warning` 仅描述不过门禁。
9. **四工件 + 复杂度探针交付（SYNTHETIC_ONLY）**：`scripts/v72p1_soft_joint_binary_adapter.py`（`rg decode_ 0`，`py_compile PASS`，仅 `numpy/pandas/pyarrow/scipy.sparse/hashlib`）输出 `v72p1_results.json + v72p1_table.{csv,json} + V72P1_SYN_REPORT.md + v72p1_manifest.json` + 控制台摘要；`scripts/v72p1_backend_audit.py`（`IntEnum`）输出 `V72P1_BACKEND_AUDIT_REPORT.md`；未创建 `run_01`。
10. **守卫 R72P1-01~10**：见 Design §8 / Spec §10，覆盖 `冻结主体+2M禁+10步+3类型 / 去self 8test 1e-12 / P1A plumbing确定性前缀增量tag / P1B tiny 64/512 c3观测1e-9 / P1C 9036×10240 1/3/10 smoke C1-C6 pivot / P1D loopy描述性 / 边内存复杂度 / 5态2态wall / 四工件双报告 / SYNTHETIC_ONLY不创run_01不改V70/V72P0不启V72`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v72p1-soft-joint-binary-adapter/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v72p1_soft_joint_binary_adapter.py` (`rg "decode_" 0 hits`, `py_compile PASS`) + `scripts/v72p1_backend_audit.py` (`IntEnum`, `rg "READY" 0 hits` 除枚举注释) + 冻结注册表 `v72p1_data_registry_synthetic.json` (`schema v72p1_synthetic_v1 head TBD, Q1024 N1024 M9036 f1.3 used_2m false successor_v72_not_started, P1A/B/C/D {plumbing, k2/3 n6/9 64/512 8trials, 9036×10240 1/3/10 smoke, n12 k3 loopy}`) + `v72p1_results.json` (per case `T_LF/P1A/P1B/P1C/P1D/edges/memory/wall/class`) + `v72p1_table.csv/.json` (每行 `case/Q/N/M/r/T_LF/plumbing/tiny/smoke/loopy/edges/CSR/wall/class/overall`) + `V72P1_SYN_REPORT.md` + `V72P1_BACKEND_AUDIT_REPORT.md` + `test_v72p1_*.py` + `v72p1_manifest.json` + 控制台摘要。
- **只读依赖**：`v72p0_data_registry_synthetic.json / v72p0_results.json`（`P0A/P0B` 复用校验，不重跑 V72P0）+ `comparison_bench/src/comparison_bench/formal_ir/ldpc_v5*.py`（`A1-A6` 只读探针，不执行 `run_ldpc_formal_v5`）+ `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照；`src/` 零改。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V72P0` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 decoder，不构业务矩阵，不重估计 V72P0，不启动 V72**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD TBD (freeze-time git rev-parse HEAD)` + `data 84d62779 synthetic_v72p1` + `predecessor V72P0 5591e16b / V71 e038114d / V70 9bc34be6` 已绑定，显式声明 SYNTHETIC_ONLY、零 decoder/业务矩阵、最小 adapter 10 步数据流 3 类型 5 终态、四层 P1A/B/C/D、边/内存估算、四工件+complexity spike 产出已声明。
- [ ] **冻结主体零改已验**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- comparison_bench/src/comparison_bench/formal_ir/ldpc_v5* ==0`，`Q1024 N1024 Nbit10240 M9036 r0 160 Δ8 max9036 f1.3 NOT_MEASURED used_2m false tag64b exact col sym*10+bit bit_i去self` 全只读，处理点 `84d62779 legacy_v1` 单点，`rg -i "gray|met|protograph|sc_coupling" scripts/v72p1_soft_joint_binary_adapter.py` 0 hits（除 adapter 纯函数注释），`rg "decode_|construct_.*business|gf_rank.*business|nested.*business" 0 hits` 已验（`ldpc_v5*` 只读探针不属业务），`rg "TEST.*read|read.*TEST" 0 hits` 且 `used_2m==false && used_test==false`。
- [ ] **10 步数据流 S1-S10 + 3 类型已验**：`S1 synthetic_bits 10240 / S2 log_prior 1024 / S3 去self LF T_LF01-08 1e-12/1e-9 / S4 extrinsic打包 col sym*10+bit / S5 mother前缀 H_r / S6 增量syndrome s_{r+8}=s_r∪new8 / S7 披露 r·1+64 f NOT_MEASURED / S8 exact tag SHA256 LE / S9 边内存估算 / S10 5态分流` 已定义且每 case 落盘 `AdapterConfig/AdapterResult/Adapter` 3 类型一致，`py_compile PASS`。
- [ ] **去self 8 测试 T_LF01-08 已验**：`log_post_excl_i=log_prior+Σ_{j≠i} - logZ`，`T_LF01 completeness / T_LF02 normalization 1e-12 / T_LF03 marginal 1e-12 / T_LF04 delta 1e-9 / T_LF05 self_exclusion 1e-12 / T_LF06 stability K1e6 isfinite / T_LF07 determinism==0 / T_LF08 brute 1e-12` 正交 `8test` 全 PASS，随 `v72p1_results.json:kernel` 落盘。
- [ ] **P1A plumbing 已验**：`adapter_pack deterministic && prefix_nested H_r==H_mother[0:r] && incremental s_{r+8} 异或一致 && tag LE exact && 二次调用 max|Δ|==0`，`wall≤30s` 已验，落盘 `P1A_PASS`。
- [ ] **P1B tiny 端到端已验**：`(k2,n6)64 (k3,n9)512 各8 trials exhaustive tree forest` 经 adapter 到 `syndrome+tag` 端到端，`c1 isfinite / c2 brute exists isfinite / c3 observed_zero&&observed_one fail-closed + 负向测试 (observed_one==false⇒c3 false 不变数值) / c4 brute exists / c5 max|Δ|<1e-9 tree-only / c6 tree / c7 total≤9 exhaustive` 7 checks 全 PASS，`worst<1e-9 wall≤30s peak≤2048MiB` 已验，落盘 `P1B_PASS`。
- [ ] **P1C full-size 1/3/10 iter smoke 已验**：`H_mother 9036×10240 sparse CSR IRA dual-diagonal det1 rank9036 info每行3-4 + H_p 2 nnz≈49698 C1 rank C2 row_min>0 C3 dup0 C4 prefix_nested C5 incremental C6 tag exact 64 samples` `pivot 160/168/176/9036 Rs r0 160 Δ8→9036` 已验，`1 iter wall<1s / 3 iter <5s / 10 iter ≤30s` 三档 `wall_s/peak_MiB/edges/CSR bytes/syndrome增量/tag exact` 已落盘，`P1C_PASS` 需三档全 PASS 且 `C1-C6 + pivot` 全 PASS。
- [ ] **P1D small loopy 描述性已验**：`n=12 k=3 total 12 bits` 含单环 small graph `syndrome/tag exact` 已验，BP 非 exact 仅 `descriptive_diagnostics {loopy_graph, cycle_count, BP_residual, syndrome_ok, tag_ok}` + `capacity_warning` 正交旗标，不入 `ADAPTER_PLAN_READY` 硬门禁，已落盘 `P1D_descriptive`。
- [ ] **边/内存/复杂度已验**：`nnz 49698±1% row_deg/col_deg zero0 dup0 CSR≈235KB peak<2GiB per_invocation ns` 已落盘且与 `V72P1_SYN_REPORT.md` 一致，`O(nnz + Q·1024)` 复杂度注释 `ponytail:` 已标 ceiling（`per-account locks if throughput matters` 升级路径显式）。
- [ ] **Per-case 5 终端互斥 + 总体 2 态已验**：每 case `classification ∈ {EVIDENCE_INCOMPLETE, KERNEL_FAIL, PLUMBING_TINY_FAIL, MATRIX_SMOKE_FAIL, ADAPTER_PLAN_READY}` 按 `EVIDENCE > KERNEL(T_LF01-02) > PLUMBING_TINY(P1A/P1B) > MATRIX_SMOKE(P1C/P0B) > ADAPTER_PLAN_READY(KERNEL∧P1A∧P1B∧P1C∧wall≤30)` 已判定；总体 `overall ∈ {ADAPTER_PLAN_READY (all cases READY), NOT_READY}` 基于 `5 orthogonal counts` 已判定，报告 5 态章节与 `json/csv` 一致。
- [ ] **四工件 + 复杂度探针完整**：`v72p1_data_registry_synthetic.json` + `v72p1_results.json` + `v72p1_table.csv/.json`（行对等，含 `case/Q/N/M/r/T_LF/plumbing/tiny/smoke/loopy/edges/CSR/wall/class/overall` 汇总且与 json 一致，`capacity_warning` 正交 + `descriptive_diagnostics` 逐 case）+ `V72P1_SYN_REPORT.md`（含 `per case T_LF/P1A c3_obs/P1B 64/512 worst/P1C 1/3/10 smoke edges/CSR/wall + overall 2 态`）+ `V72P1_BACKEND_AUDIT_REPORT.md`（含枚举探针）已齐。
- [ ] `scripts/v72p1_soft_joint_binary_adapter.py` 与 `scripts/v72p1_backend_audit.py` 为 SYNTHETIC_ONLY 可运行脚本（`rg "decode_" 0 hits`、`rg "construct_.*business" 0 hits`、`rg -i "met|protograph" 0 hits`，仅 `numpy/pandas/pyarrow/scipy.sparse/hashlib`，`py_compile` PASS，`pytest -p no:cacheprovider -q test_v72p1_*.py` PASS），输出 `results + table + 双报告` + 控制台 5 态/2 态摘要，**未创建 run_01，未构业务矩阵，未读 2M/TEST，未改 V70/V72P0，未启 V72**。
- [ ] 已停留在 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v72p1_*/run_01`（`ls` 不存在已验）且未创建任何 `.../v72_*/run_01`，不比较，不碰 `V48-V72P0` 块外，未转 qualification，未启动 V72，**四工件+registry+探针+双报告已单独提交推送，返回新 Plan SHA + per-case P1A/B/C/D/edges/memory/wall + 各分流计数 + overall 2 态**，等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/2M未读/T_LF 1e-12/P1A plumbing/P1B 64/512 c3观测1e-9/P1C 9036×10240 1/3/10 smoke/C1-C6 pivot/边内存/5态2态/CAL选VAL确认一次/V72_not_started`）。

## Tasks

见 `tasks.md`（Phase A 合成注册表；Phase B 冻结主体零改；Phase C 去self 8 测试；Phase D P1A plumbing；Phase E P1B tiny 端到端 64/512 8 trials 含负向测试；Phase F P1C full-size 1/3/10 iter smoke 9036×10240 + P0B re-validate；Phase G P1D small loopy 描述性；Phase H 5态2态 + 边内存复杂度；Phase I 四工件双报告 + T0-T3 + 守卫 R72P1-01~10 + 单独提交推送新 Plan SHA + 不启 V72）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` new-session 对照；`V66` 单 session `72` 自适应 `RATE_NOT_FEASIBLE`；`V67-MAP` 已 `V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL`（natural 5+5）；`V68-BAL` 为均衡 5+5 均衡性地图；`V69-3L` 为三层表示可行性地图；`V70-BSJ` 为二进制 soft-joint 因子完整性地图；`V71-SJK` 为 1024-state 纯因子核 5 函数 D1-D10 地图；`V72P0-SYN` 为合成 correctness P0 壁垒（`T_LF 去self 8test + P0A k2/3 6/9 64/512 8trials tree-only c3观测 1e-9 + P0B sparse CSR IRA 9036×10240 dual-diagonal 5-state`，`PLAN_CANDIDATE/SYNTHETIC_ONLY/EXECUTE_NOT_AUTHORIZED`，`5591e16b/64ca2f1e`）；`V72P1-ADP` 为**最小 adapter 衔接可行性与复杂度地图**合成探针（`10 步 S1-S10 + 3 类型 Config/Result/Adapter + P1A plumbing / P1B tiny 端到端 / P1C full-size 1/3/10 smoke / P1D small loopy + 边内存估算 + 5态2态`，`PLAN_CANDIDATE/SYNTHETIC_ONLY/EXECUTE_NOT_AUTHORIZED`，不跑 decoder，不改 V70/V72P0，不启 V72）；`V72P1` 本身不直接进入 V72 qualification；任何 decoder / 真码率 V72 需另起 `EXECUTE_AUTH`。
