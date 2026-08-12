# Proposal: Plan Parallel Binary and Nonbinary LDPC Lanes

## Why

The completed `ldpc_formal_v2` qualification shows that the current binary
short-block design is reproducible but not promotable. The existing
`qldpc_reference` path is useful as a reference implementation, but it is not a
formal nonbinary LDPC method. Continuing both research directions requires
separate identities, evidence chains, and promotion gates.

## Scope

- Document independent binary and nonbinary LDPC research lanes.
- Preserve all existing method identities, outputs, and qualification results.
- Define the shared boundary for a later fair, frame-identical comparison.
- Do not implement a decoder, create qualification data, or run experiments.

## Affected Specs

- Add `ldpc-parallel-research`.

