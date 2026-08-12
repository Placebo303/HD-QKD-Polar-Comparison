# Design: Formal Nonbinary LDPC v4 Incremental Redundancy

## 1. Immutable predecessor and identity

v4 is additive:

- method: `nbldpc_formal_v4_ir`;
- plan schema: `NBLDPCQ4IR`;
- run ID: `20260731_v4_nbldpc_ir_synthetic`;
- official root:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic`.

The implementation reconstructs the exact v3 `NBLDPC3` canonical codebook,
field identity, matrices, ordered prefixes, and manifest hash.  It does not
copy or modify any v3 artifact.  Every v1-v3 plan, source, seed, frame, result,
and output remains immutable and cannot tune v4.

## 2. Fixed decoder state machine

All policies use q=1024, n=64, nominal QSC priors, dense float64 full messages,
the exact coefficient-aware Walsh-Hadamard check update, ascending single-row
layered schedule, lambda .75, and syndrome-consistency stopping after complete
iterations.

Initial/final prefixes are:

| stratum | initial | final |
| --- | ---: | ---: |
| p=.20 | 32 | 40 |
| p=.30 | 40 | 48 |

Stage 1 has at most 12 complete iterations.  An IR policy may request its
single eight-row extension only after:

- ordinary `decode_failed`; or
- `syndrome_consistent` followed by a failed first independent 64-bit
  Toeplitz verification.

`decoder_error`, `codebook_invalid`, `invalid_input`, `unsupported_domain`,
and `aborted_resource_limit` terminate the frame and cannot be hidden by
extension or retry.

When stage 1 is syndrome-consistent, verification happens before the decision
to extend.  Stage-1 verified success terminates without extension.  After
extension, stage 2 has at most 12 complete iterations and at most one final
verification.  No third stage or per-frame parameter change exists.

### Policies

- `nbldpc_v4_control`: exact v3 lambda-.75 behavior using only the initial
  32/40 prefix and 12 iterations; it never extends.
- `nbldpc_v4_ir_warm`: on the permitted trigger, retain old directed messages,
  initialize only new-row messages uniformly, reconstruct normalized beliefs,
  then scan all 40/48 active rows in ascending order for at most 12 iterations.
- `nbldpc_v4_ir_restart`: on the permitted trigger, discard stage-1 state and
  initialize the complete 40/48 graph from the same Bob prior and uniform
  messages for at most 12 iterations.

The only persistent decoder state is the old active-edge check-to-variable
array family in exact ascending `(row, variable)` order.  Warm extension
retains those arrays, creates new-row arrays as uniform, then reconstructs
every belief as the normalized product of the Bob prior and *all* active
check-to-variable arrays.  Every variable-to-check extrinsic is recomputed
from that complete active set; a stage-1 belief cache is never reused.
Restart retains no old array or belief.

The internal state binds method, candidate, canonical codebook hash, q, n, p,
active prefix, public syndrome and stage.  A mismatch fails closed.  It
contains no Alice symbols, truth, error mask, verification result, callback,
file path, or serialized state.  A tiny deterministic fixture must prove
warm reconstruction equals the complete product, restart has no old state,
and control is result-equivalent to v3 layered-l075 on identical inputs.

## 3. Diagnostic boundary

The decoder may compute local convergence values transiently for unit tests,
but qualification discards them.  None of the eight artifacts may contain
residual counts or indices, decision changes or hashes, cycle indicators,
posterior summaries, messages, Alice truth, or error locations.  The outcome
retains only protocol-required status, stage iteration counts, active/final
prefix, extension flag, disclosure, verification and event summaries.

Strict replay independently recomputes the outcome and proves that every
formal artifact and transcript is free of the forbidden diagnostic fields.
If v4 later fails development, a separate approved diagnostic change with new
data is required; this package cannot be repurposed for post-hoc private-state
analysis.

## 4. Verification and exact accounting

Every development seed record is bound in the plan before development:
control has exactly one record per frame; each IR policy has exactly two,
keyed by `(policy_sha256, frame_id, stage)`.  An unused IR stage-2 record stays
explicitly unused and cannot be reassigned.

No confirmation frame or seed exists in the plan.  Only after development
readiness selects one policy does execution atomically materialize the
selected policy's confirmation frames and exactly one seed per control frame
or two seeds per IR frame.  It proves global seed-ID freshness and freezes
that complete material before the first confirmation decode.

Transcript lineage is fixed:

1. `SYNDROME_INITIAL`;
2. `DECODER_STAGE1`;
3. optional `VERIFICATION_TAG_STAGE1`;
4. mandatory two-bit `STAGE_DECISION_STAGE1`;
5. optional `SYNDROME_EXTENSION`;
6. optional `DECODER_STAGE2`;
7. optional `VERIFICATION_TAG_STAGE2`.
8. mandatory two-bit `STAGE_DECISION_STAGE2` when stage 2 occurs.

Each decision encodes exactly one of `00=accept`, `01=extend`, `10=reject`;
`11` is reserved and invalid.  Control can emit only accept/reject.  IR can
emit extend only at stage 1 under the permitted trigger.  Stage 2 can emit
only accept/reject.  Thus no branch relies on silence, and Alice always learns
whether to retain or discard the frame.

The initial syndrome costs 320 key-dependent bits at p=.20 or 400 at p=.30.
An extension costs 80 more.  Every emitted tag costs 64 key-dependent bits;
its seed costs 703 public-control bits.  Every stage decision costs two
public-control bits.  Decoder events are local audit events.  A protocol
interaction round is one completed stage ending in its decision event;
selection reconstructs all counts from canonical events and never from
implicit silence or row fields.  Transcript summaries, not a flattened final
check count, are authoritative.

For an accepted outcome, `outcome_epsilon_ec` is the conditional bound for
the accepting tag and equals `2^-64`; failed outcomes store null.  The
registered composable per-frame bound is separately
`protocol_epsilon_ec_bound`: `2^-64` for control and `2^-63` for either IR
policy by a union bound over at most two independent attempts.  These fields
must not be conflated.  A failed first tag is retained in leakage and
transcript even when stage 2 later succeeds.

## 5. Fresh data and isolation

PCG64 roots are fixed:

| role | p=.20 | p=.30 |
| --- | ---: | ---: |
| development | 202607510000 | 202607520000 |
| confirmation | 202607530000 | 202607540000 |

Frame generation keeps the pinned call order: Alice `integers`, error mask
`random`, nonzero error `integers`, then masked XOR.  The plan proves zero
overlap against all locally discoverable formal evidence in roots, frame IDs,
array hashes, atomic keys, and Toeplitz seed IDs.

There are 64 sacrificed development frames per stratum.  All three policies
run on all 128 development frames, producing 384 outcomes.  Confirmation has
128 frames per stratum but remains wholly unmaterialized until readiness.
After readiness, only the selected policy receives 256 confirmation frames
and its fixed one-per-control-frame or two-per-IR-frame independent seed
records.  The full selected-policy confirmation material is frozen before its
first decode.  Confirmation never selects or modifies a policy.

## 6. Eligibility, selection, and gates

A policy is eligible only with exactly 64 denominator-included development
outcomes per stratum, no prohibited status, exact transcript/accounting, and
strictly valid policy and artifact identities.  The complete allowed
performance whitelist is `verified_success`, `verify_failed`, `decode_failed`,
and `aborted_resource_limit`; the cap status remains a denominator-included
failure.  Prohibited statuses are `decoder_error`, `codebook_invalid`,
`invalid_input`, `unsupported_domain`, `invalid_run`, `provenance_failure`,
`accounting_failure`, `transcript_failure`, `internal_error`, and any
unclassified status.  One prohibited outcome makes the policy ineligible.

Eligible policies rank lexicographically by:

1. negative minimum per-stratum verified successes;
2. negative total verified successes;
3. total key-dependent disclosure;
4. total public-control bits;
5. total interaction rounds reconstructed as stage-decision count;
6. total decoder iterations;
7. policy SHA256.

The selected policy is ready only at 63/64 or better independently in both
strata.  Otherwise stop as `non_promoted_development` without creating any
confirmation frame or seed.

Promotion requires exactly 128/128 verified successes independently at p=.20
and p=.30, full denominators, zero prohibited failures, exact leakage and
transcript reconstruction, complete hash DAG, and strict read-only production
replay.  This means only that no failure was observed in each registered
128-frame sample.  It does not establish FER=0; with zero failures in 128, the
one-sided 95% binomial upper bound is about 2.31% per stratum.

## 7. Resources, artifacts, and stop rules

Caps are:

- workers 1; q=1024; n=64; checks<=48; row weight<=8;
- stage iterations<=12; total frame iterations<=24;
- decoder stages<=2 per frame and verification attempts<=2 per frame;
- dense decoder storage<=24 MiB.

Wall-clock stage, frame, and complete-run durations are monitoring fields only.
They never choose a branch, change a status, enter eligibility, or require
numeric equality during strict replay.  An externally interrupted process is
retained as an incomplete/invalid package and is not converted into a
denominator-included performance outcome.  Formal resource status is derived
only from deterministic iteration, row, call, event, and memory limits.

Use the v3 eight-artifact names with a v4 schema, no-overwrite `x` creation,
partial/invalid-run retention, explicit fake runners in tests, scoped
source/CLI/contract/codebook provenance, and deterministic production
reexecution in the read-only verifier.

Before official plan creation, main acceptance requires T0-T3, independent
review, frozen-directory/source checks, absence of the official v4 root, and
one non-qualification cost probe using fixed seed `202607559999` at p=.30.
The probe exercises 40-row stage 1 plus both 48-row state-transition modes
through the stage API, records only operational timing and deterministic
work/memory facts, is not a policy or qualification result, and cannot tune
any frozen value.  It is a go/no-go check for practical execution, not a
formal timeout threshold.  Then create one plan, execute it at most once, and
invoke strict read-only replay at most once.  No outcome inspection may change
the run.

Non-readiness or non-promotion forbids rerun, confirmation tuning, codebook
search on these data, N4, sidecars, `.ttbin`, real-data claims, or comparison
claims.  Promotion authorizes only a new N4 OpenSpec proposal, not real-data
access or execution.

Ponytail-lite boundary: the control and two state-recovery policies are the
complete candidate set.  External repositories are references only and no new
dependency is added.
