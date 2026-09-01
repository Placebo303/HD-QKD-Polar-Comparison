# OpenSpec Spec: formal-ir-v72p0-soft-joint-binary-synthetic

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — 仅 plan 四工件 + 合成链条 correctness（1024→10bit local factor 去 self ↔ mother 9036×10240 incremental syndrome ↔ exact 64b tag），`Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止`，`T_LF01-08` 去 self 8测试 + `Q1-Q6` 三态 enum 非字符串 READY + `P0A` tiny 2-4 exhaustive + `P0B` nested rank `C1-C6`，8终态 wall first-match + `T0-T3`，不跑 decoder 不改 V70/V71

**Change**: `formal-ir-v72p0-soft-joint-binary-synthetic` (`V72P0-SYN`, branch `formal-ir-mainline`, HEAD `9b7f27a25cdd74e0924ecfd05187339e7f11e165` 动态绑定 `git rev-parse HEAD`; 2M禁止 `used_2m false`, data `84d62779 + synthetic_v72p0`, `Q1024 N1024 Nbit10240 M9036`, 去 self `Σ_{j≠i}`, `T_LF01-08` 8测试, `Q1-Q6` enum 非 `== "READY"`, `P0A k2/3 n6/9 8trials 7cover 1024` + `P0B 9036×10240 r0 160 Δ8`, `8term wall`, `T0-T3`)

**Predecessor**: `formal-ir-v71-soft-joint-factor-kernel` (`487be113` `ADAPTER_REQUIRED`) + `formal-ir-v70-binary-soft-joint-feasibility` (`9bc34be6` `PARTIAL`) + `formal-ir-v70r1-parametric-channel-model-check` (`0509d10b` `CHANGES`) — V72P0 新增合成 P0 壁垒，去 self LF + mother incremental + tag exact，synthetic-only，不启 V72

## 1. 变更类型与生命周期

- **Type**: `SYNTHETIC_CHAIN_CORRECTNESS_P0` — 于合成域 `P0A tiny total_bits≤9 k2/3 n6/9 exhaustive + P0B mother 9036×10240` 上验证链条 correctness：`去 self local factor Σ_{j≠i} bits_j·llr_j` 枚举1024态 `T_LF01-08` 正交（去 self `1e-12`）+ `Q1-Q6` 三态 enum 非字符串 READY + `P0A` `2/3/4` symbols exhaustive `0 mismatch` + `P0B` `9036×10240` `r0 160 Δ8→9036` 前缀确切 GF2 秩 `C1-C6` + `wall≤30s/peak≤2048MiB` + `f1.3 NOT_MEASURED` + 8终态 wall first-match + `T0-T3`。
- **Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + 合成审计（`v72p0_data_registry_synthetic.json + v72p0_soft_joint_binary_synthetic.py + v72p0_backend_audit.py + v72p0_results.json + v72p0_table.{csv,json} + V72P0_SYN_REPORT.md + V72P0_BACKEND_AUDIT_REPORT.md + test_v72p0_*.py + v72p0_manifest.json`），**不实现 runner，不执行 decoder，不读 2M real，不构业务 disclosure，不创建 `run_01`，不改 Q/N/Nbit/M/tag/V70/V71/src，不启动 V72**；正式 `run_01` 需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`；`SYNTHETIC_ONLY` 表示零 `decode_*` 业务调用（`rg 0 hits`）且 `used_2m==false`（`rg -i "2M" synthetic 0 hits` 除禁止声明），`V72_NOT_STARTED` 表示零 `V72_*/run_01` 且 `rg -i "v72.*run_01|qualification.*run" 0 hits`（除 `V72_not_started` 注释）。
- **Branch**: `formal-ir-mainline`；`HEAD` `9b7f27a25cdd74e0924ecfd05187339e7f11e165` (动态绑定 `git rev-parse HEAD`; `git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞) 已与 `git rev-parse HEAD` 一致。`TBD` 0 hits。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) real provenance + `synthetic_v72p0` 合成独立（P0 仅合成，不读 real `CAL/VAL/TEST`，`2M` 禁止）。
- **Synthetic bound**: `P0A total_bits≤9 k2/3 n6/9 各 8 trials (7cover 1024 exhaustive)` + `P0B mother 9036×10240  r0 160 Δ8` 合成；`2M` real 不参与。
- **Rate feasibility**: **f=1.3 frozen, required_ref≈1065（`ceil(1.3·N·CE_synth)` 近似，与 9036 上限 gap 正交），f_actual NOT_MEASURED**，仅合规参照，不入合成门禁。
- **Search space**: `1024` 枚举去 self 8测试 + `Q1-Q6` 三态 enum + `P0A k2/3 n6/9` + `P0B 9036×10240` `T0-T3`。
- **V72**: **NOT_STARTED** — 本变更内禁止任何 `V72` `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结或产出。

## 2. 冻结方法（主体完全冻结，V72P0 零改，仅合成链条，不启 V72）

### 2.1 主体不变量（V70/V71 完全冻结，V72P0 仅合成）

- `Q=1024 (10-bit s∈[0,1023])`, `N=1024 symbols/block`, `Nbit=10·N=10240 bits/block`, `M=9036 rows (9036×10240 mother)`, `f=1.3 frozen f_actual NOT_MEASURED`, `tag=64 bits exact SHA256 LE`。
- `Q→10bit` 位展开 `bit_i(s)=(s>>i)&1, i=0..9` 与 LF 去 self `Σ_{j≠i}` 冻结；列序 `col = sym_idx*10 + bit_pos LSB→MSB` 冻结。
- `2M real` 禁止：`used_2m==false`，任何 real `2M` `CAL/VAL/TEST` 不参与 P0 估计/母矩阵/wall 门禁。
- `H_mother 9036×10240` nested `r0=160 Δ8→9036`，`rank==r ∀r` 确切 GF2，`C1-C6` 冻结。
- `P0A tiny total_bits≤9 k2/3 n6/9 各 8 trials (7cover 1024 exhaustive)` exhaustive `0 mismatch` 冻结；`wall≤30s peak≤2048MiB` 冻结。
- `backend Q1-Q6` 三态 enum 非字符串 `READY` 冻结；`rg '"READY"' 0 hits` 冻结。
- `T_LF01-08` 去 self 8测试正交冻结；`P0B C1-C6` 冻结；`8终态` 冻结；`T0-T3` 冻结。
- `V72` **NOT_STARTED** — 禁止本变更内任何 V72 预冻结。

### 2.2 合成锚点单点冻结

- `84d62779` 语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256, BLOCK 1024, period 204800ps, threshold 40000ps` — 单点合成锚点（real 点仅 provenance），各 synthetic 域 `bit_i` 展开 + 去 self LF + mother 增量。
- `2M` 密封：任何 `2M` 域不计 `P0A/P0B/wall/Q1-Q6`；`real 2M` 不读，`f_actual NOT_MEASURED`，`V72` 不启。
- **去 self LF**：`log_post_excl_i[a]=log_prior[a]+Σ_{j≠i} bits_j·llr_j - logZ_excl` 枚举1024态 log-domain，禁 `Gray/MET/protograph/SC` 外的重表示。

### 2.3 禁止

- 禁改任一冻结量、新增业务 disclosure/标签/prior/阈值/decoder、试 `Δ8` 外 seed 网格、跨 synthetic/real 拼接凑、将 `min(9036,ceil)` cap 伪装当通过、将 `2M` 用于 `λ` 择优、将 Q1-Q6 字符串 `"READY"` 判 READY、引 `MET/protograph/SC/Gray`、改 `src/experiments/tools` 任何文件；禁读 `2M` real 统计；**f_actual 不实测**（`NOT_MEASURED` 显式）；禁去 self 单极校验（必须 8项正交）；禁 `T_LF01/02 FAIL` 当 READY；禁 `T_LF01-08` 非正交混计；禁 `Q1/Q2 FAIL` 当 READY；禁 `Q1-Q6` 字符串判 READY；禁执行 `run_ldpc_formal_v5`；禁 `wall>30s` 放宽当 READY；禁构业务 `H/disclosure/rank`（`gf_rank_pure` 除外）；未授 `EXECUTE_AUTH` 前禁 `decode_*` 业务；**禁启 V72**。

## 3. Phase A — 数据角色 (SYNTHETIC_ONLY, P0A tiny + P0B mother, 2M 禁止)

### 3.1 角色与零重叠（键 `synthetic_v72p0` 独立）

| 集合 | 规模 | 说明 |
|---|---|---|
| P0A tiny k=2 n=6 total_bits=6 | 8 trials ×6 bits 7cover 1024 | exhaustive 部分采样 + `H_small` 增量 tag exact |
| P0A tiny k=3 n=9 total_bits=9 | 8 trials ×9 bits 7cover 1024 | 同上 |
| P0B mother full N=1024 | 9036×10240 | nested rank C1-C6，增量 tag |
| 2M real | **密封不读** | `used_2m==false`，V72P0 不启 |
| ldpc_v5* | 只读探针 | `Q1-Q6` audit 对象 |

- **合成注册表**：`v72p0_data_registry_synthetic.json` (`schema v72p0_synthetic_v1`) 含 `synthetic_seed V72P0-SYN, P0A {k2/3 n6/9 各8 trials 7cover} P0B {mother 9036×10240 r0 160 Δ8 Rs, col sym*10+bit, successor_v72_not_started}`，禁止事后换 seed 或读 2M。
- **零重叠**：`synthetic` 键与 `(V13..V71)` real `(source,session,frame)` 零重叠。
- **位展开**：`bit_i(s)=(s>>i)&1, i=0..9` 已验双射；列序 `sym*10+bit` 已验。

### 3.2 数据就绪门

- `Q==1024 && N==1024 && Nbit==10240 && M==9036 && f==1.3 && f_actual=="NOT_MEASURED" && used_2m==false && successor_v72_not_started` 否则 `EVIDENCE_INCOMPLETE`。
- `P0A_k2_n6_trials==8 && P0A_k3_n9_trials==8 && mother_shape==[9036,10240] && Rs[0]==160 && Rs[-1]==9036` 否则 `EVIDENCE_INCOMPLETE`。
- `col_order sym*10+bit LSB→MSB` 已验，否则 `EVIDENCE_INCOMPLETE`。
- `ldpc_v5* files exist && git diff ldpc_v5* ==0` 否则 `EVIDENCE_INCOMPLETE`。

## 4. Phase B — 输入合同 strict V56 (仅去 self local factor)

- **合同项**：`Q 1024, N 1024, Nbit 10240, M 9036, col sym*10+bit, bit_i(s) 0..9, 去 self Σ_{j≠i}, tag 64b exact LE, frame256, period 204800, f1.3 NOT_MEASURED, 2M禁止` 落 `v72p0_manifest.json`。
- **权威算法**：`synthetic bits → s → H_mother syndrome (GF2) → tag SHA256 LE → LF 去 self → wall/peak` 合成链条，不读 real。
- **不GE/MET/V72**：`rg -i "met|protograph|sc_coupling|v72.*run_01" 0 hits` 已验（`V72_not_started` 除外），`V72_not_started` 已显式。

## 5. Phase C/D — 去 self LF 8测试 + Q1-Q6 三态 + P0A/P0B + wall（SYNTHETIC_ONLY，不启 V72）

### 5.1 合成先验 synthetic (SYNTHETIC_ONLY 描述性)

```
P_synth(a) synthetic 先验，δ 峰值 + uniform 背景，ε 可配
total_bits≤9 k2/3 n6/9 各 8 trials (7cover 1024 exhaustive) 独立合成，N=1024 mother 仅构造
Q=1024, N=1024, Nbit=10240, M=9036
```

### 5.2 去 self local factor（冻结，枚举1024，去 self 8测试）

```
去 self 定义: log_post_excl_i[a] = log_prior[a] + Σ_{j≠i} bits_j(a)·llr_j - logsumexp(...)

1: bit_factor_from_llr_incl(llr_10) -> log_factor_incl[1024]  # Σ_j bits_j·llr_j
2: local_factor_excl(log_prior[1024], llr_10[10], i) -> log_post_excl_i[1024]
   # log_unnorm_excl_i[a]=log_prior[a]+Σ_{j≠i} bits_j·llr_j;  log_post = log_unnorm - logsumexp
3: llr_out_from_excl(log_post_excl_i, i) -> llr_out_i
   # llr_out_i = logsumexp_{a:bit_i=1} - logsumexp_{a:bit_i=0}
4: validate_local_factor(...) -> {T_LF01..T_LF08}

brute: 显式 Π_{j≠i} factor 枚举1024态后 logsumexp 归一，与 excl 逐项 max|Δ|<1e-12
  all_zero: llr≡0 ⇒ log_post_excl_i ≡ log_prior
  delta: 对a*, llr_j=+K if bit_j(a*)=1 else -K, K=1e6 ⇒ excl 退化但保留 i 位自由度
  self_exclusion: log_post_incl - log_post_excl_i == bits_i·llr_i + ΔZ ±1e-12 ∀i
```

- ponytail: `numpy.logaddexp.reduce` 实现 `logsumexp`，`K=1e6` 用 log域避免 overflow；`self_exclusion` 对 `i=0,5,9` 三点位已验。
- `2M` 隔离：`used_2m==false` 已验。

### 5.3 T_LF01-08 八测试（正交完备）

```
T_LF01 completeness: len==1024 && ∀a a==Σ bit_i<<i
T_LF02 normalization: |Σ exp(log_post)-1|<1e-12 && |logsumexp-0|<1e-12
T_LF03 marginal: llr≡0 ⇒ max|log_post - log_prior|<1e-12
T_LF04 delta: llr定向a* ⇒ log_post[a*]==0±1e-9 && 其余<-1e2
T_LF05 self_exclusion: incl-excl == bits_i·llr_i+ΔZ ±1e-12 && llr_out_i brute 1e-12 ∀i∈{0,5,9}
T_LF06 log_domain_stability: K=1e6 全程 isfinite 无 overflow
T_LF07 determinism: 同输入二次 max|Δ|==0
T_LF08 brute_vs_kernel: 1024 逐项 brute max|Δ|<1e-12 两极 (all_zero + delta a*0/511/1023)
```

### 5.4 Q1-Q6 三态 enum 非字符串 READY（per synthetic，不执行 decoder）

```
Q1 interface_presence: AST探针 ldpc_v5.py 导出 5 函数且签名稳定 -> enum PASS/FAIL/NOT_APPLICABLE
Q2 policy_manifest_schema: policy_sha256/decoder_sha256/h1_binding/mother_shape 9036×10240 -> enum
Q3 backend_model_binding: channel_model_sha256 == selection_manifest -> enum
Q4 extrinsic_interface(self_excl): error_channel List[float] 且 plane_error_channel 过滤 self -> enum
Q5 runtime_caps: caps {wall_s, decoder_calls, events} vs wall/peak -> enum
Q6 disclosure_accounting: OUTCOME_FIELDS 含 ldpc_syndrome_bits / incremental_prefix / verification_tag_bits_component 且 9036 可容纳 -> enum

三态 BackendState(IntEnum): PASS=0, FAIL=1, NOT_APPLICABLE=2
分流 (enum 比较):
  READY = Q1 PASS∧Q2 PASS∧Q3 PASS∧Q4 PASS(self_excl)∧Q6 PASS(9036)
  ADAPTER = Q1-3 PASS ∧ (Q4 ADAPTER ∨ Q6 ADAPTER)
  NOT_COMPATIBLE = Q1/Q2 FAIL ∨ T_LF01/02 FAIL
guard: rg '"READY"' 0 hits; backend_state == BackendState.READY (enum)
```

### 5.5 P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exact

```
for k in [2,3] n in [6,9] (7cover 1024, 8trials):
  wall_s, peak_MiB = benchmark(tiny_exhaustive, k*n, 8 trials)
P0A_PASS = (0 mismatch) ∧ T_LF01-08 PASS ∧ wall≤30s ∧ peak≤2048MiB
report: per k*n {wall_s, peak_MiB, mismatch, tag_mismatch, exhaustive_coverage}
```

### 5.6 P0B mother 9036×10240 nested rank C1-C6

```
H_mother ∈ GF2^{9036×10240}, col = sym*10+bit
r0=160 Δ8 Rs = {r0+k·8 ≤9036} ∪ {9036}
∀r∈Rs: C1 rank(H[0:r])==r (GF2 高斯消元)
C2 weight>0 per row; C3 distinct rows; C4 prefix; C5 incremental; C6 tag_exact
P0B_PASS = C1∧C2∧C3∧C4∧C5∧C6
```

### 5.7 f1.3 冻结 f_actual NOT_MEASURED（synthetic 参照）

```
required_ref = ceil(1.3·N·CE_synth_ref)  ≈1065 (仅参照)
f_actual = "NOT_MEASURED"  # 冻结不测
# mother 9036 为上限能力，非 required 本身
```

## 6. Phase G — 分流与总体 (per-synthetic 8终态 + overall 2态，wall first-match)

### 6.1 Per-synthetic 8终态 first-match（优先级高→低，互斥）

```
if not materialization_ok or C_ab_nonfinite or P0A_not_executed:
    classification = V72P0_EVIDENCE_INCOMPLETE; successor = recollect_synthetic
elif T_LF03/04/05/06/07/08 FAIL:
    classification = V72P0_MODEL_NOT_STABLE; successor = refine_local_factor
elif Q1 FAIL or Q2 FAIL or T_LF01/02 FAIL:
    classification = V72P0_BACKEND_NOT_COMPATIBLE; successor = backend_refactor
elif P0A mismatch>0 or wall>30s or peak>2048:
    classification = V72P0_TINY_FAIL; successor = v72p0_tiny_refine
elif C1 FAIL or C2 FAIL or C3 FAIL:
    classification = V72P0_MATRIX_RANK_FAIL; successor = regenerate_mother
elif C4 FAIL or C5 FAIL:
    classification = V72P0_SYNDROME_NESTED_FAIL; successor = fix_incremental
elif T_LF01-08 全 PASS && backend==READY(enum) && P0A PASS && P0B PASS(C1-C6) && wall≤30s && peak≤2048:
    classification = V72P0_SYNTHESIS_READY; successor = v72_mother_adapter_design
else: # T_LF PASS && Q1-Q3 PASS && (Q4 ADAPTER ∨ Q6 ADAPTER) && P0A/P0B PASS && wall≤30s
    classification = V72P0_SYNTHESIS_ADAPTER; successor = v72_mother_adapter_design
```

- `wall/peak` 载体 `wall_s` 为 `time.monotonic` `peak_MiB` 为 `tracemalloc`/`resource`，`per_invocation_ns` 显式。

### 6.2 Overall 2态

```
ready_count = #{case | SYNTHESIS_READY}
adapter_count = #{case | SYNTHESIS_ADAPTER}
if any EVIDENCE_INCOMPLETE: overall = OVERALL_EVIDENCE_INCOMPLETE
elif ready_count==1: overall = OVERALL_READY
else: overall = OVERALL_ADAPTER_OR_FAIL
counts_per_classification = {EVIDENCE, MODEL, BACKEND, TINY, RANK, NESTED, READY, ADAPTER} 8正交
audit = {per_synthetic_classification, overall, 8 counts, T_LF01-08, Q1-Q6 enum, P0A k2/3 n6/9, P0B C1-C6, wall/peak, f1.3 NOT_MEASURED}
```

## 7. Phase H — 报告与表 (per synthetic T_LF + Q + P0A/P0B + overall 2态)

- **表schema** (`v72p0_table.csv/.json` 行对等, per synthetic 1+2 行：tiny aggregated + mother + overall):
```
synthetic_case, k*n/M, registry_synthetic_sha, Q/N/Nbit/M/f1.3,
T_LF01..T_LF08 per synthetic (PASS/FAIL, maxΔ, K),
Q1..Q6 per synthetic (PASS/FAIL/NOT_APPLICABLE enum, backend_classification READY/ADAPTER/NOT_COMPATIBLE),
P0A_k2_n6 {trials 8 mismatch wall peak coverage}, P0A_k3_n9 {...}, P0A_PASS,
P0B {mother_shape 9036x10240 r0 160 Rs wall peak C1..C6 PASS/FAIL P0B_PASS},
wall_s, peak_MiB, per_invocation_ns, f1.3 NOT_MEASURED,
classification (8终态), successor, overall 2态
```
- **报告双报告**：
  - `V72P0_SYN_REPORT.md`：`T_LF01-08 去 self / P0A k2/3 n6/9 exhaustive / P0B 9036×10240 C1-C6 / wall/peak/per_invocation + overall 2态 + tag exact + 2M未读 + Q1024冻结 + V72_not_started` 与 `json/csv` 一致，不扩大为 `FER/SKR`。
  - `V72P0_BACKEND_AUDIT_REPORT.md`：`Q1-Q6 per synthetic 三态 enum / READY/ADAPTER/NOT_COMPATIBLE (enum)` + wall + `f1.3 NOT_MEASURED`。

## 8. 守卫 R72-01~09

| 守卫 | 条件 | 阈值 |
|---|---|---|
| R72-01 | 冻结主体 Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED + 2M禁止 + 不启V72 | `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED used_2m false git diff src==0 && successor_v72_not_started` |
| R72-02 | local factor 去 self LLR 冻结 + 8测试 | `去 self Σ_{j≠i} 冻结，T_LF01-08 正交，brute 1e-12，无I/O/随机` |
| R72-03 | backend 只读 Q1-Q6 三态 enum 非字符串 READY | `Q1-Q6 每问 PASS/FAIL/NOT_APPLICABLE enum，READY 用 enum== 判断，rg '"READY"' 0 hits` |
| R72-04 | synthetic P0A tiny total_bits≤9 k2/3 n6/9 exhaustive symbols exact | `total_bits≤9 k2/3 n6/9 各8 trials 0 mismatch tag exact wall≤30s` |
| R72-05 | synthetic P0B mother 9036×10240 nested rank C1-C6 | `r0=160 Δ8→9036 前缀 rank==r 非零去重前缀增量 tag exact` |
| R72-06 | 8终态 wall first-match | `EVIDENCE>MODEL>BACKEND>TINY>RANK>NESTED>READY>ADAPTER 互斥 wall/peak 已落盘` |
| R72-07 | T0-T3 矩阵 | `T0 compile/import/tiny-math, T1 8测试+Q1-Q6 mock, T2 fake P0A/P0B 前K秩, T3 V70/V71 只读+2M回归` |
| R72-08 | 四工件+双报告完整 | `registry + results + table csv/json 行对等 + V72P0_SYN_REPORT + V72P0_BACKEND_AUDIT_REPORT + test py_compile+pytest PASS` |
| R72-09 | SYNTHETIC_ONLY 不跑 decoder 不读 2M 不创 run_01 不启 V72 | `rg "decode_" 0 hits && used_2m false && run_01 不存在 && py_compile PASS && V72_not_started` |

## 9. 脚本与证据写出 (预冻结，SYNTHETIC_ONLY，不启 V72)

- **固定脚本**（本轮）：
  - `scripts/v72p0_soft_joint_binary_synthetic.py`: `T_LF01-08 去 self → P0A tiny total_bits≤9 k2/3 n6/9 exhaustive exhaustive → P0B mother 9036×10240 C1-C6 → wall/peak + f1.3 NOT_MEASURED → 8终态`，输出 `v72p0_data_registry_synthetic.json + v72p0_results.json + v72p0_table.(csv|json) + v72p0_backend_audit_report.json + V72P0_SYN_REPORT.md + V72P0_BACKEND_AUDIT_REPORT.md + v72p0_manifest.json`，`rg "decode_" 0 hits`，`rg '"READY"' 0 hits`，`py_compile PASS`，`T_LF01-08` 已验，`Q1-Q6 enum` 已验，`P0A/P0B` 已验，`wall` 已验，`f1.3 NOT_MEASURED` 已验，`2M未读` 已验。
  - `scripts/v72p0_backend_audit.py`: `Q1-Q6` 三态 enum `READY/ADAPTER/NOT_COMPATIBLE`，`rg "decode_" 0 hits`，`rg '"READY"' 0 hits`，`rg "run_ldpc_formal_v5\(" 0 hits`，`py_compile PASS`。
- **证据**：
```
openspec/changes/formal-ir-v72p0-soft-joint-binary-synthetic/  # 本轮 plan 四工件
scripts/v72p0_soft_joint_binary_synthetic.py  # SYNTHETIC_ONLY, 去 self 8测试 + P0A/P0B + wall
scripts/v72p0_backend_audit.py  # read-only Q1-Q6 三态 enum
v72p0_data_registry_synthetic.json (Q1024 N1024 M9036 f1.3 synthetic, V72_not_started, used_2m false)
v72p0_results.json (per synthetic T_LF/Q/P0A/P0B/wall + overall 2态)
v72p0_backend_audit_report.json (Q1-Q6 per synthetic enum)
v72p0_table.csv/.json (每 synthetic 行 T_LF/Q/P0A/P0B/wall/classification + overall 汇总，行对等)
V72P0_BACKEND_AUDIT_REPORT.md (Q1-Q6 enum)
V72P0_SYN_REPORT.md (T_LF/P0A/P0B/wall + tag exact + 2M未读)
v72p0_manifest.json (frozen_body + guards R72-01~09 + T_LF + Q + P0A/P0B + wall + T0-T3)
test_v72p0_soft_joint_binary_synthetic_small.py
comparison_bench/outputs_comparison/formal_ir_methods/v72p0_soft_joint_binary_synthetic/  # 未来 run_01 (本轮不建，V72 亦不建)
```
- **文件**：`v72p0_data_registry_synthetic.json` (authoritative 合成表) + `v72p0_results.json` + `v72p0_table` (行对等) + `v72p0_backend_audit_report.json` + `v72p0_manifest.json` (frozen_body + guards + T_LF + Q + P0A/P0B + T0-T3) + `V72P0_SYN_REPORT.md + V72P0_BACKEND_AUDIT_REPORT.md` + 控制台摘要；本轮仅冻结计划，不创建正式 run_01，**已单独提交推送新 Plan SHA**，**V72_NOT_STARTED**。

## 10. 验收

- **本轮 plan 自检 gate（A-H 已闭合，SYNTHETIC_ONLY，不启 V72）**：`py_compile PASS` 双脚本，`rg "decode_" 0 hits`，`rg '"READY"' 0 hits`（审计脚本 0 hits 除注释），`rg -i "met|protograph" 0 hits`，`rg -i "v72.*run_01|qualification.*run" 0 hits`（除 `V72_not_started` 注释），`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v70* ==0 && git diff -- openspec/changes/formal-ir-v71* ==0` (除本目录+scripts 外零改)，`used_2m==false` 已验，`f_actual NOT_MEASURED` 已验，`T_LF01-08` 已验，`T_LF05 self_exclusion 1e-12` 已验，`Q1-Q6 enum 非字符串` 已验，`P0A k2/3 n6/9 0 mismatch` 已验，`P0B C1-C6` 已验，`8终态优先级互斥` 已验，`overall 2态` 已验，`wall 30s/2GiB` 已验，`T0-T3` 已验，`V72_not_started` 已验，**报告表与 json 一致**，`TBD` 0 hits。
- **本轮仅 plan 四工件+registry+双脚本+双报告（去 self 8test + Q1-Q6 enum + P0A tiny total_bits≤9 k2/3 n6/9 exhaustive + P0B 9036×10240 + 8term wall + T0-T3）**，任何 `V72` 后续 real mother/decoder 需 `Plan SHA` + `v72p0_data_registry_synthetic.json` 实表 + `T_LF/Q/P0A/P0B/wall/T0-T3` 已验后、且独立 `PLAN_ACCEPT` + `EXECUTE_AUTH` 后才允许创建正式实现并执行；`SYNTHETIC_ONLY` 保持至授权，**V72 保持 NOT_STARTED**。
