# Design: Binary LDPC v5 Incremental Redundancy

## 1. Immutable predecessors

Bind and strictly replay:

- promoted corrected v4 development and synthetic packages;
- non-promoted 16 dB transfer package;
- invalid-pre-execute 10 dB v1 two-file package;
- non-promoted 10 dB v2 transfer package.

No predecessor file may be changed, overwritten, reinterpreted, or rerun.
The v5 implementation is versioned and additive.

## 2. Pre-registered real partition

Rebuild the exact 10 dB source pool from the v2 source adapter. Exclude all
384 frame identities used by v2. For each stratum rank every remaining frame:

`SHA256("binary_ldpc_v5_10db_partition_v1|<stratum>|<frame_identity>")`

Freeze, before any v5 decoding:

- ranks 0--127: sealed real confirmation, 128 frames;
- ranks 128--639: sacrificed development, 512 frames.

Require 640 eligible frames per stratum, exact source/payload uniqueness, no
overlap between roles or any predecessor selection, and unchanged source
hashes. The partition lock binds both roles, but development runners may load
only development arrays. Tests prove confirmation access is impossible
through development APIs.

## 3. Frozen policy candidates

All candidates retain q=1024, Gray mapping, 256 symbols, the v4 channel model,
selected v4 H1 matrices, `ldpc==2.4.1`, serial schedule, product-sum BP, exact
syndrome validation, and canonical transcript/accounting.

### V5-C0: control

Exact v4 policy: H1 only, max_iter=50, OSD_0, one 64-bit Toeplitz check.
It is measured but cannot be selected unless it independently meets the v5
development gate.

### V5-C1: stronger local decode

H1 only, max_iter=100, `OSD_CS`, order 2, one final 64-bit Toeplitz check.
No additional syndrome leakage.

### V5-C2: two-round incremental redundancy

Round 0 is exact v4. After a Toeplitz mismatch:

1. emit one public NACK control bit;
2. disclose an independently constructed H2 syndrome for every plane;
3. decode the stacked `[H1; H2]` system with max_iter=100, `OSD_CS`, order 2;
4. verify once with a second independently derived 64-bit Toeplitz tag.

H2 row counts by plane are:

`[16,16,16,24,24,32,48,80,88,48]`

Combined H row counts are:

`[32,32,32,48,48,64,96,160,224,240]`

For each plane, reconstruct H2 deterministically from domain
`binary_ldpc_v5_h2_cw3_v2`, plane ID, and trial. Every H2 column has weight
three; zero rows are forbidden; H2 has full row rank; stacked rank equals the
combined row count minus the one unavoidable shared all-ones row-space
vector; canonical bytes and diagnostics are self-hashed. Thus H2 contributes
exactly `H2_rows - 1` new independent checks while leakage charges all
transmitted H2 syndrome bits. Duplicate H2 column supports are allowed only
when the full stacked H1/H2 column supports remain unique. Trials are bounded
and frozen in the manifest.

Round-0 success discloses 584 syndrome bits plus one 64-bit tag. Fallback
discloses an additional 392 syndrome bits plus a second 64-bit tag. NACK and
both 2623-bit public seeds are recorded separately. Fallback verification
uses two independent seeds and reports `epsilon_ec=2^-63` by union bound;
round-0 success reports `2^-64`. Caps are 20 decoder calls, 32 events, and
10 seconds per frame.

## 4. Development

Run all three candidates on all 512 development frames in each of the three
real strata. Candidate order, frame order, roots, and two seeds per
candidate/frame are frozen before execution.

A selectable candidate must achieve at least 510/512 verified successes in
every stratum, include all denominators, and have zero backend, source,
internal, accounting, resource, syndrome, unclassified, or provenance
failures.

Rank selectable candidates by:

1. lowest exact mean key-dependent disclosure over all 1536 frames;
2. highest minimum-stratum verified successes;
3. highest total verified successes;
4. lowest exact total runtime;
5. candidate ID.

The development package is sacrificed and can never be confirmation evidence.
If no candidate passes, stop; do not create synthetic output.

## 5. Fresh synthetic confirmation

Using the selected frozen policy, generate 128 nominal and 128 stress frames
from the existing exact v4 channel model with new domain-separated CSPRNG
roots and two new Toeplitz seeds per frame. Require at least 126/128 in both
strata, all denominators, and zero forbidden failures.

Prepare, main review, execute, and read-only verify are separate. Failure is
immutable; no tuning or rerun. Real output must not exist unless synthetic
strictly promotes.

## 6. Sealed real qualification

After synthetic promotion only, prepare a plan for the pre-locked 128 real
confirmation frames in each bw layer. Generate fresh roots and two seeds per
frame, isolated from every predecessor, development, and synthetic package.

Execute 384 frames exactly once. Each layer requires at least 126/128
verified successes, all denominators, and zero forbidden failures. Retain
promoted or non-promoted evidence without tuning or rerun. The verifier is
read-only and reconstructs the entire source/method/partition/seed/transcript/
leakage/accounting/gate DAG with `decoder_reexecution=false`.
