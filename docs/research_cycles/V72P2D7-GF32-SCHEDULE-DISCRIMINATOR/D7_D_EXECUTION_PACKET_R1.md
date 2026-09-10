# D7-D execution packet R1 (frozen; NOT authorized, NOT executed)

- Plan revision `R1`; prereg `D7_D_PREREG_R1.md` (committed before any real
  artifact/decoder observation).
- Status: the command below is **frozen but unauthorized and not executed**. No
  UUID was generated, no `workspace/d7_d_schedule_discriminator_*` root exists,
  no decoder was called, no Model-F binary content was read. All authorization
  fields are false.
- Governance structure: readiness requires flooding certification F01–F08 PASS,
  S01–S22 PASS, independent implementation review PASS, and independent
  Pre-EXECUTE review PASS; a future scientific execution additionally requires
  explicit verbatim authorization of the key below (one-shot). Pre-RESULT review
  is mandatory before any result publication.

## Exact future WSL command (do not run in this task)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_<uuid>
```

- `<uuid>` is a fresh UUID for the one authorized invocation (generated only at
  authorization time, not here). The outer `timeout` is GNU coreutils
  `timeout`, `-k 30` kill grace, `1800` wall seconds.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_D_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read or root
  creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_d_schedule_discriminator_<uuid>`; must not exist; the writer refuses
  overwrite and refuses subdirectories.

## Preflight and frozen call order

Preflight (before the first scientific call, fail-closed as
`D7_D_PRE_EXECUTION_BLOCKED`): cycle-state key true for this one UUID;
`--model-f-root` exactly the accepted root and valid when loaded; out-root a
fresh direct child of `workspace/` named
`d7_d_schedule_discriminator_<uuid>` and absent; stdlib RSS measurement finite,
positive and `< 2 GiB`; frozen identities built in memory. Any failure stops
with zero scientific calls.

Call order (exact, 256 calls):

```text
for f in [1.0, 1.2]:
  for seed in 2026091300 .. 2026091315 (ascending):
    for condition in [L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1]:
      ROW_LAYERED   # call 2k-1
      FLOODING      # call 2k
```

No early stop across identities; each decoder retains its own normal internal
stopping; no retry/rerun/resume/concurrency.

## Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/cycle_state.yaml`
  holds `d7d_execution_authorized: false` (`decoder_executed: false`,
  `result_created: false`; all other authorization flags false).
- The runner reads only this state file and refuses before any work, Model-F
  read, decoder bind or root creation while the key is false.
- A future verbatim user authorization flips the key for exactly one UUID and is
  consumed on the first decoder attempt regardless of outcome. No retry, rerun,
  resume or reuse. Import, `--help`, `--dry-run` and unauthorized runs bind no
  decoder, read no Model-F and create no root.
- `--dry-run` prints the frozen 256 identities/order (128 identities × 2
  schedules; `call_idx = 2*identity_idx - 1/2` for `ROW_LAYERED`/`FLOODING`) and
  exits without binding.

## Prerequisite gate (F01–F08)

Before this packet can be declared execution-ready, `decode_flooding_fftqspa`
must be certified in `D7_D_FLOODING_CERTIFICATION_R1.md` against the accepted
D7-A independent oracle on tiny synthetic fixtures per prereg §6 (F01–F08). Any
failure stops as `D7_D_FLOODING_CERTIFICATION_FAIL` with a minimal
counterexample preserved; flooding is not patched in this packet; readiness
does not continue.

## Budgets / stop rules (frozen)

- exactly 256 scientific calls on normal completion; hard cap 256; no early
  success stop; no replacement cell.
- Per-call watchdog 120 s; stored scientific wall `<= 1500 s`; outer GNU
  timeout `1800 s` + 30 s kill grace.
- Current-process WSL RSS via stdlib
  `resource.getrusage(RUSAGE_SELF).ru_maxrss` with explicit KiB→bytes
  conversion; finite positive measurement required **before the first call**;
  RSS `< 2 GiB`; no psutil.
- Zero retry/rerun/resume/concurrency; sequential execution only.
- Terminal priority T1–T10 exactly as prereg §9; all eight stratum labels
  recorded even under a higher-priority run terminal.
- Preflight failures (target exists, RSS unavailable/nonpositive, Model-F
  absent/invalid, root mismatch) block before any call
  (`D7_D_PRE_EXECUTION_BLOCKED`).

## Root contract

`workspace/d7_d_schedule_discriminator_<uuid>/` fresh, no subdirectories,
exactly seven compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `paired_schedule.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schema and evidence fields are frozen in prereg §8/§11. No raw beliefs, symbols,
priors, syndromes, block vectors or digests are persisted. Verify mode reads
only the seven files and independently recomputes pairing, paired counts, all
eight stratum labels, work arithmetic consistency and the terminal; it never
calls a decoder and never loads Model-F.

## Verify contract

- `decoder_records.csv` must contain exactly 256 unique `call_idx` rows with the
  frozen `schedule` at each index parity and the frozen identity mapping.
- `paired_schedule.csv` must contain exactly 128 rows whose two schedule records
  share all non-schedule inputs; paired counts must recompute from the 256 call
  rows; syndrome-only analogues stay separate from exact.
- `stratum_summary.csv` must contain exactly 8 rows; each label must recompute
  from the frozen first-match rules and be empty only for an incomplete stratum.
- `summary.json` terminal must recompute from the frozen priority list.
- Missing, duplicate, unpaired or tampered scalars fail verify with the affected
  identity/field.

## Mandatory reviews and Pre-RESULT gate

- Independent implementation review must PASS
  (`D7_D_IMPLEMENTATION_REVIEW_PASS`) after flooding certification; one scoped
  rework allowed; scientific ambiguity returns to the main thread.
- Independent WSL Pre-EXECUTE review must PASS
  (`D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`): exact 256
  matrix, Model-F metadata only, dual decoder sentinel reachability, RSS units,
  GNU timeout rehearsal if the environment changed, target absence, unauthorized
  refusal, tests, protected roots and the exact future command.
- Before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
  solidification or publication, an independent reviewer must re-check the
  frozen thresholds, schedule-only inputs, work-normalized arithmetic, exact/
  syndrome isolation, eight strata, terminal replay, seven-file schema and
  disclosure accounting against the actual seven files. Issues trigger
  immediate rework; no publish-then-patch. A FAIL blocks solidification.

## Boundaries

- Zero D7-D scientific calls and zero Model-F binary content reads until a
  future explicitly authorized execution; protected roots are inspected by
  names/sizes/mtime only.
- Zero CAL/VAL/parquet/raw/real/data reads; zero `--phase`; zero R1d/G1/G2; zero
  production v35/D5/D6/D7-A/D7-B/D7-C edits; zero interface-rework
  implementation; zero UUID; zero push.
- Predecessor roots immutable: D7-C root UUID
  `94c0ea15-a786-4cb8-a991-6fec521cccae`, D7-B R2 root, Model-F, G0/P0/G1, D6,
  structure and VOID roots.
- This packet authorizes no execution and no result acceptance. Next gate:
  `D7_D_IMPLEMENTATION_PENDING`; the final
  `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` value is set only at closeout
  after both independent reviews PASS. The interface implementation remains
  `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP` and D7-D does not depend on it.
