# Design: V12 Nonbinary LDPC Real Micro-Feasibility

## 1. Scientific Question and Claim Boundary

Can the frozen finite GF(1024) R1 baseline produce at least one independently
verified exact correction among four fresh compatible real frames, with a
valid syndrome and complete transcript/leakage accounting?

V12 separates five statements:

1. implementation/tests complete;
2. a decoder returned a syndrome-consistent word;
3. independent verification observed exact correction;
4. the four-frame micro-feasibility gate passed;
5. qualification or promotion.

Only statements 1-4 are reachable. V12 never establishes a success
probability, FER, threshold, cross-stratum generalization, formal comparison,
qualification, or promotion.

V11 remains immutable `failed_coupling`. V12 neither reinterprets nor reopens
V10/V11; it changes the question from ensemble DE to a finite decoder on a
compatible real input.

## 2. Frozen Route V12-R1

V12 contains exactly one route:

- method identity: `nbldpc_formal_v12_r1_real_micro`;
- GF(1024), polynomial-basis field identity reconstructed from V7;
- `n=256`, `m=170`;
- the accepted V7 R1A full-rank degree-2 PEG matrix, reconstructed and verified
  without changing its topology, coefficients, seed, or row order;
- the V7 R1A primary undamped flooding FFT-QSPA implementation;
- all 170 checks active from the first and only decoder stage;
- the existing V7 R1A `max_iter=100` cap and primary schedule, unchanged;
- the frozen V7 R1A `p=.20` QSC prior.

The full syndrome discloses `170 * 10 = 1700` key-dependent bits. There is no
prefix search, blind extension, restart, warm continuation, additional
iteration, per-frame parameter change, fallback, or alternative route.

V7 R1A previously failed its synthetic p=.20/.30 canaries and has no real-data
evidence. V12 does not relabel that failure. R1 is reused only because its
finite `n=256` interface exactly matches the selected real source and the
historical 10 dB bw200 raw SER is lower than the failed synthetic canary
regimes. The deliberately conservative `p=.20` prior preserves the accepted
public decoder API and does not fit or expose V12 truth. This is a tractability
rationale, not predicted success or a matched real-channel model.

## 3. Decoder Information Boundary

The production plan binds `p=.20`, the lower of the two values accepted by the
unchanged V7 R1A public decoder API. It does not estimate a prior from real V12
frames and does not claim the real source is QSC with `p=.20`. It may not use:

- V5 confirmation outcomes or frames;
- any V12 Alice symbol, frame-specific raw SER, error mask, or error location;
- any old canary/confirmation outcome to change the code, prior, schedule, or
  stopping rule.

For each frame, the decoder receives only:

- Bob's 256 GF(1024) symbols;
- the frozen `p=.20` QSC prior;
- the public 170-symbol syndrome and registered decoder constants.

Alice's symbols may be used only to compute the public syndrome before decode
and by the post-decoder verification procedure. They may not enter decoder
stopping, diagnostics, candidate selection, retry, or fallback. The decoder
never receives the verification result as an oracle.

## 4. Frozen Real Domain and Partition

The sole domain is:

| field | value |
|---|---|
| acquisition | 10 dB Type-II |
| dimension / field | q=1024 / GF(1024) |
| mapping | Gray |
| bandwidth stratum | bw200 |
| frame contract | contiguous 256-symbol frame |
| role | `sacrificed_real_canary` |
| denominator | exactly 4 frames |

A 256-symbol source frame is indivisible. V12 must not split it into four
64-symbol decoder inputs or construct one by concatenating 64-symbol frames.
The old 20 dB, 64-symbol final-IR tuning and confirmation material is excluded.

The V12 partition is newly reconstructed from the complete traceable 10 dB
pool. Before selection, it uses an explicit reviewed exclusion manifest that
lists every locally discoverable package and binds the union of its frame and
payload identities. The minimum required inventory is the V4 10 dB v1/v2 real
locks, the V5 predecessor set, V5 development and confirmation roles, and all
formal/final-IR real packages present before V12 plan review. The review must
reject a missing local real package, unclassified identity-bearing artifact,
or incomplete inventory; it may not rely on a broad phrase alone. Existing V5
roles are never borrowed. Any unassigned V5 pool remainder is candidate
inventory only.

After exclusion, candidate rows retain the source adapter's canonical full-
pool order. The first four complete bw200 rows in that order form the V12
partition. This deliberately simple deterministic rule supports a tractability
canary; it is not a random or representative sample.

The partition is frozen and reviewed before Alice/Bob arrays are exposed to
the decoder. If four complete, traceable, collision-free identities cannot be
established, the state is `source_partition_blocked`. If identity or payload
freshness cannot be proven, a future change must use a fresh acquisition.

## 5. Verification and Accounting

The production plan privately freezes one independent 2623-bit Toeplitz seed
record per frame before decoding; merely storing it in the plan does not count
as public disclosure. Each record contains exactly `seed_hex`,
`seed_bit_length=2623`, and `seed_id`, follows the accepted shared
`seed_record` semantics, is unique within V12, and has no `seed_id` collision
with locally discoverable formal evidence. After the decoder returns a syndrome-consistent
candidate, the transcript emits `VERIFICATION_SEED`, then
`VERIFICATION_TAG`, followed by the local `FRAME_TAG_CHECK`. The 64-bit tag
uses the 2623-bit public seed for the 2560-bit Gray representation. The tag
costs 64 key-dependent bits and the emitted seed costs 2623 public-control
bits. A `decode_failed` frame emits no seed or tag. This one-stage canary adds
no public decision event: its terminal decoder/verification outcome is a local
audit record, not protocol disclosure.

An outcome is `verified_success` only when all of the following hold:

- the returned word is consistent with the full public syndrome;
- the independent verification tag matches;
- the offline read-only verifier confirms decoded Bob equals Alice exactly;
- every transcript and leakage field reconstructs without discrepancy.

Syndrome consistency alone is not success. A tag mismatch is `verify_failed`.
The read-only verifier must reconstruct verification after execution and must
not import or call a decoder.

Actual leakage is authoritative:

- full syndrome: 1700 key-dependent bits on every attempted frame;
- emitted verification tag: 64 key-dependent bits;
- Toeplitz seed: 2623 public-control bits only when verification is invoked;
- local decoder and verification outcome events: zero disclosure bits.

Any derived leakage efficiency or `beta_eff_empirical` is computed only from
the actual transcript and registered error inputs. Binary V5 leakage values
must not be copied.

## 6. Lifecycle and Authorization

The lifecycle is strictly ordered:

1. implement pure V12 reconstruction, method wrapper, fake lifecycle, and
   read-only verifier;
2. T0/T1 focused engineering tests;
3. T2 complete four-frame fake package and decoder-free replay;
4. return to the main thread;
5. T3 scoped regression, source/frozen checks, and implementation acceptance;
6. reconstruct and freeze the exclusion inventory and V12 partition;
7. prepare a complete production plan without decoding;
8. main-thread read-only review and explicit execute authorization;
9. execute all four real denominators exactly once;
10. run one decoder-free read-only verification and record the terminal state.

The OpenCode packet initially authorizes only steps 1-3. Steps 5-10 remain
unauthorized until the main thread explicitly advances the matching task IDs.

Tests use explicit fake runners and fresh `workspace/nbldpc_v12_*` roots.
They cannot enter a real source adapter, production decoder, or official
output root. A future production package uses one fresh additive no-overwrite
V12-specific directory under `comparison_bench/outputs_comparison/formal_ir_methods/`.

The future package contains exactly these seven files:

```text
exclusion_manifest.json
partition_lock.json
pre_run_plan.json
real_frame_outcomes.csv
real_transcript.jsonl
real_run_manifest.json
real_micro_report.json
```

`exclusion_manifest.json` binds the exact reviewed package/path inventory and
the union of excluded frame/payload identities. `partition_lock.json` binds the
10 dB source adapter and its canonical-order rule plus the four selected rows.
Prepare writes and reviews those two files before `pre_run_plan.json`; none of
the three preparation artifacts invokes a decoder. Execute finalizes the other
four even on a retained invalid partial run when possible. The read-only
verifier requires this exact file set and reconstructs each artifact from the
reviewed source and transcript.

## 7. Gate and Terminal States

All four real frames enter the denominator exactly once. No frame may be
retried, resumed, replaced, omitted, tuned, or rerun.

Allowed scientific outcomes are `verified_success`, `verify_failed`, and
`decode_failed`. Source, backend, internal, accounting, resource, syndrome,
provenance, invalid-input, unsupported-domain, and unclassified failures are
forbidden failures and make the execution invalid.

Terminal states are:

- `source_partition_blocked`: four fresh valid frames cannot be frozen before
  decoding;
- `invalid_execution`: a forbidden failure, missing denominator, lifecycle
  violation, or replay failure occurred;
- `failed_canary`: exactly 0/4 independently verified successes with otherwise
  valid complete outcomes;
- `observed_real_correction`: at least 1/4 independently verified successes,
  zero forbidden failures, exact accounting, and successful read-only replay.

`observed_real_correction` means only that exact nonbinary correction was
observed in this four-frame bw200 tractability canary. Evidence freezes under
every terminal state. No state automatically authorizes blind adaptation,
optimized irregular NB-LDPC, EMS/list decoding, a bit-symmetric front end,
multilevel/product coding, another stratum, more frames, qualification, or
promotion.

## 8. Acceptance IDs

- **V12-P01** V10/V11 and V7 predecessor meanings remain explicit and
  immutable.
- **V12-P02** One R1 route, full 170-row syndrome, unchanged V7 matrix,
  decoder, schedule, and iteration cap are frozen.
- **V12-P03** The 10 dB q=1024 Gray bw200 contiguous-256 domain and four-frame
  sacrificed role are frozen.
- **V12-P04** The conservative `p=.20` prior and Alice-information boundaries
  are frozen.
- **V12-P05** Cross-history frame/payload exclusions and no-64-split rule are
  frozen.
- **V12-P06** Transcript, verification, leakage, gate, terminal states, and
  claim boundary are frozen.
- **V12-P07** Exact seven-file package, conditional seed disclosure, and
  seed-record freshness are frozen and independently reviewed.
- **V12-I01** Reconstruct and verify the frozen V7 R1 codebook/decoder binding.
- **V12-I02** Implement the V12 method wrapper and Alice-information guard.
- **V12-I03** Implement partition preparation with no decode.
- **V12-I04** Implement transcript, verification, accounting, retained outcome,
  and terminal-state logic.
- **V12-I05** Implement production plan/execute separation and decoder-free
  read-only verification with explicit fake-runner test entry points.
- **V12-T0** Compile/import, constants, tiny syndrome/Toeplitz/accounting, and
  V7 reconstruction checks pass.
- **V12-T1** Focused unit, boundary, Alice-information, role, no-overwrite,
  failure, and tamper tests pass.
- **V12-T2** A complete four-frame fake lifecycle and decoder-free replay pass
  in a fresh test root without production-source/output access.
- **V12-T3** Scoped regression, task-file manifest, dirty-worktree scope,
  frozen V1-V11/baseline checks, and absence of a production V12 root pass.
- **V12-RP01** Reconstruct and independently review the complete historical
  real-package exclusion inventory without exposing frame arrays.
- **V12-RP02** Reconstruct, exclude, freeze, and independently review exactly
  four fresh real frame/payload identities without decoding.
- **V12-RP03** Prepare and independently review the complete production plan;
  only then may the main thread authorize execution.
- **V12-X01** Execute the four real denominators exactly once.
- **V12-X02** Verify once without decoder reexecution and reconstruct every
  identity, outcome, event, leakage field, and gate.
- **V12-D01** Record exactly one declared terminal state without silent
  promotion or successor execution.
- **V12-D02** Perform final scoped checks, decision-log/handoff update, and
  mandatory memory triage.
