# Design: V13 Existing-Data Nonbinary LDPC Diagnostics

## 1. Scientific question and evidence boundary

V13 asks: **why did the existing finite nonbinary LDPC routes fail, and is
there one falsifiable, one-factor improvement worth testing?** It does not ask
whether the method is qualified on new data.

The data boundary is explicit:

1. The 10 dB Type-II q=1024 Gray 256-symbol pool is sufficient for
   retrospective diagnostics because it contains 768 bw200 rows (and the
   corresponding bw120/bw180 strata) with Alice/Bob pairs that can be checked
   offline.
2. Those frame/payload identities are already present in V4/V5 locks and
   roles. They are therefore not fresh canary or confirmation identities.
3. Every V13 artifact and status is labelled `diagnostic_only` and
   `retrospective_reuse`. Even an all-green result can reach only
   `ready_for_fresh_confirmation`.
4. V12 remains `source_partition_blocked`; V13 neither reopens it nor runs
   X01/X02. New acquisition and formal qualification are a later user choice
   under a separate OpenSpec change.

The predecessor facts are controls, not tunable targets:

| predecessor | frozen meaning in V13 |
|---|---|
| V7 R1A | previously failed its synthetic p=.20/.30 canaries and has no real-data evidence; do not rewrite or rerun its route |
| V10 | `failed_ensemble`; no ensemble winner is silently imported |
| V11 | `failed_coupling`; no coupling hypothesis is reopened |
| V12 | `source_partition_blocked`; freshness, not a decoder outcome |
| binary V5 | 384/384 in the same 10 dB bw120/bw180/bw200 domain, 128/128 per layer, used only as a frame-difficulty/control reference |

Binary V5 does not imply that a nonbinary decoder should succeed. Its leakage,
prior, matrix, and model must not be copied into V13.

## 2. Frozen data roles and strata

P02 reconstructs a complete frame-role ledger from the locally discoverable
10 dB pool, V4 transfer locks, V5 development/partition locks, V5 sealed
real frames, and any other identity-bearing formal package. The ledger records
role, source path, frame identity, payload identity, stratum, and provenance;
it does not expose raw arrays in public telemetry.

P03 sets `bw200` as the primary stratum. `bw120` and `bw180` are not a second
optimization opportunity: they may be inspected only after a bw200 root-cause
decision and only as a pre-registered cross-stratum check.

P04 attempts to construct mutually exclusive sets:

- `characterization`: frames used only for aggregate channel statistics;
- `development`: existing V5 development frames repurposed for NB diagnostic
  development, never for formal confirmation;
- `retrospective_audit`: the 128 previously sealed V5 real frames with
  frame-identical identities, used to audit a frozen candidate after E01/E02.

No row may occupy two roles. If historical role or identity information cannot
be reconstructed without ambiguity, the state is `blocked_role_ledger` and no
diagnostic decode is allowed. The preferred allocation reuses V5 development
as NB development and V5 sealed real frames as the frame-identical audit;
that preference is not permission to overwrite or relabel V5 evidence.

## 3. Information and telemetry boundary

Alice truth may enter only two offline operations: aggregate diagnostic
statistics and post-hoc exact equality against a returned word. It may not
enter a decoder prior, candidate selection, stopping rule, retry, frame
ordering, or same-frame parameter choice. A public or persistent telemetry
record must never copy raw Alice/Bob arrays or a per-position error mask.

The future optional diagnostic hook records only aggregates and decoder-
internal traces:

- per-iteration syndrome residual/check-satisfaction counts;
- posterior concentration or entropy aggregates;
- normalization, NaN, underflow, and non-finite counters;
- stagnation/oscillation indicators;
- status and iteration count.

Hook-off must return the original V7 R1A word, status, and iteration count
element-for-element. Hook-on may add telemetry but must not change decoded
word, status, or iterations. The hook is a design item in D03, not an
authorization to alter V7 code in this planning turn.

## 4. Frozen planning phases

### Phase P — planning and role freeze

The following are drafted in this change and await P08 independent review:

- **P01** bind V7--V12 and binary V5 facts and evidence boundaries;
- **P02** rebuild the complete three-stratum frame-role ledger;
- **P03** choose bw200 primary and defer other strata;
- **P04** build mutually exclusive characterization/development/audit sets;
- **P05** freeze telemetry schema and Alice-information boundary;
- **P06** freeze resources, additive output root, and stop rules;
- **P07** freeze the root-cause decision table;
- **P08** independent read-only freeze review.

P08 is the only decision requested by this proposal. No P item is accepted as
executed until the main thread records the review.

### Phase D — initial diagnostic-only request after P08

Phase D is the first possible execution request, but is not authorized now.

- **D01 channel characterization, no decode**: raw SER distribution, GF
  symbol-difference distribution, bit-plane mismatch, burst/run/position
  aggregates, QSC `p=.20` calibration/NLL mismatch, and empirical conditional
  entropy/necessary leakage lower bound. These are empirical diagnostics, not
  Shannon or finite-length proofs. A read-only structural short-cycle/girth
  analysis of the frozen V7 R1A graph may be computed offline as D01-adjacent
  evidence for the `code` root-cause row; it does not change any D task
  boundary.
- **D02 engineering oracle**: noiseless, single-error, and tiny-q/tiny-n
  syndrome cases plus a small-instance exact oracle for field, mapping,
  syndrome, and wrapper semantics. Any failure is
  `implementation_interface_fault` and stops before real decode.
- **D03 telemetry equivalence**: implement and test the optional V7 R1A hook
  under the hook-off/hook-on contract above; no raw arrays or error masks are
  persisted.
- **Diagnostic engineering tests**: before D04, complete the dedicated
  V13-DT0--V13-DT2 diagnostic engineering gates (defined below). These are
  not candidate-implementation tests and do not authorize a route change.
- **D04 frozen baseline probe**: only after P08 and V13-DT0--V13-DT2 pass, run the
  unchanged V7 R1A `p=.20` baseline exactly once on 32 pre-registered bw200
  development frames (carved from the V5 development partition
  `development_partition_ranks:[128,639]` = 512 frames per stratum, disjoint
  from the 128 sealed frame-identical audit frames). V5 is a read-only
  frame-identity control; if exact identity cannot be established, label it
  `nearest-available control`.
- **D05 root-cause report and independent review**: choose only one of the
  declared `diagnosis_class` values in the decision table and emit a separate
  `run_state`; insufficient evidence is a `diagnosis_inconclusive` run.

Diagnostic engineering tests are frozen as:

- **V13-DT0** compile/import, structural checks, tiny GF/syndrome math, and
  the D02 noiseless/single-error/tiny-q/tiny-n engineering oracle;
- **V13-DT1** focused role-ledger, Alice-isolation, and telemetry hook
  equivalence checks;
- **V13-DT2** a complete fake diagnostic lifecycle and decoder-free replay in a
  fresh test root.

### Phase R — one-factor route selection after D05

No R task may start before D05 and a main-thread OpenSpec amendment/review.
At most one candidate is selected:

- **R1 prior-only**: same matrix, schedule, and check count; a cross-fitted,
  public global channel prior derived from characterization/development
  aggregates; audit truth is hidden.
- **R2 decoder-only**: same matrix, prior, and check count; change exactly one
  numerical or scheduling mechanism identified by D02/D03.
- **R3 code-only**: same prior and decoder interface; change exactly one
  explicitly diagnosed finite graph/rate property.

If D05 is `mixed` or `diagnosis_inconclusive`, stop and return to the planner.
Do not sweep routes or create a disguised rerun of V7/V10/V11.

### Phases I/E/A/C — future candidate path (plan only)

- **I01--Ixx** minimal implementation, restricted to `comparison_bench/`,
  with the separate V13-IT0--V13-IT3 candidate test gates and no official
  qualification output.
- **V13-IT0** candidate compile/import, structural checks, and tiny math;
- **V13-IT1** focused unit/boundary, role/Alice isolation, hook equivalence,
  no-overwrite, failure, and telemetry-tamper checks;
- **V13-IT2** complete fake candidate diagnostic lifecycle and decoder-free
  replay in a fresh test root;
- **V13-IT3** scoped regression, frozen-directory, dirty-worktree, and
  output-root absence checks. E01 is blocked until IT0--IT3 pass.
- **E01 development screen**: freeze 64 bw200 development frames (also from the V5 `development_partition_ranks:[128,639]` = 512-frames-per-stratum partition; with D04's 32, the 96 total stay disjoint from the 128 sealed frame-identical audit frames); run the
  unchanged baseline and the single candidate once each. The proof-of-
  correction gate is at least 1/64 independently exact-corrected, zero
  forbidden/internal/accounting failures, syndrome consistency, and a
  post-decode exact check. Zero successes is
  `failed_existing_data_feasibility` and freezes the route. The 1/64 floor is
  a continuation gate, not a performance claim.
- **E02**: if E01 passes, freeze the candidate and prohibit further tuning.
- **A01 retrospective audit**: run the frozen candidate once on the 128
  frame-identical V5 control/audit frames. A baseline run is permitted only if
  it was pre-registered; it may not be added after seeing candidate results.
  Suggested readiness gates are at least 120/128 exact corrections, zero
  forbidden failures, median at most 120 s/frame, and key-dependent
  reconciliation disclosure at most 8.75 bits/input-symbol with tags reported
  separately. Failure is `retrospective_non_ready`; passing is only
  `ready_for_fresh_confirmation`.
- **A02**: only after bw200 A01 passes, perform the pre-registered bw120 and
  bw180 retrospective cross-stratum check. It cannot promote the method.
- **C01** close out, obtain independent acceptance, and run memory triage.

## 5. Root-cause decision table

`diagnosis_class` is the scientific classification emitted by D05; it is not
the lifecycle state. The six classes are exactly `interface`, `prior`,
`decoder`, `code`, `mixed`, and `inconclusive`. `run_state` records lifecycle
disposition: a D02/oracle failure can directly produce
`implementation_interface_fault`; a supported single-factor conclusion
produces `diagnosis_complete`; mixed or insufficient evidence produces
`diagnosis_inconclusive`.

| diagnosis_class | Required evidence pattern | run_state | Permitted next route |
|---|---|---|---|
| `interface` | D02 field/mapping/syndrome/wrapper oracle or D03 telemetry equivalence fails | `implementation_interface_fault` | stop; repair requires a new reviewed amendment |
| `prior` | D01 shows calibrated/global prior mismatch while D02 and numeric traces are sound | `diagnosis_complete` | R1 only |
| `decoder` | D02 passes, but D03 shows non-finite, normalization, stagnation, or schedule evidence at fixed prior/graph | `diagnosis_complete` | R2 only |
| `code` | D01/D03 are compatible, and a read-only structural short-cycle/girth analysis of the frozen V7 R1A graph (offline, D01-adjacent) plus the frozen `rank=170`/`m=170` and rate facts explain the fixed-interface failure | `diagnosis_complete` | R3 only |
| `mixed` | two or more causal categories remain supported | `diagnosis_inconclusive` | stop; no mixed sweep |
| `inconclusive` | evidence does not discriminate categories | `diagnosis_inconclusive` | stop; return to planner |

The table is a decision aid, not a claim that any category is already proven.

## 6. States, gates, and authorization

Allowed `run_state` values are:

`plan_only`, `blocked_role_ledger`, `implementation_interface_fault`,
`diagnosis_complete`, `diagnosis_inconclusive`,
`failed_existing_data_feasibility`, `retrospective_non_ready`,
`ready_for_fresh_confirmation`, and `invalid_diagnostic_execution`.

`diagnosis_class` is recorded separately and is never substituted for a
`run_state`.

`promoted`, `qualified`, and `observed_fresh_correction` are forbidden state
values. The phrase “ready for fresh confirmation” means that a separate
future change may propose new acquisition/confirmation; it is not a result on
fresh data.

Authorization is sequential: P08 review -> D request -> D05 review -> one R
amendment -> I/E/A gates -> closeout. Each real or retrospective frame is
attempted at most once per frozen stage; failures are retained without retry,
replacement, or overwrite. Existing V5 artifacts remain read-only.

## 7. Artifacts, paths, and resources

The minimal diagnostic artifact set is:

```text
data_role_ledger.json
channel_diagnostics.json
diagnostic_outcomes.csv
decoder_telemetry.jsonl
root_cause_report.json
diagnostic_run_manifest.json
```

All six files are under a fresh additive
`comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/` root and
carry `diagnostic_only`, `retrospective_reuse`, status, command, time, commit,
configuration, and frame-ID provenance fields as applicable. The
`diagnostic_outcomes.csv` rows include the unchanged `baseline`, the sole
`candidate` development screen, and the retrospective audit, with explicit
`phase` and `method` columns. They must not be written under
`formal_ir_methods`.

Tests use a fresh `workspace/nbldpc_v13_<uuid>/` root and
`pytest -p no:cacheprovider` when later authorized. No checksums/hash DAGs,
signatures, atomic writes, locks, retry frameworks, or speculative schema
hardening are designed; normal Git/provenance fields are sufficient under the
research-code policy. Frozen `src/`, `experiments/`, `tools/`, and `results/`
remain untouched.

## 8. Stop conditions and fresh-acquisition boundary

Stop immediately on an ambiguous role ledger, oracle/interface failure,
telemetry equivalence failure, forbidden Alice leakage, missing denominator,
retry, output-root violation, or any unclassified failure. Preserve the
diagnostic artifact and classify it as `invalid_diagnostic_execution` where
appropriate.

Fresh acquisition becomes relevant only when the user wants a fresh canary,
confirmation, qualification, or promotion after V13 reaches at most
`ready_for_fresh_confirmation`. That work must be a separate OpenSpec change
with new identities, a new partition review, and a new authorization chain;
V13 cannot silently convert retrospective evidence into fresh evidence.
