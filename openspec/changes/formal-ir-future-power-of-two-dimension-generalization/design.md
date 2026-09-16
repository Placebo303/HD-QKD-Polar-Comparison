# Design: Power-of-Two Dimension Generalization

**Lifecycle**: `BACKLOG_PLAN / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED`

## 1. Mathematical contract

For `d=2^n`, freeze an ordered composition

`layer_bits = [r1,...,rL]`, `ri>=1`, `sum(ri)=n`, `qi=2^ri`.

Natural mixed-radix packing SHALL be bijective:

`A = U1*2^(n-r1) + U2*2^(n-r1-r2) + ... + UL`,

with an exact inverse and `Ui in [0,qi)`.  Alternative Gray/order mappings are
separate preregistered candidates, not hidden configuration changes.

The channel law is source-specific empirical `C[a,b]` of shape `(d,d)`.  Layer
`i` receives the full Bob symbol and preceding-layer APPs; it SHALL NOT replace
the full Bob observation with a remainder symbol.  Hard previous-layer decisions
are diagnostic controls only because V42 showed error amplification.

## 2. Configuration boundary

One compact immutable configuration SHALL contain:

- `dimension_bits`, `dimension`, `block_length`;
- ordered `layer_bits`, field IDs and irreducible polynomials;
- symbol packing/order contract;
- per-layer base and incremental matrix identities;
- decoder parameters, verification scope, prior provenance;
- leakage rule `leak_bits = sum_i(ri*m_i) + verification/auth extras`.

`dimension` and `block_length` SHALL never be inferred from each other.

## 3. Reusable pipeline

1. Load/build empirical `C[a,b]` for the exact dimension and source.
2. Derive normalized layer priors and conditional posteriors from the declared
   packing map.
3. Decode layers successively while transferring normalized APP distributions.
4. Apply verification-only conditional increments per layer.
5. Report `exact_layer_i`, `exact_full`, disclosure, calls, runtime, memory, and
   undetected acceptance separately.

Each new `q` requires a verified `GF(2^r)` field and newly constructed/rank-checked
matrices at the required rate.  Existing GF32 matrices are not resized or reused.

## 4. Validation sequence

- T0: pack/unpack bijection, field identities, posterior normalization, entropy
  chain rule, leakage units, noiseless limit.
- T1: synthetic matched-channel decode for `[4,4]`, `[5,5]`, `[6,6]`, and one
  unequal split; compatibility test proving `[5,5]` reproduces current inputs.
- T2: decoder-free rate/memory/complexity report followed by a small authorized
  development run for exactly one new dimension.
- T3: only after a signal, fresh paired blocks and source-balanced confirmation.

The first real experiment changes dimension only: `N`, graph-design procedure,
decoder settings, sampling rule, and gate are frozen.  Block-length experiments
are a successor change.

## 5. Gates

- `GENERALIZATION_ENGINEERING_READY`: all T0/T1 contracts pass.
- `DIMENSION_SIGNAL_RETAINED`: selected new dimension meets its preregistered
  per-source exact/undetected/disclosure gate.
- `DIMENSION_NO_RETAINED_SIGNAL`: evidence valid but gate fails.
- `UNSUPPORTED_FIELD_OR_COMPLEXITY`: field/FFT/memory bound prevents a valid run.
- `EVIDENCE_INVALID`: packing, posterior, units, or provenance fail.

These states do not imply FER/SKR qualification or universal `2^n` support.

