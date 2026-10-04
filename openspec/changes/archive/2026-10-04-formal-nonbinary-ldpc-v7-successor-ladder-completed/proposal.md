---
slug: "formal-nonbinary-ldpc-v7-successor-ladder"
createdAt: "2026-08-02T00:00:00+08:00"
---

# Proposal: Formal Nonbinary LDPC v7 Successor Ladder

## Why

V5 reached 128/128 at p=.20 and 127/128 at p=.30 with n=64, but did not meet
the frozen gate. V6 changed to a degree-2 PEG n=1024 baseline and stopped after
a fresh sacrificed canary produced 0/4 in both strata. The next work must
change the ensemble, not merely increase n or iterations.

This change freezes an ordered development ladder. OpenCode may implement and
run one route at a time, freeze every failed package, and stop at the first
development-ready candidate. It may not create confirmation data or declare
promotion.

## Ranked Routes

1. **R1 — multiplicatively repeated `(2,3)` mother code.** Closest to the
   selected V6 successor and smallest implementation delta. Try the rate-1/3
   mother first, then exactly one multiplicative repetition (rate 1/6) only if
   the mother canary fails.
2. **R2 — QSC-informed GF(1024) ensemble.** Reproduce the direct HD-QKD
   literature direction: q-ary symmetric-channel density evolution or its
   frozen deterministic approximation, followed by PEG construction. Highest
   efficiency potential, but more implementation and oracle risk.
3. **R3 — GF(32)xGF(32) nonbinary multilevel coding.** Split each 10-bit
   symbol into two 5-bit layers and reconcile both with nonbinary codes.
   Lower message complexity, but adds conditional-layer and accounting risk.

R4 (faithful proximal-ADMM) is not authorized in this ladder. It is a separate
research implementation, and the existing V5 post-processor is not equivalent
to the published nonbinary formulation.

## Definition of Development-Ready

A route is development-ready only when its immutable 16+16 sacrificed
development package has:

- at least 15/16 verified successes independently at p=.20 and p=.30;
- zero forbidden status, provenance, transcript, leakage, or replay failure;
- strict read-only replay success;
- mean key-dependent disclosure no worse than 8.75 bits/input-symbol in either
  stratum (the V5 final-prefix syndrome baseline, tag included separately);
- median runtime no more than 120 seconds/frame on the recorded environment;
- no confirmation material and no official formal-method output.

This is a readiness threshold, not promotion. A successor qualification change
must set fresh 128+128 confirmation data and its own frozen gate.

## Out of Scope

- V5/V6 reruns, tuning sacrificed rows, n=4096, real data, N4, sidecars,
  `.ttbin`, confirmation, promotion, or comparison claims.
- Automatic dependency installation, cloning/copying external repositories,
  GPU/CUDA, or modification of frozen baseline directories.
- Continuing after the first development-ready route.

