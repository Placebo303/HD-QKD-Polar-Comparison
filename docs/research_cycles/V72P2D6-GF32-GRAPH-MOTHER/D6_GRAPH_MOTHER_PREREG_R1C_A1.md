# D6 graph/mother — preregistration R1c-A1 (parallel-contract fix only)

Status: `FROZEN_PREREG_R1C_A1`. R1 §§4–6/§8 scientific freeze carries forward
verbatim (arms/seeds/rows/decoder/prior/selection/terminal thresholds
unchanged). R1c mechanics carry forward except the seven contract fixes below.
R1b PASS remains void; void144 roots quarantined, zero reuse. No §8 execution
under R1c-A1 before R1c-A1 implementation-review PASS + Pre-EXECUTE PASS +
explicit §8 authorization. This prereg + `R1C_parallel_revision.md` A1 delta +
`tasks.md` A1 tasks constitute commit 1 (no implementation).

## A1-1 --workers hard ceiling (never upscale)

- `requested` in (18,14,12,8,1) is a hard ceiling. Effective `w` satisfies
  `w <= requested` always. Request 8/12/14 with a tiny estimate stays
  8/12/14, never 18. Request 1 stays sequential. Gating only downgrades.

## A1-2 measured pool sizing + RSS recording (no 90MiB hardcode)

- Spawn `requested` workers, collect per-worker startup `rss` from hello +
  main-process RSS via `d5._rss_bytes()` (None recorded as unknown, never
  replaced by 90MiB).
- `per_worker = max(non-None worker rss)`; if all None, effective stays
  `requested` with `rss-unknown` logged (no estimate invented).
- Candidates `<= requested` from (18,14,12,8) descending; effective is the
  largest `w` with `w * per_worker + main_rss < 2GiB`; else floor to smallest
  candidate with over-budget logged. Trim extras (stop, task-owned only).
- Record in `command_log.txt` + `manifest.json`: `workers_requested`,
  `workers_effective`, `main_rss_bytes`, `worker_rss_bytes[]`,
  `aggregate_rss_bytes` (pool sum + main sum). Pure selector
  `select_effective_workers(requested, worker_rss, main_rss)` is unit-tested.

## A1-3 atomic dispatch reservation (lock-held, no check-release-run)

- `invoke()` reserves inside the lock before dispatch: under lock, if
  `setup + scientific + 1 > 2500` or `now - t0 > 12h` or `budget_stop`, set
  `budget_stop` and raise `StopIteration`; else `calls += 1`, assign reserved
  `call_idx`, release lock, dispatch, then re-acquire only to append the
  record with the reserved index + peak-RSS update. Concurrent threads cannot
  exceed 2500 calls / 12h wall. Skipped-APP placeholders (`call_idx=-1`)
  consume no budget.

## A1-4 warmup accounting (setup_decoder_calls, total <= 2500)

- Each worker spawn (initial + watchdog-respawn) runs one tiny-fixture
  warmup `_decode_block`; each counts as 1 `setup_decoder_calls` under lock
  with the same `setup + scientific + 1 <= 2500` gate. `manifest.json` +
  `summary.json` + `command_log.txt` carry `setup_decoder_calls`,
  `scientific_calls`, `total = setup + scientific`; `verify_command` checks
  `total <= 2500`. Scientific rows stay in `decoder_records.csv`; warmup never
  mixes into scientific rows.

## A1-5 per-phase incremental flush + explicit chunk-wall block terminal

- After structure build and after every decoder phase chunk (canary,
  per-arm confirmation, per-width scaling canary/confirmation), append/write
  records in frozen `call_idx` order, `flush()` + `os.fsync()`.
- `run_cells_parallel` returns `(cells, wall)`; caller checks each chunk:
  if `wall >= 5400s`, set `chunk_wall_blocked=true`, log
  `BLOCKED chunk-wall`, stop further dispatch, flush completed phases, and set
  terminal `D6_GRAPH_CHUNK_WALL_BLOCKED` (mechanics-only blocking terminal,
  overrides scientific classification; `classify_terminal` thresholds
  unchanged). Warning-only is forbidden.

## A1-6 fake-worker tests (task-owned basetemp only, no real decoder)

- New tests use fake workers/processes only: requested-ceiling values,
  budget-boundary concurrency (unique 1..N, never exceed), out-of-order
  completion with stable input-order assembly, aggregate RSS recording,
  phase-flush ordering + fsync presence, chunk-wall blocked terminal.
- No `--phase`/G1/G2/VAL/real/raw, no production roots, no real decoder.

## A1-7 pair_to_mask removal

- `pair_to_mask` bit-set mirror in `_build_T2_support` is write-only (choice
  key uses `pair_counts`/`pair_to_cols` only); R1c-A1 deletes it. Equivalence
  shown by unchanged T2 choice key + T2 replay tests.

## Freeze / scope / stop rules

- Science (arms B0/B1/T1–T4/M1/M2, coeff seeds L1 `202609120100+n` / L2
  `202609120200+n`, rows n64 L1 (49,59,64)/L2 (43,52,64) scaled x2/x4,
  `bind_historical_decoder` cold `max_iter=90`/`damping_alpha=1.0`/
  `warm_beliefs=None`, L1→APP-L2 + oracle-diagnostic-only, exact/syndrome
  separation, one sample per (n,seed) byte-identical, canary
  2026091000..03 / confirmation 2026091010..25 / scaling 2026091100..03,
  budgets 2500/12h/120s/<2GiB/no-retry, blind selection, terminal thresholds)
  unchanged. No `--phase`, G1/G2, VOID reads, VAL/real, parquet outside
  CAL-TRAIN, D5/src/experiments/tools edits, search/tuning/retry/push.
- Allowed implementation paths (commit 2): the three R1c files only.
- Any acceptance failure → STOP with raw output; no §8.
