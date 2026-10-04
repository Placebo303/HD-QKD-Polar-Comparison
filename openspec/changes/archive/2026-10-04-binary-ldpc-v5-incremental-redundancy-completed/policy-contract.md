# Frozen v5 Policy Manifest and Hash Contract

This file resolves P1-05/P1-06 policy provenance ambiguity.

## 1. Common canonical hashing

All policy hashes use compact ASCII JSON with sorted keys, comma/colon
separators, `allow_nan=False`. A `*_sha256` self-hash excludes only its own
field.

Candidate order is exactly `V5-C0,V5-C1,V5-C2`. Plane order is 0--9.

## 2. Decoder binding

A decoder binding contains exactly:

```text
max_iter
bp_method
schedule
omp_thread_count
serial_schedule_order
osd_method
osd_order
error_channel_source
decoder_sha256
```

Common values:

- `bp_method="product_sum"`
- `schedule="serial"`
- `omp_thread_count=1`
- `serial_schedule_order=[0,1,...,255]`
- `error_channel_source="v4_bob_conditioned_per_position"`

OSD_0 binding uses max_iter 50, `OSD_0`, order 0.
Strong binding uses max_iter 100, `OSD_CS`, order 2.

`decoder_sha256` hashes the binding excluding itself.

## 3. H1 binding

`h1_binding` contains exactly:

```text
selection_schema
selection_sha256
codebook_manifest_sha256
channel_model_sha256
plane_matrix_sha256
```

Values come from the exact promoted v4 selection. `plane_matrix_sha256` is
an array of exactly ten lowercase SHA256 hex strings in plane order. For
plane `p`, read its selected integer candidate ID from the bound promoted-v4
selection, reconstruct
`codebook_v4.matrix_for(p, selected_candidate_id)`, and hash exactly
`codebook_v4.canonical_matrix_bytes(matrix, plane_id=p)`. This deliberately
reuses the historical `HGF2V4` magic plus `<u4` `[rows,cols]` and row-major
`uint8` payload; no v5-specific H1 encoding, candidate-entry hash, raw-array
hash, or concatenated ten-plane hash is permitted.

## 4. H2 binding

`h2_binding` contains exactly:

```text
active
manifest_schema
manifest_sha256
h2_row_counts
plane_matrix_sha256
```

All candidates bind the exact H2 manifest, row counts, and ten canonical H2
byte hashes. `active=false` for C0/C1 and `active=true` for C2. An inactive
binding is still provenance, not permission to substitute another H2.

## 5. Preflight entries

Each policy contains `preflight`, an exact ordered list. Entry fields:

```text
candidate_id
pass_id
plane_id
matrix_kind
h_rows
h_cols
matrix_sha256
decoder_sha256
```

C0/C1 contain ten pass-0 entries in plane order:

- matrix kind `H1`;
- H1 row count and 256 columns;
- the corresponding single-plane HGF2V4 canonical-bytes hash defined in
  section 3;
- candidate's round-0 decoder hash.

C2 contains those ten pass-0 entries followed by ten pass-1 entries:

- matrix kind `H1_H2`;
- combined registered row count and 256 columns;
- SHA256 of exact canonical stacked bytes defined as
  `b"HGF2V5ST" + np.asarray([plane,rows,256],dtype="<u4").tobytes() +
  stacked.astype(np.uint8).tobytes(order="C")`;
- fallback decoder hash.

No deduplication or shape-only preflight is allowed.

## 6. Verification binding

`verification` contains exactly:

```text
locked_seed_count
round0_tag_bits
fallback_tag_bits
max_checks
epsilon_round0
epsilon_fallback
```

Common `locked_seed_count=2`, `round0_tag_bits=64`, and
`epsilon_round0="1/18446744073709551616"`.

C0/C1 use fallback tag 0, max checks 1, and
`epsilon_fallback=null`.

C2 uses fallback tag 64, max checks 2, and
`epsilon_fallback="1/9223372036854775808"`.

## 7. Candidate policy records

Each policy contains exactly:

```text
schema
candidate_id
method_id
h1_binding
h2_binding
round0_decoder
fallback_decoder
verification
caps
preflight
policy_sha256
```

Constants:

- `schema="binary_ldpc_v5_policy_v1"`
- `method_id="ldpc_formal_v5"`

Candidate mapping:

- C0: OSD_0 round 0, `fallback_decoder=null`, H2 inactive,
  caps `{wall_s:10.0,decoder_calls:10,events:32}`;
- C1: strong round 0, `fallback_decoder=null`, H2 inactive,
  caps `{wall_s:10.0,decoder_calls:10,events:32}`;
- C2: OSD_0 round 0, strong fallback, H2 active,
  caps `{wall_s:10.0,decoder_calls:20,events:32}`.

`caps` has exactly the key set and numeric values above.

## 8. Policy manifest

The manifest contains exactly:

```text
schema
method_id
h1_selection_sha256
h2_manifest_sha256
candidates
manifest_sha256
```

Constants:

- `schema="binary_ldpc_v5_policy_manifest_v1"`
- `method_id="ldpc_formal_v5"`

`candidates` is the three exact policy records in candidate order.
`manifest_sha256` hashes the manifest excluding itself.

The formal method accepts one complete candidate policy plus the complete
policy manifest. It verifies both self-hashes, exact reconstruction, manifest
membership, H1/H2 bindings, and candidate ID before input disclosure.
Every outcome `policy_sha256` equals the selected candidate policy hash.

## 9. Tamper coverage

Tests independently change and locally re-sign every decoder, H1, H2,
preflight, verification, cap, candidate, manifest membership/order, and
outer-hash relation. They also reject mismatched stacked bytes, selected
matrix hashes, inactive-H2 use, active-H2 omission, and outcome policy drift.
