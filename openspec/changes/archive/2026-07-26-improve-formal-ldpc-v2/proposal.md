# Change: Improve Formal LDPC v2

## Why

`ldpc_formal_v1` is protocol-faithful but did not pass synthetic promotion:
29/32 verified successes at p=.01 and 14/32 at p=.02. All 21 retained
failures were final verification failures after syndrome consistency. A
frame-identical Cascade/LDPC/Polar comparison therefore remains blocked.

## What Changes

- Add a new immutable identity, `ldpc_formal_v2`; preserve v1 code and evidence.
- Short term: evaluate a pre-registered finite-length decoder/rate margin using
  the pinned `ldpc==2.4.1` backend and sacrificed calibration only.
- Medium term: add deterministic n=64 rate-compatible candidate-codebook
  generation, offline screening, and a frozen selected codebook manifest.
- Require fresh synthetic promotion before creating any real LDPC lock.
- If synthetic promotion succeeds, run one fresh, group-disjoint real
  qualification before authorizing the three-method comparison.

## Out of Scope

- Modifying frozen Polar `src/`, `experiments/`, or `tools/`.
- Tuning against confirmation truth or selecting a decoder per frame.
- Reusing or overwriting formal v1 evidence.
- Nonbinary LDPC, AFF3CT integration, network/authentication costs, or a winner
  claim.

## Affected Specs

- `formal-ir-methods`
