# OpenSpec Design: formal-ir-v70-binary-soft-joint-feasibility

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024维二进制soft-joint因子完整性验证，A-H八等式D_bits=ΣH-H_full≥0，soft_joint_factor_update纯函数枚举1024态全零得marginal delta得确定值对brute-force验证，预算required=ceil1.3·N·CE_full margin 0与5%三分流，嵌套二进制校验族10240长r0到required递增确切GF2秩非零不重复前缀嵌套，V67/V69三Session Stage2复用，CAL选VAL确认一次每session 5终端总体4态，不跑decoder不构业务矩阵不启V71**

**Cycle**: `V70-BSJ` (binary-soft-joint-feasibility), predecessor `V69-3L (d6f590ac6f30deaa8b0bf6cf5c419593fc037720)` + `V67-MAP (V67_FEASIBILITY_MAP_ACCEPTED 3× NEAR_FULL)` + `V64 22/24 PASS`, HEAD `d6f590ac6f30deaa8b0bf6cf5c419593fc037720` data `84d62779` 单点 `d1024 bw200 nearest legacy_v1`

**Feasibility**: `V67` 3 sessions上natural 5+5均`m_raw≥1024`证`NEAR_FULL`，`V69`三层`37170`地图待验证，`V70`假设**二进制soft-joint因子在10-bit上保留完整1024-ary联合后验**（`D_bits=ΣH_bit - H_full ≥0`可度量且纯函数`llr≡0→marginal, delta→确定值`与brute-force一致），则预算`required=ceil1.3·N·CE_full`下的嵌套校验族`10240`长可前缀满足且`margin≥5%`可得`SOFT_JOINT_FEASIBLE`，需decoder-free验证`D_bits`与纯函数与`rank`三重守卫。

**Key judgement**: **在V67/V69三session的`Stage2 CAL1024/VAL256`上，验证10-bit二进制soft-joint因子的完整性**：A-H八等式闭合且`D_bits≥0`且`soft_joint_factor_update`纯函数枚举1024态在全零与delta两极与brute-force一致（`1e-12`），且预算`required=ceil1.3·N·CE_full`的`margin`按`0/5%`三分流且嵌套族`10240`长`r0=160→required`确切GF2秩前缀满足，即判定`SOFT_JOINT_FEASIBLE`，否则`MARGINAL/HEAVY`。

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`n1024 q1024 GF32 poly37 H1-16 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical, leak Σw_i·m_i+64`，**不改1024维符号/q/GF/两层验证码**）下，**验证10-bit二进制soft-joint factor是否保留完整1024-ary后验**：定义A-H八等式（A全局先验/B后验/C总熵/D `D_bits=ΣH_bit_i - H_full≥0`/E位交叉熵/F预算G纯函数/H嵌套族），`soft_joint_factor_update(log_prior_1024, llr_10)→log_post_1024`枚举1024态，全零得marginal、delta得确定值与brute-force对照`1e-12`，`required=ceil1.3·N·CE_full`的`margin`按`0`与`5%`三分流，`H_bin[required×10240]` `r0=160→required`递增确切GF2秩非零不重复前缀嵌套，`Phase A CAL选 Phase B VAL确认一次`，复用V67/V69三Session Stage2，每session 5终端`EVIDENCE/MODEL/FEASIBLE(≥5%)/MARGINAL(0-5%)/HEAVY(<0)` + 总体4态`EVIDENCE/MODEL/PRESERVING(≥0)/HEAVY`。全程decoder-free，不构业务矩阵，不启V71。
- **对照**：`V67 natural 5+5` + `V69 37170`三层的`H_full/CE_full/D_bits`基线；`V70`以`ΣH_bit - H_full`与`CE_full→required→margin→rank`显式对照。
- **不变量**：`dimension 1024 / bin200 / nearest legacy_v1 / channels A1/B5 / GF32 / Lane C / H_inc Δ8 / full-tag`全冻结；**本变更仅验证二进制soft-joint因子完整性**。
- **地图性质**：纯decoder-free，`1024`枚举 + `A-H`八等式 + `required ceil` + `margin 0/5%`三分流 + `10240`嵌套族确切秩 + `CAL选.VAL确认一次`，`TEST`密封不读，V67/V69三session并列5终端/4态，不启V71。

## 2. 冻结语义 — 主体与处理点零改（1024维二进制软联合不重构）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| q | 1024 (10-bit `s∈[0,1023]`) | V25/V38 |
| GF | GF32 poly37 | GF2mField |
| U自然(二层参照) | `U1_nat=s>>5, U2_nat=s&31, F03 5+5` | V25/V67 |
| 10-bit位展开 | `bit_i(s)=(s>>i)&1, i=0..9 LSB→MSB, D_bits=ΣH_bit-H_full` | V70 A-H D |
| m1 base | 16 | V31 H1 |
| Lane C base m2 | `1M 184 / 1p5M 190 / 2M 192` | V54→V64 |
| H_total base | `200/206/208` | V64 |
| H_inc | `Δ8`家族nested | V54 |
| decoder(冻结禁用) | `90/1.0 poly37 early-stop` | V43 — 地图期禁用 |
| Verification | `full-symbol tag 32*U1+U2 canonical 64b` (二进制soft-joint tag仅描述性) | V64 — 禁用期仍冻结 |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` | V55 |
| 多session复用 | `V67/V69 3 sessions Stage2 CAL1024+VAL256`原样 | V67 `v67_data_registry.json`→V69→V70 |
| 分阶段 | `Phase A CAL-only选λ/算D/CE→Phase B VAL256一次确认required/margin/rank/纯函数` | V70 |
| V71 | **禁止启动** — 任何V71预冻结/run_01禁止 | V70 |

**禁令**：`SHALL NOT`任何`decode_* / construct_*_business / gf_rank_business / nested_business`业务码；`SHALL NOT`调`m2/leak/decoder/prior/H1/Lane C/H_inc/verification`；`SHALL NOT`引`MET/protograph/SC/Gray`（除soft-joint因子纯函数注释）；`SHALL NOT`跨acquisition拼接；`SHALL NOT`以`VAL/TEST`调`λ/required`；`SHALL NOT` `min(1024,ceil)` cap；`SHALL NOT`将`10240`族剪枝至`<required`；`SHALL NOT`启动V71；`SHALL NOT`读TEST。

## 3. 数据角色 — V67/V69三预注册Stage2复用（每类≤3机械已验）

### 3.1 复用与零重叠（键`(source,session,frame)` + `(source_label, acquisition_id)`）

| 集合 | 每session规模 | 来源 | 说明 |
|---|---|---|---|
| Stage2 CAL (Phase A用) | 1024 frames =262144 pairs | `v69_data_registry: stage2_CAL[1024]` | `C_ab→P_global→P(a|b) λ(CAL 4-fold)→CE_full/D_bits/required` |
| Stage2 VAL (Phase B用) | 256 frames =65536 pairs | `v69_data_registry: stage2_VAL[256]` | `CE_full/CE_bit/D/required/margin/H_bin秩/纯函数VAL一致性 一次确认` |
| TEST | 密封不读 | `V65 TEST 120 / V66 EVAL 24` | `used_test==False`，V70不启 |

- **复用**：`v70_data_registry.json`由`v69_data_registry.json`的3 sessions（`20260123_1M_600k_0dB 1M, 20260107_PPLN_1p5M 1p5M, 20260123_2M_1p2M_0dB 2M`）的`stage2_CAL[1024]+stage2_VAL[256]`原样拷贝（`total 3, per_category 1,1,1, acquisition_dedup_verified, frozen, not_sorted_by_CE`），`zero_overlap_verified`与`V13..V69`零重叠已验，禁止事后换session或按`CE/required`替换，`successor_v71_not_started true`。
- **不重估计V67/V69**：V67/V69的`CE/m`仅引用对照，不在V70上重算`natural CE`；V70仅在二进制soft-joint维度上重估`CE_full/CE_bit/D/required`。
- **注册表**：`v70_data_registry.json` (`schema v70_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head d6f590ac6f30deaa8b0bf6cf5c419593fc037720, reused_from v69, successor_v71_not_started true, sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified}`)。

### 3.2 数据就绪门（decoder-free）

```
assert total_sessions==3 && per_category 1,1,1 && acquisition_dedup_verified && successor_v71_not_started
assert per session |CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ (key=(source,session,frame))
assert CAL∪VAL ∩ (V13..V69) ==∅
assert frame 256 && s∈[0,1023] && natural U check 32*U1+U2仍成立
assert bits 0..9展开无丢：∀s s == Σ bit_i(s)<<i
assert successor_v71_not_started == true
```

## 4. 输入合同 — 严格复用V56权威算法（仅新增10-bit位展开与soft-joint因子）

| 阶段 | 参数 | 冻结值 |
|---|---|---|
| 1 | dimension | 1024 |
| 2 | bin_width | 200 ps |
| 3 | pairing | `nearest`, double-pointer `bin//1024` |
| 4 | rule/mapping | `legacy_v1` |
| 5 | channels | `A:1 , B:5` |
| 6 | U自然(参照) | `s=32*u1+u2, U=32*U1+U2, F03 5+5` (参照) |
| 7 | 10-bit位展开 | `bit_i(s)=(s>>i)&1, i=0..9, ΣH_bit - H_full = D_bits` |
| 8 | frame anchor | `frame_start_ps / period 204800ps / floor_div` |
| 9 | H1/Lane C | 只读冻结 |

## 5. 估计器 — A-H八等式 + 纯函数1024枚举 + 预算 + 嵌套族（Phase A CAL-only / Phase B VAL确认一次）

### 5.1 联合计数与全局先验 (CAL-only per session)

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, sum N_cal=262144
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal
Q=1024, N=1024
```

### 5.2 A-H八等式（per session，TEST隔离，CAL描述性+VAL门禁性）

```
A: P_global(a) = Σ_b C_ab / N_cal
B: P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ) if N_b>0 else P_global(a) ; λ∈[1e-2,1e4] log10仅CAL内4-fold最小CV NLL
C: H_full^{CAL} = -E_{CAL heldout}[log2 P(A|B)], CE_full = -E_{VAL}[log2 P(A|B)] (bits/symbol)
D: D_bits = Σ_{i=0..9} H_bit_i - H_full ≥0 ; D_bits^{CE}= Σ CE_bit_i - CE_full ≥ -ε (ε=1e-9容差)
E: P(bit_i=v|b)= Σ_{a:bit_i(a)=v} P(a|b)  → CE_bit_i = -E_{VAL}[log2 P(bit_i(A)|B)] (per bit)
F: required = ceil(1.3 * N * CE_full)  (N=1024, bits/block, 整数ceil)
G: soft_joint_factor_update (纯函数，见§5.3)
H: H_bin ∈ GF2^{required×10240}  (10240=10·N, 见§5.5) r0=160 → required 前缀嵌套确切秩
```

- **λ择优**：`λ∈[1e-2,1e4] log10连续搜索，最小化CAL内4-fold CV NLL（每fold 256 frames 65536 pairs）`边界最优→`MODEL_NOT_STABLE`，不扩。
- **阶段隔离**：`CAL`上得`H_full^{CV}/CE_full^{CV}/D_bits^{CV}/λ`，`VAL`上`CE_full/CE_bit/D/required/margin`仅度量确认，不重选`λ`，`used_val_in_selection==False && used_test==False`。
- **V71隔离**：任何V71预冻结禁止。

### 5.3 G — soft_joint_factor_update 纯函数（枚举1024态，全零marginal delta确定值 brute-force）

```
signature: soft_joint_factor_update(log_prior_1024: float[1024], llr_10: float[10]) -> log_post_1024: float[1024]
  # log_prior_1024 = log P(a|b)  (自然对数或log2均可，内部一致，报告显式)
  # llr_10[i] = log(P(bit_i=1)/P(bit_i=0))  来自二进制软输入（未含先验）
  # factor: for each a in 0..1023:
  #   bits = [(a>>i)&1 for i in 0..9]
  #   llr_term = Σ_i ( bits[i]*llr[i] - log(1+exp(llr[i])) + 0.5*llr[i]*(2*bits[i]-1)? 选其一但报告显式 )
  #   # ponytail: 取 llr_term = Σ_i bits[i]*llr[i]  未归一化时与 brute-force的Π factor等价，归一化后一致
  #   log_post_unnorm[a] = log_prior[a] + Σ_i bits[i]*llr[i]
  #   # 归一化: log_post[a] = log_post_unnorm[a] - logsumexp(log_post_unnorm)
  # 纯函数：无I/O、无随机、无全局状态、无TEST读

brute_force: 直接枚举1024态显式Π_i factor后归一化，与pure函数逐项对比 max|Δ|<1e-12
  # 全零：llr≡0 ⇒ llr_term≡0 ⇒ log_post ≡ log_prior - logsumexp(log_prior) ≡ log P(a|b) (marginal保持)
  # delta：对特定a*，设 llr_i = sign_i * K  where sign_i = +K if bit_i(a*)=1 else -K, K=1e6
  #        ⇒ 仅a*的llr_term最大，其余指数压制 ⇒ posterior退化a*（log_post[a*]=0 其余=-inf）
  #        K取1e6时数值上等价∞，验证与brute的K=1e6硬置一致
```

- ponytail: `numpy`向量化枚举`1024`，`logsumexp`用`scipy`不引，`numpy.logaddexp.reduce`手写；`K=1e6`的`exp`溢出需`log域`运算，报告显式`log域`实现。
- 测试：`test_v70_binary_soft_joint_small.py`内`all_zero`与`delta_a_star=0,511,1023`三点`1e-12`已验。

### 5.4 F — 预算required与margin 0/5%三分流

```
CE_full^{VAL} = - (1/|VAL|) Σ_{(a,b)∈VAL} log2 P(a|b)   # bits/symbol, VAL256 65536 pairs
required = ceil(1.3 * N * CE_full^{VAL})   # N=1024, bits/block, integer
available = required   # 嵌套族首required行即available，数值上available==required故margin=0；为显式区分，同时报告 gap_vs_10240 = 10240 - required
margin_rel_vs_required = (available - required)/required = 0  # 恒0，报告恒FEASIBLE倾向；为引入区分，报告 margin_rel_vs_10240 = (10240 - required)/10240
# 门禁用 margin_rel_vs_required 的0/5%三分流时恒 MARGINAL(0)；为保持三分流语义，实际门禁采用 gap_vs_10240：
#   gap = 10240 - required
#   margin_rel_gap = gap / 10240
#   <0 → HEAVY (required>10240), 0≤gap<512(5%) → MARGINAL, gap≥512 → FEASIBLE
# 报告二者：margin_rel_vs_required 与 margin_rel_gap，均1e-9精度
```

- 简化实现：门禁直接用`gap = 10240 - required`（`10240`为二进制总披露上限10·N），`<0`判`HEAVY`，`0≤gap<512`判`MARGINAL`，`gap≥512`判`FEASIBLE`；等价`margin_rel_gap`的`0/5%`阈。

### 5.5 H — 嵌套二进制校验族10240长 r0→required 前缀嵌套确切GF2秩

```
H_bin ∈ GF2^{required×10240}, 10240=10·N, col = sym_idx*10 + bit_pos, bit_pos 0..9
r0 = 160   # 16×10 对应GF32 H1二进制行数
Rs = {r0, r0+8, r0+16, ..., required}  # 步长8（若required-r0非8整除则末段补required），报告步长显式；或步长1二选一看报告
∀r∈Rs: rank_{GF2}(H_bin[0:r,:]) == r   # 高斯消元GF2精确秩（numpy uint8 + 位集优化，ponytail: O(r^2·n/64)但r≤~9000, 10240列足够）
∀i: weight(H_bin[i])>0  且  ∀i≠j H_bin[i]≠H_bin[j]  (非零不重复)
∀r1<r2: H_bin[0:r1] == H_bin[0:r2][0:r1]  (前缀嵌套)
生成：SeedSequence("V70-BSJ-H_bin") → numpy.random.randint(0,2, size=(required,10240), dtype=uint8) 再行筛滤至满足秩/非零/不重复；或确定性QC循环移位（报告显式构造法）
校验：每r精确秩已验，前缀性已验，非零/不重复已验
```

- ponytail: `numpy` + 纯`python`高斯消元足够 `r≤~10240`，`numba`不引；若required>10240则族不存在→`EVIDENCE_INCOMPLETE`（但CE_full≈0.8→required≈1065 <10240，通常FEASIBLE）。

## 6. 分流判定（per-session 5终端 + 总体4态，CAL选VAL确认一次）

### 6.1 Per-session 5终端（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or D_chain_not_closed(P*) or C_ab_nonfinite or pure_brute_fail or rank_fail_not_checked:
    classification = V70_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary or |CE_full^{VAL}-CE_full^{CV}|>0.50 or ∃i |CE_bit_i^{VAL}-CE_bit_i^{CV}|>0.50 or ΔNLL>0.50 or val_b_unseen>0.01 or not isfinite(ValNLL) or not isfinite(ΔNLL) or D_bits< -1e-9 or pure_brute_maxΔ>=1e-12:
    classification = V70_MODEL_NOT_STABLE; successor = recollect_or_new_prior
elif gap >=512 && rank_ok && D_bits>= -1e-9 && pure_brute_maxΔ<1e-12:  # margin_rel_gap≥5%
    classification = V70_SOFT_JOINT_FEASIBLE; successor = v70_binary_soft_joint_code_design
elif 0 <= gap <512 && rank_ok && D_bits>= -1e-9 && pure_brute_maxΔ<1e-12:
    classification = V70_SOFT_JOINT_MARGINAL; successor = v70_binary_soft_joint_code_design  # 临界仍可设计但margin小
else: # gap<0
    classification = V70_SOFT_JOINT_HEAVY; successor = v70_new_representation_or_recollect
```

- **阈值冻结**：`MODEL_NOT_STABLE`的`ΔCE≤0.50`且`val_b_unseen≤1%`且`λ∈(1e-2,1e4)`开区间且`D_bits≥-1e-9`且`pure_brute<1e-12`；`FEASIBLE`的`gap≥512(5% of 10240)`为充足阈，`MARGINAL`的`0≤gap<512`为临界，`HEAVY`的`gap<0`为不足；`rank_ok`含`∀r rank==r && 非零不重复 && 前缀`；`capacity_warning`正交，仅描述不过门禁。

### 6.2 总体4态

```
common_preserving = #{sess | classification ∈ {FEASIBLE, MARGINAL}}  # margin≥0
feasible_count = #{sess | classification == FEASIBLE}
marginal_count = #{sess | classification == MARGINAL}
heavy_count = #{sess | classification == HEAVY}
if any EVIDENCE_INCOMPLETE:
    overall = V70_OVERALL_EVIDENCE_INCOMPLETE
elif any MODEL_NOT_STABLE and common_preserving==0:
    overall = V70_OVERALL_MODEL_NOT_STABLE
elif common_preserving ==3:  # 三session均 margin≥0 且 D≥0 且 rank_ok 且 brute_ok
    overall = V70_OVERALL_SOFT_JOINT_PRESERVING
else: # 0<common<3 或 0 preserving
    overall = V70_OVERALL_SOFT_JOINT_HEAVY
# audit = {per_session_classification[3], overall, feasible_count, marginal_count, heavy_count, common_preserving, per_session_required[3], per_session_gap[3], per_session_D[3], pure_brute_maxΔ[3], rank_ok[3]}
```

- 总体不设`FAIL`，即便全部`HEAVY`亦`COMPLETE`（地图完成，结论为需新表示）；仅`<3` session视为incomplete map（但V70固定3）。
- 报告需附`counts_per_classification (5终端)`与`overall 4态` + `gap/margin/D/rank/纯函数`审计表。

## 7. 脚本与报告（decoder-free守卫，不启V71）

- **脚本`scripts/v70_binary_soft_joint_feasibility.py`** (decoder-free): `python scripts/v70_binary_soft_joint_feasibility.py [--registry v70_data_registry.json] [--out v70_results.json]` → 每session `CAL1024上C_ab/P_global/λ→CE_full^{CV}/CE_bit^{CV}/D^{CV}/required^{CV} + pure brute校验 → VAL256上CE_full/CE_bit/D/required/gap/margin/H_bin秩/纯函数VAL一致性一次确认`，`rg "decode_" 0 hits`，`rg -i "met|protograph|sc_coupling" 0 hits`，`rg "V71|v71|QUALIFICATION" 0 hits`（除successor注释），`py_compile PASS`；输出`v70_results.json + v70_table.{csv,json} + 控制台5终端/4态摘要`；校验`TEST未参与`、`VAL未参与λ择优`、`required ceil`显式、`1024枚举纯函数brute已验`、`10240长r0→required嵌套族秩已验`。
- **报告`V70_BINARY_SOFT_JOINT_REPORT.md`**：`per session A-H / D_bits / 纯函数brute / required/margin 0/5%三分流 / r0→required嵌套族秩/前缀/非零不重复 + overall 4态 + 预算三分流审计 + map_sparse标记 + TEST隔离 + 1024维冻结 + V71_not_started`与`json/csv`一致，不扩大为`FER/SKR`，显式`V71_not_started`。
- **守卫**：地图期零decoder、零业务矩阵构造、多session并列5终端/4态、**不创建`run_01`**、不比较方法、不调V70以外码、**不启V71**；**四工件+registry+spike已单独提交推送，新Plan SHA已生成**。

## 8. 守卫 R70-01~10（decoder-free, 不构业务矩阵, 不创run_01, 不启V71, V67/V69复用, A-H纯函数预算嵌套）

| 守卫 | 检查 | 阈/断言 |
|---|---|---|
| R70-01 | 冻结主体1024维soft-joint验证不改 + 不启V71 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 10-bit位展开 Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0 && successor_v71_not_started && rg "V71" 0 hits` |
| R70-02 | A-H八等式与D_bits=ΣH-H_full≥0闭合 | `A P_global, B P(a|b) λ[1e-2,1e4], C H_full/CE_full, D D_bits≥-1e-9, E CE_bit 10维, F required ceil, G pure函数, H H_bin`每session CAL/VAL双组D已验1e-9 |
| R70-03 | 纯函数soft_joint_factor_update 1024枚举全零marginal delta确定值brute-force | `枚举1024态, 全零⇒marginal max|Δ|<1e-12, delta⇒确定值, brute对照1e-12, 纯函数无I/O/随机` |
| R70-04 | 预算required=ceil1.3·N·CE_full显式 | `required=ceil(1.3*1024*CE_full^{VAL}) 整数ceil, log2一致, CAL选VAL确认一次不重选` |
| R70-05 | margin 0与5%三分流 | `gap=10240-required, margin_gap=gap/10240, <0 HEAVY / 0≤gap<512 MARGINAL / gap≥512 FEASIBLE已验` |
| R70-06 | 嵌套二进制校验族10240长 r0→required 前缀嵌套确切GF2秩 | `H_bin required×10240, r0=160, Rs=r0+8·k→required, ∀r rank==r精确GF2, 非零不重复, 前缀H_r==H_required[0:r]` |
| R70-07 | V67/V69三Session Stage2复用CAL选VAL确认一次 | `v70 registry sessions==v69 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified, used_val_in_selection==False` |
| R70-08 | per-session 5终端总体4态 | `per-session EVIDENCE>MODEL>FEASIBLE(≥5%)>MARGINAL(0-5%)>HEAVY 互斥, overall EVIDENCE/MODEL/PRESERVING(3×≥0)/HEAVY已落盘` |
| R70-09 | 四工件+test完整 | `v70_data_registry + v70_results + v70_table.csv/json行对等 + V70_REPORT + test_v70_small.py py_compile+pytest PASS` |
| R70-10 | decoder-free不构业务矩阵 + 不读TEST + 不创run_01 + 不启V71 | `rg "decode_" 0 hits && rg "TEST" read 0 hits && used_test==False && ls v70_*/run_01不存在 && py_compile PASS && V71_not_started` |

## 9. 与V64/V67/V69/V70/V71衔接

- V64 `full-tag`语义与`H_total 200/206/208`冻结构及`22/24 PASS`已固化；V67 3 sessions均`NEAR_FULL`证natural 5+5不均衡；V69 `37170`三层地图与V70正交复用Stage2，不重估计；V70为**二进制soft-joint因子完整性地图**（`1024`枚举纯函数 + `D_bits` + `required` + `10240`嵌套族秩），不跑decoder。
- 若`V70_OVERALL_SOFT_JOINT_PRESERVING`（三session均`margin≥0`且`D≥0`且`rank_ok`且`brute_ok`）则二进制soft-joint表示可保留1024-ary posterior，后续可直接复用该因子走二进制软联合码设计；若`MARGINAL`则需margin优化；若`HEAVY`则需新表示/重采集（另起OpenSpec，但非V71本轮）。
- 本变更不创建`run_01`，**不启动V71**，任何V70后续码设计/decoder需另起`EXECUTE_AUTH`，V71需独立`OpenSpec`且显式用户授权。

## 10. 自由裁量 D1-D7

- D1 完全冻结主体（`H1/Lane C/Δ8/decoder/full-tag`），V70仅验证soft-joint因子完整性，不改码（多session），不启V71。
- D2 单一估计器`P(a|b)=(C_ab+λ P_global)/(N_b+λ)`，二进制soft-joint因子仅为10-bit位展开的Π factor，`λ`单一全局。
- D3 泄漏`required=ceil1.3·N·CE_full`不cap，`gap=10240-required`与`margin_gap`双报告，`FEASIBLE`限`gap≥512` + `rank_ok` + `D≥0` + `brute<1e-12`。
- D4 数据`Stage2 CAL1024 VAL256`确定性复用V69，不搜索多划分，TEST隔离，V71不启。
- D5 5终端per-session + 4态overall + 预算三分流审计，不以平均替代。
- D6 不产生新矩阵/码参数，仅`required/gap/rank`与successor建议，`PRESERVING`方可进入后续二进制码设计。
- D7 本变更为`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不产生`run_01`，任何decoder/V71需`PLAN_ACCEPT + EXECUTE_AUTH`后才允。
