# OpenSpec Tasks: formal-ir-v71-soft-joint-factor-kernel — 1024-state 纯因子核 + ldpc_v5* 只读兼容地图 (PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — **1024-state 纯因子核校验完整 posterior 保留 + extrinsic 冻结 5函数纯枚举 log-domain + D1-D10 十不变量 + 只读 ldpc_v5* A1-A6 READY/ADAPTER/NOT_COMPATIBLE + 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈 + f1.3 freeze f_actual NOT_MEASURED + per-session 6终端总体4态，四工件双报告 + test，守卫R71-01~11，不跑decoder不构业务矩阵不读TEST不启V72**

**HEAD**: `4afc4eec2a3adfca88a8f79bc9c051e3819405ac` (implementation TBD, provenance deviation dc18fd2f vs predecessor 9bc34be6) + data `84d62779` — **rev A1 1/9/1024 各1024次 deterministic / A2 去self比较需真接口否则 ADAPTER / A3 三状态分离 2M NO_INFORMATION_MARGIN**

**Predecessor**: `formal-ir-v70-binary-soft-joint-feasibility` `9bc34be64a2822c8babb4320efb47fc7e335a21a` + `formal-ir-v67-multisession-feasibility-map` `V67_FEASIBILITY_MAP_ACCEPTED` (3 sessions均`NEAR_FULL`) → `V71-SJK`

**Method frozen**: `n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U 二层natural 5+5参照 + 10-bit位展开 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak Σw_i·m_i+64`零改；处理点`84d62779`单点；`5函数纯因子核 log-domain 1024枚举 + D1-D10 + ldpc_v5* A1-A6 + 1M 1/9/1024 benchmark`

**Boundary**: 仅验证纯因子核完整性 + 兼容性，不改主体；extrinsic 冻结 `ext=log_post-log_prior`，5函数纯枚举 log-domain 全零/ delta brute `1e-12`，D1-D10 正交，A1-A6 READY/ADAPTER/NOT_COMPATIBLE，E仅1M 1/9/1024 30s/2GiB，F f1.3 freeze NOT_MEASURED，per-session 6终端总体4态，不跑decoder不启V72

## Phase A — 注册表复用（V69 Stage2复用，V67三Session，不重估计，不启V72）

- [ ] **A1 复用`v69_data_registry.json`的Stage2帧集（机械，不按CE替换，不启V72）**：读取`openspec/changes/formal-ir-v69-three-layer-representation-feasibility/v69_data_registry.json`或回退`formal-ir-v67-multisession-feasibility-map/v67_data_registry.json`的`sessions[3]`（`20260123_1M_600k_0dB 1M / 20260107_PPLN_1p5M 1p5M / 20260123_2M_1p2M_0dB 2M`）的`stage2_CAL_frame_ids[1024] (262144 pairs)+stage2_VAL_frame_ids[256] (65536 pairs)`原样拷贝至`v71_data_registry.json`（`schema v71_data_v1, lifecycle PLAN_CANDIDATE, head dc18fd2fc17a606fb3a05713efdd9f05ed6472a4 (provenance deviation), data_sha 84d62779, reused_from v69, successor_v72_not_started true, sessions[3], per_session {session_id, acquisition_id, source_label, provenance, stage2_CAL[1024], stage2_VAL[256], zero_overlap_verified, acquisition_dedup_verified, frozen, not_sorted_by_CE}`），校验`total 3 && per_category 1,1,1 && acquisition_dedup_verified && zero_overlap_verified && Stage2_key ∩ (V13..V70)_key ==∅`键`(source,session,frame)`，禁止事后换session，且`successor_v72_not_started==true`，且 Phase E 仅1M benchmark 的声明已显式。
- [ ] **A2 冻结10-bit位展开与extrinsic语义（纯比特置换，不改s，不启V72）**：实现`bit_i(s)=(s>>i)&1, i=0..9 LSB→MSB`与`ext[a]=log_post[a]-log_prior[a]` log域差分冻结定义，每帧校验`∀s s== Σ bit_i(s)<<i`双射且10 bits无丢，`rg -i "gray|met|protograph|sc_coupling|v72" 0 hits`（除纯因子核注释），`src/`零改，`V72_not_started`已显式，落盘`v71_manifest.json:frozen_body {extrinsic_def}`。

## Phase B — 冻结主体1024维纯因子核验证仅核检查（decoder-free，不构业务矩阵，不启V72）

- [ ] **B1 主体明文化（逐项显式，冻结零改，不启V72）**：写入`v71_manifest.json:frozen_body {n1024, q1024, GF32 poly37, H1 16×1024 rank16, 10-bit位展开, extrinsic冻结, per_frame 256, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 disabled, full-tag canonical, leak Σw_i·m_i+64, materialization legacy_v1, f1.3 frozen, successor_v72_not_started true}`，显式`not Gray/not MET/protograph/SC/not H business construction/not V72`，`git diff -- src/ ==0`已验。
- [ ] **B2 权威算法只读复用**：直接复用`src.reconciliation.run_nbldpc_demo_point`的`legacy_v1`物化算法不重写；`Stage2 CAL/VAL`均按该链物化后`frame_id=row//256`切片，`10-bit位展开`仅在`a_cal/b_cal`的`s`上比特置换，不改`pairs.parquet`帧边界，不读TEST，不启V72，不执行`run_ldpc_formal_v5`。
- [ ] **B3 不构业务矩阵守卫 + 不启V72守卫**：`rg "decode_" scripts/v71_soft_joint_factor.py 0 hits && rg "decode_" scripts/v71_ldpc_v5_audit.py 0 hits`且不调用任何业务`H`构造/`nested`（`ldpc_v5*` 只读探针不属业务 `construct`，仅AST/signature探针），且`rg -i "v72|qualification" scripts/v71_soft_joint_factor.py 0 hits && rg -i "v72|qualification" scripts/v71_ldpc_v5_audit.py 0 hits`（除successor注释`V72_not_started`），`py_compile`双脚本校验；脚注`ponytail:`标明ceiling（若需后续因子核对接/ V72，需另起OpenSpec）。

## Phase C — 冻结 extrinsic 定义 + 5函数纯枚举 log-domain（CAL-only，不启V72）

- [ ] **C1 冻结 extrinsic 定义**：写入`v71_manifest.json:extrinsic {def: "ext[a]=log_post[a]-log_prior[a] log域差分，不含信道因子", log_domain: true, pure: true}`，`extrinsic` 输入输出分离，不含 `P(a|b)` 信道部分，报告显式，`V72_not_started`。
- [ ] **C2 实现5函数纯枚举 log-domain（枚举1024，全零/ delta brute 1e-12）**：在`scripts/v71_soft_joint_factor.py`实现5纯函数`log_prior_from_posterior / bit_factor_from_llr / soft_joint_factor_kernel / extrinsic_from_logs / validate_kernel`（签名见Design §5.2，`numpy.logaddexp.reduce`手写 `logsumexp`，枚举1024态，`llr_term=Σ bits[i]*llr[i]`后归一，log域运算），校验`all_zero llr≡0 ⇒ log_post≡log_prior (max|Δ|<1e-12)`与`delta K=1e6 定向a*=0,511,1023 ⇒ posterior退化a* (log_post[a*]=0 其余=-inf, |Δ|<1e-9)`二极与显式1024枚举brute-force对照`max|Δ|<1e-12`，纯函数无I/O/随机/全局状态，落盘`pure_brute_maxΔ`与`pure_is_pure==true`，`py_compile PASS`。
- [ ] **C3 纯函数校验落盘**：在`v71_results.json:kernel {log_prior_is_pure, bit_factor_is_pure, kernel_is_pure, extrinsic_is_pure, validate_is_pure, brute_maxΔ_all_zero, brute_maxΔ_delta_a0/a511/a1023}`已验，且`rg "run_ldpc_formal_v5\(" 0 hits`（仅审计脚本探针）。

## Phase D — D1-D10 十不变量（正交完备，1M CAL-only + VAL确认）

- [ ] **D1-D2 完备性与归一（NOT_COMPATIBLE 路由）**：`D1 completeness: len 1024 && ∀a a==Σ bit_i<<i` 已验，`D2 normalization: |Σ exp(log_post)-1|<1e-12 && |logsumexp-0|<1e-12` 已验，任一 FAIL 抬至 `NOT_COMPATIBLE`，落盘`D1/D2 PASS/FAIL` per session。
- [ ] **D3-D4 边际保持与 delta 退化**：`D3 marginal_preservation: llr≡0 ⇒ max|Δ|<1e-12` 已验，`D4 delta_concentration: K=1e6 定向a* ⇒ log_post[a*]==0±1e-9 && 其余<-1e2` 已验，FAIL 抬至 `MODEL_NOT_STABLE`，落盘`D3/D4`。
- [ ] **D5-D7 extrinsic/稳定/确定性**：`D5 extrinsic_consistency: ext==log_post-log_prior && |logsumexp(log_prior+ext)-0|<1e-12` 已验，`D6 log_domain_stability: K=1e6 全程 isfinite 无overflow` 已验，`D7 determinism: 同输入二次 max|Δ|==0` 已验，FAIL 抬至 `MODEL_NOT_STABLE`，落盘`D5/D6/D7`。
- [ ] **D8-D10 chain/隔离/正交**：`D8 chain_closure: |CE_full - (ΣCE_bit - D_bits)|<1e-9` (复用1M CAL 4-fold `λ` 的 `P(a|b)`，仅校验不作预算门禁) 已验，`D9 test_isolation: used_test==False && rg TEST 0 hits` 已验，`D10 orthogonality: 十项正交分解报告` 已验，`D8/D9` FAIL 抬至 `MODEL_NOT_STABLE/EVIDENCE_INCOMPLETE`，落盘`D8/D9/D10`。
- [ ] **D11 落盘 D1-D10 汇总**：`v71_results.json:invariants {D1..D10 per session, overall}` 与 `V71_KERNEL_REPORT.md` 一致，`py_compile` 已验。

## Phase E — 仅1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈

- [ ] **E1 benchmark 执行（仅1M，1/9/1024 block）**：在`1M session`的`CAL1024 (262144 pairs)+VAL256 (65536 pairs)`上对主核`soft_joint_factor_kernel`分`block∈{1,9,1024}`各计`wall_s/peak_MiB/per_invocation_ns`（`1: per-symbol`, `9: per-plane-batch`, `1024: per-frame 1024符号批量`，`log_prior`固定为1M CAL上`λ*`的`P(a|b)`，`llr`取`0`与`N(0,1)`两档，`wall`用`time.monotonic` `peak`用`tracemalloc`/`resource`，三次取median），落盘`v71_results.json:benchmark {1M, block 1/9/1024, wall_s, peak_MiB, per_invocation_ns, mode}`，`1p5M/2M`未 benchmark 已验`benchmark_executed_sessions==["1M"]`。
- [ ] **E2 路由阈判定**：`1024-block` 在 `1M VAL256` 全量 (`256*1024=262144` 符号) 上 `wall_1024≤30.0 && peak_1024≤2048` 判 `E_PERF_PASS`，否则 `E_PERF_BLOCKED`，三档明细与 `per invocation ns` 已报告，`V71_KERNEL_REPORT.md` 一致。
- [ ] **E3 审计关联**：`A5 runtime_caps` 与 `E benchmark` 关联审计已落盘`audit_E_correlation`。

## Phase F — f1.3 冻结 f_actual NOT_MEASURED

- [ ] **F1 f1.3 冻结**：算`CE_full^{VAL_1M} = -E_{1M VAL} log2 P(a|b)` (bits/symbol, `λ` 固定为1M CAL择优，不重选) → `required = ceil(1.3*1024*CE_full^{VAL_1M})` 整数已验，仅作`A6 disclosure`参照，落盘`required_1M / CE_full_1M`，`m_raw`不cap显式，`grep "min(1024" 0 hits`已验。
- [ ] **F2 f_actual NOT_MEASURED**：所有 `f_actual` 字段 `== "NOT_MEASURED"` 已验，`grep "f_actual.*NOT_MEASURED" v71_results.json` 命中且`rg "f_actual.*[0-9]\."`对数值赋值的命中为0，报告显式`f1.3 frozen, f_actual NOT_MEASURED`，门禁不以`f_actual`判，`V71_KERNEL_REPORT.md`一致。

## Phase G — per-session 6终端总体4态（优先级互斥，不启V72）

- [ ] **G1 Per-session 6终端 first-match（优先级互斥，D1-D10 + A1-A6 + E benchmark）**：`EVIDENCE_INCOMPLETE(D9/物化失败/C_ab非有限) > MODEL_NOT_STABLE(λ触边/ΔCE>0.5/unseen>1%/D3-D8 FAIL) > NOT_COMPATIBLE(A1/A2/D1/D2 FAIL) > READY(D1-10 PASS && READY && E PASS) > ADAPTER(D1-10 PASS && ADAPTER && E PASS) > HEAVY(E超限)`，`6 orthogonal counts ready/adapter/heavy/not_compatible/evidence/model` 已验，落盘`classification + successor + audit/D/E/f1.3` per session。
- [ ] **G2 总体4态**：`evidence_count>0 ⇒ OVERALL_EVIDENCE_INCOMPLETE / model_count>0 && ready+adapter==0 ⇒ OVERALL_MODEL_NOT_STABLE / ready==3 ⇒ OVERALL_KERNEL_READY / else ⇒ OVERALL_KERNEL_ADAPTER_OR_HEAVY` 基于3 sessions汇聚（E仅1M实测但分流仍基于三 session audit），`ready/adapter/heavy/not_compatible/evidence/model` 6计数已验，落盘`overall + 6 counts + f1.3`。
- [ ] **G3 Common审计表**：落盘`audit {per_session_classification[3], overall, ready/adapter/heavy counts, D1-D10 per session, audit_A1-A6 per session, E benchmark 1M, f1.3, f_actual NOT_MEASURED, successor per session}`，报告`overall 4态`审计章节显式三session是否同核且同`READY`。

## Phase H — 四工件 + 双报告交付（PLAN_CANDIDATE / DECODER_FREE，不启V72）

- [ ] **H1 编写`scripts/v71_soft_joint_factor.py`** (decoder-free, 本变更目录下): `python scripts/v71_soft_joint_factor.py [--registry v71_data_registry.json] [--out v71_results.json]` → `1M CAL C_ab/P/λ→D8 chain + 5函数1024枚举brute D1-D10 → 1M VAL 1/9/1024 benchmark + f1.3 freeze`，`rg "decode_" 0 hits` `rg -i "met|protograph|v72" 0 hits`（除successor注释）仅`numpy/pandas/pyarrow`，`py_compile PASS`，输出`v71_results.json + v71_table.(csv|json) + V71_KERNEL_REPORT.md` + 控制台摘要。
- [ ] **H2 编写`scripts/v71_ldpc_v5_audit.py`** (read-only A1-A6): `python scripts/v71_ldpc_v5_audit.py [--out v71_audit_report.json]` → `ldpc_v5* A1-A6 READY/ADAPTER/NOT_COMPATIBLE` per session + overall 4态，`rg "decode_" 0 hits` `rg "run_ldpc_formal_v5\(" 0 hits`（仅AST探针）仅`ast/importlib`，`py_compile PASS`，输出`v71_audit_report.json + V71_AUDIT_REPORT.md` + 控制台摘要。
- [ ] **H3 执行 decoder-free 回填（含5函数 + D1-D10 + A1-A6 + benchmark）**：运行`scripts/v71_soft_joint_factor.py`与`scripts/v71_ldpc_v5_audit.py`得每 session `D1-D10/audit_A1-A6/benchmark/f1.3/required/λ`与`overall 4态`，落盘`v71_results.json`与`v71_table.csv/.json`（CSV行对等，含`capacity_warning`正交 + `D1-D10/audit/benchmark`）与`v71_audit_report.json`，`D1-D10`已验，`A1-A6`已验，`1M 1/9/1024 30s/2GiB`已验，`f_actual NOT_MEASURED`已验。
- [ ] **H4 撰写双报告**：`V71_KERNEL_REPORT.md`（`per session 5函数/D1-D10/1024枚举双极brute 1e-12/1/9/1024 benchmark f1.3 freeze + overall 4态 + TEST隔离 + 1024维冻结 + V72_not_started`）与`V71_AUDIT_REPORT.md`（`A1-A6 per session / READY/ADAPTER/NOT_COMPATIBLE + overall 4态`）与`json/csv`一致，不扩大为`FER/SKR`，显式`1024枚举5函数 + D1-D10 + A1-A6 + 1M benchmark 30s/2GiB + f1.3 NOT_MEASURED`。
- [ ] **H5 自检（6终端+4态+守卫+R71-01~11，不启V72）**：`py_compile`双脚本 PASS, `rg "decode_" 0 hits`, `rg -i "met|protograph" 0 hits`, `rg -i "v72|qualification" 0 hits`（除V72_not_started注释），`git diff -- src/ ==0`未改码, V69 Stage2复用`3`已验, `D1-D10`已验, `5函数1024枚举双极brute 1e-12`已验, `A1-A6`已验, `1M 1/9/1024 30s/2GiB`已验, `f1.3 NOT_MEASURED`已验, `6终端优先级互斥`已验, `overall 4态`已验, `TEST未读`已验, `V72_not_started`已验, 报告与json/csv一致 **无TBD**, **A-H已闭合**。
- [ ] **H6 小测试**：`pytest -p no:cacheprovider -q`小测试（`test_v71_soft_joint_factor_kernel_small.py`）验证`bit展开 / D1-D10 小矩阵 / 5函数全零/delta 1e-12 / f1.3 NOT_MEASURED / A1-A6 mock / 1/9 benchmark 不含1024全量 + TEST隔离 + V72_not_started`，`py_compile`双PASS。
  - ponytail: `soft_joint_factor_kernel`为10-bit纯移位/掩码+`logsumexp`，不引`numba`；`D1-D10`小矩阵为`tuple`校验，`O(1024)`足够；`E benchmark`小测试仅 `1/9` 不测 `1024` 全量以控成本；`A1-A6` mock 用临时 `ldpc_v5*.py` 片段。

## Phase I — 守卫R71-01~11 + 单独提交推送新Plan SHA + 不启V72

- [ ] **I1 守卫R71-01~11落盘验证**：在`v71_manifest.json:guards {R71-01..R71-11}`逐项`true`，见Design §8 / Spec §10。
  - R71-01 冻结主体1024维纯因子核验证不改 + 不启V72
  - R71-02 extrinsic冻结 + 5函数纯枚举 log-domain
  - R71-03 D1-D10 十不变量正交完备
  - R71-04 只读 ldpc_v5* A1-A6 READY/ADAPTER/NOT_COMPATIBLE
  - R71-05 仅1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈
  - R71-06 f1.3冻结 f_actual NOT_MEASURED
  - R71-07 V67/V69三Session Stage2复用CAL选VAL确认一次
  - R71-08 per-session 6终端总体4态
  - R71-09 四工件+双报告完整
  - R71-10 decoder-free不构业务矩阵 + 不读TEST + 不创run_01 + 不启V72
  - R71-11 1024-state 数值闭合
- [ ] **I2 单独提交推送四工件+registry+双脚本+双报告（V71 provenance — 新Plan SHA）**：`git add openspec/changes/formal-ir-v71-soft-joint-factor-kernel/ scripts/v71_soft_joint_factor.py scripts/v71_ldpc_v5_audit.py v71_data_registry.json v71_results.json v71_table.csv v71_table.json v71_audit_report.json V71_AUDIT_REPORT.md V71_KERNEL_REPORT.md test_v71_soft_joint_factor_kernel_small.py v71_manifest.json && git commit -m "formal-ir-v71: 1024-state pure factor kernel 5FUNC D1-D10 A1-A6 READY/ADAPTER 1M 1/9/1024 30s/2GiB f1.3 NOT_MEASURED 6term4state" && git push origin formal-ir-mainline`，返回新`Plan SHA`（40位），记录于`proposal/design/tasks` HEAD占位替换，**不创建run_01，不启V72**。
- [ ] **I3 停留`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED`**，未创建任何`.../v71_*/run_01`且未创建任何`.../v72_*/run_01`，未构业务矩阵，不比较，不碰`V48-V70`块外，未转qualification，未启动V72，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT`独立线程复核`HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/TEST未读/D1-D10/5函数1024枚举 brute/A1-A6/1M benchmark 30s/2GiB/f1.3 NOT_MEASURED/6终端+4态/CAL选VAL确认一次/V72_not_started`），返回`Plan SHA / per-session D1-D10/audit/E + 各分流计数 + overall 4态`等待`PLAN_ACCEPT`。

## 本变更显式禁止

decoder/业务矩阵构造（`decode_*` / `construct_*_business` / `gf_rank_business` / `nested_business`等）；读密封`TEST`的`H/CE/NLL/MAP`统计或将其用于`P/required/rank`选择；读`VAL`参与`λ`择优（`λ`仅`1M CAL`）；在原`V55 90-block`或`V48-V70`已用`(source,session,frame)`上重跑先验估计而不零重叠；调`H1/Lane C/Δ8/decoder/m2/m_total/leak/prior/H_inc/H_total/verification`任一冻结参数或新增业务矩阵；**跨acquisition拼接凑3**；**将floor/round当ceil**；**将`min(1024, ceil(...))` cap伪装当通过**（`required`必须显式ceil，仅A6参照）；**将`+8`外degree/seed网格当自适应**；**用`VAL/TEST`择优`λ`**（`λ`仅`CAL`）；**将不足3伪判为complete**（应`EVIDENCE_INCOMPLETE`）；**将`acquisition`未去重多计**（必须V69复用）；**将1024枚举剪枝**（必须全1024态）；**将纯函数全零/ delta单极当全验证**（必须双极`1e-12`）；**将`D1/D2 FAIL`当可行**（必须`NOT_COMPATIBLE`）；**将`D1-D10`非正交混计**（必须逐项分解）；**将`f_actual`实测值当门禁**（必须`NOT_MEASURED`）；**将`1M`外 session benchmark 当路由**（必须仅1M 1/9/1024）；**将`30s/2GiB`阈放宽**（必须冻结）；**引MET/protograph/SC/Gray**（仅纯因子核）；**改`src/`基线**；宣称LDPC证伪或`FER/阈值/SKR/晋升`；创建正式`.../v71_*/run_01`；任意`bin_width/dimension/pairing/mapping`网格或阈网格（处理点单点）；用第二estimator作门禁；覆盖已有输出；`V55 90 / V48-V70`永久禁用違反；**主观“显著可行”替代硬阈`D1-D10 PASS && READY && E PASS`**；**擅自调V71以外码**（仅纯因子核）；**保留TBD占位不回填**；**启动V72**（任何`V72_*/run_01`、`QUALIFICATION_PLAN_READY`、`V72` OpenSpec预冻结均禁止）；**执行`run_ldpc_formal_v5`**（仅只读审计）。

## 验收

- proposal/design/tasks/specs一致 `9bc34be6→新Plan SHA` `84d62779` lifecycle `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED` 6终端+4态按优先级互斥明确，显式1024维冻结仅验证纯因子核、extrinsic冻结、5函数纯枚举 log-domain、D1-D10 十不变量、A1-A6 READY/ADAPTER/NOT_COMPATIBLE、仅1M 1/9/1024 30s/2GiB 路由阈、f1.3 freeze `f_actual NOT_MEASURED`、V69三Session Stage2复用、per-session 6终端总体4态、四工件产出已声明，严格复用V56权威算法，冻结分段/熵-CE与f公式/分流阈 + V72_not_started
- 1024维冻结仅核验证已验，`5函数 log-domain 1024枚举双极brute 1e-12`已验，`D1-D10`已验，`A1-A6 READY/ADAPTER`已验，`1M 1/9/1024 30s/2GiB`已验，`f1.3 NOT_MEASURED`已验，`6终端`已验，`overall 4态`已验，`CAL-only`选λ不读VAL/TEST且`VAL确认一次`已验，`VAL`上`D1-D10`一次确认已验，`纯函数`双极`1e-12`已验，不扩，禁第二estimator已验，`cal_val_consistency`已报告
- 合同`dimension 1024 / bin200 / nearest legacy_v1 / channels/frame anchor/mapping 每帧256`算法一致已验，`10-bit位展开`每帧已验，`extrinsic`冻结已验，偏则`EVIDENCE_INCOMPLETE`已验，`1024枚举`与`5函数`无丢已验
- 每session `CAL C_ab→P(a|b) λ(CAL 4-fold)→D8 chain→required ceil→D1-D10→audit A1-A6→E 1/9/1024→f1.3 NOT_MEASURED`已算且`CAL-only`选λ已验，`VAL`上`D1-D10/audit/E`一次确认已验，`纯函数`双极`1e-12`已验，不扩，禁第二estimator已验
- 每session `6终端 final_classification + successor`已落盘，`overall 4态`已统计
- `3行(每session)+总体4态 / 5函数/ D1-D10/ audit A1-A6/ benchmark/ f1.3 NOT_MEASURED/ classification/successor/capacity_warning/descriptive`已回填，`报告表CSV行对等JSON`已验，`overall 4态`已验，`V72_not_started`已验
- 守卫`R71-01~11`已验（`5函数 log-domain/ D1-D10/ A1-A6/ 1M 1/9/1024 30s/2GiB/ f1.3 NOT_MEASURED/ V69复用/6终端+4态/四工件+双报告/decoder-free不构业务矩阵不读TEST/不创run_01/py_compile/小测试+V72_not_started/1024闭合`）
- 双脚本`rg "decode_" 0 hits` `rg -i "met|protograph" 0 hits` `rg -i "v72|qualification" 0 hits`（除V72_not_started注释） `py_compile` PASS `pytest小测试`PASS `f_actual NOT_MEASURED`已验 `VAL未参与λ择优` `TEST未读` `5函数1024枚举`已验 `D1-D10`已验 `A1-A6`已验 `1M 1/9/1024 30s/2GiB`已验 `capacity_warning`正交与`descriptive`已落盘报告与json/csv一致未建`run_01`未启`V72`已停留`PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`仅改本目录 + `scripts/`（`src/`零改），未启动decoder/业务矩阵，**四工件+registry+双脚本+双报告已单独提交推送，新Plan SHA + per-session D1-D10/audit/E + 各分流数 + overall 4态已返回**，推送后等待独立审核
