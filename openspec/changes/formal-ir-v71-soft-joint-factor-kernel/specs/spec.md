# OpenSpec Spec: formal-ir-v71-soft-joint-factor-kernel

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅plan四工件 + decoder-free 1024-state 纯因子核校验完整 posterior 保留 + 只读 ldpc_v5* A1-A6 分流 READY/ADAPTER/NOT_COMPATIBLE，不改1024维符号GF32两层验证，仅验证5函数纯枚举 log-domain 因子核，不跑decoder不构业务矩阵不读TEST不启V72

**Change**: `formal-ir-v71-soft-joint-factor-kernel` (`V71-SJK`, branch `formal-ir-mainline`, HEAD `580b83e640c7e93ae7f9f7eab229eb8556cbc5a0` 动态绑定 `git rev-parse HEAD`; 已修正历史静态偏差 `历史三头` vs predecessor 9bc34be6, data `84d62779`, 3 sessions复用V69 Stage2 (E benchmark仅1M 1/9/1024 workload对应 kernel_calls 1/9/1024 各workload次 deterministic seed0), 5函数 log-domain 1024枚举, D1-D10 十不变量, A1-A6 audit 去self比较需真接口否则 ADAPTER, A3 三状态 kernel/backend/capacity 2M NO_INFORMATION (capacity FEASIBLE/MARGINAL/NO_INFORMATION), f1.3 NOT_MEASURED)

**Predecessor**: `formal-ir-v70-binary-soft-joint-feasibility` (`9bc34be64a2822c8babb4320efb47fc7e335a21a` `PLAN_CANDIDATE`) + `formal-ir-v67-multisession-feasibility-map` (`V67_FEASIBILITY_MAP_ACCEPTED`) + `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) + `binary-ldpc-v5` (`ldpc_v5*` read-only) — V71新增1024-state纯因子核 + ldpc_v5*兼容地图，5函数D1-D10 E benchmark f1.3，decoder-free，不启V72

## 1. 变更类型与生命周期

- **Type**: `PURE_FACTOR_KERNEL_COMPATIBILITY_MAP` — 于V67/V69三预注册Session的`Stage2 CAL1024+VAL256`上（E benchmark仅1M实测），验证1024-state纯因子核完整性 + ldpc_v5*兼容性：extrinsic冻结`ext=log_post-log_prior` log域差分，5函数纯枚举`log_prior/bit_factor/kernel/extrinsic/validate` log-domain 全零得marginal delta得确定值与brute-force对照`|Δ|<1e-12`，D1-D10 十不变量正交完备，A1-A6 READY/ADAPTER/NOT_COMPATIBLE，`1M`上`1/9/1024 block` `wall≤30s/peak≤2GiB`路由阈，`f1.3 freeze f_actual NOT_MEASURED`，每session 6终端总体4态。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于plan四工件 + decoder-free地图（`v71_data_registry.json + v71_soft_joint_factor.py + v71_ldpc_v5_audit.py + v71_results.json + v71_audit_report.json + v71_table.{csv,json} + V71_KERNEL_REPORT.md + V71_AUDIT_REPORT.md + test_v71_soft_joint_factor_kernel_small.py + v71_manifest.json`），**不实现runner，不执行decoder，不构业务矩阵，不创建`run_01`，不读VAL/TEST择优，不改1024维主体/V67/V69/src，不启动V72**；正式`run_01`需独立`PLAN_ACCEPT` + `EXECUTE_AUTH`；`DECODER_FREE`表示零`decode_*`业务调用（`rg 0 hits`），`V72_NOT_STARTED`表示零`V72_*/run_01`且`rg -i "v72|qualification" 0 hits`（除successor注释）。
- **Branch**: `formal-ir-mainline`；`HEAD` `580b83e640c7e93ae7f9f7eab229eb8556cbc5a0` (动态绑定 `git rev-parse HEAD`; 已修正历史三头偏差 `历史三头` vs predecessor `9bc34be6`，`git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞) 已与 `git rev-parse HEAD` 一致。`TBD` 0 hits。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) — V71复用V69三session Stage2 (`CAL1024+VAL256`)，但E benchmark仅1M实测，不换点，不启V72。
- **Session bound**: `total 3 (=V69 3)`复用，`per_category 1,1,1`，E benchmark仅`1M`实测，不新增acquisition。
- **Rate feasibility**: **f=1.3 freeze, required=ceil(1.3·N·CE_full^{VAL_1M}), f_actual NOT_MEASURED**，仅作A6 disclosure参照，不入核门禁。
- **Search space**: `1024`枚举5函数纯核（全零/ delta双极）+ `D1-D10`十不变量 + `A1-A6`六项 audit + `1/9/1024 block` benchmark。
- **V72**: **NOT_STARTED** — 本变更内禁止任何`V72` `QUALIFICATION_PLAN_READY / run_01 / 阈/码族`预冻结或产出。

## 2. 冻结方法（主体完全冻结，V71零改，仅验证纯因子核，不启V72）

### 2.1 主体不变量（V64完全冻结，V67/V69零改，V71仅核验证）

- `n=1024 symbols/block` (`4×256 frames`), `q=1024 (10-bit s)`, `GF32 poly37`, `tag=64 bits/block`。
- `H1 = V31-H1-QC 16×1024 rank16 80b`母矩阵；`U自然 =32*U1+U2, F03 5+5`（`U1>>5, U2&31`）二层参照；`10-bit位展开 bit_i(s)=(s>>i)&1, i=0..9`与`extrinsic = log_post - log_prior`冻结。
- `Lane C` ordinal-2 `s38310x`：`m2 base 1M 184 / 1p5M 190 / 2M 192`全冻。
- `H_inc1 8×1024 + H_joint1 192×1024` nested；`H_inc2 8×1024 + H_total 200×1024` nested；`rank_total==m2+16`等全冻，**本变更不构业务H**（仅纯因子核，不属业务码）。
- `decoder`: `decode_row_layered_fftqspa` `90/1.0 poly37 early-stop` (禁用至后续授权)；`rescue=verification-only`。
- `leak`: `leak = Σw_i·m_i+64`（二层参照），验证期仅`f1.3 required`作A6参照，不cap；`full-symbol tag s_hat compute`单64b。
- `budget 地图预冻结`: `V67/V69 Stage2 CAL1024+VAL256`每session，`TEST`密封，`f1.3 freeze f_actual NOT_MEASURED`，`D1-D10`正交，`A1-A6`分流，`1M 1/9/1024 30s/2GiB`路由阈。
- `V67终态`: `3× NEAR_FULL`二层natural已固化，V71以纯因子核完整性 + ldpc_v5*兼容为检验假设。
- `V72`: **NOT_STARTED** — 禁止本变更内任何V72预冻结。

### 2.2 处理点与物化单点冻结

- `84d62779`语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，多session provenance，各session单独物化后位展开 + 5函数核。
- `TEST`密封：任何`TEST/EVAL`域不计`CE/D/required/D1-D10/A1-A6/E benchmark`；`C_ab/P/CE/D1-D10/A1-A6/E`均`CAL/VAL`测，`TEST`不读，`f_actual NOT_MEASURED`，`V72`不启。
- **5函数纯因子核**：`log_prior_from_posterior / bit_factor_from_llr / soft_joint_factor_kernel / extrinsic_from_logs / validate_kernel` 枚举1024态 log-domain，禁`Gray/MET/protograph/SC`外的重表示。

### 2.3 禁止

- 禁改任一冻结量、新增业务矩阵/标签/prior/阈值/decoder、试`Δ8`外degree/seed网格、跨acquisition拼接凑`3`、将`min(1024,ceil)` cap伪装当通过、将`VAL`数据用于`λ`择优、将零重叠仅比`frame_id`、引`MET/protograph/SC/Gray`、改`src/experiments/tools`任何文件；禁读`TEST`统计；**f_actual不实测**（`NOT_MEASURED` 显式）；禁5函数单极校验（必须全零+ delta双极`1e-12`）；禁`D1/D2 FAIL`可行；禁`D1-D10`非正交混计；禁`A1/A2 FAIL`可行；禁`f_actual`实测当门禁；禁执行`run_ldpc_formal_v5`；禁`1M`外 benchmark 当路由；禁构业务`H/matrix/rank/nested`；未授`EXECUTE_AUTH`前禁`decode_*`业务；**禁启V72**。

## 3. Phase A — 数据角色 (V69 Stage2复用，E benchmark仅1M，不启V72)

### 3.1 角色与零重叠（键`(source,session,frame)`复用）

| 集合 | 每session规模 | 说明 |
|---|---|---|
| Stage2 CAL (Phase A) | 1024 frames (262144 pairs) | `C_ab→P_global→P(a|b) λ→D8 chain` + D1-D10 准备 |
| Stage2 VAL (Phase D/E) | 256 frames (65536 pairs) | `D1-D10 VAL确认 + 1M VAL 1/9/1024 benchmark + f1.3` |
| TEST | 密封不读 | `used_test==False`，V72不启 |
| ldpc_v5* | 只读探针 | `A1-A6 audit` 对象 |

- **复用**：`v71_data_registry.json`由`v69_data_registry.json` Stage2原样复用`sessions[3]`，`per_category 1,1,1`，`acquisition_dedup_verified:true`，`successor_v72_not_started:true`，**E benchmark仅1M实测**。
- **零重叠**：`CAL_key∩VAL_key==∅ && (CAL∪VAL)_key ∩ (V13..V70)_key ==∅`（键`(source,session,frame)`），`not_cross_spliced:true`。
- **注册表**：`v71_data_registry.json` (`schema v71_data_v1`)含`sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE, reused_from v69, successor_v72_not_started}`，禁止事后换session。
- **位展开**：`bit_i(s)=(s>>i)&1, i=0..9`已验双射。

### 3.2 数据就绪门

- `total==3 && per_category 1,1,1 && acquisition_dedup_verified && successor_v72_not_started`否则`EVIDENCE_INCOMPLETE`。
- `|CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ && (CAL∪VAL)∩(V13..V70)==∅`否则`EVIDENCE_INCOMPLETE`。
- `frame 256` + `s∈[0,1023]`已验，否则`EVIDENCE_INCOMPLETE`。
- `10-bit位展开无丢：s == Σ bit_i<<i ∀s`已验，否则`EVIDENCE_INCOMPLETE`。
- `ldpc_v5* files exist && git diff ldpc_v5* ==0`否则`EVIDENCE_INCOMPLETE`。

## 4. Phase B — 输入合同 strict V56 (仅5函数纯因子核)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, U自然 32*U1+U2 5+5参照, 10-bit位展开 bit_i(s), extrinsic冻结 ext=log_post-log_prior, 5函数纯枚举 log-domain, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256`落`v71_manifest.json`。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U (natural) → bit_i展开 → 5函数核 → D1-D10`原样复用，不重写。
- **不GE/MET/V72**：`rg -i "met|protograph|sc_coupling|v72|qualification" 0 hits`已验（纯因子核注释 + `V72_not_started`除外），`V72_not_started`已显式。

## 5. Phase C/D — 5函数纯因子核 + D1-D10 十不变量 + A1-A6 + f1.3（CAL选VAL确认一次，不启V72）

### 5.1 C_ab与P_global (1M CAL-only per session 描述性)

```
C_ab[a,b] = bincount2d(a_cal_1M, b_cal_1M)  1024×1024, sum 262144 (CAL1024 1M)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, N=1024
```

### 5.2 5函数纯因子核（extrinsic冻结，枚举1024，全零/ delta brute 1e-12）

```
extrinsic_def: ext[a] = log_post[a] - log_prior[a]  # log域差分，不含信道因子

1: log_prior_from_posterior(log_P_a_given_b: float[1024]) -> log_prior[1024]
   # log_P_a_given_b = log P(a|b) (自然对数)，归一校验 logsumexp==0±1e-12
2: bit_factor_from_llr(llr_10: float[10]) -> log_factor[1024]
   # log_factor[a] = Σ_{i=0..9} bits_i(a)*llr[i]  bits_i=(a>>i)&1
3: soft_joint_factor_kernel(log_prior[1024], llr_10[10]) -> log_post[1024]
   # log_unnorm[a]=log_prior[a]+log_factor[a]
   # log_post[a]=log_unnorm[a]-logsumexp(log_unnorm)
4: extrinsic_from_logs(log_prior[1024], log_post[1024]) -> extrinsic[1024]
   # extrinsic[a]=log_post[a]-log_prior[a]
   # 校验: logsumexp(log_prior+extrinsic)==0±1e-12
5: validate_kernel(log_prior, llr, log_post, extrinsic) -> {D1..D10}

brute_force: 显式Π_i factor枚举1024态后 logsumexp 归一，与 kernel 逐项 max|Δ|<1e-12
  all_zero: llr≡0 ⇒ log_factor≡0 ⇒ log_post≡log_prior
  delta: 对a*, llr_i=(+K if bit_i(a*)=1 else -K), K=1e6 ⇒ 仅a* 项最大 ⇒ posterior退化a* (log_post[a*]=0 其余=-inf)
```

- ponytail: `numpy.logaddexp.reduce`实现`logsumexp`，`K=1e6`的`exp`溢出用log域避免；`delta`验证取`a*=0,511,1023`三点，`logsumexp`需显式。
- `λ`择优：`λ∈[1e-2,1e4] log10`仅`1M CAL内4-fold`最小`CV NLL`，触界则`MODEL_NOT_STABLE`，不扩网格。`VAL`测时`λ`固定为`CAL`择优值，不重选。
- `TEST`隔离：任何V72预冻结禁止，`used_test==False`已验。

### 5.3 D1-D10 十不变量（正交完备）

```
D1 completeness: len(log_post)==1024 && ∀a a==Σ bit_i(a)<<i
D2 normalization: |Σ exp(log_post)-1|<1e-12 && |logsumexp-0|<1e-12
D3 marginal_preservation: llr≡0 ⇒ max|log_post-log_prior|<1e-12
D4 delta_concentration: llr定向a* ⇒ log_post[a*]==0±1e-9 && 其余<-1e2
D5 extrinsic_consistency: ext==log_post-log_prior && |logsumexp(log_prior+ext)-0|<1e-12
D6 log_domain_stability: K=1e6 全程 isfinite 且无 exp overflow
D7 determinism: 同输入二次 max|Δ|==0
D8 chain_closure: |CE_full - (ΣCE_bit - D_bits)|<1e-9 (复用1M P(a|b)，仅校验)
D9 test_isolation: used_test==False && rg TEST 0 hits
D10 orthogonality: 十项正交分解，任一FAIL不掩盖他项
```

### 5.4 f1.3 冻结 f_actual NOT_MEASURED（1M VAL参照，仅A6对照）

```
CE_full^{VAL_1M}= - (1/|VAL_1M|) Σ_{(a,b)∈VAL_1M} log2 P(a|b)  bits/symbol, VAL256 65536 pairs
required= ceil(1.3·N·CE_full^{VAL_1M})  N=1024 bits/block integer
f_actual = "NOT_MEASURED"  # 冻结不测，门禁不以 f_actual 判
# A6 披露对照：required vs ldpc_v5 h1+h2+tag 描述性 gap
```

### 5.5 A1-A6 只读 audit（per session，不执行 decoder）

```
A1 interface_presence: AST探针 ldpc_v5.py 导出 5 函数且签名稳定 PASS/FAIL
A2 policy_manifest_schema: policy_sha256/decoder_sha256/h1_binding 重建一致 PASS/FAIL
A3 backend_model_binding: channel_model_sha256 == selection_manifest.channel_model_sha256 PASS/FAIL
A4 extrinsic_interface: error_channel list[float] 且 plane_error_channel 可注入 extrinsic PASS/FAIL
A5 runtime_caps: caps {wall_s 10, decoder_calls 20, events 32} 兼容性 PASS/FAIL
A6 disclosure_accounting: OUTCOME_FIELDS 含 ldpc_syndrome_bits/h1/h2/verification_tag_bits_component PASS/FAIL

分流:
  READY = A1-A6 全 PASS
  ADAPTER = A1-A3 PASS 且 (A4 FAIL 或 A6 需适配)
  NOT_COMPATIBLE = A1/A2 FAIL 或 D1/D2 FAIL
```

### 5.6 E — 仅1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈

```
# 仅1M session 实测
for block in [1,9,1024]:
  wall_s, peak_MiB = benchmark(soft_joint_factor_kernel, 1M_VAL256, block, {llr_zero, llr_random})
E_PERF_PASS = (wall_1024 ≤30.0 && peak_1024 ≤2048)
report: per block {wall_s, peak_MiB, per_invocation_ns}
```

## 6. Phase G — 分流与总体 (per-session 6终端 + 总体4态，CAL选VAL确认一次)

### 6.1 Per-session 6终端 first-match（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or D9 FAIL or C_ab_nonfinite:
    classification = V71_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary or |CE^{VAL}-CE^{CV}|>0.50 or val_b_unseen>0.01 or D_bits<-1e-9 or D3/D4/D5/D6/D7 FAIL or D8 FAIL:
    classification = V71_MODEL_NOT_STABLE; successor = recollect_or_new_prior
elif A1 FAIL or A2 FAIL or D1 FAIL or D2 FAIL:
    classification = V71_NOT_COMPATIBLE; successor = v71_new_representation
elif D1-D10 全 PASS && audit==READY && E_PERF_PASS:
    classification = V71_KERNEL_READY_FEASIBLE; successor = v71_ldpc_v5_integration
elif D1-D10 全 PASS && audit==ADAPTER && E_PERF_PASS:
    classification = V71_KERNEL_ADAPTER_FEASIBLE; successor = v71_kernel_adapter_design
else: # E_PERF_BLOCKED 或残差
    classification = V71_KERNEL_HEAVY; successor = v71_kernel_adapter_design_or_downscale
```

- `capacity_warning` 正交，仅描述不过门禁。

### 6.2 总体4态

```
ready_count = #{sess | KERNEL_READY_FEASIBLE}
adapter_count = #{sess | KERNEL_ADAPTER_FEASIBLE}
heavy_count = #{sess | KERNEL_HEAVY}
not_compatible_count = #{sess | NOT_COMPATIBLE}
evidence_count = #{sess | EVIDENCE_INCOMPLETE}
model_count = #{sess | MODEL_NOT_STABLE}
if any EVIDENCE_INCOMPLETE:
    overall = V71_OVERALL_EVIDENCE_INCOMPLETE
elif any MODEL_NOT_STABLE and (ready_count+adapter_count)==0:
    overall = V71_OVERALL_MODEL_NOT_STABLE
elif ready_count==3:
    overall = V71_OVERALL_KERNEL_READY
else:
    overall = V71_OVERALL_KERNEL_ADAPTER_OR_HEAVY
counts_per_classification = {EVIDENCE, MODEL, NOT_COMPATIBLE, READY, ADAPTER, HEAVY}
audit = {per_session_classification[3], overall, ready/adapter/heavy counts, D1-D10[3], audit_A1-A6[3], E_benchmark_1M, f1.3, f_actual NOT_MEASURED}
```

## 7. Phase H — 报告与表 (per session 5函数 + D1-D10 + A1-A6 + E benchmark + overall 4态)

- **表schema** (`v71_table.csv/.json`行对等, 每session 1行 + 总体4态汇总):
```
session_id, acquisition_id, source_label, provenance,
CAL: CAL_lambda, CAL_lambda_at_boundary, CAL_CE_full, CAL_D_bits, CAL_val_b_unseen,
VAL: CE_full, D_bits, chain_delta, ValNLL, DeltaCE,
kernel: pure_brute_maxΔ_all_zero, pure_brute_maxΔ_delta_a0/a511/a1023, pure_is_pure,
D1..D10 per session (PASS/FAIL), audit_A1..A6 per session (PASS/FAIL), audit_classification (READY/ADAPTER/NOT_COMPATIBLE),
benchmark_1M: wall_1, peak_1, wall_9, peak_9, wall_1024, peak_1024, per_invocation_ns, E_PERF_PASS,
f1.3: CE_full_1M, required_1M, f_actual NOT_MEASURED,
classification (6终端), successor, overall 4态
```
- **报告双报告**：
  - `V71_KERNEL_REPORT.md`：`per session 5函数/D1-D10/1024枚举双极brute 1e-12/1/9/1024 benchmark wall/peak/per_invocation + overall 4态 + TEST隔离 + 1024维冻结 + V72_not_started`与`json/csv`一致，不扩大为`FER/SKR`。
  - `V71_AUDIT_REPORT.md`：`A1-A6 per session / READY/ADAPTER/NOT_COMPATIBLE` + overall 4态 + `f1.3 NOT_MEASURED`。

## 8. 守卫 R71-01~11

| 守卫 | 条件 | 阈值 |
|---|---|---|
| R71-01 | 冻结主体1024维纯因子核验证不改 + 不启V72 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0 && successor_v72_not_started && rg -i "v72|qualification" 0 hits` |
| R71-02 | extrinsic冻结 + 5函数纯枚举 log-domain | `ext=log_post-log_prior 冻结，5函数签名稳定，枚举1024态，全零⇒marginal delta⇒确定值 brute 1e-12，无I/O/随机` |
| R71-03 | D1-D10 十不变量正交完备 | `D1 completeness / D2 normalization / D3 marginal / D4 delta / D5 extrinsic / D6 stability / D7 determinism / D8 chain / D9 test_isolation / D10 orthogonality 逐项 PASS/FAIL 正交已验` |
| R71-04 | 只读 ldpc_v5* A1-A6 READY/ADAPTER/NOT_COMPATIBLE | `A1 interface / A2 policy_manifest / A3 backend_model_binding / A4 extrinsic_interface / A5 runtime_caps / A6 disclosure_accounting 每 session READY/ADAPTER/NOT_COMPATIBLE 已分流` |
| R71-05 | 仅1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB | `仅1M session 1/9/1024 block 各 wall/peak 已测，1024-block wall≤30s && peak≤2048MiB 判 PASS，三档 per_invocation_ns 已报告` |
| R71-06 | f1.3冻结 f_actual NOT_MEASURED | `f=1.3 frozen, required=ceil(1.3*1024*CE_full^{VAL_1M}), f_actual=="NOT_MEASURED" 全 session 已验` |
| R71-07 | V67/V69三Session Stage2复用CAL选VAL确认一次 | `v71 registry sessions==v69 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified, used_val_in_selection==False` |
| R71-08 | per-session 6终端总体4态 | `per-session EVIDENCE>MODEL>NOT_COMPATIBLE>READY>ADAPTER>HEAVY 互斥, overall EVIDENCE/MODEL/READY(3×)/ADAPTER_OR_HEAVY 已落盘` |
| R71-09 | 四工件+双报告完整 | `v71_data_registry + v71_results + v71_table.csv/json行对等 + V71_AUDIT_REPORT + V71_KERNEL_REPORT + v71_audit_report.json + test_v71_small.py py_compile+pytest PASS` |
| R71-10 | decoder-free不构业务矩阵 + 不读TEST + 不创run_01 + 不启V72 | `rg "decode_" 0 hits && rg "TEST" read 0 hits && used_test==False && run_01不存在 && py_compile PASS && V72_not_started` |
| R71-11 | 1024-state 数值闭合 | `1024 枚举 + logsumexp 归一 + K=1e6 log域稳定 + brute 1e-12 已验` |

## 9. 脚本与证据写出 (预冻结，decoder-free，不构业务矩阵，不启V72)

- **固定脚本**（本轮）：
  - `scripts/v71_soft_joint_factor.py`: `1M CAL C_ab/P/λ→D8 chain + 5函数1024枚举brute D1-D10 → 1M 1/9/1024 benchmark + f1.3 freeze → 6终端/4态`，输出`v71_data_registry.json + v71_results.json + v71_table.(csv|json) + v71_audit_report.json + V71_KERNEL_REPORT.md + V71_AUDIT_REPORT.md + v71_manifest.json`，`rg "decode_" 0 hits`，`rg -i "met|protograph|v72" 0 hits`（除V72_not_started注释），`py_compile PASS`，`D1-D10`已验，`A1-A6`已验，`1M benchmark`已验，`f_actual NOT_MEASURED`已验。
  - `scripts/v71_ldpc_v5_audit.py`: `ldpc_v5* A1-A6` 只读探针 `READY/ADAPTER/NOT_COMPATIBLE`，`rg "decode_" 0 hits`，`rg "run_ldpc_formal_v5\(" 0 hits`，`py_compile PASS`。
- **证据**：
```
openspec/changes/formal-ir-v71-soft-joint-factor-kernel/  # 本轮plan四工件
scripts/v71_soft_joint_factor.py  # decoder-free, 5函数 log-domain + D1-D10 + benchmark + f1.3
scripts/v71_ldpc_v5_audit.py  # read-only A1-A6
v71_data_registry.json (复用V69 Stage2 3 sessions, V72_not_started)
v71_results.json (per session D1-D10/audit/benchmark/f1.3 + overall 4态)
v71_audit_report.json (A1-A6 per session)
v71_table.csv/.json (每session 1行 D1-D10/audit/benchmark/classification + overall汇总, 行对等)
V71_AUDIT_REPORT.md (A1-A6)
V71_KERNEL_REPORT.md (D1-D10 + 5函数 + benchmark + f1.3 NOT_MEASURED)
v71_manifest.json (frozen_body + guards R71-01~11 + D1-D10 + A1-A6 + E)
test_v71_soft_joint_factor_kernel_small.py
comparison_bench/outputs_comparison/formal_ir_methods/v71_soft_joint_factor/  # 未来run_01 (本轮不建, V72亦不建)
```
- **文件**：`v71_data_registry.json` (authoritative `3`实表，复用V69 Stage2) + `v71_results.json` + `v71_table` (行对等) + `v71_audit_report.json` + `v71_manifest.json` (frozen_body + guards + D1-D10 + A1-A6 + E) + `V71_AUDIT_REPORT.md + V71_KERNEL_REPORT.md` + 控制台摘要；本轮仅冻结计划，不创建正式run_01，**已单独提交推送新Plan SHA**，**V72_NOT_STARTED**。

## 10. 验收

- **本轮plan自检gate（A-H已闭合，不启V72）**：`py_compile PASS` 双脚本，`rg "decode_" 0 hits`，`rg -i "met|protograph" 0 hits`，`rg -i "v72|qualification" 0 hits`（除V72_not_started注释），`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-9]/ ==0 && git diff -- openspec/changes/formal-ir-v71/ ==0` (除本变更+scripts外零改)，`VAL`未参与`λ`择优已验 (`used_val_in_selection==False`)，`TEST`未读已验 (`used_test==False`)，`f_actual NOT_MEASURED`已验，`D1-D10`已验，`5函数1024枚举双极brute 1e-12`已验，`A1-A6 READY/ADAPTER/NOT_COMPATIBLE`已验，`1M 1/9/1024 benchmark 30s/2GiB`已验，`6终端优先级互斥`已验，`overall 4态`已验，`V69 Stage2复用3`已验，`VAL确认一次`已验，`capacity_warning`正交与`descriptive`已落盘，`run_01`不存在已验，`V72_not_started`已验，**报告表与json一致**，`TBD` 0 hits。
- **本轮仅plan四工件+registry+双脚本+双报告（5函数 log-domain 1024枚举双极brute + D1-D10 + A1-A6 + 1M 1/9/1024 benchmark + f1.3 NOT_MEASURED）**，任何`V71`后的核适配/decoder需`Plan SHA` + `v71_data_registry.json`实表 + `D1-D10/A1-A6/E/f1.3`已验后、且独立`PLAN_ACCEPT` + `EXECUTE_AUTH`后才允许创建正式实现并执行；`DECODER_FREE`保持至授权，**V72保持NOT_STARTED**。
