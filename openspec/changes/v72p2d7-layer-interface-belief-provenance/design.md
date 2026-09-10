# Layer-interface belief provenance — design (correction; implementation deferred)

> Status: design freeze for a future implementation. No code, no decoder call,
> no root, no execution. All authorizations false.

## Frozen constants and semantics

### Provenance tokens (exact)

- `PRIOR_ONLY`
- `CHECK_UPDATED`
- `WARM_START_UNSPECIFIED`

Optional/unspecified representation for legacy or non-migrated results:
`None`/absent = unspecified/legacy. `None` is never upgraded to
`CHECK_UPDATED`.

### Field

`belief_provenance`, attached to the decoder-returned result:

- v35 `DecoderResult`: new field with default `None`, appended after the
  existing six fields so positional construction and existing fakes keep
  working.
- Adapter result dicts: optional `belief_provenance` key; absence = unspecified.

### Cold-start definition (frozen)

- **Cold start**: decoder called with `warm_beliefs=None` (the current
  historical/D5/D7-B binding).
- **Zero completed check sweeps**: the return happens at the initial-syndrome
  check before any check-row update (`iterations == 0`, v35 L683–692) →
  `PRIOR_ONLY`. The returned beliefs are the input log-prior after the
  documented floor (1e-15) and renormalization, with `check_to_var` still all
  zeros.
- **At least one completed sweep**: every check row has been updated at least
  once before the return (`iterations > 0`; in the row-layered schedule the
  hard decision follows a full layer sweep, v35 L725–736) → `CHECK_UPDATED`.
  Per ruling 6, `iterations > 0` is sufficient for the current cold row-layered
  decoder, but the contract uses the explicit field so consumers do not infer.
- **Flooding**: no iteration-0 path exists (loop starts `it=1`, v35 L591;
  first return L607–616 follows a full check-update round) → `CHECK_UPDATED`.
- **Warm start**: any non-`None` `warm_beliefs` seed (v35 L660–661) yields
  `WARM_START_UNSPECIFIED` unless the caller supplies explicit provenance.
  Provenance is never inferred from `iterations` (ruling 7). Warm-start
  provenance design is out of scope until a route needs warm starts.

### Provenance rule (frozen)

`final_beliefs` is a current log-belief state (ruling 2). It may be labeled
syndrome-conditioned APP/conditioned posterior only when its provenance is
`CHECK_UPDATED` (or stronger explicit provenance to be defined by a future
warm-start design). A `PRIOR_ONLY` return may be recorded only as
`PRIOR_ONLY_CURRENT_BELIEF`, never as posterior/APP.

### Fail-closed default (frozen)

A consumer that requires a conditioned APP input must:

- accept only `CHECK_UPDATED` (or explicitly stronger provenance);
- treat `PRIOR_ONLY`, `WARM_START_UNSPECIFIED`, `None`, absent, or unknown
  tokens as **not conditioned** and fail closed;
- never silently forward the value as cross-layer APP evidence.

"Fail closed" = refuse/raise before computing or forwarding the cross-layer
prior. The smallest candidate enforcement point is the migrated call site
(e.g. D5 `_run_layered_block`); the pure math helper (`app_fed_l2_prior`)
may keep its signature and docstring contract. The exact mechanism is an
implementation decision for the deferred task, not a scientific parameter.

### Future-consumer migration rule (frozen)

- The interface implementation must be in place before the next sequential,
  alternating or joint cross-layer APP run.
- Consumers with no cross-layer APP use may keep current behavior until
  separately migrated; they must not be used for a cross-layer APP route before
  migration.
- Historical consumers (v45–v55, shell adapter, v72p2d3, V64 runner) are
  migrated or fail closed before any rerun as cross-layer APP. No retroactive
  change to published numbers.
- No retroactive change of any historical result; the D7-B R2 evidence,
  terminal, scope, and all existing artifacts stay exactly as published.
- D7-C single-layer oracle readiness/execution does not require this interface;
  D7-C must not import or depend on the future interface-rework implementation;
  D7-C never feeds returned beliefs into another layer (ruling 8).

## Compatibility matrix

Canonical rows; narrative evidence and exact line citations are in
`proposal.md` "Compatibility analysis". "Migrate before cross-layer APP" = must
be migrated (or fail closed) before being executed as a cross-layer APP route.

| # | Consumer | Current reading of the value | Under A | Migrate before cross-layer APP? |
|---|---|---|---|---|
| 1 | v35 `DecoderResult` + `decode_row_layered_fftqspa` (L519–526, L636–747) | current log-beliefs; it0 = log-prior | add + populate `belief_provenance`; hard-decision semantics byte-identical | Yes (producer) |
| 2 | v35 `decode_flooding_fftqspa` (L529–633) | first return after full round | populate `CHECK_UPDATED` | Yes (producer) |
| 3 | D5 `_run_layered_block` (L1341–1364) | unconditional `softmax → app_fed_l2_prior` | require conditioned provenance; fail closed on `PRIOR_ONLY`/unknown | Yes — first mandatory consumer |
| 4 | D5 `_decode_block` (L1026–1059) | extracts beliefs + iterations | carry provenance | Yes (plumbing) |
| 5 | D5 `app_fed_l2_prior` (L353–375) | accepts any `q` as APP | contract unchanged; guard at migrated call site | No (docstring authority) |
| 6 | D5 `historical_g0_decoder` (L1085–1111) | verbatim dict passthrough | propagate provenance key | Yes for cross-layer use |
| 7 | D5 `_bound_hist` (L1616–1632) | verbatim passthrough | propagate provenance key | Yes for cross-layer use |
| 8 | D5 `bind_historical_decoder` (L2453–2475) | verbatim passthrough | propagate provenance key | Yes for cross-layer use |
| 9–18 | v45 L1046; v46 L1166; v47 L1091; v48 L1170; v50 L1454; v51 L1336; v52 L1218; v53 L1265; v54 L1314 (+ `get_l1_app_prior_l2` L432–450); v55 L1428 | `softmax(final_beliefs)` → `q @ P(U2|B,U1)` as BP posterior/APP | stale; migrate/fail closed before any rerun as cross-layer APP; historical results unchanged | Yes, if ever rerun cross-layer |
| 19 | `methods/nbldpc_shell_adapter.py:254` | same pattern (V63 shell) | migrate/fail closed | Yes, if executed cross-layer |
| 20 | `v72p2d3_gf32_contrast.py` L668–671 / L688–689 / L720–721 / L1351–1352 | passthrough + `q @ P` recombination | propagate; fail closed at recombination; label the `np.log(prior_p)` fallback `PRIOR_ONLY` | Yes for a cross-layer run |
| 21 | D7-B harness `v72p2d7_gf32_easy_regime.py` L538 → L554–578 → L627–634 | beliefs compared against exact posterior (tol 1e-10) | R2 immutable; future reruns label it0 as `PRIOR_ONLY_CURRENT_BELIEF`; metric separation (E10) | Yes, if ever rerun |
| 22 | `scripts/execute_v64_fresh_verify.py:188` (discovery beyond review §2) | `softmax → get_l1_app_prior_l2` | same as #9 | Yes, if ever rerun |
| 23 | `nonbinary_v10_fftqspa.py` L444–450 | different decoder, probability-domain `"beliefs"` from `log_prior + c2v` | excluded — not the v35/D5 log-domain contract | No — out of scope |
| 24 | Test-only fakes/stubs (D7-A/D5/v45–v55 tests) | construct/consume `final_beliefs` | update during implementation; missing provenance = not conditioned | n/a |

## Alternatives

| Alt | Description | Pros | Cons | Verdict |
|---|---|---|---|---|
| **A** | Expose provenance; cross-layer APP consumers fail closed | Smallest honest contract correction; no stopping change; no forced computation; no retroactive reinterpretation; fail-closed only where the evidence would have been silently wrong | A `PRIOR_ONLY` early stop cannot feed L2 on that route at all; a true APP need must be decided separately (B) | **Recommended** |
| **B** | Force/compute ≥1 check sweep when a conditioned APP is required | Keeps an L1 APP available for L2 in early-stop cases | Extra sweep; touches stopping/schedule semantics — needs its own frozen decision at the consumer/mode boundary; still an approximation (E05: TREE 0.00689 after one sweep), never exact posterior; changes numerics vs historical runs | Defer; freeze separately per consumer only if needed |
| **C** | Keep prior-only fallback; prohibit APP/conditioned claims only | No behavior change; least work | Not enforceable; the silent `prior @ P` path stays live; consumers still *use* the value as APP | Rejected as a standalone fix |

Decision: adopt A; hold B as a separately frozen decision if a specific
consumer requires it; do not implement any alternative here.

## Deferred implementation outline (not started)

Ordered tasks live in `tasks.md`, all marked
"not started / deferred — must precede any cross-layer APP route". This design
fixes only the semantics above; it deliberately does not choose the guard
mechanism, storage representation of adapter provenance, or the exact
fail-closed error type — those are implementation decisions inside the frozen
contract.
