# Proposal: Binary LDPC Adjacent-Channel v4

## Why

The immutable `ldpc_formal_v3` synthetic qualification is non-promoted:
calibrated confirmation achieved 3/32 and the 1.25x stress stratum achieved
1/32. The package verified strictly and had no provenance, accounting,
internal, or unclassified failures, so it must remain evidence rather than a
tuning set.

Two development-only findings justify a new method identity:

1. The v3 systematic-prefix construction admits explicitly constructible
   very-low-weight codewords. At n=256 its first three prefixes have minimum
   distance upper bound at most 3 and its final prefix has upper bound at most
   6. Rank and column uniqueness therefore did not establish a usable
   finite-length code.
2. The 64 sacrificed bw100 calibration frames contain 16,384 symbols with
   signed modular Alice-minus-Bob deltas exactly in `{0,+1,-1}`:
   12,403 zero, 3,865 plus one, and 116 minus one. Every nonzero delta changes
   exactly one Gray bit. The v3 independent bit-plane BSC confirmation was a
   valid decoder stress test but not a faithful model of the locked TTBIN
   acquisition.

The successor must replace the codebook and consume Bob-conditioned,
plane-specific soft information before it spends evidence on a fresh
confirmation.

## What Changes

- Add an independent method identity, `ldpc_formal_v4`.
- Add a deterministic n=256 anchored column-weight-three binary LDPC family
  with four development candidates per Gray plane and plane-specific fixed
  syndrome lengths.
- Reconstruct a self-hashed adjacent-bin channel model from only the existing
  64 sacrificed bw100 calibration frames.
- Use Bob-conditioned per-position error probabilities with the installed
  `ldpc==2.4.1` product-sum BP+OSD-0 decoder.
- Run and strictly verify a 512-frame-per-stratum sacrificed development
  selection before any confirmation is prepared.
- Run a fresh 128+128 synthetic confirmation once, with a statistically
  pre-registered 126/128 gate per stratum.
- Only after strict synthetic promotion, lock and run 128 fresh real frames
  from each of bw120, bw180, and bw200, again requiring 126/128 per stratum.
- Keep every output additive, immutable, failure-retaining, and verifiable
  without decoder reexecution.

## Evidence Boundary

- The v3 package, seeds, outcomes, and reserved confirmation identities are
  immutable and are not development data.
- V4 may use only the 64 sacrificed bw100 frames already designated as
  calibration.
- V4 synthetic confirmation uses new roots, frame IDs, execution order, and
  Toeplitz seeds.
- V4 real confirmation excludes every v3 reserved real-confirmation frame
  identity and uses a new lock.
- No real output directory may be created before strict synthetic promotion.

## Out of Scope

- Modifying `src/`, `experiments/`, `tools/`, `results/`, any v1-v3 method, or
  any historical output.
- Copying GPL-3.0 code or matrices from LDPC4QKD. That repository and AFF3CT
  are research oracles only.
- Treating independent bit-plane BSC performance as the v4 promotion domain.
- n=512/1024 concatenation, cross-frame superframes, multistage/joint-plane
  decoding, nonbinary LDPC, cross-loss claims, or a Cascade/Polar winner claim.
- Rate adaptation, puncturing/shortening, or nested incremental redundancy.
  Those require a separate post-promotion v4.1 OpenSpec.

## Affected Specs

- Add `binary-ldpc-adjacent-channel-v4`.
