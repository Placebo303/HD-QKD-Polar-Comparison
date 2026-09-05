# V72P2D5-GF32-RATE-MOTHER — G0 Tiny Execution Packet

Status: `G0_PACKET_CANDIDATE / EXECUTE_NOT_AUTHORIZED`

This packet follows the accepted R2 D5 plan and the completed
`STRUCTURE_PASS_WITH_CYCLE_RISK` result. It authorizes no implementation,
decoder call, output creation, or data read until an independent packet review
and a separate G0 authorization record pass.

## 1. Sole question

Does the existing GF32 prior algebra, syndrome calculation, tiny matrix
interface, and historical FFT-QSPA call contract agree on a noiseless matched
synthetic example at tiny width?

This is a mathematical/plumbing gate only. It is not evidence for the full
mother, G1/G2 performance, real-data correction, FER, SKR, or information
limits.

## 2. Prerequisites

- Structure result remains `STRUCTURE_PASS_WITH_CYCLE_RISK`.
- All eight frozen structure prefixes passed the eleven hard gates.
- Four-cycle counts are carried unchanged; no graph change is allowed.
- `structure_execution_authorized=false` and all later authorizations remain
  false until the G0 gate is separately accepted.
- The historical R2 implementation and structure runner remain unchanged by
  the G0 plan review.

## 3. Frozen G0 scope

Allowed data are in-memory synthetic tables only. No CAL, VAL, parquet, raw
pairs, registry, real output, or `run_01` may be read or created.

Use the already frozen G0 seeds exactly:

```text
2026090510, 2026090511, 2026090512, 2026090513,
2026090514, 2026090515, 2026090516, 2026090517
```

Use a tiny matrix width `n<=9` and a hand-checkable positive probability
table. The existing `A=32*U1+U2` mapping, `(Alice,Bob)` axis convention,
`P1/P2` formulas, `1e-300` audit floor, `1e-15` decoder floor, and GF32
polynomial 37 remain unchanged.

The true decoder path, when authorized, must call the historical
`decode_row_layered_fftqspa` implementation through a thin local adapter with:

- `decode_fn=None` only for refusal tests;
- `max_iter=90`;
- `damping_alpha=1.0`;
- `warm_beliefs=None` (cold start);
- no argmax substitute and no fake decoder in the authorized run.

Fake decoders are permitted only in unit tests proving gate plumbing.

## 4. Required checks

The authorized G0 run must report all of the following:

1. Probability axis and normalization errors are finite and `<1e-12`.
2. `CE_joint - CE_L1 - CE_L2_oracle` absolute error is `<1e-10`.
3. `A=32*U1+U2` round-trip is exact.
4. Tiny syndrome recomputation from the known noiseless symbol vector equals
   the syndrome passed to the decoder.
5. The decoder result is finite and its hard output is exactly equal to the
   known synthetic truth for every attempted seed.
6. The decoder-reported syndrome is satisfied for every attempted seed.
7. All eight seeds are attempted exactly once; no retry or seed substitution.
8. `exact_failure_fraction = 1 - exact_count / attempted_blocks` is zero.
9. A tiny exhaustive/tree posterior comparison is included for the hand-sized
   case, with maximum probability error `<1e-12`.

Any mathematical mismatch, syndrome mismatch, non-finite output, wrong hard
word, or exhaustive discrepancy is `G0_BLOCKED`; do not reinterpret it as a
graph or information-limit result.

## 5. Required implementation delta before authorization

The current core phase function is injection-only. Before G0 authorization,
implement the smallest explicit synthetic entrypoint that:

- constructs the hand-sized synthetic `p_b`, `p_f`, and tiny `h` in memory;
- calls the existing prior helpers and `run_g0_phase` semantics;
- supplies the thin historical decoder adapter only from the authorized G0
  path;
- keeps fake decoder injection available for tests;
- emits no output by default and never reads repository data;
- refuses before any construction/import of the historical decoder when G0 is
  unauthorized.

Do not modify the accepted mother construction, structure output, V31/V35/V54
source, or any frozen D5 plan file. Do not add a generalized framework.

## 6. Output contract after authorization

Use a fresh additive workspace directory only, never the structure directory.
The exact G0 output directory and four-file names must be fixed in the
authorization record before execution. Store only scalar metrics, tiny
histograms, seed list, call counts, and the exhaustive error maximum.

Do not store matrices, support/coeff arrays, prior tables, syndromes, raw
symbols, decoder messages, absolute paths, hashes, checksums, or tags.

## 7. Budget and attempt semantics

- One G0 invocation only.
- Eight tiny synthetic blocks, one per frozen seed.
- No retry, rerun, seed search, or early claim after a subset.
- The G0 invocation count increments immediately before the first authorized
  historical decoder call.
- A preflight/test-only fake call does not count.
- Tiny run budget: 120 seconds and RSS `<2 GiB`; timeout is BLOCKED with
  evidence retained.

## 8. Mandatory reviews

Before implementation is accepted:

- independent implementation review checks the exact code/file allowlist,
  decoder adapter, fake/real separation, and no-data/no-output behavior;
- `py_compile` and the complete existing D5 test suite pass;
- no G0 authorization is granted by implementation review.

Before execution:

- exact implementation binding is checked;
- G0 output directory is absent;
- G0 authorization is explicitly true while structure/G1/G2/real/formal are
  false;
- decoder adapter call graph is checked;
- command and budget are recorded.

After execution:

- independent Pre-RESULT review checks all nine required checks, seed count,
  output schema, and no forbidden data;
- authorization is closed;
- next gate is `P0_PACKET_REVIEW`, never G1/G2 automatic execution.

## 9. Decisions

Only these G0 decisions are valid:

- `G0_PASS`
- `G0_BLOCKED_MATH`
- `G0_BLOCKED_DECODER`
- `G0_BLOCKED_RESOURCE`

No G0 decision authorizes P0, G1, G2, or real execution.

## 10. Current authorization

```yaml
g0_execution_authorized: false
p0_cost_execution_authorized: false
g1_execution_authorized: false
g2_execution_authorized: false
real_execution_authorized: false
formal_execution_authorized: false
scientific_promotion: false
```

Next gate: `INDEPENDENT_G0_PACKET_REVIEW`.
