# Tasks: V13 Existing-Data Nonbinary LDPC Diagnostics

Status: **PLAN FROZEN / P08 ACCEPTED / D05 EMITTED + REVIEW ACCEPTED / R3 FROZEN (2026-08-14)**.
P01--P08 accepted (zero blockers). D01-D04 + DT0-DT2 complete; D05 emitted
`diagnosis_class=code`, `run_state=diagnosis_complete` and the independent
read-only review returned ACCEPT (zero blockers, four non-blocking warnings).
R3 code-only candidate is frozen by amendment (connected simple check graph,
seed 20260818, Tanner girth >= 8; prior/decoder/checks/rate unchanged; E01
pre-registered 64 frames). R1/R2 locked; I/E/A/C items remain unchecked.

## Planning freeze (frozen via P08)

- [x] **V13-P01** Bind V7 R1A, V10 `failed_ensemble`, V11
  `failed_coupling`, V12 `source_partition_blocked`, and binary V5 control
  facts without rewriting prior claims.
- [x] **V13-P02** Reconstruct the complete existing 10 dB
  bw120/bw180/bw200 frame-role ledger, including frame and payload identity
  provenance.
- [x] **V13-P03** Freeze bw200 as the primary stratum and defer bw120/bw180
  to a post-bw200 cross-stratum check.
- [x] **V13-P04** Freeze mutually exclusive characterization, development,
  and retrospective-audit roles; use `blocked_role_ledger` if they cannot be
  reconstructed unambiguously.
- [x] **V13-P05** Freeze diagnostic telemetry fields and the Alice-information
  boundary; raw arrays and per-position masks remain excluded from persistent
  telemetry.
- [x] **V13-P06** Freeze additive output paths, resource/test roots, no-retry
  and no-overwrite rules, and the invalid-diagnostic stop conditions.
- [x] **V13-P07** Freeze the root-cause decision table and the one-factor
  successor boundary.
- [x] **V13-P08** Obtain an independent read-only freeze review of P01--P07,
  the data-role contract, telemetry schema, thresholds, and claim boundary.
  (Done 2026-08-14: reviewer-go returned ACCEPT, zero blockers; non-blocking
  corrections below are required before D05.)

## Phase D — initial diagnostic-only work (main-thread authorized 2026-08-14: D01-D04 + DT0-DT2; D05 remains unauthorized)

Gate: V13-P08 accepted (2026-08-14). D04 required DT0-DT2 to pass first and
then a separate main-thread authorization (granted 2026-08-14). D05 requires
D04 results and a separate main-thread authorization; no decoder execution
beyond the 32 pre-registered D04 baseline frames is authorized.

- [x] **V13-D01** Produce no-decode channel characterization: raw SER,
  GF-symbol differences, bit-plane mismatch, burst/run/position aggregates,
  QSC `p=.20` calibration/NLL mismatch, and empirical conditional entropy or
  necessary-leakage lower bound. Do not call it a Shannon or finite-length
  proof. (Done 2026-08-14: run v13_d01_20260814, 128 bw200 characterization
  frames, aggregates only.)
- [x] **V13-D02** Run the engineering oracle on noiseless, single-error, and
  tiny-q/tiny-n cases, including exact field/mapping/syndrome/wrapper checks.
  Any failure yields `run_state=implementation_interface_fault` with
  `diagnosis_class=interface` and stops before real decode. (Done: oracle
  implemented, DT0 covers all cases, pass.)
- [x] **V13-D03** Implement and test an optional V7 R1A diagnostic hook. Hook
  off must be element-for-element equivalent to the original return; hook on
  must not alter decoded word, status, or iterations. Persist only aggregate
  internal traces and never Alice error locations. (Done: wrapper/adapter,
  equivalence verified, V7 sources byte-unchanged.)
- [x] **V13-D04** After P08 and V13-DT0--V13-DT2 only, run unchanged V7 R1A `p=.20`
  once on 32 pre-registered bw200 development frames. Import binary V5 only as
  a read-only identity/control reference; label nearest-available controls
  when exact identity cannot be established. (Done 2026-08-14: main-thread
  authorized; run `v13_d04_20260814` executed exactly once, six-file package
  at `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13_d04_20260814/`;
  outcomes 8/32 `syndrome_consistent` + `exact_correct` (all at iteration 1),
  24/32 `decode_failed` at the iteration limit, zero `decoder_error`, zero
  exact mismatches, zero non-finite/normalisation failures; strict read-only
  verifier PASS; D04-lane engineering tests 27/27.)
- [x] **V13-D05** Produce a root-cause report, retain all failures, and obtain
  independent review. Emit separate fields: `diagnosis_class` is exactly one
  of `interface`, `prior`, `decoder`, `code`, `mixed`, or `inconclusive`;
  `run_state` is `diagnosis_complete` for a supported single-factor class and
  `diagnosis_inconclusive` for `mixed`/`inconclusive`. An oracle/interface
  failure may already have set `run_state=implementation_interface_fault`.
  (Done 2026-08-14: first emission `v13_d05_20260814` was invalidated by a
  decision-machinery defect — see the sibling
  `v13_d05_20260814_invalid_execution_notice.json`; corrected emission
  `v13_d05_20260814_corrected` emits `diagnosis_class=code`,
  `run_state=diagnosis_complete`, successor R3 code-only, prior documented as
  co-factor; strict read-only verifier PASS. Decisive evidence: the frozen R1A
  graph is 85 disconnected 2-check components (Tanner girth 4, d_min 3) and
  the structural ceiling over the 32 D04 frames is 0.75 == observed failure
  fraction 0.75 with perfect frame-level correspondence (24/24 failed frames
  contain a >=2-error component; 8/8 exact-correct frames contain none).
  Independent read-only review: **ACCEPT 2026-08-14, zero blockers**
  (reviewer-go; five tasks completed read-only; decision reproduced
  exactly; four non-blocking warnings recorded in the decision-log).

## Phase R — one-factor candidate (D05 = code; R3 frozen by amendment 2026-08-14)

- [ ] **V13-R1** prior-only: LOCKED — D05 emitted `code`, not `prior`.
- [ ] **V13-R2** decoder-only: LOCKED — D05 emitted `code`, not `decoder`.
- [x] **V13-R3** code-only: D05 `diagnosis_class=code`; ONE finite graph/rate
  property change frozen by amendment (2026-08-14, main-thread authorized):
  replace the degenerate frozen graph (85 disconnected 2-check components,
  Tanner girth 4) with a CONNECTED simple check graph — 170 check nodes, 256
  variable edges, all variables degree 2, check degrees 168x3 + 2x4, no
  parallel edges, check-graph girth >= 4 (Tanner girth >= 8) — deterministic
  seeded construction with frozen seed 20260818 (smallest seed passing the
  gates). Prior (QSC p=.20), decoder interface, check count 170, n=256, rate
  and max_iter=100 unchanged. New identity `nbldpc_v13_r3_code_v1`.
- [ ] **V13-R4** mixed/inconclusive: not applicable (D05 = code).

## Phase I — minimal implementation (R3 candidate; complete 2026-08-14, IT0-IT3 46/46)

- [x] **V13-I01** Implement only the selected one-factor candidate under
  `comparison_bench/` (R3 codebook module `nbldpc_v13_r3_code_v1` + E01 lane);
  keep frozen baseline directories unchanged. (Done: `nonbinary_v13_r3_candidate.py`
  + `run_e01` + CLI `e01`; frozen `src/`/`experiments/`/`tools/`/`results/`
  zero-diff.)
- [x] **V13-I02** Bind diagnostic-only status, provenance, output-root, and
  Alice-isolation contracts without checksums/hash DAGs/signatures/locks.
  (Done: R3 canonical manifest, per-decoder syndrome separation, six-file
  contract, E01 verify branch.)
- [x] **V13-I03** Add explicit fake-runner entry points so tests cannot enter a
  production decoder, raw-data source, or official output root implicitly.
  (Done: `run_e01` accepts explicit `baseline_decode`/`candidate_decode`
  runners; IT2 uses fake runners, IT3 verifies real-tiny wiring; official
  output root untouched by tests.)

## Diagnostic engineering tests (before D04; not candidate implementation)

- [x] **V13-DT0** Compile/import, structural checks, tiny GF/syndrome math,
  oracle limits, and the D02 engineering oracle. (Done: 8 tests pass.)
- [x] **V13-DT1** Focused role-ledger, Alice-isolation, and telemetry
  hook-equivalence tests. (Done: 8 tests pass.)
- [x] **V13-DT2** Complete fake diagnostic lifecycle and decoder-free replay in
  a fresh `workspace/nbldpc_v13_<uuid>/` root with
  `pytest -p no:cacheprovider`. (Done: 5 tests pass; total 21/21. 2026-08-14
  D04 lane: DT3 tests added for the baseline-probe lane — deterministic
  pre-registration, fake lifecycle + read-only verify, authorization tamper,
  Alice boundary, no-overwrite, frozen failure packages — total 27/27.)

## Candidate implementation tests (before E01; future only)

- [ ] **V13-IT0** Compile/import, structural checks, and tiny math for the
  single selected candidate.
- [ ] **V13-IT1** Focused unit/boundary, Alice-isolation, role-ledger,
  hook-equivalence, no-overwrite, failure, and telemetry-tamper tests.
- [ ] **V13-IT2** Complete fake candidate diagnostic lifecycle and decoder-free
  replay in a fresh `workspace/nbldpc_v13_<uuid>/` root.
- [ ] **V13-IT3** Scoped regression, frozen-directory checks, dirty-worktree
  scope review, output-root absence, and proof that no official qualification
  output was created. E01 is blocked until IT0--IT3 pass.

## Phase E — development screen (2026-08-14: E01 PASSED, E02 done)

- [x] **V13-E01** Freeze 64 bw200 development frames and run unchanged
  baseline plus the sole candidate once each. Continue only if at least 1/64
  is independently exact-corrected with zero forbidden/internal/accounting
  failures, syndrome consistency, and post-decode exact equality. Zero
  successes yields `failed_existing_data_feasibility` and freezes the route.
  (Done 2026-08-14, run `v13_e01_20260814`: candidate `nbldpc_v13_r3_code_v1`
  exact-corrected **64/64** on the pre-registered frames; baseline (unchanged
  V7 R1A) 13/64; zero forbidden/internal/accounting failures; syndrome
  consistency and post-decode exact equality on all rows; gate PASSED;
  strict read-only verifier PASS.)
- [x] **V13-E02** If E01 passes, freeze the candidate and prohibit further
  tuning or candidate substitution. (Done: the candidate was already frozen
  by the R3 amendment before E01; no tuning, no substitution occurred.)

## Phase A — retrospective audit and closeout (2026-08-14: A01 running)

- [ ] **V13-A01** Run the frozen candidate once on the 128 frame-identical V5
  control/audit frames. Use the suggested readiness gate (>=120/128 exact,
  zero forbidden failures, median <=120 s/frame, disclosure <=8.75
  bits/input-symbol with tag separated). Failure is
  `retrospective_non_ready`; pass is only `ready_for_fresh_confirmation`.
  (Running: run id `v13_a01_20260814`, candidate-only pre-registered, 128
  frames.)
- [ ] **V13-A02** Only after bw200 A01 passes, perform the pre-registered
  read-only bw120/bw180 cross-stratum check; do not promote.
- [ ] **V13-C01** Complete independent acceptance and mandatory memory triage;
  preserve all diagnostic failures and decide separately whether to open a
  new fresh-acquisition/qualification change.

## Diagnostic artifact contract

The six-file additive package uses `diagnostic_outcomes.csv`. Its rows cover the unchanged baseline, candidate
development, and retrospective audit, each with explicit `phase` and `method`
fields; all rows remain `diagnostic_only`/`retrospective_reuse`.

## Stop rule

Any ambiguous role, oracle/interface failure, Alice-information leak, hook
equivalence failure, missing denominator, retry, output-root violation,
unclassified failure, or insufficient root-cause evidence freezes the current
artifact. The resulting state is one of the declared diagnostic states; it is
never `promoted`, `qualified`, or `observed_fresh_correction`.

The allowed `run_state` values are `plan_only`, `blocked_role_ledger`,
`implementation_interface_fault`, `diagnosis_complete`,
`diagnosis_inconclusive`, `failed_existing_data_feasibility`,
`retrospective_non_ready`, `ready_for_fresh_confirmation`, and
`invalid_diagnostic_execution`. The separate `diagnosis_class` values are
`interface`, `prior`, `decoder`, `code`, `mixed`, and `inconclusive`.
