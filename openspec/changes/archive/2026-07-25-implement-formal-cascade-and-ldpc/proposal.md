# Change Proposal: implement-formal-cascade-and-ldpc

## Summary

Add two additive, protocol-faithful offline reconciliation methods:
`cascade_formal_v1` and `ldpc_formal_v1`. They are prerequisites for a future
frame-identical Cascade/LDPC/Polar comparison, not a winner-selection exercise.

## Motivation

The existing `cascade_lite` and `layered_ldpc_lite` are useful executable
baselines, but their simplified correction/accounting behavior cannot support
a paper-grade comparison with the frozen Polar implementation. In particular,
the lite LDPC path may fall back to an experimental decoder and neither method
currently exposes a shared formal verification transcript.

## Scope

In scope:

- additive formal method identities, configurations, manifests, transcripts,
  and qualification outputs in `comparison_bench/`;
- an explicit Alice-reference/Bob-correction protocol, shared Toeplitz
  universal2 verification, and auditable disclosure accounting;
- protocol-faithful Cascade look-back and a fixed-family LDPC syndrome flow;
- synthetic and locked real-frame qualification of each method separately.

Out of scope:

- changes to frozen `src/`, `experiments/`, or `tools/` Polar logic;
- Polar adaptation, three-method ranking, or a method winner claim;
- network transport, authentication cost, hardware real-time operation,
  finite-key/Route-A numerical proof, shortening, or puncturing;
- reinterpretation or replacement of any existing lite evidence or outputs.

## Success Criteria

- `cascade_formal_v1` and `ldpc_formal_v1` coexist with unchanged lite
  methods and preserve every attempted/failed frame.
- Each attempt has a deterministic protocol transcript, a formal Toeplitz
  verification record, and key-dependent versus public-control disclosure
  fields.
- Formal qualification has reproducible synthetic and locked-real evidence,
  or records the predeclared stop/failure condition without promotion.
- No future Polar comparison is started by this change; it only establishes
  qualified formal candidates.

The pinned backend contract is established by actual constructor behavior,
not docstring keyword claims. A no-decode `BpOsdDecoder` construction probe
must accept the exact frozen kwargs before LDPC frames may be attempted.

Synthetic evidence is promotable only when generation, execution order,
verification seeds, unmodified method transcripts, deterministic preflight,
provenance, exception finalization, and read-only verification all satisfy the
active spec. Partial v1 and contract-violating v2 synthetic artifacts are
diagnostics only; neither may support promotion.

Promotion is method-specific. The change may be archived with one or both
methods recorded as non-promoted, provided all attempted evidence and the
reason are retained. A future formal Polar comparison may include only methods
that passed this change's promotion gate; a lite method MUST NOT substitute for
a non-promoted formal method. Improving a non-promoted method requires a new
OpenSpec change.
