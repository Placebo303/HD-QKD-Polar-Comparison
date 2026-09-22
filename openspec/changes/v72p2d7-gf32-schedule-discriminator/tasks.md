# D7-D schedule discriminator — tasks (R1)

Status: plan `R1` — T0 baseline/protected-state audit PASS; T1 freeze artifacts
written (this change, prereg, execution packet, `cycle_state.yaml`); T2–T7
pending. No D7-D scientific execution; all authorization false; no UUID; no
root; no push.

- [x] T0 — Baseline/protected-state audit at HEAD `1f472c2a` (Phase-A
  acceptance commit, branch `formal-ir-v72p1-addendum-clean`): D7-C cycle dir and
  root six files untouched; no `workspace/d7_d_*` root; D7-C accepted scope
  `D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC` present; all
  authorization false; R1d/G2 absent; protected roots inspected by
  names/sizes/mtime only; no VOID read; no Model-F content read
- [x] T1 — Freeze OpenSpec (proposal/design/tasks/spec) +
  `D7_D_PREREG_R1.md` + `D7_D_EXECUTION_PACKET_R1.md` + `cycle_state.yaml`
  BEFORE any real artifact/decoder observation; exact 256 matrix/order, schedules
  `[ROW_LAYERED, FLOODING]`, work-normalized metrics, five classifications, ten
  terminals, budgets, seven-file root, F01–F08 gate and reuse contract frozen;
  scoped local commit (plan); no push
- [x] T2 — Flooding certification F01–F08 against the accepted D7-A independent
  oracle on tiny synthetic fixtures, recorded in
  `D7_D_FLOODING_CERTIFICATION_R1.md`; failure terminal
  `D7_D_FLOODING_CERTIFICATION_FAIL` with minimal counterexample, no flooding
  patch, stop; then minimal implementation: new module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_schedule_discriminator.py`,
  new focused tests
  `comparison_bench/tests/test_v72p2d7_gf32_schedule_discriminator.py`, new
  script `scripts/v72p2d7_gf32_schedule_discriminator.py`; lazy local-source
  bind, DI for joint tensor/blocks/matrices/dual decoders/clock/RSS, seven-file
  writer + verifier, fail-before-first-call guards, frozen 256-call loop;
  production D7-C/v35/D5/D6/D7-A/D7-B read-only; no interface-rework import
- [x] T3 — Qualification S01–S22 (listed verbatim below): fake Model-F and fake
  decoders only; no real artifact content, no production decoder calls; fresh
  task-owned basetemps; skip perf-v38
- [x] T4 — Independent implementation review (source inspection + independent
  recomputation of representative schedule pairing, work arithmetic and
  classification cases); verdict `D7_D_IMPLEMENTATION_REVIEW_PASS`; one scoped
  rework max; scientific ambiguity returns to the main thread; record in
  `D7_D_IMPLEMENTATION_REVIEW_R1.md`
- [x] T5 — Independent Pre-EXECUTE review in the actual WSL environment:
  branch/scoped commits; exact 256 matrix and thresholds; accepted Model-F
  metadata/root presence without content read; dual external-cwd decoder
  sentinel reachability; live stdlib RSS positive with correct units; GNU
  timeout existence and rehearsal exit 124 if the environment changed; future
  UUID root absent; unauthorized exact-shape refusal before decoder/model/root;
  tests, protected metadata, all authorization false, R1d/G2 absent; exact
  future command; mandatory Pre-RESULT. Verdict
  `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`; record in
  `D7_D_PRE_EXECUTE_REVIEW_R1.md`
- [x] T6 — Closeout: scoped local commits (plan → certification/implementation →
  reviews → closeout, append-only); record parallel states
  `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` and
  `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP` only after
  both reviews PASS; all authorization false; no UUID; no root; no push; STOP
  (no D7-D execution)
- [x] T7 — Memory triage: durable readiness facts only (schedule matrix,
  metrics/classification/terminal rules, budgets, certification and review
  verdicts, deferred interface); no speculative results

## S01–S22 (packet §11, verbatim; verifiable acceptance criteria for T3)

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

## Acceptance matrix A01–A20 (packet §14, verbatim)

- A01 D7-C root/review/lifecycle verified immutable
- A02 D7-C accepted only under the §0 ceiling
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

Note: A01–A05 were satisfied by the preceding D7-C acceptance phase (Phase A,
committed at HEAD `1f472c2a`); the D7-D phases are bound by A06–A20.
