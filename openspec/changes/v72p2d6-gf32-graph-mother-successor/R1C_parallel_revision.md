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
