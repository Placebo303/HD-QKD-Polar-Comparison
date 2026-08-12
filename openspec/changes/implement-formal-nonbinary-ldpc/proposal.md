# Proposal: Implement Formal Nonbinary LDPC

## Why

The existing `qldpc_reference` method is a useful hard-decision reference, but
it is not a formal nonbinary LDPC implementation. The next safe step is to
establish a deterministic, pinned GF(2^m) backend contract before selecting or
integrating a soft nonbinary decoder.

## Scope

- Add a new formal method identity, provisionally `nbldpc_formal_v1`.
- Implement the N0 field-backend contract and a bounded read-only preflight.
- Implement the N1 deterministic rate-compatible q-ary codebook contract,
  GF(q) rank verification, canonical bytes, and manifest hashing.
- Implement a bounded N2 full-message Walsh-Hadamard QSPA feasibility decoder,
  q-ary symmetric priors, syndrome/coset semantics, MSB-first symbol mapping,
  and exact disclosure-accounting helpers.
- Pre-register and run one additive N3 q=1024 synthetic qualification package
  with disjoint development/confirmation evidence and strict verification.
- Support the intended powers-of-two field domain through q=1024.
- Fail closed on unsupported fields, representation mismatch, arithmetic
  self-test failure, or nondeterministic backend metadata.
- Preserve `qldpc_reference`, all frozen Polar code, and all existing outputs.

## Out of Scope

- A production decoder, decoder-performance claim, or final EMS/min-sum versus
  FFT-QSPA selection.
- New decoder dependencies or dependency installation.
- Real-data qualification, production promotion, or comparison claims.

## Affected Specs

- Add `formal-nonbinary-ldpc`.
