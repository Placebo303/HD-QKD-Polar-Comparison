# V72P2D2-R1 最小恢复 Addendum（PREP-FIX ONLY / CANDIDATE）

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- HEAD（本 addendum 基线）: `e2b028ffb68e74f4e3d19299e9dd1394b876eb9a`
- Base: `e094f7e548380db4bfcbc1fe73472e670c32379a`
- Accepted plan SHA: `4592bdad357a02f8f08a880ca0036beaed3ee900`
- Failed implementation SHA: `580471cf`（`RESULT_SUMMARY.md` / `cycle_state.yaml: BLOCKED_PREP_FAILED`）
- Cycle: `V72P2D2-TRIAGE`，R1 恢复子轮（不开启新 cycle）
- Kind: `ADDENDUM_R1_CANDIDATE` — 仅关闭 prep-time NameError，不做科学变更
- Lifecycle: `ADDENDUM_CANDIDATE / IMPLEMENTATION_NOT_STARTED / EXECUTE_NOT_AUTHORIZED`
- Formal execution: `false` | Real execution authorized by this file: `false`

> 本文件是本轮唯一允许新增的文件。禁止改写原四工件原文（`openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/` 下 `proposal.md` / `design.md` / `tasks.md` / `specs/spec.md`），禁止改写 `docs/research_cycles/V72P2D2-TRIAGE/` 下既有 `PLAN_CANDIDATE.md` / `PLAN_REVIEW_VERDICT.md` / `IMPLEMENTATION_REVIEW.md` / `RESULT_SUMMARY.md` / `cycle_state.yaml`，禁止覆盖原 `PREP_FAILED` 四文件输出。本 addendum 自身为 CANDIDATE，不授权实现与执行；真实执行需 addendum 接受 + 实现复审 + Pre-EXECUTE 全 PASS 后另行授权。

## Goal

V72P2D2 原执行以 `invocation_status=PREP_FAILED / prep_status=FAILED / fatal_error=NameError: name 'Q' is not defined` 停止，三新臂 `L/I/P=NOT_ATTEMPTED`、0 sweep、0 checkpoint metrics，未进入 decoder arm（见 `RESULT_SUMMARY.md` §Outcome 与预算节）。R1 只做最小恢复：允许修复 prep-time `NameError` 及同类静态未定义名，允许加一个 fake 端到端 preparation test，使同一科学计划能在新 additive 目录下获得一次合规重走 prep 的机会，不改变任何科学结论与路由裁决。

## Non-Goals

- 不重写原计划、不调科学参数/数据/三臂/预算/checkpoint/prior/interleaver。
- 不做九块确认、FER、SKR、信息极限、方法定级、跨 session 推广、图因果、M2 优胜断言。
- 不修复 `run_incremental_decoder` stale-return、不碰 adapter/frozen baseline（`src/`、`experiments/`、`tools/`、`results/`）、不改 config/fixture。
- 不覆盖原 `comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/` 四文件，不创建 `run_01`。
- 不引入 SHA/checksum/签名/内容校验机制（Git 版本绑定仅作版本来源，见下）。
- 本文件不授予真实执行；禁真实执行直到 addendum 接受 + 实现复审 + Pre-EXECUTE 全 PASS。

## Impact Scope

允许触及（实现阶段，最小 diff）：

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d2_orthogonal_triage.py` — 仅 prep-time 未定义名修复。
2. `scripts/v72p2d2_orthogonal_triage.py` — 仅同上（若 `Q` 引用在此）。
3. `comparison_bench/tests/test_v72p2d2_orthogonal_triage.py` — 仅新增 fake preparation test（显式注入 fake runner，写 `workspace/<task>/<uuid>`）。

冻结（禁止触及）：原四工件、`PLAN_CANDIDATE.md`、既有 cycle verdict/review 文件、`cycle_state.yaml`（R1 不得直接改状态）、adapter、V72P1/V72P2/D1 接受文件、frozen baseline、既有 outputs、`run_01`。

## Acceptance Criteria

- [ ] R1-1：静态复现 `NameError: name 'Q' is not defined` 为 prep 路径、decoder arm 未进入（L/I/P 0 sweep 语义不变）。
- [ ] R1-2：修复 diff 仅限 prep-time 未定义名（`Q` + 同类静态 `NameError`），`git diff` 无科学语义变更（block/ladder/预算/prior/interleaver/调度/计量/计费无 diff）。
- [ ] R1-3：新增 fake preparation test 通过，生产 import/CLI 默认不进真实 decoder/raw/parquet/生产输出。
- [ ] R1-4：科学冻结字段与原计划字面一致（§冻结清单），A 仍只读复用 D1（decoder0，不重跑）。
- [ ] R1-5：新输出根为 additive `comparison_bench/outputs_comparison/v72p2d2r1_orthogonal_oneblock_20260904/`，原 `v72p2d2_orthogonal_oneblock_20260904/` 四文件 untouched，无 `run_01`。
- [ ] R1-6：`py_compile` + T0/既有 focused 测试 + 新 prep test PASS，`git diff --check` 干净。
- [ ] R1-7：新授权仍为一次（`execution_count_authorized=1`，R1 独立计数，不复用已消耗的 D2 一次）。

## 冻结清单（全不变）

- Block：session `20260123_1M_600k_0dB`，`VAL1726..1729`，`non_fresh=true`。
- Mother：`9036x10240`、`nnz=49620`、check degree `{4:1,5:4594,6:4441}`、degree-2 列 `9035`。
- Ladder：`range(160,8993,128)+[9032,9036]` 共 72 点；每 checkpoint 10 次完整更新，每臂 720；`float64`、`llr_clip=20.0`、`convergence_tol=1e-6`。
- 四臂：A 只读复用 D1（decoder0，不重跑）；L 原 H+M0+layered，I H_I+M0+flooding，P 原 H+M2+flooding；禁混合臂。
- P：V70R1 1M CAL-only M2（Laplace、`mu=0.0`、`scale=0.2714417616594907`、`eps=0.562251256281407`、`Q=1024`）。
- I：`old_cols 0..1203` + seed `20260902` `default_rng` 全列映射，代数方向 `H_I[:,old_to_phys[j]]=H_old[:,j]`。
- 预算：prep 600s + L/I/P 各 600s soft wall，invocation 2400s，peak RSS 2GiB；stop/计费/syndrome-only/oracle-after-arm 语义全不变。

## 输出与授权

- 新输出根（additive，恰四文件 `manifest.json` / `results.json` / `table.csv` / `report.md`）：`comparison_bench/outputs_comparison/v72p2d2r1_orthogonal_oneblock_20260904/`。
- 禁覆原 `v72p2d2_orthogonal_oneblock_20260904/`（`PREP_FAILED` 证据保留），禁 `run_01`。
- 新授权仍一次：R1 接受后另行记录 `execution_count_authorized=1`（R1 独立），A 只读、L/I/P 各一次，无 rerun/调参。
- `base_sha` / `accepted_plan_sha` / `implementation_sha` 仅为 AGENTS 要求的 Git 版本绑定，不承担数据/artifact 内容校验；不新增摘要/签名/校验字段。
- 真实执行门禁：addendum 接受 + 实现复审 + Pre-EXECUTE 全 PASS（含 synthetic cost-preflight `projected_L_wall_s<=600` 重跑确认）之前，禁止任何真实执行。

## Tasks

1. **R1-T1 复现与定界**：用 `py_compile` + fake runner 静态复现 prep `NameError: 'Q'`，确认调用栈止于 prep、未进 L/I/P decoder arm；记录 failing command + traceback，不读 raw/parquet，不写生产输出。
2. **R1-T2 最小修复**：仅定义/传入缺失的 prep-time 名（`Q` 及同类静态 `NameError`，以 `pyflakes/compileall` 无新 `NameError` 为准）；禁止改调度/prior/映射/计量/计费/预算常量；`git diff` 逐行可审。
3. **R1-T3 Fake preparation test**：在既有测试文件内新增一个 fake 端到端 preparation test（显式 fake runner + fresh `workspace/<task>/<uuid>`），断言 prep 通过且默认路径不进真实 decoder/raw/parquet/`run_01`/生产输出根。
4. **R1-T4 冻结校验**：`rg` 科学常量（mother/ladder/预算/M2 参数/seed/三臂 order/输出根）与原计划一致；A 复用 D1 decoder0 只读语义不变。
5. **R1-T5 门禁与停机**：确认新输出根 additive、原 PREP_FAILED 目录 untouched、`git diff --check` + `git status --short` 干净；停止于 `NEXT_GATE: INDEPENDENT_ADDENDUM_REVIEW`，等待接受、实现复审、Pre-EXECUTE。

Next gate: `INDEPENDENT_ADDENDUM_REVIEW`（本文件接受后才允许 R1-T2/T3 实现开工）。
