# OpenSpec Proposal: REDO V72P0 — retain LOCAL_FACTOR_KERNEL_PASS; P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover no true self-compare; P0B sparse CSR IRA 9036x10240; 5-state ADAPTER_PLAN_READY needs 3 passes

# OpenSpec Proposal: formal-ir-v72p0-soft-joint-binary-synthetic

**Status**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — 仅计划四工件 + 合成校验链条 correctness（1024→10bit local factor ↔ binary LDPC mother BP incremental syndrome exact 64-bit tag），冻结 Q1024 N1024 Nbit10240 M2 required9036 f1.3 f_actual NOT_MEASURED 2M禁止，local factor 去 self-message LLR定义 8测试，backend 只读审计6问分三态（不字符串判READY），synthetic P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exact + P0B 1024 synthetic mother 9036×10240 nested rank，5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2)，T0-T3 矩阵，不跑 decoder 不改 V70/V70R1/V71

**Domain**: Formal IR / soft-joint binary synthetic correctness (V70 二进制 soft-joint 因子 + V71 纯因子核直接后继，V70R1 参数化模型对照已完成)

**Change ID**: `formal-ir-v72p0-soft-joint-binary-synthetic`

**Cycle ID**: `V72P0-SYN` (soft-joint-binary-synthetic P0), predecessor `formal-ir-v71-soft-joint-factor-kernel` (`V71-SJK` latest `487be11387a5a68c275c43ccb5528ec700bfd3d3` `KERNEL_ADAPTER_FEASIBLE`) + `formal-ir-v70-binary-soft-joint-feasibility` (`9bc34be64a2822c8babb4320efb47fc7e335a21a` `PARTIAL_SESSIONS_FEASIBLE`) + `formal-ir-v70r1-parametric-channel-model-check` (`0509d10ba78902b36f6bcf447f1ebfe289e03fc89b` `CHANGES`)

**Branch**: `formal-ir-mainline`

**HEAD**: `9b7f27a25cdd74e0924ecfd05187339e7f11e165` (动态绑定 `git rev-parse HEAD`; `origin/formal-ir-mainline == HEAD` 40位重核，不一致阻塞；predecessor V71/V70 数值只读，不改)

**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点 provenance；V72P0 **SYNTHETIC_ONLY**：real pairs 不参与 P0A/P0B 估计，`synthetic_v72p0` 合成注册表独立，2M real 禁止)

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + decoder-free 合成审计（`v72p0_data_registry_synthetic.json` + `scripts/v72p0_soft_joint_binary_synthetic.py` + `scripts/v72p0_backend_audit.py` + `v72p0_results.json` + `v72p0_table.csv/.json` + `V72P0_SYN_REPORT.md` + `V72P0_BACKEND_AUDIT_REPORT.md` + `test_v72p0_*.py` + `v72p0_manifest.json`）+ 只读 backend A1-A6 三态 + P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exhaustive + P0B 9036×10240 mother nested rank，5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2)，**不创建 `run_01`，不执行 decoder，不构业务 disclosure，不改 src/V70/V71，只读合成，不启 V72**

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 合成 spike（`numpy` 直算 1024 枚举 log-domain + 按 bit 去 self-message `logsumexp`，`scipy/numba/sklearn` 不引）+ 1 只读 backend 审计脚本（AST/import 探针，三态 enum 非字符串，`rg "decode_" 0 hits`）+ 1 小 mother 矩阵构造器（9036×10240 GF2 高斯消元，prefix nested）+ 1 结果表 JSON + 双报告 + 1 小测试；零 decoder/real-data 扫描/新依赖，最短合成路径。laziest alternative: `numpy` + `logaddexp.reduce` 手写，不引外部数值库。

> **科学问题（冻结）**：于**完全冻结主体**（`Q=1024, N=1024 symbols/block, Nbit=10240 bits/block (10·N), M2 required=9036 rows, GF2 mother 9036×10240, f=1.3 frozen f_actual NOT_MEASURED, full-symbol 64-bit tag `SHA256(s_hat)[:8B] = SHA256(bit_hat)[:8B] exact`，**不改维度/q/GF/验证**）下，**验证 1024→10bit local factor ↔ binary LDPC mother BP incremental syndrome exact 64-bit tag 链条合成 correctness**：定义 **local factor 去 self-message LLR 语义**（`LLR_{→bit_i} = log P(bit_i=1)/P(bit_i=0) | prior + Σ_{j≠i} bits_j·LLR_j`，纯函数枚举1024态，8测试正交）+ **binary mother `9036×10240` nested prefix syndrome 族**（确切 GF2 秩 `rank(H_{0:r})==r ∀r∈Rs`，非零不重复前缀嵌套，增量 disclosure 可合成）+ **exact tag 等价**（symbol 域 64b == bit 域 64b）+ **只读 backend 6问三态** + **synthetic P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exhaustive + P0B 1024 合成 full 壁垒 gate** + **5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2) + T0-T3 矩阵**，SYNTHETIC_ONLY 不跑 decoder 不改 V70/V71。

## Goal

以最短 synthetic-only 路径完成 **local factor 去 self-message ↔ mother BP incremental syndrome ↔ exact tag 链条合成 correctness** 的可验证证据，为 V71 `ADAPTER_REQUIRED` 后是否可进入 `V72 mother code` 提供 synthesis 先验：

### 1. 冻结 Q1024 N1024 Nbit10240 M2 required9036 f1.3 f_actual NOT_MEASURED 2M禁止
- **冻结**：`Q=1024 (10-bit s∈[0,1023])`, `N=1024 symbols/block`, `Nbit=10·N=10240 bits/block`, `M2 required=9036 rows (9036×10240 mother)`，`f=1.3 frozen` 仅作 `required=ceil(1.3·N·CE_full)` 参照一致性锚点（`CE_full` 取 synthetic 先验 `≈0.8 bit/symbol` 时 `ceil≈1065` 与 `9036` 上限 gap 正交描述，不以 `9036` 反推 CE），所有 `f_actual` 字段 `== "NOT_MEASURED"`，`git diff -- src/ ==0`，**2M 禁止**：不读 `2M` session 的任何 `CAL/VAL/TEST` real pairs 作 P0 估计或母矩阵选择（`rg -i "2M|1p5M.*synthetic" 0 hits` 对 P0 路径），synthetic 注册表独立 `synthetic_v72p0`。
- **Tag 冻结**：`64-bit tag = SHA256(s_hat_bits_concatenated)[:8B]` 与 `SHA256(bit_hat)[:8B]` **exact 等价**（`s_hat = Σ bit_j<<j` 双射，byte 序 canonical `LE`），验证期不计 `+64` 泄漏到 `required/margin` 门禁，仅作 exact 性校验。

### 2. local factor 必须排除 self-message，LLR 定义 8测试正交
- **LLR 冻结**：对 symbol 先验 `log_prior[1024]` 与输入 `llr_10[10]`（来自 binary LDPC bit 节点的外信息），local factor 到 bit `i` 的外发消息 **排除 self**：
  ```
  log_unnorm_excl_i[a] = log_prior[a] + Σ_{j≠i} bits_j(a)·llr_j
  log_post_excl_i[a] = log_unnorm_excl_i[a] - logsumexp(log_unnorm_excl_i)
  llr_out_i = logsumexp_{a:bit_i=1} log_post_excl_i[a] - logsumexp_{a:bit_i=0} log_post_excl_i[a]
  ```
  全包含核 `soft_joint_factor_kernel`（`Σ_j bits_j·llr_j`）仅用于对照，二者差 `Δ_i = bits_i·llr_i` 已验。
- **8测试**（纯函数，无 I/O/随机/全局，枚举1024，log-domain，三态报告）：
  1. `T_LF01 completeness` 1024 枚举无丢 `∀s s==Σ bit_i<<i`
  2. `T_LF02 normalization` `logsumexp(log_post)==0±1e-12`
  3. `T_LF03 marginal_preservation` 全零 `llr≡0 ⇒ log_post≡log_prior` `max|Δ|<1e-12`
  4. `T_LF04 delta_concentration` 定向 `a*`（`K=1e6`）`⇒ log_post[a*]==0±1e-9` 其余 `<-1e2`
  5. `T_LF05 self_exclusion` `log_post_incl - log_post_excl_i == bits_i·llr_i ±1e-12` ∀i 且 `llr_out_i` 自洽
  6. `T_LF06 log_domain_stability` `K=1e6` 全程 `isfinite` 无 `exp overflow`（logaddexp）
  7. `T_LF07 determinism` 同输入二次 `max|Δ|==0`
  8. `T_LF08 brute_vs_kernel` 显式 1024 逐项 `Π factor` brute 对照 `max|Δ|<1e-12`（全零与 delta 两极）

### 3. backend 只读审计6问分三态，不字符串判 READY
- **对象**：`comparison_bench/src/comparison_bench/formal_ir/ldpc_v5*.py` (`ldpc_v5.py`, `ldpc_v5_development.py`, `codebook_v5_h2.py` 等) 全只读（`git diff -- .../formal_ir/ldpc_v5* ==0`），`rg "decode_" 审计脚本 0 hits`，不执行 `run_ldpc_formal_v5`。
- **6问（Q1-Q6）每问三态 `{PASS, FAIL, NOT_APPLICABLE}` enum（`IntEnum`），禁止 `if status=="READY"` 字符串判定**：
  - Q1 `interface_presence` — 导出 `run_ldpc_formal_v5 / build_v5_policy_manifest / verify_v5_policy_manifest` 等存在且签名稳定
  - Q2 `policy_manifest_schema` — `policy_sha256 / decoder_sha256 / h1_binding / mother_shape 9036×10240` 重建一致
  - Q3 `backend_model_binding` — `channel_model.model_sha256 == selection_manifest.channel_model_sha256`
  - Q4 `extrinsic_interface` — 是否暴露 per-bit `llr_ext` 注入点且 **支持 self-exclusion 语义**（探针 `plane_error_channel` 参数类型与是否过滤 self）
  - Q5 `runtime_caps` — `caps {wall_s, decoder_calls, events}` vs 合成壁垒 benchmark 兼容性描述
  - Q6 `disclosure_accounting` — `OUTCOME_FIELDS` 中 `ldpc_syndrome_bits / h1/h2 / verification_tag_bits_component / incremental_prefix` 是否可容纳 `9036` 增量 disclosure（不混 `key_dependent`）
- **分流**：`READY = Q1∧Q2∧Q3 PASS ∧ Q4 PASS(self_excl) ∧ Q6 PASS(9036可容纳)`；`ADAPTER = Q1-Q3 PASS ∧ (Q4 需适配 ∨ Q6 需扩展)`；`NOT_COMPATIBLE = Q1/Q2 FAIL ∨ T_LF01/02 FAIL`，per synthetic session 独立，**判定用 `enum == BackendState.READY` 非 `== "READY"`**（`rg '"READY"' 审计脚本 0 hits` 除注释）。

### 4. synthetic P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exact
- **范围**：synthetic 合成域 tiny 块 `k∈{2,3} n∈{6,9} (total_bits≤9, 7cover 1024, 8trials) symbols`（`Nbit_small ∈ {20,30,40}`），`Q=1024` 保持，每 `N_small` 各 `num_trials=8` 合成样本，信道为已知 synthetic 先验 `P_synth(a|b)`（`δ uniform` + `peak 0` 可配，seed `V72P0-SYN-P0A` 确定性），**exhaustive exact 校验**：枚举 `Q^{k*n}` 全码字空间（2→1M, 3→1B 采样, 4→采样 Monte-Carlo + exact tag/syndrome 小矩阵对照），校验 `local factor 去 self + 小 mother (m_small = ceil(1.3·N_small·CE_synth))` 的 `syndrome = H_small · bit_hat (GF2)` 与 `exact tag` 链条合成 correctness（`syndrome_ok ⇒ tag_ok` 或 `tag mismatch` 精确一致），`wall_s/peak_MiB` 记录。
- **门禁**：`P0A_PASS = T_LF01-08 全 PASS ∧ tiny exhaustive 0 mismatch ∧ tag exact 0 mismatch ∧ wall≤30s`。

### 5. synthetic P0B 1024 synthetic mother 9036×10240 nested rank 等 gate
- **族**：`H_mother ∈ GF(2)^{9036×10240}`（列序 `col = sym_idx*10 + bit_pos`, `bit_pos 0..9 LSB→MSB` 与 LF 位定义一致），`r0=160`（`16×10` 对应 V31 H1 二进制展开行数），`Rs = {r0, r0+Δ, …, 9036}`（Δ=8 为增量步长，若 `9036-r0` 非 Δ 整除则末段补至 `9036`，报告末行 `achieved==requested true`），增量前缀 `H_{0:r} = H_mother[0:r, :]`。
- **校验**（确切 GF2 秩，`numpy` + 纯 Python 高斯消元，`numba` 不引）：
  - `C1 rank`: `rank_{GF2}(H_{0:r}) == r ∀r∈Rs`
  - `C2 non_zero`: 每行 `weight>0`
  - `C3 distinct`: 行间 `H_i≠H_j`
  - `C4 nested`: `H_{0:r} == H_mother[0:r]` 前缀嵌套
  - `C5 incremental_disclosure`: `syndrome_r = H_{0:r}·bits (GF2)` 可增量合成（`r1<r2 ⇒ syndrome_{r2}[0:r1]==syndrome_{r1}`）
  - `C6 tag_exact`: `tag = SHA256(bits)[:8B] == SHA256(s_hat_bytes)[:8B]` exact
- **Gate**：`P0B_PASS = C1∧C2∧C3∧C4∧C5∧C6 全 PASS`，任一 FAIL 抬至 `MATRIX_RANK_FAIL / SYNDROME_NESTED_FAIL`。

### 6. 报告 wall 等 8终态 first-match
- **Per-synthetic 8终态 first-match（优先级高→低互斥）**：
  1. `V72P0_EVIDENCE_INCOMPLETE` — 物化/帧256/provenance/`C_ab` 非有限/1024枚举不足/`logsumexp` 非有限/`P0A not executed`
  2. `V72P0_MODEL_NOT_STABLE` — `T_LF03/04/05/06/07/08` 任一 FAIL 或 `ΔCE>0.50` 或 `D_bits<-1e-9`
  3. `V72P0_BACKEND_NOT_COMPATIBLE` — Q1/Q2 FAIL 或 `T_LF01/02` FAIL
  4. `V72P0_TINY_FAIL` — `P0A` tiny exhaustive 或 tag exact mismatch
  5. `V72P0_MATRIX_RANK_FAIL` — `C1/C2/C3` FAIL（秩/非零/去重）
  6. `V72P0_SYNDROME_NESTED_FAIL` — `C4/C5` FAIL（前缀/增量）
  7. `V72P0_SYNTHESIS_READY` — `T_LF01-08 全 PASS ∧ Q1-Q6 READY (enum) ∧ P0A PASS ∧ P0B PASS (C1-C6) ∧ wall≤30s ∧ peak≤2048MiB ∧ f1.3 NOT_MEASURED`
  8. `V72P0_SYNTHESIS_ADAPTER` — `T_LF01-08 PASS ∧ Q1-Q3 PASS ∧ (Q4 ADAPTER ∨ Q6 ADAPTER) ∧ P0A PASS ∧ P0B PASS ∧ wall≤30s`（需适配层）
- **Overall 2态（合成域）**：`OVERALL_READY (READY==2? P0A/P0B 两相皆 READY) / OVERALL_ADAPTER_OR_FAIL` + `6计数`。

### 7. T0-T3 矩阵
- **T0** compile/import/structural/tiny-math：双脚本 `py_compile PASS`，`import` 无 `decode_`，`T_LF01-03` 小矩阵 `|Δ|<1e-12`
- **T1** focused unit & tamper：`T_LF01-08` 8测试 + `Q1-Q6` 三态 enum mock（字符串判定 0 hits），`C1-C4` 对 9036 族前 `r0+8*2` 前缀小秩
- **T2** complete fake/test-only qualification + strict replay：`P0A` tiny 2-4 symbols exhaustive（`--fake --tiny`）+ `P0B` 前 `K=3` 秩点 + `incremental` 前 3 增量点，`--test-only` runner 显式 fake，strict replay `ok==true`
- **T3** cross-version / broad regression：`rg "decode_" 0 hits` + `V70/V71` 冻结值对照（`git diff -- openspec/changes/formal-ir-v70* ==0` 除本目录）+ `2M 未读` 回归

### 8. 本轮交付边界（四工件 + audit + spike + report，SYNTHETIC_ONLY）
- 产出 `proposal/design/tasks/specs` 四工件 + `scripts/v72p0_soft_joint_binary_synthetic.py` (`rg "decode_" 0 hits`) + `scripts/v72p0_backend_audit.py` (`rg '"READY"' 0 hits`) + `v72p0_data_registry_synthetic.json` + `v72p0_results.json` + `v72p0_table.csv/.json` + `V72P0_SYN_REPORT.md` + `V72P0_BACKEND_AUDIT_REPORT.md` + `test_v72p0_*.py` + `v72p0_manifest.json` + 控制台 8终态摘要；**禁** `decode_/construct_H*_business/gf_rank_business` 业务调用（除 P0B 秩校验 `gf_rank_pure`）、`run_01`、跨方法比较、改 `src/` baseline、读 `2M` real、字符串判 READY、启动 V72。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa/construct_H*_business/nested_business` decoder 或业务码构造（P0B 秩校验仅 `gf_rank_pure` 高斯消元，不属业务 `construct`，脚本内 `rg "decode_" 0 hits`）；不改 `Q/N/Nbit/M2/f1.3/tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不以 `required/9036` 构造业务执行 disclosure。
- 不读密封 `2M` real session 的任何 `H/CE/NLL/MAP` 统计作 `P/required/rank` 选择（synthetic only），`λ` 择优仅 synthetic `P_synth` 描述性，`2M` 违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779` 合成锚点复用）；`synthetic` 仅 `Q1024→10bit` 去 self LF + `9036×10240` 母矩阵前缀族。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank。
- 不改写/覆盖 `V70/V70R1/V71` 任何已有输出与终态（只读，`git diff -- openspec/changes/formal-ir-v70* 0 hits` 除本目录）；V71 `ADAPTER_REQUIRED` 仅复用 Stage2 形态，不重跑 Stage0/Stage1。
- 不以总体平均替代 per-synthetic 分流；不以 `V25 H` 作新域门禁，门禁用 `T_LF01-08 + Q1-Q6 enum + P0A/P0B C1-C6 + wall 30s/2GiB`。
- 不创建正式 `.../v72p0_*/run_01` decoder 执行；正式 decoder 需另起 OpenSpec + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单 soft-joint 二进制合成链条内 correctness 探查。
- **不启动 V72**：任何 `V72` `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结均禁止在本变更内声明或执行；V72P0 报告仅以 `successor ∈ {v72_mother_adapter_design, v72_tiny_refine, recollect_synthetic}` 指向，不创建 V72 目录或产出。
- 不实测 `f_actual`：所有 `f_actual` 字段 `NOT_MEASURED`，仅冻结 `f=1.3` 作参照。
- 不字符串判定 READY：`rg '"READY"'` 审计脚本 0 hits，必须 `enum == BackendState.READY`。

## Scope

1. **冻结主体与合成锚点零改（1024维符号二进制合成扩展，仅链条验证）**：`Q1024 N1024 Nbit10240 M2 9036 required9036 f1.3 full-tag canonical leak Σw_i·m_i+64` 全只读；`84d62779 legacy_v1` 单点合成锚点；`2M 禁止`；不引 V72P0 新码本以外的表示。
2. **local factor 去 self-message LLR 定义 + 8测试**：`T_LF01 completeness / T_LF02 normalization / T_LF03 marginal / T_LF04 delta / T_LF05 self_exclusion / T_LF06 stability / T_LF07 determinism / T_LF08 brute 1e-12` 逐项 `PASS/FAIL`，任一 FAIL 抬至 `MODEL_NOT_STABLE` 或 `BACKEND_NOT_COMPATIBLE`（T_LF01/02 属后者）。
3. **只读 backend 6问三态审计**：`Q1 interface / Q2 policy_manifest / Q3 backend_model_binding / Q4 extrinsic_interface(self_excl) / Q5 runtime_caps / Q6 disclosure_accounting(9036)` 六项每 synthetic 独立 `PASS/FAIL/NOT_APPLICABLE` enum，输出 `READY/ADAPTER/NOT_COMPATIBLE` 分流，不执行 `run_ldpc_formal_v5`，**禁止字符串 `"READY"` 判定**。
4. **synthetic P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exact**：tiny 合成块 `total_bits≤9 k2/3 n6/9` exhaustive `Q^{k*n}` 或采样 + 小 `H_small` 增量 syndrome + exact tag `0 mismatch`，`wall≤30s`。
5. **synthetic P0B mother 9036×10240 nested rank 等 gate**：`H_mother 9036×10240` 列序 `sym*10+bit`，`r0=160 Δ8 →9036` 前缀嵌套确切 GF2 秩 `rank==r` + 非零/去重/前缀/增量/tag exact `C1-C6`。
6. **5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2) + overall 2态**：每 synthetic `EVIDENCE > MODEL > BACKEND_NOT_COMPATIBLE > TINY_FAIL > MATRIX_RANK_FAIL > SYNDROME_NESTED_FAIL > READY > ADAPTER` 互斥；overall `READY(全READY)/ADAPTER_OR_FAIL` + `8正交计数`。
7. **T0-T3 矩阵**：T0 compile/import/structural/tiny-math；T1 focused unit & tamper；T2 complete fake/test-only qualification + strict replay；T3 cross-version regression（V70/V71 只读 + 2M 未读）。
8. **四工件 + 双报告交付（SYNTHETIC_ONLY）**：`scripts/v72p0_soft_joint_binary_synthetic.py` + `scripts/v72p0_backend_audit.py` (`rg "decode_" 0 hits`, `rg '"READY"' 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`) 输出 `v72p0_results.json + v72p0_table.{csv,json} + V72P0_SYN_REPORT.md + V72P0_BACKEND_AUDIT_REPORT.md` + 控制台摘要，未创建 `run_01`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v72p0-soft-joint-binary-synthetic/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v72p0_soft_joint_binary_synthetic.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`) + `scripts/v72p0_backend_audit.py` (`rg '"READY"' 0 hits`, `rg "decode_" 0 hits`, 三态 `IntEnum`) + 冻结合成注册表 `v72p0_data_registry_synthetic.json` (`schema v72p0_synthetic_v1`, `Q1024 N1024 Nbit10240 M9036 f1.3`) + `v72p0_results.json` (per synthetic `T_LF01-08/Q1-Q6/P0A/P0B C1-C6/wall` + overall 2态) + `v72p0_table.csv/.json` (每行 `synthetic_case/T_LF/Q/wall/peak/rank_ok/classification` + 总体) + `V72P0_SYN_REPORT.md` + `V72P0_BACKEND_AUDIT_REPORT.md` + `test_v72p0_soft_joint_binary_synthetic_small.py` + `v72p0_manifest.json` + 控制台摘要。
- **只读依赖**：`v71_data_registry.json / v70_data_registry.json`（形态对照，不参与 P0 估计）+ `comparison_bench/src/comparison_bench/formal_ir/ldpc_v5*.py` (`Q1-Q6` 只读探针) + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V70/V70R1/V71` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零 real 扫描，不启动 decoder，不重估计 V70/V71，不启动 V72**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD 9b7f27a25cdd74e0924ecfd05187339e7f11e165` (动态绑定 `git rev-parse HEAD == origin/formal-ir-mainline` 重核) + `data 84d62779 + synthetic_v72p0` + `predecessor V71 487be113 / V70 9bc34be6 / V70R1 0509d10b` 已绑定，显式声明 SYNTHETIC_ONLY、零 decoder/real 扫描、Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止、local factor 去 self 8测试、backend 6问三态非字符串 READY、P0A tiny total_bits≤9 k2/3 n6/9 exhaustive exact、P0B 9036×10240 nested rank、5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2)、T0-T3、四工件产出。
- [ ] **冻结主体零改已验**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v70* ==0 && git diff -- openspec/changes/formal-ir-v71* ==0`（除本目录+`scripts/`），`Q1024 N1024 Nbit10240 M9036 f1.3 full-tag 64b exact` 全只读，`2M` 未读（`rg -i "2M" synthetic 脚本 0 hits` 除禁止声明），`rg "decode_" 0 hits` 已验。
- [ ] **local factor 去 self-message LLR 定义 8测试已验**：`LLR→bit_i` 定义 `Σ_{j≠i} bits_j·llr_j` 冻结，`T_LF01 completeness / T_LF02 normalization / T_LF03 marginal / T_LF04 delta / T_LF05 self_exclusion / T_LF06 stability / T_LF07 determinism / T_LF08 brute 1e-12` 逐项 `PASS/FAIL` 已在 synthetic P0A/P0B 上校验且与 `v72p0_results.json` 一致，`K=1e6` 时 `isfinite` 且 `max|Δ|<1e-12`，`rg '"READY"' 0 hits` 对 LF 脚本已验。
- [ ] **只读 backend 6问三态已验**：`Q1 interface_presence / Q2 policy_manifest_schema / Q3 backend_model_binding / Q4 extrinsic_interface(self_excl) / Q5 runtime_caps / Q6 disclosure_accounting(9036)` 每 synthetic 独立三态 `PASS/FAIL/NOT_APPLICABLE` enum，分流 `READY(Q1-Q6 PASS且Q4 self_excl)/ADAPTER(Q1-Q3 PASS)/NOT_COMPATIBLE(Q1/Q2 FAIL)` 已判定，`ldpc_v5*` 文件 `git diff ==0` 且脚本内 `rg "run_ldpc_formal_v5\(" 0 hits`（仅 import 探针，不执行），`rg '"READY"'` 审计脚本 0 hits 且 `if backend_state == BackendState.READY` enum 已验，落盘 `v72p0_backend_audit_report.json` 与 `V72P0_BACKEND_AUDIT_REPORT.md` 一致。
- [ ] **synthetic P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exact 已验**：`total_bits≤9 k2/3 n6/9` 各 `8 trials` exhaustive（或采样）`0 mismatch`，`syndrome = H_small·bits (GF2)` 与 `tag = SHA256(bits)[:8B]` exact `0 mismatch`，`wall≤30s ∧ peak≤2048MiB`，`v72p0_results.json:P0A` 已验。
- [ ] **synthetic P0B mother 9036×10240 nested rank 等 gate 已验**：`H_mother ∈ GF2^{9036×10240}` 列序 `sym*10+bit` 已验，`r0=160 Δ8→9036` 前缀 `rank==r` 确切 GF2（高斯消元）已验，非零 `weight>0` 去重 `H_i≠H_j` 前缀 `H_{0:r}==H_mother[0:r]` 增量 `syndrome_{r2}[0:r1]==syndrome_{r1}` tag exact `SHA256(bits)==SHA256(s_hat)` 已验，`C1-C6` 全 `PASS` 时 `P0B_PASS`，报告与 json 一致。
- [ ] **5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2) 已验**：每 synthetic `classification ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, BACKEND_NOT_COMPATIBLE, TINY_FAIL, MATRIX_RANK_FAIL, SYNDROME_NESTED_FAIL, SYNTHESIS_READY, SYNTHESIS_ADAPTER}` 按 `EVIDENCE > MODEL > BACKEND > TINY > RANK > NESTED > READY > ADAPTER` 已判定；`wall_s/peak_MiB` 已落盘，超限抬至 `EVIDENCE/TINY`（`wall>30s` 或 `peak>2048`）。
- [ ] **T0-T3 矩阵已验**：T0 `py_compile PASS` + `rg "decode_" 0 hits` + `T_LF01-03` 小矩阵 `1e-12`；T1 `T_LF01-08` 8测试 + `Q1-Q6` mock 三态 enum + 9036 族前 3 秩点 `C1-C4`；T2 fake `P0A tiny + P0B 前K秩` `test-only` 显式 fake `strict replay ok==true`；T3 `V70/V71` 只读对照 + `2M` 未读回归已验。
- [ ] **四工件 + 双报告完整**：`v72p0_data_registry_synthetic.json` + `v72p0_results.json` + `v72p0_table.csv/.json`（行对等，含 `synthetic_case/T_LF/Q1-Q6/P0A/P0B/wall/peak/classification` + `overall 2态` 汇总且与 json 一致）+ `V72P0_BACKEND_AUDIT_REPORT.md` (Q1-Q6 enum) + `V72P0_SYN_REPORT.md` (T_LF/P0A/P0B/wall) 已齐。
- [ ] `scripts/v72p0_soft_joint_binary_synthetic.py` 与 `scripts/v72p0_backend_audit.py` 为 SYNTHETIC_ONLY 可运行脚本（`rg "decode_" 0 hits`、`rg '"READY"' 0 hits`、`rg -i "met|protograph" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，`pytest -p no:cacheprovider -q test_v72p0_*` PASS），输出 `results + audit + table + 双报告` + 控制台 8终态摘要，**未创建 run_01，未构业务 disclosure，未读 2M real，T_LF01-08 已验，Q1-Q6 enum 已验，P0A/P0B 已验，wall 30s/2GiB 已验，f1.3 NOT_MEASURED 已验**。
- [ ] 已停留在 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v72p0_*/run_01`（`ls` 不存在已验）且未创建任何 `.../v72_*/run_01`，不比较，不碰 `V70/V71` 块外，未转 qualification，未启动 V72，**四工件+registry+spike+双报告已单独提交推送，返回新 Plan SHA + T_LF/Q/P0A/P0B/wall + 8终态计数 + overall 2态**，等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01 不存在/py_compile/TEST 未读/T_LF01-08 self_exclusion brute/ Q1-Q6 enum 非字符串/ P0A tiny total_bits≤9 k2/3 n6/9 exhaustive exact/ P0B 9036×10240 nested rank/8终态+wall/f1.3 NOT_MEASURED/2M 未读/V70_V71 未改`）。

## Tasks

见 `tasks.md`（Phase A 合成注册表；Phase B 冻结主体 1024→10bit 去 self；Phase C T_LF01-08 8测试；Phase D backend 6问三态；Phase E P0A tiny total_bits≤9 k2/3 n6/9 exhaustive exact；Phase F P0B 9036×10240 nested rank；Phase G 5终态 wall first-match (REDO: P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, 8trials; P0B sparse CSR IRA 9036x10240; provenance synced 9b7f27a2)；Phase H T0-T3 矩阵；Phase I 守卫 R72-01~09 + 四工件双报告 + 单独提交推送新 Plan SHA + 不启 V72）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V67-MAP` 已 `V67_FEASIBILITY_MAP_ACCEPTED` 3×`NEAR_FULL`；`V68-BAL` 均衡 5+5；`V69-3L` 三层 `37170`；`V70-BSJ` 二进制 soft-joint `PARTIAL_SESSIONS_FEASIBLE`；`V70R1` 参数化 `CHANGES`；`V71-SJK` 纯因子核 `KERNEL_ADAPTER_FEASIBLE (ADAPTER_REQUIRED)`；`V72P0-SYN` 为**二进制 soft-joint 合成 correctness P0** synthetic-only 预冻结（当前 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`：验证 1024→10bit local factor 去 self ↔ mother 9036×10240 BP incremental syndrome ↔ exact 64-bit tag 链条合成 correctness，8测试+6问三态+P0A tiny+P0B mother+8终态+T0-T3，四工件，不跑 decoder，不改 V70/V71）；`V72P0` 本身不直接进入 qualification；任何 real decoder / V72 需另起 `EXECUTE_AUTH`。
