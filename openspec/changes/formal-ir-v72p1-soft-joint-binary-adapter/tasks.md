# OpenSpec Tasks: formal-ir-v72p1-soft-joint-binary-adapter — 最小 adapter 衔接 1024 local factor 自排除 ↔ binary IRA mother 9036×10240 nnz49620 精确复用 V72P0 mother indptr/indices相等 ↔ exact 64-bit tag (PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED 本轮只四工件)

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — **10 步 S1-S10 + 3 类型 Config8字段/Result/Adapter + 4公式，P1A plumbing / P1B tiny 端到端 64/512 8trials tree-only 1e-9 c3观测 / P1C 真消息传递 9036×10240 1/3/10 iter 报告finite/maxLLR/residual 30s / P1D small loopy n12 k3 描述性，10数组 memory O(nnz+N*Q*10)，5 态 first-match AND，四工件本轮只四工件，守卫 R72P1-01~10 精确复用 V72P0 mother 不跑 decoder 不启 V72**

**HEAD**: `TBD (freeze-time git rev-parse HEAD; EXTERNAL_BINDING until Pre-RESULT)` + data `84d62779 synthetic_v72p1` — **精确复用 V72P0 mother nnz49620 indptr/indices相等 / 4公式 / Config8字段 / Δ8 vs checkpoint72 checkpoint 160 72批量 9036 max disclosed / 真消息 1/3/10 finite/maxLLR/residual / 10数组 memory O(nnz+N*Q*10) 本轮只四工件**

**Predecessor**: `formal-ir-v72p0-soft-joint-binary-synthetic 5591e16bf35b03c3df30a003bee12011a796d73e (V72P0 64ca2f1e)` + `formal-ir-v71-soft-joint-factor-kernel e038114db5095a57158b0e1cd36884d6a1a5d8be` + `formal-ir-v70-binary-soft-joint-feasibility 9bc34be6` → `V72P1-ADP` 精确复用 V72P0 mother 删新 seed

**Method frozen**: `Q1024 prior[1024,1024] N1024 Nbit10240 M9036 r0 160 Δ8 max9036 checkpoint 72批量 f1.3 NOT_MEASURED used_2m false tag64b exact SHA256 LE col sym*10+bit bit_i(s)=(s>>i)&1 LF去self Σ_{j≠i} logsumexp 4消息数组 mother 9036×10240 nnz49620 indptr/indices相等 sparse CSR IRA dual-diagonal det1 rank9036` 零改精确复用；10 步 S1-S10 + 3 类型 Config8字段 + 4消息数组 + P1A-D 四层 synthetic 真消息

**Boundary**: 仅验证 adapter 无损衔接 + 4消息数组 + Config8字段 + Δ8 vs checkpoint + 真消息传递 + 10数组 memory 复杂度，不改主体精确复用 mother；S1 synthetic_bits → S2 prior → S3 LF去self T_LF01-08 1e-12/1e-9 10数组 → S4 extrinsic打包 sym*10+bit 10数组 → S5 mother前缀 H_r 精确复用 V72P0 Δ8 vs checkpoint128 → S6 增量syndrome s_{r+8}=s_r∪new8 → S7 披露 checkpoint disclosed r+64 f NOT_MEASURED → S8 exact tag SHA256 LE → S9 10数组 memory nnz49620 CSR indptr/indices相等 peak → S10 5态 first-match AND，每 case 5 终端总体 2 态，不跑 decoder 精确复用 mother 不启 V72 本轮只四工件

## Phase A — 合成注册表占位（SYNTHETIC_ONLY，精确复用 V72P0 mother，不读 2M，不启 V72，本轮只定义不落盘）

- [ ] **A1 冻结合成注册表占位 `v72p1_data_registry_synthetic.json` 定义（本轮只四工件不产文件，下一轮落盘）**：定义 `schema v72p1_synthetic_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head TBD (freeze-time git rev-parse HEAD), reused_from v72p0_synthetic_v1 (5591e16b), successor_v72_not_started true, frozen {Q 1024,N 1024,Nbit 10240,M 9036,r0 160,delta 8,max 9036,checkpoint 160 72批量 8992 9036 disclosed,max9036,f 1.3,f_actual NOT_MEASURED,tag 64b exact, col sym*10+bit, mother精确复用 V72P0 nnz49620 indptr/indices相等 删V72P1新seed, Config8字段 {Q,N,M,r0,delta,max_r,f,tag_bits}, 4消息数组 {log_prior,extrinsic10,bit_llr,c_llr,msg_v2c,msg_c2v,var_belief,check_residual,syndrome,app_llr}, P1A {plumbing indptr/indices相等}, P1B {k2/3 n6/9 64/512 8trials tree-only c3_obs worst 1e-9}, P1C {9036×10240 nnz49620 1/3/10 真消息 finite/maxLLR/residual checkpoint disclosed}, P1D {n12 k3 12bits loopy descriptive cycle1}, edges {nnz49620 精确}, memory {10数组分项 float O(nnz+N*Q*10)}, used_2m false, used_test false}`，校验 `Q1024 N1024 M9036 nnz49620 f1.3 NOT_MEASURED used_2m false successor_v72_not_started==true indptr/indices相等`，且 `rg "V72P1新seed" 0 hits` ，且 `V72_not_started` 已显式，本轮只四工件不产 registry 文件。
- [ ] **A2 10 步 S1-S10 与 3 类型 Config8字段 与 4消息数组冻结**：在 `v72p1_manifest.json:frozen_body` 占位写入 `S1 synthetic_bits 10240 / S2 log_prior 1024 / S3 LF去self Σ_{j≠i} T_LF01-08 4消息数组 extrinsic[10][1024] 公式 / S4 extrinsic打包 sym*10+bit 10数组 / S5 mother前缀 精确复用 V72P0 nnz49620 indptr/indices相等 Δ8 vs checkpoint72批量 / S6 增量syndrome s_{r+8}=s_r∪new8 / S7 披露 checkpoint disclosed r+64 f NOT_MEASURED / S8 exact tag SHA256 LE / S9 10数组 memory nnz49620 CSR indptr/indices peak+分项 float O(nnz+N*Q*10) / S10 5态分流 first-match AND` 10 步定义，且 `AdapterConfig 8字段 {Q,N,M,r0,delta,max_r,f,tag_bits} 精确冻结` 与 `4公式` 已显式，`rg "V72P1新seed" 0 hits`，`V72_not_started` 已显式，本轮只四工件。

## Phase B — 冻结主体零改 精确复用 V72P0 mother（SYNTHETIC_ONLY，不构业务矩阵，不启 V72，本轮只四工件）

- [ ] **B1 主体明文化（逐项显式，冻结零改 精确复用 mother，不启 V72）**：在四工件中写入 `frozen_body {Q1024,N1024,Nbit10240,M9036,nnz49620 精确 indptr/indices与V72P0 byte-equal,r0 160,Δ8,max9036,checkpoint 160 72批量 8992 9036 disclosed,max9036,f 1.3,f_actual NOT_MEASURED,used_2m false,tag 64b exact SHA256 LE,col sym*10+bit,bit_i(s)=(s>>i)&1,LF 去self Σ_{j≠i} logsumexp 4消息数组,T_LF01-08 1e-12/1e-9,mother 9036×10240 nnz49620 精确复用 V72P0 indptr/indices相等 sparse CSR IRA dual-diagonal det1 rank9036 info 3-4 H_p2, Rs Δ8, checkpoint 72批量, leak disclosed r+64, adapter pack/syndrome/tag/prefix/incremental 4消息数组, 10步 S1-S10, 3类型 Config8字段/Result/Adapter, S1-S10 3类型10数组已冻结, successor_v72_not_started true}`，显式 `删 V72P1新seed 新 seed 精确复用 V72P0 mother / not Gray/not MET/protograph/SC/not H business construction/not V72 / 无1pct容差`，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- comparison_bench/src/comparison_bench/formal_ir/ldpc_v5* ==0` ，`rg "V72P1新seed" 0 hits` 。
- [ ] **B2 权威算法精确复用（SYNTHETIC_ONLY）**：SYNTHETIC_ONLY 合成 bits→H syndrome→tag→LF→wall 链路精确复用 `V72P0` 的 `legacy_v1` synthetic 生成与 `scipy.sparse CSR` 逻辑及落盘 `indptr/indices nnz49620`，不读 2M，不重写 V72P0 的 tree/small 校验；`10-bit位展开` 仅在 `a` 的 `s` 上比特置换，不改帧边界，不读 TEST，不启 V72，不执行 `run_ldpc_formal_v5`，`4消息数组 O(nnz+N*Q*10)` 已显式。
- [ ] **B3 不构业务矩阵守卫 + 精确复用 mother 守卫 + 不启 V72 守卫 + 本轮只四工件守卫**：`rg "decode_" 0 hits && rg "V72P1新seed" 0 hits` 且不调用任何业务 `H` 构造/`nested`（`ldpc_v5*` 只读探针不属业务 `construct`，仅 AST/signature 探针，精确复用 mother 无新生成），且 `rg -i "v72|qualification" 0 hits`（除 successor 注释 `V72_not_started`），且 `git diff -- openspec/changes/formal-ir-v70-binary-soft-joint-feasibility/ ==0 && git diff -- openspec/changes/formal-ir-v72p0-soft-joint-binary-synthetic/ ==0` ，`py_compile` 四工件校验；且 `ls scripts/v72p1_* 2>/dev/null | wc -l ==0` 本轮只四工件；脚注 `ponytail:` 标明 10数组 ceiling `O(nnz+N*Q*10)`。

## Phase C — 去self 8 测试 T_LF01-08（SYNTHETIC_ONLY，10 步 S3，4消息数组）

- [ ] **C1 去self 定义（S3，4消息数组核心）**：写入 `local_factor {def: "LLR_{→i}=logsumexp_{bit_i=1} Σ_{j≠i} bits_j·llr_j - logsumexp_{bit_i=0} Σ_{j≠i} extrinsic_llr[10][1024] 4消息数组核心", logsumexp: "numpy.logaddexp.reduce 手写", self_exclusion: "Σ_{j≠i}", 10array: "extrinsic_llr[10][1024] 公式显式"}`，与 `T_LF01-08` 阈 `1e-12/1e-9` 已显式，`S3` 与 `S4 打包 4消息数组` 语义一致。
- [ ] **C2 纯函数 log-domain 实现（枚举 1024，logsumexp，4消息数组，无 numba）**：在四工件中定义 `validate_local_factor(log_prior_1024, llr_10) → log_post_excl`（枚举 1024 态，`logsumexp` 实现，`i∈{0,5,9}` 三点探针，`K=1e6` 稳定性 isfinite，输出 `extrinsic_llr[10][1024]` 4消息数组），校验 `T_LF01 completeness / T_LF02 normalization 1e-12 / T_LF03 marginal 1e-12 / T_LF04 delta 1e-9 / T_LF05 self_exclusion 1e-12 / T_LF06 stability K1e6 isfinite / T_LF07 determinism==0 / T_LF08 brute 1e-12` 正交 8 test 全 PASS， `max|Δ|` 与 `isfinite`。
- [ ] **C3 落盘占位 T_LF01-08**：下一轮在 `v72p1_results.json:kernel {T_LF01..T_LF08 per case, KERNEL_PASS}` 落盘定义，本轮四工件中已显式阈与公式，`KERNEL_PASS = T_LF01∧...∧T_LF08 AND` 。

## Phase D — P1A plumbing（确定性/前缀/增量/tag，SYNTHETIC_ONLY 精确复用 mother）

- [ ] **D1 P1A plumbing 定义（S1+S4+S5+S6+S8，确定性 精确复用 mother，4消息数组）**：定义 P1A 4 probes + indptr/indices 相等校验：`pack_determinism 同输入二次 max|Δ|==0 10条消息打包 / prefix_nested ∀checkpoint∈{160,288,416,9036} H_r==H_mother[0:r] indptr/indices相等 / incremental s_{r+8} 异或一致 (s_{r+8}[0:r]==s_r 且新增 8 行独立 Δ8) / tag_exact SHA256 LE 64 samples 全 exact / indptr_indices_equal byte-equal`，各 probe `PASS/FAIL` 定义，`wall≤30s peak≤2048MiB` 阈值已显式，本轮四工件已定义。
- [ ] **D2 P1A 校验占位**：`P1A_PASS = pack_ok ∧ prefix_ok ∧ incremental_ok ∧ tag_ok ∧ deterministic_ok ∧ indptr_indices_equal ∧ wall≤30 AND 精确` 已定义，无 OR_SYM，本轮四工件已显式。

## Phase E — P1B tiny 端到端（k2/3 n6/9 64/512 各8 trials tree-only 1e-9，含负向测试，4消息数组）

- [ ] **E1 P1B tiny 定义（S1+S3+S4+S6+S8，经 adapter 端到端，tree-only，4消息数组）**：定义 `configs (k=2,n=6)→total_bits 6 exhaustive 64 与 (k=3,n=9)→total_bits 9 exhaustive 512 各8 trials 种子0..7，H_small tree forest (each var degree 1 无环) 保证无环 BP exact 4消息数组 tiny 版` 经 adapter 到 `syndrome+tag` 端到端，每 trial 计 `c1 isfinite 10条消息 finite / c2 brute exists isfinite / c3 observed_zero&&observed_one fail-closed (负向测试：observed_one==false ⇒ c3 false 且数值 64/512 wall delta 保持) / c4 brute exists / c5 BP-marg vs brute max|Δ|<1e-9 tree-only / c6 tree / c7 total≤9 exhaustive` 7 checks，全 trials 全 m 需全 PASS，且 `syndrome增量 && tag exact` 亦 PASS，`wall≤30s peak≤2048MiB` 阈值已显式，本轮四工件已定义。
- [ ] **E2 tiny tag exact + incremental 校验占位**：定义 `P1B_PASS = ∀trials ∀(k,m) c1..c7 true ∧ c3_obs true ∧ worst<1e-9 ∧ syndrome_ok ∧ tag_ok ∧ wall≤30 AND`，本轮四工件已显式。
- [ ] **E3 负向测试保留（c3 fail-closed）**：构造 `observed_one==false` 人工 case 探针 `c3==false` 且 `64/512 exhaustive 计数、wall、delta 数值保持` 定义，下一轮落盘 `negative_test`，本轮四工件已显式。

## Phase F — P1C 真消息传递 1/3/10 iter + P0B re-validate（9036×10240 sparse CSR IRA nnz49620 精确复用 mother，Δ8 vs checkpoint分离，4消息数组）

- [ ] **F1 mother 精确复用（S5，sparse CSR IRA dual-diagonal，删新 seed）**：定义 `H_mother 9036×10240 sparse CSR (scipy.sparse.csr_matrix, dtype uint8/int32) nnz=49620 prefix1111 tail4 精确值 indptr/indices与V72P0 byte-equal`，`H_p dual-diagonal (diag+subdiag) det1 ⇒ rank9036`，`info 每行 3-4 列随机`（复用 V72P0 落盘，不新生成），`rg "V72P1新seed" 0 hits` ，`nnz==49620 精确 无1pct容差` 已定义，`indptr/indices相等` 校验已定义。
- [ ] **F2 C1-C6 re-validate + checkpoint 72批量 disclosed（S5+S6+S8，精确复用 V72P0）**：定义 `C1 rank9036 (H_p det1) / C2 row_min>0 / C3 dup0 (行 hash 去重) / C4 prefix_nested H_r==H_mother[0:r] indptr/indices相等 / C5 incremental s_{r+8} 异或一致 Δ8 / C6 tag64 exact 64 samples SHA256 LE` 全 PASS，且 `checkpoint 160,288,416,...,8992,9036 72批量 max9036 上限 报告disclosed=r+64` 已定义，`disclosed` 与 `leak_r` 一致，本轮四工件已显式。
- [ ] **F3 P1C 1/3/10 iter 真消息传递（S9，三档 wall/peak/finite/maxLLR/residual/10数组/disclosed）**：定义在 `H_mother 9036×10240 nnz49620` 上对固定 `synthetic_bits 10240 种子0` 跑 `1 iter / 3 iter / 10 iter` 三档真消息传递（真迭代更新 `msg_v2c/msg_c2v/var_belief/check_residual/app_llr` 4消息数组），每档报告 `wall_s, peak_MiB 双向 streaming workspace, finite, maxLLR, residual, per_invocation_ns, nnz=49620, row_deg, col_deg, CSR_bytes, 10数组分项, syndrome_inc_ok, tag_ok, disclosed`，阈 `1 iter <1s finite==true && 3 iter <5s && 10 iter ≤30s && peak≤2048MiB` 已定义，`finite==true && syndrome增量 && tag exact` 三档全 PASS 定义，`P1C_PASS = C1-C6∧checkpoint∧1/3/10三档 wall/peak/finite/maxLLR/residual/增量/tag/disclosed 全PASS AND`，本轮四工件已定义。

## Phase G — P1D small loopy（n12 k3 含环描述性，4消息数组，不入硬门禁）

- [ ] **G1 P1D small loopy 定义（n12 k3 12bits 8 trials 含单环，4消息数组）**：定义 `n=12 k=3 total_bits 12 ×8 trials 种子0..7，H_small_loopy 含单环 (cycle_count 1, 非 tree) 4消息数组 loopy 版` 经 adapter 到 `syndrome+tag`，每 trial 报告 `syndrome_ok (H·b mod2 异或一致) / tag_ok (SHA256 LE exact) / cycle_count (DFS 手写计数 1) / BP_residual/maxLLR/finite (BP 后残差maxLLR finite 描述性) / wall`，本轮四工件已定义。
- [ ] **G2 capacity_warning 正交旗标**：定义 `capacity_warning = (cycle_count>0 || BP_residual>1e-9 || finite==false)` 正交旗标下一轮落盘，报告单独 `descriptive_diagnostics` 与 `capacity_warning` 已显式，**不入 `ADAPTER_PLAN_READY` 硬门禁**，仅描述性，本轮四工件已显式。

## Phase H — 5 态 first-match AND + 10数组 memory O(nnz+N*Q*10) + T0-T3（本轮只四工件定义）

- [ ] **H1 5 终态判定 first-match AND 精确（S10，per-case，R72P1-07 机械修正AND gate）**：`if !synthetic_bits_ok or !H_mother_exists or !indptr_indices_equal → EVIDENCE_INCOMPLETE / elif !T_LF01_02_PASS → KERNEL_FAIL / elif !P1A_PASS or !P1B_PASS → PLUMBING_TINY_FAIL / elif !P0B_revalidate_PASS or !P1C_PASS → MATRIX_SMOKE_FAIL / elif T_LF01_08_PASS∧P1A_PASS∧P1B_PASS∧P1C_PASS∧wall≤30∧peak≤2048∧finite==true → ADAPTER_PLAN_READY (需 4 硬 AND 全 PASS，P1D 仅描述，无 OR_SYM，精确 AND)` first-match 优先级已定义，每 case `classification + successor` 下一轮落盘，本轮四工件已显式，无 `OR_SYM` 误用，删除 `1pct容差`。
- [ ] **H2 总体 2 态**：`overall = ADAPTER_PLAN_READY iff ∀cases classification==ADAPTER_PLAN_READY else NOT_READY` 基于 `5 orthogonal counts {EVIDENCE/KERNEL/PLUMBING_TINY/MATRIX_SMOKE/ADAPTER_PLAN_READY: n}` 定义，下一轮落盘，本轮四工件已显式。
- [ ] **H3 10数组 memory/复杂度审计表（R72P1-06）**：定义 `audit {per_case classification, overall, 5 counts, per_case P1A/P1B/P1C/P1D, edges {nnz49620 精确,indptr/indices相等,row_deg,col_deg,zero0,dup0}, memory {CSR_bytes 278KB, 10数组分项 {log_prior8KB,extrinsic80KB,bit_llr80KB,c_llr80KB,msg_v2c388KB,msg_c2v388KB,var_belief80KB,check_residual71KB,syndrome9KB,app_llr80KB}=prior 8MiB, peak_MiB}, wall {P1A,P1B,P1C iter1/3/10 finite/maxLLR/residual, per_invocation_ns}, complexity {O(nnz+N*Q*10)=O(49620+1024*1024*10) ponytail ceiling}, checkpoint disclosed, f1.3 NOT_MEASURED, successor per case, capacity_warning}`，本轮四工件已显式，无 `1pct容差`，`O(nnz+N*Q*10)` 已标。
- [ ] **H4 T0-T3（SYNTHETIC_ONLY，四工件新增，精确复用 mother）**：`T0 compile/import/tiny-math 1e-12 (py_compile + T_LF01-08 小矩阵)` / `T1 unit & tamper 8test+enum+P1A plumbing+10条消息+indptr/indices相等+P1B负向` / `T2 fake/test-only replay (fake H_small 跑全量 64/512 不触 real 不生成新 mother)` / `T3 regression rg decode_ 0 hits && rg "V72P1新seed" 0 hits && rg "旧nnz" 0 hits && rg "1pct容差" 0 hits && V70/V72P0 只读` 已定义，本轮四工件。

## Phase I — 四工件修订 + 守卫 R72P1-01~10 + 本轮只四工件（SYNTHETIC_ONLY）

- [ ] **I1 修订 `proposal.md`** (SYNTHETIC_ONLY, 本变更目录下): 修订完成 `R72P1-01 删V72P1新seed 精确复用V72P0 mother nnz49620 indptr/indices相等 / R72P1-02 4公式 / R72P1-03 Config8字段 / R72P1-04 Δ8与checkpoint72批量分离 / R72P1-05 P1C真消息 finite/maxLLR/residual / R72P1-06 10数组memory O(nnz+N*Q*10) / R72P1-07 5态first-match AND / R72P1-08 机械修正无1pct容差 / R72P1-09 本轮只四工件`，`rg "V72P1新seed" 0 hits` `rg "decode_" 0 hits` `rg "旧nnz" 0 hits` `rg "1pct容差" 0 hits` ，保持未完成 `[ ]`，`py_compile PASS`。
- [ ] **I2 修订 `design.md`** (10步+Config8字段+10条消息+Δ8 checkpoint+真消息+10数组 memory+5态 first-match): 修订完成同上，`rg "V72P1新seed" 0 hits` `rg "旧nnz" 0 hits` ，保持未完成。
- [ ] **I3 修订 `tasks.md`** (本文件): 修订完成同上，保持未完成。
- [ ] **I4 修订 `specs/spec.md`** (守卫与验收): 修订完成同上，保持未完成。
- [ ] **I5 自检（5态 first-match AND +守卫+R72P1-01~10，本轮只四工件，精确复用 mother，不启 V72）**：`py_compile` 四工件 PASS, `rg "decode_" 0 hits`, `rg "V72P1新seed" 0 hits`, `rg "旧nnz" 0 hits`, `rg "1pct容差" 0 hits`, `rg "OR_SYM" 0 hits`, `git diff -- src/ ==0` 未改码, `git diff -- openspec/changes/formal-ir-v72p0-soft-joint-binary-synthetic/ ==0` 未改 V72P0, `git diff -- openspec/changes/formal-ir-v70-binary-soft-joint-feasibility/ ==0` 未改 V70, `T_LF 1e-12` , `Config8字段` , `4消息数组` , `Δ8 vs checkpoint 72批量` , `P1A plumbing indptr/indices相等` , `P1B 64/512 c3_obs 负向 worst<1e-9` , `P1C 1/3/10 9036×10240 nnz49620 finite/maxLLR/residual checkpoint disclosed` , `P1D loopy` 描述性, `10数组 memory O(nnz+N*Q*10)` , `5态 first-match AND` , `overall 2态` , `3类型8字段10数组` , `TEST未读 2M未读` , `V72_not_started` , 四工件一致 无 TBD（除 HEAD TBD 占位），**保持未完成 `[ ]`**。
- [ ] **I6 四工件一致性校验（无脚本小测试，本轮只四工件）**：`py_compile` 四工件 PASS，`rg "V72P1新seed" 0 hits`，`rg "旧nnz" 0 hits`，`rg "1pct容差" 0 hits`，`rg "OR_SYM" 0 hits`，`Config8字段` 校验，`4消息数组` 校验，四工件 `proposal/design/tasks/specs` 行对等一致，保持未完成。

## Phase J — 守卫 R72P1-01~10 + 本轮只四工件 保持未完成

- [ ] **J1 守卫 R72P1-01~10 落盘定义（四工件内）**：在四工件中守卫已定义，见 Design §8 / Spec §10。
  - R72P1-01 精确复用 V72P0 mother nnz49620 indptr/indices相等 删V72P1新seed 新 seed
  - R72P1-02 4公式
  - R72P1-03 Config 8字段冻结
  - R72P1-04 Δ8与 checkpoint 分离 160 72批量 末端9036 max上限 报告disclosed
  - R72P1-05 P1C真消息传递 1/3/10 iter 报告finite/maxLLR/residual
  - R72P1-06 10数组 memory 分项 float 复杂度 O(nnz+N*Q*10)
  - R72P1-07 5终态 first-match AND gate 精确
  - R72P1-08 机械修正 无1pct容差 保持未完成
  - R72P1-09 本轮只四工件
  - R72P1-10 SYNTHETIC_ONLY 不构业务矩阵 + 不读 2M/TEST + 不创 run_01 + 不改 V70/V72P0 + 不启 V72 精确复用 mother
- [ ] **J2 本轮只四工件 保持未完成 推送准备**：四工件已修订 `rg "V72P1新seed" 0 hits && rg "旧nnz" 0 hits && rg "1pct容差" 0 hits && rg "OR_SYM" 0 hits` ，**保持 `[ ]` 未勾选，不产 registry/脚本/报告/test，不创建 `run_01`，不启 V72**，四工件推送后等待独立审核（由下一轮执行推送）。
- [ ] **J3 停留 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED` + 本轮只四工件**，未创建任何 `.../v72p1_*/run_01` 且未创建任何 `.../v72_*/run_01`，未构业务矩阵，不比较，不碰 `V48-V72P0` 块外，未转 qualification，未启动 V72，仅改本目录四工件，**保持未完成，推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/2M未读/T_LF 1e-12/Config8字段/10条消息/Δ8 checkpoint 72批量/P1C 真消息 finite/maxLLR/residual/10数组 memory O(nnz+N*Q*10)/5态 first-match AND/无1pct容差/精确复用 mother nnz49620 indptr/indices相等/V72_not_started/本轮只四工件`）。

## 本变更显式禁止

decoder/业务矩阵构造（`decode_*` / `construct_*_business` / `gf_rank_business` / `nested_business` 等）；新生成 mother（`V72P1新seed` 新 seed 禁止，必须精确复用 V72P0 `nnz49620 indptr/indices相等`）；读密封 `TEST` 或 `2M` 的 `H/CE/NLL/MAP` 统计或将其用于 adapter 选择；调 `Q/N/M/f/tag/col/LF/mother/Rs/Δ/checkpoint/max` 任一冻结参数或新增业务矩阵；跨 acquisition 拼接；将 floor/round 当 ceil；将 `min(1024, ceil(...))` cap 伪装当通过；将 `+8` 外 degree/seed 网格当自适应；用 `VAL/TEST` 择优；将不足 3 伪判为 complete；将 acquisition 未去重多计；将 1024 枚举剪枝；将纯函数全零/ delta 单极当全验证（必须双极 1e-12 4消息数组）；将 `T_LF 1e-12` FAIL 当可行；将 P1C 真消息 finite/maxLLR/residual 不报告当 smoke；将 Δ8 与 checkpoint 混为一谈；将 Config 超 8字段或少 8字段；将 `1pct容差` 容差当精确；引 MET/protograph/SC/Gray（仅 adapter）；改 `src/` 基线；宣称 LDPC 证伪或 `FER/阈值/SKR/晋升`；创建正式 `.../v72p1_*/run_01`；任意 `bin_width/dimension/pairing/mapping` 网格或阈网格（处理点单点）；用第二 estimator 作门禁；覆盖已有输出；`V55 90 / V48-V72P0` 永久禁用违反；主观“显著可行”替代硬阈 `T_LF 1e-12 ∧ P1A∧P1B 真消息 1e-9 finite ∧ 10数组 memory O(nnz+N*Q*10)`；擅自调 V72P1 以外码（仅 adapter）；保留 TBD 占位不回填（除 HEAD TBD）；启动 V72（任何 `V72_*/run_01`、`QUALIFICATION_PLAN_READY`、`V72` OpenSpec 预冻结均禁止）；执行 `run_ldpc_formal_v5`（仅只读审计）；本轮超越四工件产脚本/registry/报告（本轮只四工件）。

## 验收

- proposal/design/tasks/specs 一致 `V72P0 5591e16b→新 Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED` 5 态 2 态按 first-match AND 优先级互斥明确，显式 10 步 S1-S10 + 3 类型 Config8字段/Result/Adapter + 4公式 + P1A plumbing indptr/indices相等 / P1B tiny 64/512 c3观测 1e-9 / P1C 真消息 9036×10240 nnz49620 1/3/10 finite/maxLLR/residual checkpoint 72批量 / P1D small loopy 描述性 + 10数组 memory O(nnz+N*Q*10) + checkpoint disclosed 已声明，精确复用 V72P0 mother 删新 seed，本轮只四工件 保持未完成
- 10 步数据流 + 3 类型8字段 + 4消息数组，`T_LF01-08 1e-12` ，`Config8字段 {Q,N,M,r0,delta,max_r,f,tag_bits}` ，`P1A plumbing indptr/indices相等` ，`P1B 64/512 c3观测 负向 worst<1e-9` ，`P1C 1/3/10 9036×10240 nnz49620 checkpoint disclosed finite/maxLLR/residual` ，`P1D loopy` 描述性，`10数组 memory O(nnz+N*Q*10)` ，`5态 first-match AND` ，`overall 2态` ，`wall≤30s finite==true` ，不扩，禁第二 estimator  精确复用 mother
- 合同 `Q1024 N1024 Nbit10240 M9036 nnz49620 r0 160 Δ8 max9036 checkpoint128 tag64 f1.3 NOT_MEASURED col sym*10+bit` 算法一致，`10-bit位展开` 每 case ，`S1-S10` 无丢，`4消息数组` ，`indptr/indices相等` 
- 每 case `S1 bits→S2 prior→S3 LF去self 10数组→S4 pack→S5 mother 精确复用 Δ8 vs checkpoint→S6 syndrome→S7 leak disclosed→S8 tag→S9 10数组 memory→S10 5态 first-match AND` 已定义且 `SYNTHETIC_ONLY` 精确复用 mother 不读 2M ，`P1A/B/C/D` 已定义，`T_LF` 双极 `1e-12` ，`Δ8 vs checkpoint分离` 
- 每 case `5 终端 final_classification + successor` 定义 first-match AND，`overall 2 态` 已定义
- 守卫 `R72P1-01~10` （`精确复用 mother nnz49620 indptr/indices相等 删新 seed / 4公式 / Config8字段 / Δ8与checkpoint分离72批量9036 max disclosed / 真消息1/3/10 finite/maxLLR/residual / 10数组 memory O(nnz+N*Q*10) / 5态 first-match AND / 机械修正无1pct容差 保持未完成 / 本轮只四工件 / SYNTHETIC_ONLY不构业务矩阵不读TEST不创run_01不改V70/V72P0不启V72`）
- 四工件 `rg "V72P1新seed" 0 hits` `rg "旧nnz" 0 hits` `rg "1pct容差" 0 hits` `rg "OR_SYM" 0 hits` `rg "decode_" 0 hits` `py_compile` PASS `Config8字段`  `4消息数组`  `Δ8 checkpoint`  `10数组 memory O(nnz+N*Q*10)`  `5态 first-match AND`  `finite/maxLLR/residual`  `checkpoint disclosed`  `精确复用 mother nnz49620 indptr/indices相等`  保持 `[ ]` 未完成 未建 `run_01` 未启 `V72` 已停留 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` 仅改本目录四工件（`src/` 零改），未启动 decoder/业务矩阵，本轮只四工件保持未完成

max_iter 10 total720 warm_start true float64
