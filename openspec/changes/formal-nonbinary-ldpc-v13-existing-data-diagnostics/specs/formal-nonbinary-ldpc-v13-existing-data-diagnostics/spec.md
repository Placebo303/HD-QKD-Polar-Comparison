# Delta Specification: V13 Existing-Data Nonbinary LDPC Diagnostics

## ADDED Requirements

### Requirement: Retrospective evidence is not fresh evidence

The diagnostic lane SHALL label every artifact and outcome
`diagnostic_only` and `retrospective_reuse`. Existing frame and payload
identities already used by V4/V5 SHALL NOT be called fresh canary,
confirmation, qualification, promotion, or `observed_fresh_correction`.

#### Scenario: Existing data is reused

- **WHEN** a V13 diagnostic consumes an existing 10 dB frame or payload
  identity
- **THEN** its role and artifact SHALL state `retrospective_reuse`
- **AND** the result SHALL be ineligible for qualification or promotion

#### Scenario: All diagnostic checks pass

- **WHEN** every V13 diagnostic gate is green
- **THEN** the maximum state SHALL be `ready_for_fresh_confirmation`
- **AND** no fresh-data or promotion claim SHALL be emitted

### Requirement: Historical facts remain immutable controls

The V13 plan SHALL preserve the meanings of V7 R1A, V10 `failed_ensemble`,
V11 `failed_coupling`, and V12 `source_partition_blocked`. Binary V5's
384/384 result in the same 10 dB bw120/bw180/bw200 domain SHALL be used only as
a frame-difficulty/control reference; its leakage, prior, code, or model SHALL
NOT be copied.

#### Scenario: Prior failure is interpreted

- **WHEN** a root-cause report cites a predecessor
- **THEN** it SHALL cite the predecessor's frozen status without relabeling,
  rerunning, or treating it as a new route

### Requirement: Role ledger and primary stratum are frozen before decode

The lane SHALL reconstruct a complete frame/payload role ledger and mutually
exclusive `characterization`, `development`, and `retrospective_audit` sets.
`bw200` SHALL be primary; bw120/bw180 SHALL be deferred until after a bw200
root-cause decision. Ambiguous identity or role reconstruction SHALL produce
`blocked_role_ledger` and SHALL prohibit diagnostic decode.

#### Scenario: Ambiguous historical role

- **WHEN** a frame cannot be assigned to exactly one frozen role
- **THEN** the lane SHALL stop at `blocked_role_ledger`
- **AND** SHALL not silently borrow or overwrite a V5 role

### Requirement: Alice information is offline-only

Alice truth SHALL be allowed only for aggregate offline diagnostics and
post-hoc exact-equality checks. It SHALL NOT influence a prior, candidate,
stopping rule, retry, frame order, or same-frame parameter. Persistent public
telemetry SHALL NOT contain raw Alice/Bob arrays or per-position error masks.

#### Scenario: Truth reaches decoder control

- **WHEN** Alice symbols, frame SER, error locations, or verification feedback
  can affect decoding or selection
- **THEN** the run SHALL be `invalid_diagnostic_execution`

### Requirement: Diagnostics must separate channel, interface, and root cause

Before a candidate route, the lane SHALL plan no-decode channel
characterization, a tiny engineering oracle, optional telemetry equivalence,
and one unchanged V7 R1A `p=.20` baseline probe on 32 pre-registered bw200
development frames. D05 SHALL emit separate `diagnosis_class` and `run_state`
fields. `diagnosis_class` SHALL be exactly one of `interface`, `prior`,
`decoder`, `code`, `mixed`, or `inconclusive`; a supported single-factor class
has `run_state=diagnosis_complete`, mixed/insufficient evidence has
`run_state=diagnosis_inconclusive`, and an oracle/interface failure may
directly have `run_state=implementation_interface_fault`.

#### Scenario: Engineering oracle fails

- **WHEN** a noiseless/single-error/tiny-q/tiny-n field, mapping, syndrome, or
  wrapper oracle fails
- **THEN** `diagnosis_class` SHALL be `interface` and `run_state` SHALL be
  `implementation_interface_fault`
- **AND** no real-data decoder probe SHALL run

#### Scenario: Evidence is insufficient

- **WHEN** D01--D04 do not discriminate a single causal category
- **THEN** `diagnosis_class` SHALL be `inconclusive` and `run_state` SHALL be
  `diagnosis_inconclusive`
- **AND** no mixed parameter sweep SHALL be started

### Requirement: Diagnostic and candidate test tiers are distinct

Before D04, the lane SHALL complete diagnostic engineering tests
V13-DT0--V13-DT2: compile/tiny-oracle checks, role/Alice/telemetry-equivalence
checks, and a complete fake diagnostic/replay. After a one-factor candidate
is frozen and before E01, it SHALL complete candidate tests V13-IT0--V13-IT3:
candidate compile/tiny math, focused boundary/isolation/telemetry tests, fake
candidate replay, and scoped regression/frozen-output checks. D04 SHALL NOT
refer to candidate test tiers, and E01 SHALL be blocked until IT0--IT3 pass.

#### Scenario: Candidate tests run before diagnosis is complete

- **WHEN** a candidate implementation test tier (V13-IT0--V13-IT3) is invoked
  before D05 completes
- **THEN** the tier SHALL be skipped as out of order
- **AND** D04 SHALL not depend on candidate test results

### Requirement: Telemetry hook is behavior-equivalent

An optional V7 R1A diagnostic hook SHALL preserve hook-off decoded word,
status, and iteration count element-for-element. Hook-on SHALL not alter those
values and SHALL record only aggregate syndrome/check satisfaction, posterior
concentration/entropy, non-finite/normalization counters, and
stagnation/oscillation traces.

#### Scenario: Hook changes behavior

- **WHEN** hook-on and hook-off differ in decoded word, status, or iterations
- **THEN** the diagnostic execution SHALL be invalid and stop

### Requirement: Candidate routes are one-factor and post-diagnosis only

After D05 and a new reviewed amendment, V13 MAY select at most one route:
prior-only, decoder-only, or code-only. A prior-only route SHALL keep matrix,
schedule, and check count fixed; decoder-only SHALL keep matrix, prior, and
check count fixed; code-only SHALL keep prior and decoder interface fixed.
Mixed/inconclusive diagnosis SHALL prohibit all three routes.

#### Scenario: Multiple mechanisms are changed

- **WHEN** a candidate changes prior and matrix, or decoder and rate, together
- **THEN** the candidate SHALL be rejected as outside V13
- **AND** no development screen SHALL run

### Requirement: Development and retrospective gates are diagnostic gates

E01 SHALL use 64 frozen bw200 development frames and require at least 1/64
independent exact correction, zero forbidden/internal/accounting failures,
syndrome consistency, and post-decode exact equality to continue. A01 SHALL
use the 128 frame-identical V5 audit/control frames once; the suggested gate is
at least 120/128 exact corrections, zero forbidden failures, median at most
120 s/frame, and disclosure at most 8.75 bits/input-symbol with tags separate.
The E01 floor is not a performance gate, and A01 pass is only
`ready_for_fresh_confirmation`.

#### Scenario: E01 has zero exact corrections

- **WHEN** the candidate corrects 0/64 development frames
- **THEN** the state SHALL be `failed_existing_data_feasibility`
- **AND** the route SHALL freeze without tuning or retry

#### Scenario: A01 misses its audit gate

- **WHEN** the retrospective audit is below its frozen gate or has a forbidden
  failure
- **THEN** the state SHALL be `retrospective_non_ready`
- **AND** bw120/bw180 checks and fresh confirmation SHALL remain blocked

### Requirement: Outputs and lifecycle are additive and explicit

Future outputs SHALL be limited to the six-file diagnostic set under
`comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/`:
`data_role_ledger.json`, `channel_diagnostics.json`,
`diagnostic_outcomes.csv`, `decoder_telemetry.jsonl`,
`root_cause_report.json`, and `diagnostic_run_manifest.json`. Tests SHALL use
fresh `workspace/nbldpc_v13_<uuid>/` roots. Frozen `src/`, `experiments/`,
`tools/`, `results/`, and official `formal_ir_methods` roots SHALL remain
unchanged.

`diagnostic_outcomes.csv` SHALL include baseline rows, candidate-development
rows, and retrospective-audit rows, each carrying explicit `phase` and
`method` fields.

#### Scenario: Production output path is requested

- **WHEN** a diagnostic attempts to write an official qualification root or
  overwrite an existing artifact
- **THEN** the run SHALL be `invalid_diagnostic_execution`
- **AND** the existing evidence SHALL be retained unchanged

### Requirement: Declared state set and fresh-acquisition boundary

The only V13 `run_state` values SHALL be `plan_only`, `blocked_role_ledger`,
`implementation_interface_fault`, `diagnosis_complete`,
`diagnosis_inconclusive`,
`failed_existing_data_feasibility`, `retrospective_non_ready`,
`ready_for_fresh_confirmation`, and `invalid_diagnostic_execution`.
`diagnosis_class` SHALL be recorded separately with the six values defined
above and SHALL NOT be substituted for a `run_state`.
`promoted`, `qualified`, and `observed_fresh_correction` SHALL be forbidden.
New acquisition or formal qualification SHALL require a separate OpenSpec
change after a user decision.

#### Scenario: Fresh canary is requested

- **WHEN** the user wants a fresh canary, confirmation, qualification, or
  promotion
- **THEN** V13 SHALL stop at its current retrospective state
- **AND** a new change with new identities and a new authorization chain SHALL
  be required
