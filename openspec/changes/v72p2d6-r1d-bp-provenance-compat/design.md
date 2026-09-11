# D6 R1d BP provenance compatibility repair — design

> Freeze only (Track A R02). No code, no decoder call, no root, no
> execution. All authorizations false.

## Frozen semantics

### Provenance tokens (exact, from the accepted BP contract)

`PRIOR_ONLY`, `CHECK_UPDATED`, `WARM_START_UNSPECIFIED`.
Missing/`None`/unknown = not conditioned. `None` is never upgraded.

### Worker IPC (`_worker_main`)

- Unpack exactly six values from `core._decode_block`:
  `(exact, syndrome_ok, iterations, finite, beliefs, provenance)`.
- Carry `provenance` in the IPC result dict alongside the existing keys
  (`exact`, `syndrome_ok`, `iterations`, `finite`, `beliefs`, `crash`,
  `error`, plus `wall_s`/`rss`/`timeout`/`wall_timeout` set by the
  existing paths).
- Beliefs remain transient IPC only: included only when the task sets
  `return_beliefs` and non-`None`; never persisted (CSV schema unchanged).
- Provenance is carried even when beliefs are not requested, so the
  parent gate always sees the token.
- The existing `except` clause is not broadened: a shape-incompatible
  decoder return keeps its loud `ValueError` arity signature in `error`
  (e.g. `too many values to unpack (expected 5)` pre-repair shape), and
  the warmup shape gate below is the loud incompatibility barrier.

### Warmup / setup readiness

- Warmup explicitly validates the decoder-result shape (six values).
- Compatible shape → `ready=true`, `warmup=ok` (existing behavior).
- Incompatible shape → `ready=false`, `warmup=fail:<reason>` naming the
  shape mismatch loudly in the hello message the parent already logs.
- Warmup never binds science: tiny in-memory fixture only.

### Parent gate (`run_cell` L1 → APP-L2)

- Before `q` construction and `app_fed_l2_prior`, call the accepted
  helper `require_check_updated_provenance(provenance, consumer=...)`
  (lazy import of
  `comparison_bench.formal_ir.v35_algorithm_development`; no V35 edit).
- Exactly `CHECK_UPDATED` → existing `softmax(bel)` → `app_fed_l2_prior`
  → L2-APP decode path, numerically unchanged.
- Every other token → deterministic provenance-blocked record:
  `call_idx=-1` (no budget consumed, no worker call, nothing appended to
  scientific records), `crash=False`, `finite=True`, `error` carrying a
  stable `provenance-blocked:belief_provenance=<token>` marker,
  in-memory `note` `provenance-blocked-l1-not-check-updated`.
  Never an L2 APP decode, never a crash cell.
- L1 unavailable/crashed (no beliefs) keeps the existing
  `app-undefined-l1-unavailable` skip record unchanged.
- L2-oracle diagnostic path untouched (uses true `u1`, no beliefs).

### Compatibility pins

- `DECODER_FIELDNAMES` unchanged; flush/verify paths untouched
  (in-memory-only keys never reach CSV).
- `R1D_ARMS`, `R1D_VALID_SUBSET`, `ARMS`, `ROW_BUDGETS`, `MODES`,
  `POINTS`, budgets, watchdog, terminals: unchanged.
- D6 module (`v72p2d6_gf32_graph_mother.py`) untouched; V35 untouched.

## Alternatives considered

- **Broaden the worker `except` to label arity errors specially:**
  rejected — widens the crash-mapping surface; the warmup gate plus the
  loud `ValueError` signature already prevents silent selling.
- **Force a sweep / synthesize `CHECK_UPDATED` (Alternative B style):**
  rejected — changes stopping/schedule semantics; separately frozen
  decision only, never implicit.
- **Drop blocked cells as crashes:** rejected — a controlled provenance
  refusal is not a crash; crash accounting and the A3 crash-override
  terminal must not see it.
