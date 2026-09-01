# REDO V72P0: LOCAL_FACTOR_KERNEL_PASS preserved, P0A k=2/3 BP syndrome 0/1 flip vs brute exact posterior 1e-9 tree-only 7cover, P0B sparse CSR IRA 9036x10240, 5-state ADAPTER_PLAN_READY requires 3 passes, provenance synced

# OpenSpec Tasks: formal-ir-v72p0-soft-joint-binary-synthetic — 1024→10bit local factor 去 self ↔ mother 9036×10240 incremental ↔ exact 64b tag 合成 correctness (PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED)

**Lifecycle**: `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` — **Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止，T_LF01-08 去 self 8测试 + backend Q1-Q6 三态 enum 非字符串 READY + P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols exhaustive + P0B 9036×10240 nested rank C1-C6 + 8终态 wall first-match + T0-T3 矩阵，四工件双报告，不跑 decoder 不改 V70/V70R1/V71**

**HEAD**: `0926457520a0c680d087de28b1380f2a87f8161a` (动态绑定 `git rev-parse HEAD`; 2M禁止, mother 仅合成, V70/V71 零改) + data `84d62779` + `synthetic_v72p0`

**Predecessor**: `formal-ir-v71-soft-joint-factor-kernel` `487be113` + `formal-ir-v70-binary-soft-joint-feasibility` `9bc34be6` + `formal-ir-v70r1-parametric-channel-model-check` `0509d10b (CHANGES)` → `V72P0-SYN`

**Method frozen**: `Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止 tag 64b exact` 零改；处理点 `84d62779` 合成锚点；`去 self local factor Σ_{j≠i} bits_j·llr_j` + `T_LF01-08` + `Q1-Q6 enum` + `P0A tiny 2/3/4` + `P0B mother 9036×10240`

**Boundary**: 仅验证合成链条 correctness，不改主体；去 self 冻结 `Σ_{j≠i}`，8测试 brute `1e-12`，Q1-Q6 READY 非字符串，P0A tiny exact，P0B nested rank，8终态 wall first-match，T0-T3，不跑 decoder 不启 V72

## Phase A — 合成注册表（synthetic_v72p0，2M 禁止，不启 V72）

- [ ] **A1 冻结合成注册表 `v72p0_data_registry_synthetic.json`（SYNTHETIC_ONLY，2M禁止）**：写入 `schema v72p0_synthetic_v1, lifecycle PLAN_CANDIDATE/SYNTHETIC_ONLY, Q1024 N1024 Nbit10240 M9036 f1.3 f_actual NOT_MEASURED used_2m false successor_v72_not_started true synthetic_seed V72P0-SYN-P0A-B, P0A {total_bits≤9 k2-3 n2-3 各 64 trials} P0B {mother_shape [9036,10240] r0 160 Δ8 Rs, col_order sym*10+bit}`，校验 `Q==1024 && N==1024 && M==9036 && f==1.3 && used_2m==false && Rs[0]==160 && Rs[-1]==9036 && successor_v72_not_started==true`，且 `rg -i "2M" scripts/v72p0_*.py 0 hits`（除禁止声明 `used_2m==false`），禁止事后换 seed 或读 2M real。
- [ ] **A2 冻结去 self 语义与母矩阵列序（纯比特置换，不改 Q，仅合成）**：实现 `bit_i(s)=(s>>i)&1, i=0..9` 与 `col = sym_idx*10 + bit_pos` 与 `去 self Σ_{j≠i}` 冻结定义，每 synthetic 校验 `∀s s==Σ bit_i<<i` 双射且 10 bits 无丢，`H_mother` 列序与 LF 位定义一致，`rg -i "gray|met|protograph|sc_coupling|v72.*run_01" 0 hits`（除注释 `V72_not_started`），`src/` 零改，`V72_not_started` 显式。

## Phase B — 冻结主体合成链条验证仅核检查（SYNTHETIC_ONLY，不构业务 disclosure，不启 V72）

- [ ] **B1 主体明文化（逐项显式，冻结零改，2M禁止，不启 V72）**：写入 `v72p0_manifest.json:frozen_body {Q1024, N1024, Nbit10240, M9036, f1.3 NOT_MEASURED used_2m false, tag 64b exact SHA256(bits)[:8B]==SHA256(s)[:8B] LE canonical, col_order sym*10+bit, successor_v72_not_started true}`，显式 `not Gray/not MET/protograph/SC/not 2M/not H business disclosure/not V72`，`git diff -- src/ ==0 && git diff -- openspec/changes/formal-ir-v70* ==0 && git diff -- openspec/changes/formal-ir-v71* ==0`（除本目录）已验。
- [ ] **B2 合成权威算法复用**：P0A/P0B 均按 `legacy_v1` 合成采样不读 real `pairs.parquet`，`bit_i` 展开仅在 synthetic `s` 上比特置换，不改 real 帧边界，不读 2M，不启 V72，不执行 `run_ldpc_formal_v5`。
- [ ] **B3 不跑 decoder 守卫 + 不字符串判 READY 守卫 + 不启 V72 守卫**：`rg "decode_" scripts/v72p0_soft_joint_binary_synthetic.py 0 hits && rg "decode_" scripts/v72p0_backend_audit.py 0 hits` 且不调用业务 `H` disclosure 构造（`gf_rank_pure` 仅 P0B 秩校验，不属业务 `construct`，仅高斯消元），且 `rg '"READY"' scripts/v72p0_backend_audit.py 0 hits` 且 `rg '"READY"' scripts/v72p0_soft_joint_binary_synthetic.py 0 hits`（除注释），审计脚本内 `BackendState.READY` enum 比较已验，且 `rg -i "v72.*run_01|qualification.*run" 0 hits`（除 `V72_not_started` 注释），`py_compile` 双脚本校验；脚注 `ponytail:` 标明 ceiling（若需后续 V72 real mother，需另起 OpenSpec）。

## Phase C — 去 self local factor 定义 + 8测试（synthetic only，去 self 冻结）

- [ ] **C1 冻结去 self LLR 定义**：写入 `v72p0_manifest.json:local_factor {def: "log_post_excl_i[a]=log_prior[a]+Σ_{j≠i} bits_j(a)·llr_j - logZ_excl_i", incl对照 "Σ_j bits_j·llr_j", self_exclusion: true, log_domain: true, pure: true}`，`log_post_excl_i` 排除 self `i`，`llr_out_i` 由 excl 归一后 `logsumexp_{1} - logsumexp_{0}`，与全包含核差 `bits_i·llr_i` 已验，`V72_not_started`。
- [ ] **C2 实现去 self 纯函数 log-domain（枚举1024，去 self 8测试）**：在 `scripts/v72p0_soft_joint_binary_synthetic.py` 实现 `bit_factor_from_llr_incl / local_factor_excl / soft_joint_factor_kernel_incl / llr_out_from_excl / validate_local_factor`（签名见 Design §5.2，`numpy.logaddexp.reduce` 手写 `logsumexp`，枚举1024态，`logZ_excl`/`logZ_incl` 配分差校验，log域运算），校验 `T_LF01-08`（见 Design §5.3）`1e-12/1e-9` 正交，且 `T_LF05 self_exclusion` 对 `i=0,5,9` 三点位 `max|Δ|<1e-12`，`ponytail:` 不引 `numba`，落盘 `T_LF01-08 PASS/FAIL` per synthetic，`py_compile PASS`。
- [ ] **C3 去 self 8测试落盘**：在 `v72p0_results.json:local_factor {T_LF01 completeness, T_LF02 normalization, T_LF03 marginal, T_LF04 delta, T_LF05 self_exclusion (per i 0,5,9), T_LF06 stability K=1e6 isfinite, T_LF07 determinism, T_LF08 brute maxΔ_all_zero/delta_a0/a511/a1023}` 已验，且 `rg "run_ldpc_formal_v5\(" 0 hits`。

## Phase D — Backend 只读 6问三态 enum 非字符串 READY（per synthetic，不执行 decoder）

- [ ] **D1 Q1-Q3 基础三态**：`Q1 interface_presence / Q2 policy_manifest_schema(mother 9036×10240) / Q3 backend_model_binding` 每 synthetic 独立 `PASS/FAIL/NOT_APPLICABLE` enum（`IntEnum BackendState`），`AST探针` 不执行 `run_ldpc_formal_v5`，`rg "decode_" 0 hits`，`rg '"READY"' 0 hits` 已验，落盘 `Q1-Q3 PASS/FAIL/NOT_APPLICABLE`。
- [ ] **D2 Q4-Q6 适配三态**：`Q4 extrinsic_interface(self_excl) / Q5 runtime_caps(wall/peak) / Q6 disclosure_accounting(9036 incremental)` 三态 enum 已验，`Q4` 探针 `error_channel: List[float]` 且过滤 self 逻辑（`rg '"READY"' 0 hits` 且 `backend_state == BackendState.READY` enum 比较已验），`Q6` 校验 `9036` 可容纳 `incremental_prefix` 且 `verification_tag_bits_component` 不混 `key_dependent`。
- [ ] **D3 分流判定落盘（非字符串）**：`READY = Q1∧Q2∧Q3 PASS ∧ Q4 PASS(self_excl) ∧ Q6 PASS(9036)` / `ADAPTER = Q1-Q3 PASS ∧ (Q4 ADAPTER ∨ Q6 ADAPTER)` / `NOT_COMPATIBLE = Q1/Q2 FAIL ∨ T_LF01/02 FAIL` enum 分流已验，禁止 `status=="READY"` 字符串判定（`rg '"READY"' 0 hits` + `assert type(state)==BackendState`），落盘 `backend_classification READY/ADAPTER/NOT_COMPATIBLE` per synthetic + `audit_report.json`。

## Phase E — synthetic P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols exhaustive (wall 30s gate)

- [ ] **E1 P0A tiny exhaustive 执行**：对 `N_small ∈ {2,3,4}` 各 `64 trials` 合成采样 `bits_small`（`N_small*10` bits, seed `V72P0-SYN-P0A-{N_small}-{trial}`），构造小 `H_small ∈ GF2^{m_small×N_small*10}`（`m_small=ceil(1.3*N_small*CE_synth)`，`CE_synth` 合成先验收敛近似 `0.8` 仅描述性），计 `syndrome = H_small @ bits (GF2)` 与 `tag = SHA256(bits)[:8B]` 与 `tag_from_s = SHA256(s_hat)[:8B]` exact 比较，记录 `wall_s/peak_MiB/per_invocation_ns`，落盘 `v72p0_results.json:P0A {total_bits≤9 k2-3 n2-3 各 64 trials 0 mismatch}`，`wall≤30s && peak≤2048MiB` 判 `P0A_PASS`，否则 `TINY_FAIL`。
- [ ] **E2 tag exact 校验**：`tag == tag_from_s` 且 `syndrome_incremental`（小矩阵前缀）`syndrome_{r2}[0:r1]==syndrome_{r1}` 已验，`ponytail:` 采样不足 `Q^{N_small}` 全空间时显式报告 `exhaustive_coverage` 比例。
- [ ] **E3 P0A 审计关联**：`Q5 runtime_caps` 与 `E wall` 关联审计已落盘 `audit_E_correlation`.

## Phase F — synthetic P0B mother 9036×10240 nested rank 等 gate (C1-C6)

- [ ] **F1 mother 生成（合成域，Δ8 前缀）**：确定性 `SeedSequence("V72P0-SYN-MOTHER-9036x10240")` 生成 `H_mother ∈ GF2^{9036×10240}`（列序 `sym*10+bit`），`r0=160` 起 `Rs={r0 + k·8 ≤9036}∪{9036}`（末段补至 `9036` 报告 `achieved==requested true`），落盘 `mother_shape [9036,10240] r0 160 Δ8 Rs`，`rg '"READY"' 0 hits` 已验，`synthetic_only` 显式。
- [ ] **F2 C1-C4 前缀秩/非零/去重/嵌套校验（确切 GF2 秩高斯消元）**：对 `∀r∈Rs` 校验 `C1 rank==r` + `C2 weight>0` + `C3 H_i≠H_j` + `C4 H_{0:r}==H_mother[0:r]` 前缀嵌套，落盘 `C1-C4 PASS/FAIL per r`，`py_compile PASS`。
- [ ] **F3 C5-C6 增量/tag exact 校验**：`C5 syndrome_{r2}[0:r1]==syndrome_{r1}` 增量合成对 `R=3` 随机比特样本已验，`C6 tag_exact SHA256(bits)==SHA256(s_hat)` 对 `64` 随机 `N=1024` 合成样本 exact `0 mismatch` 已验，落盘 `C5/C6 PASS/FAIL`，`P0B_PASS = C1∧C2∧C3∧C4∧C5∧C6`。

## Phase G — 8终态 wall first-match + overall 2态（per synthetic，不启 V72）

- [ ] **G1 Per-synthetic 8终态 first-match（优先级互斥，T_LF+Q+C+wall）**：`EVIDENCE_INCOMPLETE(物化/C_ab非有限/P0A未执行) > MODEL_NOT_STABLE(T_LF03/04/05/06/07/08 FAIL) > BACKEND_NOT_COMPATIBLE(Q1/Q2/T_LF01/02 FAIL) > TINY_FAIL(P0A mismatch或wall>30s) > MATRIX_RANK_FAIL(C1/C2/C3 FAIL) > SYNDROME_NESTED_FAIL(C4/C5 FAIL) > READY(T_LF PASS∧READY∧P0A PASS∧C1-C6 PASS∧wall≤30s) > ADAPTER(T_LF PASS∧Q1-Q3 PASS∧Q4 ADAPTER∧P0A/P0B PASS)`，`8 orthogonal counts` 已验，落盘 `classification + successor + T_LF/Q/P0A/P0B/wall` per synthetic。
- [ ] **G2 Overall 2态**：`ready_count==1 && ...` 基于 synthetic 汇聚（synthetic 单域），`ready/adapter/tiny/rank/nested/evidence/model/backend 8计数` 已验，落盘 `overall ∈ {OVERALL_READY, OVERALL_ADAPTER_OR_FAIL} + 8 counts`。
- [ ] **G3 Common审计表**：落盘 `audit {per_synthetic_classification, overall, 8 counts, T_LF01-08 per synthetic, Q1-Q6 per synthetic, P0A 2/3/4, P0B C1-C6, wall/peak, f1.3 NOT_MEASURED, successor per synthetic}`，报告 `overall 2态` 审计章节显式 synthetic 是否同母矩阵且同 `READY`。

## Phase H — 四工件 + 双报告交付（PLAN_CANDIDATE / SYNTHETIC_ONLY，不启 V72）+ T0-T3 矩阵

- [ ] **H1 编写 `scripts/v72p0_soft_joint_binary_synthetic.py`** (SYNTHETIC_ONLY, 本变更目录下): `python scripts/v72p0_soft_joint_binary_synthetic.py [--registry v72p0_data_registry_synthetic.json] [--out v72p0_results.json]` → `T_LF01-08 去 self → P0A tiny 2/3/4 exhaustive 64 trials → P0B mother 9036×10240 C1-C6 → wall/peak + f1.3 NOT_MEASURED`，`rg "decode_" 0 hits` `rg '"READY"' 0 hits` `rg -i "met|protograph|v72.*run_01" 0 hits`（除 `V72_not_started` 注释）仅 `numpy/pandas/pyarrow`，`py_compile PASS`，输出 `v72p0_results.json + v72p0_table.(csv|json) + V72P0_SYN_REPORT.md` + 控制台 8终态摘要。
- [ ] **H2 编写 `scripts/v72p0_backend_audit.py`** (read-only Q1-Q6 三态 enum): `python scripts/v72p0_backend_audit.py [--out v72p0_backend_audit_report.json]` → `Q1-Q6` 三态 `PASS/FAIL/NOT_APPLICABLE` enum（`IntEnum BackendState`）`READY/ADAPTER/NOT_COMPATIBLE` per synthetic + overall 2态，`rg "decode_" 0 hits` `rg '"READY"' 0 hits` `rg "run_ldpc_formal_v5\(" 0 hits`（仅 AST 探针）仅 `ast/importlib/enum`，`py_compile PASS`，输出 `v72p0_backend_audit_report.json + V72P0_BACKEND_AUDIT_REPORT.md` + 控制台摘要。
- [ ] **H3 T0-T3 矩阵执行与落盘**：
  - **T0** compile/import/structural/tiny-math: `py_compile` 双脚本 PASS, `import` 无 `decode_`，`T_LF01-03` 小矩阵 `|Δ|<1e-12`，`git diff -- src/ ==0` 未改码
  - **T1** focused unit & tamper: `T_LF01-08` 8测试 + `Q1-Q6` mock 三态 enum（`rg '"READY"' 0 hits` 已验）+ `C1-C4` 对 mother 前 `r0+8*2` 前缀小秩 `3` 点 + `incremental` 前 `2` 点，`pytest -p no:cacheprovider -q test_v72p0_*.py` 前置
  - **T2** complete fake/test-only qualification + strict replay: 运行 `scripts/v72p0_*.py --fake --test-only` 得 `P0A tiny + P0B 前K秩` fake 资格 + `strict replay ok==true`（制品 DAG/hash 重核，不跑 decoder）
  - **T3** cross-version / broad regression: `rg "decode_" 0 hits` + `git diff -- openspec/changes/formal-ir-v70* 0 hits` + `git diff -- openspec/changes/formal-ir-v71* 0 hits`（除本目录）+ `used_2m==false` 回归 + `V70/V71` 冻结值对照未漂移
  均落盘 `v72p0_manifest.json: T0-T3 {pass/fail}`，`V72P0_SYN_REPORT.md` 一致。
- [ ] **H4 撰写双报告**：`V72P0_SYN_REPORT.md`（`T_LF01-08/P0A 2/3/4/P0B C1-C6/wall/peak/per_invocation/f1.3 NOT_MEASURED + overall 2态 + 2M未读 + Q1024冻结 + V72_not_started`）与 `V72P0_BACKEND_AUDIT_REPORT.md`（`Q1-Q6 per synthetic 三态 enum / READY/ADAPTER/NOT_COMPATIBLE + wall + overall`）与 `json/csv` 一致，不扩大为 `FER/SKR`，显式 `去 self 8测试 + Q1-Q6 enum + P0A tiny + P0B 9036×10240 + wall 30s/2GiB + f1.3 NOT_MEASURED`。
- [ ] **H5 自检（8终态+overall+T0-T3+守卫 R72-01~09，不启 V72）**：`py_compile` 双脚本 PASS, `rg "decode_" 0 hits`, `rg '"READY"' 0 hits`, `rg -i "met|protograph" 0 hits`, `rg -i "v72.*run_01|qualification.*run" 0 hits`（除 `V72_not_started` 注释），`git diff -- src/ ==0` 未改码, 合成注册表 `Q1024 N1024 M9036 used_2m false` 已验, `T_LF01-08` 已验, `Q1-Q6 enum` 已验, `P0A tiny 2/3/4 0 mismatch` 已验, `P0B C1-C6` 已验, `8终态优先级互斥` 已验, `overall 2态` 已验, `wall 30s/2GiB` 已验, `f1.3 NOT_MEASURED` 已验, `2M未读` 已验, `V72_not_started` 已验, `T0-T3` 已验, 报告与 `json/csv` 一致 **无 TBD**, **A-H 已闭合**。
- [ ] **H6 小测试**：`pytest -p no:cacheprovider -q` 小测试（`test_v72p0_soft_joint_binary_synthetic_small.py`）验证 `bit展开 / T_LF01-08 小矩阵 / 去 self 1e-12 / Q1-Q6 enum mock 非字符串 / P0A 前K秩 / wall gate + 2M隔离 + V72_not_started`，`py_compile` 双 PASS。
  - ponytail: `local_factor_excl` 为 10-bit 纯移位/掩码 + `logsumexp`，不引 `numba`；`T_LF01-08` 小矩阵为 `tuple` 校验 `O(1024)` 足够；`P0B` 小秩仅前 `3` 行前缀以控成本；`Q1-Q6` mock 用临时 `ldpc_v5*.py` 片段 `IntEnum`。

## Phase I — 守卫 R72-01~09 + 单独提交推送新 Plan SHA + 不启 V72

- [ ] **I1 守卫 R72-01~09 落盘验证**：在 `v72p0_manifest.json:guards {R72-01..R72-09}` 逐项 `true`，见 Design §8 / Spec §10。
  - R72-01 冻结主体 Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED + 2M禁止 + 不启 V72
  - R72-02 local factor 去 self LLR 冻结 + 8测试
  - R72-03 backend 只读 Q1-Q6 三态 enum 非字符串 READY
  - R72-04 synthetic P0A tiny total_bits≤9 k2-3 n2-3 exhaustive symbols exact
  - R72-05 synthetic P0B mother 9036×10240 nested rank C1-C6
  - R72-06 8终态 wall first-match
  - R72-07 T0-T3 矩阵
  - R72-08 四工件+双报告完整
  - R72-09 SYNTHETIC_ONLY 不跑 decoder 不读 2M 不创 run_01 不启 V72
- [ ] **I2 单独提交推送四工件+registry+双脚本+双报告（V72P0 provenance — 新 Plan SHA）**：`git add openspec/changes/formal-ir-v72p0-soft-joint-binary-synthetic/ scripts/v72p0_soft_joint_binary_synthetic.py scripts/v72p0_backend_audit.py v72p0_data_registry_synthetic.json v72p0_results.json v72p0_table.csv v72p0_table.json v72p0_backend_audit_report.json V72P0_BACKEND_AUDIT_REPORT.md V72P0_SYN_REPORT.md test_v72p0_soft_joint_binary_synthetic_small.py v72p0_manifest.json && git commit -m "formal-ir-v72p0: Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止 去self 8test Q1-Q6 enum P0A tiny total_bits≤9 k2-3 n2-3 exhaustive P0B 9036x10240 8term T0-T3" && git push origin formal-ir-mainline`，返回新 `Plan SHA`（40位），记录于 `proposal/design/tasks` HEAD 占位替换，**不创建 run_01，不启 V72**。
- [ ] **I3 停留 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED`**，未创建任何 `.../v72p0_*/run_01` 且未创建任何 `.../v72_*/run_01`，未构业务 disclosure，不比较，不碰 `V70/V71` 块外，未转 qualification，未启动 V72，仅改本目录 + `scripts/`，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01 不存在/py_compile/2M 未读/T_LF01-08 self_exclusion brute/ Q1-Q6 enum 非字符串/ P0A tiny total_bits≤9 k2-3 n2-3 exhaustive exact/ P0B 9036×10240 nested rank/8终态 wall/ T0-T3/f1.3 NOT_MEASURED/V70_V71 未改/V72_not_started`），返回 `Plan SHA / per synthetic T_LF/Q/P0A/P0B/wall + 8终态计数 + overall 2态` 等待 `PLAN_ACCEPT`。

## 本变更显式禁止

decoder/业务 disclosure 构造（`decode_*` / `construct_*_business` / `gf_rank_business` 除 `gf_rank_pure` 外）；读密封 `2M` real 的 `H/CE/NLL/MAP` 统计或将其用于 `P/required/rank` 选择；读 `VAL`/`2M` 参与 `λ` 择优（`λ` 仅 synthetic 描述性）；在 `V70/V71` 已用 `(source,session,frame)` 上重跑先验估计而不零重叠；调 `Q/N/Nbit/M/tag/prior/H` 任一冻结参数或新增业务 disclosure；**跨 synthetic/real 拼接凑**；**将 floor/round 当 ceil**；**将 `min(9036, ceil(...))` cap 伪装当通过**（`required` 必须显式 ceil，仅 P0B 上限参照）；**将 `+8` 外 degree/seed 网格当自适应**；**用 real VAL/2M 择优 `λ`**（仅 synthetic）；**将 `2M` 未隔离当 complete**（应 `EVIDENCE_INCOMPLETE`）；**将 acquisition 未去重多计**（必须 synthetic 独立）；**将1024枚举剪枝**（必须全1024态）；**将去 self 单极当全验证**（必须 `T_LF01-08` 8项正交）；**将 `T_LF01/02 FAIL` 当 READY**；**将 `T_LF01-08` 非正交混计**；**将 `Q1/Q2 FAIL` 当 READY**；**将 `Q1-Q6` 字符串 `"READY"` 判 READY**（必须 `enum == BackendState.READY`）；**将 `f_actual` 实测值当门禁**（必须 `NOT_MEASURED`）；**将 `P0A` 未执行当 READY**；**将 `wall>30s` 放宽**；**引 MET/protograph/SC/Gray**；**改 `src/` 基线**；宣称 `FER/阈值/SKR/晋升`；创建正式 `.../v72p0_*/run_01`；任意 `bin_width/dimension/pairing/mapping` 网格或阈网格（处理点单点）；用第二 estimator 作门禁；覆盖已有输出；`V70/V71` 永久禁用违反；**主观“显著可行”替代硬阈 `T_LF PASS ∧ Q READY ∧ P0A/P0B PASS ∧ wall≤30s`**；**擅自调 V72P0 以外码**（仅合成链条）；**保留 TBD 占位不回填**；**启动 V72**（任何 `V72_*/run_01`、`QUALIFICATION_PLAN_READY` 均禁止）；**执行 `run_ldpc_formal_v5`**（仅只读审计）。

## 验收

- proposal/design/tasks/specs 一致 `8dfd7c9→新 Plan SHA` `84d62779 + synthetic_v72p0` lifecycle `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` + `V72_NOT_STARTED` 8终态按优先级互斥明确，显式 Q1024 N1024 Nbit10240 M9036 f1.3 NOT_MEASURED 2M禁止、去 self 8测试、Q1-Q6 enum 非字符串、P0A tiny total_bits≤9 k2-3 n2-3 exhaustive exact、P0B 9036×10240 嵌套 rank、8终态 wall、T0-T3、四工件产出已声明，严格合成锚点，冻结去 self /熵-CE与f公式/分流阈 + V72_not_started
- 去 self 冻结已验，`T_LF01-08` 8测试 `1e-12/1e-9` 已验，`Q1-Q6 enum` 非字符串已验，`P0A 2/3/4 0 mismatch` 已验，`P0B C1-C6` 已验，`8终态` 已验，`overall 2态` 已验，`SYNTHETIC_ONLY 2M未读` 已验，`wall 30s/2GiB` 已验，`f1.3 NOT_MEASURED` 已验，禁第二 estimator 已验
- 合同 `Q1024 N1024 Nbit10240 M9036 列序 sym*10+bit tag 64b exact f1.3` 算法一致已验，去 self 每位 `i=0,5,9` 已验，偏则 `EVIDENCE_INCOMPLETE` 已验，`1024枚举` 与 `8测试` 无丢已验
- 每 synthetic `P0A tiny → P0B mother rank→wall→f1.3 NOT_MEASURED` 已算且 `SYNTHETIC_ONLY 2M未读` 已验，`T0-T3` 已验
- 每 synthetic `8终态 final_classification + successor` 已落盘，`overall 2态` 已统计
- `synthetic_case 行 (P0A 2/3/4 + P0B) + overall 2态 / T_LF01-08/ Q1-Q6/ P0A/P0B/wall/peak/classification/successor/8counts` 已回填，`报告表 CSV 行对等 JSON` 已验，`overall 2态` 已验，`V72_not_started` 已验
- 守卫 `R72-01~09` 已验（`去 self 8test/ Q1-Q6 enum/ P0A tiny/ P0B 9036×10240 8term wall/ T0-T3/ 四工件+双报告/SYNTHETIC_ONLY不跑decoder不读2M`）
- 双脚本 `rg "decode_" 0 hits` `rg '"READY"' 0 hits` `rg -i "met|protograph" 0 hits` `rg -i "v72.*run_01|qualification.*run" 0 hits`（除 `V72_not_started` 注释）`py_compile` PASS `pytest 小测试` PASS `f1.3 NOT_MEASURED` 已验 `SYNTHETIC_ONLY 2M未读` `T_LF01-08` 已验 `Q1-Q6 enum` 已验 `P0A/P0B` 已验 `wall 30s/2GiB` 已验 `8counts` 正交与 `descriptive` 已落盘报告与 `json/csv` 一致未建 `run_01` 未启 `V72` 已停留 `PLAN_CANDIDATE / SYNTHETIC_ONLY / EXECUTE_NOT_AUTHORIZED` 仅改本目录 + `scripts/`（`src/` 零改），未启动 decoder/业务 disclosure，**四工件+registry+双脚本+双报告已单独提交推送，新 Plan SHA + per synthetic T_LF/Q/P0A/P0B/wall + 8终态计数 + overall 2态已返回**，推送后等待独立审核
