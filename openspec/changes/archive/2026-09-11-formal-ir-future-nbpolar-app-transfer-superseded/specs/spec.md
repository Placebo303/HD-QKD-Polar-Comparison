# Specification: NB-Polar APP Transfer and Conditional Rescue

## Requirement: Decoder-family boundary

The future implementation SHALL treat empirical posteriors, APP transfer, and
verification-triggered disclosure as reusable semantics, while treating all
LDPC matrices, BP messages, graph labels, and results as non-transferable.  It
SHALL modify only the comparison layer and keep Polar Release read-only.

## Requirement: Soft-output upper layer

The NB-Polar upper layer SHALL emit a normalized 32-state `q(U1)` derived only
from Bob, the empirical prior, and public Polar constraints.  The lower-layer
prior SHALL be `sum q(U1)P(U2|B,U1)`.  Hard one-hot transfer and Alice-truth
conditioning SHALL NOT satisfy the APP gate.

## Requirement: Single-factor hybrid first

The first real experiment SHALL change only the upper-layer decoder family:
accepted NB-LDPC versus NB-Polar, with the lower-layer NB-LDPC, blocks, prior,
verification, and accounting fixed.  Polar incremental disclosure and full
NB-Polar SHALL be conditional successor changes.

## Requirement: Backlog boundary

This change SHALL remain planning-only until the accepted NB-LDPC/V62 dependency,
backend feasibility review, and explicit user authorization exist.  It SHALL
produce no current decoder call, Polar modification, performance result, or
qualification claim.

