# Specification: Power-of-Two Dimension Generalization

## Requirement: Independent dimension and block-length parameters

The future implementation SHALL represent `d=2^n`, `layer_bits`, and block
length `N` independently.  It SHALL require `sum(layer_bits)=n`, exact bijective
pack/unpack, supported `GF(2^ri)` identities, explicit field polynomials, and
per-layer matrices/rates/leakage.  It SHALL NOT infer `N=d` or reuse GF32
matrices for another `q`.

## Requirement: Soft multilevel channel semantics

Every layer SHALL retain the complete Bob symbol and SHALL build its prior from
the exact source/dimension empirical channel.  Previous-layer information SHALL
be transferred as normalized APP distributions.  Hard decisions MAY appear only
as preregistered diagnostic controls and SHALL NOT silently replace APP transfer.

## Requirement: Single-factor validation

The first authorized experiment SHALL hold `N=1024` and all non-dimension
factors fixed while testing one preregistered new dimension.  A later block-length
experiment SHALL be a separate change.  Results SHALL report per-layer/full exact,
per-source outcomes, disclosure, verification, calls, runtime, and memory.

## Requirement: Backlog boundary

This change SHALL remain planning-only until the accepted NB-LDPC/V62 dependency
and explicit user authorization exist.  It SHALL create no production code,
decoder output, matrix, or performance claim in the present turn.

