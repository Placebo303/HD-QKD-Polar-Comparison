# Delta Spec: Parallel Binary and Nonbinary LDPC Research

## Requirement: Independent Method Identities

Binary formal LDPC and nonbinary formal LDPC SHALL remain separate method
identities. `qldpc_reference` SHALL remain reference-grade and SHALL NOT be
renamed, promoted, or treated as a formal nonbinary implementation.

## Requirement: Independent Evidence

Each lane SHALL use its own immutable codebook, manifest, sacrificed
development data, fresh confirmation data, transcript, verifier, disclosure
accounting, and promotion decision. Existing confirmation evidence SHALL NOT
be used for tuning.

## Requirement: Parallel Development and Comparison Barrier

The two lanes MAY proceed in parallel. Neither lane SHALL enter a formal
frame-identical comparison until it independently passes its predeclared
synthetic and applicable real-data promotion gates. A later comparison SHALL
preserve method-specific leakage decomposition while expressing disclosure in
comparable bits.

