# Proposal: Binary LDPC Long-Frame and Incremental-Redundancy v3

## Why

`ldpc_formal_v2` is reproducible but did not pass synthetic promotion. Its
development evidence improved monotonically with added redundancy while OSD
variants were indistinguishable, so the next binary lane must move beyond the
n=64 code family rather than tune the frozen confirmation result.

## Scope of the First Frozen Work Package

- Add an offline, candidate-only long-frame binary codebook component.
- Support exactly n=256, 512, and 1024.
- Produce deterministic row-prefix-nested parity-check candidates with
  canonical bytes, hashes, structural diagnostics, and a fail-closed manifest.
- Preserve all v1/v2 modules, APIs, outputs, and conclusions.
- Do not wire a decoder, run development/confirmation frames, install a new
  backend, or make a promotion claim.

## Later Work, Not Yet Authorized

- Development-only FER evaluation and code-family selection.
- Per-bit-plane likelihoods and multistage decoding.
- Frozen incremental-redundancy policy selection.
- Fresh synthetic or real qualification beyond the frozen Phase 6 package.

## Phase 6 Authorized Scope

- Add a read-only bridge from the existing 20 dB q=1024 sidecars to exact
  256-symbol formal frames while binding the source `.ttbin` header/chunk,
  sidecars, metadata, processing rule, and hashes.
- Derive the frozen ten-plane calibration from sacrificed bw100 frames only.
- Add verifier-bound synthetic qualification and, only after strict synthetic
  promotion, a bounded real qualification over bw120/bw180/bw200.
- Keep claims limited to the current 20 dB acquisition and frozen processing
  domain. Do not modify or rerun the Polar baseline.

## Affected Specs

- Add `binary-ldpc-long-frame`.
