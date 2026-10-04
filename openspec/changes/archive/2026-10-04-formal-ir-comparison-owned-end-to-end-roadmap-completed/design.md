# Design: Comparison-owned end-to-end NB-LDPC roadmap

## Repository ownership

`HD-QKD_Polar_Comparison` owns the mutable path:

`CAL/model -> NB-LDPC -> verification/leakage -> fixed-point result -> tau scan -> d x tau scan -> secure-point inputs`.

`HD-QKD_Polar_Release` is read-only reference material for ttbin processing,
physical framing, Polar baseline behavior, and reporting semantics. A future
Release-side consumer is permitted only through a separate change after the
Comparison output contract and real single-point evidence are accepted. It
must be a thin adapter and must not contain the NB-LDPC algorithm or scanner.

## Ordered milestones

1. Accept the current P0/G1/G2 implementation candidate and provide the
   canonical Model-F CAL-TRAIN input without a synthetic fallback.
2. Run separately authorized P0, G1, and G2 gates in order.
3. On G2 qualification only, validate the target `n_IR=1024` configuration.
4. Produce one independent real-data result at fixed `(d,tau,n_IR)`.
5. In Comparison, connect the existing symbol/intermediate-data boundary to
   NB-LDPC and emit honest per-block acceptance, leakage, retention, and cost.
6. Scan `tau` at fixed `d`, confirm the selected point on held-out data, then
   generalize to one additional `d` before a full `d x tau` scan.
7. Combine qualified security inputs only after their measurement contract is
   satisfied; select on reconciled net first and secure key rate later.

## Current boundary

The current gate is candidate review/rework before `P0_PACKET_REVIEW`. The
accepted G0 recovery is tiny synthetic evidence only. P0/G1/G2, `n_IR=1024`,
real data, scans, and secure selection remain unexecuted and unauthorized.

