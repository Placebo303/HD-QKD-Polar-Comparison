# OpenSpec Proposal: formal-ir-v66-single-segment-adaptive-nbldpc

**Status**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 本轮仅交付计划四工件 + decoder-free 只读调查 + 冻结注册表 + spike 摘要 + 终态机 + 独立 review packet，不实现/不执行 decoder，不创建 run_01，不比较，不改 baseline，不转 qualification，不自行 ACCEPT
**Domain**: Formal IR / NB-LDPC single-segment adaptive (V64/V65 唯一后继探索分支)
**Change ID**: `formal-ir-v66-single-segment-adaptive-nbldpc`
**Cycle ID**: `V66-ADAPT` (single-segment-adaptive), predecessor `formal-ir-v65-new-session-channel-compatibility` (9625afb4→cabc928f) + `formal-ir-v64-full-symbol-verification-correction` (80c35647/6c7b00a9 22/24 PASS)
**Branch**: `formal-ir-mainline`
**HEAD**: `832e5394bb366927c779414ee5a08427bd740a2d` (本次修订后单独提交推送产生的新 40位 Plan SHA，实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 40位重核，不一致阻塞；归档前重核)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点；V66 单 session 复用该处理点，不换点)
**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — `DEVELOPMENT_BENCHMARK` 表示允许复用旧 session 数据但显式标记 `development_replay=true` 的开发态 benchmark，不作 qualification/对比；任何 decoder 执行需独立 `PLAN_ACCEPT` + `EXECUTE_AUTH`

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 只读调查脚本 + 1 decoder-free spike + 2 注册表 + 1 报告占位 + review packet；零 decoder/矩阵/依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: `numpy` 直算 `C_ab/bincount2d` + 链式 CE，不引 `scipy/sklearn`；`m` 校验纯代数，不调 decoder。

> **科学问题（冻结，2026-08-31 修订）**：于**单一 session `20260123_1M_600k_0dB` 连续数据段**内，切 `CAL 24 blocks + VAL 24 blocks + EVAL 24 blocks =72 blocks overall`（单源单 session，内部互不重叠，键 `(source, session_id, frame_id)`），以 `CAL` 重估 `P(U1|B)/P(U2|U1,B)`，以 `VAL` 上 `CE1/CE2` 得 `raw m1_raw/m2_raw = ceil(1.3*1024*CE/5)`，在同家族内至多 `+8` 档调整得到已验证码 `m1<1024 && m2<1024` 且满秩嵌套披露一致后，冻结参数在**密封 `EVAL`** 上度量 `verified exact rate` 是否达到门禁 `exact_full≥19/24 overall && undetected==0`（含披露、效率分解，**已删 per-source 6/8**），且全程不以 `EVAL` 调参，保持 decoder-free 先验证 `RATE_NOT_FEASIBLE` 守卫（`m1/m2` 分别判，不用 `m_total`）；族不能覆盖则 `MATRIX_NOT_CONSTRUCTIBLE`。

## Goal

以最短 decoder-free 路径完成**单 session 单源自适应**的可验证闭环预冻结，为后续独立授权的 `EVAL` decoder 测量提供：

### 1. 单 session 单源冻结分段（复用旧数据但 development_replay 标记，键为 `(source, session_id, frame_id)`）

- **规模**：`CAL 24 blocks + VAL 24 blocks + EVAL 24 blocks =72 blocks overall`，全部归属 `20260123_1M_600k_0dB` 单 session，每 block `4×256=1024 symbols`, 每 frame `256 pairs`，`CAL || VAL || EVAL` 零重叠且与 `V13/V48..V64` 零重叠（键 `(source,session,frame)`），单 `session_id=20260123_1M_600k_0dB` provenance，不跨 session 拼接。
- **判定**：若单 session 可用连续窗口 `K <72` 或任一段 `!=24` 则 `V66_DATA_NOT_READY`（不伪造，不以 SER/vis 代理），否则冻结 `v66_data_registry.json` authoritative。
- **可复用旧数据**：复用 `v55_intake_20260828` 中 `20260123_1M_600k_0dB` 2130 frames (`K=532`) 的前 72 blocks 连续窗口，显式标记 `development_replay=true` 且 `replay_source=v55_intake_20260828`，与 fresh qualification 区分。

### 2. 冻结主体零改（U=32*U1+U2, Lane C conditional, Δ8 家族，不引 MET 等）

- **不变量**：`n=1024, q=1024 (10-bit s=32*u1+u2, U1=s>>5 0..31 high, U2=s&31 low), GF32 poly37, H1 16×1024 rank16 80b, L1-APP q via H1 BP, Lane C ordinal-2 s38310x m2 184/190/192 per source（单源仅 184 生效）, H_inc1/2 Δ8×1024 同家族巢式, decoder 90/1.0 poly37 early-stop, full-symbol tag 64b canonical 32*U1+U2 单64b, leak=5*(m1+m2)+64` 全只读。
- **禁新结构**：不引入 MET / protograph / SC / 空间耦合 / 新 degree 分布 / 非 Δ8 家族矩阵；唯一变量是 `P(U1|B)/P(U2|U1,B)` 重估与同家族 `+8` 冗余档。

### 3. 仅允许重估与同家族 +8 自适应（VAL CE 门禁，decoder-free 先验，不依 EVAL 调参）

- **重估**：`CAL 24 blocks (6144 frames? 24*256? 实际 24 blocks=96 frames=24576 pairs 单源)` 上 `C_ab 1024×1024 → P(a|b) → P(U1|B) 32×1024 + P(U2|U1,B) 32×32×1024`，随后在 `VAL` 上计量 `CE1=-E_VAL log P(U1|B)`, `CE2=-E_VAL log P(U2|U1,B)`, `CE_full` 链式。
- **raw 冗余**：`m1_raw=ceil(1.3*1024*CE1/5)`, `m2_raw=ceil(1.3*1024*CE2/5)`，**不 cap 伪装**。
- **同家族 +8 调整**：仅允许在已冻结验证通过的 `H` 家族内将 `m1_raw/m2_raw` 各自上调至最近的 `H` 可构造行数（step `+8` 档，来自 `H_inc Δ8`），即 `m1 = ceil_to_family(m1_raw, +8)`, `m2 = ceil_to_family(m2_raw, +8)`，若族内无覆盖则 `MATRIX_NOT_CONSTRUCTIBLE`（而非静默 cap）。禁止以 `EVAL` 统计重选 `+8` 档或网格搜索其他 Δ。
- **decoder-free 码校验（先于 EVAL）**：`m1<1024 && m2<1024 && gf_rank(H1(m1))==m1 && gf_rank(H2(m2))==m2 && nested(H) && disclosure ==5*(m1+m2)+64 && constructibility` 全过才进入 EVAL；任一失败则 `overall=V66_RATE_NOT_FEASIBLE`（含 `MATRIX_NOT_CONSTRUCTIBLE` 子类），不启动 decoder。**已从 `m_total<1024` 改为 `m1<1024 && m2<1024`**。

### 4. EVAL 密封度量门禁（19/24, undetected 0, 披露/效率分解，已删 per-source 6/8）

- **门禁**：`exact_full == (exact_u1 && exact_l2) ≥19/24 overall (79.17%)`，`undetected_full_tag == count(syndrome_ok && tag_ok_full && !exact_full) ==0`，`所有 exact 帧 tag_ok_full==True`，`disclosure ==5*(m1+m2)+64` 双校验，`efficiency = disclosure / (1024*CE_full)` 报告。**已删除 per-source 6/8，仅 overall 19/24**。
- **密封**：`EVAL` 不参与 `P/λ/CE/m` 任何选择；`EVAL` 仅一度量，不回灌。

### 5. 本轮交付边界（四工件 + 只读调查 + 冻结注册表 + spike + 终态机 + 独立 review packet）

- 产出 `proposal/design/tasks/specs` 四工件 + `v66_data_registry.json`（单 session 72） + `v66_spike_summary.json`（CE/m/rank/nested/disclosure/constructibility 已回填无 TBD） + `V66_ADAPTIVE_REPORT.md` 占位 + review packet；**禁** `decode_row_layered_fftqspa / construct_*` 调用（`rg "decode_" 0 hits` 守卫）、禁 `run_01`、禁跨方法比较、禁改 `src/` baseline、禁转 qualification、禁自行 `ACCEPT`。**四工件 + registry + spike + 脚本结果单独提交推送，返回新 Plan SHA**。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_H*` decoder（脚本内 `rg "decode_" 0 hits`）；不改 `H1/Lane C/m2/H_inc/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；不新增矩阵。
- 不读密封 `EVAL` 的任何 `H/CE/NLL/MAP` 统计作 `P/m/阈值` 选择，违则 `EVIDENCE_INVALID`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；不以 `EVAL` 网格调 `+8` 档。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification。
- 不改写/覆盖 `V13/V48–V64` 任何已有输出与终态（只读）；可复用旧数据仅作 `development_replay` 显式标记。
- **不以 per-source 6/8 作门禁（已删）**；不以 `V25 H` 作新域门禁，门禁用 `VAL CE`。
- 不创建正式 `.../v66_*/run_01` decoder 执行；正式 `EVAL` decoder 需另起 `OpenSpec` + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单 session 内验证，不作跨方法 rank。

## Scope

1. **单 session 单源冻结分段（可复用旧数据但 development_replay 标记）**：`CAL 24 + VAL 24 + EVAL 24 =72 blocks overall` 全部 `20260123_1M_600k_0dB`，`BLOCK 4×256`, `FRAME 256 pairs`, `frame_id∈[0,F_s-1]`，三段零重叠且与 `V13/V48..V64` 零重叠（键 `(source,session,frame)`），单 `session_id` provenance，不跨 session 拼接，少于 72 或任段 !=24 则 `DATA_NOT_READY`，禁止事后换段；`v66_data_registry.json` authoritative（单源 72）。
2. **冻结主体零改**：`n1024, GF32 poly37, H1 16×1024 rank16, Lane C ordinal-2 s38310x m2 184（单源）, H_inc Δ8 家族, U=32*U1+U2 F03 5+5 natural, decoder 90/1.0, full-tag canonical` 全只读。
3. **单一重估 + VAL CE 门禁**：`CAL C_ab → P(U1|B)/P(U2|U1B)` → `VAL CE1/CE2` → `m_raw ceil` → **同家族 `+8` 调整** → `m1<1024 && m2<1024 满秩嵌套披露 constructibility` decoder-free 校验 → 否则 `RATE_NOT_FEASIBLE` / `MATRIX_NOT_CONSTRUCTIBLE`。
4. **EVAL 密封门禁**：`exact_full 19/24 overall, undetected 0, tag_ok_full, disclosure, efficiency` 冻结判定，仅一度量（**已删 per-source**）。
5. **终态五选一**：`EVIDENCE_INVALID > DATA_NOT_READY > RATE_NOT_FEASIBLE/MATRIX_NOT_CONSTRUCTIBLE > ADAPTIVE_EVAL_FAIL > ADAPTIVE_EVAL_PASS`（`EVAL` 未执行时前三态可直接判定）。
6. **脚本与报告交付（DEVELOPMENT_BENCHMARK）**：`scripts/v66_data_readiness.py`（只读调查+注册表） + `scripts/v66_spike.py`（decoder-free `C_ab/P/CE/m_raw/m_family` + 满秩嵌套校验+constructibility）`rg "decode_" 0 hits`, `py_compile PASS`，输出 `v66_data_registry.json + v66_spike_summary.json + V66_ADAPTIVE_REPORT.md` 占位 + 控制台摘要，未创建 `run_01`，**spike 已回填 CE1/CE2/raw/aligned m1/m2 rank nested disclosure，无 TBD**。
7. **独立 review packet**：`review/V66_REVIEW_PACKET.md` 预留，记录 `HEAD/新 Plan SHA, data 84d62779, zero_overlap, development_replay, m_raw/m_family, rank/nested, DATA_NOT_READY/RATE_NOT_FEASIBLE/MATRIX_NOT_CONSTRUCTIBLE` 复核清单，不自行 `ACCEPT`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v66-single-segment-adaptive-nbldpc/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v66_data_readiness.py` + `scripts/v66_spike.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`) + 冻结注册表 `v66_data_registry.json` (单 session 20260123_1M_600k_0dB CAL24+VAL24+EVAL24) + `v66_spike_summary.json` (CE1/CE2/raw/aligned m1/m2 rank nested disclosure constructibility 已回填) + `V66_ADAPTIVE_REPORT.md` 占位 + `review/V66_REVIEW_PACKET.md` 占位 + spike 控制台摘要。
- **只读依赖**：`v55_intake_20260828` 单 session 旧数据（复用时 `development_replay=true`） + `v55_stratified_registry_candidate.json / v64_fresh_registry`（零重叠校验，键含 session） + `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet` + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V65` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 EVAL decoder**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，`HEAD 832e5394bb366927c779414ee5a08427bd740a2d` + `branch formal-ir-mainline` + `data 84d62779` + `predecessor V64 80c35647/6c7b00a9 22/24 PASS` 已绑定，显式声明 decoder-free、零 decoder、单 session 单源 72、development_replay、冻结主体、仅 P 重估 + VAL CE + 同家族 +8、不依 EVAL 调参、**m1<1024 && m2<1024** 满秩嵌套披露 constructibility 先验、EVAL 19/24 undetected0（**无 per-source**）已声明，**新 Plan SHA 已推送**。
- [ ] **单 session 单源冻结可复现（72 overall =24+24+24，单源）**：`CAL 24 blocks (96 frames 24576 pairs) + VAL 24 + EVAL 24 =72` 全部 `20260123_1M_600k_0dB`，`BLOCK 4×256`, `frame 256`，已 `assert` 三段零重叠（`CAL_key∩VAL_key==∅`, `CAL∪VAL_key∩EVAL_key==∅`, `CAL∪VAL∪EVAL_key ∩ (V13∪V48..V64)_key==∅`，键=`(source,session_id,frame_id)`，单 `session_id`），`F_s=2130 K=532 ≥72` 已验，少 72 或任段 ≠24 → `DATA_NOT_READY`，注册表已落盘，标记 `development_replay=true`。
- [ ] **冻结主体零改已验**：`U=32*U1+U2, GF32 poly37, H1 16×1024 rank16, Lane C ordinal-2 s38310x m2 184（单源）, H_inc Δ8 家族, decoder 90/1.0, full-tag canonical` 全只读，`git diff -- src/ ==0` 且未引 MET。
- [ ] **单一重估 + VAL CE + 同家族 +8 + 先验校验可复现（decoder-free，无 TBD）**：`CAL C_ab → P(U1|B)/P(U2|U1B) → VAL CE1/CE2/CE_full 链式 |CE_full-CE1-CE2|<1e-9 → m_raw ceil → m_family ceil_to_+8 → m1<1024 && m2<1024 && rank==m && nested && disclosure==5*(m1+m2)+64 && constructible` 已算，`m_raw/aligned` 已回填，`m_raw` 未 cap，`m_family` 显式，若族不能覆盖则 `MATRIX_NOT_CONSTRUCTIBLE`，`EVAL` 未参与，不扩网格，禁第二 estimator。
- [ ] **报告完整（不读 EVAL）**：`Cal/Val pairs/frames/size, CE1/CE2/CE_full + chain_delta, m1_raw/m2_raw/m_total_raw, m1/m2/m_total aligned, Δm, rank/nested/disclosure/constructibility` 已回填无 TBD，`EVAL 仅 identity 密封` 已验，`m` 公式 `ceil(1.3*1024*CE/5)` 未 cap 伪装已验。
- [ ] **EVAL 门禁冻结（未执行但判定框架已验，已删 per-source）**：`exact_full ≥19/24 overall && undetected_full_tag==0 && all exact→tag_ok_full && disclosure/efficiency` 已显式，五态 `EVIDENCE_INVALID > DATA_NOT_READY > RATE_NOT_FEASIBLE/MATRIX_NOT_CONSTRUCTIBLE > ADAPTIVE_EVAL_FAIL > ADAPTIVE_EVAL_PASS` 优先级互斥已落盘，且 `EVAL` 触发前 `RATE_NOT_FEASIBLE` 可直接阻断。
- [ ] `scripts/v66_data_readiness.py` 与 `scripts/v66_spike.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS），输出 `v66_data_registry.json + v66_spike_summary.json + V66_ADAPTIVE_REPORT.md` 占位 + 控制台摘要，**已回填无 TBD，未创建 run_01，未读 EVAL，未改码参，development_replay 已标记**。
- [ ] 已停留在 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v66_*/run_01`，不比较，不碰 `V48-V65` 块外，未转 qualification，**四工件+registry+spike 已单独提交推送，返回新 Plan SHA，等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile/EVAL 未读/m_raw 显式/rank_nested/constructibility/单 session 72/development_replay`），返回 `Plan SHA / 冻结段数量 / raw m1/m2 / 可构造性 / 下一步` 等待 `PLAN_ACCEPT`。

## Tasks

见 `tasks.md`（Phase A 单 session 72 单源冻结+只读调查+注册表；Phase B 冻结主体 U=32*U1+U2 Lane C Δ8；Phase C P重估+VAL CE+raw m+同家族 +8 decoder-free 校验 **m1<1024 && m2<1024** 满秩嵌套 constructibility；Phase D EVAL 密封门禁 19/24 undetected0（无 per-source）；Phase E 五态机；Phase F spike 回填无 TBD +报告；Phase G 独立 review packet + 单独提交推送新 Plan SHA）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` 为 new-session 两会话兼容性（新数据域）；`V66-ADAPT` 为**单 session 单源自适应**分支，当前 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`（仅 decoder-free 预冻结，单 session 20260123_1M_600k_0dB 72，可复用旧单 session 但标记 development_replay，不实现 runner，不执行 decoder，不创建 `run_01`，不比较，**m1/m2 分别 <1024**，EVAL 19/24 undetected0 无 per-source）；`V66` 本身不直接进入 qualification；正式 `EVAL` decoder 需另起 `EXECUTE_AUTH`。
