# D7-D schedule discriminator — proposal (freeze + implementation, no execution)

## What

Freeze and implement (without executing) a schedule-only discriminator at the
accepted n=64 GF32 operating point: with every scientific input held identical
to D7-C, compare the certified current row-layered FFT-QSPA against the existing
independent flooding FFT-QSPA on the 128 frozen D7-C identities, once per
schedule = exactly 256 calls, in a frozen order. The deliverable freezes this
OpenSpec change, `D7_D_PREREG_R1.md`, `D7_D_EXECUTION_PACKET_R1.md` and
`cycle_state.yaml`; implementation, flooding certification, qualification and
reviews follow under the later packet phases.

## Why

D7-C is accepted as
`D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`: under the frozen
priors, matrices, decoder, disclosures, n=64 and 16 paired blocks, true
other-layer symbols materially improve recovery (`f=1.0`: L1 `0/16 -> 10/16`,
L2 `0/16 -> 1/16`; `f=1.2`: L1 `3/16 -> 16/16`, L2 `0/16 -> 13/16`), while no
implementable alternating/joint decoder, bootstrap, FER, leakage or key-rate
claim is accepted, and `f=1.0` L2 remains effectively unrecovered even with
oracle (`1/16`). The next mainline question is whether the schedule alone —
certified row-layered versus independent flooding FFT-QSPA — produces a
reproducible exact-recovery advantage with every other scientific input fixed.
Only the schedule may change.

## Decision question and claim ceiling

Question: holding every scientific input fixed, does independent flooding
FFT-QSPA or the certified current row-layered FFT-QSPA yield a reproducible
exact-recovery advantage?

May establish: per-`(f,layer,condition)` stratum schedule classification from
the frozen five labels; one run terminal from the frozen ten-entry priority;
per-identity paired exact/syndrome outcomes and work-normalized differences.

May not establish: FER, leakage, reconciliation efficiency, key rate, protocol
recovery, cross-layer APP viability, interface acceptance, code qualification,
R1d/G1/G2 readiness, promotion, or any general GF32/NB-LDPC conclusion.
Schedule classifications are route discriminators, not success-rate or FER
estimates. The layer interface remains
`DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`.

## Scope

In scope: OpenSpec freeze (this change), `D7_D_PREREG_R1.md`,
`D7_D_EXECUTION_PACKET_R1.md`, `cycle_state.yaml`, and the later frozen phases:
flooding certification F01–F08, minimal module
(`comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_schedule_discriminator.py`),
focused tests
(`comparison_bench/tests/test_v72p2d7_gf32_schedule_discriminator.py`), runner
script (`scripts/v72p2d7_gf32_schedule_discriminator.py`), fake/unit
qualification, independent implementation review, independent Pre-EXECUTE
review, scoped local commits and memory triage.

Out of scope until a future explicit authorization: any D7-D scientific call,
any real Model-F binary content read, any UUID, any `workspace/d7_d_*` root,
R1d, G1/G2, CAL/VAL/parquet/raw/real/formal/VOID content reads, `--phase`,
production v35/D5/D6/D7-A/D7-B/D7-C edits, cross-layer APP or interface
implementation, push.

## Frozen scientific contract (full text in `D7_D_PREREG_R1.md`)

- **Only schedule changes.** Identical to D7-C: accepted Model-F estimator and
  root; the 16 D7-C paired blocks/seeds `2026091300..2026091315`; f `[1.0,1.2]`;
  L1/L2 rows and D5 mothers; the four marginal/oracle prior conditions;
  syndrome/truth/labels; `max_iter=90`; cold start; finite/exact/syndrome
  definitions and resource limits.
- **Forbidden simultaneous changes**: damping, clipping, restart, min-sum, warm
  start, graph changes, new priors, more disclosure, cross-layer feedback,
  cross-layer APP.
- **Schedules in order** `[ROW_LAYERED, FLOODING]`; 16 seeds × 2 f × 4
  conditions = 128 identities × 2 schedules = exactly 256 calls, hard cap 256,
  in the frozen order
  `for f in [1.0,1.2]: for seed in 2026091300..2026091315: for condition in [L1_MARGINAL,L1_ORACLE_U2,L2_MARGINAL,L2_ORACLE_U1]: ROW_LAYERED; FLOODING`.
  Each decoder retains its own normal internal stopping; no early stop across
  identities; row-layered `damping_alpha=1.0`, `warm_beliefs=None`; flooding is
  called with its frozen production shape and no invented damping/warm-start
  parameter.
- **Decoder identities**: `v35.decode_row_layered_fftqspa(h_matrix, priors,
  syndromes, max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=None)`
  (L636–644) and `v35.decode_flooding_fftqspa(h_matrix, priors, syndromes,
  max_iter=90, field=None)` (L529–535; `DEFAULT_MAX_ITER=30` never used;
  flooding declares no `damping_alpha`/`warm_beliefs`).
- **Priors/mothers/estimator**: exactly the D7-C constructions — direct four
  formulas from `J[u1,u2,b]`, one `d5._floor_renorm(..., 1e-15)` at the decoder
  boundary, D6-frozen D5-native mothers, `LAMBDA_STAR`, D5 graph seeds; narrow
  reuse of the D7-C module by imported helper or exact contract copy with
  tests; D7-C and previous production modules are never modified.
- **Work-normalized metrics**: per-call `check_node_updates = rows ×
  completed_iterations` (iteration 0 explicitly zero) and `check_edge_updates =
  sum(frozen matrix row degrees) × completed_iterations`; current-belief
  confidence/entropy with provenance labels; per-identity paired exact and
  separate syndrome-only outcomes; work differences/ratios only when
  denominators are valid; no winner inferred from iteration count alone.
- **Classifications**: five labels `FLOODING_EXACT_ADVANTAGE`,
  `LAYERED_EXACT_ADVANTAGE`, `EXACT_TIE_HIGH`, `EXACT_TIE_LOW`,
  `MIXED_SCHEDULE_EFFECT` per `(f,layer,condition)` stratum of 16 blocks; ten
  run terminals in exact priority order; all eight stratum labels reported even
  under a higher terminal.
- **Budgets**: exactly 256 calls on normal completion; per-call watchdog 120 s;
  stored wall `<= 1500 s`; GNU outer `timeout -k 30 1800`; current-process RSS
  `< 2 GiB` via stdlib `resource` KiB→bytes (no psutil); fail before the first
  call if RSS is unavailable, Model-F is invalid or the target exists; no
  retry/rerun/resume/concurrency.
- **Prerequisite gate**: flooding certification F01–F08 must PASS before
  readiness; failure terminal `D7_D_FLOODING_CERTIFICATION_FAIL` with a minimal
  counterexample preserved and no flooding patch in this packet.

## Files, root, command

New module, tests and script per Scope. Future root
`workspace/d7_d_schedule_discriminator_<uuid>/` fresh/no-overwrite/no-subdirs
with exactly `manifest.json`, `decoder_records.csv`, `paired_schedule.csv`,
`stratum_summary.csv`, `summary.json`, `report.md`, `command_log.txt`.
Frozen future WSL command (not run):

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_<uuid>
```

## Gate and closeout

- This freeze is committed before any D7-D artifact/decoder observation. All
  authorizations false; no UUID; no root; cross-layer interface implementation
  remains deferred.
- Readiness requires: F01–F08 PASS, S01–S22 PASS, independent implementation
  review `D7_D_IMPLEMENTATION_REVIEW_PASS`, independent Pre-EXECUTE review
  `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`, and the
  closeout gate `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.
- No push; scoped local commits only.

## Prohibitions

No D7-D scientific execution; no real Model-F content read; no decoder bind
outside fake/unit qualification; no R1d/G1/G2/CAL/VAL/raw/VOID access; no
`--phase`; no production v35/D5/D6/D7-A/D7-B/D7-C edits; no cross-layer APP; no
UUID; no push.
