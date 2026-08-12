# Proposal: Binary LDPC v4 10 dB Transfer Qualification v1

## Why

The immutable 16 dB transfer qualification completed and verified but was
non-promoted: bw120 achieved 125/128 against the frozen 126/128 gate, while
bw180 and bw200 achieved 128/128. It must not be tuned or rerun.

An independently acquired Type-II 10 dB `.ttbin` capture already has more
than 1,100 complete q=1024 frames in each target bin-width layer. This change
tests the exact unchanged promoted binary LDPC v4 method in that separately
named domain. It is not a retry of the 16 dB package and cannot promote the
16 dB or 20 dB domains.

## Scope

- Add a read-only, hash-pinned 10 dB source adapter.
- Add a versioned prepare/execute/read-only-verify qualification package.
- Reuse the exact promoted corrected-v2 synthetic prerequisite and unchanged
  v4 codebook, channel model, decoder policy, leakage, transcript, resource,
  and failure semantics.
- Select 128 frames independently in each of bw120, bw180, and bw200.
- Require at least 126/128 verified successes in every layer with zero
  forbidden failures.
- Bind the immutable non-promoted 16 dB package as predecessor evidence.

## Out of Scope

- Any parameter, matrix, rate, iteration, or decoder change.
- Reading 10 dB decoder outcomes before the one frozen execution.
- Reusing the 16 dB confirmation as development data.
- Claims about 16 dB, 20 dB, other losses, or population-wide performance.
- Changes to `src/`, `experiments/`, `tools/`, historical artifacts, or
  existing output directories.

