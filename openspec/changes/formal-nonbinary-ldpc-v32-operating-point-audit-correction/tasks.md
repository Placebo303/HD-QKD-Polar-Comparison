# Tasks: formal-nonbinary-ldpc-v32-operating-point-audit-correction

> Do NOT mark any task complete without evidence (command output, file hash, log
> line, or reviewer report)。A11/A12 保持未勾选直到 Codex 主控审查。
> 锚点：`proposal.md`；语义/设计细节：`design.md` §1–§12；normative SHALLs：
> `specs/formal-nonbinary-ldpc-v32-operating-point-audit-correction/spec.md`。
> 数值冻结值以 proposal/design 为准，本文件集中复述，不得改写。

## Allowed New Files

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit_correction.py`
  — 单一只读 correction verifier CLI（子命令 d0/d1/d2/d3/all + `--runner` 注入 + collision STOP）
- `comparison_bench/tests/test_nonbinary_v32_operating_point_audit_correction.py`
  — T0/T1/T2 测试套件（T3 smoke 含在内）
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/*`
  — 恰八件：`audit_manifest.json`、`d0_failure_signature.json`、`d1_support_mismatch.json`、
  `d2_dual_law_feasibility.json`、`d3_next_question.json`、`corrected_branch_decision.json`、
  `readonly_review.json`、`operator_handoff.md`（多一件少一件都算违规）
- `workspace/nbldpc_v32_operating_point_audit_correction/<fresh-id>/*` — scratch/test roots only
- `workspace/nb_polar_feasibility_concept/README.md` — NB-Polar feasibility concept note 草案（draft only，不执行）
- `workspace/` 下 next-phase（V33 rate-aligned empirical-channel ensemble DE）OpenSpec 候选草案文件
  （draft only；不入 `openspec/changes/`；不注册变更、不执行）

其余新文件需主控批准。

## Forbidden（MUST NOT be edited/executed/created at any stage）

No-run list:
- 运行 DE / decoder / graph builder / finite-control / raw-data pipeline /
  任何 `longrun_*` / `minrerun_*` / `routeA_*`；触碰 `../HD-QKD_Polar_Release/**`。

Old-root overwrite protection（每个根 byte-identical before/during/after）:
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/**`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/**`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_02/**`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/**`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/**`
- archive 中所有历史 evidence（`openspec/changes/archive/**`）
- frozen baseline：`src/**`、`experiments/**`、`tools/**`

报告历史原文:
- 修改旧 V31/V32 报告历史原文禁止（旧审计 run_01 十件仅引用/标注，绝不回改）。

本轮禁改 docs/memory（A11/A12 才涉及，且须 Codex ACCEPT 后）:
- `AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md`、V32 final report
  （`docs/nbldpc-v32-main-review-verdict-20260822.md`）、archive state。

Git/worktree 纪律:
- `AGENTS.md` 不 stage / 不 revert / 不覆盖（用户改动保留在 worktree）；
- 不清理用户 untracked 文件；
- 无 `git reset` / `git checkout` / `git clean` / `git push`。

措辞禁令:
- qualification / promotion / deployment 措辞在任何本变更产物中出现即违规。

其他:
- 除唯一新根 `…_v2/run_01/` 外不得写任何既有 output root；run root 已存在 ⇒ STOP collision，
  禁自动 `run_02`。

## Frozen Constants（集中复述，跨 proposal/design/spec 一致）

- **旧审计生命周期四标签**（verbatim 写入 v2 `audit_manifest.json` 的 `lifecycle_note`）：
  `post_hoc_exploratory_only` / `not_formal_pre_registered_gate` / `numerical_outputs_retained` /
  `scientific_terminal_superseded_pending_correction`。
- **support-miss 三源参考值**（旧审计 v1 对照基准，v2 独立重算，差异如实列 delta，绝不静默对齐、
  绝不回改旧文件）：旧 `q_mass_on_p_zero_cells` ≈ **0.239468 / 0.254127 / 0.255348**
  （1M / 1p5M / 2M）。
- **命名三件套**（C4）：`full_expected_nll` = 字符串字面值 `"infinity"`（附正质量落在 P=0 格推导行）；
  `conditional_finite_support_mean`（仅非命中样本条件统计）；
  `truncated_common_support_cross_entropy`（共同支撑截断交叉熵）；
  三者禁止称 full NLL / full cross entropy。
- **Q_B1 律（Law B）**：H_Q(B|A) = h2(raw_ser) + raw_ser·log2(1023) ≈
  **3.1921 / 3.3626 / 3.3773** bits/symbol；required_bits = n × H_Q @ n=1024 ≈
  **3268.7 / 3443.3 / 3458.4** bits vs pure syndrome total **{1000, 1030, 1040}** bits
  （gap 强烈为负 ⇒ information-theoretically infeasible at current allocation）。
- **V31 层率表**（verbatim 写入 d3 输出）：L1 **0.984375 ×3 源**；L2 **0.8203125 / 0.814453125 / 0.8125**；
  **m1=16**；**m2 ∈ {184, 190, 192}**；`leak_total_bits` verbatim **{1064, 1094, 1104}**
  （与 pure syndrome 定义分开引用，不合并）。
- **MC 参数**（manifest 预冻结，禁 tuning）：seed=**20260822**；n_samples=**100000**；
  quantiles=**[0.05, 0.5, 0.95]**。
- **raw_ser 三源值**（verbatim）：1M `0.239779296875`；1p5M `0.2544695292735815`；
  2M `0.2557409550754458`。
- **D3 问题原文**（逐字出现在 `d3_next_question.json` 的 question 字段）：
  「在 V25 empirical joint P(A,B)、F03/A02 分配和 V31 实际层率下，对应 ensemble DE
  是否在三源、两层全部收敛？」红线：DE 是 ensemble/channel 分析，**不是 fixed-QC DE**；
  `not_fixed_packet_de=true` 必须写入。
- **终态优先级**（机械、严格序）：
  `audit_evidence_inconsistent` > `audit_verifier_blocked` >
  `audit_corrected_rate_aligned_de_required`。
- **13 条件清单**（candidate = corrected 当且仅当全部满足；编号 C01–C13，design §9）：
  - C01. D0 全量重算记录与谓词一致（P-i/P-ii/P-iii 通过或 mismatch 已如实标注）；
  - C02. B2 sentinel 语义正确（=1024 not_run，排除出轨迹/发散统计）；
  - C03. B3/B4 improve-but-no-syndrome 表述正确（divergent 字样不得用于 B3/B4）；
  - C04. D1 零支撑质量逐源解析重算（q_mass_on_p_zero_cells 三源齐备）；
  - C05. 完整 NLL 标记为 infinity（字符串字面值 + 推导行）；
  - C06. conditional/truncated 指标命名正确（无 full NLL / cross entropy 误用）；
  - C07. D2 双 law 并存未合并（empirical_P_budget 与 original_Q_B1_budget 平级两个对象）；
  - C08. empirical-P 仅标 nominal information budget feasible（conclusion_scope 逐字）；
  - C09. Q_B1 标 information-theoretically infeasible at current allocation（逐字）；
  - C10. D3 已改为 exact-V31-rate empirical-P ensemble DE 问题（question 逐字 + 层率表）；
  - C11. 全程无 DE / decoder 被调用（静态 + 运行期证据）；
  - C12. 旧证据根字节不变（V32 bridge run_01、旧审计 run_01、V25/V26/V31 各根前后哈希一致）；
  - C13. reviewer 独立复算通过（readonly_review.json 存在且 blocking=false）。
  任一不满足 → 按优先级降级为 evidence_inconsistent 或 blocked，理由逐条记录。
- **终态禁令七串**（不得作为 corrected_branch_decision 或任何 v2 报告的结论出现；
  T1/T2 机械扫描）：
  `finite_graph_decoder_mismatch`；`QC graph confirmed failure`；`decoder confirmed failure`；
  `NB-Polar preferred`；`qualification-ready`；`promotion-ready`；`deployment-ready`。
  （注：`finite_graph_decoder_mismatch` 仅允许以被否定的历史对象身份出现在 §1/lifecycle 语境。）
- **Run rules**：唯一根 `…_v2/run_01`；执行序 manifest freeze → d0 → d1 → d2 → d3 →
  corrected_branch_decision；readonly_review.json（A8）与 operator_handoff.md（A10）事后补入，
  凑齐恰八件。

## Role Isolation（frozen）

- **Planner**：A1–A2 文档（清点 + OpenSpec 作者ship与一致性自检）。不实现。
- **Coder-fast**：A4–A6 实现+测试；A7 执行。不得标记 ACCEPT、不得重定义需求、
  不得写 `readonly_review.json`。
- **Reviewer-go**：两轮独立 —— R1 = A3 规格审查；R2 = A8 独立重算并写 readonly_review.json。
  R2 是独立 reviewer 且不得是实现者或执行者。
- **Main（orchestrator/user）**：所有 ACCEPT 门与 A9 C01–C13 矩阵裁决；
  Codex 主控持有最终科学 ACCEPT/REJECT。
- **Closeout agent**：A10 handoff 组装（candidate-only）。
- 执行者不得兼任最终 reviewer；所有 ACCEPT 门由 main 持有；candidate 不得自我升级为 ACCEPT。

---

### A1 — 只读清点和输入绑定（planner）

- [x] A1.1 记录 git branch / HEAD / status / `ls-files -m`；七类输入路径（design §2 R1–R7）
  存在性与 SHA256 清单；确认 `AGENTS.md` 处于 modified 状态（用户改动，保留、永不 stage）。
  — Evidence: 清点输出（branch=main、HEAD=dda3503e、AGENTS.md +18/-0 modified unstaged；
  三旧根存在：bridge run_01=13 文件 / opaudit run_01=10 文件 / v31 run_01=16 文件）。
- **Done when**: 七行绑定零缺失；全程零写操作。 ✓

### A2 — OpenSpec 完整冻结（planner）

- [x] A2.1 四件套齐备且一致（proposal / design / specs / tasks）：交付物八件、绑定 7 行、
  冻结数值（support-miss 参考值、命名三件套、Q_B1 熵与 required、层率表、m1/m2/leak_total_bits、
  MC 参数、raw_ser、D3 问题原文、终态优先级 + 13 条件、禁令七串）跨文件逐项相同。
  — Evidence: 分步写入（design/tasks/spec 各单文件任务）+ planner 自检表（数值逐位对照旧 run_01）
  + 主控 grep 一致性抽查。
- **Done when**: main 确认冻结；未写任何生产代码；未执行任何分析。 ✓

### A3 — Review Round R1: Specification Freeze Review（reviewer-go，独立，pre-execution）

- [x] A3.1 reviewer-go 只读审查四件套：一致性 / 科学语义（§3 C1–C6）/ Forbidden 纯度 /
  绑定数值磁盘核实（对照 R1–R7 实盘）。— Evidence: R1 报告分项 PASS/FAIL（仅 1 项阻塞：
  design §8 selected_branch 枚举未用冻结终态名）。主控修复三处（selected_branch 三值统一 /
  R7 stage-0 allocation 过滤注记 / tasks 补四标签字面量），按 reviewer 预授权完成 B2 范围
  复核（grep 零残留、四文件终态名与四标签齐备）→ **ACCEPT_FREEZE**（2026-08-22，main 记录）。
  实现授权随之生效（A4 起动）。
- **Done when**: R1 ACCEPT_FREEZE。**强制停止点：freeze acceptance 前不得开始实现。** ✓

### A4 — Correction Verifier 实现（coder-fast）

- [x] A4.1 实现 CLI（design §2–§8）：stage-0 七绑定校验（存在性 + 字面值 + SHA256）；
  子命令 d0/d1/d2/d3/all + `--runner` 注入；collision STOP（run root 已存在即 exit 非 0）；
  manifest 先冻后算（MC 参数/bin 边界/lifecycle_note 四标签/no_de_run/no_decoder_run/
  old_roots_read_only/git HEAD/implementation identity）；谓词引擎 P-i..P-iii（mismatch 如实记录）；
  B2 sentinel 排除；D1 六指标 + 旧值对照列 + naming_rules；D2 双 law 分开输出；
  D3 问题/层率表/not_fixed_packet_de；机械终态选择（优先级 + 13 条件 checklist）；
  区分 exit code（ok/collision/blocked/evidence-inconsistent/write-guard）。
  测试套件骨架同批创建。
  **偏差记录**：「测试套件骨架同批创建」条款经主控指令调整为 A5 任务执行（偏差已记录，
  本任务仅交付恰一个实现文件）。
  — Evidence: `python -m py_compile comparison_bench/src/comparison_bench/cli/
  run_nonbinary_v32_operating_point_audit_correction.py` exit 0；文件清单 = 恰一文件
  （CLI 本体，1301 行）；静态 grep：DE 采样调用 0 / decoder 入口 0（"decode" 字符串命中
  均为冻结 schema 字段名 terminal_decoder_status、l1_decoder_status_verbatim、禁令七串
  常量与 docstring 措辞）/ ttbin 0 / graph-builder 标记 0；import 清单 = argparse/hashlib/
  importlib/json/math/subprocess(git HEAD)/sys/datetime/pathlib + numpy（stdlib+numpy 白名单）；
  另附合成 fixture + fake runner 端到端 smoke（temp scratch，非真实输入、非 canonical root）：
  `all` exit 0 六件产出、D0 谓词全过且 B2 sentinel=60 单列、D1 analytic q_mass>0 →
  full_expected_nll="infinity"、D2 Law-A 交叉核对 diff<1e-9 且 Law-B gap =
  -2268.7/-2413.3/-2418.4 bits（与冻结值 -2269/-2413/-2418 一致）、D3 question 逐字、
  collision replay exit 2、C13 pending ⇒ 终态 audit_verifier_blocked（决策时点诚实值）。
- **Done when**: CLI 编译通过、静态检查干净；尚未对真实输入执行。

### A5 — Tests T0/T1（coder-fast）

- [x] A5.1 按 design §11 完成 T0（结构/tiny math/infinity 语义/rates 断言/import 白名单/
  same-root 拒绝）与 ≥12 项 T1（分类/sentinel/命名/双 law/question wording/overwrite guard/
  禁令七串扫描等）；fresh `workspace/<fresh-id>/` root + `pytest -p no:cacheprovider`。
  — Evidence: pytest 计数行（T0 8 passed；T1 16 passed）—
  `python -m pytest comparison_bench/tests/test_nonbinary_v32_operating_point_audit_correction.py
  -k t0/-k t1 -q -p no:cacheprovider --basetemp workspace/opaudit_corr_t0_a1b2c3/t{0,1}`；
  scoped git status 核对零 canonical 路径改动（2026-08-23）。
- **Done when**: T0+T1 全过；canonical 路径零改动（scoped `git status` 核对）。 ✓

### A6 — Fake T2 + Strict Replay（coder-fast）

- [x] A6.1 fake fixture 完整 correction 流程（合成 per_block + tiny channel_counts，
  显式 fake runner，绝不触生产 runner）；独立 recount 复现 headline 数字；tamper 系列
  （terminal/summary/count drift/source/rate/law substitution/deep semantic）；strict replay
  （同输入重跑输出一致，时间戳字段白名单除外）；collision 端到端。— Evidence: pytest 计数行
  （T2 13 passed；全套件单文件 37 passed in 14.01s）— `-k t2 --basetemp
  workspace/opaudit_corr_t0_a1b2c3/t2`（2026-08-23）。
- **Done when**: T2 PASS；delta-only 报告交付 main，请求 A7 授权。
  **强制停止点：main 未授权前不得对真实输入执行。** ✓

### A7 — 真实输入只读 Correction 执行一次（coder-fast，执行身份）

- [x] A7.1 前置断言 run root 不存在（存在 ⇒ STOP collision）；按固定执行序 `all` 一次，
  生成 v2 run_01 六件（`audit_manifest.json` / `d0_failure_signature.json` /
  `d1_support_mismatch.json` / `d2_dual_law_feasibility.json` / `d3_next_question.json` /
  `corrected_branch_decision.json`）；输入哈希前后对照（含全部 protected old roots）。
  — Evidence: exit 0；六件恰齐；pre/post SHA256 全一致（per_block/channel_counts/channel_summary/
  V31 RUN_MANIFEST/candidate_terminal + 旧审计十件）；目录计数 bridge=13 / opaudit_v1=10 不变。
- **Done when**: 六件产出，或白名单 STOP 发生且证据不可变保留、终态按优先级路由。 ✓

### A8 — 独立 Reviewer 重算与 T3（reviewer-go R2，独立于实现者与执行者）

- [x] A8.1 从原始持久化记录独立重算 headline（尽量不走 CLI 代码路径），与六件持久化输出
  逐一比对；按优先级 + C01–C13 重derive 终态；核实全部 protected roots 前后哈希一致。
  — Evidence: R2 W1–W3 全 PASS（D0 逐位相等 tol 1e-9；D1 q_mass/MC/truncated bit-exact，
  MC 随机流单流复现 hits 24046/25469/25518；Law A 对 V31 漂移 ≤2e-15；Law B gap
  −2268.74/−2413.33/−2418.36 bits）；W6 29 绑定 SHA256 drift=[]。
- [x] A8.2 T3 只读回归（最小必要集合：真实输入存在性/关键身份；不调 DE/decoder；
  canonical/frozen roots 快照对比；准确措辞 "T3 smoke: PASS; full frozen T3 regression:
  not in scope."）。— Evidence: W8 stage-0 等价身份断言 7/7。
- [x] A8.3 将结论写入 `readonly_review.json` 入 run_01（该文件是 reviewer 在本变更中
  唯一允许写的文件；blocking=false 时 C13 成立）。— Evidence: 11751 字节，JSON 校验通过，
  blocking_findings 空。run_01 七件齐备。
- **Done when**: R2 verdict 发布；run_01 此时七件齐备（尚缺 operator_handoff.md）。 ✓
  **R2_VERDICT: ACCEPT_CANDIDATE_EVIDENCE**

### A9 — 主控候选 C01–Cxx 矩阵（main）

- [x] A9.1 main 按 AC-D0 / AC-D1 / AC-D2 / AC-D3 / AC-L / AC-N / AC-R / AC-T 八组对
  C01–C13 逐项 ACCEPT/REJECT（引用证据 ID：pytest 日志行、哈希日志行、readonly_review 条目等）；
  严格按优先级产出候选终态判定；任一 REJECT 则降级并逐条记录理由。— Evidence: 矩阵表
  （每条件 ✓/✗ + 引用证据 ID）。主控矩阵（2026-08-22）：C01✓(R2-W1) C02✓(R2-W1 P-ii)
  C03✓(R2-W1 P-iii+W4) C04✓(R2-W2 解析逐位) C05✓(R2-W2 infinity×3+推导) C06✓(R2-W2/W4
  命名字段与禁令零命中) C07✓(R2-W3 双 law 平级) C08✓(R2-W3 conclusion_scope 逐字)
  C09✓(R2-W3 强负 gap) C10✓(R2-W4 问题原文+层率表+not_fixed_packet_de) C11✓(manifest
  三 flag+静态检查+no_DE_executed=true) C12✓(R2-W6 29 绑定 drift=[]+E3 pre/post) 
  C13✓(readonly_review.json blocking=false，11751 字节)。13×✓ ⇒ 按冻结优先级候选终态 =
  **audit_corrected_rate_aligned_de_required**（main-adjudication 层级，仍 candidate_only
  等 Codex ACCEPT；执行时点 corrected_branch_decision.json 的 audit_verifier_blocked 快照
  系 C13 当时未满足的诚实记录，予以保留不改写）。
- **Done when**: 候选终态判定记录（预期 corrected ⇔ 13×✓）。 ✓

### A10 — 候选 Handoff（operator closeout）

- [x] A10.1 补写 `operator_handoff.md` 入 run_01（changed files / commands / results /
  evidence root / dirty worktree scope / frozen roots diff / known limitations /
  exact next authorization boundary），恰八件齐备。— Evidence: 八件清单精确匹配 + 文件存在
  （七件既有 + operator_handoff.md，目录计数恰 8，2026-08-23 核对）。
- [x] A10.2 Commit 3 落库（见「Git 提交分离」）。— Evidence: Commit 3
  `evidence(nbldpc-v32-audit-correction): candidate v2 evidence and independent review`
  的 `git log` 行（本文件随 Commit 3 入库后可核）。
- **Done when**: handoff 交付 main；change 返回 candidate_only。 ✓

### A11 — Codex ACCEPT 后 Durable Docs（保持未勾选直到 Codex 主控审查）

- [ ] A11.1 `docs/decision-log.md` 新增条目（Decision / Reason / Consequence 按主控给定文本）。
  — Evidence: (pending Codex)。
- [ ] A11.2 V32 final report addendum（措辞按主控指令）。— Evidence: (pending Codex)。
- [ ] A11.3 memory triage 三层结论（经 memory agent）。— Evidence: (pending Codex)。
- **Done when**: (pending Codex) — Codex 给出 ACCEPT/REJECT 前必须保持未勾选。

### A12 — Archive / Commit Decision（保持未勾选直到 Codex 主控审查）

- [ ] A12.1 仅在 Codex 主控 ACCEPT/REJECT 后：裁决本变更可归档性，若批准执行 `/opsx-archive`。
  — Evidence: (pending Codex)。
- **Done when**: (pending Codex) — 同上，保持未勾选。

---

## Candidate Fix 2026-08-23 — verifier semantic guards（candidate fix，不得视为 ACCEPT）

主控裁决（2026-08-23）：科学候选证据可接受，变更整体暂 REJECT；唯一阻塞 =
design §11 / spec AC-D1 的 infinity 语义未按 iff 条件实现。本轮修复（任务 B/C/D）
仅改动 CLI/tests/tasks.md 三文件；旧 v2 run_01 八件证据字节不变（pre/post SHA256 全同）。

- [x] F-B1 infinity 语义修正：`run_d1` 改为条件式——q_mass_on_p_zero_cells > 0 ⇒
  `full_expected_nll="infinity"`（保留推导行）；== 0 ⇒ 输出 JSON-safe 有限解析值
  （数值上等于共同支撑期望，零质量时与 truncated CE 恒等），附
  `ZERO_MASS_FULL_NLL_DERIVATION`。`NAMING_RULES.full_expected_nll` 同步改为 iff
  条件语义；C05 checklist 改为 iff 一致性判定形式。— Evidence: T0 uniform-P 玩具
  两方向断言（零质量 ⇒ 有限 20.0 且 ≠ "infinity"；正质量 ⇒ "infinity"）；全量 47 passed。
- [x] F-C1 run-root 护栏：`validate_run_root()` 最小显式路径检查——拒绝 repo root、
  results 根、diagnostics 根、outputs_comparison 根等过宽路径，五个 protected old root
  本身及其任意子路径、archive；仅允许冻结 v2 默认根，或显式 fake runner 时 workspace
  下的测试根（workspace 根本身仍拒）。cli_main 两分支入口接线。— Evidence: T1
  guardrail 测试（protected self/subpath/broad/workspace-root/non-fake 全拒 +
  default/fake-fresh 允许）。
- [x] F-D1 verify_manifest 字段级强化：schema、lifecycle_note 四标签、no_de_run /
  no_decoder_run / old_roots_read_only 必须为 true、implementation_identity 结构完整、
  output_files_expected_eight 清单核对、frozen 块内容与模块常量相等（防"改值+重算
  digest"绕过）、freeze_digest 原有检查保留。Git HEAD 与 implementation identity 遵守
  时间绑定：仅做格式/存在性校验，绝不与当前 HEAD 或当前 CLI 文件比对。— Evidence:
  tamper 参数化新增 8 例全过 + time-binding 测试（HEAD 漂移为另一合法哈希后流程
  继续至 stage collision，证明无 current-HEAD 等值检查）。
- [x] F-T 全量验证：T0=8 / T1=26 / T2=13 / 全量 **47 passed**（fresh basetemp
  workspace/v32_correction_fix_20260822a/{t0,t1,t2,all}）；py_compile exit 0；
  旧八件证据 pre/post SHA256 逐字节一致；nbldpc_v32_operating_point_audit_v2/ 下
  无新增目录。
- [ ] F-G1 Codex 主控复核本 candidate fix（保持未勾选直到审查）。

状态：candidate fix 完成 —— 等待 Codex 主控 ACCEPT/REJECT；未运行 DE，未运行 decoder，
未启动 successor，未触碰任何旧证据。

---

## Git 提交分离（三条；禁止 amend/rebase 隐藏顺序）

1. **Commit 1** `spec(nbldpc-v32-audit-correction): freeze correction OpenSpec` —
   scope：本 change 目录四件套。只有完整 OpenSpec 经 reviewer ACCEPT（A3 R1 ACCEPT_FREEZE）
   后才进实现。
2. **Commit 2** `impl(nbldpc-v32-audit-correction): read-only operating-point audit
   correction verifier` — scope：CLI + test 文件（A6 后）。
3. **Commit 3** `evidence(nbldpc-v32-audit-correction): candidate v2 evidence and
   independent review` — scope：v2 run_01 八件（+ tracked workspace 草案若仓库惯例跟踪）。

规则：显式路径 staging（`git add <path>`，禁 `git add -A`）；`AGENTS.md` 用户改动永不 stage；
legacy untracked 输出目录永不 stage；无 `git reset` / `git checkout` / `git clean` / `git push`。

## 强制停止点（mandatory stop-and-wait）

1. OpenSpec 冻结（A3 R1 ACCEPT_FREEZE + main 确认）⇒ 之后才可实现；
2. T0–T3 全过 + main 授权（A6→A7 门）⇒ 之后才可对真实输入执行；
3. v2 run_01 → independent reviewer → candidate terminal 持久化 → handoff → DE draft only →
   NB-Polar concept note only → 无 DE/decoder → 无 push → memory/archive 未动 ⇒ 立即停止；
4. 任何 design §12 STOP-trigger 触发：halt、保留不可变证据、上报（失败命令 / 确切错误 /
   已试补救 / 所需单一决策）。

## Final Return Statement（逐字，closeout 必附）

> candidate_only，等待 Codex 主控 ACCEPT/REJECT；未运行 DE，未运行 decoder，未启动 successor。

---

**Do not mark tasks complete without evidence. Each checkbox requires a cited command
output, file hash, log line, or reviewer report.**
