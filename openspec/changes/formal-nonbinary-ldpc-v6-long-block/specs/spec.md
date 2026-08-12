# Formal Nonbinary LDPC v6 Long-Block Development

## ADDED Requirements

### Requirement: Additive Development Identity

The system SHALL add `nbldpc_formal_v6_long` without changing v1-v5 source,
artifacts, plans, identities, seeds, results, or conclusions.  It SHALL be
labelled development-only until a later qualification change promotes it.

### Requirement: Frozen Field and Frame Domain

The method SHALL use the accepted polynomial-basis `GF(1024)` field and
natural-symbol mapping with exactly 1024 symbols per frame.  Input symbols
outside `0..1023`, wrong frame lengths, non-finite priors, malformed syndromes,
or codebook identity drift SHALL fail closed before verification.

### Requirement: Deterministic Fixed-Rate Codebooks

The system SHALL construct exactly two deterministic PEG codebooks:
`(n,m)=(1024,320)` and `(1024,480)`.  Every variable SHALL have degree two;
parallel edges are forbidden; check degrees SHALL differ by at most one; all
coefficients SHALL be nonzero; and every matrix SHALL have full GF(1024) row
rank.  Canonical bytes and a manifest SHALL permit independent reconstruction
and hash verification.

### Requirement: Bounded Layered FFT-QSPA

The decoder SHALL use ascending-row layered FFT-QSPA, damping .75, no more than
50 complete iterations, exact whole-graph syndrome checks, deterministic
ordering, and workers=1 for production.  Message updates SHALL normalize and
fail closed on invalid mass, NaN, Inf, or resource-cap breach.  No fallback
decoder is permitted in this change.

### Requirement: Verification and Accounting

Only a syndrome-consistent candidate MAY invoke the accepted 64-bit Toeplitz
verification.  Syndrome disclosure SHALL be exactly `10*m` bits and an invoked
tag SHALL add exactly 64 key-dependent bits.  Verification seeds remain public
control and SHALL follow the existing canonical packing and seed-ID rules.

### Requirement: Engineering Acceptance

Acceptance SHALL cover: deterministic reconstruction, full rank, degree and
cycle metrics, GF(4)/GF(8) exhaustive oracle vectors, noiseless and planted
error cases, coefficient/syndrome orientation, deterministic repeatability,
invalid input, allocation cap, raw and semantic tamper, fake execution, strict
fake replay, v5 regression, frozen-directory hashes, and absence of official
v6 output.  Tests that exercise execution SHALL pass an explicit fake runner.

### Requirement: Scientific Stop Boundary

This change SHALL NOT create confirmation data, a promotion decision, a real
lock, or a comparison claim.  A development plan and run require main-thread
review after engineering acceptance.  Any qualification requires a new
OpenSpec change with fresh roots/seeds and pre-registered gates.

