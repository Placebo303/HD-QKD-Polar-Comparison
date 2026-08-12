---
slug: "formal-nonbinary-ldpc-v6-long-block"
createdAt: "2026-08-02T00:00:00+08:00"
---

# Proposal: Formal Nonbinary LDPC v6 Long-Block Development

## Why

The completed v5 routes A-D all used `GF(1024)` with 64-symbol frames.  Each
strictly verified confirmation ended at 128/128 for p=.20 and 127/128 for
p=.30.  Codebook redesign, decoder changes, extra redundancy, list search,
and the existing post-processor therefore did not remove the same one-frame
tail.  Continuing to tune the n=64 family would spend fresh confirmation data
on a regime that is structurally too short to distinguish ensemble behavior
from finite-length trapping/error-floor behavior.

Published HD-QKD work models the source as a q-ary symmetric channel and uses
nonbinary LDPC degree distributions optimized by density evolution.  The most
direct next experiment is therefore a longer `GF(1024)` code, not another
n=64 decoder variant.

## Scope

This change creates one development-only candidate:

- method identity `nbldpc_formal_v6_long`;
- `GF(1024)`, polynomial/natural-symbol conventions inherited from the
  accepted v5 field implementation;
- frame length `n=1024` symbols;
- two deterministic variable-degree-2, check-concentrated PEG codebooks:
  `(n,m)=(1024,320)` for p=.20 and `(1024,480)` for p=.30;
- deterministic layered FFT-QSPA with stable normalization, 50 iterations,
  damping .75, and workers=1;
- exact syndrome consistency and the existing 64-bit Toeplitz verification;
- tiny-math/oracle, structural, tamper, fake-runtime, and cross-version tests;
- one fresh, sacrificed synthetic development run only after independent
  engineering acceptance.

The initial implementation packet stops before creating or executing a
development plan.  A later main-thread review may authorize a fresh additive
development plan.  Confirmation material is not defined or materialized by
this change.

## Out of Scope

- Any confirmation, promotion, real-data, N4, sidecar, `.ttbin`, or method
  comparison claim.
- Reuse of v1-v5 frames, roots, seed bytes, seed IDs, plans, or outputs.
- Changes to frozen `src/`, `experiments/`, `tools/`, `results/`, or existing
  formal nonbinary source and artifacts.
- Multiplicative repetition, GF(32)xGF(32) multilevel coding, proximal-ADMM,
  GPU/CUDA, a C/C++ production backend, or a new third-party runtime.
- Importing code from an external repository.  External implementations may
  supply manually generated oracle fixtures only after license review.
- Selecting a confirmation gate from development results.  A successor
  qualification change must pre-register its own fresh data and gates.

## Success Boundary

This change succeeds when the engineering candidate and all frozen tests pass
and a review-ready source-hash manifest is produced.  It does **not** succeed
by claiming scientific promotion.  Any sacrificed development result is
diagnostic evidence only.

## Affected Specs

- Add `formal-nonbinary-ldpc-v6-long-block` development requirements.

