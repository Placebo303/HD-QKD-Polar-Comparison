# OpenSpec Design: formal-ir-v71-soft-joint-factor-kernel

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024-state 纯因子核校验完整 posterior 保留，extrinsic 冻结 `ext=log_post-log_prior` log域差分，5函数纯枚举 log-domain，D1-D10 十不变量正交，ldpc_v5* 只读 A1-A6 分流 READY/ADAPTER/NOT_COMPATIBLE，1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈，f1.3 freeze `f_actual NOT_MEASURED`，per-session 6终端总体4态，不跑 decoder 不构业务矩阵不启 V72**

**Cycle**: `V71-SJK` (soft-joint-factor-kernel), predecessor `V70-BSJ (9bc34be64a2822c8babb4320efb47fc7e335a21a)` + `V67-MAP (V67_FEASIBILITY_MAP_ACCEPTED 3× NEAR_FULL)` + `V64 22/24 PASS` + `binary-ldpc-v5 ldpc_v5*` (read-only audit 对象), HEAD `TBD_new_plan_SHA` (provenance deviation registry head `9825d0b336042ad4bf2b26ed31b7fa09a04de620` vs predecessor `9bc34be6`) data `84d62779` 单点 `d1024 bw200 nearest legacy_v1`

**Feasibility**: `V70` 在 3 sessions 上验证 `D_bits≥0` 且 `soft_joint_factor_update` 纯函数双极 `1e-12`，证二进制 soft-joint 因子保留 1024-ary posterior；`V71` 假设 **1024-state 纯因子核以 log-domain 5 函数纯枚举可完整保留 posterior**（`extrinsic` 冻结分离，且 `D1-D10` 全 PASS 且 `ldpc_v5*` A1-A6 至少 `ADAPTER` 且 `1M benchmark 30s/2GiB` 内），则核可零改对接 `ldpc_v5` 仅需适配层，需 decoder-free 验证 `D1-D10` 与 `A1-A6` 与 `E benchmark` 三重守卫。

**Key judgement**: **在 V67/V69 三 session 的 `Stage2 CAL1024/VAL256` 上（E benchmark 仅 1M 实测），验证 1024-state 纯因子核 5 函数 log-domain 枚举的完备性**：全零 `llr≡0` 边际保持且 delta 退化且 `extrinsic` 一致且 `logsumexp` 归一且确定性且 chain 闭合且 TEST 隔离且正交分解，且只读 `ldpc_v5*` `A1-A6` 分流为 `READY/ADAPTER`，且 `1M` 上 `1/9/1024 block` 实测 `wall≤30s/peak≤2GiB`，即判定 `KERNEL_READY_FEASIBLE`，否则 `ADAPTER/HEAVY/NOT_COMPATIBLE`。

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`n1024 q1024 GF32 poly37 H1-16 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical, leak Σw_i·m_i+64`，**不改1024维符号/q/GF/两层验证码**）下，**验证 1024-state 纯因子核保留完整 1024-ary 后验 + ldpc_v5* 兼容性**：定义 extrinsic 冻结（`ext=log_post-log_prior` log域差分）+ 5 函数纯枚举 log-domain 因子核 + D1-D10 十不变量 + 只读 `ldpc_v5*` A1-A6 分流 + 1M CAL/VAL `1/9/1024 block` `30s/2GiB` 路由阈 + `f1.3 freeze` `f_actual NOT_MEASURED`，每 session 6终端 `EVIDENCE/MODEL/NOT_COMPATIBLE/READY/ADAPTER/HEAVY` + 总体4态 `EVIDENCE/MODEL/READY(3×)/ADAPTER_OR_HEAVY`。全程 decoder-free，不构业务矩阵，不启 V72。
- **对照**：`V70 D_bits` 与 `CE_full` 基线作 `D8 chain` 对照；`ldpc_v5` 的 `caps/disclosure` 作 `A5/A6` 对照；`1M benchmark` 三档作 `E` 路由。
- **不变量**：`dimension 1024 / bin200 / nearest legacy_v1 / channels A1/B5 / GF32 / Lane C / H_inc Δ8 / full-tag` 全冻结；**本变更仅验证纯因子核完整性 + 兼容性**。
- **地图性质**：纯 decoder-free，`1024` 枚举 + `5函数 log-domain` + `D1-D10` + `A1-A6` + `1M 1/9/1024 benchmark` + `f1.3 NOT_MEASURED`，`TEST` 密封不读，V67/V69 三 session audit，每 session 6终端/4态，不启 V72。

## 2. 冻结语义 — 主体与处理点零改（1024维纯因子核不重构）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| q | 1024 (10-bit `s∈[0,1023]`) | V25/V38 |
| GF | GF32 poly37 | GF2mField |
| U自然(二层参照) | `U1_nat=s>>5, U2_nat=s&31, F03 5+5` | V25/V67 |
| 10-bit位展开 | `bit_i(s)=(s>>i)&1, i=0..9 LSB→MSB` | V70 A-H D |
| extrinsic冻结 | `ext[a]=log_post[a]-log_prior[a]` log域差分，不含信道因子 | V71 Phase C |
| 5函数核 | `log_prior / bit_factor / kernel / extrinsic / validate` 纯枚举 log-domain | V71 Phase C |
| m1 base | 16 | V31 H1 |
| Lane C base m2 | `1M 184 / 1p5M 190 / 2M 192` | V54→V64 |
| H_total base | `200/206/208` | V64 |
| H_inc | `Δ8` 家族 nested | V54 |
| decoder(冻结禁用) | `90/1.0 poly37 early-stop` | V43 — 地图期禁用 |
| Verification | `full-symbol tag 32*U1+U2 canonical 64b` | V64 — 禁用期仍冻结 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` | V55 |
| 多session复用 | `V67/V69 3 sessions Stage2 CAL1024+VAL256` 原样（E benchmark 仅 1M 实测） | V67 `v67_data_registry.json`→V69→V71 |
| 分阶段 | `Phase A CAL-only audit准备 → Phase C 5函数 → Phase D D1-D10 → Phase E 1M benchmark → Phase F f1.3 → Phase G 6终端/4态` | V71 |
| V72 | **禁止启动** — 任何 V72 预冻结/run_01 禁止 | V71 |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_*_business / gf_rank_business / nested_business` 业务码；`SHALL NOT` 调 `m2/leak/decoder/prior/H1/Lane C/H_inc/verification`；`SHALL NOT` 引 `MET/protograph/SC/Gray`（除纯因子核注释）；`SHALL NOT` 跨 acquisition 拼接；`SHALL NOT` 以 `VAL/TEST` 调 `λ`；`SHALL NOT` 实测 `f_actual`（`NOT_MEASURED`）；`SHALL NOT` 启动 V72；`SHALL NOT` 读 TEST；`SHALL NOT` 执行 `run_ldpc_formal_v5`。

## 3. 数据角色 — V67/V69 三预注册 Stage2 复用（每类≤3 机械已验，E benchmark 仅 1M）

### 3.1 复用与零重叠（键 `(source,session,frame)` + `(source_label, acquisition_id)`）

| 集合 | 每session规模 | 来源 | 说明 |
|---|---|---|---|
| Stage2 CAL (Phase A用) | 1024 frames =262144 pairs | `v69_data_registry: stage2_CAL[1024]` | `C_ab→P_global→P(a|b) λ(1M CAL 4-fold)→D1-D10/D8 chain` + audit输入 |
| Stage2 VAL (E benchmark & D确认) | 256 frames =65536 pairs | `v69_data_registry: stage2_VAL[256]` | `D1-D10 VAL确认 + 1M VAL benchmark 1/9/1024` |
| TEST | 密封不读 | `V65 TEST 120 / V66 EVAL 24` | `used_test==False`，V71 不启 |
| ldpc_v5* | 只读探针 | `formal_ir/ldpc_v5*.py` | A1-A6 audit 对象 |

- **复用**：`v71_data_registry.json` 由 `v69_data_registry.json` 的 3 sessions（`20260123_1M_600k_0dB 1M, 20260107_PPLN_1p5M 1p5M, 20260123_2M_1p2M_0dB 2M`）的 `stage2_CAL[1024]+stage2_VAL[256]` 原样拷贝（`total 3, per_category 1,1,1, acquisition_dedup_verified, frozen, not_sorted_by_CE`），`zero_overlap_verified` 与 `V13..V71` 零重叠已验，禁止事后换 session 或按 `CE/required` 替换，`successor_v72_not_started true`，**Phase E benchmark 仅 1M session 实测**（`1p5M/2M` 仅 audit 输入，不测 benchmark）。
- **注册表**：`v71_data_registry.json` (`schema v71_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head 9825d0b336042ad4bf2b26ed31b7fa09a04de620 (provenance deviation), reused_from v69, successor_v72_not_started true, sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified}`)。

### 3.2 数据就绪门（decoder-free）

```
assert total_sessions==3 && per_category 1,1,1 && acquisition_dedup_verified && successor_v72_not_started
assert per session |CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ (key=(source,session,frame))
assert CAL∪VAL ∩ (V13..V70) ==∅
assert frame 256 && s∈[0,1023] && bit展开 0..9 无丢
assert successor_v72_not_started == true
assert ldpc_v5*_files exist && git diff -- .../formal_ir/ldpc_v5* ==0
```

## 4. 输入合同 — 严格复用 V56 权威算法（仅新增 5 函数因子核）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | dimension | 1024 |
| 2 | bin_width | 200 ps |
| 3 | pairing | `nearest`, double-pointer `bin//1024` |
| 4 | rule/mapping | `legacy_v1` |
| 5 | channels | `A:1 , B:5` |
| 6 | U自然(参照) | `s=32*u1+u2, U=32*U1+U2, F03 5+5` (参照) |
| 7 | 10-bit位展开 | `bit_i(s)=(s>>i)&1, i=0..9` |
| 8 | extrinsic冻结 | `ext=log_post-log_prior` |
| 9 | 5函数核 | 纯枚举 log-domain 1024态 |
| 10 | frame anchor | `frame_start_ps / period 204800ps / floor_div` |

## 5. 估计器 — 5 函数纯因子核 + D1-D10 + A1-A6 + benchmark + f1.3（CAL选VAL确认一次，不启 V72）

### 5.1 联合计数与全局先验 (1M CAL-only 描述性)

```
C_ab = bincount2d(a_cal_1M, b_cal_1M)  shape 1024×1024, sum N_cal=262144
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal
Q=1024, N=1024
B: P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ) if N_b>0 else P_global(a) ; λ∈[1e-2,1e4] log10 仅 1M CAL内4-fold最小CV NLL
```

### 5.2 Phase C — 5 函数纯因子核（extrinsic 冻结，枚举 1024，log-domain）

```
signature 1: log_prior_from_posterior(log_P_a_given_b: float[1024]) -> log_prior[1024]
  # log_P_a_given_b = log P(a|b) (自然对数)，归一校验: logsumexp(log_prior)==0±1e-12
  # 纯函数：无I/O/随机/全局

signature 2: bit_factor_from_llr(llr_10: float[10]) -> log_factor[1024]
  # for a in 0..1023: bits=[(a>>i)&1 for i 0..9]; log_factor[a]= Σ_i bits[i]*llr[i]
  # 未归一化因子，log域叠加

signature 3: soft_joint_factor_kernel(log_prior[1024], llr_10[10]) -> log_post[1024]
  # for a in 0..1023: log_unnorm[a]=log_prior[a]+log_factor[a]
  # log_post[a]=log_unnorm[a]-logsumexp(log_unnorm)  # 归一化
  # 纯函数：枚举1024，无I/O/随机/全局，log域数值稳定

signature 4: extrinsic_from_logs(log_prior[1024], log_post[1024]) -> extrinsic[1024]
  # extrinsic[a]=log_post[a]-log_prior[a]
  # 校验: logsumexp(log_prior+extrinsic)==0±1e-12

signature 5: validate_kernel(log_prior, llr, log_post, extrinsic) -> {D1*..D10*}
  # 触发 D1-D10 逐项 PASS/FAIL，返回 dict
  # brute_force: 显式Π_i factor枚举1024态后 logsumexp 归一，与 kernel 逐项 max|Δ|<1e-12
  #   all_zero: llr≡0 ⇒ log_factor≡0 ⇒ log_post≡log_prior
  #   delta: 对a*, llr_i=(+K if bit_i(a*)=1 else -K), K=1e6 ⇒ 仅a* 项最大 ⇒ posterior 退化a*
```

- ponytail: `numpy` 向量化枚举 `1024`，`logsumexp` 用 `numpy.logaddexp.reduce` 手写；`K=1e6` 的 `exp` 溢出需 log域运算，报告显式 log域实现。
- 测试：`test_v71_soft_joint_factor_kernel_small.py` 内 `all_zero` 与 `delta_a_star=0,511,1023` 三点 `1e-12` 已验，`1/9/1024 block` 小 benchmark 在 `test` 侧仅 `1/9` 不测 `1024` 全量。

### 5.3 Phase D — D1-D10 十不变量（正交完备）

| ID | 名称 | 阈/断言 | FAIL 路由 |
|---|---|---|---|
| D1 | completeness | `len==1024 && ∀a a==Σ bit_i<<i` | `NOT_COMPATIBLE` |
| D2 | normalization | `|Σ exp(log_post)-1|<1e-12 && |logsumexp-0|<1e-12` | `NOT_COMPATIBLE` |
| D3 | marginal_preservation | `llr≡0 ⇒ max|log_post-log_prior|<1e-12` | `MODEL_NOT_STABLE` |
| D4 | delta_concentration | `llr定向a* ⇒ log_post[a*]==0±1e-9 && 其余<-1e2` | `MODEL_NOT_STABLE` |
| D5 | extrinsic_consistency | `ext==log_post-log_prior && |logsumexp(log_prior+ext)-0|<1e-12` | `MODEL_NOT_STABLE` |
| D6 | log_domain_stability | `K=1e6` 全程 `isfinite` 且无 `exp overflow` | `MODEL_NOT_STABLE` |
| D7 | determinism | 同输入二次 `max|Δ|==0` | `MODEL_NOT_STABLE` |
| D8 | chain_closure | `|CE_full - (ΣCE_bit - D_bits)|<1e-9` (复用 V70 P(a|b)，仅校验) | `MODEL_NOT_STABLE` |
| D9 | test_isolation | `used_test==False && rg TEST 0 hits` | `EVIDENCE_INCOMPLETE` |
| D10 | orthogonality | 任一 FAIL 不掩盖他项，逐项分解报告 | 正交描述 |

- 链式 `D8` 的 `CE_full/CE_bit/D_bits` 复用 `1M CAL/VAL` 上 `P(a|b)` 估计，`λ` 仅 `1M CAL 4-fold`，`VAL` 确认一次，不读 TEST。

### 5.4 Phase E — 仅 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈

```
# 仅 1M session 实测
for block in [1,9,1024]:
  for mode in [llr_zero, llr_random_N01]:
    wall_s, peak_MiB = benchmark(soft_joint_factor_kernel, 1M_VAL256, block, mode)
    # 1: per-symbol (1*1024 次核调用)
    # 9: per-plane-batch (9 批次)
    # 1024: per-frame (1024符号批量，单次向量化1024态枚举)
# 路由阈：1024-block 在 1M VAL全量 (256 frames *1024 symbols) 上 wall_s ≤30s && peak_MiB ≤2048
E_PERF_PASS = (wall_1024 ≤30.0 && peak_1024 ≤2048)
report: per block {wall_s, peak_MiB, per_invocation_ns=(wall_s*1e9)/(num_invocations)}
```

- `tracemalloc` 或 `resource.getrusage` 估 `peak`，`wall` 用 `time.monotonic`，三次取 `min` 或 `median` 报告显式。
- `1p5M/2M` 不 benchmark，仅作 audit 分流输入。

### 5.5 Phase F — f1.3 冻结 f_actual NOT_MEASURED

```
CE_full^{VAL_1M} = - (1/|VAL_1M|) Σ_{(a,b)∈VAL_1M} log2 P(a|b)  bits/symbol
required = ceil(1.3 * N * CE_full^{VAL_1M})  N=1024 bits/block integer
f_actual = "NOT_MEASURED"  # 冻结不测
# 仅 A6 披露对照参照：required vs ldpc_v5 的 h1+h2+tag 分解作描述性 gap，不入核门禁
```

- `f1.3` frozen，报告显式 `f1.3 frozen, f_actual NOT_MEASURED`，门禁不以 `f_actual` 判。

### 5.6 Phase A/B — ldpc_v5* 只读 A1-A6 audit（per session，不执行 decoder）

```
A1 interface_presence: AST探针 ldpc_v5.py 是否导出 5 函数且签名稳定
A2 policy_manifest_schema: 是否含 policy_sha256/decoder_sha256/h1_binding 且重建一致
A3 channel_binding: channel_model_sha256 是否 == selection_manifest.channel_model_sha256
A4 extrinsic_interface: error_channel 是否为 list[float] 且 plane_error_channel 是否可注入 extrinsic (探针参数类型)
A5 runtime_caps: caps {wall_s 10, decoder_calls 20, events 32} 是否 ≥ 因子核开销 (描述性，cap 不超限即 PASS)
A6 disclosure_accounting: OUTCOME_FIELDS 是否含 ldpc_syndrome_bits/h1/h2/verification_tag_bits_component 且可容纳 extrinsic (不混 key_dependent)

分流:
  READY = A1-A6 全 PASS
  ADAPTER = A1-A3 PASS 且 (A4 FAIL 或 A6 需适配)
  NOT_COMPATIBLE = A1/A2 FAIL 或 D1/D2 FAIL
```

- 只读：`ast.parse` + `inspect.signature` + `importlib.util.spec_from_file_location` 不执行 `run_ldpc_formal_v5`，`rg "run_ldpc_formal_v5\(" 0 hits`（除审计探针注释），`git diff ldpc_v5* ==0`。

## 6. 分流判定（per-session 6终端 + 总体4态，1M benchmark 路由）

### 6.1 Per-session 6终端 first-match（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or C_ab_nonfinite or D9 FAIL:
    classification = V71_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary or |CE^{VAL}-CE^{CV}|>0.50 or val_b_unseen>0.01 or D_bits<-1e-9 or D3/D4/D5/D6/D7 FAIL or D8 FAIL or D10 not orthogonal:
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

- **阈值冻结**：`MODEL_NOT_STABLE` 的 `ΔCE≤0.50` 且 `val_b_unseen≤1%` 且 `λ∈(1e-2,1e4)` 开区间且 `D_bits≥-1e-9` 且 `D3/D4 1e-12/1e-9`；`READY` 需 `D1-D10 PASS` + `A1-A6 READY` + `wall≤30s && peak≤2GiB` (1024-block 1M VAL 全量)。

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
# audit = {per_session_classification[3], overall, ready/adapter/heavy/not_compatible/evidence/model 6 counts,
#          per_session_audit[3], per_session_D1-D10[3], E_benchmark_1M, f1.3, f_actual NOT_MEASURED}
```

- 总体不设 `FAIL`，即便全部 `HEAVY` 亦 `COMPLETE`（地图完成，结论为需适配）；仅 `<3` session 视为 incomplete map（但 V71 固定3）。
- 报告需附 `counts_per_classification (6终端)` 与 `overall 4态` + `D1-D10/audit/E benchmark` 审计表。

## 7. 脚本与报告（decoder-free守卫，不启 V72）

- **脚本 `scripts/v71_soft_joint_factor.py`** (decoder-free): `python scripts/v71_soft_joint_factor.py [--registry v71_data_registry.json] [--out v71_results.json]` → `1M CAL1024 C_ab/P/λ→D8 chain + 5函数纯枚举 brute 双极校验 D1-D10 → 1M VAL 1/9/1024 benchmark + f1.3 冻结`，`rg "decode_" 0 hits`，`rg -i "met|protograph|sc_coupling" 0 hits`，`rg -i "v72|qualification" 0 hits`（除 successor 注释），`py_compile PASS`；输出 `v71_results.json + v71_table.{csv,json}` + 控制台 6终端/4态摘要；校验 `TEST未参与`、`f_actual NOT_MEASURED`、`1024枚举 D1-D10` 已验。
- **脚本 `scripts/v71_ldpc_v5_audit.py`** (read-only): `python scripts/v71_ldpc_v5_audit.py [--out v71_audit_report.json]` → `ldpc_v5* A1-A6` 只读探针 `READY/ADAPTER/NOT_COMPATIBLE` per session + overall 4态，`rg "decode_" 0 hits`，`rg "run_ldpc_formal_v5\(" 0 hits`，`py_compile PASS`；输出 `v71_audit_report.json + V71_AUDIT_REPORT.md`。
- **报告 `V71_KERNEL_REPORT.md`**：`per session 5函数 / D1-D10 / 1024枚举双极 brute / 1/9/1024 benchmark `wall/peak/per_invocation` + overall 4态 + TEST隔离 + 1024维冻结 + V72_not_started` 与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `f1.3 frozen, f_actual NOT_MEASURED`。
- **报告 `V71_AUDIT_REPORT.md`**：`A1-A6 per session / READY/ADAPTER/NOT_COMPATIBLE` + overall 4态。
- **守卫**：地图期零 decoder、零业务矩阵构造、多 session 并列 6终端/4态、**不创建 `run_01`**、不比较方法、不调 V71 以外码、**不启 V72**；**四工件+registry+spike 已单独提交推送，新 Plan SHA 已生成**。

## 8. 守卫 R71-01~11（decoder-free, 不构业务矩阵, 不创 run_01, 不启 V72, V67/V69复用, 5函数D1-D10 A1-A6 benchmark f1.3）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R71-01 | 冻结主体 1024维纯因子核验证不改 + 不启 V72 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0 && successor_v72_not_started && rg -i "v72|qualification" 0 hits` |
| R71-02 | extrinsic 冻结 + 5函数纯枚举 log-domain | `ext=log_post-log_prior 冻结，5函数签名稳定，枚举1024态，全零⇒marginal delta⇒确定值 brute 1e-12，无I/O/随机` |
| R71-03 | D1-D10 十不变量正交完备 | `D1 completeness / D2 normalization / D3 marginal / D4 delta / D5 extrinsic / D6 stability / D7 determinism / D8 chain / D9 test_isolation / D10 orthogonality 逐项 PASS/FAIL 正交已验` |
| R71-04 | 只读 ldpc_v5* A1-A6 READY/ADAPTER/NOT_COMPATIBLE | `A1 interface / A2 policy_manifest / A3 channel_binding / A4 extrinsic_interface / A5 runtime_caps / A6 disclosure_accounting 每 session READY/ADAPTER/NOT_COMPATIBLE 已分流` |
| R71-05 | 仅 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈 | `仅1M session 1/9/1024 block 各 wall/peak 已测，1024-block wall≤30s && peak≤2048MiB 判 PASS，三档 per_invocation_ns 已报告` |
| R71-06 | f1.3 冻结 f_actual NOT_MEASURED | `f=1.3 frozen, required=ceil(1.3*1024*CE_full^{VAL_1M}), f_actual=="NOT_MEASURED" 全 session 已验` |
| R71-07 | V67/V69 三 Session Stage2 复用 CAL选VAL确认一次 | `v71 registry sessions==v69 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified, used_val_in_selection==False` |
| R71-08 | per-session 6终端总体4态 | `per-session EVIDENCE>MODEL>NOT_COMPATIBLE>READY>ADAPTER>HEAVY 互斥, overall EVIDENCE/MODEL/READY(3×)/ADAPTER_OR_HEAVY 已落盘` |
| R71-09 | 四工件+双报告完整 | `v71_data_registry + v71_results + v71_table.csv/json行对等 + V71_AUDIT_REPORT + V71_KERNEL_REPORT + v71_audit_report.json + test_v71_small.py py_compile+pytest PASS` |
| R71-10 | decoder-free 不构业务矩阵 + 不读 TEST + 不创 run_01 + 不启 V72 | `rg "decode_" 0 hits && rg "TEST" read 0 hits && used_test==False && ls v71_*/run_01 不存在 && py_compile PASS && V72_not_started` |
| R71-11 | 1024-state 数值闭合 | `1024 枚举 + logsumexp 归一 + K=1e6 log域稳定 + brute 1e-12 已验` |

## 9. 与 V64/V67/V69/V70/V71/V72 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208` 冻结构及 `22/24 PASS` 已固化；V67 3 sessions 均 `NEAR_FULL` 证 natural 5+5 不均衡；V69 `37170` 三层地图与 V70 `D_bits` 因子完整性正交复用 Stage2，不重估计；V71 为**1024-state 纯因子核 + ldpc_v5* 兼容地图**（`5函数 log-domain` + `D1-D10` + `A1-A6` + `1M benchmark`），不跑 decoder。
- 若 `V71_OVERALL_KERNEL_READY`（三 session 均 `READY && D1-D10 PASS && E PASS`）则纯因子核可零改对接 `ldpc_v5` 的 `error_channel` 适配；若 `ADAPTER` 则需适配层；若 `HEAVY` 则需降 block 或核优化；若 `NOT_COMPATIBLE` 则需新表示（另起 OpenSpec，但非 V72 本轮）。
- 本变更不创建 `run_01`，**不启动 V72**，任何 V71 后续核适配/decoder 需另起 `EXECUTE_AUTH`，V72 需独立 `OpenSpec` 且显式用户授权。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`H1/Lane C/Δ8/decoder/full-tag`），V71 仅验证纯因子核 + 兼容性，不改码（多 session audit + 1M benchmark），不启 V72。
- D2 单一估计器 `P(a|b)=(C_ab+λ P_global)/(N_b+λ)`，因子核仅为 10-bit 位展开的 Π factor `Σ bits*llr`，`λ` 单一全局 `1M CAL 4-fold`。
- D3 泄漏 `required=ceil1.3·N·CE_full` 不 cap，仅作 `A6` 披露参照，`f_actual NOT_MEASURED`。
- D4 数据 `Stage2 CAL1024 VAL256` 确定性复用 V69，不搜索多划分，TEST 隔离，V72 不启；Phase E 仅 1M benchmark 以控成本。
- D5 6终端 per-session + 4态 overall + D1-D10/A1-A6/E benchmark 正交审计，不以平均替代。
- D6 不产生新矩阵/码参数，仅 `D1-D10/audit/benchmark/f1.3` 与 successor 建议，`READY` 方可零改对接 `ldpc_v5`。
- D7 本变更为 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，任何 decoder/V72 需 `PLAN_ACCEPT + EXECUTE_AUTH` 后才允。
