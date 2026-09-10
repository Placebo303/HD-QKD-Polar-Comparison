# D7-C bidirectional cross-layer oracle — tasks (R1 + A1)

Status: plan `R1_A1`. This planning pass drafted the T1 documents (OpenSpec,
`D7_C_PREREG_R1.md`, `D7_C_EXECUTION_PACKET_R1.md`, `cycle_state.yaml`) without
any decoder call, Model-F content read, root, UUID or commit; the main thread
commits them as the first scoped commit. T0/T2–T7 are not started. No
authorization is granted.

- [ ] T0 — Baseline/protected-state audit at the Phase-P descendant of
  `212f69ba`: branch `formal-ir-v72p1-addendum-clean`; D7-B audit PASS and A1.3
  proposal PASS present; D7-B R2 root UUID
  `c605d1e6-8577-4c52-a865-12500fc8c964` immutable; all authorization false;
  R1d/G2 absent; no `workspace/d7_c_bidirectional_oracle_*` root; protected
  roots inspected by names/sizes/mtime only; no VOID read; no Model-F content
  read
- [ ] T1 — Freeze OpenSpec (proposal/design/tasks/spec) +
  `D7_C_PREREG_R1.md` + `D7_C_EXECUTION_PACKET_R1.md` + `cycle_state.yaml`
  BEFORE any real artifact/decoder observation; H03 estimator trace confirmed
  (unique accepted concentration estimator; rejected per-cell alternative and
  reason recorded); mother expressions and geometry disambiguation frozen;
  scoped local commit (plan); no push
- [ ] T2 — Minimal implementation: new module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_bidirectional_oracle.py`,
  new focused tests
  `comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py`, new
  script `scripts/v72p2d7_gf32_bidirectional_oracle.py`; lazy local-source
  bind, DI for joint tensor/blocks/matrices/decoder/clock/RSS, six-file writer
  + verifier, fail-before-first-call guards, frozen 128-call loop; production
  v35/D5/D6/D7-A/D7-B read-only; no interface-rework import
- [ ] T3 — Qualification C01–C20 (R1 §7, listed verbatim below): fake
  tensors/blocks only; no real Model-F content, no production decoder calls;
  fresh task-owned basetemps; no perf-v38
- [ ] T4 — Independent implementation review (source inspection + independent
  recomputation of representative prior/pairing cases); verdict
  `D7_C_IMPLEMENTATION_REVIEW_PASS`; one scoped rework max; scientific
  ambiguity returns to the main thread
- [ ] T5 — Independent Pre-EXECUTE review in the actual WSL environment with
  separate probe commands: branch/scoped commits and accepted D7-B/A1
  dependencies; exact 128 matrix and thresholds; accepted Model-F
  metadata/root presence without content read; external-cwd package/decode
  sentinel and Model-F loader sentinel separately; live stdlib RSS positive
  with correct units; GNU timeout existence and 3-second rehearsal exit 124;
  future UUID root absent; unauthorized exact-shape refusal before
  decoder/model/root; tests, protected metadata, all authorization false,
  R1d/G2 absent; direct four-prior construction and absence of
  `final_beliefs -> other layer` data flow; exact future command; mandatory
  Pre-RESULT. Verdict
  `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
- [ ] T6 — Closeout: scoped local commits (plan → implementation → reviews →
  closeout, append-only); record parallel states
  `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` and
  `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP` only after
  both reviews PASS; all authorization false; no attempts/results/completed
  fields; no push; STOP (no D7-C execution)
- [ ] T7 — Memory triage: durable readiness facts only (estimator ID, frozen
  matrix/mother/disclosures, budgets, review verdicts, deferred interface);
  no speculative results

## C01–C20 (R1 §7, verbatim; verifiable acceptance criteria for T3)

- C01 exact 128 identities and order
- C02 both f share the same 16 block identities
- C03 four prior formulas match literal tensor calculations
- C04 axis-swap negative controls fail
- C05 positivity/normalization/floor-once
- C06 correct L1/L2 rows and mother-prefix identity
- C07 oracle truth used only in prior construction and never persisted
- C08 marginal/oracle pairs share H, syndrome target, block and decoder config
- C09 all stratum thresholds and boundaries
- C10 all 11 run terminals and priority
- C11 128 hard cap and no retry
- C12 120/1500/1800/2GiB boundaries
- C13 WSL `resource` KiB→bytes conversion and fail-before-call
- C14 current-belief diagnostics never labeled posterior when unconditioned
- C15 six-file scalar-only schema/no subdirs/no overwrite
- C16 verifier detects duplicate/missing/unpaired/tampered scalar records
- C17 lazy import/help/dry-run/unauthorized isolation
- C18 external-cwd local-source bind sentinel reaches first decoder call with
  zero Model-F real read and zero root
- C19 protected-root lifecycle snapshots and G2/R1d absence
- C20 related D7-A/D7-B/D5 fake regression and py_compile

## Acceptance items

- H01 both reviews PASS (D7-B audit + A1.3 proposal)
- H02 primary MIXED outcome cited; D7-C never consumes cross-layer returned
  beliefs
- H03 accepted estimator uniquely traced; rejected alternative documented
- H04 prereg committed before real artifact/decoder observation
- H05 128 calls and paired identities frozen exactly
- H06 four prior formulas independently verified
- H07 oracle diagnostic/nonclaim boundary explicit
- H08 current-belief labeling respects the D7-B audit (A1 C14)
- H09 WSL stdlib RSS preflight prevents null telemetry
- H10 DI/lazy binding, no generalized framework
- H11 C01–C20 PASS
- H12 related regression/compile PASS
- H13 six-file writer/verifier qualification PASS
- H14 independent implementation review PASS
- H15 independent Pre-EXECUTE PASS
- H16 zero real Model-F content/decoder/phase/formal execution
- H17 protected roots unchanged; no D7-C/R1d/G2 root
- H18 all authorization false and no UUID generated
- H19 scoped local commits/no push/dirty tree preserved
- H20 memory triage contains only durable readiness facts

A1-01–A1-10 apply as recorded in the A1 packet §A1.5 (verified D7-B outcome and
gate; frozen eight architecture rulings; complete A/B/C alternatives; no hidden
implementation; sole allowed proposal-review PASS; direct-prior independence;
Phase-P commit precedes D7-C commits; R1 H01–H20 with A1 labels; zero
execution and all auth false; no push and R1d/G1/G2 absent).
