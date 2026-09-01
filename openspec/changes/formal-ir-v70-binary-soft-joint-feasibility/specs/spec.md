# OpenSpec Spec: formal-ir-v70-binary-soft-joint-feasibility

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅plan四工件 + decoder-free二进制soft-joint因子完整性地图，不改1024维符号GF32两层验证，仅验证10-bit soft-joint factor保留完整1024-ary posterior，不跑decoder不构业务矩阵不读TEST不启V71

**Change**: `formal-ir-v70-binary-soft-joint-feasibility` (`V70-BSJ`, branch `formal-ir-mainline`, HEAD `d6f590ac6f30deaa8b0bf6cf5c419593fc037720`, data `84d62779`, 3 sessions复用V69 Stage2, 10-bit软联合A-H八等式，1024枚举纯函数，10240嵌套秩族)

**Predecessor**: `formal-ir-v69-three-layer-representation-feasibility` (`d6f590ac6f30deaa8b0bf6cf5c419593fc037720` `PLAN_CANDIDATE`) + `formal-ir-v67-multisession-feasibility-map` (`V67_FEASIBILITY_MAP_ACCEPTED`) + `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) — V70新增二进制soft-joint因子完整性地图，A-H全约束，decoder-free，不启V71

## 1. 变更类型与生命周期

- **Type**: `BINARY_SOFT_JOINT_FACTOR_FEASIBILITY_MAP` — 于V67/V69三预注册Session的`Stage2 CAL1024+VAL256`上，验证10-bit二进制soft-joint因子完整性：A-H八等式`D_bits=ΣH_bit - H_full≥0`，纯函数`soft_joint_factor_update(log_prior_1024, llr_10)→log_post_1024`枚举1024态全零得marginal delta得确定值与brute-force对照`|Δ|<1e-12`，预算`required=ceil(1.3·N·CE_full)`（`N=1024`）与`gap=10240-required`按`0`与`5%`三分流，嵌套二进制校验族`H_bin[required×10240]` `r0=160→required`前缀嵌套确切GF2秩非零不重复，CAL选VAL确认一次，每session 5终端总体4态。
- **Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于plan四工件 + decoder-free地图（`v70_data_registry.json + v70_binary_soft_joint_feasibility.py + v70_results.json + v70_table.{csv,json} + V70_BINARY_SOFT_JOINT_REPORT.md + test_v70_binary_soft_joint_small.py + v70_manifest.json`），**不实现runner，不执行decoder，不构业务矩阵，不创建`run_01`，不读VAL/TEST择优，不改1024维主体/V67/V69/src，不启动V71**；正式`run_01`需独立`PLAN_ACCEPT` + `EXECUTE_AUTH`；`DECODER_FREE`表示零`decode_*`业务调用（`rg 0 hits`），`V71_NOT_STARTED`表示零`V71_*/run_01`且`rg -i "v71|qualification" 0 hits`（除successor注释）。
- **Branch**: `formal-ir-mainline`；`HEAD` `d6f590ac6f30deaa8b0bf6cf5c419593fc037720`重核，不一致阻塞；已与`git rev-parse HEAD`一致。`TBD` 0 hits。
- **Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`) — V70复用V69三session Stage2 (`CAL1024+VAL256`)，不换点，不启V71。
- **Session bound**: `total 3 (=V69 3)`复用，`per_category 1,1,1`，不新增acquisition。
- **Rate feasibility**: **required=ceil(1.3·N·CE_full), gap=10240-required, margin_gap=gap/10240三分流`<0 / 0-5% / ≥5%`**，择优无，仅CAL选`λ` VAL确认`required/gap`，`H_bin`秩与`D≥0`与`pure<1e-12`同入`FEASIBLE`门禁。
- **Search space**: `1024`枚举纯函数（全零/ delta双极）+ `H_bin 10240`长`r0=160→required`前缀嵌套确切秩族（步长8或1，报告显式）。
- **V71**: **NOT_STARTED** — 本变更内禁止任何`V71` `QUALIFICATION_PLAN_READY / run_01 / 阈/码族`预冻结或产出。

## 2. 冻结方法（主体完全冻结，V70零改，仅验证soft-joint因子，不启V71）

### 2.1 主体不变量（V64完全冻结，V67/V69零改，V70仅因子验证）

- `n=1024 symbols/block` (`4×256 frames`), `q=1024 (10-bit s)`, `GF32 poly37`, `tag=64 bits/block`。
- `H1 = V31-H1-QC 16×1024 rank16 80b`母矩阵；`U自然 =32*U1+U2, F03 5+5`（`U1>>5, U2&31`）二层参照；`10-bit位展开 bit_i(s)=(s>>i)&1, i=0..9`与`soft_joint_factor_update`纯函数枚举1024态。
- `Lane C` ordinal-2 `s38310x`：`m2 base 1M 184 / 1p5M 190 / 2M 192`全冻。
- `H_inc1 8×1024 + H_joint1 192×1024` nested；`H_inc2 8×1024 + H_total 200×1024` nested；`rank_total==m2+16`等全冻，**本变更不构业务H**（`H_bin`验证族仅秩验证，不属业务码）。
- `decoder`: `decode_row_layered_fftqspa` `90/1.0 poly37 early-stop` (禁用至后续授权)；`rescue=verification-only`。
- `leak`: `leak = Σw_i·m_i+64`（二层参照），验证期仅`required/gap`不cap；`full-symbol tag s_hat compute`单64b。
- `budget 地图预冻结`: `V67/V69 Stage2 CAL1024+VAL256`每session，`TEST`密封，`required=ceil1.3·N·CE_full`与`gap=10240-required`三分流，`H_bin`秩前缀嵌套，`D≥0`与`pure<1e-12`同入`FEASIBLE`。
- `V67终态`: `3× NEAR_FULL`二层natural已固化，V70以二进制soft-joint因子完整性为检验假设；`V69` `37170`三层地图正交。
- `V71`: **NOT_STARTED** — 禁止本变更内任何V71预冻结。

### 2.2 处理点与物化单点冻结

- `84d62779`语义：`dimension 1024, bin_width 200ps, pairing nearest double-pointer bin//1024, rule legacy_v1, channels A1/B5, frame_len 256 pairs, BLOCK 1024, period 204800ps floor_div, threshold 40000ps, gate 200ps` — 单点，多session provenance，各session单独物化后位展开。
- `TEST`密封：任何`TEST/EVAL`域不计`CE/D/required/pure/rank`；`C_ab/P/CE/D/required/pure/rank`均`CAL/VAL`测，`TEST`不读，`λ`择优仅`CAL`，`V71`不启。
- **10-bit位展开与soft-joint因子**：`bit_i(s)=(s>>i)&1, i=0..9`与`soft_joint_factor_update(log_prior, llr_10)→log_post`枚举1024态，禁`Gray/MET/protograph/SC`外的重表示。

### 2.3 禁止

- 禁改任一冻结量、新增业务矩阵/标签/prior/阈值/decoder、试`Δ8`外degree/seed网格、跨acquisition拼接凑`3`、将`min(1024,ceil)` cap伪装当通过、将`VAL`数据用于`λ`择优、将零重叠仅比`frame_id`、引`MET/protograph/SC/Gray`、改`src/experiments/tools`任何文件；禁读`TEST`统计；**required不cap**（`ceil`显式，`gap=10240-required`显式）；禁纯函数单极校验（必须全零+ delta双极`1e-12`）；禁`D<0`可行；禁`rank≠r`可行；禁`gap`恒0掩饰三分流；禁构业务`H/matrix/rank/nested`；未授`EXECUTE_AUTH`前禁`decode_*`业务；**禁启V71**。

## 3. Phase A — 数据角色 (V69 Stage2复用，A-H软联合前置，不启V71)

### 3.1 角色与零重叠（键`(source,session,frame)`复用）

| 集合 | 每session规模 | 说明 |
|---|---|---|
| Stage2 CAL (Phase A) | 1024 frames (262144 pairs) | `C_ab→P_global→P(a|b) λ→H_full/CE_full/D` + 纯函数CAL校验 |
| Stage2 VAL (Phase B) | 256 frames (65536 pairs) | `CE_full/CE_bit/D/required/gap/margin/H_bin秩/纯函数VAL一致性一次确认` |
| TEST | 密封不读 | `used_test==False`，V71不启 |

- **复用**：`v70_data_registry.json`由`v69_data_registry.json` Stage2原样复用`sessions[3]`，`per_category 1,1,1`，`acquisition_dedup_verified:true`，`successor_v71_not_started:true`。
- **零重叠**：`CAL_key∩VAL_key==∅ && (CAL∪VAL)_key ∩ (V13..V69)_key ==∅`（键`(source,session,frame)`），`not_cross_spliced:true`。
- **注册表**：`v70_data_registry.json` (`schema v70_data_v1`)含`sessions[3] {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE, reused_from v69, successor_v71_not_started}`，禁止事后换session。
- **位展开**：`bit_i(s)=(s>>i)&1, i=0..9`已验双射。

### 3.2 数据就绪门

- `total==3 && per_category 1,1,1 && acquisition_dedup_verified && successor_v71_not_started`否则`EVIDENCE_INCOMPLETE`。
- `|CAL|==1024 && |VAL|==256 && CAL∩VAL==∅ && (CAL∪VAL)∩(V13..V69)==∅`否则`EVIDENCE_INCOMPLETE`。
- `frame 256` + `s∈[0,1023]`已验，否则`EVIDENCE_INCOMPLETE`。
- `10-bit位展开无丢：s == Σ bit_i<<i ∀s`已验，否则`EVIDENCE_INCOMPLETE`。

## 4. Phase B — 输入合同 strict V56 (仅10-bit位展开与soft-joint因子)

- **合同项**：`dimension 1024, bin 200, pairing nearest bin//1024, legacy_v1, channels A1/B5, U自然 32*U1+U2 5+5参照, 10-bit位展开bit_i(s) soft-joint因子, frame_start_ps, period 204800, floor_div, mapping legacy_v1, 每帧256`落`v70_manifest.json`。
- **权威算法**：`_read_ttbin_timetags → _bin_indices_sorted_for_binwidth → _pairs_from_sorted_bins → 256分组 → legacy_v1 → U (natural) → bit_i展开 → A-H D`原样复用，不重写。
- **不GE/MET/V71**：`rg -i "met|protograph|sc_coupling|v71|qualification" 0 hits`已验（soft-joint纯函数注释 + `V71_not_started`除外），`V71_not_started`已显式。

## 5. Phase C/D/E — A-H八等式 + 纯函数1024枚举 + 预算 + 嵌套族（CAL选VAL确认一次，不启V71）

### 5.1 C_ab与P_global (CAL-only per session)

```
C_ab[a,b] = bincount2d(a_cal, b_cal)  1024×1024, sum 262144 (CAL1024)
N_b[b] = Σ_a C_ab
P_global(a) = Σ_b C_ab / N_cal
Q=1024, N=1024
```

### 5.2 A-H八等式（CAL描述性 + VAL门禁性，TEST隔离，CAL-only择优）

```
A: P_global(a)= Σ_b C_ab / N_cal
B: P(a|b)= (C_ab+λ P_global)/(N_b+λ) (N_b>0); P_global (N_b==0); λ∈[1e-2,1e4] log10仅CAL内4-fold最小CV NLL
C: H_full^{CAL}= -E_{CAL heldout}[log2 P(A|B)], CE_full^{VAL}= -E_{VAL}[log2 P(A|B)]
D: D_bits= Σ_{i=0..9} H_bit_i - H_full ≥0 ; D^{CE}= Σ CE_bit_i - CE_full ≥ -1e-9
E: P(bit_i=v|b)= Σ_{a:bit_i(a)=v} P(a|b) → CE_bit_i= -E_{VAL}[log2 P(bit_i(A)|B)] (10维)
F: required= ceil(1.3·N·CE_full^{VAL})  (N=1024, bits/block, integer ceil)
G: soft_joint_factor_update (纯函数，见§5.3，枚举1024，全零→marginal delta→确定值 brute 1e-12)
H: H_bin ∈ GF2^{required×10240} (10240=10·N, r0=160→required前缀嵌套确切秩，非零不重复)
```

- **λ择优**：`λ∈[1e-2,1e4] log10`仅`CAL内4-fold`最小`CV NLL`，触界则`MODEL_NOT_STABLE`，不扩网格。`VAL`测时`λ`固定为`CAL`择优值，不重选。
- **阶段隔离**：`CAL`上得`H_full^{CV}/CE_full^{CV}/D^{CV}/λ`，`VAL`上`CE_full/D/required/gap/margin`仅度量确认，不重选`λ`，`used_val_in_selection==False && used_test==False`已验。
- **V71隔离**：任何V71预冻结禁止。

### 5.3 G — soft_joint_factor_update纯函数（枚举1024态，全零marginal delta确定值brute-force）

```
signature: soft_joint_factor_update(log_prior_1024: float[1024], llr_10: float[10]) -> log_post_1024: float[1024]
  log_prior[a] = log P(a|b) (自然对数，log2需显式ln2因子)
  llr_10[i] = log(P(bit_i=1)/P(bit_i=0)) 二进制软输入
  for a in 0..1023:
    bits = [(a>>i)&1 for i 0..9]
    log_post_unnorm[a] = log_prior[a] + Σ_i bits[i]*llr[i]   # 未归一化
  log_post[a] = log_post_unnorm[a] - logsumexp(log_post_unnorm)  # 归一化
  pure: 无I/O/随机/全局状态/TEST读

brute_force: 显式Π_i factor枚举1024态后归一化，与pure逐项 max|Δ|<1e-12
  all_zero: llr≡0 ⇒ llr_term≡0 ⇒ log_post ≡ log_prior - logsumexp(log_prior) ≡ log P(a|b)
  delta: 对a*，llr_i = (+K if bit_i(a*)=1 else -K), K=1e6 ⇒ 仅a*项最大 ⇒ posterior退化a* (log_post[a*]=0 其余=-inf)
```

- ponytail: `numpy.logaddexp.reduce`实现`logsumexp`，`K=1e6`的`exp`溢出用log域避免；`delta`验证取`a*=0,511,1023`三点。

### 5.4 F — 预算required与gap 0/5%三分流

```
CE_full^{VAL}= - (1/|VAL|) Σ_{(a,b)∈VAL} log2 P(a|b)  bits/symbol, VAL256 65536 pairs
required= ceil(1.3·N·CE_full^{VAL})  N=1024 bits/block integer
gap= 10240 - required; margin_gap= gap/10240; margin_vs_required= (required - required)/required =0
门禁三分: gap<0 ⇒ HEAVY, 0≤gap<512 ⇒ MARGINAL, gap≥512 ⇒ FEASIBLE  (512=5%·10240)
```

### 5.5 H — 嵌套二进制校验族10240长 r0→required前缀嵌套确切GF2秩

```
H_bin ∈ GF2^{required×10240}, 10240=10·N, col=sym*10+bit, r0=160
Rs= {r0, r0+8, r0+16, ..., required} 步长8（或1，报告显式）
∀r∈Rs: rank_{GF2}(H[0:r])==r (高斯消元GF2精确秩) ∧ ∀i weight(H[i])>0 ∧ ∀i≠j H[i]≠H[j] ∧ ∀r1<r2 H[0:r1]==H[0:r2][0:r1]前缀
生成: SeedSequence("V70-BSJ-H_bin") → numpy randint(0,2)筛滤至满足秩/非零/不重复
```

## 6. Phase F — 分流与总体 (per-session 5终端 + 总体4态，CAL选VAL确认一次)

### 6.1 Per-session 5终端（优先级高→低，互斥）

```
if not materialization_ok or frame_256_violation or D_chain_not_closed or C_ab_nonfinite or pure_brute_fail or rank_not_checked:
    classification = V70_EVIDENCE_INCOMPLETE; successor = recollect
elif λ_at_boundary or |CE_full^{VAL}-CE_full^{CV}|>0.50 or ∃i |CE_bit_i^{VAL}-CE_bit_i^{CV}|>0.50 or ΔNLL>0.50 or val_b_unseen>0.01 or not isfinite(ValNLL) or D<-1e-9 or pure_maxΔ>=1e-12:
    classification = V70_MODEL_NOT_STABLE; successor = recollect_or_new_prior
elif gap>=512 && rank_ok && D>= -1e-9 && pure_maxΔ<1e-12:  # margin_gap≥5%
    classification = V70_SOFT_JOINT_FEASIBLE; successor = v70_binary_soft_joint_code_design
elif 0<=gap<512 && rank_ok && D>= -1e-9 && pure_maxΔ<1e-12:
    classification = V70_SOFT_JOINT_MARGINAL; successor = v70_binary_soft_joint_code_design
else: # gap<0
    classification = V70_SOFT_JOINT_HEAVY; successor = v70_new_representation_or_recollect
```

- `LaneC+8+8`仅描述性，不入`FEASIBLE`门禁；`capacity_warning_m1/m2/disclosure`正交，仅描述不过门禁；旧三项`ValNLL>H+1 / H+0.5 / joint>1%`改归`descriptive_diagnostics`。

### 6.2 总体4态

```
common_preserving = #{sess | classification∈{FEASIBLE, MARGINAL}} # gap≥0 0..3
feasible_count = #{sess | FEASIBLE} # 0..3
marginal_count = #{sess | MARGINAL}
heavy_count = #{sess | HEAVY}
if any EVIDENCE_INCOMPLETE:
    overall = V70_OVERALL_EVIDENCE_INCOMPLETE
elif any MODEL_NOT_STABLE and common_preserving==0:
    overall = V70_OVERALL_MODEL_NOT_STABLE
elif common_preserving==3: # 三session均 margin≥0且D≥0且rank_ok且brute_ok
    overall = V70_OVERALL_SOFT_JOINT_PRESERVING
else:
    overall = V70_OVERALL_SOFT_JOINT_HEAVY
counts_per_classification = {EVIDENCE, MODEL, FEASIBLE, MARGINAL, HEAVY}
audit = {per_session_classification[3], overall, feasible/marginal/heavy counts, common_preserving, per_session_required/gap/D/pure_maxΔ/rank_ok}
```

## 7. Phase G — 报告与表 (per session A-H + 纯函数 + 预算 + 秩 + overall 4态)

- **表schema** (`v70_table.csv/.json`行对等, 每session 1行 + 总体4态汇总):
```
session_id, acquisition_id, source_label, provenance,
CAL: CAL_lambda, CAL_lambda_at_boundary, CAL_H_full, CAL_CE_full, CAL_CE_bit[10], CAL_D_bits, CAL_ValNLL, CAL_DeltaNLL, CAL_val_b_unseen, CAL_joint_unseen, CAL_q_mass (descriptive), CAL_effective_contexts,
VAL: CE_full, CE_bit[10], D_bits, chain_delta, ValNLL, DeltaNLL, DeltaCE=|CE^{VAL}-CE^{CV}|, val_b_unseen, joint_unseen, q_mass (descriptive), descriptive×3, capacity_warning, required, gap, margin_gap, margin_vs_required, r0, required_rows, rank_ok, prefix_ok, nonzero_ok, unique_ok,
pure: pure_brute_maxΔ_all_zero, pure_brute_maxΔ_delta_a0, pure_brute_maxΔ_delta_a511, pure_brute_maxΔ_delta_a1023, pure_is_pure,
classification (5终端), successor, cal_val_consistency, successor_v71_not_started
# 另汇总行: overall 4态 + feasible/marginal/heavy counts + common_preserving
```
- **报告** `V70_BINARY_SOFT_JOINT_REPORT.md`：`per session A-H/D/纯函数brute 1e-12/required/gap/margin 0/5%三分流/r0→required嵌套族秩前缀非零不重复 + overall 4态 + 预算三分流审计 + map_sparse + TEST隔离 + 1024维冻结 + V71_not_started`与`json/csv`一致，不扩大为`FER/SKR`。

## 8. 守卫 R70-01~10

| 守卫 | 条件 | 阈值 |
|---|---|---|
| R70-01 | 冻结主体1024维soft-joint验证不改 + 不启V71 | `n1024 q1024 GF32 poly37 H1 16×1024 rank16 10-bit位展开 Lane C/H_inc Δ8 decoder 90/1.0 full-tag git diff src==0 && successor_v71_not_started && rg -i "v71|qualification" 0 hits` |
| R70-02 | A-H八等式D_bits=ΣH-H_full≥0闭合 | `A P_global, B P(a|b) λ[1e-2,1e4], C H_full/CE_full, D D≥-1e-9, E CE_bit 10维, F required ceil, G pure函数, H H_bin`每session CAL/VAL双组D已验1e-9 |
| R70-03 | 纯函数soft_joint_factor_update 1024枚举全零marginal delta确定值brute-force | `枚举1024态, 全零⇒marginal max|Δ|<1e-12, delta⇒确定值, brute对照1e-12, 纯函数无I/O/随机` |
| R70-04 | 预算required=ceil1.3·N·CE_full显式 | `required=ceil(1.3*1024*CE_full^{VAL}) 整数ceil, log2一致, CAL选VAL确认一次不重选` |
| R70-05 | margin 0与5%三分流 | `gap=10240-required, margin_gap=gap/10240, <0 HEAVY / 0≤gap<512 MARGINAL / gap≥512 FEASIBLE已验` |
| R70-06 | 嵌套二进制校验族10240长 r0→required 前缀嵌套确切GF2秩 | `H_bin required×10240, r0=160, Rs=r0+8·k→required, ∀r rank==r精确GF2, 非零不重复, 前缀H_r==H_required[0:r]` |
| R70-07 | V67/V69三Session Stage2复用CAL选VAL确认一次 | `v70 registry sessions==v69 Stage2 3 sessions, total 3 per_cat 1,1,1 acq_dedup_verified zero_overlap_verified, used_val_in_selection==False` |
| R70-08 | per-session 5终端总体4态 | `per-session EVIDENCE>MODEL>FEASIBLE(≥5%)>MARGINAL(0-5%)>HEAVY 互斥, overall EVIDENCE/MODEL/PRESERVING(3×≥0)/HEAVY已落盘` |
| R70-09 | 四工件+test完整 | `v70_data_registry + v70_results + v70_table.csv/json行对等 + V70_REPORT + test_v70_small.py py_compile+pytest PASS` |
| R70-10 | decoder-free不构业务矩阵 + 不读TEST + 不创run_01 + 不启V71 | `rg "decode_" 0 hits && rg "TEST" read 0 hits && used_test==False && run_01不存在 && py_compile PASS && V71_not_started` |

## 9. 脚本与证据写出 (预冻结，decoder-free，不构业务矩阵，不启V71)

- **固定脚本**（本轮）：
  - `scripts/v70_binary_soft_joint_feasibility.py`: `CAL1024 C_ab/P/λ→H_full/CE_full/D→required/gap → pure 1024枚举brute双极校验 → VAL256 CE/D/required/gap/margin → H_bin 10240×required秩前缀校验 → 5终端/4态`，输出`v70_data_registry.json + v70_results.json + v70_table.(csv|json) + v70_manifest.json + V70_BINARY_SOFT_JOINT_REPORT.md`，`rg "decode_" 0 hits`，`rg -i "met|protograph|v71" 0 hits`（除V71_not_started注释），`py_compile PASS`，`required`未cap，`VAL`未参与λ择优，`D≥0`已验，`pure brute 1e-12`已验，`10240 r0→required秩`已验。
- **证据**：
```
openspec/changes/formal-ir-v70-binary-soft-joint-feasibility/  # 本轮plan四工件
scripts/v70_binary_soft_joint_feasibility.py  # decoder-free, 1024枚举纯函数 + A-H八等式 + 10240嵌套秩
v70_data_registry.json (复用V69 Stage2 3 sessions, V71_not_started)
v70_results.json (per session A-H/CE/D/required/gap/margin/纯函数brute/H_bin秩 + overall 4态)
v70_table.csv/.json (每session 1行 CE/D/required/gap/margin/r0/rank_ok/classification + overall汇总, 行对等)
V70_BINARY_SOFT_JOINT_REPORT.md
v70_manifest.json (frozen_body + guards R70-01~10 + A-H + pure + 秩指纹)
test_v70_binary_soft_joint_small.py
comparison_bench/outputs_comparison/formal_ir_methods/v70_binary_soft_joint/  # 未来run_01 (本轮不建, V71亦不建)
```
- **文件**：`v70_data_registry.json` (authoritative `3`实表，复用V69 Stage2) + `v70_results.json` + `v70_table` (行对等) + `v70_manifest.json` (frozen_body + guards + A-H + pure + 秩) + `V70_BINARY_SOFT_JOINT_REPORT.md` + 控制台摘要；本轮仅冻结计划，不创建正式run_01，**已单独提交推送新Plan SHA**，**V71_NOT_STARTED**。

## 10. 验收

- **本轮plan自检gate（A-H已闭合，不启V71）**：`py_compile PASS` spike，`rg "decode_" 0 hits`，`rg -i "met|protograph" 0 hits`，`rg -i "v71|qualification" 0 hits`（除V71_not_started注释），`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v6[0-9]/ ==0 && git diff -- openspec/changes/formal-ir-v70/ ==0` (除本变更+scripts外零改)，`VAL`未参与`λ`择优已验 (`used_val_in_selection==False`)，`TEST`未读已验 (`used_test==False`)，`required`未cap伪装已验 (`grep "min(1024" 0 hits`且`required ceil`显式 `gap=10240-required`)，`A-H D≥-1e-9`已验，`pure 1024枚举全零marginal delta确定值brute 1e-12`已验，`H_bin 10240长r0→required前缀嵌套确切GF2秩非零不重复`已验，`gap 0/5%三分流`已验，`5终端优先级互斥`已验，`overall 4态`已验，`V69 Stage2复用3`已验，`VAL确认一次`已验，`capacity_warning`正交与`descriptive`已落盘，`run_01`不存在已验，`V71_not_started`已验，**报告表与json一致**，`TBD` 0 hits。
- **本轮仅plan四工件+registry+spike+报告表（A-H八等式 + 纯函数1024枚举双极brute + required ceil + gap 0/5% + 10240嵌套秩）**，任何`V70`后的二进制码设计/decoder需`Plan SHA` + `v70_data_registry.json`实表 + `A-H/纯函数/预算/秩`已验后、且独立`PLAN_ACCEPT` + `EXECUTE_AUTH`后才允许创建正式实现并执行；`DECODER_FREE`保持至授权，**V71保持NOT_STARTED**。
