# Frozen Phase 1 In-Memory Test Harness Contract

This contract resolves T2 without defining or simulating the Phase 2
production package. The harness is test-only, entirely in memory, and cannot
produce qualification evidence.

## 1. Formal-method API

The public frame method signature is exactly:

```python
run_ldpc_formal_v5(
    alice_symbols,
    bob_symbols,
    *,
    pair_idx_sequence,
    dataset_id: str,
    frame_id: str,
    stratum: str,
    candidate_policy,
    policy_manifest,
    selection_manifest,
    channel_model,
    h2_manifest,
    locked_seeds,
    _decoder_factory=None,
    _preflight_result=None,
    _clock=time.monotonic,
) -> dict
```

The return object contains exactly `outcome` and `events`. It never returns
decoded bits/symbols. `candidate_id`, selected H1 IDs, caps, decoder
parameters, and every provenance hash are derived from the mandatory bound
objects; callers cannot pass independent values for them.

Before the first disclosure, the method validates:

- the complete policy manifest and selected candidate-policy membership;
- exact H1 selection/codebook/channel binding;
- exact H2 manifest reconstruction and active/inactive relation;
- exact policy preflight entries and caps;
- two locked seed records, exact input domain, and pair-index sequence.
- `stratum` is exactly one of `bw120,bw180,bw200`. A v5-local
  `v5_plane_error_channel(bob_symbols, plane_id, stratum, channel_model)`
  validates that vocabulary and delegates to the unchanged v4
  `plane_error_channel` with the exact profile `adjacent_nominal` for all
  three values. This is the same explicit real-transfer mapping used by the
  bound v4 16 dB and 10 dB runners. No other mapping/profile is accepted, v4
  source is not modified, and the real stratum is never inferred from a
  dataset or frame identifier.

Any policy/provenance mismatch is non-attempted `invalid_input` with no
events. Backend preflight failure is `backend_unavailable` with no events.
Private injection parameters are accepted only for dependency substitution in
tests; there is no `_test_only` branch and injected results pass the same
validation/accounting state machine.

## 2. Harness APIs

Create `formal_ir/ldpc_v5_test_harness.py` with exactly:

```python
run_test_development_batch(
    frame_records,
    *,
    policies,
    policy_manifest,
    selection_manifest,
    channel_model,
    h2_manifest,
    seed_records,
    decoder_factory,
    preflight_result,
    clock_factory,
) -> dict

verify_test_development_batch(
    batch,
    *,
    frame_records,
    policies,
    policy_manifest,
    selection_manifest,
    channel_model,
    h2_manifest,
    seed_records,
) -> dict
```

Neither API accepts a path, opens a file, imports a production runner, calls a
real decoder, or writes bytes. The verifier never invokes `decoder_factory`
and returns `decoder_reexecution=false`.

For deterministic path injection, `decoder_factory` may be a callable test
object with a `begin_attempt(candidate_id, stratum, role_rank)` method. The
harness calls that method exactly once immediately before the corresponding
formal-method call; absence of the method is allowed and means no
notification. `begin_attempt` is a test-harness seam only and is never passed
to or inspected by the production formal method.

`clock_factory` is called exactly once per attempt as
`clock_factory(candidate_id, stratum, role_rank)` and returns that attempt's
monotonic callable. This permits deterministic wall-cap coverage without
global constructor-count inference. Tests use these two attempt-aware seams
to select retained failure, C2 fallback, decoder exception/malformed/
syndrome-inconsistent, and resource-cap paths. The batch/verifier objects do
not record or trust the injected mode.

## 3. Exact test domain

Candidate order is `V5-C0,V5-C1,V5-C2`. Stratum order is
`bw120,bw180,bw200`. Each stratum contains exactly 512 development records
with `role_rank=0..511`; therefore a complete batch has 4,608 outcomes.

Each frame record contains exactly:

```text
role
stratum
role_rank
plan_frame_id
dataset_id
frame_id
alice
bob
pair_idx_sequence
alice_sha256
bob_sha256
```

`role` is always `development`. Alice/Bob are detached 256-symbol integer
arrays in `[0,1023]`; pair indices are 256 integers and are hashed in their
exact order. Payload hashes use canonical little-endian `<u2` array bytes.
Records are ordered by stratum then role rank.

`policies` contains the three complete candidate policies in candidate order.
`seed_records` is keyed by
`candidate_id|stratum|role_rank` and supplies exactly two locked seed records
per attempt. All 9,216 seed IDs are unique.

Execution order is candidate, stratum, role rank. The harness calls the formal
method once per record/candidate and retains every outcome in the denominator.

## 4. In-memory batch object

The returned object contains exactly:

```text
schema
test_only
execution_order
source_digest
policy_manifest_sha256
h2_manifest_sha256
outcomes
transcripts
candidate_summaries
test_gate
batch_sha256
```

Constants:

- `schema="binary_ldpc_v5_phase1_test_batch_v1"`
- `test_only=true`
- `execution_order="candidate_stratum_role_rank"`

`source_digest` hashes compact JSON of ordered frame identity, payload hash,
and pair-index hash records, never array values or paths.

`outcomes` are the exact typed formal outcomes with the added prefix fields
`role,stratum,role_rank,plan_frame_id,alice_sha256,bob_sha256`.
`transcripts` is an equally ordered list of per-attempt event lists.

`candidate_summaries` contains, in candidate/stratum order:
`candidate_id,stratum,denominator,verified_success,forbidden_failure_count,
key_dependent_disclosure_bits_total,runtime_s_total`.

`test_gate` contains exactly:

```text
test_only
required_successes_per_stratum
required_denominator_per_stratum
eligible_candidates
selected_candidate_id
```

with `test_only=true`, required 510/512, eligible candidates meeting every
stratum and zero forbidden failures, and selection using the frozen Phase 2
ranking. This object is only a state-machine test oracle; it is never a
development result or authorization to prepare synthetic/real output.

`batch_sha256` is compact sorted-key ASCII JSON SHA256 excluding only itself.
Arrays never enter the returned object.

## 5. Read-only verification

The verifier validates outer and nested exact key sets and hashes, rebuilds
source/policy/H1/H2/seed bindings, reconstructs every public Alice syndrome
and tag, validates every transcript/outcome/accounting relation, recomputes
summaries and the test gate, and returns exactly:

```text
status
test_only
outcomes
decoder_reexecution
```

Success is `{"status":"verified","test_only":true,"outcomes":4608,
"decoder_reexecution":false}`.

## 6. T2 tamper matrix

T2 uses a deterministic fake decoder and clock but the complete 4,608-outcome
domain. It tests all-success, retained failure, cap, and fallback paths.
Independent locally re-signed mutations cover source identities/payloads,
pair order, role/order/count, policy and manifest membership, H1/H2 matrices,
seed identity, every event payload/order/parent/pass/bit count, outcome
status/accounting/provenance, transcript association, summary, gate, and outer
hash. Verification must reject each mutation without decoder execution.

The harness module and its objects are forbidden from any production plan,
lock, runner, report, handoff claim, or qualification output.
