# Frozen H2 Construction Contract

This file resolves P1-04/T1-H2 ambiguity. All integer and byte conventions
below are normative.

## 1. Constants

- `construction_id = "binary_ldpc_v5_h2_cw3_v2"`
- `construction_version = "2"`
- `status = "candidate_only_not_qualified"`
- `block_length = 256`
- `plane_ids = [0,1,2,3,4,5,6,7,8,9]`
- `h2_row_counts = [16,16,16,24,24,32,48,80,88,48]`
- `trial_bound = 1000`
- `magic = b"HGF2V5H2"`

The H1 matrix for each plane is the exact v4 selected matrix bound by the
promoted v4 selection manifest.

## 2. Seed and trial enumeration

For plane `p`, compute:

```python
label = f"binary_ldpc_v5_h2_cw3_v2|plane={p}".encode("ascii")
base_seed = int.from_bytes(hashlib.sha256(label).digest()[:8], "little")
```

Enumerate `trial` in exact increasing order `0,1,...,999`.

For each trial instantiate exactly:

```python
rng = np.random.Generator(np.random.PCG64(base_seed + trial))
```

No global RNG, platform entropy, modulo reduction, seed wrapping, or alternate
bit generator is permitted.

## 3. Candidate matrix generation

Let `e = h2_row_counts[p]`. Start with
`h2 = np.zeros((e,256), dtype=np.uint8)`.

For columns `col=0..255` in increasing order:

```python
support = np.sort(
    rng.choice(np.arange(e, dtype=np.int64), size=3, replace=False)
)
h2[support, col] = 1
```

Repeated H2-only column supports are allowed. There is no resampling within a
trial.

Accept the first trial satisfying all conditions:

1. `h2` is binary, shape `(e,256)`, and every column has weight exactly 3;
2. no H2 row has weight zero;
3. exact GF(2) rank of H2 equals `e`;
4. `stacked = np.vstack((h1,h2)).astype(np.uint8)` has exact rank
   `h1_rows + e - 1`;
5. all 256 full stacked column-support tuples are unique.

The minus one is the unique unavoidable cross-block dependency: both H1 and
H2 have odd column weight three, so XORing every row of either matrix yields
the same 256-bit all-ones vector. Therefore the stacked rank can never be
`h1_rows + e`. Requiring `h1_rows + e - 1` is the maximal possible rank and
proves that H2 contributes exactly `e - 1` new independent checks. All `e`
transmitted H2 syndrome bits remain charged to leakage; the redundant bit is
not subtracted or hidden.

GF(2) rank uses the same exact integer row-elimination semantics as v4
`codebook_v4.gf2_rank`. If no trial is accepted, raise
`ValueError("v5 H2 construction exhausted frozen trials")`.

## 4. Canonical matrix bytes

For accepted plane `p`, serialize:

```python
magic
+ np.asarray([p, e, 256], dtype="<u4").tobytes()
+ h2.tobytes(order="C")
```

Parsing requires exact magic, exact total length, exact registered plane/row
count, and all acceptance checks against the exact bound H1. Return a
detached writable `np.uint8` matrix. Every public matrix accessor also returns
a detached writable copy.

## 5. Diagnostics

Each plane entry contains exactly:

- `plane_id`
- `construction_seed`
- `accepted_trial`
- `h2_shape`
- `h2_rank`
- `stacked_shape`
- `stacked_rank`
- `h2_column_weight_min`
- `h2_column_weight_max`
- `h2_row_weight_min`
- `h2_row_weight_max`
- `h2_zero_rows`
- `h2_four_cycles`
- `h2_duplicate_column_support_count`
- `stacked_duplicate_column_support_count`
- `canonical_bytes_sha256`

Four-cycles use the exact v4 overlap formula. Duplicate support count is
`256 - number_of_unique_support_tuples`.

## 6. Manifest and hashes

Manifest fields are exactly:

- `schema = "binary_ldpc_v5_h2_manifest_v1"`
- `construction_id`
- `construction_version`
- `status`
- `domain`
- `candidates`
- `manifest_sha256`

`domain` fields are exactly:

- `block_length`
- `plane_ids`
- `h2_row_counts`
- `trial_bound`
- `h1_codebook_manifest_sha256`
- `h1_selection_sha256`

Candidates are the ten exact diagnostic entries in plane order.

All JSON hashes use:

```python
json.dumps(
    value,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
    allow_nan=False,
).encode("ascii")
```

`manifest_sha256` is SHA256 of the complete manifest object excluding only
the `manifest_sha256` field. No timestamps, paths, NumPy scalars, runtime
values, or environment fields enter the manifest.

## 7. Test requirements

T1-H2 pins all ten accepted trials, canonical byte SHA256 values, ranks,
shapes, and diagnostics after independent reconstruction. It also covers
wrong magic/plane/rows/length/bit/weight/rank/stacked rank/support uniqueness,
manifest self-hash, H1 binding, trial-bound exhaustion, mutation isolation,
and cache isolation.
