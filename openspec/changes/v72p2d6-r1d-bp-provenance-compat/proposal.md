# D6 R1d BP provenance compatibility repair — proposal

> Status: freeze only (Track A R02). Docs, no code, no execution, no
> authorization. All execution/promotion authorizations remain false.
> Historical A2 roots immutable. No R1d execution under this change.

## What

Adapt the D6 graph/mother development runner
(`scripts/v72p2d6_graph_mother_development.py`) to the accepted BP
Alternative A interface contract (`PRIOR_ONLY` / `CHECK_UPDATED` /
`WARM_START_UNSPECIFIED`; only `CHECK_UPDATED` may feed a conditioned
cross-layer APP), without changing any frozen science.

## Why — the defect (reproduced R01, zero real decoder, fake only)

`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py:1026`
`_decode_block` returns six values
`(exact, syndrome_ok, iterations, finite, beliefs)` + optional syndrome +
`(provenance,)`, i.e. six normally. The D6 worker
(`scripts/v72p2d6_graph_mother_development.py:126`) unpacks five:

```text
e, s, it, f, bel = core._decode_block(dec, h, prior, xt)
```

R01 reproduction (fake six-returning `_decode_block`, tiny in-memory
arrays, no production decoder binding, no root):

- (a) the unpack raises
  `ValueError('too many values to unpack (expected 5)')`, swallowed by the
  broad worker `except` (L132–135) into a crash cell with zero scientific
  content; the warmup call (L108–116) ignores the return shape and still
  reports `warmup=ok`;
- (b) the parent `run_cell` (L778–793) pops L1 beliefs, builds
  `q = softmax(bel)`, and calls `d5.app_fed_l2_prior(p2, bob, q)` with no
  provenance check — a provenance-less L1 return fed a real L2-APP decode
  (`call_idx >= 0`) in the repro.

Therefore the R1d Pre-EXECUTE verdict
(`D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1D.md`) is stale: it reviewed code
that cannot consume the accepted decoder-result shape and that forwards
beliefs without the accepted provenance gate. The addendum
`D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_ADDENDUM_BP_COMPAT_A1.md` declares it
superseded after repair and grants no execution.

## Frozen repair scope

1. Worker unpacks six values
   `(exact, syndrome_ok, iterations, finite, beliefs, provenance)` and
   carries `provenance` in the IPC result dict; beliefs stay transient IPC
   only (when requested), never persisted.
2. `CHECK_UPDATED` (exact token, via the accepted
   `require_check_updated_provenance` helper, lazy import) is required
   before `q` construction and `app_fed_l2_prior`; all other tokens
   (`PRIOR_ONLY`, `WARM_START_UNSPECIFIED`, missing/`None`, unknown) yield
   a deterministic named provenance-blocked record — never a crash cell
   and never an L2 APP decode.
3. Setup/warmup explicitly validates the decoder-result shape; an
   incompatible shape reports ready=false / warm=fail loudly.
4. The worker `except` is not broadened: arity/programming errors keep
   their loud `ValueError` signature and are gated by the warmup shape
   check, never silently sold as scientific crash cells.

## Non-goals (frozen)

- No scientific arm, seed, rows, mother, schedule, estimator, threshold,
  budget, or terminal-interpretation change.
- CSV schema `DECODER_FIELDNAMES` unchanged; all existing scientific
  constants and non-BP records byte/field compatible.
- Historical A2 roots immutable; no R1d execution, no UUID, no root.
- No V35 modification (consumer of the accepted contract only).
- R05–R07 (independent review, renewed Pre-EXECUTE, commits) are out of
  scope for the R01–R04 operator packet.
