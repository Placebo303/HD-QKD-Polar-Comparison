# R1c parallel revision addendum — V72P2D6 GF32 graph/mother successor

Status: `FROZEN_PREREG_R1C_DELTA`. Main-thread ruling B: establish R1c parallel
revision; R1b PASS (cycle-2, commit 61767ca2 chain) is void for execution —
no R1b evidence reuse, void144 calls quarantined.

## R1c scientific freeze (unchanged from R1 §§4–6/§8)

- Arms: B0/B1/T1–T4/M1/M2 only; no new topology/degree/window/parameter.
- Coefficient seeds: L1 `202609120100+n`, L2 `202609120200+n`; triples
  identical by `(n,layer,column)` across B1/T1–T4/M-degree-3; degree-2 cols
  use entries 0–1; no selection.
- Rows: n64 L1 `(49,59,64)` / L2 `(43,52,64)`, scaled x2/x4 for n128/n256.
- Decoder: historical row-layered FFT-QSPA via `d5.bind_historical_decoder`,
  cold start, `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None`.
- Schedule: L1 then APP-propagated L2; oracle-L2 diagnostic only.
- Exact = full reconstructed Alice equality; syndrome separate, never upgrades
  exact; `syndrome_ok != exact` on APP is disagreement (isolated).
- Samples: one per `(n,block_seed)` via `d5.sample_matched_block`, reused
  byte-identically across arms.
- Seeds: canary `2026091000..03`, confirmation `2026091010..25`, scaling
  `2026091100..03`; nothing else.
- Budgets: 2500 calls / 12 h wall / 120 s per-call watchdog / RSS <2 GiB /
  no retry; beliefs chain at 61767ca2 (`invoke` transient carries `beliefs`)
  preserved verbatim.

## R1c allowed parallel-only additions (no semantic change)

- 18-worker decoder pool (20 logical cores, leave 2): `workers=18` full only
  when `workers * peak_rss_estimate < 2 GiB`; otherwise downgrade to 14/12/8
  by measured RSS and record chosen count + reason in `command_log.txt` and
  `manifest.json`. Main process generates all samples single-threaded before
  dispatch, then shares read-only (no mutation during parallel phase).
- Structure `arm x layer` parallel via `ProcessPoolExecutor` (16 tasks at
  n=64: 8 arms x 2 layers); assembly in `ARMS` order; per-task replay check
  (build twice, array equality) preserved; deterministic output identical to
  sequential build.
- T2 incremental vectorization/cache: adjacency bit-sets + `pair_counts`
  indexed map + `pair_to_cols` support reuse + O(1) degree update retained;
  no girth computation inside candidate loop; final girth follows packet §6
  (exact Tanner BFS, `NOT_COMPUTED` only when acyclic).
- Per-cell accounting unchanged + parallel-safe: each counted invocation
  records `worker_pid`, `wall_s`, `rss_bytes`, `watchdog_ok`; watchdog 120 s
  `poll` + terminate/respawn retained per worker; no retry (timeout/crash
  consumes cell).
- Chunked append, same UUID root: canary / confirmation / scaling each split
  so every chunk wall <1.5 h; `structure_records.csv` appends for scaling
  widths; `decoder_records.csv` flushed per chunk (append); single
  `manifest.json` / `summary.json` / `selected_arms.json` at end; one UUID
  root `workspace/d6_graph_mother_r1c_<uuid>/`, refuses overwrite.
- Evidence: six files + scalar-ID provenance, same `verify_command`
  recomputation (coverage/counts/separation/extrema/advancement/
  classification). Post-call fixes limited to evidence/report arithmetic.

## Non-goals (R1 prohibitions retained)

No `--phase`, formal G1 rerun/resume/recovery, VOID reads, G2/VAL/real,
parquet outside CAL-TRAIN, D5/src/experiments/tools edits, auth/promotion
changes, graph/block/coefficient/decoder/row search or tuning, retry,
push/reset/checkout/stash/clean/amend/rebase, decoder-dynamics.

## Files

- This addendum + `D6_GRAPH_MOTHER_PREREG_R1C.md` constitute commit 1 (R1c).
- Implementation diff (commit 2) touches only
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
  (T2 cache comment/vectorization),
  `scripts/v72p2d6_graph_mother_development.py` (parallel pool + chunking),
  `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (parallel
  equivalence test, task-owned basetemp only).
- Reviews (commit 3): `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1C.md`,
  `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1C.md` (self-written disclosure).

## R1c-A1 parallel-contract revision (frozen delta, mechanics only)

Status: `FROZEN_PREREG_R1C_A1`. Science (arms/seeds/rows/decoder/prior/
selection/terminal thresholds) unchanged. Seven fixes, else STOP:

1. `--workers` hard ceiling: effective `w <= requested` always; request
   8/12/14 never becomes 18; 1 stays sequential. Gating only downgrades.
2. Measured pool sizing: spawn `requested`, use startup actual RSS
   (main via `d5._rss_bytes()` + per-worker hello `rss`); no 90MiB hardcode
   (all-None stays at requested with `rss-unknown` logged). Effective is
   largest `w <= requested` with `w*per_worker_max + main < 2GiB`, else
   floor with over-budget logged; trim extras. Record requested/effective/
   main/each-worker/aggregate (pool + main sum) in `command_log.txt` +
   `manifest.json` via pure `select_effective_workers`.
3. Atomic dispatch reservation: `invoke()` reserves `call_idx` + call/wall
   budget inside the lock before dispatch (`setup + scientific + 1 <= 2500`
   and `now - t0 <= 12h`, else `budget_stop` + `StopIteration`); release
   lock only for the blocking call; re-acquire only to append with the
   reserved index. No check-release-run; concurrency never exceeds budgets.
   Skip placeholders (`call_idx=-1`) consume nothing.
4. Warmup accounting: each worker spawn/respawn warmup counts 1
   `setup_decoder_calls` under lock under the same total gate;
   `manifest.json`/`summary.json`/`command_log.txt` carry
   `setup_decoder_calls`/`scientific_calls`/`total`; `verify_command`
   checks `total <= 2500`. Warmup never mixes into scientific rows.
5. Per-phase incremental persistence: structure + every decoder chunk flush
   in frozen `call_idx` order (`flush()` + `os.fsync()`).
   `run_cells_parallel` returns `(cells, wall)`; any chunk `wall >= 5400s`
   sets `chunk_wall_blocked`, stops further dispatch, flushes completed
   phases, terminal `D6_GRAPH_CHUNK_WALL_BLOCKED` (blocking, overrides
   science classification; `classify_terminal` unchanged). Warning-only
   forbidden.
6. Fake-worker tests (task-owned basetemp, no real decoder): requested
   ceiling, budget-boundary concurrency, out-of-order stable order,
   aggregate RSS, phase flush, chunk-wall block.
7. Delete write-only `pair_to_mask` mirror (choice key uses
   `pair_counts`/`pair_to_cols` only); equivalence via unchanged key +
   T2 replay tests.

## R1c-A2 execution-safety closeout (frozen delta, mechanics only)

Status: `FROZEN_PREREG_R1C_A2`. Old A2 prompt void; this task text is the
sole contract. `a16d3184`/`fc447e12` body retained; science
(arms/seeds/rows/prior/decoder/mother/selection/scientific terminal
thresholds) unchanged. Nine items, else STOP:

- A2-01 three history roots verbatim `VOID_RETAINED_ZERO_REUSE`
  (`923a25897087495ab4605870e561f3cc`,
  `e8ee45a4669c4738bf7e96d926ba7e5c`,
  `f15cfa29baa2458e804c80a9f1045140`); name-only, no read/delete/move/use;
  fresh `workspace/d6_graph_mother_r1c_<uuid>/` only.
- A2-02 RSS fail-closed: single pilot measures RSS then sizes pool (no
  start-18-then-trim); main/pilot None → `D6_RSS_UNKNOWN_BLOCKED` before
  scientific calls; candidates include 1; `1+main >= 2GiB` →
  `D6_RSS_LIMIT_BLOCKED`; expansion re-samples each worker
  (unknown/over-limit stops); per-call/per-barrier worker/main/sampled
  aggregate + single/aggregate peaks; persist
  main/worker/aggregate/peaks/semantics; unknown never 0, single never
  masquerades as aggregate.
- A2-03 12h `deadline=t0+12h`; atomic remaining check before dispatch;
  `poll=min(120s,remaining)`; deadline arrival terminates task-owned with
  `wall_timeout=true`, no respawn/dispatch, terminal
  `D6_WALL_BUDGET_BLOCKED`; final wall overrun with other terminal → verify
  FAIL.
- A2-04 records carry
  `worker_pid/respawn_pid/timeout/wall_timeout/error`;
  `watchdog_ok=not timeout and not wall_timeout and wall<=120`; watchdog
  timeout respawns (failure no retry, warmup counts setup); wall timeout
  never respawns.
- A2-05 semantics renamed to same-UUID phase checkpoint rewrite (never
  append-only); each phase ordered rewrite + flush + fsync (fsync failure
  fail-closed); canary/confirm/scaling + StopIteration/blocks share finally
  checkpoint; `chunk>=5400s` → zero new dispatches.
- A2-06 `workers=1` scaling-confirm indent: `cc[point]` inside point loop,
  `conf_counts[arm]` inside arm loop outside point loop; fake proves
  f1.0/f1.2/square retained, parallel-consistent.
- A2-07 verify 15 independent rejections (call_idx continuity / semantic-key
  duplicate / calls consistency / ≤2500 / effective≤requested / RSS / wall /
  terminal / timeout-watchdog / PID / seed-domain / coverage / scaling
  recompute / manifest consistency / six-file+set).
- A2-08 fake/tmp-only coverage (RSS unknown / single-over-limit /
  pilot-downcore / runtime-over-limit / deadline<120s / dual-timeout
  separation / dual-PID / fsync-fail / StopIteration checkpoint / sequential
  three-point / malformed verify FAIL / seed pollution); `py_compile` three
  files + D6 focused + original seven-file suite (no perf-v38 800s); fresh
  `workspace/<uuid>` basetemp, delete only own.
- A2-09 land 1) A2 prereg/OpenSpec 2) implementation+tests 3) check A1/A2
  tasks then STOP for independent review (coder never writes review).

## R1c-A3 post-run verifier and terminal rework (frozen delta, verifier only)

Status: `FROZEN_PREREG_R1C_A3` (`D6_GRAPH_MOTHER_PREREG_R1C_A3.md` is the
contract; eight rules frozen there). Science and execution mechanics
unchanged; the A2 six-file root is immutable evidence. Two A2 verifier FAILs
(n-agnostic semantic key; canary/scaling mixing) plus 64 attempted degree
crashes under a stored `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` force this
amendment via OpenSpec, not silent patch:

- Identity key becomes `(n,arm,seed,point,mode)`; `call_idx` stays independent.
- Canary recompute: `n=64` + canary seeds only, per-cell
  `app=(L1.exact and L2-APP.exact)`, missing L2-APP ⇒ `app=False`.
- Scaling recompute: scaling seeds only, grouped per `n=128`/`n=256`;
  reproduces fallback dispatch, per-width sig/advancing (frozen
  `select_advancement`, stop-at-first-width), confirmation width, terminal
  inputs.
- Confirmation recompute: confirmation seeds at selected width only; empty
  stage labeled `EMPTY_NOT_EVIDENCE`, never observed safety.
- Attempted crash/nonfinite precedence: any counted crash/nonfinite forces a
  blocking recomputed terminal over recovery/no-recovery labels;
  `call_idx=-1` placeholders excluded.
- Degree `ValueError` ⇒ `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`; other
  attempted crash/nonfinite ⇒ `D6_GRAPH_ATTEMPTED_CELL_INVALID`; neither
  supports topology-no-recovery.
- Verifier stays pure read-only over any supplied root (hash-proven).
- Stored + recomputed terminals both printed with agreement flag;
  disagreement is fail-closed at the decision layer (recomputed governs;
  Pre-RESULT must route BLOCKED), while the mechanical VERIFY exit covers the
  15 checks — so A3-05 stays mechanical, A3-06 stays semantic.

Allowed paths: `scripts/v72p2d6_graph_mother_development.py` (verifier path
only), `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (10 A3 fake
tests), this addendum + prereg + tasks (commit 1), forensic report under the
D6 cycle dir (commit 2 with implementation). Mother module, execution
generation, historical artifacts: untouched.
