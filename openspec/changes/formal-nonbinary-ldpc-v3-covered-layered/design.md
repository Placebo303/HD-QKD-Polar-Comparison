# Design: Formal Nonbinary LDPC v3 Covered Layered Successor

## Decision and evidence boundary

v3 is additive and independent: method `nbldpc_formal_v3`, canonical matrix
magic `NBLDPC3\n`, plan schema `NBLDPCQ3`, and future output root
`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v3_nbldpc_synthetic`.
It keeps q=1024 and n=64 so the new evidence isolates codebook coverage and
schedule rather than silently changing all dimensions.  v1 and v2 packages,
including their seeds, frames, policy choices and outcomes, are immutable and
must not select or tune v3.

The v2 prefix audit is recorded only as design motivation:

| prefix checks | zero-degree columns | minimum column degree |
| --- | ---: | ---: |
| 24 | 23 | 0 |
| 32 | 15 | 0 |
| 40 | 7 | 0 |
| 48 | 0 | 2 |

An uncovered symbol cannot receive parity-check information in that prefix,
so this can plausibly contribute to wrong coset choices and `verify_failed`.
The count does not identify the cause of any individual failure and does not
turn v2's development outcome into FER evidence.

## Exact covered QC/PEG-like codebook

The deterministic mother is a 6-by-8 QC base graph with lifting factor Z=8:
48 checks and 64 variables.  A base edge `(a,b)` expands to the 8-by-8
circulant permutation with coefficient `c(a,b)` over the pinned
polynomial-basis GF(1024).  Rows and columns are ordered by base index then
lift index.  Supported ordered prefixes are exactly 24, 32, 40 and 48 rows.

The binary base-edge masks, written as ascending column sets by base row, are
fixed as:

```
0: 0 1 2 3 4 5
1: 0 1 2 3 6 7
2: 0 1 4 5 6 7
3: 0 2 4 6
4: 1 3 5 7
5: 0 1 2 3 4 5 6 7
```

Thus the first three base rows (the 24-check prefix) give every variable
group degree 2 or 3; lifting preserves that fact for every one of the 64
columns.  Later prefixes only add edges.  The verifier must reject any
prefix with a zero-degree column or a minimum column degree below two.

The independent SHA-derived shift-salt proposal was read-only tested before
Phase 1: using big-endian SHA256 integer reduction mod 8, salts 0..65,535
never reached zero 4-cycles (best was one at salt 15,004).  It is rejected as
a planning validation result, not a production/output artifact or data run.
The base graph itself remains feasible.  Its fixed shifts, in the mask order
above, are:

```
0: 2 7 7 5 1 7
1: 5 5 1 6 0 2
2: 2 3 4 1 3 3
3: 0 1 4 4
4: 5 2 1 1
5: 0 4 2 6 0 3 2 6
```

For base edge `(a,b)` and lift row `i`, the nonzero lifted matrix entry is at
column `8*b + ((i + shift[a,b]) mod 8)`; this direction is canonical.  Only
the coefficient salt is searched: for `s=0..65,535`, set
`c(a,b)=1 + int.from_bytes(SHA256(ASCII("NBLDPC3|coef|1024|2026072803|s|a|b")),
"big") mod 1023`, and choose the first salt that passes every frozen rank and
distance-proxy preflight.  The planning probe found expected salt 0 passes;
the implementation must recompute rather than trust that observation.
Exhaustion is `codebook_invalid`; there is no random retry or fallback.  The
fixed shifts plus finite coefficient search are the bounded deterministic
PEG-like construction.

Canonical bytes contain the base masks, Z, construction seed, accepted salt,
all shifts, coefficients, full matrix and ordered prefixes.  The preflight
reconstructs those bytes and requires: full and prefix GF(1024) rank equal to
the respective check count; zero 4-cycles; exact column-degree vectors;
and the distance proxy `d_min >= 3` in the following limited sense.  For
*each* supported prefix, it must exhaust all 2016 unordered column pairs and
reject if either column is zero or their zero/nonzero coordinate pattern is
identical and the nonzero coordinate-wise GF(1024) ratio is constant.  This
excludes weight-one and weight-two codewords only; it is explicitly not an
exact minimum-distance computation or performance claim.

## Decoder candidates

Both candidates are genuinely different from v2 flooding.  Let normalized
QSC prior at variable v be `L_v`; initialize `belief_v=L_v` and every stored
directed check message `c_{r->v}` uniformly.  Process check rows strictly in
ascending row order (a check block `0..checks/8-1` is only an audit label;
there is no eight-row parallel update).  For each row r and each incident v,
form its extrinsic message `v->r ∝ belief_v / old_c_{r->v}`.  Implementations
must recompute the normalized product of `L_v` and all other stored incident
check messages instead of literal division, so a zero cannot be hidden.
Use these extrinsics to form the fresh normalized FFT-QSPA check message u,
apply the frozen damping, then write the normalized new `c_{r->v}`.  Update
that variable immediately as `belief_v ∝ (v->r) * new_c_{r->v}` before the
next row is processed.  Thus later rows consume earlier rows' updates.
After every complete iteration (all selected check rows), hard-decide by
ascending-symbol argmax and check the disclosed syndrome; only then may it
return `syndrome_consistent`.  At initialization, every message update,
extrinsic product, belief update and hard decision, nonfinite values or a
zero normalizer are `decoder_error`.  Exhaustion after exactly max_iter full
iterations is `decode_failed`.

The decoder retains dense float64 messages, existing Walsh-Hadamard q=1024
check convolution, exact GF coefficient permutations, Bob-only inputs and
Alice syndrome.

The only two candidates are `nbldpc_formal_v3_layered_l050` and
`nbldpc_formal_v3_layered_l075`.  For a normalized fresh check-to-variable
message `u` and stored old message `c`, each writes and normalizes
`lambda*u + (1-lambda)*c`, with lambda respectively .50 and .75.  Directed
messages initialize uniformly; all ordering is ascending check, edge, then
symbol.  Nonfinite or zero normalizers are `decoder_error`.  No tempering,
EMS tail rule, pruning, list decoding, external package or per-frame change
is permitted.

Ponytail-lite bound: two damping values test schedule stability without a
decoder zoo.  A one-candidate fixed damping route would be simpler, but would
not distinguish whether the schedule's behavior is damping-sensitive.

## Fresh data, selection, and confirmation isolation

Use PCG64 roots `202607380000`, `202607390000`, `202607400000`, and
`202607410000` for development p=.20, development p=.30, confirmation p=.20,
and confirmation p=.30 respectively.  These are distinct from v1/v2 roots.
Each frame uses the already-pinned call sequence: Alice `integers`, error-mask
`random`, nonzero errors `integers`, then masked XOR.  v3 records and proves
zero overlap of roots, frame IDs, arrays, atomic keys and locally discoverable
formal Toeplitz seed IDs.

There are 24 sacrificed development frames and 32 immutable confirmation
frames per stratum.  Each candidate is paired only with margins 4 and 8,
fixed max_iter 12, and nominal QSC p; this makes four global policies.  The
smallest covered permitted prefix meeting
`ceil(64*(h2(p)+p*log2(1023))/10)+margin` is selected per stratum.
Policy hashes bind candidate, schedule, damping, prefixes, margins and chosen
checks.  Development selection ranks eligible policies by maximum minimum
stratum verified successes, then total successes, lower key-dependent
disclosure, lower iterations and lexical hash.  Any integrity status makes a
policy ineligible; `verify_failed`, `decode_failed` and cap failures are
retained performance outcomes.

If zero policies are eligible, the selection object is exactly the existing
null-selection shape, readiness is false, run status is
`non_promoted_development`, and no confirmation frame/Toeplitz record/outcome
is generated.  Otherwise confirmation is materialized and executed only when
the selected policy reaches 22/24 in *both* development strata.  Confirmation
never participates in selection.  Promotion still requires 31/32 verified
successes in each stratum, full denominators, no prohibited integrity failure,
and strict artifact replay.  Failure forbids N4, sidecars, and `.ttbin` work.

Toeplitz input remains 640 bits and tags 64 bits, so every fresh record has
703 bits.  Development records bind policy+frame; confirmation records bind
the selected policy+frame only after readiness.  The plan must make the latter
absence explicit until readiness, rather than leaking confirmation material.

## Resources, artifacts, provenance

The domain caps are q=1024, n=64, checks<=48, row weight<=8, max_iter<=12,
24 MiB declared dense storage, 30 seconds per decoder call, one worker and
10,800 seconds for a complete run.  Cap failures stay denominator-included.

Use the existing eight-artifact shape, no-overwrite `x` creation, invalid-run
retention, scoped source/CLI/contract/codebook hashes, and read-only strict
replay.  Scoped provenance gates verification; unrelated later worktree drift
is diagnostic only.  The future implementation must include fake-run,
tamper, all-prefix coverage, null-selection, confirmation-isolation,
denominator, and strict-replay tests before any expensive plan is created.

N4 is out of scope.  Only a promoted v3 confirmation may authorize a separate
OpenSpec decision for an adapter, lock, verifier and explicitly authorized
real-data execution.
