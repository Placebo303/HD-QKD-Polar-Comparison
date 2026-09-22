# D6 graph/mother — preregistration R1c-A2 (execution-safety + recomputation closeout)

Status: `FROZEN_PREREG_R1C_A2`. R1 §§4–6/§8 scientific freeze carries forward
verbatim (arms/seeds/rows/prior/decoder/mother/selection/scientific terminal
thresholds unchanged). R1c mechanics + R1c-A1 seven fixes carry forward except
the A2 fail-closed deltas below. `a16d3184`/`fc447e12` body retained; A2 only
repairs execution safety and recomputation. No §8 execution under R1c-A2
before R1c-A2 implementation-review PASS + Pre-EXECUTE PASS + explicit §8
authorization. This prereg + `R1C_parallel_revision.md` A2 delta + `tasks.md`
A2 tasks constitute commit 1 (no implementation). Old A2 prompt is void; this
task text is the sole A2 contract. R1b/R1c parallel directions skipped per
user approval (not questioned).

## Science freeze (unchanged, no retuning)

- Arms B0/B1/T1–T4/M1/M2 only; coefficient seeds L1 `202609120100+n` / L2
  `202609120200+n`, triples identical by `(n,layer,column)`, degree-2 uses
  entries 0–1, no selection.
- Rows n64 L1 `(49,59,64)` / L2 `(43,52,64)` scaled x2/x4 for n128/n256.
- Decoder `d5.bind_historical_decoder` cold `max_iter=90`
  `damping_alpha=1.0` `warm_beliefs=None`; L1→APP-L2 + oracle-diagnostic-only.
- Exact = full Alice equality; syndrome separate, never upgrades exact.
- One sample per `(n,seed)` byte-identical across arms.
- Seeds canary `2026091000..03` / confirmation `2026091010..25` / scaling
  `2026091100..03`; nothing else.
- Budgets 2500 calls / 12h wall / 120s watchdog / <2GiB / no-retry.
- Blind selection + `classify_terminal` scientific thresholds unchanged.
- New A2 terminals below are mechanics-only blocking terminals that override
  scientific classification; they do not change scientific thresholds.

## A2-01 VOID freeze (three roots, zero reuse)

- `d6_graph_mother_r1_923a25897087495ab4605870e561f3cc` → `VOID_RETAINED_ZERO_REUSE`
- `d6_graph_mother_r1_e8ee45a4669c4738bf7e96d926ba7e5c` → `VOID_RETAINED_ZERO_REUSE`
- `d6_graph_mother_r1_f15cfa29baa2458e804c80a9f1045140` → `VOID_RETAINED_ZERO_REUSE`
- Name-only freeze: no read / delete / move / use / hash of contents. R1c-A2
  uses only fresh `workspace/d6_graph_mother_r1c_<uuid>/`. Existing D6 root
  never reused.

## A2-02 RSS fail-closed (single pilot, no start-18-then-trim)

- Spawn single pilot worker, collect pilot hello `rss` + main `d5._rss_bytes()`.
- If main is None or pilot is None → no scientific dispatch; terminal
  `D6_RSS_UNKNOWN_BLOCKED`.
- `per_worker` = pilot rss (single measurement). Candidates `<= requested`
  from `(18,14,12,8,1)` descending (1 always included; request 1 stays
  sequential). Effective = largest `w` with `w*per_worker + main < 2GiB`;
  if even `1*per_worker + main >= 2GiB` → terminal `D6_RSS_LIMIT_BLOCKED`,
  no scientific dispatch.
- Expand to effective: spawn `effective-1` more workers, re-sample each
  worker hello rss. Any new hello None → `D6_RSS_UNKNOWN_BLOCKED`, stop. New
  aggregate `sum(worker_rss) + main >= 2GiB` → `D6_RSS_LIMIT_BLOCKED`, stop.
- Per-call + per-barrier (chunk boundary) update: worker-last rss, main-last
  rss (sampled via `d5._rss_bytes()`), sampled aggregate
  `sum(known worker-last) + main-last` (None if any side unknown), single
  peak (max known single) and aggregate peak (max known sampled aggregate)
  tracked separately.
- Persist in `command_log.txt` + `manifest.json`: `main_rss_bytes`,
  `worker_rss_bytes[]`, `aggregate_rss_bytes`, `peak_single_rss_bytes`,
  `peak_aggregate_rss_bytes`, `rss_semantics`
  (`fail-closed-strict-unknown-None-no-zero-substitution-no-single-as-aggregate`).
- Unknown never treated as 0; single peak never masquerades as aggregate peak.
- Pure selector `select_effective_workers_pilot(requested, pilot_rss,
  main_rss)` is unit-tested (fail-closed, includes 1, limit case).

## A2-03 12h deadline (atomic remaining, fail-closed wall)

- `deadline = t0 + 12h` (`t0 = perf_counter` at run start).
- Before every dispatch, atomically (lock-held) check `remaining =
  deadline - now`: if `setup + scientific + 1 > 2500` or `remaining <= 0`
  or `budget_stop` → set `budget_stop`, raise `StopIteration`.
- Worker poll = `min(120s, remaining)` (remaining>0; else 0, no dispatch).
- Deadline arrival during a call: terminate only task-owned worker, record
  `wall_timeout=true`, no respawn, no retry, no further dispatch; terminal
  `D6_WALL_BUDGET_BLOCKED`.
- Final `wall_s > 12h` with terminal != `D6_WALL_BUDGET_BLOCKED` → verify FAIL.

## A2-04 per-record watchdog/wall separation + PID/error

- Every scientific record carries `worker_pid`, `respawn_pid` ("" if no
  respawn), `timeout` (watchdog), `wall_timeout` (deadline), `error` (text).
- `watchdog_ok = (not timeout) and (not wall_timeout) and (wall_s <= 120)`.
- Watchdog timeout (120s poll, remaining >= 120s): terminate + respawn,
  failure consumes cell, no retry; respawn warmup counts 1 `setup_decoder_calls`
  under the same total gate.
- Wall timeout (deadline): terminate, no respawn, no retry; warmup never runs
  after deadline.
- Skipped-APP placeholders (`call_idx=-1`) consume no budget, carry empty
  PID fields.

## A2-05 checkpoint-rewrite persistence (not append-only)

- Semantics renamed to "same fresh UUID root phase checkpoint rewrite".
  Never called append-only.
- After structure build and after every decoder phase chunk (canary,
  per-arm confirmation, per-width scaling canary/confirmation), rewrite
  `decoder_records.csv` in frozen `call_idx` order + `flush()` + `os.fsync()`.
- `os.fsync` failure is fail-closed (raise, stop, no silent pass).
- Canary / confirmation / scaling and `StopIteration` / chunk-wall / RSS /
  wall blocks share one `finally` rule: completed records are always
  checkpointed before exit/override.
- Once any chunk `wall >= 5400s`, zero new dispatches (all later chunks
  skipped, completed phases flushed, terminal overridden as below).
- `run_cells_parallel` returns `(cells, wall)`; caller checks each chunk.

## A2-06 workers=1 scaling-confirmation indent fix

- `cc[point]` inside the point loop; `conf_counts[arm]` inside the arm loop
  outside the point loop. Fake test proves `f1.0`/`f1.2`/`square` all retained
  and identical to the parallel path ordering.

## A2-07 verify expansion (15 independent rejections)

`verify_command` independently rejects on: (1) call_idx not `1..N`
continuous; (2) semantic key `(arm,seed,point,mode)` duplicate; (3) csv count
vs summary `calls` mismatch; (4) `setup + scientific > 2500`; (5) `effective >
requested`; (6) RSS unknown-as-zero / single-as-aggregate / aggregate `>=
2GiB` / `rss_known_ok` mismatch; (7) wall `> 12h` without
`D6_WALL_BUDGET_BLOCKED` / chunk `>= 5400s` without
`D6_GRAPH_CHUNK_WALL_BLOCKED`; (8) terminal recomputation mismatch (science
+ all four blocking terminals); (9) `timeout`/`wall_timeout`/`watchdog_ok`
definition mismatch; (10) `worker_pid` empty on counted rows / unknown PID
reuse; (11) seed-domain violation (outside canary/confirmation/scaling sets);
(12) arm/point/mode coverage mismatch vs selected/advancing; (13) scaling
width/counts recomputation mismatch; (14) manifest/summary field consistency
(requested/effective/calls/setup/total/wall/peaks/semantics); (15) six-file
presence + `decoder-set ≤ 6` + B0-in-set. Any FAIL → `VERIFY FAIL`.

## Freeze / scope / stop rules

- Science (arms/seeds/rows/prior/decoder/mother/selection/scientific terminal
  thresholds) unchanged. No `--phase`, G1/G2, VOID reads, VAL/real/raw,
  parquet outside CAL-TRAIN, D5/src/experiments/tools edits (except
  fail-closed fsync raise in the D6 mother writer if needed),
  search/tuning/retry/push.
- Allowed paths (commit 2): this prereg + `R1C_parallel_revision.md` +
  `tasks.md` (commit 1); `scripts/v72p2d6_graph_mother_development.py` +
  `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (+
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
  only for fail-closed fsync) (commit 2). A2 review file is reviewer-owned;
  coder-fast never writes it.
- Forbidden: three VOID contents, formal roots, V35 report, perf-v38, other
  dirty trees; `git clean/reset/checkout/renormalize/stash/broad-stage/push`;
  `§8`/`--phase`/G1/G2/true decoder; VAL/real/raw reads; reuse of any
  existing D6 root.
- Tests use fakes + task-owned `workspace/<uuid>` basetemps only; delete only
  own basetemp after resolved-prefix verification.
- Any acceptance failure → STOP with ID + command + raw output; no §8.
