# Delta Spec: Formal Nonbinary LDPC

## Requirement: Independent Formal Identity

The formal nonbinary lane SHALL use `nbldpc_formal_v1`.
`qldpc_reference` SHALL remain unchanged and reference-grade.

## Requirement: Deterministic Field Contract

The N0 backend SHALL support deterministic polynomial-basis GF(2^m)
arithmetic for every power-of-two q from 2 through 1024. It SHALL record the
exact primitive polynomial, basis, symbol encoding, backend identity/version,
and a canonical field identifier.

### Scenario: Intended q=1024 domain

- **WHEN** the N0 preflight requests q=1024
- **THEN** it verifies a complete 1023-element nonzero multiplicative cycle,
  field identities and inverses, distributivity, bounded symbols, and
  repeatable metadata
- **AND** returns `ok` only if every check passes.

## Requirement: Fail-Closed Preflight

The N0 preflight SHALL be read-only and SHALL NOT silently select another
backend, decoder, field representation, or lower q.

### Scenario: Unsupported field

- **WHEN** q is not a supported power of two in [2, 1024]
- **THEN** the preflight returns `unsupported_domain`.

### Scenario: Representation mismatch

- **WHEN** an expected canonical field ID differs from the constructed field
- **THEN** the preflight returns `backend_unavailable`
- **AND** does not continue with a fallback.

## Requirement: No Qualification Claim

N0 evidence SHALL establish backend feasibility only. It SHALL NOT be reported
as decoder feasibility, synthetic qualification, real qualification,
promotion, or a method-comparison result.

## Requirement: Deterministic Rate-Compatible Codebooks

N1 SHALL construct an n=64 nonbinary mother parity-check matrix with 32 rows.
The 16-, 24-, and 32-check codebooks SHALL be exact ordered row prefixes of
that one matrix. The topology SHALL use a cyclic/protograph-style information
half with explicit nonzero GF(q) coefficients and an identity parity half.

### Scenario: q=1024 family

- **WHEN** the same q=1024 field ID and construction seed are supplied twice
- **THEN** both constructions produce byte-identical mother and prefix matrices
- **AND** their GF(q) ranks are exactly 16, 24, and 32.

## Requirement: GF(q) Rank

Rank SHALL be calculated using the pinned N0 GF(q) arithmetic. GF(2), integer,
floating-point, or real-valued rank SHALL NOT justify codebook validity.

## Requirement: Canonical Codebook Evidence

Every codebook SHALL have canonical bytes containing the complete field
representation, dimensions, topology, coefficients, construction seed, and
ordering. Its codebook ID SHALL be the SHA256 of those bytes. The ordered
family manifest SHALL have its own reproducible SHA256 manifest ID.

### Scenario: Tampered evidence

- **WHEN** a field ID, coefficient, rank, prefix relation, codebook ID, or
  manifest ID differs from deterministic reconstruction
- **THEN** verification returns `codebook_invalid`
- **AND** does not repair, replace, or fall back to another codebook.

## Requirement: N1 Evidence Boundary

N1 SHALL remain pure, in-memory structural evidence. It SHALL NOT write
qualification outputs, invoke a decoder, or establish decoder feasibility,
distance/FER performance, qualification, or promotion.

## Requirement: Bounded Syndrome Decoder Feasibility

N2 SHALL provide a deterministic, full-message FFT-QSPA feasibility decoder
over verified N1 codebooks. It SHALL use Bob's q-ary side information and
Alice's disclosed GF(q) syndrome, and SHALL NOT accept Alice's symbols or a
truth callback as decoder input.

### Scenario: Consistent coset result

- **WHEN** the decoder returns symbols whose GF(q) syndrome equals Alice's
  disclosed syndrome
- **THEN** status is `syndrome_consistent`
- **AND** the result is not called verified or correct until the separate
  locked Toeplitz verification succeeds.

### Scenario: Resource cap

- **WHEN** q, n, row weight, check count, iteration count, or dense-message
  storage exceeds the frozen N2 cap
- **THEN** status is `aborted_resource_limit`
- **AND** no alternate decoder, backend, or lower q is selected.

## Requirement: QSPA Check Semantics

Check-node convolution SHALL use the Walsh-Hadamard transform over the
polynomial-basis XOR ordering. Explicit nonzero GF(q) parity-check
coefficients SHALL be applied through exact pinned-field permutations.
Normalization failure or nonfinite state SHALL fail closed as `decoder_error`.

## Requirement: Formal Nonbinary Mapping And Disclosure

Each q=2^m symbol SHALL map to exactly m MSB-first bits including leading
zeros. For r syndrome symbols, key-dependent syndrome disclosure SHALL be
exactly r*m bits. An invoked verification tag SHALL add its exact bit length;
an uninvoked tag SHALL add zero. Public-control bits SHALL remain separate.

### Scenario: Toeplitz verification

- **WHEN** syndrome consistency has been reached
- **THEN** the decoder output and Alice symbols are converted with the same
  MSB-first mapping and passed to the existing locked Toeplitz verifier
- **AND** a mismatch is retained as verification failure, not coerced into
  decoder success.

## Requirement: N2 Evidence Boundary

N2 unit and feasibility checks SHALL NOT be reported as FER performance,
synthetic or real qualification, promotion, production readiness, or a fair
method-comparison result.

## Requirement: Frozen N3 Synthetic Evidence

N3 SHALL use q=1024, n=64, q-ary-symmetric p=.20 and p=.30, with 8 sacrificed
development and 32 immutable confirmation frames per stratum. Generation
seeds, exact RNG call order, frame order, hashes, and development/confirmation
separation SHALL be fixed in the pre-run plan.

## Requirement: Global Development Policy

The eight frozen rate-margin, p-scale, and iteration policies SHALL each run
every development frame. Exactly one global policy SHALL be selected by
verified successes, then disclosure, iterations, and policy hash.
Confirmation evidence SHALL NOT participate in selection.

### Scenario: Confirmation isolation

- **WHEN** confirmation arrays or outcomes are changed in a test fixture
- **THEN** reconstructed development outcomes and selected policy remain
  byte-identical
- **AND** the strict verifier rejects any package whose recorded confirmation
  no longer matches its frozen plan.

## Requirement: Formal Confirmation Gate

Every one of the 64 requested confirmation frames SHALL remain denominator-
included. Promotion SHALL require at least 31/32 verified successes separately
at p=.20 and p=.30, zero prohibited failures, and exact artifact/transcript/
accounting verification.

### Scenario: Gate failure

- **WHEN** either stratum has fewer than 31 verified successes or any
  prohibited failure
- **THEN** status is `non_promoted`
- **AND** N4 real qualification remains unauthorized.

## Requirement: Additive Strict Artifacts

Plan-only SHALL create a fresh directory containing only
`pre_run_plan.json` and SHALL make zero decoder calls. Execute SHALL require
that exact reviewed state and SHALL create the other six frozen artifacts
without overwrite. Verify SHALL be read-only and reconstruct generation,
codebooks, policy selection, outcomes, transcripts, disclosure, hashes, and
gates for both promoted and non-promoted packages.

### Scenario: Invalid execution

- **WHEN** provenance, generator, codebook, plan, resource, or infrastructure
  validation prevents a valid completed package
- **THEN** the runner finalizes an additive `invalid_run` evidence package
- **AND** the strict verifier confirms its partial-state declaration
- **AND** promotion is impossible.
