# MSD information budget

Track: EXPLORE for the initial approved aggregate diagnostic.

### Requirement: Conditional chain accounting
Use approved C[a,b], complete Alice bit orders and full Bob side information. Verify chain equality, distinguish marginal BSC costs, preserve source roles and report units. Entropy arithmetic SHALL NOT imply decoder success.

### Requirement: Explicit modeled accounting
Disclose finite-length assumptions, N, tag once only, failure penalty and OOS limitations. Historical absolute budgets SHALL NOT transfer across sources/block lengths without explicit provenance and scaling.

### Requirement: Bounded independent evidence
Freeze exact input/output paths and commands before calculation. Independently recompute every reported number; write source rows progressively. Decoder experiments require effect/MDE before their packets; prohibited GF32 microprobes SHALL NOT resume.

### Requirement: Truth-free syndrome integration
Implementation SHALL separate sender truth from receiver Bob/public-syndrome inputs, propagate actually recovered prefixes, and count every transmitted parity row in bits/block. Syndrome satisfaction SHALL NOT mean verified success. Receiver factories SHALL be explicit; implementation tests SHALL inject fake decoders and SHALL NOT construct or execute a production backend. Backend selection, graph design and empirical execution remain subject to their later gates.

### Requirement: Explicit exact-prior mechanism
The receiver MAY expose a default-disabled branch that bypasses the backend only when every queried error probability equals zero exactly. It SHALL retain the same public-syndrome check, failure stop, recovered-prefix propagation and upfront transmitted-row accounting. Any positive probability, including unsupported-cell fallback, SHALL retain the ordinary explicit-factory path. A deterministic model conflict SHALL stop rather than invent a correction. TRAIN determinism SHALL NOT imply OOS correctness, zero disclosure, verified acceptance or measured efficiency.
