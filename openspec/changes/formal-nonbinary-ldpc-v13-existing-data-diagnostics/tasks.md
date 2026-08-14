# Tasks: V13 Existing-Data Nonbinary LDPC Diagnostics

Status: **PLAN FROZEN / P08 ACCEPTED / EXECUTION NOT AUTHORIZED** (2026-08-14).
P01--P08 were accepted by an independent read-only freeze review (zero
blockers; two WARNING-level items and three suggestions recorded for
correction before D05). Every D/R/I/E/A/C item remains unauthorized and
unchecked.

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

## Phase D — initial diagnostic-only work (main-thread authorized 2026-08-14: D01-D03 + DT0-DT2 only)

Gate: V13-P08 accepted (2026-08-14). D04 and D05 remain NOT authorized —
D04 requires DT0-DT2 to pass first and then a separate main-thread
authorization; D05 requires D04 results. No real-data decode is authorized.

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
- [ ] **V13-D04** After P08 and V13-DT0--V13-DT2 only, run unchanged V7 R1A `p=.20`
  once on 32 pre-registered bw200 development frames. Import binary V5 only as
  a read-only identity/control reference; label nearest-available controls
  when exact identity cannot be established. (DT0-DT2 passed 21/21; D04
  remains NOT authorized — requires separate main-thread authorization.)
- [ ] **V13-D05** Produce a root-cause report, retain all failures, and obtain
  independent review. Emit separate fields: `diagnosis_class` is exactly one
  of `interface`, `prior`, `decoder`, `code`, `mixed`, or `inconclusive`;
  `run_state` is `diagnosis_complete` for a supported single-factor class and
  `diagnosis_inconclusive` for `mixed`/`inconclusive`. An oracle/interface
  failure may already have set `run_state=implementation_interface_fault`.
  (NOT authorized — requires D04 results first.)

## Phase R — one-factor candidate (blocked until D05)

- [ ] **V13-R1** If and only if D05 emits `diagnosis_class=prior`, freeze one
  prior-only candidate with the same matrix, schedule, and checks; derive a
  cross-fitted public global prior without audit truth.
- [ ] **V13-R2** If and only if D05 emits `diagnosis_class=decoder`, freeze one
  decoder-only numerical or scheduling change with the same matrix, prior,
  and checks.
- [ ] **V13-R3** If and only if D05 emits `diagnosis_class=code`,
  freeze one finite graph/rate change with the same prior and decoder
  interface.
- [ ] **V13-R4** If D05 emits `diagnosis_class=mixed` or `inconclusive`, the
  run_state is `diagnosis_inconclusive`; stop and return to the planner. No
  mixed route or disguised V7/V10/V11 rerun is allowed.

## Phase I — future minimal implementation (not authorized)

- [ ] **V13-I01** Implement only the selected one-factor candidate under
  `comparison_bench/`; keep frozen baseline directories unchanged.
- [ ] **V13-I02** Bind diagnostic-only status, provenance, output-root, and
  Alice-isolation contracts without checksums/hash DAGs/signatures/locks.
- [ ] **V13-I03** Add explicit fake-runner entry points so tests cannot enter a
  production decoder, raw-data source, or official output root implicitly.

## Diagnostic engineering tests (before D04; not candidate implementation)

- [x] **V13-DT0** Compile/import, structural checks, tiny GF/syndrome math,
  oracle limits, and the D02 engineering oracle. (Done: 8 tests pass.)
- [x] **V13-DT1** Focused role-ledger, Alice-isolation, and telemetry
  hook-equivalence tests. (Done: 8 tests pass.)
- [x] **V13-DT2** Complete fake diagnostic lifecycle and decoder-free replay in
  a fresh `workspace/nbldpc_v13_<uuid>/` root with
  `pytest -p no:cacheprovider`. (Done: 5 tests pass; total 21/21.)

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

## Phase E — development screen (future, not authorized)

- [ ] **V13-E01** Freeze 64 bw200 development frames and run unchanged
  baseline plus the sole candidate once each. Continue only if at least 1/64
  is independently exact-corrected with zero forbidden/internal/accounting
  failures, syndrome consistency, and post-decode exact equality. Zero
  successes yields `failed_existing_data_feasibility` and freezes the route.
- [ ] **V13-E02** If E01 passes, freeze the candidate and prohibit further
  tuning or candidate substitution.

## Phase A — retrospective audit and closeout (future, not authorized)

- [ ] **V13-A01** Run the frozen candidate once on the 128 frame-identical V5
  control/audit frames. Use the suggested readiness gate (>=120/128 exact,
  zero forbidden failures, median <=120 s/frame, disclosure <=8.75
  bits/input-symbol with tag separated). Failure is
  `retrospective_non_ready`; pass is only `ready_for_fresh_confirmation`.
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
