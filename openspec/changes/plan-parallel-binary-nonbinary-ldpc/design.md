# Design: Parallel LDPC Research Lanes

## Decision

The project will maintain two independent formalization paths:

1. Binary LDPC will advance from the non-promoted `ldpc_formal_v2` evidence
   toward longer frames, stronger deterministic code families, incremental
   redundancy, and bit-plane soft information.
2. Nonbinary LDPC will start as a new formal method, provisionally
   `nbldpc_formal_v1`, after a bounded GF(q) backend and decoder feasibility
   stage.

`qldpc_reference` remains unchanged and cannot be relabeled as the formal
nonbinary lane.

## Evidence Boundary

Each lane owns its codebook, manifest, development/confirmation split,
transcript, disclosure accounting, verifier, and promotion decision. A result
from one lane cannot promote the other. Existing confirmation data remains
immutable and cannot be used for tuning.

## Integration Boundary

Both lanes may be developed concurrently. Only independently promoted formal
methods may enter a later OpenSpec change for a frame-identical comparison
with formal Cascade and Polar. Leakage must be expressed in disclosed bits
with method-specific decomposition preserved.

## Simpler First Step

Do not add a new nonbinary decoder dependency yet. First freeze the field,
decoder, determinism, runtime, and disclosure contracts and perform a bounded
feasibility check.

