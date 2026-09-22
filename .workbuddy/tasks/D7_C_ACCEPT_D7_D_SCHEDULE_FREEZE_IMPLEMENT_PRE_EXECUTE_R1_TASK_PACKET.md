# D7-C acceptance + D7-D flooding-versus-layered readiness R1

## 0. Main-thread scientific adjudication

Accept the immutable D7-C run and independent review as:

`D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`

Accepted scope:

- 128/128 frozen single-layer calls completed, finite and internally coherent;
- exact and syndrome agreed on all calls; 43/128 exact;
- f=1.0: L1 marginal/oracle `0/16 -> 10/16`; L2 `0/16 -> 1/16`;
- f=1.2: L1 `3/16 -> 16/16`; L2 `0/16 -> 13/16`;
- f=1.2 has `STRONG_ORACLE_LIFT` in both layers;
- run terminal `D7_C_BIDIRECTIONAL_DEPENDENCE` is accepted as a bounded
  mechanism-classification result;
- no crash/nonfinite/resource/watchdog issue; RSS known and below 2 GiB;
- D7-C did not consume cross-layer returned beliefs and is not affected by the
  deferred D7-B APP-interface implementation.

Scientific interpretation ceiling:

- accepted: true other-layer symbols materially improve recovery under the
  frozen priors, matrices, decoder, disclosures, n=64 and 16 paired blocks;
- not accepted: that an implementable alternating/joint decoder can generate
  that information, bootstrap from marginal priors, achieve FER, improve
  leakage/key rate, qualify the code, or generalize beyond this matrix;
- f=1.0 L2 remains effectively unrecovered even with oracle (1/16), showing
  disclosure/finite-length difficulty remains alongside cross-layer dependence.

The next mainline stage is D7-D: isolate schedule only. Do not implement
alternating/joint BP yet. Layer-interface provenance implementation remains
mandatory before any future cross-layer APP route.

## 1. Authority

This packet authorizes:

1. durable D7-C result acceptance under §0;
2. D7-D OpenSpec/preregistration;
3. independent tiny-synthetic certification of the existing flooding decoder;
4. D7-D implementation and fake/unit qualification;
5. independent implementation and Pre-EXECUTE reviews;
6. scoped local commits and memory triage.

It authorizes zero D7-D scientific calls and zero real Model-F content reads.
It does not authorize D7-C rerun, R1d, G1/G2, any `--phase`, CAL/VAL/real/raw,
cross-layer APP or algorithm changes.

## 2. Baseline and protected evidence

- Branch `formal-ir-v72p1-addendum-clean`
- Expected starting HEAD `b4ba2896`
- D7-C UUID `94c0ea15-a786-4cb8-a991-6fec521cccae`
- Pre-RESULT verdict `D7_C_PRE_RESULT_REVIEW_PASS_R1`
- current gate `INDEPENDENT_D7_C_RESULT_ACCEPTANCE_R1`
- D7-C authorization false; attempts/completed `1/1`; decoder/result true
- D7-B and D7-C roots immutable
- Model-F root metadata only in this task
- R1d/G2 absent; all authorization false; no push

Read D7-C root twice by names/sizes/mtime around all work. Never modify it.
Preserve unrelated dirty/CRLF and pending SOP/workbuddy changes. Use explicit
manifests/content numstat. No clean/reset/checkout/stash/rebase/amend/broad
stage/push.

## 3. Phase A — D7-C durable acceptance

Create:

`docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/D7_C_RESULT_ACCEPTANCE_R1.md`

Transcribe §0 completely, include the four 2×2 paired tables, resource facts,
supported/unsupported claims and immutable UUID. Update D7-C `cycle_state.yaml`
with accepted-result fields and:

`next_gate: D7_D_SCHEDULE_DISCRIMINATOR_PACKET_FREEZE`

Keep every authorization false and promotion false. Append only the accepted
diagnostic and route decision to decision log and project memory. Commit:

`docs(d7-c): accept bidirectional-dependence diagnostic and route to D7-D`

Do this before D7-D implementation.

## 4. D7-D decision question

Holding every scientific input fixed, does independent flooding FFT-QSPA or
the certified current row-layered FFT-QSPA yield a reproducible exact-recovery
advantage?

Only schedule changes. Freeze identical:

- Model-F estimator and root;
- 16 D7-C paired blocks/seeds;
- f values, L1/L2 rows and mothers;
- four marginal/oracle prior conditions;
- syndrome, truth, labels, max_iter=90 and cold start;
- finite/exact/syndrome definitions and resource limits.

Do not simultaneously add damping, clipping, restart, min-sum, warm start,
graph changes, new priors, more disclosure or cross-layer feedback.

## 5. Flooding correctness prerequisite

Before freezing a scientific execution as ready, certify existing
`decode_flooding_fftqspa` against the accepted D7-A independent oracle on tiny
synthetic fixtures.

Required F01–F08:

- F01 direct check update remains the already certified kernel;
- F02 single-check full posterior equals exact enumeration within `1e-10`;
- F03 a two-check tree full posterior/MAP equals exact enumeration within
  `1e-10` after sufficient flooding iterations;
- F04 one flooding iteration matches an independently written flooding
  recurrence, not the production implementation;
- F05 iterations 1/2/3 on a small cycle match independent per-iteration beliefs
  within `1e-10`; do not compare loopy BP with MAP;
- F06 nonzero coefficients and syndromes include negative-direction controls;
- F07 cold start, normalization, stopping and `final_beliefs` current-state
  semantics are explicit, including iteration-0 `PRIOR_ONLY`;
- F08 no real Model-F, production evidence or formal root is read.

If any F item fails, terminal is
`D7_D_FLOODING_CERTIFICATION_FAIL`; preserve a minimal counterexample, do not
patch flooding in this packet, and do not continue to D7-D readiness.

## 6. Frozen D7-D matrix

Create OpenSpec:

`openspec/changes/v72p2d7-gf32-schedule-discriminator/`

Create cycle:

`docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/`

Freeze before any real artifact/decoder observation:

- schedules in order `[ROW_LAYERED, FLOODING]`;
- D7-C identities in their original order:
  16 seeds × 2 f × 4 conditions = 128 identities;
- two schedules per identity = exactly 256 calls;
- call order:

```text
for f in [1.0,1.2]:
  for seed in 2026091300..2026091315:
    for condition in [L1_MARGINAL,L1_ORACLE_U2,L2_MARGINAL,L2_ORACLE_U1]:
      ROW_LAYERED
      FLOODING
```

- same accepted estimator and direct prior formulas as D7-C;
- same matrices/rows/truth/syndrome for each paired schedule;
- max_iter=90, cold start; row-layered damping=1.0; flooding has no invented
  damping parameter;
- no early stop across identities; each decoder retains its own normal internal
  stopping;
- exactly 256 calls on normal completion; hard cap 256.

## 7. Work-normalized metrics

Iteration counts alone are not comparable. Persist per call:

- schedule/f/seed/condition/layer/rows/n;
- exact, independently recomputed syndrome, iterations, status, finite;
- symbol errors, unsatisfied checks;
- wall and RSS;
- number of full check-node updates = `rows × completed_iterations`, with
  iteration-0 explicitly zero;
- total check-edge updates using frozen matrix row degrees;
- current-belief confidence/entropy labeled with provenance, never posterior
  unless independently established.

Per identity paired result:

- layered-only exact, flooding-only exact, both, neither;
- syndrome-only analogues kept separate from exact;
- iteration difference, check-update difference, edge-update difference and
  wall ratio only when denominators are valid;
- no winner inferred from iteration count alone.

## 8. Frozen schedule classifications

For each `(f,layer,condition)` stratum of 16 blocks:

- `FLOODING_EXACT_ADVANTAGE`: flooding-only `>=4`, layered-only `<=1`;
- `LAYERED_EXACT_ADVANTAGE`: layered-only `>=4`, flooding-only `<=1`;
- `EXACT_TIE_HIGH`: both exact `>=12` and exclusive wins each `<=1`;
- `EXACT_TIE_LOW`: neither exact `>=12` and exclusive wins each `<=1`;
- `MIXED_SCHEDULE_EFFECT`: otherwise.

Run terminal priority:

1. `D7_D_PRE_EXECUTION_BLOCKED`
2. `D7_D_WATCHDOG_TIMEOUT_VOID`
3. `D7_D_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_D_RESOURCE_OVERRUN`
5. `D7_D_INCOMPLETE_CALL_MATRIX`
6. `D7_D_FLOODING_ADVANTAGE` — at least two strata flooding-advantage and no
   layered-advantage stratum
7. `D7_D_LAYERED_ADVANTAGE` — converse
8. `D7_D_SCHEDULE_DEPENDENT_MIXED` — both advantage directions appear
9. `D7_D_SCHEDULE_NO_EXACT_DIFFERENCE` — exact flags identical for all 128
   identities
10. `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`

These are route discriminators, not FER estimates. Report all eight stratum
labels even under a higher terminal.

## 9. Budgets and WSL environment

- exactly 256 scientific calls on normal completion
- per-call watchdog 120 s
- stored wall <=1500 s
- GNU outer timeout 1800 s + 30 s grace
- current-process RSS finite/positive and `<2GiB`
- stdlib `resource.ru_maxrss` KiB→bytes; no psutil
- fail before first call if RSS unavailable, Model-F invalid or target exists
- no retry/rerun/resume/concurrency

Freeze future command, do not run:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_<uuid>
```

## 10. Implementation and artifacts

Preferred new files:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_schedule_discriminator.py`
- `comparison_bench/tests/test_v72p2d7_gf32_schedule_discriminator.py`
- `scripts/v72p2d7_gf32_schedule_discriminator.py`

Required docs:

- `D7_D_PREREG_R1.md`
- `D7_D_EXECUTION_PACKET_R1.md`
- `D7_D_FLOODING_CERTIFICATION_R1.md`
- `D7_D_IMPLEMENTATION_REVIEW_R1.md`
- `D7_D_PRE_EXECUTE_REVIEW_R1.md`
- `cycle_state.yaml`

Future root `workspace/d7_d_schedule_discriminator_<uuid>/`, fresh/no-overwrite/
no-subdirs, exactly:

- `manifest.json`
- `decoder_records.csv`
- `paired_schedule.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Reuse D7-C fixture/prior identities through a narrow imported helper or exact
contract copy with tests. Do not modify D7-C or previous production modules.
Use DI/lazy binds. Import/help/dry-run/unauthorized must read no Model-F, bind no
decoder and create no root. Verifier reads only seven files and independently
recomputes pairs, strata and terminal.

## 11. Tests S01–S22

- S01 F01–F08 flooding certification
- S02 exact 256 identities/order
- S03 schedule pairs share all non-schedule inputs
- S04 accepted estimator and four priors equal D7-C contract
- S05 rows/mothers/seeds identical to D7-C
- S06 exact/syndrome separation
- S07 iteration-0 provenance labeling
- S08 check/edge update arithmetic
- S09 no winner from iterations alone
- S10 five stratum classifications and boundaries
- S11 ten terminal priorities and boundaries
- S12 256 call hard cap/no retry
- S13 120/1500/1800/2GiB gates
- S14 WSL stdlib RSS positive/fail-closed
- S15 seven-file schema/scalar-only/no subdirs/no overwrite
- S16 verifier detects missing/duplicate/unpaired/tampered records
- S17 lazy import/help/dry-run/unauthorized isolation
- S18 external-cwd dual-decoder sentinels reach exact functions without calls
- S19 fake full 256-call qualification for each terminal family
- S20 D7-A/C related regressions
- S21 protected-root lifecycle and D7-B/C immutability
- S22 no cross-layer APP, CAL/VAL/raw/phase/R1d/G1/G2 path

Use fake Model-F and decoders in tests. No real artifact content or production
decoder call. Fresh task-owned basetemps; skip perf-v38.

## 12. Independent reviews

Implementation reviewer independently checks flooding certification,
work-normalized arithmetic, exact pairing and code. PASS token:

`D7_D_IMPLEMENTATION_REVIEW_PASS`

One scoped implementation rework allowed; scientific ambiguity returns to main
thread.

Then separate WSL Pre-EXECUTE reviewer checks exact 256 matrix, Model-F metadata
only, dual sentinel reachability, RSS, GNU timeout rehearsal if environment
changed, target absence, unauthorized refusal, tests, protected roots and
future command. PASS token:

`D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`

No UUID, real Model-F read, scientific call or authorization flip.

## 13. Commits and next gate

Use scoped local commits:

1. D7-C acceptance;
2. D7-D OpenSpec/prereg/execution packet;
3. flooding certification + implementation/tests;
4. implementation review;
5. Pre-EXECUTE + closeout/memory.

After both reviews PASS:

- all authorization false;
- no D7-D root/UUID;
- `next_gate: D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`;
- retain `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP`;
- no push.

## 14. Acceptance matrix

- A01 D7-C root/review/lifecycle verified immutable
- A02 D7-C accepted only under §0 ceiling
- A03 four D7-C paired tables and terminal recorded exactly
- A04 no alternating/joint bootstrap claim
- A05 D7-C acceptance committed before D7-D implementation
- A06 F01–F08 flooding certification PASS
- A07 D7-D prereg precedes real observation
- A08 256 exact paired identities frozen
- A09 work-normalized metrics correct
- A10 stratum/terminal rules exact
- A11 seven-file writer/verifier qualified
- A12 S01–S22 PASS
- A13 related regression/compile PASS or unrelated failure isolated
- A14 independent implementation review PASS
- A15 independent Pre-EXECUTE PASS
- A16 zero real Model-F/decoder/scientific execution
- A17 protected roots unchanged; no D7-D/R1d/G2 root
- A18 all auth false/no UUID
- A19 scoped commits/no push/dirty tree preserved
- A20 memory triage contains only accepted/readiness facts

## 15. Hard STOP

STOP if D7-C evidence differs, flooding certification fails, D7-D requires any
non-schedule scientific change, real Model-F/decoder is reached, protected root
or auth changes, or review fails after one scoped rework. Do not execute D7-D.

## 16. Return

Report D7-C acceptance first, then F01–F08, 256 matrix, implementation/schema,
S01–S22, tests, reviews, WSL evidence, commits, roots/auth/no-push and gate.

End exactly:

`D7-C 双向依赖诊断已按受限口径接受；D7-D flooding-vs-layered 已完成冻结、实现与独立 Pre-EXECUTE，尚未授权、未执行，跨层接口实现仍 deferred，R1d、G1、G2 均未授权。`

