# Proposal: Binary LDPC v4 Backend Correction v1

## Why

The immutable `20260727_v1_binary_ldpc_v4_development` package completed and
verified, but every decoder construction returned
`development_decoder_error`. A no-decode diagnostic established the sole
cause: pinned `ldpc==2.4.1` requires `error_channel` as a Python `list`, while
the development evaluator supplied a NumPy array. The formal v4 method already
uses the required conversion.

The failed package is implementation evidence, not FER evidence. It must
remain immutable and must not be repaired in place.

## What Changes

- Add a versioned development evaluator and package runner/verifier.
- Convert the already frozen float64 error-channel vector with `.tolist()`
  exactly at the `BpOsdDecoder` constructor boundary.
- Add a regression that exercises the pinned production constructor contract.
- Bind the predecessor package and correction source in a fresh immutable
  development plan.
- Execute the unchanged 512+512 sacrificed-development qualification once.

## What Does Not Change

- Method identity `ldpc_formal_v4`, q=1024, 256-symbol frames, Gray mapping.
- Calibration, adjacent-channel probabilities, generated development frames,
  all 40 matrices, decoder policy, candidate selection, accounting, resource
  caps, and the 495/512 readiness floor.
- Historical v1-v4 source files and all existing output packages.
- Synthetic or real qualification. Those remain separate conditional work.

## Evidence Boundary

Passing proves only that the corrected development implementation meets the
existing readiness screen. Failing is retained without tuning or rerun.
Neither result is synthetic qualification, real-data evidence, FER across a
population, or a Cascade/LDPC/Polar comparison.

