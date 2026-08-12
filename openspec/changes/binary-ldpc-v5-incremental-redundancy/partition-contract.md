# Frozen v5 Partition Lock and Development API Contract

This file resolves P1-02/P1-03 ambiguity. “Sealed confirmation” is enforced
by role-scoped code and lifecycle review; it is not a claim that an operator
with filesystem access cannot read the external sidecars.

## 1. Builder API

New v5 source module exports exactly:

```python
build_partition_lock() -> dict
validate_partition_lock(lock: Mapping) -> None
write_partition_lock(path: Path) -> dict
development_rows(lock: Mapping) -> list[dict]
development_arrays_for_frame(lock: Mapping, row: Mapping) -> tuple[np.ndarray, np.ndarray]
```

`build_partition_lock` and `validate_partition_lock` are read-only.
`write_partition_lock` first builds and validates, requires the parent
directory already exists, and writes canonical JSON with `open("xb")`.

There is no Phase-1 public confirmation array API and no generic
`arrays_for_role` API.

`development_rows` returns detached dictionaries in canonical development
order. `development_arrays_for_frame` accepts only an exact row present in
the lock's development role. A confirmation row, changed row, unknown row,
wrong role, or out-of-range source slice raises `ValueError` before loading
arrays. Returned arrays are detached, writable, shape `(256,)`, integer, and
in `[0,1023]`.

## 1A. Sole production lock instance

The only authorized production instance for this change is:

```text
comparison_bench/outputs_comparison/formal_ir_methods/
  20260731_v1_binary_ldpc_v5_partition/
    partition_lock.json
```

The directory must not exist before the sole write. The main thread creates
the directory, calls `write_partition_lock` exactly once, then performs
read-only reconstruction and review. The directory contains exactly that one
canonical file. No retry, overwrite, alternate dated directory, decoder call,
development outcome, transcript, or confirmation-array access is permitted
during lock creation.

After successful review the file and directory are immutable predecessor
evidence for Phase 2. A failed or partial write is retained as
`invalid_pre_decode`; it is never repaired in place.

## 2. Source and exclusion inputs

Rebuild the exact v4 10 dB source files and all complete frames using the v2
source adapter's source/acquisition/identity semantics. Do not use only its
selected-frame list as the candidate pool.

The excluded predecessor set comes from the exact selected-frame rows in:

- invalid 10 dB v1 `real_data_lock.json`;
- completed 10 dB v2 `real_data_lock.json`.

The two lock files are byte-identical and must be proven so. Their union is
exactly 384 unique frame identities and 384 unique payload identities, with
128 per stratum. A disagreement, duplicate within either lock, or nonidentical
selection fails.

The 16 dB acquisition has a different acquisition identity and contributes
no 10 dB exclusion rows, but remains bound through the predecessor contract.

## 3. Full-pool reconstruction

For every complete frame in each registered stratum, reconstruct the exact
row fields:

```text
stratum
frame_id
frame_identity
payload_identity
source_record_sha256
source_pair_start
source_pair_end
```

Canonical full-pool order is stratum order
`d1024_bw120,d1024_bw180,d1024_bw200`, then ascending integer `frame_id`.
Require global uniqueness of frame and payload identities.

Remove the exact predecessor identities. Rank remaining rows independently
per stratum by:

`SHA256("binary_ldpc_v5_10db_partition_v1|<stratum>|<frame_identity>")`

Sort by `(ranking_sha256, frame_identity)`; the second key is a mandatory
deterministic tie-breaker.

## 4. Role rows

Confirmation uses partition ranks 0--127. Development uses partition ranks
128--639.

Every role row contains exactly:

```text
role
stratum
partition_rank
role_rank
ranking_sha256
frame_id
frame_identity
payload_identity
source_record_sha256
source_pair_start
source_pair_end
```

`role` is exactly `confirmation` or `development`.
`role_rank` is 0--127 for confirmation and 0--511 for development.

Canonical role-row order:

1. all confirmation rows, stratum order then role rank;
2. all development rows, stratum order then role rank.

Require 128 confirmation and 512 development rows per stratum, no identity or
payload overlap between roles, and no overlap with the predecessor set.

## 5. Partition lock schema

The lock has exactly:

```text
schema
source_binding
predecessor_binding
predecessor_selection
partition_policy
pool_summary
role_rows
role_digests
access_contract
partition_sha256
```

Constants:

- `schema="binary_ldpc_v5_10db_partition_lock_v1"`

`source_binding` fields:

```text
source_adapter
source_adapter_sha256
source_lock_schema
source_lock_sha256
source_lock_file_sha256
raw_main_sha256
raw_chunk_sha256
```

`source_lock_file_sha256` is SHA256 of the canonical rebuilt v2 source-lock
bytes, not a new file path.

`predecessor_binding` is the complete self-hashed record produced from
`predecessor-contract.md`, including its `binding_sha256`.

`predecessor_selection` fields:

```text
v1_lock_file_sha256
v2_lock_file_sha256
lock_bytes_identical
identity_count
frame_identities_sha256
payload_identities_sha256
counts_by_stratum
```

Identity digests hash compact JSON of the lexicographically sorted unique
string list.

`partition_policy` fields:

```text
selection_domain
ranking
tie_breaker
confirmation_partition_ranks
development_partition_ranks
frame_len_symbols
dimension
mapping
```

Exact values are the domain/ranking above, `[0,127]`, `[128,639]`, `256`,
`1024`, and `gray`.

`pool_summary` fields:

```text
complete_frames_by_stratum
excluded_frames_by_stratum
eligible_frames_by_stratum
all_frame_identities_sha256
all_payload_identities_sha256
eligible_frame_identities_sha256
eligible_payload_identities_sha256
```

Each digest uses canonical full-pool order, not sorted order.

`role_rows` is the exact canonical list from section 4.

`role_digests` fields:

```text
confirmation_count
development_count
confirmation_rows_sha256
development_rows_sha256
all_role_rows_sha256
```

Row digests hash compact JSON of the exact ordered row list.

`access_contract` is exactly:

```json
{
  "confirmation_api": "absent_phase1",
  "confirmation_decoding_authorized": false,
  "development_api": "development_arrays_for_frame_v1",
  "role_enforcement": "exact_locked_row_membership_before_array_load"
}
```

`partition_sha256` is SHA256 of compact canonical JSON excluding only
`partition_sha256`, using the common ASCII/sorted-key/no-NaN contract.

## 6. Validation and access proof

`validate_partition_lock` reconstructs the predecessor binding, v2 source
lock, full pool, exclusion set, rankings, role rows, every digest, and the
self-hash. Comparing only embedded hashes is insufficient.

Tests patch the underlying array loader and prove it is never invoked for a
confirmation/changed/unknown row. They also mutate every schema field,
source/predecessor link, pool count/digest, rank/tie, role/order/slice,
access-contract field, and locally recompute outer self-hashes; all must fail.
