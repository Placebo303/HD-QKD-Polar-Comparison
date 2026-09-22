# V72P2D5 G0 implementation candidate — R1 rework (B1/B2)

```yaml
review_status: CANDIDATE_R1_AWAITING_INDEPENDENT_REVIEW
implementation_review: NOT_SELF_GRANTED
g0_execution_authorized: false
decoder_executed: false
cal_rows_read: 0
val_rows_read: 0
formal_output_created: false
```

This file records only the implementation handoff. The G0 packet remains the
source of truth for the tiny synthetic contract, the eight frozen seeds, the
historical decoder call parameters, the output schema, and the separate
execution gates. An independent reviewer must inspect the code and tests
before any G0 authorization record is created. This rework grants no PASS
and no execution authorization; stop gate is
``INDEPENDENT_G0_IMPLEMENTATION_R1_REVIEW``.

B1 true tiny tree (ponytail-lite): the prior probability-decomposition check
is kept but accurately named ``factorization_error``; alone it is not
tree-vs-exhaustive evidence. A minimal acyclic GF32 factor graph is added
(two GF32 vars ``x,y`` + one nontrivial parity ``x (+) a*y = syndrome``,
``a=7``, strictly positive normalized non-uniform asymmetric priors).
Exhaustive side is explicit 32x32 enumeration with parity constraint then
normalize; tree side is independent factor-to-variable messages plus both
posterior marginals (separate code path). Frozen gate:
``max_abs_posterior_error<1e-12``, MAP identical, finite true. No historic
decoder calls in the check. Transposed prior / wrong coefficient / wrong
syndrome mappings are caught by the gate metric. Any math-gate failure is
``G0_BLOCKED_MATH`` before decoder lazy-import/call with ``decoder_calls=0``.

B2 resource and invocation (ponytail-lite, no generic scheduler):
``historical_decoder_invocations`` is 0 for fake paths and 0->1 before the
first real historic call (max 1 per whole G0, stays 1 across its eight
seeds). ``wall_seconds`` plus explicit ``peak_rss_bytes`` (null when
unavailable) are recorded. Before/after EACH seed call checks
elapsed<=120s and RSS<2GiB; on exceed remaining seeds stop as
``G0_BLOCKED_RESOURCE`` with attempted/completed/calls/failed_seed/stage
plus obtained scalars preserved (never zeroed, never mislabeled as decoder
failure/success). A single historic call that hangs needs an outer-process
watchdog in the future Pre-EXECUTE packet; no extra-process machinery lives
 here. Four-file outputs carry scalars/seeds/status/counts/error-bounds only.

R1 edge fix (resource post-check, candidate only): the post-call resource
check (elapsed>120s OR RSS>=2GiB) now runs for EVERY seed including the
last — the prior `pos + 1 < len(seeds_list)` restriction no longer skips
the last-seed evaluation. A last-seed exceed records
``G0_BLOCKED_RESOURCE`` with ``passed=false``, attempted/completed/calls
all 8, exact/syndrome/finite counts preserved (never zeroed),
``failed_seed`` set to the just-completed last seed and
``failure_stage=resource``; it is never labeled ``G0_PASS`` or
``G0_BLOCKED_DECODER``. Mid-seed stop semantics are unchanged. This grants
no PASS and no execution authorization; stop gate remains
``INDEPENDENT_G0_IMPLEMENTATION_R1_FINAL_REVIEW``.

Implementation notes for review (not acceptance): the tiny fixture uses an
eight-cycle with check and variable degree two; one coefficient is 2 so the
all-ones cycle is not singular, and no degree-one check is passed to the
historical kernel. The factorization check explicitly enumerates the
``(U1, B, U2)`` states and compares the recovered ``P_F`` with
``P1(U1|B) * P2(U2|U1,B)``. The fake authorized test supplies its generated
fixture truth only to exercise the adapter; the adapter independently
recomputes the candidate syndrome. No claim is made that the historical
decoder will pass all eight seeds until a separately authorized G0 run.
