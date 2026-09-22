# D6 graph/mother — Implementation Review R1c-A2 (independent, read-only)

Status: `PASS` (reviewer-go, independent re-read of two commits, no code edits, no S8/decoder/phase execution)

- Branch: `formal-ir-v72p1-addendum-clean`
- Commit 1 (prereg, docs only): `03eff680` docs(v72p2d6): freeze R1c-A2 execution-safety prereg
- Commit 2 (implementation+tests): `15f1de79` feat(v72p2d6): R1c-A2 execution-safety rework
- Reviewer: reviewer-go (read-only; this file + Pre-EXECUTE file are the only reviewer-owned writes)
- Date (UTC): 2026-09-09
- Scope: verify A2-01..A2-08 against `D6_GRAPH_MOTHER_PREREG_R1C_A2.md` + `R1C_parallel_revision.md` A2 delta + `tasks.md` A2 tasks; science zero-change; forbidden-path exclusion; tests.

## Verdict

Verdict: **pass**

No blocking issues. Two review files are created per task (this file + `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1C_A2.md`). No code changes, no S8 authorization (see Pre-EXECUTE file: S8 still requires separate authorization; this round does NOT authorize S8).

## Commit manifests (allowed paths only)

Commit 1 `git show --name-only --pretty=format:"%H %s" 03eff680`:

- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_PREREG_R1C_A2.md`
- `openspec/changes/v72p2d6-gf32-graph-mother-successor/R1C_parallel_revision.md`
- `openspec/changes/v72p2d6-gf32-graph-mother-successor/tasks.md`

Commit 2 `git show --name-only --pretty="" 15f1de79`:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py` (numstat 2/2, fsync fail-closed only)
- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (numstat 375/0, 12 new fake tests)
- `scripts/v72p2d6_graph_mother_development.py` (numstat 1005/170, execution-safety rework)

Matches prereg Freeze/scope allowlist: prereg + R1C_parallel_revision + tasks (commit 1); development script + D6 tests (+ formal_ir only for fail-closed fsync) (commit 2). Coder did not write review files (both were absent before this review; verified via Test-Path False/False).

## A2-01 VOID freeze (three roots, zero reuse) — PASS

- Prereg names verbatim: `d6_graph_mother_r1_923a25897087495ab4605870e561f3cc`, `d6_graph_mother_r1_e8ee45a4669c4738bf7e96d926ba7e5c`, `d6_graph_mother_r1_f15cfa29baa2458e804c80a9f1045140` -> `VOID_RETAINED_ZERO_REUSE`, name-only, no read/delete/move/use, fresh `workspace/d6_graph_mother_r1c_<uuid>/` only.
- Code/touch check: `Select-String VOID|923a|e8ee|f15c` in `scripts/v72p2d6_graph_mother_development.py` at HEAD returns zero hits; test-file diff contains zero VOID/root-reuse hits; `git grep VOID_RETAINED|923a|e8ee|f15c` at 03eff680 vs 15f1de79 shows hits only in pre-existing docs + new prereg/OpenSpec (name-level), none in code paths. Implementation never references VOID contents; `main()` refuses overwrite (`if out.exists(): sys.exit(2)`) and requires explicit `--out-root` (no formal default).

## A2-02 RSS fail-closed single pilot — PASS

- `select_effective_workers_pilot(requested, pilot_rss, main_rss)` (scripts L401-443): pure selector, candidates from (18,14,12,8,1) filtered `<= requested` + dedup (request 1 stays sequential); pilot/main None or non-int -> `(None,"unknown")`; even w=1 over budget -> `(None,"limit")`; largest w with `w*per+main < 2GiB`, else limit. Logging distinguishes unknown vs limit.
- `aggregate_rss_strict` (L382-398): None if any side unknown/non-int (never 0).
- `update_rss_sample` / `update_rss_barrier` (L446-534): per-call/per-barrier worker-last + main-last + sampled aggregate (None unless full-pool view covers effective), single peak vs aggregate peak tracked separately, no single-as-aggregate substitution.
- `main()` pilot flow (L1534-1669): single `Worker(logfh, state)` pilot first, sample `d5._rss_bytes()` main + pilot hello rss; `st != ok` -> stop pilot, `workers=0`, `budget_stop=True`, terminal `D6_RSS_UNKNOWN_BLOCKED`/`D6_RSS_LIMIT_BLOCKED`, zero scientific dispatch (`rss_blocked` gates canary/confirmation/scaling; placeholders flushed). Expansion spawns `effective-1` more, re-samples each hello; any None -> UNKNOWN stop; strict aggregate `>= 2GiB` -> LIMIT stop. Persistence: manifest/summary carry `main_rss_bytes`, `worker_rss_bytes[]`, `aggregate_rss_bytes`, `peak_single_rss_bytes`, `peak_aggregate_rss_bytes`, `rss_semantics=fail-closed-strict-unknown-None-no-zero-substitution-no-single-as-aggregate`.
- Tests: `test_r1c_a2_rss_unknown_blocked`, `test_r1c_a2_single_worker_over_limit`, `test_r1c_a2_pilot_downcore`, `test_r1c_a2_runtime_over_limit_barrier` (all PASS, see Tests).

## A2-03 12h deadline — PASS

- Constants unchanged: `CALL_BUDGET=2500`, `WALL_BUDGET=12*3600`, `WATCHDOG=120`, `R1C_CHUNK_WALL_MAX=5400` (scripts L39-48; no diff changing definitions).
- `_deadline(state)` = `state.deadline` else `t0+WALL_BUDGET` (L122-134); `_remaining_s` (L137-141); `can_dispatch` blocks on `budget_stop`/`chunk_wall_blocked`/`remaining<=0` (L144-152).
- `reserve_setup_idx` / `reserve_call_idx` (L155-196): lock-held atomic check `setup+scientific+1>2500 or remaining<=0 or budget_stop` -> set `budget_stop`, raise `StopIteration`. No check-release-run.
- `Worker.call` (L243-309): `poll_s=min(120s,remaining)` when state present; `rem0<=0` pre-dispatch returns wall-timeout record without dispatch; poll expiry distinguishes `deadline_hit=_remaining_s<=0` -> wall record (`wall_timeout=True`, `budget_stop=True`, no respawn) vs watchdog path (respawn, see A2-04). Deadline warmup never runs after deadline (reserve fails first).
- Terminal precedence (L2103-2133): RSS-block > WALL (`_wall_seen or _wall_early>WALL_BUDGET or _rem_early<=0` -> `D6_WALL_BUDGET_BLOCKED`) > CHUNK. Verify wall-budget check (L1205-1221): `wall<=12h or term==D6_WALL_BUDGET_BLOCKED`, chunk-over without `D6_GRAPH_CHUNK_WALL_BLOCKED` -> FAIL.
- Test: `test_r1c_a2_deadline_poll_min` PASS (remaining in (0,30], `min(120,rem)<120`, past-deadline `can_dispatch False` + `reserve_call_idx StopIteration` + `budget_stop`).

## A2-04 dual PID/error + watchdog/wall separation — PASS

- `DECODER_FIELDNAMES` (L58-63) carries `worker_pid`, `respawn_pid`, `timeout`, `wall_timeout`, `error` (plus `watchdog_ok`, `wall_s`, `rss_bytes`).
- `run_cell`/`invoke` path (L820-878 reviewed): `watchdog_ok=(not timeout) and (not wall_timeout) and (wall<=120)`; watchdog timeout (120s poll, remaining>=120s) terminate+respawn, failure consumes cell, warmup counts 1 setup under same total gate; wall timeout terminate, no respawn, no retry, `budget_stop=True`; skipped-APP placeholders `call_idx=-1` consume no budget with empty PID fields.
- Verify `timeout-watchdog` (L1265-1281): recomputes `exp=(not to)and(not wt)and(w<=120)`, requires `got==exp` and `not(to and wt)`. Verify `pid-present` (L1282-1297): counted rows require non-empty `worker_pid`, presence of `respawn_pid`/`wall_timeout`/`error`, respawn differs from worker when present.
- Tests: `test_r1c_a2_dual_timeout_separation` (mutual exclusion, `watchdog_ok False`, non-empty error) + `test_r1c_a2_dual_pid` (respawn 111->222, normal 333/"") PASS.

## A2-05 checkpoint rewrite + fsync fail-closed — PASS

- Semantics renamed (never append-only): `flush_decoder_records` (L881-900) ordered rewrite by `call_idx` + `flush()` + `os.fsync()` with `raise RuntimeError("fsync-failed decoder_records")` on failure; `append_structure_records` (L903-948) read+merge+ordered rewrite by (arm,n,layer,prefix_rows) + flush/fsync with `raise RuntimeError("fsync-failed structure_records")`. Formal_ir change is the same fail-closed pattern for structure writer (2-line diff, `except Exception as ex: raise RuntimeError(...)`).
- Per-phase checkpoint: structure after build; decoder after canary, per-arm confirmation, per-width scaling canary/confirmation; `run_cells_parallel` returns `(cells, wall)` (L984-1022), caller checks each chunk via `note_chunk_wall` + `chunk>=5400s -> zero new dispatches` (`can_dispatch` + `chunk_wall_blocked` + `budget_stop`, L992-999).
- Unified `finally` (L2235-2255): completed records always checkpointed before exit/override; `StopIteration`/chunk-wall/RSS/wall blocks each flush completed phases before override.
- Test: `test_r1c_a2_fsync_fail_closed` (injected `os.fsync` boom -> RuntimeError for both writers) + `test_r1c_a2_stopiteration_checkpoint` (budget=2, two invokes then StopIteration, ordered rewrite [1,2]) PASS.

## A2-06 workers=1 indent fix — PASS

- Sequential confirmation (L1789-1805): `cc[point]=ex` inside point loop (36-space indent), `conf_counts[arm]=cc` inside arm loop outside point loop (32-space). Parallel confirmation tally (L1854-1866) and scaling-confirm sequential (L1998-2017) / parallel (L2072-2083) follow the same point-major ordering.
- Diff evidence: `git diff 03eff680..15f1de79` shows `cc[point]` indent shift into point loop + `conf_counts[arm]` placement; current file L1804-1805 matches the asserted literal.
- Test: `test_r1c_a2_sequential_three_point_consistent` proves f1.0/f1.2/square retained (`{"f1.0":1,"f1.2":2,"square":1}`) and parallel-consistent, plus source-indent literal assert PASS.

## A2-07 verify 15 independent rejections — PASS

`verify_command` (L1037-1373) implements 15 `check()` gates (each FAIL -> `VERIFY FAIL`):

1. six-files presence (`manifest/structure/selected/decoder/summary/command_log`)
2. call_idx continuous 1..N
3. semantic-key `(arm,seed,point,mode)` no-dup
4. calls csv vs summary/manifest consistency
5. total `setup+scientific<=2500` + total equality
6. effective<=requested (+ blocked-None handling, req in (18,14,12,8,1))
7. RSS strict (unknown-as-zero / single-as-aggregate / aggregate>=2GiB / `rss_known_ok` agreement / semantics substring)
8. wall `>12h` without `D6_WALL_BUDGET_BLOCKED` / chunk `>=5400s` without `D6_GRAPH_CHUNK_WALL_BLOCKED`
9. terminal replay (science via `_adv`/`_cls` + 4 blocking terminals)
10. timeout/wall_timeout/watchdog_ok definition
11. PID present + respawn/error fields + no PID reuse
12. seed domain (canary/confirmation/scaling sets)
13. coverage (arms/points/modes in frozen sets, decoder-set<=6 + B0-in-set)
14. scaling recompute (canary replay + advancement + width)
15. manifest/summary consistency (setup/total/itmax/revision/wall-delta)

All 15 present with independent `check()` names; terminal set includes all four blocking terminals (`D6_GRAPH_CHUNK_WALL_BLOCKED`, `D6_RSS_UNKNOWN_BLOCKED`, `D6_RSS_LIMIT_BLOCKED`, `D6_WALL_BUDGET_BLOCKED`).

## A2-08 fake/tmp-only tests — PASS

12 new tests (fake/tmp only, no real decoder, `tmp_path` basetemps):

- `test_r1c_a2_rss_unknown_blocked` (unknown pilot/main -> unknown, strict None)
- `test_r1c_a2_single_worker_over_limit` (w=1 over -> limit)
- `test_r1c_a2_pilot_downcore` (18x120MiB+50MiB -> 14; ceiling holds; 1 stays 1)
- `test_r1c_a2_runtime_over_limit_barrier` (aggregate over -> detectable, peaks separated)
- `test_r1c_a2_deadline_poll_min` (poll=min, past-deadline fail-closed)
- `test_r1c_a2_dual_timeout_separation` (watchdog vs wall mutual exclusion)
- `test_r1c_a2_dual_pid` (respawn PID separation)
- `test_r1c_a2_fsync_fail_closed` (injected fsync -> RuntimeError)
- `test_r1c_a2_stopiteration_checkpoint` (budget StopIteration + ordered checkpoint)
- `test_r1c_a2_sequential_three_point_consistent` (three-point + indent literal)
- `test_r1c_a2_malformed_verify_fail` (call_idx gap -> VERIFY False)
- `test_r1c_a2_seed_pollution_verify_fail` (seed 999999999 -> VERIFY False)

Total file now 32 tests (10 packet + 10 R1c/A1 + 12 A2). No VOID reads, no production `--out-root`, no VAL/real/raw, no decoder execution (Fake workers only).

## Science zero-change — PASS

- Formal_ir numstat 2/2 (only fsync raise); scripts diff contains no changes to `ARMS`/`ROW_BUDGETS`/`CANARY_SEEDS`/`CONF_SEEDS`/`SCALING_SEEDS` definitions, `CALL_BUDGET`/`WALL_BUDGET`/`WATCHDOG`/`CHUNK` values, `bind_historical_decoder`/`max_iter=90`/`damping_alpha=1.0`/`warm_beliefs=None`, L1->APP-L2 schedule, exact/syndrome separation, single-sample reuse, blind `select_advancement`/`classify_terminal` thresholds. New terminals are mechanics-only blocking overrides (do not change scientific thresholds, per prereg).
- Grep `^[-+].*SEEDS.*=|^[-+].*WALL_BUDGET|^[-+].*WATCHDOG|^[-+].*CALL_BUDGET` on the scripts diff returns only usage/context lines, no redefinition.

## Forbidden-path exclusion — PASS

- `git show --name-only` for both commits lists only the 6 allowed paths above; V35 report, formal roots, perf-v38 paths absent from both commits.
- Content scan of the scripts diff for `perf-v38|V35-report|VAL_|parquet|--phase|G1|G2` returns zero hits (excluding benign substring matches already triaged).
- No `git clean/reset/checkout/renormalize/stash/broad-stage/push` in commits; no S8/`--phase`/G1/G2/true-decoder execution in this review (only `py_compile` + fake `pytest`, see Tests).

## Tests — PASS (32/32)

- `python -m py_compile` on all three commit-2 files: PASS (`PY_COMPILE_PASS_3_FILES`).
- Focused: `python -m pytest comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py -p no:cacheprovider -q -k r1c_a2` -> **12 passed, 20 deselected** (0.49s).
- Full D6: same file without `-k` -> **32 passed** (2.17s). Matches required 12 fake + prior 20 (no perf-v38 800s suite, per A2-08).
- No S8/decoder/phase executed; tests use fakes + `tmp_path` only.

## Blocking Issues

- None.

## Non-Blocking Suggestions

- Worktree is dirty with many unrelated modifications (e.g. `docs/v35-algorithm-development-report.md`, `comparison_bench/outputs_comparison/_tmp_*`, plus CRLF warnings). Out of scope for these two commits (name-only proves exclusion); preserve unrelated changes and re-verify scoped cleanliness before any future S8 Pre-EXECUTE execution.
- `verify_command` check (1) `six-files` + check (13) `coverage` jointly cover the A2-07 item-15 six-file + decoder-set<=6 + B0-in-set semantics; consider a one-line comment cross-linking the two checks to the prereg item number for faster future audits.
- `RSS_SEMANTICS` is split across two string literals; concatenated value matches prereg verbatim, but a single `assert RSS_SEMANTICS == "fail-closed-..."` unit line would prevent future line-wrap drift.

## Checklist

- [x] Matches OpenSpec spec (prereg R1c-A2 + R1C_parallel_revision A2 delta + tasks A2-01..A2-09; A2-09 STOP-for-review honored)
- [x] Tests pass (py_compile 3 files; 12 A2 fake PASS; full D6 32 PASS)
- [x] No scope creep (formal_ir 2-line fsync only; scripts mechanics-only; tests fake-only; docs prereg-only)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No — mechanics-only closeout, no new durable decision or reusable failure mode beyond prereg coverage.

*Reviewer did not edit code, did not execute S8/decoder/phase, did not touch VOID contents or formal roots.*