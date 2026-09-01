# OpenSpec Design: REDO V72P0 — sparse CSR IRA, 5-state

# OpenSpec Design: formal-ir-v72p0-soft-joint-binary-synthetic

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — **1024→10bit local factor 去 self-message LLR ↔ binary LDPC mother 9036×10240 BP incremental syndrome ↔ exact 64-bit tag 链条合成 correctness 合成校验，Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止，T_LF01-08 8测试正交，backend 6问三态 enum 非字符串 READY，P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols exhaustive + P0B synthetic mother nested rank C1-C6，8终态 wall first-match，T0-T3 矩阵，不跑 decoder 不改 V70/V70R1/V71**

**Cycle**: `V72P0-SYN` (soft-joint-binary-synthetic P0), predecessor `V71-SJK (487be113)` + `V70-BSJ (9bc34be6)` + `V70R1 (0509d10b CHANGES)`，HEAD `0926457520a0c680d087de28b1380f2a87f8161a` (动态绑定 `git rev-parse HEAD`; 2M 禁止, 9036×10240 mother 仅合成, V70/V71 零改) data `84d62779` 单点 `d1024 bw200 nearest legacy_v1` + `synthetic_v72p0`

**Feasibility**: `V70` `PARTIAL` 证 `D_bits≥0` 且 `soft_joint_factor_update` 纯函数双极 `1e-12`，`V71` `ADAPTER_REQUIRED` 证纯因子核 `D1-D10` 全 PASS 但需适配层，母亲码 `9036×10240` 未验增量嵌套与 tag exact。`V72P0` 假设 **local factor 去 self + mother incremental syndrome + exact tag 在合成域可零构造正确**（`T_LF01-08` 全 PASS 且 `Q1-Q6` 至多 `ADAPTER` 且 `P0A` tiny exhaustive `0 mismatch` 且 `P0B` `C1-C6` 全 PASS 且 `wall≤30s/peak≤2GiB`），则该链条可进入 `V72` real mother 设计，否则 `TINY/RANK/NESTED` 失败需重构。

**Key judgement**: **在合成域（P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols + P0B 1024 full）上，验证 1024→10bit 去 self local factor 的外发 LLR 定义 + mother 前缀秩/增量/tag exact 三重 correctness**：`T_LF05 self_exclusion` 显式 `Σ_{j≠i}` 且 `8测试` 双极 `1e-12`，且只读 backend `Q1-Q6` 三态 enum 得 `READY/ADAPTER`，且 `P0A` `2/3/4` symbols exhaustive `0 mismatch`，且 `P0B` `9036×10240` `r0=160 Δ8→9036` 确切 GF2 秩前缀满足 `C1-C6`，且 `wall≤30s/peak≤2GiB`，即判定 `SYNTHESIS_READY`，否则 `ADAPTER/TINY_FAIL/RANK_FAIL/NESTED_FAIL`。

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`Q1024 N1024 Nbit10240 M9036 f1.3 full-tag canonical`，**不改1024维符号/q/GF/两层验证**，2M real 禁止）下，**验证 1024→10bit local factor 去 self ↔ binary LDPC mother 9036×10240 BP incremental syndrome ↔ exact 64-bit tag 链条合成 correctness**：定义去 self LLR（`Σ_{j≠i} bits_j·llr_j`）+ 8测试正交（`T_LF01-08`）+ 只读 backend `Q1-Q6` 三态 enum + 合成 P0A tiny total_bits≤9 k2-3 n2-3 exhaustive exhaustive + P0B mother nested rank `C1-C6` + `f1.3 NOT_MEASURED` + wall `30s/2GiB`，8终态 `EVIDENCE/MODEL/BACKEND_NOT_COMPATIBLE/TINY/RANK/NESTED/READY/ADAPTER` + overall 2态。合成域，不跑 decoder，不改 V70/V71，不启 V72。

- **对照**：`V70 D_bits` 与 `V71 D1-D10` 基线作 LF 对照；`ldpc_v5` caps/disclosure 作 `Q5/Q6` 对照；`P0A/P0B` 合成 wall/peak 作 `E` 路由。
- **不变量**：`Q1024 / N1024 / Nbit10240 / M9036 / f1.3 / tag 64b exact / period 204800 / 2M禁止` 全冻结；**本变更仅验证合成链条 correctness**。
- **地图性质**：纯 synthetic-only，`1024` 枚举 + 去 self 8测试 + `Q1-Q6` enum + `P0A 2-4` + `P0B 9036×10240` `T0-T3`，`2M` real 密封不读，V70/V71 只读对照，不启 V72。

## 2. 冻结语义 — 主体与合成锚点零改（1024→10bit 合成链条不重构）

| 项 | 冻结值 | 来源 |
|---|---|---|
| Q | 1024 (10-bit `s∈[0,1023]`) | V25/V70 |
| N | 1024 symbols/block | V31/V70 |
| Nbit | 10240 bits/block (`10·N`) | V72P0 冻结 |
| M2 required | 9036 rows (`9036×10240` mother) | V72P0 冻结 |
| 列序 | `col = sym_idx*10 + bit_pos, bit_pos 0..9 LSB→MSB` | V70/V72P0 |
| GF | GF(2) binary mother | ldpc_v5 |
| f | 1.3 frozen, `f_actual NOT_MEASURED` | V71→V72P0 |
| 2M | **禁止** — 不读 2M real pairs | V72P0 |
| tag | `64-bit exact = SHA256(bit_concatenated LE)[:8B] == SHA256(s_hat)[:8B]` | V64 |
| Data SHA | `84d62779` real provenance + `synthetic_v72p0` 合成 | V55 + V72P0 |
| 处理点 | `d1024 bw200 nearest legacy_v1 period 204800 frame256` | V55 |
| LF 语义 | `去 self: Σ_{j≠i} bits_j·llr_j` 冻结 | V72P0 Phase C |
| 8测试 | `T_LF01-08` 正交 | V72P0 Phase C |
| Backend | `Q1-Q6` 三态 enum 非字符串 | V72P0 Phase D |
| P0A | tiny `total_bits≤9 k2-3 n2-3` exhaustive | V72P0 Phase E |
| P0B | mother `9036×10240 r0=160 Δ8` nested rank | V72P0 Phase F |
| 终态 | 8终态 wall first-match | V72P0 Phase G |
| T0-T3 | T0 compile / T1 unit / T2 fake / T3 regression | V72P0 Phase H |
| V72 | **禁止启动** — 任何 V72 预冻结/run_01 禁止 | V72P0 |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_*_business / nested_business` 业务码（`gf_rank_pure` 除外）；`SHALL NOT` 调 `Q/N/Nbit/M/f/tag/prior/H`；`SHALL NOT` 引 `MET/protograph/SC/Gray`；`SHALL NOT` 读 `2M` real；`SHALL NOT` 字符串判 READY（`rg '"READY"' 0 hits`）；`SHALL NOT` 跨 synthetic/real 拼接；`SHALL NOT` 以 real VAL 调 `λ`；`SHALL NOT` 实测 `f_actual`；`SHALL NOT` 启动 V72；`SHALL NOT` 改 `src/V70/V71`。

## 3. 数据角色 — SYNTHETIC_ONLY（P0A tiny + P0B full 合成，2M real 禁止）

### 3.1 合成与零重叠（键 `(synthetic, N_small, trial)` + `synthetic_v72p0`）

| 集合 | 规模 | 来源 | 说明 |
|---|---|---|---|
| P0A tiny `N_small=2` | `64 trials × 2 symbols =128` | `synthetic_v72p0: P0A_N2` | exhaustive `Q^2` 部分采样 + `H_small` 增量 tag exact |
| P0A tiny `N_small=3` | `64 trials × 3 =192` | `synthetic_v72p0: P0A_N3` | 同上，部分采样 |
| P0A tiny `N_small=4` | `64 trials × 4 =256` | `synthetic_v72p0: P0A_N4` | 采样 + 小秩 brute |
| P0B full `N=1024` | `synthetic_v72p0: P0B_MOTHER` | `synthetic_v72p0: mother 9036×10240` | nested rank C1-C6，增量 tag |
| Real 2M | **密封不读** | `84d62779` 2M session | `used_2m==False`，V72P0 不启 |
| ldpc_v5* | 只读探针 | `formal_ir/ldpc_v5*.py` | Q1-Q6 三态 audit |

- **合成注册表**：`v72p0_data_registry_synthetic.json` (`schema v72p0_synthetic_v1, lifecycle PLAN_CANDIDATE/SYNTHETIC_ONLY, Q1024 N1024 Nbit10240 M9036 f1.3 synthetic_seed V72P0-SYN, P0A {total_bits≤9 k2-3 n2-3 各 64 trials} P0B {mother 9036×10240 r0 160 Δ8 Rs}, successor_v72_not_started true, used_2m false`），**禁止事后换 synthetic seed 或读 2M**。
- **零重叠**：`synthetic` 键与 `V13..V71` 任何 real `(source,session,frame)` 零重叠（`synthetic` 域独立）。

### 3.2 数据就绪门（synthetic-only）

```
assert Q==1024 && N==1024 && Nbit==10240 && M==9036
assert f==1.3 && f_actual=="NOT_MEASURED" && used_2m==false
assert P0A_N2==64 && P0A_N3==64 && P0A_N4==64 && P0B_mother_shape==[9036,10240]
assert r0==160 && Rs[0]==160 && Rs[-1]==9036 && prefix_nested_verified
assert successor_v72_not_started == true
assert ldpc_v5*_files exist && git diff -- .../formal_ir/ldpc_v5* ==0
```

## 4. 输入合同 — 严格复用 V56 权威算法（仅新增去 self local factor）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | Q | 1024 |
| 2 | N | 1024 symbols |
| 3 | Nbit | 10240 bits |
| 4 | M | 9036 rows |
| 5 | 列序 | `sym*10+bit` LSB→MSB |
| 6 | 10-bit 位展开 | `bit_i(s)=(s>>i)&1, i=0..9` |
| 7 | LF 去 self | `Σ_{j≠i} bits_j·llr_j` |
| 8 | tag | `64b exact LE` |
| 9 | 帧 | `period 204800 frame256` |
| 10 | f | `1.3 NOT_MEASURED` |

## 5. 估计器 — 去 self local factor + 8测试 + 6问三态 + P0A/P0B + wall（synthetic only，不启 V72）

### 5.1 联合先验 synthetic（SYNTHETIC_ONLY 描述性）

```
synthetic先验 P_synth(a) = (1-ε)·K_δ(a) + ε/1024, K_δ 为 δ 分布峰值载体
total_bits≤9 k2-3 n2-3 的 P0A 各自独立 synthetic 采样，N=1024 的 P0B 仅 matrix 构造（不估计 CE）
Q=1024, N=1024, Nbit=10240
```

### 5.2 Phase C — 去 self local factor（LLR 定义冻结，枚举1024，8测试）

```
# 冻结定义：去 self

def bit_factor_from_llr(llr_10: float[10]) -> log_factor_incl[1024]:
  # incl: log_factor_incl[a] = Σ_{j=0..9} bits_j(a)*llr_j
def local_factor_excl(log_prior[1024], llr_10[10], target_bit i) -> log_post_excl_i[1024]:
  for a in 0..1023:
    bits = [(a>>j)&1 for j 0..9]
    log_unnorm_excl_i[a] = log_prior[a] + Σ_{j≠i} bits[j]*llr[j]
  log_post_excl_i = log_unnorm_excl_i - logsumexp(log_unnorm_excl_i)

def llr_out_i(log_post_excl_i) -> float:
  llr_out_i = logsumexp_{a:bit_i=1} log_post_excl_i[a] - logsumexp_{a:bit_i=0} log_post_excl_i[a]

# 全包含对照核（V71复用语义，仅对照）：
def soft_joint_factor_kernel_incl(log_prior, llr_10) -> log_post_incl:
  log_unnorm[a]=log_prior[a]+Σ_j bits_j*llr_j
  log_post=log_unnorm - logsumexp(log_unnorm)

# 自洽关系（T_LF05）：
#   log_post_incl[a] - log_post_excl_i[a] == bits_i(a)*llr_i + (logZ_excl_i - logZ_incl)  # 配分归一差
#   llr_out_i 的定义与 brute Π_{j≠i} factor 枚举一致 max|Δ|<1e-12

# 枚举 brute：显式 Π_{j≠i} factor 后 logsumexp 归一，与 kernel_excl 逐项 max|Δ|<1e-12
#   all_zero: llr≡0 ⇒ log_post_excl_i ≡ log_prior
#   delta: 对a*, llr_j=+K if bit_j(a*)=1 else -K, K=1e6 ⇒ excl 仍退化但保留1位自由度
```

- ponytail: `numpy` 向量化枚举 `1024`，`logsumexp` 用 `numpy.logaddexp.reduce` 手写；`K=1e6` 的 `exp` 溢出需 log域运算，报告显式 log域实现。
- 测试：`test_v72p0_local_factor_small.py` 内 `T_LF01-08` 各 `1e-12` 已验，`self_exclusion` 对 `i=0,5,9` 三点位已验。

### 5.3 Phase C — T_LF01-08 八测试（正交完备）

| ID | 名称 | 阈/断言 | FAIL 路由 |
|---|---|---|---|
| T_LF01 | completeness | `len==1024 && ∀a a==Σ bit_i<<i` | `BACKEND_NOT_COMPATIBLE` |
| T_LF02 | normalization | `|Σ exp(log_post)-1|<1e-12 && |logsumexp-0|<1e-12` | `BACKEND_NOT_COMPATIBLE` |
| T_LF03 | marginal_preservation | `llr≡0 ⇒ max|log_post-log_prior|<1e-12` | `MODEL_NOT_STABLE` |
| T_LF04 | delta_concentration | `llr定向a* ⇒ log_post[a*]==0±1e-9 && 其余<-1e2` | `MODEL_NOT_STABLE` |
| T_LF05 | self_exclusion | `log_post_incl - log_post_excl_i == bits_i·llr_i + ΔZ ±1e-12` 且 `llr_out_i` brute `1e-12` | `MODEL_NOT_STABLE` |
| T_LF06 | log_domain_stability | `K=1e6` 全程 `isfinite` 无 overflow | `MODEL_NOT_STABLE` |
| T_LF07 | determinism | 同输入二次 `max|Δ|==0` | `MODEL_NOT_STABLE` |
| T_LF08 | brute_vs_kernel | 显式 1024 逐项 brute `max|Δ|<1e-12` 两极 | `MODEL_NOT_STABLE` |

### 5.4 Phase D — Backend 只读 Q1-Q6 三态（per synthetic，不执行 decoder，不字符串）

```
Q1 interface_presence: AST探针 ldpc_v5.py 是否导出 5 函数且签名稳定 -> {PASS,FAIL,NOT_APPLICABLE}
Q2 policy_manifest_schema: 是否含 policy_sha256/decoder_sha256/h1_binding/mother_shape 9036×10240 -> enum
Q3 backend_model_binding: channel_model_sha256 == selection_manifest -> enum
Q4 extrinsic_interface: error_channel 是否为 List[float] 且 plane_error_channel 是否去 self（探针参数名+过滤逻辑）-> enum
Q5 runtime_caps: caps {wall_s 10, decoder_calls 20, events 32} 兼容 wall/peak -> enum
Q6 disclosure_accounting: OUTCOME_FIELDS 是否含 ldpc_syndrome_bits/h1/h2/verification_tag_bits_component/incremental_prefix 且 9036 可容纳 -> enum

三态 enum BackendState(IntEnum): PASS=0, FAIL=1, NOT_APPLICABLE=2
分流 (enum 比较，禁止字符串):
  READY = Q1 PASS ∧ Q2 PASS ∧ Q3 PASS ∧ Q4 PASS(self_excl) ∧ Q6 PASS(9036)
  ADAPTER = Q1-3 PASS ∧ (Q4 ADAPTER ∨ Q6 ADAPTER)
  NOT_COMPATIBLE = Q1/Q2 FAIL ∨ T_LF01/02 FAIL

guard: rg '"READY"' audit脚本 0 hits (除注释); assert backend_state == BackendState.READY
```

- 只读：`ast.parse` + `inspect.signature` + `importlib.util.spec_from_file_location` 不执行 `run_ldpc_formal_v5`，`rg "run_ldpc_formal_v5\(" 0 hits`（除探针注释），`git diff ldpc_v5* ==0`。

### 5.5 Phase E — P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols exhaustive

```
# 合成 tiny 域
for N_small in [2,3,4]:
  for trial in 0..63:
    bits_small = random_bits(N_small*10, seed V72P0-SYN-P0A-{N_small}-{trial})
    H_small = generate_H_small(N_small)  # m_small = ceil(1.3*N_small*CE_synth) ≈?
    syndrome = H_small @ bits_small (GF2)
    tag = SHA256(bits_small)[:8B]
    tag_from_s = SHA256(s_hat_bytes)[:8B]  # s_hat = Σ bit<<j per symbol
    assert syndrome_incremental_correct && tag == tag_from_s
P0A_PASS = (all 192 trials 0 mismatch) ∧ (T_LF01-08 PASS) ∧ wall≤30s ∧ peak≤2048MiB
```

### 5.6 Phase F — P0B mother 9036×10240 nested rank C1-C6

```
H_mother ∈ GF2^{9036×10240}, col = sym_idx*10 + bit_pos
r0=160, Δ=8, Rs = {r0 + k·Δ ≤9036} ∪ {9036}
∀r∈Rs: C1 rank(H[0:r])==r  (高斯消元 GF2)
C2 weight>0 per row
C3 distinct rows
C4 H[0:r]==H_mother[0:r] prefix
C5 syndrome_{r2}[0:r1]==syndrome_{r1} incremental
C6 tag_exact SHA256(bits)==SHA256(s_hat) ∀ synthetic sample (64 random bits)
P0B_PASS = C1∧C2∧C3∧C4∧C5∧C6
```

### 5.7 f1.3 冻结 f_actual NOT_MEASURED（synthetic 参照，仅合规）

```
CE_synth_ref ≈0.8 bits/symbol (synthetic δ 分布近似)
required_ref = ceil(1.3*1024*CE_synth_ref) ≈1065 (参照，与 9036 上限 gap 正交)
f_actual = "NOT_MEASURED"  # 冻结不测
# mother 9036 为上限能力，非 required 本身；A6 仅校验 9036 可容纳 incremental disclosure
```

## 6. 分流判定（per-synthetic 8终态 + overall 2态，wall first-match）

### 6.1 Per-synthetic 8终态 first-match（优先级高→低，互斥）

```
if not materialization_ok or C_ab_nonfinite or T_LF09-like D9 FAIL or P0A_not_executed:
    classification = V72P0_EVIDENCE_INCOMPLETE; successor = recollect_synthetic
elif T_LF03/04/05/06/07/08 FAIL or D_bits<-1e-9:
    classification = V72P0_MODEL_NOT_STABLE; successor = refine_local_factor
elif Q1 FAIL or Q2 FAIL or T_LF01/02 FAIL:
    classification = V72P0_BACKEND_NOT_COMPATIBLE; successor = backend_refactor
elif P0A mismatch>0 or wall>30s or peak>2048:
    classification = V72P0_TINY_FAIL; successor = v72p0_tiny_refine
elif C1 FAIL or C2 FAIL or C3 FAIL:
    classification = V72P0_MATRIX_RANK_FAIL; successor = regenerate_mother
elif C4 FAIL or C5 FAIL:
    classification = V72P0_SYNDROME_NESTED_FAIL; successor = fix_incremental
elif T_LF01-08 全 PASS && backend==READY && P0A PASS && P0B PASS(C1-C6) && wall≤30s && peak≤2048:
    classification = V72P0_SYNTHESIS_READY; successor = v72_mother_adapter_design
else: # T_LF PASS && Q1-Q3 PASS && (Q4 ADAPTER ∨ Q6 ADAPTER) && P0A/P0B PASS && wall≤30s
    classification = V72P0_SYNTHESIS_ADAPTER; successor = v72_mother_adapter_design
```

- **阈值冻结**：`MODEL` 的 `D<-1e-9`；`TINY` 的 `wall≤30s && peak≤2048MiB`；`RANK` 的 `rank==r` 确切；`NESTED` 的 `prefix==`；`READY` 需 `T_LF01-08 PASS` + `Q1-Q6 READY(enum)` + `P0A PASS` + `C1-C6 PASS` + `wall≤30s`。

### 6.2 Overall 2态

```
ready_count = #{case | SYNTHESIS_READY}
adapter_count = #{case | SYNTHESIS_ADAPTER}
if any EVIDENCE_INCOMPLETE: overall = OVERALL_EVIDENCE_INCOMPLETE (not in 2态, explicit)
elif ready_count==1 && adapter_count==0: overall = OVERALL_READY
else: overall = OVERALL_ADAPTER_OR_FAIL
# counts_per_classification = {EVIDENCE, MODEL, BACKEND, TINY, RANK, NESTED, READY, ADAPTER} 8正交
```

## 7. 脚本与报告（SYNTHETIC_ONLY守卫，不启 V72）

- **脚本 `scripts/v72p0_soft_joint_binary_synthetic.py`** (SYNTHETIC_ONLY): `python scripts/v72p0_soft_joint_binary_synthetic.py [--registry v72p0_data_registry_synthetic.json] [--out v72p0_results.json]` → `T_LF01-08 去 self → P0A tiny total_bits≤9 k2-3 n2-3 exhaustive exhaustive → P0B 9036×10240 C1-C6 → wall/peak + f1.3 NOT_MEASURED`，`rg "decode_" 0 hits`，`rg '"READY"' 0 hits`，`py_compile PASS`；输出 `v72p0_results.json + v72p0_table.{csv,json}` + 控制台 8终态摘要。
- **脚本 `scripts/v72p0_backend_audit.py`** (read-only 三态 enum): `python scripts/v72p0_backend_audit.py [--out v72p0_backend_audit_report.json]` → `Q1-Q6` 三态 enum `READY/ADAPTER/NOT_COMPATIBLE`，`rg "decode_" 0 hits`，`rg '"READY"' 0 hits`（除注释），`rg "run_ldpc_formal_v5\(" 0 hits`，`py_compile PASS`；输出 `v72p0_backend_audit_report.json + V72P0_BACKEND_AUDIT_REPORT.md`。
- **报告 `V72P0_SYN_REPORT.md`**：`per synthetic T_LF01-08/P0A/P0B C1-C6/wall/peak/per_invocation + overall + tag exact + 2M未读 + Q1024冻结 + V72_not_started` 与 `json/csv` 一致，不扩大为 `FER/SKR`。
- **报告 `V72P0_BACKEND_AUDIT_REPORT.md`**：`Q1-Q6 per case 三态 enum / READY/ADAPTER/NOT_COMPATIBLE` + wall + `f1.3 NOT_MEASURED`。
- **守卫**：合成期零 decoder、零 real 2M、多 synthetic 并列 8终态、**不创建 `run_01`**、不比较方法、不调 V72 以外码、**不启 V72**；**四工件+registry+spike 已单独提交推送，新 Plan SHA 已生成**。

## 8. 守卫 R72-01~09（SYNTHETIC_ONLY, 不构业务矩阵, 不创 run_01, 不启 V72, 去 self, 三态 enum, P0A/P0B）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R72-01 | 冻结主体 Q1024 N1024 Nbit10240 M9036 f1.3 + 2M禁止 + 不启V72 | `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M未读 git diff src==0 && successor_v72_not_started && used_2m==false` |
| R72-02 | local factor 去 self LLR 冻结 + 8测试 | `去 self Σ_{j≠i} 冻结，8测试 T_LF01-08 正交，brute 1e-12，无I/O/随机` |
| R72-03 | backend 只读 Q1-Q6 三态 enum 非字符串 READY | `Q1-Q6 每问 PASS/FAIL/NOT_APPLICABLE enum，READY 用 enum== 判断，rg '"READY"' 0 hits` |
| R72-04 | synthetic P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols exact | `total_bits≤9 k2-3 n2-3 各64 trials 0 mismatch，tag exact，wall≤30s` |
| R72-05 | synthetic P0B mother 9036×10240 nested rank C1-C6 | `r0=160 Δ8→9036 前缀 rank==r 非零去重前缀增量 tag exact` |
| R72-06 | 8终态 wall first-match | `EVIDENCE>MODEL>BACKEND>TINY>RANK>NESTED>READY>ADAPTER 互斥，wall/peak 已落盘` |
| R72-07 | T0-T3 矩阵 | `T0 compile/import/tiny-math, T1 8测试+Q1-Q6 mock, T2 fake P0A/P0B 前K秩, T3 V70/V71 只读+2M回归` |
| R72-08 | 四工件+双报告完整 | `registry + results + table csv/json 行对等 + V72P0_SYN_REPORT + V72P0_BACKEND_AUDIT_REPORT + test py_compile+pytest PASS` |
| R72-09 | SYNTHETIC_ONLY 不跑 decoder 不读 2M 不创 run_01 不启 V72 | `rg "decode_" 0 hits && used_2m==false && ls run_01 不存在 && py_compile PASS && V72_not_started` |

## 9. 与 V64/V70/V71/V72 衔接

- V70 `PARTIAL` 与 V71 `ADAPTER_REQUIRED` 已固化合成对照；V72P0 为**二进制 soft-joint 合成 P0 壁垒**（`去 self LF + mother 9036×10240 + 8终态`），不跑 decoder。
- 若 `V72P0_SYNTHESIS_READY`（`T_LF PASS ∧ Q1-Q6 READY ∧ P0A PASS ∧ C1-C6 PASS ∧ wall≤30s`）则 local factor ↔ mother incremental ↔ tag 链条可在合成域零适配对接，后续可进入 `V72` real mother 增量设计；若 `ADAPTER` 则需适配层；若 `TINY/RANK/NESTED` 则需重构 mother 或 LF。
- 本变更不创建 `run_01`，**不启动 V72**，任何 V72P0 后续 real mother/decoder 需另起 `EXECUTE_AUTH`。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`Q/N/Nbit/M/tag`），V72P0 仅验证合成链条 correctness，不改码（多 synthetic，P0A/P0B），不启 V72，2M 禁止。
- D2 单一 synthetic 先验 `P_synth`，local factor 仅为 10-bit 去 self `Σ_{j≠i}`，不搜索多分布。
- D3 `f1.3` 不 cap，`required_ref≈1065` 与 `9036` 上限 gap 双报告，`READY` 限 `P0A PASS ∧ C1-C6 PASS ∧ Q1-Q6 READY`。
- D4 数据 `P0A total_bits≤9 k2-3 n2-3 各64 trials + P0B mother 9036×10240` 确定性 synthetic，不搜索多划分，2M 隔离，V72 不启。
- D5 8终态 per-synthetic + overall 2态 + T0-T3 正交审计，不以平均替代。
- D6 不产生 real 矩阵/码参数，仅 `P0A/P0B/C1-C6/wall` 与 successor 建议，`READY` 方可进入 V72。
- D7 本变更为 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder/V72 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允。
