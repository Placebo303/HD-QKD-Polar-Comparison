# OpenSpec Tasks: formal-ir-v70-binary-soft-joint-feasibility — 二进制soft-joint因子完整性地图 (PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024维二进制soft-joint因子是否保留完整1024-ary posterior，A-H八等式D_bits=ΣH-H_full≥0，soft_joint_factor_update纯函数枚举1024态全零得marginal delta得确定值对brute-force验证，预算required=ceil1.3·N·CE_full margin 0与5%三分流，嵌套二进制校验族10240长r0到required递增确切GF2秩非零不重复前缀嵌套，CAL选VAL确认一次每session 5终端总体4态，四工件spike/results/table/report+test，守卫R70-01~10，不跑decoder不构业务矩阵不读TEST不启V71**

**HEAD**: `9bc34be64a2822c8babb4320efb47fc7e335a21a` (implementation 9bc34be6, provenance deviation 9825d0b336042ad4bf2b26ed31b7fa09a04de620 vs 9bc34be6) + data `84d62779`

**Predecessor**: `formal-ir-v69-three-layer-representation-feasibility` `d6f590ac6f30deaa8b0bf6cf5c419593fc037720` + `formal-ir-v67-multisession-feasibility-map` `V67_FEASIBILITY_MAP_ACCEPTED` (3 sessions均`NEAR_FULL`) → `V70-BSJ`

**Method frozen**: `n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U 二层natural 5+5参照 + 10-bit位展开bit_i(s) soft-joint factor Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak Σw_i·m_i+64`零改；处理点`84d62779`单点；`soft_joint_factor_update`纯函数枚举1024态 + `H_bin 10240`嵌套秩族

**Boundary**: 仅验证soft-joint因子完整性，不改主体；A-H八等式D_bits≥0与纯函数全零/ delta brute-force 1e-12双极校验，`required=ceil1.3·1024·CE_full`整数ceil与`gap=10240-required`按`<0 / 0-5% / ≥5%`三分流，`H_bin[required×10240]` r0=160→required前缀嵌套确切GF2秩非零不重复，CAL选VAL确认一次，不跑decoder不启V71

## Phase A — 注册表复用（V69 Stage2复用，V67三Session，不重估计，不启V71）

- [ ] **A1 复用`v69_data_registry.json`的Stage2帧集（机械，不按CE替换，不启V71）**：读取`openspec/changes/formal-ir-v69-three-layer-representation-feasibility/v69_data_registry.json`或回退`formal-ir-v67-multisession-feasibility-map/v67_data_registry.json`的`sessions[3]`（`20260123_1M_600k_0dB 1M / 20260107_PPLN_1p5M 1p5M / 20260123_2M_1p2M_0dB 2M`）的`stage2_CAL_frame_ids[1024] (262144 pairs)+stage2_VAL_frame_ids[256] (65536 pairs)`原样拷贝至`v70_data_registry.json`（`schema v70_data_v1, lifecycle PLAN_CANDIDATE, head d6f590ac6f30deaa8b0bf6cf5c419593fc037720, data_sha 84d62779, reused_from v69, successor_v71_not_started true, sessions[3], per_session {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE}`），校验`total 3 && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && Stage2_key ∩ (V13..V69)_key ==∅`键`(source,session,frame)`，禁止事后换session，且`successor_v71_not_started==true`。
- [ ] **A2 冻结10-bit位展开与A-H位序（纯比特置换，不改s，不启V71）**：实现`bit_i(s)=(s>>i)&1, i=0..9 LSB→MSB`与列映射`col=sym_idx*10+bit_pos`一一对应，每帧校验`∀s s== Σ bit_i(s)<<i`双射且10 bits无丢，`rg -i "gray|met|protograph|sc_coupling|v71" 0 hits`（除soft-joint纯函数注释），`src/`零改，`V71_not_started`已显式。

## Phase B — 冻结主体1024维soft-joint验证仅因子检查（decoder-free，不构业务矩阵，不启V71）

- [ ] **B1 主体明文化（逐项显式，冻结零改，不启V71）**：写入`v70_manifest.json:frozen_body {n1024, q1024, GF32 poly37, H1 16×1024 rank16, 10-bit位展开, per_frame 256, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 disabled, full-tag canonical, leak Σw_i·m_i+64, materialization legacy_v1, successor_v71_not_started true}`，显式`not Gray/not MET/protograph/SC/not H business construction/not V71`，`git diff -- src/ ==0`已验。
- [ ] **B2 权威算法只读复用**：直接复用`src.reconciliation.run_nbldpc_demo_point`的`legacy_v1`物化算法不重写；`Stage2 CAL/VAL`均按该链物化后`frame_id=row//256`切片，`10-bit位展开`仅在`a_cal/b_cal`的`s`上比特置换得`bit_i`统计，不改`pairs.parquet`帧边界，不读TEST，不启V71。
- [ ] **B3 不构业务矩阵守卫 + 不启V71守卫**：`rg "decode_" scripts/v70_binary_soft_joint_feasibility.py 0 hits`且不调用任何业务`H`构造/`nested`（嵌套验证族`H_bin`的`GF2 rank`校验仅为存在性前缀验证，不属业务`construct`），且`rg -i "v71|qualification" scripts/v70_binary_soft_joint_feasibility.py 0 hits`（除successor注释`V71_not_started`），`py_compile`校验；脚注`ponytail:`标明ceiling（若需后续二进制码构造/V71，需另起OpenSpec）。

## Phase C — A-H八等式D_bits≥0与soft_joint_factor_update纯函数1024枚举全零marginal delta确定值brute-force（CAL-only CAL选，不启V71）

- [ ] **C1 每session CAL1024上C_ab→P_global/P(a|b) λ择优（CAL-only，1024×1024）**：按`CAL1024 (262144 pairs)`算`C_ab 1024×1024 int32 sum 262144 → N_b/P_global`，`λ∈[1e-2,1e4] log10`仅`CAL内4-fold`（每fold 256 frames 65536 pairs）最小`CV NLL`择优，生成`per session CAL {λ, λ_at_boundary, H_full^{CV}, CE_full^{CV}, CE_bit_i^{CV}×10, D_bits^{CV}, effective_contexts}`，校验`used_val_in_selection==False && used_test==False`，落盘`per session CAL`，`H_full`与`ΣH_bit`一致性仅描述。
- [ ] **C2 D_bits=ΣH-H_full≥0（CAL描述性+VAL门禁性，A-H D）**：对每session在`CAL` held-out上计`H_full^{CV}`与`H_bit_i^{CV}` → `D_bits^{CV}=ΣH_bit_i^{CV} - H_full^{CV}`，校验`D≥ -1e-9`（理论≥0，数值容差），在`VAL`上同算法得`CE_full/CE_bit/D^{VAL}`供`D≥ -1e-9`门禁，落盘`D_bits^{CAL} / D_bits^{VAL} / chain_delta_H = |D - (ΣCE_bit-CE_full)|`，报告`ΣH_bit vs H_full`链式`1e-9`。
- [ ] **C3 soft_joint_factor_update纯函数枚举1024态（CAL-only纯函数，brute-force对照）**：实现`soft_joint_factor_update(log_prior_1024, llr_10) → log_post_1024`枚举1024态（`log_prior=log P(a|b)`，`llr_term=Σ bits[i]*llr[i]`后`logsumexp`归一化，log域运算），校验`all_zero llr≡0 ⇒ log_post≡log_prior (max|Δ|<1e-12)`与`delta K=1e6 定向a*=0,511,1023 ⇒ posterior退化a* (log_post[a*]=0 其余=-inf, |Δ|<1e-9)`二极与显式1024枚举brute-force对照`max|Δ|<1e-12`，纯函数无I/O/随机/全局状态，落盘`pure_brute_maxΔ`与`pure_is_pure==true`，`py_compile PASS`。

## Phase D — 预算required=ceil1.3·N·CE_full与margin 0/5%三分流（CAL选VAL确认一次）

- [ ] **D1 预算required=ceil(1.3·N·CE_full)（VAL确认，不cap）**：对每session在`VAL256 (65536 pairs)`上以`P_λ*`计`CE_full^{VAL}=-E_VAL log2 P(A|B)`（`λ`固定为CAL择优值，不重选）→ `required=ceil(1.3*1024*CE_full^{VAL})`整数已验，同时算`required^{CV}=ceil(1.3*1024*CE_full^{CV})`仅描述，落盘`CE_full^{VAL}/CE_full^{CV}/required/required_CV`，`m_raw`不cap显式，`grep "min(1024" 0 hits`已验。
- [ ] **D2 margin 0与5%三分流（gap vs 10240）**：算`gap=10240 - required`与`margin_rel_gap=gap/10240`与`margin_rel_vs_required=(available-required)/required`（available==required故恒0），门禁按`gap`三分：`gap<0 ⇒ HEAVY`, `0≤gap<512 ⇒ MARGINAL`, `gap≥512 ⇒ FEASIBLE`（512=5%·10240），落盘`gap/margin_gap/margin_vs_required/budget_classification` per session，`CAL选VAL确认一次`已验（`VAL`上`required`仅度量，不重选λ）。
- [ ] **D3 一致性字段**：落盘`cal_val_ce_consistency = |CE_full^{VAL}-CE_full^{CV}|`与`required_consistency`仅描述，报告`CAL vs VAL`的`CE/D/required/gap`对照，`VAL确认仅一次`已验。

## Phase E — 嵌套二进制校验族10240长 r0起始 到required递增 确切GF2秩 非零不重复 前缀嵌套（VAL确认一次）

- [ ] **E1 构造H_bin[required×10240]（r0=160起始）**：`10240=10·1024`列，`col=sym*10+bit_pos`，`r0=160 (16×10)`起始，`Rs={r0, r0+8,...,required}`步长8（或1，报告显式），确定性`SeedSequence V70-BSJ-H_bin`生成`required×10240`二元矩阵，再筛滤至`rank==r ∀r∈Rs`且每行`weight>0`且行间不重复`H_i≠H_j`，落盘`H_bin_shape/dtype/seed/r0/Rs`描述性（不落全矩阵，仅落`rank`与`prefix`指纹`sha256`），`VAL确认一次`不重构。
- [ ] **E2 确切GF2秩前缀嵌套校验（高斯消元精确秩）**：对每`r∈Rs`算`rank_{GF2}(H_bin[0:r])`高斯消元`GF2`精确秩（`numpy` uint8，`O(r^2 n/64)`），校验`rank==r ∀r`且`∀i weight>0`且`∀i≠j H_i≠H_j`且`∀r1<r2 H[0:r1]==H[0:r2][0:r1]`前缀嵌套，落盘`rank_ok/prefix_ok/nonzero_ok/unique_ok` per session（全session共用同一族，故三session同值），若`required>10240`则`rank_fail → EVIDENCE_INCOMPLETE`。
- [ ] **E3 秩与预算关联审计**：落盘`per session gap vs rank_ok`对照，报告`r0→required`的`rank`曲线（`r` vs `rank`恒`y=x`），`capacity_warning`正交旗标仅描述不过门禁，`rank`校验与`D/纯函数`正交但同入`FEASIBLE`门禁（`rank_ok==false`则`MODEL_NOT_STABLE`或`EVIDENCE_INCOMPLETE`）。

## Phase F — per-session 5终端总体4态CAL选VAL确认一次（优先级互斥，不启V71）

- [ ] **F1 Per-session 6终端 first-match（优先级互斥，预算三分流 + D/秩/纯函数，与实现 9bc34be6 一致）**：`required≥10240 → NO_INFORMATION_MARGIN (matrix NOT_APPLICABLE, family_sha NOT_APPLICABLE, tail+7 不构造) first-match` > `EVIDENCE_INCOMPLETE` > `MODEL_NOT_STABLE` > `SOFT_JOINT_FEASIBLE(gap≥512&&rank_ok)` > `MARGINAL(0≤gap<512&&rank_ok)` > `HEAVY(gap<0)`，`family 9519/10047 tail+7 achieved==requested true, 11169 NOT_APPLICABLE` 已验，`6 orthogonal counts feasible/marginal/heavy/no_information_margin/evidence/model` 已验，`capacity_warning`正交，落盘`classification + successor + family_sha/shape/step/tail/achieved/requested/matrix_status` per session。
- [ ] **F2 总体4态 PARTIAL（基于3 sessions汇聚，6 正交计数）**：`feasible 1 + marginal 1 + no_information_margin 1 (heavy 0, evidence 0, model 0) → overall V70_OVERALL_PARTIAL_SESSIONS_FEASIBLE` (实现 9bc34be6)，`family_sha 97ab00bc tail+7 9519/10047 achieved==requested, 11169 NOT_APPLICABLE` 已验，落盘`overall + 6 counts + family`。
- [ ] **F3 Common审计表**：落盘`audit {per_session_classification[3], overall, feasible/marginal/heavy counts, common_preserving, per_session CE_full/CE_bit/D/required/gap/margin/rank_ok/pure_brute_maxΔ, cal_val_consistency[3], successor per session}`，报告`overall 4态`审计章节显式三session是否同族且同`margin≥0`。

## Phase G — 四工件 + 审计报告交付（PLAN_CANDIDATE / DECODER_FREE，不启V71）

- [ ] **G1 编写`scripts/v70_binary_soft_joint_feasibility.py`** (decoder-free, 本变更目录下): `python scripts/v70_binary_soft_joint_feasibility.py [--registry v70_data_registry.json] [--out v70_results.json]` → `CAL1024 C_ab/P/λ→H_full/CE_full/D/required → pure 1024枚举brute校验 → VAL256 CE_full/D/required/gap/margin → H_bin 10240×required秩前缀校验 → 5终端/4态`，`rg "decode_" 0 hits` `rg -i "met|protograph" 0 hits` `rg -i "v71|qualification" 0 hits`（除successor V71_not_started注释）仅`numpy/pandas/pyarrow`，`py_compile PASS`，输出`v70_results.json + v70_table.(csv|json) + rank指纹` + 控制台摘要。
- [ ] **G2 执行decoder-free枚举回填（含A-H与纯函数与秩）**：运行`scripts/v70_binary_soft_joint_feasibility.py`得每session `CE_full/CE_bit×10/D/required/gap/margin/λ/pure_maxΔ/rank_ok`与`overall 4态`，落盘`v70_results.json`与`v70_table.csv/.json`（CSV行对等，含`capacity_warning`正交 + `pure_brute_maxΔ/D/rank`），`gap`与`margin`已验，`required ceil`已验，`1024枚举纯函数brute 1e-12`已验，`10240长r0→required嵌套族秩`已验。
- [ ] **G3 撰写`V70_BINARY_SOFT_JOINT_REPORT.md`**：`per session A-H/D_bits/纯函数brute 1e-12/required/margin 0/5%三分流/r0→required嵌套族秩前缀非零不重复 + overall 4态 + 预算三分流审计 + map_sparse标记 + TEST隔离 + 1024维冻结 + V71_not_started`与`json/csv`一致，不扩大为`FER/SKR`，显式`1024枚举纯函数 + required ceil + margin 0/5% + 10240长r0→required秩`。
- [ ] **G4 自检（5终端+4态+守卫+R70-01~10，不启V71）**：`py_compile` spike PASS, `rg "decode_" 0 hits`, `rg -i "met|protograph" 0 hits`, `rg -i "v71" 0 hits`（除V71_not_started注释），`git diff -- src/ ==0`未改码, V69 Stage2复用`3`已验, `A-H D_bits≥-1e-9`已验, `纯函数1024枚举全零marginal delta确定值brute 1e-12`已验, `required ceil`不cap已验, `gap margin 0/5%三分流`已验, `H_bin 10240长r0→required前缀嵌套确切GF2秩非零不重复`已验, `5终端优先级互斥`已验, `overall 4态`已验, `CAL选VAL确认一次`已验, `TEST未读`已验, `V71_not_started`已验, 报告与json/csv一致 **无TBD**, **A-F已闭合**。
- [ ] **G5 小测试**：`pytest -p no:cacheprovider -q`小测试（`test_v70_binary_soft_joint_small.py`）验证`bit展开 / D_bits非负 / 纯函数全零marginal delta确定值 1e-12 / required ceil / gap 0/5%三分 / H_bin秩小矩阵前缀`纯函数与`TEST隔离` + `V71_not_started`，`py_compile`双PASS。
  - ponytail: `soft_joint_factor_update`为10-bit纯移位/掩码+`logsumexp`，不引`numba`；`H_bin`小矩阵秩为`tuple`高斯消元，`O(r^2 n)`足够，VAL仅对`required`秩一次详检以控成本。

## Phase H — 守卫R70-01~10 + 单独提交推送新Plan SHA + 不启V71

- [ ] **H1 守卫R70-01~10落盘验证**：在`v70_manifest.json:guards {R70-01..R70-10}`逐项`true`，见Design §8 / Spec §10。
  - R70-01 冻结主体1024维soft-joint验证不改 + 不启V71
  - R70-02 A-H八等式D_bits=ΣH-H_full≥0闭合
  - R70-03 纯函数soft_joint_factor_update 1024枚举全零marginal delta确定值brute-force
  - R70-04 预算required=ceil1.3·N·CE_full显式
  - R70-05 margin 0与5%三分流
  - R70-06 嵌套二进制校验族10240长 r0→required 前缀嵌套确切GF2秩非零不重复
  - R70-07 V67/V69三Session Stage2复用CAL选VAL确认一次
  - R70-08 per-session 5终端总体4态
  - R70-09 四工件+test完整
  - R70-10 decoder-free不构业务矩阵 + 不读TEST + 不创run_01 + 不启V71
- [ ] **H2 单独提交推送四工件+registry+spike+报告表（V70 provenance — 新Plan SHA）**：`git add openspec/changes/formal-ir-v70-binary-soft-joint-feasibility/ scripts/v70_binary_soft_joint_feasibility.py v70_data_registry.json v70_results.json v70_table.csv v70_table.json V70_BINARY_SOFT_JOINT_REPORT.md test_v70_binary_soft_joint_small.py v70_manifest.json && git commit -m "formal-ir-v70: binary soft-joint 1024枚举 pure D_bits required ceil margin 0/5% 10240 r0→required GF2秩 CAL选VAL确认 5终端4态 V69复用" && git push origin formal-ir-mainline`，返回新`Plan SHA`（40位），记录于`proposal/design/tasks` HEAD占位替换，**不创建run_01，不启V71**。
- [ ] **H3 停留`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V71_NOT_STARTED`**，未创建任何`.../v70_*/run_01`且未创建`.../v71_*/run_01`，未构业务矩阵，不比较，不碰`V48-V69`块外，未转qualification，未启动V71，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT`独立线程复核`HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST未读/required ceil/margin 0/5%/1024枚举纯函数brute/D≥0/10240长r0→required嵌套族秩/5终端+4态/CAL选VAL确认一次/V71_not_started`），返回`Plan SHA / per-session required/margin/D/rank_ok + 各分流计数 + overall 4态`等待`PLAN_ACCEPT`。

## 本变更显式禁止

decoder/业务矩阵构造（`decode_*` / `construct_*_business` / `gf_rank_business` / `nested_business`等）；读密封`TEST`的`H/CE/NLL/MAP`统计或将其用于`P/required/rank`选择；读`VAL`参与`λ`择优（`λ`仅`CAL`）；在原`V55 90-block`或`V48-V69`已用`(source,session,frame)`上重跑先验估计而不零重叠；调`H1/Lane C/Δ8/decoder/m2/m_total/leak/prior/H_inc/H_total/verification`任一冻结参数或新增业务矩阵；**跨acquisition拼接凑3**；**将floor/round当ceil**；**将`min(1024, ceil(...))` cap伪装当通过**（`required`必须显式ceil，`gap`显式10240-required）；**将`+8`外degree/seed网格当自适应**；**用`VAL/TEST`择优`λ`**（`λ`仅`CAL`）；**将不足3伪判为complete**（应`EVIDENCE_INCOMPLETE`）；**将`acquisition`未去重多计**（必须V69复用）；**将1024枚举剪枝**（必须全1024态）；**将纯函数全零/ delta单极当全验证**（必须双极`1e-12`）；**将`D_bits<0`当可行**（必须`≥-1e-9`）；**将`rank≠r`当通过**（必须确切GF2秩`==r`且非零不重复前缀）；**将`gap`换`(available-required)/required`恒0掩饰**（必须`gap=10240-required`显式三分流）；**引MET/protograph/SC/Gray**（仅soft-joint纯函数）；**改`src/`基线**；宣称LDPC证伪或`FER/阈值/SKR/晋升`；创建正式`.../v70_*/run_01`；任意`bin_width/dimension/pairing/mapping`网格或阈网格（处理点单点）；用第二estimator作门禁；覆盖已有输出；`V55 90 / V48-V69`永久禁用違反；**主观“显著可行”替代硬阈`margin≥5% && rank_ok && D≥0 && pure<1e-12`**；**擅自调V70以外码**（仅soft-joint因子）；**保留TBD占位不回填**；**启动V71**（任何`V71_*/run_01`、`QUALIFICATION_PLAN_READY`、`V71` OpenSpec预冻结均禁止）。

## 验收

- proposal/design/tasks/specs一致 `d6f590ac6f30deaa8b0bf6cf5c419593fc037720→新Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V71_NOT_STARTED` 5终端+4态按优先级互斥明确，显式1024维冻结仅验证soft-joint因子完整性、A-H八等式`D_bits=ΣH-H_full≥0`、纯函数枚举1024态全零marginal delta确定值brute-force `1e-12`、预算`required=ceil1.3·N·CE_full`与`gap` `0/5%`三分流、嵌套族`10240`长`r0=160→required`确切GF2秩非零不重复前缀嵌套、V69三Session Stage2复用、per-session 5终端总体4态、CAL选VAL确认一次、四工件产出已声明，严格复用V56权威算法，冻结分段/熵-CE与required公式/分流阈 + V71_not_started
- 1024维冻结仅因子验证已验，`A-H` D_bits≥-1e-9已验，`纯函数1024枚举全零marginal delta确定值brute 1e-12`已验，`required ceil`与`gap` `0/5%`三分流已验，`H_bin 10240长r0→required`前缀嵌套确切GF2秩非零不重复已验，`CAL-only`选λ不读VAL/TEST且`VAL确认一次`已验，`VAL`上`CE/D/required/gap/margin/rank`已验，`required ceil`不cap，`TEST`未读已验，3 sessions复用已验，**新Plan SHA已推送，V71未启动**
- 合同`dimension 1024 / bin200 / nearest legacy_v1 / channels/frame anchor/mapping 每帧256`算法一致已验，`10-bit位展开`每帧已验，偏则`EVIDENCE_INCOMPLETE`已验，`1024枚举`与`10-bit`无丢已验
- 每session `CAL C_ab→P(a|b) λ(CAL 4-fold)→H_full/CE_full/D→required ceil→gap/margin→H_bin秩`已算且`CAL-only`选λ已验，`VAL`上`CE/D/required/gap/margin`一次确认已验，`纯函数`双极`1e-12`已验，`rank`前缀秩已验，不扩，禁第二estimator已验，`cal_val_consistency`已报告
- 每session `5终端 final_classification + successor`已落盘，`overall 4态`已统计
- `3行(每session)+总体4态 / 纯函数/ D/ required/ gap/ rank_ok / classification/successor/capacity_warning/descriptive`已回填，`报告表CSV行对等JSON`已验，`overall 4态`已验，`V71_not_started`已验
- 守卫`R70-01~10`已验（`A-H D≥0/纯函数1024枚举双极brute/required ceil/gap 0/5%三分/H_bin 10240 r0→required前缀秩/V69复用/CAL选VAL确认一次/5终端+4态/四工件+test/decoder-free不构业务矩阵不读TEST/不创run_01/py_compile/小测试+V71_not_started`）
- 双脚本`rg "decode_" 0 hits` `rg -i "met|protograph" 0 hits` `rg -i "v71" 0 hits`（除V71_not_started注释） `py_compile` PASS `pytest小测试`PASS `required`未cap `VAL未参与λ择优` `TEST未读` `1024枚举`已验 `H_bin 10240 r0→required秩`已验 `capacity_warning`正交与`descriptive`已落盘报告与json/csv一致未建`run_01`未启`V71`已停留`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`仅改本目录 + `scripts/`（`src/`零改），未启动decoder/业务矩阵，**四工件+registry+spike+报告表已单独提交推送，新Plan SHA + per-session required/margin/D/rank_ok + 各分流数 + overall 4态已返回**，推送后等待独立审核
