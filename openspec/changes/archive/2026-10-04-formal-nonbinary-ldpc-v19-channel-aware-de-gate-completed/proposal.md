# Proposal: formal-nonbinary-ldpc-v19-channel-aware-de-gate

> Status: DRAFT (not yet approved for production execution)

## What
Design and gate a channel-aware density-evolution route that addresses the Route B M2
finding: plain irregular NB-LDPC DE is limited by structured-channel shape, not by
search budget. The change will evaluate channel-specific mechanisms (per-symbol-class
puncture, LSB-public/Pacher-style, structured edge labels) before committing to a
finite-length code.

## Why
- V18-B2 M2: q=16 folded real structured channel plain DE rate ceiling ≈0.60 (f≈4.18).
- Equal-entropy QSC control converged 16/16 at rate 0.63/0.65; folded channel failed.
- Target f≤1.3 requires an effective mother rate ≈0.876 on q=16 or equivalent channel-aware decomposition.
- V19 Polar MLC experiments (PW/MC/GA, CA-SCL list 32/128, N up to 8192) did not reach f≤1.3 with the current decoder; the remaining path is optimized LDPC/DE-gated design.

## Scope
- Add v19 modules/CLI/tests for channel-aware DE gate, reusing frozen V10 DE/V14 MC-DE.
- Pre-register gates: G0 deterministic effective-channel reproduction; G1 rate ladder
  {0.70,0.75,0.80,0.85,0.875}; G2 honest full-channel f≤1.3 on q=1024 legacy statistics.
- Diagnostic-only until gate review; no finite code construction in this change.

## Out of scope
- q=32/64/128 scaling before G1 passes.
- PEG/finite-code/decoder qualification until DE gate passes.
- Rerunning/tuning V14/V17/V18 frozen results.
