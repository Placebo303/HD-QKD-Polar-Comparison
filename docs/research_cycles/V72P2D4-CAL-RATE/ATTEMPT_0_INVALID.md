# V72P2D4-CAL-RATE ATTEMPT_0 INVALID — 旧审计目录非证据（只读收口，不提交旧四输出）

Date: 2026-09-05
Cycle: V72P2D4-CAL-RATE (D4 `formal-ir-v72p2d4-cal-gf32-model-rate-audit`, PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED)
Head: `a7a6ec62` (`formal-ir-v72p1-addendum-clean`)
Old dir (NON-EVIDENCE): `comparison_bench/outputs_comparison/v72p2d4_cal_gf32_model_rate_audit_20260905/` (audit.json / manifest.json / table.csv / report.md)

## 1. 分支/远端/worktree 只读检查（未改、未删、未提交）

- `HEAD == origin/formal-ir-v72p1-addendum-clean == a7a6ec62`；`git status -sb` 跟踪面干净（仅 `AGENT_PROJECT_MEMORY.md` + `docs/decision-log.md` 已改动，未动本次收口不提交）。
- `git worktree list`: `D:/Code/HD-QKD_Polar_Comparison` (`a7a6ec62`) + `D:/Code/HD-QKD_Polar_Comparison-worktree-cascade-single` (`df01f068`)；只读 `rev-parse`/`branch -vv`/`log`，未 fetch、未切换、未删 worktree。
- 未跟踪旧代码/OpenSpec/旧输出全部保留不删：`comparison_bench/src/.../v72p2d4_cal_gf32_model_rate_audit.py`、`scripts/v72p2d4_cal_gf32_model_rate_audit.py`、`comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`、`openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/`、`comparison_bench/outputs_comparison/v72p2d4_cal_gf32_model_rate_audit_20260905/` 均未删除。
- 不提交旧四输出：旧目录四文件保持 untracked，不 `git add`、不 `git commit`、不进正式输出根；本次仅新增本收口文件。

## 2. ATTEMPT_0 无效判定：Pre-RESULT FAIL

旧目录以 D4 前实现口径跑通 CAL-only 标量审计，但对照 D4 冻结计划（proposal/design/tasks `D4T0-2/D4T1-3/D4T2-1~D4T2-4`）逐项不合规，故记 `Pre-RESULT FAIL`，不得作为 D4 证据、不得进选择与路线判定：

- symbol-shuffle 非 blocked：`v72p2d3_gf32_contrast.cal_4fold_cv_heldout_nll` 用 `rng.permutation(n)` + `perm[k::4]` 做 symbol 级打散（`n_train=196608/n_heldout=65536`），不是 D4 冻结的 frame-blocked 4 折 nested（`F0..F3` 各 256 帧、`train768/test256`、确定性帧序划分）；`D4T0-2` FAIL。
- lambda 固定无 inner：`lam=1.0` (`DEFAULT_LAM=PREPARE_LAM`，`audit.json: lambda=1.0`) 单点直通，无 lambda 内层/选择语义。
- 单模型、无 M0、无 rate grid：仅复用 V54 `P1(high|B)/P2(low|high,B)` 单一模型（`prior_shapes P1[1024,32]/P2[32,1024,32]`）；无 `M0` 基线、无 `M0–M3` 估计子/平滑/回退声明与手算验证（`D4T1-3` 缺）；`rate_audit_r5` 只用 resub `CE` 算单点 `required=N*CE`，无 `f∈{1.0,1.1,1.2,1.3}` + `rows=ceil(N*CE*f/5)` 分层行表（`D4T2-4` 缺）；无 `mean(CE_joint)` 最小 + `Δ<0.01` 简单优先名次表（`D4T2-3` 缺）；R5 复现门未跑（`D4T2-2` 缺）。
- 旧目录非证据：旧四文件 `rate_status=MODEL_BUDGET_MISMATCH` 只是描述性标量；`formal:false/cal_only:true`，不进 D4 审计结论。
- VAL0 decoder0：`audit.json: decoder_calls=0/published_bits=0`，`manifest.json: decoder_calls=0/formal:false`；VAL loader 未用于模型（`n_read_rows=545280/n_retained_rows=262144` 仅 CAL 过滤计数），符合“未读 VAL/未调 decoder”但不补合规性。
- 7.796 非合规信号：`cv mean_ce_joint=7.796122677407631`（`3.8974493104279024+3.8986733669797284`，链式自洽）来自上述 symbol-shuffle 单模型路径；`resub ce_joint=5.211667858814099` 同样仅描述性。7.796 不得用于 D4 模型选择、预算路线 A/B/C 或任何纠错/SKR 断言。
- 216 vs 1597 缺 1381：预算 `total1080bit/5=216行`（`L1 80bit/16行、L2 1000bit/200行、rate1.0546875`）；`7.796122677407631*1024=7983.2296bit`，`/5=1596.6459→ceil 1597行`；`1597-216=1381` 行缺口。仅预算算术，不构成信息论下界/失败定论。
- 529 仅 resub 差：`5.211667858814099*1024=5336.7479bit→ceil1068行`；`1597-1068=529` 行只是同一单模型 resub 与 symbol-shuffle CV 的落差，不是模型间比较（无 M0–M3），不得读作改进/退化证据。

## 3. R5 三数值来源结论（synthetic，非真实 CAL）

- R5_REFERENCE_PROVENANCE: `synthetic` — `docs/research_cycles/V72P2D3-GF32/R5_RATE_AUDIT.json: synthetic_cal_only=true, seed=20260905, n_cal=4096, lam=1.0, counts_shape[1024,1024]`；`R5_MATH_INTERFACE_AND_RATE_AUDIT.md §R5实现` 明示“合成 CAL（均匀独立最坏情形，描述性）”；`resub 2.350880/1.021631/3.372511` + `cv mean 6.422161237462124/5.083351288530697/11.50551252599282`（`6.422161+5.083351=11.505513` 链式，`folds L1 6.416225/6.476192/6.420708/6.375520`，`3072/1024`）均为該合成 fixture 产物；`val_reads=0/decoder_calls=0/formal_root_exists=false`。
- R5_FIXTURE_REPRODUCED: 同 fixture 复现公式 — 仅允许同 `seed=20260905/n=4096/lam=1.0` 均匀独立合成口径复算 `6.422161/5.083351/11.505513`（各 `|Δ|<1e-6` 且链式 `<1e-10`）；通过才放行同口径对照，失败即 `BLOCKED`。
- REAL_CAL_EXACT_MATCH_APPLICABLE: `false` — 真实 `CAL702..1725/262144symbols` 与 R5 合成域不同分布、不同 `n`，禁拿 `6.422/5.083/11.505` 硬凑真实 CAL；D4 真实复现门必须按 canonical counts + V54 链 + CAL-only frame-blocked 口径重算，不得预设三数会重现。
- NOT_REPRODUCIBLE 不适用：R5 JSON 完整（非不完整），故不标 `NOT_REPRODUCIBLE`、不猜测缺失值。

## 4. 收口状态

- 本文件为唯一新增：`docs/research_cycles/V72P2D4-CAL-RATE/ATTEMPT_0_INVALID.md`；旧四输出未提交、未覆盖、未删。
- 下一步仍停于 `NEXT_GATE: INDEPENDENT_PLAN_REVIEW`；任何 D4 合规审计须在新输出根按冻结四文件重跑 frame-blocked nested CV + M0–M2 + R5 门（真实 CAL 口径）+ f 网格预算表。
