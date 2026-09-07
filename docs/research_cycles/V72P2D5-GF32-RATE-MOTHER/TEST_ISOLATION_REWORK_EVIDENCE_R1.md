# Test isolation rework evidence R1 (CID-01..05, no prod change)

Scope: narrow rework only. No algorithm/lifecycle redesign. No prod change,
no real decoder, no formal modify, no G1 disposition.

## CID-02 forbidden snapshots (path/size/mtime_ns, no hash)

Start (before edit):
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py` | size=116839 | mtime_ns=1788713310404805700
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py` | size=11543 | mtime_ns=1788713158063866800
- `scripts/v72p2d5_gf32_rate_mother.py` | size=3755 | mtime_ns=1788713319458596300
- `scripts/v72p2d5_prepare_model_f_input.py` | size=5980 | mtime_ns=1788716422049194900
- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml` | size=1893 | mtime_ns=1788634129755485000
- `AGENT_PROJECT_MEMORY.md` | size=224974 | mtime_ns=1788625778417799600
- `docs/decision-log.md` | size=184595 | mtime_ns=1788708167610194900
- `openspec/project.md` | size=10196 | mtime_ns=1788711190006705100

End (after rework, before review):
- same 8 files: sizes/mtimes identical to start (verified pre-pytest and
  post-pytest; no edit during rework).

Pre-existing HEAD diffs acknowledged (not caused by this rework, not
reverted/absorbed):
- `AGENT_PROJECT_MEMORY.md`, `comparison_bench/src/.../v72p2d5_gf32_rate_mother.py`,
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`,
  `docs/decision-log.md`, `docs/.../cycle_state.yaml`,
  `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/design.md`,
  `proposal.md`, `specs/spec.md`, `tasks.md`, `openspec/project.md`,
  `scripts/v72p2d5_gf32_rate_mother.py` were already `M` at HEAD before rework.
- Allowlist dirt in rate_mother core+CLI, MEMORY, decision-log, cycle_state,
  mother-plan OpenSpec, project.md used as read-only context only.

Changed files this rework (only):
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (M; parametrized + TIS repair)
- `openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/tasks.md` (untracked dir; additive T-ISOL)
- `openspec/changes/v72p2d5-p0-g1-g2-production-path/tasks.md` (untracked dir; additive T-ISOL)
- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/TEST_ISOLATION_REWORK_EVIDENCE_R1.md` (this file, CREATE)
- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` (append containment rework only)

`git diff --name-only HEAD` (tracked) during rework lists only pre-existing
`M` files above plus the allowed test file; no new tracked prod file appears.
`git status --porcelain=v1 -- <allowed>` shows:
- `M comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- `?? comparison_bench/tests/test_v72p2d5_model_f_input.py` (unchanged, not edited)
- `?? .../UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md`
- `?? openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/tasks.md`
- `?? openspec/changes/v72p2d5-p0-g1-g2-production-path/tasks.md`
No hash/stash/reset/commit performed.

## Lifecycle roots (stat only, no hash/copy/delete/move/rename/normalize)

Before edit / pre-pytest / post-focused / post-combined (all identical):
- Model-F root `workspace/v72p2d5_model_f_input/20260907_r1/` exists:
  `model_f_input.npz` 208467 ticks 1788718027043698800;
  `model_f_input_summary.json` 752 same mtime.
- G0 recovery `workspace/v72p2d5_g0_recovery/20260906_r1/` exists:
  `execution_summary.json` 404, `report.md` 722, `results.json` 2531,
  `table.csv` 306 (mtimes per start snapshot; unchanged).
- Incident G1 `workspace/v72p2d5_g1/20260906_r1/` exists, preserved unchanged:
  `execution_summary.json` 267, `report.md` 146, `results.json` 2593,
  `table.csv` 126 (mtimes per start snapshot; unchanged).
- P0/G2 absent confirmed each stage:
  `workspace/v72p2d5_p0_cost/20260906_r1` False,
  `workspace/v72p2d5_g2/20260906_r1` False.
- No new formal output created by focused/combined runs (tmp basetemps only).

## CID-01 T-ISOL location

Additive `## T-ISOL Lifecycle-independent test containment` with T-ISOL-01..10
added to BOTH:
- `openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/tasks.md`
- `openspec/changes/v72p2d5-p0-g1-g2-production-path/tasks.md`
No rewrite of T1-T9/T1-T6/PX11. Mappings: M19 unauthorized, M21 missing
P0/G1/G2, P0G1G2_i ex-unsafe G1, M20 fake runner, TIS static, M24/P12,
new parametrized P0/G1/G2.

## CID-03 physical vs logical enumeration (AST+manual, no invented count)

Method: stdlib `ast` walk for `run_p0_cost_synthetic`/`run_g1_synthetic`/
`run_g2_synthetic` via direct `mod.run_*`, `runner=getattr(mod,name)`,
loop-var `fn` only inside `for fn in (...synth...)`, parametrized
`runner_name`. Phase loops (`run_p0_cost_phase` etc.) excluded.
`test_v72p2d5_model_f_input.py` has 0 synthetic calls.

Physical 8 / logical 16:

| CID-idx | file | line | enclosing-test | callee | direct/loop | functions-if-loop | authorized | expected-count-if-loop | counts/p_b | decode_fn | out_dir | isolated-missing | binder-boom | writer-boom | prod-reachable | formal-reachable | classification | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-01 | test_v72p2d5_gf32_rate_mother.py | 2884 | test_P0G1G2_e_authorization_refuses_before_work | fn | loop | run_p0_cost_synthetic,run_g1_synthetic,run_g2_synthetic | False | 3 | absent/absent | absent | absent | N/A (choke first) | _load_g0_decoder boom, 0 entries | 3 writers boom, 0 entries | False | False | unauthorized_choke | NotAuthorizedError x3, entered [], tmp empty |
| E-02 | test_v72p2d5_gf32_rate_mother.py | 2886 | test_P0G1G2_e_authorization_refuses_before_work | fn | loop | run_p0_cost_synthetic,run_g1_synthetic,run_g2_synthetic | False | 3 | absent/absent | FakeDecoder() explicit | absent | N/A (choke first) | same booms, 0 | same booms, 0 | False | False | unauthorized_choke | NotAuthorizedError x3, entered [], tmp empty, CLI exit 3 |
| E-03 | test_v72p2d5_gf32_rate_mother.py | 3108 | test_P0G1G2_i_g0_recovery_structure_regression | run_g1_synthetic | direct mod.run_* | — | True | — | absent/absent | absent (boom guards) | absent (absent-tmp root) | YES absent_model_f tmp + chdir tmp | bind_historical_decoder boom, 0 | write_g1_evidence boom, 0 | False | False | fail_before_decoder | BLOCKED, entered [], tmp empty, real Model-F unchanged |
| E-04 | test_v72p2d5_gf32_rate_mother.py | 3162 | test_M19_d5_unauthorized_artifact_zero | run_g1_synthetic | direct | — | False | — | absent/absent | absent | absent | N/A | binder boom, 0 | writer boom, 0 | False | False | unauthorized_choke | NotAuthorizedError, entered [], tmp empty |
| E-05 | test_v72p2d5_gf32_rate_mother.py | 3164 | test_M19_d5_unauthorized_artifact_zero | run_g1_synthetic | direct | — | False | — | absent/absent | FakeDecoder() | absent | N/A | binder boom, 0 | writer boom, 0 | False | False | unauthorized_choke | NotAuthorizedError, entered [], snapshots unchanged |
| E-06 | test_v72p2d5_gf32_rate_mother.py | 3189 | test_M20_d5_authorized_fake_load_reaches_runner | run_g1_synthetic | direct | — | True | — | counts_ab=c explicit, p_b=pb explicit (injected) | FakeDecoder() explicit | out tmp explicit | NO (injected fake load via mock) | not entered (mocked loader) | real writer to tmp only | False (FakeDecoder, hist 0) | False (tmp only, G1 unchanged) | authorized_fake_tmp | 440 calls, phase g1, tmp 4 files, P0/G2 absent |
| E-07 | test_v72p2d5_gf32_rate_mother.py | 3238 | test_M21_d5_missing_artifact_blocked_no_toy | fn | loop | run_p0_cost_synthetic,run_g1_synthetic,run_g2_synthetic | True | 3 | absent/absent | absent (boom guards) | absent (absent-tmp root) | YES absent_model_f tmp + chdir tmp | bind boom, 0 | all 3 writers boom, 0 | False | False | fail_before_decoder | BLOCKED x3, entered [], tmp empty, real MF/G1 unchanged, no toy (source asserts) |
| E-08 | test_v72p2d5_gf32_rate_mother.py | 3282 | test_M21_param_missing_isolation | runner (=getattr(mod,runner_name)) | getattr-parametrized | run_p0_cost_synthetic/write_p0_cost_evidence, run_g1_synthetic/write_g1_evidence, run_g2_synthetic/write_g2_evidence | True | 3 (parametrize) | absent/absent | absent (boom guards) | absent (absent-tmp root) | YES absent_model_f tmp + chdir tmp | bind boom, 0 | corresponding + all 3 writers boom, 0 | False | False | fail_before_decoder | BLOCKED x3, entered [], tmp empty, real MF/G1 unchanged |

Physical_callsite_count=8, logical_variants=16 (3+3+1+1+1+1+3+3).
Table complete: True. All prod False, formal False. Fakes (E-06) have
fake+injected+tmp. Fail-before (E-03,E-07,E-08) have missing+guards
(absent root + binder boom + writer boom + BLOCKED assert).

## STATIC guard repair

`test_TIS_static_authorized_synthetic_isolation` now handles direct
`mod.run_*`, `Name in synth`, `runner=getattr(mod,runner_name|\"run_*\")`,
loop-var `fn` only inside `for fn in (...synth...)` (phase loops excluded),
parametrized `runner_name` strings. Enforces SAFE A (unauthorized False
continue), SAFE B (authorized True + counts + p_b + decode_fn + out_dir
continue), SAFE C (authorized True bare only in allowlisted
`test_M21_d5_missing_artifact_blocked_no_toy`,
`test_M21_param_missing_isolation`,
`test_P0G1G2_i_g0_recovery_structure_regression` with boom + BLOCKED +
absent_model_f + bind_historical_decoder + writer-evidence markers).
Stdlib `ast` only. No broad except. No blocker weaken.

## CID-05 parametrized

`@pytest.mark.parametrize(("runner_name","writer_name"),[("run_p0_cost_synthetic","write_p0_cost_evidence"),("run_g1_synthetic","write_g1_evidence"),("run_g2_synthetic","write_g2_evidence")])`
`test_M21_param_missing_isolation` supplements (not replaces) M21 loop.
Each: monkeypatch FORMAL_ROOT to absent tmp, binder boom, corresponding +
all-3 writer booms, `runner=getattr(mod,runner_name)`, `runner(authorized=True)`
requires BLOCKED, binder 0 writer 0, tmp empty, real Model-F/G1 unchanged.
P0G1G2_i keeps G0/recovery asserts + one documented isolated G1; no bare
authorized True elsewhere.

## GATE G01-G09 (before pytest, all PASS)

- G01 enumerate: 8 physical / 16 logical enumerated above, no hidden call.
- G02 no default decoder: every authorized True has explicit FakeDecoder (E-06)
  or binder-boom BLOCKED (E-03,E-07,E-08); no prod bind reachable.
- G03 no default formal root: every authorized True has tmp out_dir (E-06) or
  absent-tmp root with BLOCKED (E-03,E-07,E-08); no formal default written.
- G04 P0/G1/G2 missing covered: M21 loop (3) + param (3) + P0G1G2_i (G1).
- G05 no CLI auth exec: rate_mother test file has no `--execution-authorized`
  literal, no `"*_execution_authorized": True`; CLI unauthorized exit 3 only.
  (model_f_input file authorized CLI calls are its own fake-loader scope.)
- G06 no cycle write: no `STATE_PATH.write`, no `yaml.dump` in either test file
  (only obfuscated guard literals).
- G07 prod snapshots unchanged: 8 forbidden sizes/mtimes identical start→pre-pytest.
- G08 evidence unchanged: Model-F/G0-recovery/G1 snapshots identical, tmp clean.
- G09 P0/G2 absent: both `False` before pytest.
Gate verdict: PASS → pytest started. Prod 0, formal 0.

## Step1 collect-only

Cmd: `python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py --collect-only -q -p no:cacheprovider`
Result: total 165 collected, errors 0.
Per-file: `test_v72p2d5_gf32_rate_mother.py` 134, `test_v72p2d5_model_f_input.py` 31.
No line-count inference used.

## Step2 focused

Cmd: `python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_M19_d5_unauthorized_artifact_zero comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_M20_d5_authorized_fake_load_reaches_runner comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_M21_d5_missing_artifact_blocked_no_toy comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_M21_param_missing_isolation comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_P0G1G2_i_g0_recovery_structure_regression comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_TIS_static_authorized_synthetic_isolation comparison_bench/tests/test_v72p2d5_model_f_input.py::test_M24_formal_roots_absent comparison_bench/tests/test_v72p2d5_model_f_input.py::test_P12_formal_roots_absent -p no:cacheprovider --basetemp workspace/v72p2d5_test_isolation_rework_focused_20260907r1 --tb=short -v`
Result: collected 10, passed 10, failed 0, duration ~1.93s, failed IDs none.
Incident G1 / Model-F / G0 unchanged after; P0/G2 still absent.
No prod decoder bind (binder booms 0, FakeDecoder only in M20).

## Step3 combined (only because focused passed)

Cmd: `python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py -p no:cacheprovider --basetemp workspace/v72p2d5_test_isolation_rework_combined_20260907r1 --tb=short -q`
Result: 165 passed, 0 failed, duration ~8.14s.
Incident G1 / Model-F / G0 unchanged after; P0/G2 still absent.

## Step4 per-file collect-only (for clarity)

- `test_v72p2d5_gf32_rate_mother.py --collect-only`: 134 collected.
- `test_v72p2d5_model_f_input.py --collect-only`: 31 collected.

## Forbidden shortcuts (all False)

No prod edit, no G1 delete/move/auth, no cycle true, no skip on existence,
no valid-fixture assert, no absence→exists flip, no removed auth tests,
no broad except, no weakened blocker, no real parquet prep, no CLI P0/G1/G2,
no prod decoder, no new formal output, no commit/push.
