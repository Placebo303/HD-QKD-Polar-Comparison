# Design: formal-nonbinary-ldpc-v23-met-protograph-de

## Status

CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE. The directory name is
historical and does not describe the implemented semantics.

## Implemented semantics

For a base matrix `B`, V23 computed:

- total edges `E = sum(B)`;
- aggregate `lambda_d = d * count(variable_degree=d) / E`;
- aggregate `rho_d = d * count(check_degree=d) / E`;
- one V22b single-edge DE evaluation of the resulting distributions.

No message state was indexed by base-matrix location or edge type. Therefore
two topologically different matrices with the same aggregate degree counts are
indistinguishable to this path. This is neither topology-preserving
protograph DE nor MET DE.

## Evidence coverage

- The first 2x32 all-ones aggregate profile was non-convergent.
- The raw scan package contains three matrices.
- The consolidated summary contains additional regular/simple-irregular
  entries without corresponding independent raw/verify packages.

Only raw-backed records can be described as raw scan evidence. Summary-only
entries remain unverified diagnostics. The observed entropy range must not be
used to claim exhaustive coverage.

## Unimplemented work

- I03 true MET extension: NOT_IMPLEMENTED.
- V01 independent verification against V22b semantics: NOT_RUN.
- topology-preserving protograph search: NOT_IMPLEMENTED.

## Successor boundary

V24 may test bounded aggregate single-edge optimization. True MET can be
proposed only after V24 FAIL in a separate change with explicit user
authorization.
