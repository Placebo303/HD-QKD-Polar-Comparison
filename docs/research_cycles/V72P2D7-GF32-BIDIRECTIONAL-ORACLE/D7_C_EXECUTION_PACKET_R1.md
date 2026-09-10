# D7-C execution packet R1 (frozen; NOT authorized, NOT executed)

- Plan revision `R1_A1`; prereg `D7_C_PREREG_R1.md` (committed before any real
  artifact/decoder observation).
- Status: the command below is **frozen but unauthorized and not executed**.
  No UUID was generated, no `workspace/d7_c_bidirectional_oracle_*` root exists,
  no decoder was called, no Model-F binary content was read. All authorization
  fields are false.

## Exact future WSL command (do not run in this task)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_<uuid>
```

- `<uuid>` is a fresh UUID for the one authorized invocation (generated only
  at authorization time, not here). The outer `timeout` is GNU coreutils
  `timeout`, `-k 30` kill grace, `1800` wall seconds.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_C_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read or root
  creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_c_bidirectional_oracle_<uuid>`; must not exist; the writer refuses
  overwrite and refuses subdirectories.

## Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/cycle_state.yaml`
  holds `d7c_execution_authorized: false` (`decoder_executed: false`,
  `result_created: false`; no attempts/results/completed fields).
- The runner reads only this state file and refuses before any work, Model-F
  read, decoder bind or root creation while the key is false.
- A future verbatim user authorization flips the key for exactly one UUID and
  is consumed on the first historical-decoder attempt regardless of outcome.
  No retry, rerun, resume or reuse. Import, `--help`, `--dry-run` and
  unauthorized runs bind no decoder, read no Model-F and create no root.
- `--dry-run` prints the frozen 128 identities/order and exits without
  binding.

## Budgets / stop rules (frozen)

- `<= 128` scientific calls (exactly 128 on normal completion); no early
  success stop; no replacement cell.
- Per-call watchdog 120 s; stored scientific wall `<= 1500 s`; outer GNU
  timeout `1800 s` + 30 s kill grace.
- Current-process WSL RSS via stdlib
  `resource.getrusage(RUSAGE_SELF).ru_maxrss` with explicit KiB→bytes
  conversion; finite positive measurement required **before the first call**;
  RSS `< 2 GiB`; no psutil.
- Zero retry/rerun/resume/reuse; sequential execution only.
- Terminal priority T1–T11 exactly as prereg §10; all stratum labels recorded
  even under a higher-priority run terminal.
- Preflight failures (target exists, RSS unavailable/nonpositive, Model-F
  absent/invalid, root mismatch) block before any call
  (`D7_C_PRE_EXECUTION_BLOCKED`).

## Root contract

`workspace/d7_c_bidirectional_oracle_<uuid>/` fresh, no subdirectories, exactly
six compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `paired_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schema and evidence fields are frozen in prereg §9. No raw beliefs, symbols,
priors, syndromes or block vectors are persisted. Verify mode recomputes
schema, 128-identity uniqueness, pair matching, counts/outcomes, stratum labels
and terminal from the six files alone; it never calls the decoder and never
loads Model-F.

## Mandatory Pre-RESULT review

Before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
solidification or publication, an independent reviewer must re-check the
frozen thresholds, prior/pair construction, `exact`/`syndrome` isolation
(syndrome never upgrades exact), per-stratum breakdown, evidence schema,
disclosure accounting and terminal replay against the actual six files.
Issues trigger immediate rework; no publish-then-patch. A FAIL blocks
solidification.

## Boundaries

- Zero Model-F binary content reads until a future explicitly authorized D7-C
  execution; in this task, protected roots are inspected by names/sizes/mtime
  only (and none were inspected by the planning pass).
- Zero CAL/VAL/parquet/raw/real data reads; zero `--phase`; zero R1d/G1/G2;
  zero production v35/D5/D6/D7-A/D7-B edits; zero interface-rework
  implementation; zero UUID; zero push.
- Predecessor roots immutable: D7-B R2 root UUID
  `c605d1e6-8577-4c52-a865-12500fc8c964`, Model-F, G0/P0/G1, D6, structure and
  VOID roots.
- This packet authorizes no execution and no result acceptance. Next gate:
  `D7_C_IMPLEMENTATION_AND_REVIEWS`; the final
  `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` value is set only at closeout
  after both independent reviews PASS. The interface implementation remains
  `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP` and D7-C does not depend on it.
