# Delta Spec: Formal Nonbinary LDPC v4 IR

## Requirement: Immutable codebook reuse

`nbldpc_formal_v4_ir` SHALL reconstruct and bind the exact v3 GF(1024),
n=64 covered QC codebook and its ordered 24/32/40/48 prefixes.  It SHALL NOT
modify or reinterpret v1-v3 source, plans, data, policies, results, seeds, or
artifacts.

## Requirement: Fixed two-stage decoder

The candidate set SHALL contain only exact-v3 control, warm IR, and restart
IR with lambda .75.  Initial/final prefixes SHALL be 32→40 at p=.20 and 40→48
at p=.30.  Each stage SHALL allow at most 12 complete ascending-row layered
FFT-QSPA iterations.  Only `decode_failed` or first-tag `verify_failed` SHALL
trigger the single eight-row extension.  Integrity, input, backend, codebook,
or resource failures SHALL terminate without retry.

The warm state SHALL retain only ordered old active-edge check-to-variable
messages, initialize new-row messages uniformly, reconstruct each belief from
the Bob prior times every active check message, recompute every extrinsic, and
process the complete active graph.  It SHALL NOT reuse stale stage-1 beliefs.
The restart state SHALL discard every old message and belief and initialize
from the same Bob prior.  Neither decoder nor state SHALL accept Alice truth
or be serialized.  Control SHALL be result-equivalent to v3 layered-l075 on
identical inputs.

## Requirement: Auditable interaction and leakage

Every initial/extension syndrome, decoder stage, verification attempt, and
mandatory two-bit stage decision SHALL have a canonical ordered event.
Decisions SHALL encode accept, extend, or reject without implicit silence.
Syndrome symbols and 64-bit tags SHALL be charged as key-dependent disclosure;
each 703-bit Toeplitz seed and decision SHALL be public control.  A failed
first tag SHALL remain charged.  Accepted outcomes SHALL report conditional
`outcome_epsilon_ec=2^-64`; the separate registered composable per-frame
bound SHALL be `2^-64` for control and `2^-63` for IR.

Qualification SHALL discard every transient decoder diagnostic other than
protocol-required status, stage iteration counts, prefixes and extension flag.
No formal artifact or transcript SHALL contain residual counts/indices,
decision changes/hashes, cycle indicators, posterior summaries, messages,
Alice truth, or error locations.  Strict replay SHALL verify their absence.

## Requirement: Fresh isolated qualification

The four fixed v4 PCG64 roots, all frame identities/arrays/atomic keys, and
all CSPRNG seed records SHALL be disjoint from locally discoverable formal
evidence.  Development SHALL bind one seed per control frame and two per IR
frame in its plan.  Confirmation SHALL contain 128 frames per stratum for the
selected policy and SHALL remain wholly unmaterialized unless readiness
reaches 63/64 independently in both development strata.  After readiness, its
complete one-seed control or two-seed IR material SHALL be atomically created,
freshness-checked, and frozen before the first confirmation decode.

## Requirement: Promotion and stop boundary

Promotion SHALL require 128/128 verified successes independently at p=.20 and
p=.30, full denominators, zero prohibited failures, exact accounting and
transcripts, a complete hash DAG, and strict read-only replay.  The claim
SHALL be limited to zero observed failures in the registered samples and
SHALL NOT state FER=0.

The package SHALL be planned once, executed at most once, and strictly replayed
at most once.  Non-readiness or non-promotion SHALL forbid rerun, confirmation
tuning, N4, sidecars, `.ttbin`, real-data claims, and comparison claims.
Promotion SHALL authorize only a separately approved N4 OpenSpec proposal.

Wall time SHALL be monitoring-only and SHALL NOT change a formal outcome,
selection, or promotion result.  Formal resource limits SHALL be deterministic
iteration, row, decoder-stage, verification-attempt, event, and memory bounds.
An interrupted execution SHALL remain incomplete/invalid rather than becoming
a performance outcome.
