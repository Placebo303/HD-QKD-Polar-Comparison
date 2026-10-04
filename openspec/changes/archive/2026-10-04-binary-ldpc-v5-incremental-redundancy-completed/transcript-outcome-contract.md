# Frozen v5 Transcript, Outcome, and Public-Payload Contract

This file resolves P1-05/P1-07 serialization ambiguity.

## 1. Event envelope

Every event has exactly the v4 envelope fields:

`event_id, frame_key, method, event_type, direction, parent_event_id,
pass_id, plane_id, key_dependent_bits, public_control_bits, payload`

Rules:

- `event_id` is contiguous from 1 in emission order.
- `frame_key = f"{dataset_id}:{frame_id}"`.
- `method = "ldpc_formal_v5"`.
- pass 0 events have `parent_event_id=None`.
- pass 1 events have `parent_event_id` equal to the pass-0
  `FRAME_TAG_CHECK` event ID.
- Canonical bytes are produced by a new v5-local `canonical_event_v5(event)`
  using the same compact-JSON-plus-one-newline encoding as v4. Do not modify
  historical `shared.canonical_event`; its payload whitelist is intentionally
  narrower.

`canonical_event_v5` permits only the payload keys explicitly present in this
contract:

`syndrome, seed_bit_length, seed_id, verification_round, tag, tag_bits,
value, reason, h2_matrix_sha256, h2_rows, cap`

Each event type requires its exact payload key set below; the union is not a
license to add keys to an individual event.

## 2. Exact events and payloads

### H1 syndrome, pass 0

- type `SYNDROME`
- direction `alice_to_bob`
- plane `0..9`
- key-dependent bits equal the exact H1 row count
- public control bits 0
- payload exactly `{"syndrome": <lowercase packed-big-bitorder hex>}`

Emit in plane order.

### Verification events

For verification round `r` (`pass_id=r`):

`VERIFICATION_SEED`:

- direction `control`, plane -1
- key-dependent bits 0, public control bits 2623
- payload exactly:
  `{"seed_bit_length":2623,"seed_id":<64 lowercase hex>,
  "verification_round":r}`

`VERIFICATION_TAG`:

- direction `alice_to_bob`, plane -1
- key-dependent bits 64, public control bits 0
- payload exactly:
  `{"tag":<16 lowercase hex>,"tag_bits":64,
  "verification_round":r}`

`FRAME_TAG_CHECK`:

- direction `bob_local`, plane -1
- both bit counts 0
- payload exactly:
  `{"value":"match"|"mismatch","verification_round":r}`

They are emitted seed, tag, check.

### Fallback NACK

Immediately after a pass-0 mismatch:

- type `FALLBACK_NACK`
- direction `bob_to_alice`
- pass 1, plane -1
- parent is pass-0 check
- key-dependent bits 0, public control bits 1
- payload exactly:
  `{"reason":"toeplitz_mismatch","value":"fallback_requested"}`

### H2 incremental syndrome, pass 1

After NACK, in plane order:

- type `INCREMENTAL_SYNDROME`
- direction `alice_to_bob`
- parent is pass-0 check
- key-dependent bits equal the registered H2 row count
- public control bits 0
- payload exactly:
  `{"h2_matrix_sha256":<bound canonical H2 bytes SHA256>,
  "h2_rows":<integer>,"syndrome":<lowercase packed-big-bitorder hex>}`

Then emit pass-1 verification seed, tag, and check.

An `ABORT` event follows existing v4 canonical semantics and is emitted only
when event capacity permits:

`{"cap":<exact cap name>,"reason":"resource_limit"}`.

## 3. Candidate event sequences

- C0/C1: ten H1 syndromes, then pass-0 seed/tag/check.
- C2 round-0 success: same sequence.
- C2 fallback: the round-0 sequence ending mismatch, NACK, ten H2 syndromes,
  then pass-1 seed/tag/check.

Prefix sequences are allowed only for a retained attempted failure. No event
may appear out of order or after a terminal check.

## 4. Formal outcome fields

The method outcome contains exactly, in this canonical field order:

```text
dataset_id
frame_id
n_pairs
pair_idx_sequence_sha256
method
candidate_id
attempted
denominator_included
status
failure_reason
dimension
frame_len_symbols
raw_ser
fallback_invoked
rounds_attempted
verification_invoked
verification_seed_id_round0
verification_seed_id_round1
verification_tag_bits
epsilon_ec
key_dependent_disclosure_bits_total
public_control_bits_total
transcript_first_event_id
transcript_last_event_id
transcript_sha256
runtime_s
decoder_call_count
verification_check_count
ldpc_syndrome_bits
h1_syndrome_bits
h2_syndrome_bits
verification_tag_bits_component
feedback_control_bits
selection_sha256
channel_model_sha256
h1_codebook_manifest_sha256
h2_manifest_sha256
policy_sha256
mapping
leakage_comparison_policy
backend_name
backend_version
```

Exact constants:

- `method="ldpc_formal_v5"`
- `n_pairs=frame_len_symbols=256`
- `dimension=1024`
- `mapping="gray"`
- `leakage_comparison_policy="method_specific_not_cross_ranked"`
- `candidate_id` is one of `V5-C0`, `V5-C1`, `V5-C2`.

`status` uses this exact v5 vocabulary:

`invalid_input, unsupported_domain, backend_unavailable,
aborted_resource_limit, decoder_error, syndrome_inconsistent,
verify_failed, verified_success`

Attempted statuses remain in the denominator; only `invalid_input`,
`unsupported_domain`, and `backend_unavailable` are non-attempted. Implement
the v5 status validator locally; do not expand historical shared constants.

## 5. Derived accounting

All bit totals are recomputed from canonical events:

- `h1_syndrome_bits`: SYNDROME key-dependent sum;
- `h2_syndrome_bits`: INCREMENTAL_SYNDROME key-dependent sum;
- `ldpc_syndrome_bits = h1 + h2`;
- `verification_tag_bits_component`: VERIFICATION_TAG key-dependent sum;
- `feedback_control_bits`: FALLBACK_NACK public-control sum;
- `key_dependent_disclosure_bits_total`: all event key-dependent bits;
- `public_control_bits_total`: all event public-control bits.

Further relations:

- `fallback_invoked` iff exactly one NACK exists;
- `rounds_attempted = 1 + int(fallback_invoked)`;
- `verification_check_count` is the number of check events;
- `verification_invoked` iff check count is nonzero;
- round-0 seed ID is present iff pass-0 seed/tag is emitted;
- round-1 seed ID is present iff pass-1 seed/tag is emitted;
- seed IDs must match the supplied locked seed records;
- `epsilon_ec = verification_check_count * 2^-64`, restricted to
  `0`, `2^-64`, or `2^-63`.

Complete C0/C1 or C2 round-0 outcomes have H1=584, H2=0, tag=64,
key disclosure=648, public control=2623, checks=1.

Complete C2 fallback outcomes have H1=584, H2=392, tag=128,
key disclosure=1104, public control=5247, checks=2, feedback=1.

Partial failures retain exact prefix-derived values; validators must not
invent full-round totals.

## 6. Package CSV encoding

Package runners prepend these provenance fields, in order:

`role, stratum, plan_frame_id, alice_sha256, bob_sha256,
transcript_bytes_len, transcript_bytes_sha256`

Then append the exact formal outcome fields above.

CSV uses `csv.DictWriter`, UTF-8, header, `lineterminator="\n"`, no CR bytes.
Booleans encode lowercase `true`/`false`. `raw_ser`, `epsilon_ec`, and
`runtime_s` encode `repr(float(value))`. All other scalars use their canonical
string form. The reader parses exact typed fields and requires byte-for-byte
row round-trip; NaN, infinity, negative runtime, extra/missing columns, and
noncanonical booleans fail.

## 7. Public-payload reconstruction

The read-only verifier, without decoder execution:

1. rebuilds exact Alice bits from the locked frame;
2. rebuilds H1/H2 matrices and recomputes every disclosed syndrome;
3. reconstructs each emitted seed from the locked root;
4. recomputes each Alice Toeplitz tag from the corresponding seed;
5. checks event ordering, parents, pass IDs, payload keys, hex length/case,
   bit counts, and package transcript slices;
6. checks that outcome status and fallback flow agree with check values
   (`match` terminates success; C2 pass-0 mismatch requires fallback;
   terminal mismatch is `verify_failed`);
7. recomputes every outcome accounting field and package gate.

It does not reconstruct Bob's decoded candidate and reports
`decoder_reexecution=false`.

## 8. Test requirements

Tests cover every event/payload/outcome field and locally re-signed tampering:
syndrome bytes, matrix ID, seed, tag, check value, NACK, parent, pass, order,
bit counts, epsilon, prefix failure, CSV typing/canonical bytes, transcript
slice/hash, status flow, disclosure, and gate reconstruction.

## 9. Phase 1 API and package boundary

Phase 1 implements only the following three pure, in-memory APIs in
`ldpc_v5.py`:

```python
verify_public_payload_v5(
    outcome,
    events,
    *,
    alice_symbols,
    pair_idx_sequence,
    stratum: str,
    candidate_policy,
    policy_manifest,
    selection_manifest,
    channel_model,
    h2_manifest,
    locked_seeds,
) -> dict

encode_outcome_csv_v5(rows) -> bytes
decode_outcome_csv_v5(raw: bytes) -> list[dict]
```

They accept no path and perform no file I/O.

`verify_public_payload_v5` validates all bound manifests/policies, input and
pair-index identity, exact H1/H2 Alice syndromes, locked seed identities,
Alice Toeplitz tags, event schema/order/parents/passes, transcript hash,
outcome flow/status/provenance, and all disclosure/accounting fields. It does
not reconstruct Bob's decoded candidate, invoke a decoder, or independently
prove a `FRAME_TAG_CHECK.value`; it proves that the recorded check value and
terminal/fallback flow are mutually consistent. It returns exactly:

```text
status
decoder_reexecution
event_count
transcript_sha256
key_dependent_disclosure_bits_total
public_control_bits_total
```

Success uses `status="verified"` and `decoder_reexecution=false`.

The CSV encoder accepts a sequence of exact package-prefixed rows: the seven
prefix fields from section 6 followed by all formal outcome fields in their
frozen order. It returns canonical CSV bytes only. The decoder accepts those
bytes and returns exact typed dictionaries in input order after enforcing
header, LF-only termination, scalar encodings, finite runtime/floats, exact
field sets, and byte-for-byte re-encoding. Empty input, duplicate/missing/
extra headers, CR bytes, noncanonical booleans/floats/integers, invalid UTF-8,
NaN/infinity, and extra/missing row values fail.

The Phase 1 in-memory harness must call the public-payload helper for every
attempt, round-trip its outcome rows through these CSV functions, and
reconstruct only the already frozen `test_gate` from
`phase1-test-harness-contract.md`. Phase 1 defines no production artifact
names, package manifest/index, qualification gate, or development/synthetic/
real promotion schema. Those remain mandatory Phase 2--4 contracts and may
not be inferred from these pure functions.
