# OpenSpec Proposal: formal-ir-v70-binary-soft-joint-feasibility

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅计划四工件 + decoder-free 二进制 soft-joint 因子完整性可行性验证，不改1024维符号/GF32/验证框架，不跑 decoder 不构业务矩阵，仅验证10-bit soft-joint factor 是否保留完整1024-ary后验

**Domain**: Formal IR / NB-LDPC binary soft-joint factor feasibility (V69 同域直接后继，V67/V69 三预注册Stage2复用)

**Change ID**: `formal-ir-v70-binary-soft-joint-feasibility`

**Cycle ID**: `V70-BSJ` (binary-soft-joint-feasibility), predecessor `formal-ir-v69-three-layer-representation-feasibility` (`d6f590ac6f30deaa8b0bf6cf5c419593fc037720` V69 `PLAN_CANDIDATE/DECODER_FREE`) + `formal-ir-v67-multisession-feasibility-map` (`V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL` natural 5+5) + `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`)

**Branch**: `formal-ir-mainline`

**HEAD**: `9bc34be64a2822c8babb4320efb47fc7e335a21a` (implementation 9bc34be6; provenance deviation: registry/report head 9825d0b336042ad4bf2b26ed31b7fa09a04de620 vs implementation 9bc34be6, report 已记 provenance 9825d0b not d6f590ac; 推送后以 `git rev-parse HEAD == origin/formal-ir-mainline` 40位重核，不一致阻塞)

**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点；V70复用V67/V69三session的`Stage2 CAL1024+VAL256`，不换点，不换bin/mapping，不新增acquisition)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + decoder-free软联合因子完整性地图（registry复用 + spike枚举1024态纯函数 + results + table + report + small test），零decoder/业务矩阵/新依赖（`numpy/pandas/pyarrow`已装），不创建`run_01`，不比较方法，不转qualification，不启动V71，任何decoder执行需独立`PLAN_ACCEPT + EXECUTE_AUTH`

> ponytail lite: 本变更仅4 OpenSpec工件 + 1 decoder-free spike（枚举1024态 `numpy` 直算`C_ab 1024×1024` + 10-bit软联合因子纯函数 `soft_joint_factor_update`，`itertools`无需，不引`scipy/sklearn`）+ 1结果表 + 1报告 + 1小测试；零decoder/矩阵/新依赖，最短科学路径。

> **科学问题（冻结）**：于**完全冻结主体**（`n=1024, q=1024 (10-bit), GF32 poly37, H1 16×1024 rank16, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37, full-tag canonical 32*U1+U2(+U3)扩展, leak Σw_i·m_i+64`全只读，**不改维度/符号/q/GF/两层验证**）下，**验证10-bit二进制 soft-joint factor 是否保留完整1024-ary联合后验**：定义**A-H八等式**（A全局先验/B条件后验/C总熵F/B位熵/D信息冗余`D_bits=ΣH_bit_i - H_full ≥0`/E交叉熵链式/F预算/G纯函数/H嵌套校验族），以`CAL1024`独立估计`P(A|B)`在`VAL256`上得`CE_full`，纯函数`soft_joint_factor_update(log_prior_1024, llr_10)→log_posterior_1024`枚举1024态，**全零得marginal、delta得确定值与brute-force对照**，预算`required=ceil(1.3·N·CE_full)`（`N=1024`）计算`margin`按`0`与`5%`三分流，嵌套二进制校验族`10240`长（`10·N`）从`r0=160`起始到`required`递增确切GF2秩、非零不重复、前缀嵌套，`Phase A CAL选 Phase B VAL确认一次`，每session 5终端总体4态，产出四工件，不跑decoder不改src不读TEST不启V71。

## Goal

以最短decoder-free路径完成**二进制soft-joint因子完整性可行性地图**，为V67`NEAR_FULL`/V69三层重划分后是否需二进制软联合表示提供可验证证据：

### 1. 仅验证10-bit soft-joint factor是否保留完整1024-ary posterior，不改1024维符号GF32验证框架
- **冻结**：`n=1024, q=1024 (10-bit s∈[0,1023]), GF32 poly37, H1 16×1024 rank16 80b U=32*U1+U2, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0, full-tag canonical`全只读（`git diff -- src/ ==0`），处理点`84d62779 legacy_v1`单点，`per frame 256, BLOCK 1024, period 204800`等同V67/V69。
- **唯一变量**：二进制soft-joint因子`soft_joint_factor_update`：对10-bit符号`s`的位展开`bit_i(s)=(s>>i)&1, i=0..9`，输入每符号先验`log_prior[1024]=log P(a|b)` + 10维LLR向量`llr[10]`，输出联合后验`log_post[1024]`，纯函数枚举1024态，不改`s`本身，不引`Gray/MET/protograph/SC`。

### 2. 定义A-H八等式，D_bits=ΣH-H_full≥0，soft_joint_factor_update纯函数枚举1024态全零得marginal delta得确定值对brute-force验证
- **A-H**：
  - A `P_global(a)=Σ_b C_ab/N_cal`
  - B `P(a|b)=(C_ab+λ P_global)/(N_b+λ)`（`λ`仅CAL内4-fold择优`[1e-2,1e4]`）
  - C `H_full = H(A|B) = -E_{CAL}[log2 P(A|B)]` 及 `CE_full = -E_{VAL}[log2 P(A|B)]`
  - D `D_bits = Σ_{i=0..9} H_bit_i - H_full ≥0` 其中`H_bit_i = H(bit_i(A)|B)`，`CE版 D_bits_CE = Σ CE_bit_i - CE_full ≥ -ε`
  - E `CE_bit_i = -E_{VAL}[log2 P(bit_i(A)|B)]`，`P(bit_i=v|b)=Σ_{a:bit_i(a)=v} P(a|b)`
  - F `required = ceil(1.3·N·CE_full)`（`N=1024`，单位bits/block）
  - G `soft_joint_factor_update`纯函数（见Design §5.3，枚举1024，全零→marginal，delta→确定值，brute-force对照`|log_post - brute|<1e-12`）
  - H 嵌套二进制校验族`H_bin[required ×10240]`（`10240=10·N`，见Goal 4）
- **纯函数验证**：`llr≡0 ⇒ log_post == log P(a|b)`（marginal保持）；`llr_{k}=±∞`（delta，仅一态`a*`兼容）`⇒ posterior`退化为`a*`确定值（`log_post[a*]=0`其余`-inf`）；二者与显式1024枚举brute-force对照`|Δ|<1e-12`（自然对数与log2一致性`ln2`因子显式）。

### 3. 预算required=ceil(1.3·N·CE_full)，margin前后阈0与5%三分流
- `required = ceil(1.3*1024*CE_full)`（`CE_full`取`VAL`上`CE_full^{VAL}`，`H_cal`仅描述性，不入预算门禁；`λ`固定为CAL择优，不重选）
- `available`由嵌套族`H_bin`的首`required`行定义（或`r_max=required`），`margin = (available - required)/required` 或等价`available - required`（报告二者，门禁用相对`margin_rel`）
- **三分流（预算维度）**：`margin_rel <0 → HEAVY`（披露不足），`0 ≤ margin_rel <5% → MARGINAL`（临界），`margin_rel ≥5% → FEASIBLE`（充足）；`margin_rel`精确到`1e-9`，`required`整数ceil已验。

### 4. 嵌套二进制校验族10240长 r0起始 到required递增 确切GF2秩 非零不重复 前缀嵌套
- **族**：`H_bin ∈ GF(2)^{required ×10240}`（`10240=10·1024`，每符号`s`展为10 bits纵向拼接，列序`col = sym_idx*10 + bit_pos`，`bit_pos 0..9`LSB→MSB与A-H位定义一致），`r0=160`（`16×10`对应GF32 H1的二进制展开行数）起始，`r= r0, r0+8, ..., required`（步长8对应Δ8的二进制等效；若`required-r0`非8整除则末段补至`required`，末行仍满足秩），**或步长1**（实现可选其一但报告显式，二者均满足前缀嵌套，守卫按报告步长校验）
- **确切GF2秩**：`rank_{GF2}(H_r) == r ∀r`（`required<10240` 时；`required≥10240` 则 `family NOT_APPLICABLE` 不校验秩），每行非零`weight>0`，行间不重复`H_i≠H_j`，前缀嵌套`H_r = H_required[0:r, :]`
- **构造约束**：确定性SeedSequence `V70-BSJ-` + `session`无关（全session共用同一族），`family_sha=97ab00bc38ab5a70`，`tail+7: 9519=160+8*1169+7, 10047=160+8*1235+7 achieved==requested true, 11169 NOT_APPLICABLE`，`numpy` 生成 + `GF2 rank` 校验，6 正交计数与实现一致

### 5. CAL选 VAL确认一次 每session 5终端 总体4态 decoder-free
- **复用**：`v70_data_registry.json`复用`v69_data_registry.json`（即`v67 Stage2`）的3 sessions `stage2_CAL[1024]+stage2_VAL[256]`原样（`total 3, per_category 1,1,1, acquisition_dedup_verified, zero_overlap_verified`），与`V13..V69`零重叠键`(source,session,frame)`已验，禁止跨acquisition拼接或按`CE/required`换session
- **Phase A CAL-only**：`λ`择优仅CAL内4-fold`CV NLL`最小，`CE_full^{CV}`与`H_full^{CAL}`与`D_bits^{CAL}`与`soft_joint_factor_update`的marginal/delta对照仅CAL上完成，脚本内`assert used_val_in_selection==False && used_test==False`
- **Phase B VAL确认一次**：对`CAL`择的`λ`在`VAL256`上独立一次计量`CE_full^{VAL}/CE_bit_i^{VAL}/D_bits^{VAL}/required^{VAL}/margin^{VAL}/H_bin秩/纯函数VAL一致性`，落盘不重选`P*`，`VAL確認僅一次`
- **Per-session 6终端 first-match（优先级高→低互斥，与实现 9bc34be6 一致）**：
   1. `V70_SOFT_JOINT_NO_INFORMATION_MARGIN` — `required ≥10240 → matrix NOT_APPLICABLE`（first-match 最优先，非 EVIDENCE/rank_fail，tail+7 家族不构造）
   2. `V70_EVIDENCE_INCOMPLETE` — 物化/帧256/provenance/D_bits链式` |ΣCE_bit - CE_full - D_bits|≥1e-9`/`C_ab`非有限/1024枚举不足（NO_INFORMATION_MARGIN 已拦截则不入此）
   3. `V70_MODEL_NOT_STABLE` — `λ`触边`[1e-2,1e4]`或`ΔCE=|CE^{VAL}-CE^{CAL-CV}|>0.50`或`ΔNLL>0.50`或`val_b_unseen>1%`或纯函数brute-force偏差`≥1e-12`或`D_bits< -1e-9`
   4. `V70_SOFT_JOINT_FEASIBLE` — `margin_rel ≥5% && rank_ok && D_bits≥0 && brute_ok && MODEL_NOT_STABLE未触发`
   5. `V70_SOFT_JOINT_MARGINAL` — `0 ≤ margin_rel <5% && rank_ok && D_bits≥0 && brute_ok`（临界可行）
   6. `V70_SOFT_JOINT_HEAVY` — `margin_rel <0`（披露不足，需更深表示/新acquisition）
- **总体4态（基于3 sessions汇聚，与实现一致为 PARTIAL 家族语义）**：
   1. `V70_OVERALL_EVIDENCE_INCOMPLETE` — 任一session `EVIDENCE_INCOMPLETE`
   2. `V70_OVERALL_MODEL_NOT_STABLE` — 无`EVIDENCE`但任一`MODEL_NOT_STABLE`且无共同FEASIBLE
   3. `V70_OVERALL_PARTIAL_SESSIONS_FEASIBLE` — `feasible 1 + marginal 1 + no_information_margin 1`（实现 9bc34be6 实测，family_sha 97ab00bc38ab5a70，tail+7: 9519=160+8*1169+7,10047=160+8*1235+7 均 achieved==requested true, 11169 NOT_APPLICABLE，不再用 common_preserving 3）
   4. `V70_OVERALL_SOFT_JOINT_PRESERVING / HEAVY` — 否则（保留历史命名；优先级`EVIDENCE > MODEL > PARTIAL/PRESERVING > HEAVY`，互斥；预算三分流在报告内显式 6 正交计数 `feasible/marginal/heavy/no_information_margin/evidence/model`）

### 6. 本轮交付边界（四工件 + 审计报告，decoder-free）
- 产出`proposal/design/tasks/specs`四工件 + `v70_data_registry.json`（复用V69三session Stage2） + `scripts/v70_binary_soft_joint_feasibility.py`（纯函数枚举1024态`rg "decode_" 0 hits`） + `v70_results.json`（per session `CE_full/CE_bit/D_bits/required/margin/rank` + 纯函数校验） + `v70_table.csv/.json`（每行`session/CE_full/CE_bit/D_bits/required/margin/r0/required/rank_ok/classification`） + `V70_BINARY_SOFT_JOINT_REPORT.md` + `test_v70_binary_soft_joint_small.py`（`py_compile PASS, pytest -p no:cacheprovider -q`） + `v70_manifest.json` + 控制台5终端/4态摘要；**禁**`decode_/construct_H*`业务调用、`run_01`、`H`业务码构造（除嵌套验证族秩校验）、跨方法比较、改`src/`baseline、调`TEST`、启动V71。

## Non-Goals

- 不运行任何`decode_row_layered_fftqspa/construct_H*_business/gf_rank_business/nested_business` decoder或业务矩阵构造（嵌套验证族`H_bin`的`GF2 rank`校验仅为存在性/前缀性验证，不作为业务码；脚本内`rg "decode_" 0 hits`）；不改`H1/Lane C/m2/H_inc/decoder/full-tag`任一冻结量；不引`MET/protograph/SC`新码族；**不以`required/margin`是否`<10240`去构造业务H**（仅验证族前缀存在）。
- 不读密封`TEST`的任何`H/CE/NLL/MAP`统计作`P/required/rank`选择，`λ`择优与`D_bits`计算仅`CAL`，`VAL`仅确认度量，违则`EVIDENCE_INCOMPLETE`。
- 不做`bin_width/dimension/pairing/mapping/frame anchor`网格搜索（单点`84d62779`）；`λ`仅`[1e-2,1e4] log10`仅`CAL 4-fold`，不扩；`H_bin`族固定`10240`列`r0=160`到`required`前缀嵌套，不剪枝，不按`CE`预过滤。
- 不宣称`FER/阈值/SKR/晋升/安全证明`；本变更止于`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不直接进入qualification，不作跨方法rank，不以`SOFT_JOINT_FEASIBLE`宣称码可译。
- 不改写/覆盖`V13/V48–V70`任何已有输出与终态（只读）；V67/V69三session仅复用Stage2，不重跑Stage0/Stage1。
- 不以总体平均替代per-session分流；不以`V25 H`作新域门禁，门禁用`VAL CE` + `required/margin` + `D_bits≥0` + `rank_ok`。
- 不创建正式`.../v70_*/run_01` decoder执行；正式decoder需另起OpenSpec + 独立`EXECUTE_AUTH`。
- 不比较Polar/Cascade/LDPC方法；单soft-joint因子内可行性探查，不作跨方法rank。
- **不启动V71**：任何V71 `QUALIFICATION_PLAN_READY / run_01 / 阈/码族`预冻结均禁止在本变更内声明或执行；V70报告仅以`successor ∈ {v70_binary_soft_joint_code_design, v70_new_representation, recollect}`指向，不创建V71目录或产出。

## Scope

1. **冻结主体与处理点零改（1024维符号二进制软联合扩展，仅因子验证）**：`n1024, q1024 (10-bit s), GF32 poly37, H1 16×1024 rank16 80b U=32*U1+U2, Lane C ordinal-2 s38310x m2 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 early-stop (禁用), full-tag canonical, leak Σw_i·m_i+64`全只读；`84d62779 legacy_v1`单点；不引V70新码本以外的表示。
2. **A-H八等式 + soft_joint_factor_update纯函数枚举1024态全零得marginal delta得确定值对brute-force验证**：`A P_global / B P(a|b) / C H_full/CE_full / D D_bits=ΣH_bit-H_full≥0 / E CE_bit_i / F required=ceil(1.3·N·CE_full) / G soft_joint_factor_update(log_prior, llr10)→log_post 1024枚举 + 全零/ delta对照brute-force |Δ|<1e-12 / H H_bin 10240×required前缀嵌套`，`λ`仅CAL 4-fold，TEST隔离。
3. **预算required=ceil1.3·N·CE_full，margin 0与5%三分流**：`required`整数ceil，`margin_rel=(available-required)/required`（available=`required`行前缀秩族的`r_max`，数值上`available==required`故`margin`恒0？为显式区分，报告同时给出`disclosure_budget = 10240`与`required`的`gap=10240-required`与`margin_rel`；门禁用`margin_rel`按`<0 / [0,5%) / ≥5%`三分流，`FEASIBLE/MARGINAL/HEAVY`）。
4. **嵌套二进制校验族10240长 r0起始 到required递增 确切GF2 rank 非零不重复 前缀嵌套**：`H_bin ∈ GF2^{required×10240}`，`r0=160`起始`r=r0+8·k → required`（或步长1），`rank_{GF2}(H_r)==r ∀r`，每行`weight>0`且`H_i≠H_j`，`H_r = H_required[0:r]`前缀嵌套，确定性`SeedSequence V70-BSJ-`生成，`numpy`高斯消元精确秩。
5. **Session复用V67/V69三预注册Stage2，CAL选VAL确认一次 每session 5终端总体4态**：`v70_data_registry.json`复用`v69_data_registry.json: sessions[3]`的`stage2_CAL[1024] (262144 pairs)+stage2_VAL[256] (65536 pairs)`原样，`total 3, per_category 1,1,1, acquisition_dedup_verified, zero_overlap_verified`，与`V13..V69`零重叠键`(source,session,frame)`已验，不新增acquisition，不按`CE/required`替换；Phase A CAL-only选`λ` Phase B VAL一次确认`CE/D/required/margin/rank/纯函数`。
6. **终态per-session 5终端 + 总体4态 + 预算三分流审计**：每session `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE(ΔCE>0.5/ΔNLL>0.5/unseen>1%/λ触边/brute偏差/D<0) > SOFT_JOINT_FEASIBLE(margin≥5%&&rank_ok) > SOFT_JOINT_MARGINAL(0≤margin<5%) > SOFT_JOINT_HEAVY(margin<0)`；总体`EVIDENCE/MODEL/PRESERVING(3×margin≥0)/HEAVY` + `common_feasible_count/marginal_count/heavy_count`审计；`capacity_warning`正交旗标仅描述不过门禁。
7. **四工件 + 审计报告交付（DECODER_FREE）**：`scripts/v70_binary_soft_joint_feasibility.py`（`rg "decode_" 0 hits`, `py_compile PASS`, 仅`numpy/pandas/pyarrow`）输出`v70_results.json + v70_table.{csv,json} + V70_BINARY_SOFT_JOINT_REPORT.md`（表含`session/CE_full/CE_bit/D_bits/required/margin/r0/rank_ok/classification`等 + `overall 4态`）+ 控制台摘要，未创建`run_01`。
8. **守卫R70-01~10**：见Design §9与Spec §10，覆盖`冻结主体 / A-H等式D_bits≥0 / 纯函数1024枚举全零marginal delta确定值brute-force / required ceil / margin 0/5%三分流 / 10240长r0到required嵌套族确切GF2秩非零不重复前缀 / V67/V69三Session复用 / CAL选VAL确认一次 / per-session 5终端总体4态 / 四工件+test / decoder-free不构业务矩阵 + 不读TEST + 不启V71 / 不创run_01+py_compile`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v70-binary-soft-joint-feasibility/`下4工件`proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v70_binary_soft_joint_feasibility.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅`numpy/pandas/pyarrow`) + 冻结注册表`v70_data_registry.json` (复用V69三session Stage2) + `v70_results.json` (per session `CE_full/CE_bit/D_bits/required/margin/rank/纯函数校验`) + `v70_table.csv/.json` (每行`session/CE_full/D_bits/required/margin/r0/rank_ok/classification` + 总体4态汇总) + `V70_BINARY_SOFT_JOINT_REPORT.md` + `test_v70_binary_soft_joint_small.py` + `v70_manifest.json` + 控制台摘要。
- **只读依赖**：`v69_data_registry.json / v67_data_registry.json / v67_feasibility_table.json`（V69三session Stage2帧集复用） + `v55_intake_20260828/pairs/*` 3 sessions + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`仅对照。
- **不修改**：任何既有`spec/代码/测试/输出`（除本目录 + `scripts/`外）、`V38–V69`输出、`outputs_comparison/workspace`以外；**不改`src/`基线，不创建`run_01`，零码参增量，不启动decoder，不构业务矩阵，不重估计V67/V69，不启动V71**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md`齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD 9bc34be64a2822c8babb4320efb47fc7e335a21a` (implementation 9bc34be6, provenance deviation registry/report 9825d0b336042ad4bf2b26ed31b7fa09a04de620 vs 9bc34be6) + `data 84d62779` + `predecessor V69 d6f590ac6f30deaa8b0bf6cf5c419593fc037720 / V67 FEASIBILITY_MAP_ACCEPTED / V64 22/24 PASS`已绑定，显式声明decoder-free、零decoder/业务矩阵、1024维符号二进制soft-joint因子完整性验证、A-H八等式`D_bits=ΣH-H_full≥0`、纯函数枚举1024态全零marginal/delta确定值brute-force、预算`required=ceil(1.3·N·CE_full)`、margin `0`与`5%`三分流、嵌套族`10240`长`r0`到`required`递增确切GF2秩非零不重复前缀嵌套、CAL选VAL确认一次每session 5终端总体4态、四工件产出已声明。
- [ ] **冻结主体零改已验**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`，`n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak Σw_i·m_i+64`全只读，处理点`84d62779 legacy_v1`单点，`rg -i "gray|met|protograph|sc_coupling" scripts/v70_binary_soft_joint_feasibility.py` 0 hits（除soft-joint因子纯函数注释），`rg "decode_|construct_.*business|gf_rank.*business|nested.*business" 0 hits`已验（嵌套验证族`rank`仅验证族前缀秩，不作业务`construct`），`rg "TEST.*read|read.*TEST" 0 hits`且`used_test==False`。
- [ ] **A-H八等式与D_bits≥0已验**：`A P_global / B P(a|b) λ[1e-2,1e4] / C H_full/CE_full / D D_bits=ΣCE_bit_i - CE_full ≥ -1e-9 (理论≥0，CE估计容差) / E CE_bit_i per bit 10维 / F required ceil / G soft_joint_factor_update / H H_bin秩`已定义且每session `CAL`与`VAL`双组`D_bits`已验`≥ -1e-9`，`H_full`与`ΣH_bit`一致性`1e-9`链式已验。
- [ ] **纯函数soft_joint_factor_update 1024枚举全零marginal delta确定值brute-force已验**：`log_prior_1024` + `llr_10`枚举1024态，全零向量`llr≡0 ⇒ log_post ≡ log P(a|b)`（`|Δ|<1e-12`），delta向量（单`a*`的10-bit模式`llr_i=±1e6`定向）`⇒ posterior`在`a*`处`0`其余`-inf`（`|Δ|<1e-9`），二者与显式1024枚举brute-force（`Σ_a exp`归一化）对照`max|Δ|<1e-12`，`py_compile PASS`，`pytest`小测试PASS，且`soft_joint_factor_update`为纯函数（无I/O、无随机、无全局状态）。
- [ ] **预算required=ceil(1.3·N·CE_full)与margin 0/5%三分流已验**：每session `CE_full^{VAL}`（`VAL256`上独立计量）→ `required=ceil(1.3*1024*CE_full)`整数已验，`margin_rel=(10240 - required)/10240`或`(available-required)/required`（报告二者）按`<0 / [0,5%) / ≥5%`三分流，每session `classification`按预算维度已判定，`VAL`上`required`与`CAL`上`required_CV`一致性仅描述不重选。
- [ ] **嵌套二进制校验族10240长 r0到required递增 确切GF2秩 非零不重复 前缀嵌套已验**：`H_bin ∈ GF2^{required×10240}`（`10240=10·1024`，列序`sym*10+bit`），`r0=160`起始`r∈{r0, r0+8,...,required}`（步长8或1，报告显式），`∀r rank_{GF2}(H_r)==r`（高斯消元精确秩）已验，每行`weight>0`且行间不重复`H_i≠H_j`已验，`H_r == H_required[0:r]`前缀嵌套已验，确定性`SeedSequence V70-BSJ-`生成，`VAL`确认一次不重构。
- [ ] **Session复用V67/V69三预注册Stage2 CAL选VAL确认一次已验**：`v70_data_registry.json`复用`v69_data_registry.json: sessions[3]`的`stage2_CAL[1024] (262144 pairs)+stage2_VAL[256] (65536 pairs)`原样，`total 3 ∈[3,9] && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && (Stage2_key ∩ (V13..V69)_key ==∅)`已验，`P`重标记不改帧集，不新增acquisition，不按`CE/required`替换，`Phase A CAL-only` `used_val_in_selection==False && used_test==False`已验，`Phase B VAL`一次确认不重选已验。
- [ ] **Per-session 5终端互斥 + 总体4态已验**：每session `classification ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, SOFT_JOINT_FEASIBLE(margin≥5%), SOFT_JOINT_MARGINAL(0≤margin<5%), SOFT_JOINT_HEAVY(margin<0)}`按`EVIDENCE > MODEL(brute偏差/λ触边/ΔCE>0.5/ΔNLL>0.5/unseen>1%/D<0) > FEASIBLE > MARGINAL > HEAVY`已判定；总体`overall ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, SOFT_JOINT_PRESERVING(3×margin≥0), SOFT_JOINT_HEAVY}`基于共同`H_bin`族与预算`margin`已判定，`common_feasible_count/marginal_count/heavy_count`已落盘，报告4态章节与`json/csv`一致。
- [ ] **四工件 + 审计报告完整**：`v70_data_registry.json` + `v70_results.json` + `v70_table.csv/.json`（行对等，含`session/CE_full/CE_bit/D_bits/required/margin/r0/rank_ok/classification` + `overall 4态`汇总且与json一致，`capacity_warning`正交 + `descriptive_diagnostics`逐session）+ `V70_BINARY_SOFT_JOINT_REPORT.md`（含`per session A-H / D_bits / 纯函数brute校验 / required/margin 0/5%三分流 / r0→required嵌套族秩/implication + overall 4态`）已齐。
- [ ] `scripts/v70_binary_soft_joint_feasibility.py`为decoder-free可运行脚本（`rg "decode_" 0 hits`、`rg "construct_.*business" 0 hits`、`rg "gf_rank.*business" 0 hits`、`rg -i "met|protograph" 0 hits`，仅`numpy/pandas/pyarrow`，`py_compile` PASS，`pytest -p no:cacheprovider -q test_v70_binary_soft_joint_small.py` PASS），输出`results + table + report` + 控制台5终端/4态摘要，**未创建run_01，未构业务矩阵，未读TEST，λ不扩搜索，required ceil不cap，1024枚举纯函数brute校验已验，10240长嵌套族秩已验**。
- [ ] 已停留在`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何`.../v70_*/run_01`（`ls`不存在已验），不比较，不碰`V48-V69`块外，未转qualification，未启动V71，**四工件+registry+spike+报告表已单独提交推送，返回新Plan SHA + per-session required/margin/D_bits/rank_ok + 各分流计数 + overall 4态**，等待独立审核（`Pre-RESULT`独立线程复核`HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST未读/margin/required ceil/1024枚举纯函数brute/D_bits≥0/10240长r0→required嵌套族秩/5终端+4态/CAL选VAL确认一次`）。

## Tasks

见`tasks.md`（Phase A 注册表复用；Phase B 冻结主体1024维二进制软联合不重构；Phase C A-H八等式D_bits≥0与soft_joint_factor_update纯函数1024枚举全零marginal delta确定值brute-force；Phase D 预算required ceil与margin 0/5%三分流；Phase E 嵌套二进制校验族10240长r0到required递增确切GF2秩非零不重复前缀嵌套；Phase F per-session 5终端总体4态CAL选VAL确认一次；Phase G 四工件+审计报告；Phase H 守卫R70-01~10 + 单独提交推送新Plan SHA + 不启V71）。

## Lifecycle

`V64`已`22/24 full-tag PASS`；`V65` new-session对照；`V66`单session `72`自适应`RATE_NOT_FEASIBLE`；`V67-MAP`已`V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions均`NEAR_FULL`（natural 5+5）；`V68-BAL`为**均衡 5+5 均衡性地图**decoder-free预冻结（`252`枚举`max→sum→abs→lex`）；`V69-3L`为**三层表示可行性地图**decoder-free预冻结（`3^10=59049→37170`升序唯一词典序）；`V70-BSJ`为**二进制soft-joint因子完整性可行性地图**decoder-free预冻结，当前`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（验证10-bit soft-joint factor保留完整1024-ary posterior，A-H八等式D_bits=ΣH-H_full≥0，纯函数枚举1024态全零得marginal delta得确定值对brute-force验证，预算`required=ceil1.3·N·CE_full` margin前后阈`0`与`5%`三分流，嵌套二进制校验族`10240`长`r0`起始到`required`递增确切GF2秩非零不重复前缀嵌套，CAL选VAL确认一次每session 5终端总体4态，不跑decoder不构业务矩阵，不启V71）；`V70`本身不直接进入qualification；任何decoder / 新表示需另起`EXECUTE_AUTH`。
