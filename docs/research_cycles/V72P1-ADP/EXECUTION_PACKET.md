# V72P1-ADP Implementation Packet — FROZEN (PLAN_ACCEPTED / EXECUTE_NOT_AUTHORIZED)

**Repository**: `HD-QKD_Polar_Comparison`
**Branch**: `formal-ir-mainline`
**Cycle ID**: `V72P1-ADP`
**Change ID**: `formal-ir-v72p1-soft-joint-binary-adapter`
**Packet Kind**: `FREEZE_IMPLEMENTATION_PACKET_ONLY` (no code, no decoder, no run_01)

> 本文件为唯一允许的新增文件。不得修改任何现有文件，不实现代码，不运行 decoder，不创建 run_01。
> 任何与本文不一致的执行均属越权。

---

## 1. SHA 与生命周期 (SHA & Lifecycle)

| field | value |
|---|---|
| `required_base_sha` | `f03e160c270765cee6ddbe0ff2765426ae0468a6` |
| `accepted_plan_sha` | `73efd91f379b5abdeda675c36d1a054f59ff89ff` |
| `packet_base_sha` | `f03e160c270765cee6ddbe0ff2765426ae0468a6` (= REQUIRED_BASE_SHA at freeze time) |
| `lifecycle` | `PLAN_ACCEPTED / EXECUTE_NOT_AUTHORIZED` |
| `state` (cycle_state.yaml) | `PLAN_ACCEPTED` (`accepted_plan_sha: 73efd91f...`, `implementation_sha: null`) |
| `implementation_authorized` | `false` |
| `development_execution_authorized` | `false` |
| `formal_execution_authorized` | `false` |
| `decoder_authorized` | `false` |
| `scientific_promotion` | `false` |

- 冻结时刻 `HEAD == refs/remotes/origin/formal-ir-mainline == f03e160c...` 已验证一致。
- `ACCEPTED_PLAN_SHA` 为已接受四工件快照 `73efd91f...`，见 `docs/research_cycles/V72P1-ADP/REVIEW_VERDICT.md` (PLAN_ACCEPTED)。
- 本 packet 冻结后，任何实现或执行需基于新的 implementation SHA 并重新通过 pre-EXECUTE / pre-RESULT 双重 review。
- 不得在同一 commit 内记录其自身 SHA；目标 SHA 由 handoff 绑定、下一 verdict/return 记录。

---

## 2. 唯一允许修改的 implementation/test 文件清单 (Allowed — verbatim from accepted plan)

**判定依据**: 已接受四工件 `proposal.md / design.md / tasks.md / specs/spec.md` (SHA `73efd91f...`) 全文检索。

- 四工件状态均为 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` 且 `design.md §10 / spec §11 / tasks Phase I-J` 明确表述 `This change is plan-only. No src/ modification, no decoder run.` / `本轮只四工件` / `no code, no run_01`。
- 全文未出现任何足以确定的精确 implementation/test 文件绝对路径（无 `comparison_bench/src/...` 新增文件路径、无 `comparison_bench/tests/test_...` 精确路径、无 `scripts/...` CLI 路径）。
- 按冻结指令 `若计划没有给出足以确定的精确路径，立即 BLOCKED，不自行发明路径`，本 packet **不自行发明**任何路径。

**结论 — 本冻结阶段允许清单 = NONE (空集)**:

```
allowed_implementation_files: []
allowed_test_files: []
allowed_config_files: []
```

- 任何未来实现阶段如需新增代码/测试，必须先以独立补冻（如 `EXECUTION_PACKET_ADDENDUM.md` 或新 packet 版本）逐项抄录精确路径并经独立 review ACCEPT 后方可触及文件系统。
- 在该补冻之前，任何对 `comparison_bench/src/`、`comparison_bench/tests/`、`scripts/` 等的写入均属越权，即使声称为 V72P1 适配器实现。
- 本 packet 冻结阶段本身不授权对任何 implementation/test 文件的修改（见 §6）。

---

## 3. 明确禁止 (Forbidden — exhaustive)

以下路径/工件在本 packet 及后续未补冻前**禁止任何修改、创建、覆盖、删除**：

- `src/` — frozen Polar baseline
- `experiments/` — frozen Polar experiments
- `tools/` — frozen replay/security/audit scripts
- `results/` 与既有 `comparison_bench/outputs_comparison/` 下所有既有输出（禁止覆盖、追加需 additive 命名且非本轮）
- `V70` / `V71` / `V72P0` 对应代码、输出、docs（`formal-ir-v70-*`, `formal-ir-v71-*`, `formal-ir-v72p0-*`）
- 已接受的四个 OpenSpec 工件（`openspec/changes/formal-ir-v72p1-soft-joint-binary-adapter/proposal.md`, `design.md`, `tasks.md`, `specs/spec.md`）— 冻结后只读
- `docs/research_cycles/V72P1-ADP/REVIEW_VERDICT.md`
- `docs/research_cycles/V72P1-ADP/cycle_state.yaml`
- `AGENT_PROJECT_MEMORY.md`
- `docs/decision-log.md`
- 真实数据（`2M`/`TEST`/`holdout` 原始 pairs、任何 `*2m*` 采样）、任何 `run_01` 目录、`formal decoder execution`（含 `run_ldpc_formal_v5`、`longrun_*`、`minrerun_*`、`routeA_*`）

补充禁止（来自 tasks §显式禁止）：`decoder/业务矩阵`、`新 mother`、`读 2M/TEST`、`调冻结参数`、`跨 acquisition 拼接`、`MET/protograph/SC`、`宣称 FER/阈值/SKR`、`创建 run_01`、`网格搜索`、`用第二 estimator`、`覆盖输出`、`启动 V72`。

---

## 4. 实现合同 (Implementation Contract — frozen, identical in all four artifacts)

### 4.1 FrozenMotherSpec — 恰好 9 fields (tag_bits NOT here)

```
FrozenMotherSpec:
  Q = 1024
  N = 1024
  Nbit = 10240
  M = 9036
  r0 = 160
  delta = 8
  max_rows = 9036
  f_planning = 1.3
  column_mapping = "sym*10+bit"
```

Exactly 9 fields. `tag_bits` is NOT here.

### 4.2 SoftJointConfig — 恰好 8 fields

```
SoftJointConfig:
  checkpoint_rows = {160,288,...,8992,9032,9036}  # 72 points, see §4.5
  max_iter_per_checkpoint = 10
  max_total_iterations = 720                       # 72*10
  llr_clip = <float>                               # frozen float, to be补冻具体值
  convergence_tol = <float>                        # frozen float, to be补冻具体值
  warm_start = true
  dtype = "float64"
  tag_bits = 64
```

Exactly 8 fields. `tag_bits` only here. `warm_start=true`, `dtype="float64"`, `tag_bits=64`.

### 4.3 权威五式 (Five-Equation Dataflow — COMPLETE and IDENTICAL)

```
bit_to_factor[sym,b]          = sum(check_to_variable[e] for e incident to variable(sym,b))
factor_to_bit[sym,b]          = local_factor_extrinsic(prior_logp[sym,:], bit_to_factor[sym,other_bits_excluding_b])
variable_to_check[e=(v,c)]    = factor_to_bit[v] + sum(check_to_variable[e2] for e2 incident to v if e2.check != c)
check_to_variable[e=(c,v)]    = syndrome_aware_spa(syndrome_target[c], variable_to_check[other_edges_of_c])
app_llr[v]                    = factor_to_bit[v] + sum(check_to_variable[e] for e incident to v)
```

Keywords for rg guard: `local_factor_extrinsic`, `other_bits_excluding_b`, `syndrome_aware_spa`, `syndrome_target`, `factor_to_bit[v]`, `prior_logp[N,Q]`.

### 4.4 八项数据流语义 (8 semantic notes)

1. `prior` only once in local factor — `local_factor_extrinsic` is sole consumer of `prior_logp`
2. `bit_to_factor` only aggregates `check_to_variable`
3. local factor self-exclusion: `other_bits_excluding_b` excludes target bit
4. `variable_to_check` must include `factor_to_bit`
5. `app_llr` must include `factor_to_bit`
6. check update must depend on `syndrome_target` (`syndrome_aware_spa` uses `syndrome_target`)
7. no extra binary channel prior/LLR is introduced
8. forbid `app_llr must not be computed as prior plus sum(c2v)` — semantic: forbid `APP equals prior plus sum`

### 4.5 11 个核心数组及精确 shape/dtype

| # | name | dtype | shape | bytes |
|---|---|---|---|---|
| 1 | prior_logp | float64 | [N,Q] (1024,1024) | 8,388,608 |
| 2 | bit_to_factor | float64 | [N,10] | 81,920 |
| 3 | factor_to_bit | float64 | [N,10] | 81,920 |
| 4 | variable_to_check | float64 | [nnz] (49620) | 396,960 |
| 5 | check_to_variable | float64 | [nnz] (49620) | 396,960 |
| 6 | app_llr | float64 | [Nbit] (10240) | 81,920 |
| 7 | hard_bits | uint8 | [Nbit] | 10,240 |
| 8 | hard_symbols | uint16 | [N] | 2,048 |
| 9 | syndrome_target | uint8 | [active_rows] | 9,036 |
| 10 | syndrome_observed | uint8 | [active_rows] | 9,036 |
| 11 | factor_workspace | float64 | [Q] (1024) | 8,192 |

Prohibit: shape `[Nbit]` for `variable_to_check`, duplicate `app_llr`, `extrinsic[N,Q,10]`, extra binary LLR, `var_belief`. Exactly 11 arrays.

### 4.6 统一内存表 (Authoritative Aperture)

- 11 arrays total: **9,466,840 B ≈ 9.03 MiB**
- CSR: `indptr 36,148 B (9037*4) + indices 198,480 B (49620*4) + data 49,620 B = 284,248 B ≈ 278 KiB`
- Grand total **9,751,088 B ≈ 9.30 MiB**, plus temp still `<2 GiB`
- This is the single authoritative table; delete all old erroneous tables.

### 4.7 复用 V72P0 mother 约束

- 复用 V72P0 `9036×10240` mother, `nnz=49620`, CSR total `284,248`
- `indptr`/`indices` must be **byte-identical** to V72P0
- No new mother matrix construction; SYNTHETIC_ONLY

### 4.8 Prefix / Checkpoint / Iteration

- `prefix 1111`: disclosure prefixes `{160,168,...,9032,9036}`, regular +8 count 1110 + tail 4
- `checkpoints 72`: decoder checkpoints `{160,288,...,8992,9032,9036}`
- `max 10 iterations/checkpoint` (`max_iter_per_checkpoint = 10`)
- `max total iterations 720` (`max_total_iterations = 720`)
- `warm_start = true` (cross-checkpoint message carry-over)
- 无额外 binary channel LLR；不允许 `app_llr` 直接加入 `prior_logp`
- `data_sha = 84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1`, `used_2m false`)

---

## 5. 测试矩阵 (Test Matrix — future-implementation acceptance criteria)

### 5.1 T0 — py_compile / import / 字段 / shape / dtype / 计数 / 内存复算

| test | command | expected PASS | fail stop |
|---|---|---|---|
| T0-1 | `python -m py_compile <all touched py>` | exit 0, no SyntaxError | BLOCKED, fix syntax |
| T0-2 | `python -c "import <adapter modules>"` | import ok | BLOCKED |
| T0-3 | `FrozenMotherSpec` 字段检查 | exactly 9 fields, `tag_bits` absent | BLOCKED — config violation |
| T0-4 | `SoftJointConfig` 字段检查 | exactly 8 fields, `tag_bits==64`, `warm_start==true`, `dtype=="float64"` | BLOCKED |
| T0-5 | 11 arrays shape/dtype 断言 | shapes/dtypes per §4.5 exactly | BLOCKED |
| T0-6 | 机械内存复算 | `11 arrays 9466840`, `CSR 284248`, `grand 9751088` byte-identical to §4.6 | BLOCKED |
| T0-7 | `used_2m false` + mother dims | `9036x10240 nnz 49620` | BLOCKED |

### 5.2 T1 — T-DATAFLOW-1..5, T-CONFIG-1, T-MEMORY-1 (semantic)

| test | semantics | command (synthetic, no real data) | expected PASS | fail stop |
|---|---|---|---|---|
| T-DATAFLOW-1 | `variable_to_check equals factor_to_bit` when `check_to_variable==0` | `pytest -p no:cacheprovider workspace/<task>/.../test_dataflow_1.py -k T_DATAFLOW_1` — construct `factor_to_bit` non-zero, zero `check_to_variable`, assert `variable_to_check[e]==factor_to_bit[v]` | assert PASS | BLOCKED, dataflow §4.3 violation |
| T-DATAFLOW-2 | `app_llr equals factor_to_bit not prior` when `check_to_variable==0` | same harness — assert `app_llr[v]==factor_to_bit[v]` and `app_llr[v]!=prior` path | assert PASS; also checks `prior only once` | BLOCKED |
| T-DATAFLOW-3 | syndrome-aware sign/parity | flip single `syndrome_target[c]`, assert `check_to_variable` sign/coset changes (syndrome_aware_spa) | sign change observed | BLOCKED |
| T-DATAFLOW-4 | prior only via local factor | change `prior_logp[sym,:]` only, assert `variable_to_check`/`check_to_variable`/`app_llr` change only through `factor_to_bit` path, no direct `prior plus sum(c2v)` | dependency probe PASS | BLOCKED — extra prior injection |
| T-DATAFLOW-5 | local-factor self-exclusion | change `bit_to_factor[sym,target_b]` vs other bits, assert `factor_to_bit[sym,target_b]` unaffected by its own incoming but affected by other bits (`other_bits_excluding_b`) | self-exclusion PASS | BLOCKED |
| T-CONFIG-1 | config strict separation | assert `FrozenMotherSpec` keys == 9-field set, `SoftJointConfig` keys == 8-field set, no overlap, `tag_bits` only in SoftJointConfig | exact equality | BLOCKED |
| T-MEMORY-1 | mechanical recompute | recompute bytes per dtype/shape vs frozen table §4.6 | exact match | BLOCKED |

Additional T1 semantics (derived from §4.4, must be covered):
- `local-factor self-exclusion` (T-DATAFLOW-5)
- `syndrome-aware sign/parity` (T-DATAFLOW-3)
- `v2c self-exclusion` (`variable_to_check` excludes `e2.check==c`, verified in T-DATAFLOW-1 harness)
- `APP 含 factor_to_bit` (T-DATAFLOW-2 + §4.3 eq5)
- `prior 只注入 local factor 一次` (T-DATAFLOW-4)
- `mother identity` — `indptr/indices` byte-identical to V72P0 (§4.7)
- `prefix/checkpoint 计数` — `prefix1111` / `checkpoint72` (§4.8)
- `tiny tree BP 对 exhaustive posterior` — P1B `k2/3 n6/9 64/512 8trials 1e-9` (future synthetic, wall <1s)
- `deterministic repeat` — same seed → byte-identical `hard_bits`/`syndrome_observed`
- `finite/clip/convergence/warm-start` — `llr_clip` finite, `convergence_tol` gates, `warm_start` carry-over, `max_total_iterations 720` respected; infinite/NaN → BLOCKED

All T1 tests: synthetic-only, no real data, no `run_01`.

### 5.3 执行与停止规则

- 每项命令预期 `PASS` (exit 0, assertions ok)。
- 任意 `FAIL` → 立即 `BLOCKED`，保留 partial 证据不删除，等待 main-thread 决策，不 rerun/tune/改阈值。
- 测试根目录用 `workspace/<task>/<uuid>` + `pytest -p no:cacheprovider`（Windows ACL 规避）。
- 测试不得隐式触发 production decoder / raw pipeline / `run_01` 创建；需 fake runner 显式注入（本阶段无 runner）。

---

## 6. 允许的执行范围 (Allowed Execution Scope)

| phase | allowed | forbidden |
|---|---|---|
| **packet 冻结阶段 (本轮)** | `NONE` — only create this `EXECUTION_PACKET.md`, no code, no tests, no decoder | 任何代码修改、任何测试执行、任何 decoder、任何 `run_01` |
| **后续实现阶段** | `synthetic qualification only` — P1A plumbing deterministic, P1B tiny `k2/3 n6/9 64/512 8trials`, P1C `9036x10240 1/3/10 iter finite/maxLLR/residual wall <1/<5/≤30s`, P1D small loopy `n12 k3 12bits`, T0/T1 per §5, all synthetic `data_sha 84d62779` | 禁止真实数据（`2M`/`TEST`/`holdout` real pairs）、禁止 `formal decoder execution`、禁止创建任何 `run_01`/`formal run`、禁止 `grid search`/`tuning`/`seed hunting` |
| **formal 阶段** | 未授权 — `FORMAL_EXECUTION_AUTHORIZED: false`，需独立用户 `EXECUTE_AUTH` + pre-EXECUTE review | 一切 formal `run_01` 均属越权 |

---

## 7. Operator 返回合同 (Operator Return Contract)

**本轮返回条件**（二选一）：

- `COMPLETE` — 本 packet 已按 §1-§6 完整冻结，`git diff --check` 0 warnings, staged manifest 恰好一个新文件 `docs/research_cycles/V72P1-ADP/EXECUTION_PACKET.md`
- `BLOCKED` — 具体 blocker（如 `HEAD != REQUIRED_BASE_SHA`、`ACCEPTED_PLAN_SHA` 不一致、`rg <stale-SHA>` 命中、计划无精确路径但强行发明、禁止路径被触及）

**本轮实际返回**（由 operator 填）：

```
COMPLETE
ACCEPTED_PLAN_SHA: 73efd91f379b5abdeda675c36d1a054f59ff89ff
PACKET_BASE_SHA: f03e160c270765cee6ddbe0ff2765426ae0468a6
PACKET_SHA: <to be filled after commit>
HEAD_SHA: f03e160c270765cee6ddbe0ff2765426ae0468a6 (pre-commit; post-commit == PACKET_SHA)
ORIGIN_SHA: f03e160c270765cee6ddbe0ff2765426ae0468a6
CHANGED_FILES:
- docs/research_cycles/V72P1-ADP/EXECUTION_PACKET.md (new)
IMPLEMENTATION_AUTHORIZED: false
DECODER_EXECUTED: false
RUN_01_CREATED: false
```

**剩余独立 review 项**（packet 阶段后）：

- implementation candidate 的独立 review（检查 FrozenMotherSpec 9 / SoftJointConfig 8 / 11 arrays / 5 equations / 8 semantics 全量一致、`rg` 旧 SHA 0 命中、内存复算、`prefix1111`/`checkpoint72`/`max_total_iterations 720`/`warm_start true`/`dtype float64`）
- pre-EXECUTE review（如未来授权 synthetic execution：`HEAD == origin == implementation SHA`、`ACCEPTED_PLAN_SHA` 重推导一致、`run_01` 不存在、`py_compile`+T0 PASS）
- pre-RESULT review（development result 发布前独立线程复核阈值、泄漏分解、`undetected` 隔离等）

---

## 8. 权威合同校验行

`max_total_iterations 720 warm_start true dtype float64 prior_logp[N,Q] local_factor_extrinsic other_bits_excluding_b syndrome_aware_spa syndrome_target factor_to_bit[v] checkpoint_rows FrozenMotherSpec SoftJointConfig 11 arrays 5 equations prefix1111 checkpoint72 9036x10240 nnz49620` — 用于 `rg` 一致性校验。

---

*Freeze time: 2026-09-02, operator V72P1-ADP packet freeze. No implementation, no decoder, no run_01.*
