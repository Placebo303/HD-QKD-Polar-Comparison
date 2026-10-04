# Design: Formal Nonbinary LDPC N0 Backend Contract

## Decision

Create an additive module under
`comparison_bench/src/comparison_bench/formal_ir/` for the new method identity
`nbldpc_formal_v1`. The first slice exposes only an immutable field
specification, deterministic GF(2^m) arithmetic, and a read-only preflight.
It does not expose a decoder or runner.

## Frozen Field Domain

- Supported q values: 2, 4, 8, 16, 32, 64, 128, 256, 512, and 1024.
- Symbol encoding: unsigned polynomial-basis coefficient integers in
  `[0, q)`, with bit i representing the coefficient of x^i.
- Addition/subtraction: coefficient-wise XOR.
- Multiplication: polynomial multiplication reduced by the explicitly recorded
  primitive polynomial for the selected field.
- Every field specification records method identity, backend identity and
  version, q, m, primitive polynomial, basis, symbol encoding, and a canonical
  SHA256 identifier.

The primitive-polynomial table is part of the frozen implementation contract.
Construction must verify that the selected polynomial generates all nonzero
field elements; a bad or incomplete cycle fails closed.

## Preflight

The read-only preflight accepts a requested q and optional expected field ID.
It:

1. validates the exact supported domain;
2. constructs the deterministic internal field without importing or falling
   back to `qldpc_reference` or an optional external package;
3. verifies the multiplicative cycle, identities, inverses, distributivity,
   symbol bounds, and repeatable canonical field ID;
4. returns structured status and metadata without writing files.

Success status is `ok`. Unsupported q returns `unsupported_domain`.
Representation or arithmetic mismatch returns `backend_unavailable`. No
exception or silent lower-q/backend fallback may be reported as success.

## Integration Boundary

The new module may be re-exported by `formal_ir.__init__`, but it must not
modify the current `qary_ldpc.py`, `qldpc_reference.py`, benchmark dispatch, or
method-status classifier. Later N1/N2 tasks may consume this contract only
after separate task review.

## N1 Codebook Contract

N1 freezes one bounded structural family. It does not claim decoder
performance.

- Field domain: every N0-supported q, with q=1024 required in tests.
- Frame length: exactly 64 q-ary symbols.
- Mother matrix: 32 rows by 64 columns.
- Rate-compatible check counts: 16, 24, and 32, each the exact ordered row
  prefix of the same mother matrix.
- Topology: a 32-column cyclic/protograph-style information half plus a
  32-column identity parity half. Each row contains the identity coefficient
  1 and three information-half edges at three distinct construction-seed-
  derived circulant shifts.
- Coefficients: every information edge has an explicit nonzero GF(q)
  coefficient derived deterministically from SHA256 over the frozen
  construction inputs. No NumPy RNG, process hash, backend fallback, or
  decoder state participates.
- Rank: calculate by Gaussian elimination using the pinned N0 GF(q)
  arithmetic. Every prefix must have rank equal to its check count. Integer,
  real, or GF(2) rank is not acceptable evidence.

The right identity half makes the nested prefix rank property explicit rather
than relying on a random search. Structural rank is only a codebook-contract
check; it is not decoding or distance evidence.

## N1 Canonicalization And Manifest

Each codebook's canonical byte sequence is:

1. ASCII magic `NBLDPC1\n`;
2. one compact, key-sorted ASCII JSON header followed by `\n`;
3. the complete matrix in row-major unsigned 16-bit big-endian order.

The header records method/schema identity, complete N0 field metadata and
field ID, q, dimensions, check count, mother dimensions, topology, ordered
circulant shifts, construction seed, coefficient derivation, matrix ordering,
and coefficient encoding. The matrix payload records every coefficient.

The codebook ID is SHA256 of those canonical bytes. A top-level manifest
records the complete field specification, frozen family parameters, ordered
entries, ranks, byte lengths, codebook IDs, and the exact prefix relationship.
Its manifest ID is SHA256 of compact key-sorted ASCII JSON before adding the
manifest ID. Verification reconstructs every byte/hash/rank/prefix and fails
closed as `unsupported_domain` or `codebook_invalid`; it does not repair input.

N1 APIs are pure and in-memory. They do not write output files or run a
decoder. File persistence and immutability rules belong to a later
pre-registered runner.

The frozen public API is:

- `gf_rank(matrix, field) -> int`;
- `build_nonbinary_codebook_family(q, *, construction_seed=2026072601)
  -> (manifest, matrices)`, where `matrices` maps ordered check counts to
  immutable row tuples;
- `verify_nonbinary_codebook_family(manifest, matrices) -> status report`.

The seed is a non-boolean integer in `[0, 2^64)`. Shift candidates are derived
from SHA256 of ASCII
`NBLDPC1|shift|<seed>|<slot>|<attempt>` and accepted modulo 32 until three
distinct shifts exist. The coefficient for `(row, edge)` is
`1 + int(SHA256("NBLDPC1|coef|<q>|<seed>|<row>|<edge>"), 16) mod (q-1)`.
These strings are encoded as ASCII. This derivation is part of the canonical
contract, not an implementation choice.

## N2 Decoder Feasibility Decision

N2 starts with a bounded full-message probability-domain FFT-QSPA decoder over
the additive GF(2)^m representation already frozen by N0. This is a feasibility
implementation, not the production-decoder selection.

The choice follows two primary-source constraints:

- HD-QKD nonbinary reconciliation is asymmetric Slepian-Wolf coding: Alice
  discloses a GF(q) syndrome and Bob decodes with his correlated q-ary symbols
  as side information. The q-ary symmetric channel is an explicit supported
  model: https://arxiv.org/abs/2305.08631
- Direct q-ary check convolution is order q^2, while a Walsh-Hadamard transform
  over q=2^m reduces it to order q log q. EMS truncation can reduce work but
  requires an additional, non-trivial frozen rule for retained symbols and the
  missing-message tail: https://arxiv.org/abs/1407.4342

Therefore N2 does not invent an EMS tail rule. EMS/min-sum remains a later
bounded alternative if full-message q=1024 evidence exceeds the caps below.

## N2 Frozen Domain And API

- Exact codebooks: verified N1 n=64 families only, at check counts 16, 24, or
  32.
- q: any N0-supported value, with q=1024 required by focused feasibility tests.
- Channel prior: q-ary symmetric, with frozen `p` strictly in
  `(0, (q-1)/q)`. For Bob symbol y, the probability is `1-p` at x=y and
  `p/(q-1)` elsewhere.
- Decoder input contains Bob symbols, Alice's disclosed syndrome, the verified
  N1 manifest/matrices, check count, frozen p, and max iterations. It has no
  Alice-symbol argument or truth callback.
- Iterations: flooding schedule, deterministic row/edge/symbol ordering,
  `1 <= max_iter <= 20`, default 20, no damping, no random tie breaking.
- Resource cap: n=64, at most 32 checks, N1 row weight exactly four,
  q<=1024, and declared dense-message storage at most 16 MiB. Exceeding a cap
  returns `aborted_resource_limit`; it does not switch decoder or q.

The frozen public API is:

- `qsc_symbol_priors(bob_symbols, q, p)`;
- `nonbinary_syndrome(matrix, symbols, field)`;
- `decode_nonbinary_fft_qspa(bob_symbols, syndrome, manifest, matrices, *,
  check_count, p, max_iter=20)`;
- `symbols_to_msb_bits(symbols, q)`;
- `nonbinary_disclosure_accounting(check_count, q, *,
  verification_invoked, verification_tag_bits=64, public_control_bits=0)`;
- `verify_nonbinary_symbols(alice_symbols, bob_symbols, q, locked_seed, *,
  invoked)`.

## N2 Message And Status Semantics

Variable-to-check and check-to-variable messages are dense float64 probability
vectors in canonical symbol order 0..q-1. Each update is normalized. The
Walsh-Hadamard transform uses the polynomial-basis integer XOR ordering.
Nonzero field coefficients are handled by exact N0 multiplication
permutations before and after additive-group convolution. Negative inverse-
transform roundoff is clipped to zero before normalization; a zero/nonfinite
normalizer is `decoder_error`, never success.

The decoder stops only when the reconstructed symbols reproduce Alice's
disclosed GF(q) syndrome. That produces `syndrome_consistent`, not
`verified_success`: another codeword in the same coset can still be wrong.
Exhausting iterations is `decode_failed`. Other statuses are
`invalid_input`, `unsupported_domain`, `codebook_invalid`,
`aborted_resource_limit`, and `decoder_error`. Every return records iteration
count, consistency, q/n/check count, field/codebook IDs, and deterministic
resource counters.

## N2 Mapping, Verification, And Disclosure

Formal verification remains separate from the decoder. Symbols use exactly m
bits each in MSB-first order, preserving leading zeros. The existing locked
Toeplitz `verification_result` is invoked only after syndrome consistency.

For r disclosed syndrome symbols over q=2^m:

- syndrome disclosure is exactly `r*m` key-dependent bits;
- an invoked verification tag adds exactly its tag length to key-dependent
  disclosure;
- a non-invoked tag adds zero;
- public control is recorded separately and never folded into syndrome bits.

These pure helpers establish mapping/accounting semantics only. N2 creates no
qualification runner, output, calibration data, promotion decision, or fair
comparison.

## N3 Cost Evidence And Claim Domain

A read-only N2 cost probe on 2026-07-26 used q=1024, n=64, 32 checks, and 20
iterations. Fixed seeds produced 18 errors at p=.20 and 22 errors at p=.30;
both frames returned `decode_failed` in 5.42 and 5.46 seconds respectively,
with 3,145,728 declared dense-message bytes. These are cost observations, not
development or qualification outcomes.

N3 freezes exactly:

- method `nbldpc_formal_v1`, q=1024, n=64, polynomial-basis mapping;
- q-ary symmetric channel strata p=.20 and p=.30;
- 8 sacrificed development frames and 32 immutable confirmation frames per
  stratum;
- output root
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`;
- one plan-only creation, one execution, and any number of read-only
  verifications; no overwrite or resume into a partial directory.

The domain reflects the repository's d=1024 medium-SER target. N3 makes no
claim for other q, frame lengths, channels, or real data.

## N3 Synthetic Generation

Every frame has an independent NumPy `PCG64` seed recorded in the pre-run
plan. Development seeds use disjoint ranges rooted at `202607300000` and
`202607310000`; confirmation seeds use `202607320000` and `202607330000`.
Within a frame the exact call order is:

1. `integers(0, 1024, size=64, dtype=int64)` for Alice;
2. `random(64) < p` for the error mask;
3. `integers(1, 1024, size=64, dtype=int64)` for 64 candidate nonzero errors;
4. select candidates by the mask and set Bob to Alice XOR error.

Frame order is p=.20 then p=.30, each by ascending index. IDs encode method,
q, p, role, and zero-padded index. Development and confirmation seeds, frame
IDs, Alice arrays, Bob arrays, and atomic `(role,stratum,index,pair_idx)` keys
must have zero overlap as applicable. The generator contract and reconstructed
arrays receive canonical SHA256 hashes. Confirmation arrays are never exposed
to policy selection.

## N3 Policy Grid And Selection

N3 freezes eight global policies, the Cartesian product of:

- rate margin in syndrome symbols: 0 or 7;
- decoder p scale: 1.00 or 1.25;
- max iterations: 10 or 20.

For nominal stratum p, compute
`ceil(64 * (h2(p) + p*log2(1023)) / 10) + margin` and choose the smallest N1
check count in 16/24/32 that meets it, failing closed if none exists. Decoder
p is `p*scale`, which must remain inside the frozen QSC domain. This selects
24 or 32 checks at p=.20 and 32 checks at p=.30 without per-frame truth.

Every policy runs every development frame in plan order. Consistent results
receive independent locked 64-bit Toeplitz verification. One global policy is
selected by, in order:

1. most `verified_success` outcomes across all 16 development frames;
2. least total key-dependent disclosure bits;
3. least total decoder iterations;
4. lexicographically smallest canonical policy SHA256.

No confirmation field participates in selection. The selected canonical
policy and hash are persisted before confirmation starts.

## N3 Confirmation And Promotion Gate

The selected global policy runs all 64 confirmation frames in frozen order.
Every requested frame remains in the denominator. Decoder consistency is
verified with a unique locked Toeplitz seed only when consistency is reached.

Promotion requires, independently in each 32-frame stratum:

- at least 31 `verified_success` outcomes;
- exactly 32 requested and denominator-included outcomes;
- zero unclassified, internal, provenance, accounting, codebook, unsupported-
  domain, or backend failures;
- exact transcript/disclosure reconciliation and a valid artifact DAG.

The 31/32 gate is retained because N3 uses the same 32-frame per-stratum
denominator and the same formal near-zero-observed-FER promotion semantics as
the prior formal synthetic gate. It is not reused for a changed denominator.
Failure of either stratum yields `non_promoted` and forbids N4 real-data work.
Confirmation must never be tuned or rerun under this change.

## N3 Resource And Stop Rules

- Per decoder call: N2 caps plus 10 wall-clock seconds measured around the
  completed call; a slower call is retained as `aborted_resource_limit`.
- Complete execution: 1,800 wall-clock seconds, single process, no parallel
  workers. On cap, all remaining requested confirmation frames are materialized
  as denominator-included `aborted_resource_limit`.
- No policy may change after development selection.
- Any plan/provenance/generator/codebook/hash mismatch stops before
  confirmation and finalizes an `invalid_run`.
- Any unexpected per-frame exception becomes retained `decoder_error`; it does
  not silently remove the frame.

## N3 Artifacts And Strict Verification

The additive top-level contract is exactly:

1. `pre_run_plan.json`;
2. `formal_frame_outcomes.csv`;
3. `formal_transcript.jsonl`;
4. `formal_run_manifest.json`;
5. `formal_codebook_manifest.json`;
6. `formal_policy_manifest.json`;
7. `formal_qualification_report.json`.

The plan records exact generation seeds/order, CSPRNG Toeplitz seed records,
zero-overlap proof, policy hashes/order, caps, generator/source/code/config
hashes, environment and git snapshot, status precedence, and artifact schema.
Toeplitz seed length is 703 bits for 640 input bits and a 64-bit tag; all
development-policy/frame and confirmation-frame seed IDs are globally unique
and disjoint from locally discoverable prior formal plans.

Each public transcript contains an Alice-to-Bob syndrome event, a Bob-local
decoder event, and, only after consistency, an Alice-to-Bob verification-tag
event. Key-dependent disclosure is syndrome bits plus invoked tag bits.
The 703-bit public Toeplitz seed is public control and remains separate.

The strict read-only verifier reconstructs generator frames, N1 codebooks,
policy selection, confirmation order/denominators, transcript bytes, disclosure
accounting, seed bindings, source hashes, artifact DAG, gate counts, and report
decision. It verifies completed promoted and non-promoted packages fully.
Infrastructure-finalized `invalid_run` packages are verified against their
declared partial state and cannot be promoted. Existing artifacts are never
rewritten; any superseding attempt requires a new OpenSpec change and output
root.

## Simpler Alternative

Depending directly on an external GF package would be shorter, but it would
not satisfy the current q=1024, pinned-representation, and fail-closed
requirements without first proving the same contract. The bounded internal
field layer is therefore the smallest acceptable N0 slice.
