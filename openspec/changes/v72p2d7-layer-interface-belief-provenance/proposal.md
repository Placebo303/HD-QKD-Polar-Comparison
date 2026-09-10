# Layer-interface belief provenance — proposal (correction; implementation deferred)

> Status: proposal only. This change folder adds no production code and no
> execution. Implementation is deferred and gated (see "Gating rules"). All
> execution/promotion authorizations remain false. Source of the frozen
> architecture rulings: D7-C heavy readiness Addendum A1 §A1.1 (A1 takes
> precedence over R1 on conflict). D7-C R1 itself is not started here.

## What

Freeze a minimal decoder **belief-provenance** contract and the migration rule
for cross-layer APP consumers, so that a cold row-layered GF32 return with zero
completed check sweeps (`PRIOR_ONLY`) can never again be silently forwarded as a
syndrome-conditioned `P(U1 | B, s1)` APP input to another layer.

The correction:

1. exposes an explicit provenance token on every decoder return;
2. requires cross-layer APP consumers to handle provenance explicitly and
   **fail closed** on `PRIOR_ONLY` (or unknown/missing provenance);
3. forbids labeling an unconditioned current belief as a conditioned
   posterior/APP anywhere it is recorded, plotted, or used.

Implementation is **not** part of this document. It is mandatory before the
next sequential, alternating or joint cross-layer APP run, and is **not**
required before D7-C single-layer oracle readiness/execution. D7-C constructs
its four priors directly from the frozen joint model and never consumes
`final_beliefs` across layers; its implementation must not import or depend on
the future interface-rework implementation.

## Why — immutable D7-B R2 evidence (no historical result is retroactively changed)

Evidence root `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`
(exactly five files), accepted by `D7_B_RESULT_ACCEPTANCE_R2.md`; zero-decoder
audit `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md`; independent review verdict
`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`; audited primary outcome
`D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`.

- Stored terminal `D7_B_RESOURCE_OVERRUN` — produced by the RSS telemetry gap
  below, not by any measured resource breach. The frozen terminal is not
  upgraded.
- 64 invoked rows; iteration split **49 × iteration-0 / 15 × iteration-1**
  (48 truth-centered P99/P90/P60 at iteration 0 plus the single all-even-truth
  PAIR cell; 15/16 PAIR at iteration 1).
- Hard decision accepted: 64/64 exact + 64/64 syndrome-consistent at cap 1;
  accepted scope exactly
  `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`.
- Posterior-tolerance failure: **25 tractable iteration-0 rows** fail the
  max-abs ≤ 1e-10 comparison (scale 0.500 SINGLE PAIR / 0.400 TREE P60), plus
  **4 TREE PAIR iteration-1 rows** at 0.00689; 3 SINGLE PAIR iteration-1 rows
  pass. MAP agreement 32/32 on tractable cells.
- Secondary outcome `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP`: 64/64 invoked rows
  store empty `rss_bytes` (psutil absent in the WSL venv, pre-documented);
  unknown telemetry was converted post hoc into the resource terminal. No
  `<2GiB` PASS is or may be claimed.
- **Non-retroactivity**: D7-B R2 numbers, the frozen terminal, the accepted
  scope, historical v45–v55 results, and every existing artifact remain exactly
  as published. This proposal adds only a future interface contract and a
  future labeling rule.

## Four distinct concepts (not one)

1. **Hard decision** — `x_hat`, verified by `H x_hat == s`. Correct 64/64; the
   decoder's actual objective. Ruling 1: this is not redefined or patched here.
2. **Current belief state** — `final_beliefs`, a log-domain current belief.
   At iteration 0 it is the untouched, floored and renormalized log-prior. No
   conditioning promise exists in `DecoderResult` (v35 L519–526) or in the
   row-layered docstring (v35 L645–649); returning current state is internally
   honest. It is **not** inherently a calibrated syndrome-conditioned
   posterior.
3. **Syndrome-conditioned belief / APP** — `P(U1 | B, s1)`: a belief that
   incorporates both the channel observation and the disclosed L1 syndrome.
   Reaching it requires at least one completed check sweep that consumed `s1`.
4. **Downstream cross-layer APP input** — what a consumer actually feeds into
   another layer (D5: `q @ P(U2 | B, U1)` via `app_fed_l2_prior`). Treating (2)
   as (3) and feeding it as (4) is the defect this proposal corrects.

## The E09 defect chain (re-verified from source, HEAD `212f69ba`)

- **E02** — `decode_row_layered_fftqspa`
  (`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`):
  L659–665 initialize `beliefs = log(priors_clean)` (floor 1e-15 + renormalize;
  warm start copies `warm_beliefs`); L676–678 keep `check_to_var` all zeros;
  L681 takes `best_x = argmax(beliefs)`; L683–692, on an initial-syndrome match,
  return `iterations=0`, `status="converged_exact"`,
  `final_beliefs=beliefs` — the untouched log-prior with zero check messages.
  Contrast: `decode_flooding_fftqspa` (L529–633) starts its loop at `it=1`
  (L591) and its first return (L607–616) follows a full check-update round; the
  iteration-0 path exists only in the row-layered schedule, which is what D7-B
  binds (cold, damping 1.0, `warm_beliefs=None`).
- **E03** — at iteration 0, `softmax(final_beliefs)` equals the input prior to
  floating-point (~1e-16); all D7-B prior entries exceed the 1e-15 floor by ≥8
  orders of magnitude, so flooring is the identity. The decoder returns the
  input prior, relabelled.
- **E08** — D5 `app_fed_l2_prior`
  (`v72p2d5_gf32_rate_mother.py` L353–375, docstring L354: "Production L2 prior
  `q @ P` from L1 APP beliefs"; `einsum("nq,qnv->nv")` L374) documents its
  contract input as the L1 posterior conditioned on everything disclosed at L1
  — channel AND the disclosed syndrome — i.e. `q ≈ P(U1 | B, s1)`.
  `oracle_l2_prior` (L378–397; L381 "production decoding must use
  `app_fed_l2_prior`") confirms production L2 may see syndrome evidence only
  through `q`.
- **E09** — D5 `_run_layered_block` (L1341–1364) consumes L1 beliefs
  **unconditionally**: `bel = ...` (L1348), `q = _softmax_rows(bel)`
  (L1349; `_softmax_rows` L948–952), `prior_l2 = app_fed_l2_prior(p2,
  block["bob"], q)` (L1352). On an iteration-0 return, `softmax` yields the
  channel prior (E03), so L2 silently receives `prior @ P` with `s1` dropped
  while L1 reports a valid codeword. The consumer already holds `it1` (L1344)
  but never checks it. Repo-wide grep confirms **no consumer guards
  `iterations == 0`**; the full consumer inventory is in the matrix below.

Latent in practice (real channel priors rarely satisfy the syndrome at
iteration 0), structural in code (the path has no guard), and real in the D7-B
fixture (49/64 returns).

## Frozen architecture rulings (main-thread; A1 addendum §A1.1)

1. v35 hard-decision stopping is not redefined or patched in this workstream.
2. `final_beliefs` is a current log-belief state, not inherently a calibrated
   syndrome-conditioned posterior.
3. A cold-start return with zero completed check sweeps is `PRIOR_ONLY`.
4. A consumer must not label `PRIOR_ONLY` as syndrome-conditioned APP.
5. Sequential/alternating/joint consumers must carry explicit belief provenance
   before using returned beliefs as cross-layer evidence.
6. `iterations > 0` suffices to show ≥1 check sweep in the current cold
   row-layered decoder, but the durable contract should use an explicit
   provenance field rather than consumer inference.
7. Warm-start provenance is separate and must not be guessed from iterations;
   out of scope until a route actually needs warm starts.
8. D7-C is single-layer oracle diagnosis. It records exact/syndrome/iterations
   and may record current-belief confidence, but must never feed those beliefs
   into another layer nor call them conditioned posterior without provenance.

This ruling permits D7-C readiness only after independent review of this
proposal. It does not accept a specific interface implementation.

## Proposed minimal provenance contract

Field: `belief_provenance`, attached to the decoder-returned result (v35
`DecoderResult` field and adapter result dicts). Exact tokens:

| Token | Meaning | Current-decoder mapping |
|---|---|---|
| `PRIOR_ONLY` | Cold start, zero completed check sweeps; returned beliefs are the floored/renormalized input log-prior; not syndrome-conditioned. | row-layered return with `iterations == 0` (v35 L683–692) |
| `CHECK_UPDATED` | At least one full check sweep completed before the return; check messages have been consumed. | row-layered returns with `iterations > 0` (L728–736, L738–747); all flooding returns (first return follows a full round, L591, L607–616) |
| `WARM_START_UNSPECIFIED` | Initial beliefs came from a warm start whose provenance is not carried; never inferred from iterations; out of scope until a route needs warm starts. | any return where a non-`None` `warm_beliefs` seeded the state (v35 L660–661) and no caller-supplied provenance exists |

Defaulting/back-compat:

- `DecoderResult` gains the field with a default of `None`
  (unspecified/legacy), appended so existing positional construction and all
  current test fakes keep working.
- Adapter dicts carry an optional `belief_provenance` key; absence means
  unspecified.
- A consumer that requires a conditioned APP must treat `None`/absent as
  **not conditioned** and fail closed. `None` is never upgraded to
  `CHECK_UPDATED`.
- The producer never guesses warm-start provenance from `iterations` (ruling 7).

## Compatibility analysis — every inventoried `final_beliefs` consumer

Re-verified from source; D7-B review §2 is the cross-check, not the only
evidence. "Under A" = recommended alternative below. "Untouched?" = physical
file change required to land the correction vs. permitted to stay as-is until
it is next used for a cross-layer APP route.

| # | Consumer (file:line) | Current behavior on the value | Under A | Untouched? |
|---|---|---|---|---|
| 1 | v35 `DecoderResult` + `decode_row_layered_fftqspa` (`v35_algorithm_development.py` L519–526; L636–747; it0 return L683–692; `decode_damped_row_layered_fftqspa` L750–766 delegates) | Returns current log-beliefs on all five return sites; iteration-0 return is the untouched log-prior; no conditioning promise | Additive `belief_provenance` field + populate: it0 cold → `PRIOR_ONLY`; `iterations>0` → `CHECK_UPDATED`; warm seed → `WARM_START_UNSPECIFIED`; field defaulted | No — this is the additive producer change. Hard-decision fields/stopping stay byte-identical (ruling 1) |
| 2 | v35 `decode_flooding_fftqspa` (L529–633; loop L591; first return L607–616) | First return follows a full check-update round; no iteration-0 path | Populate `CHECK_UPDATED`; no warm-start parameter | No — additive populate only; never `PRIOR_ONLY` |
| 3 | D5 `_run_layered_block` (`v72p2d5_gf32_rate_mother.py` L1341–1364; key L1344, L1348–1352) | Unconditional `softmax(bel)` → `app_fed_l2_prior`; no `iterations == 0` guard; **the E09 hazard** | Explicitly require conditioned provenance before forwarding; `PRIOR_ONLY`/`None`/unknown → fail closed (no silent `prior@P` as APP). Any explicitly labeled prior-only fallback must never claim APP | No — the one mandatory production consumer migration before any cross-layer APP route |
| 4 | D5 `_decode_block` (L1026–1059; `beliefs = get("final_beliefs")` L1053) | Extracts beliefs + `iterations`; drops other result fields | Carry provenance alongside beliefs so the consumer can check it | No — minimal plumbing (or read from the same result object) |
| 5 | D5 `app_fed_l2_prior` (L353–375) | Accepts any probability vector as `q ≈ P(U1|B,s1)`; no provenance parameter | Contract stays the authority; fail-closed guard lives at the migrated call site; optionally assert conditioned input | May remain signature-stable; docstring contract unchanged. `oracle_l2_prior` (L378–397) stays untouched (diagnostic) |
| 6 | D5 `historical_g0_decoder` (L1085–1111; dict L1106–1111) | Verbatim passthrough of `final_beliefs` | Propagate `belief_provenance` in the returned dict | No for cross-layer use; hard-decision-only use unaffected |
| 7 | D5 `_bound_hist` (L1616–1632; L1631) | Verbatim passthrough | Propagate provenance | No for cross-layer use |
| 8 | D5 `bind_historical_decoder` (L2453–2475; L2472) | Verbatim passthrough | Propagate provenance | No for cross-layer use |
| 9 | v45 `v45_l1_app_soft_transfer.py:1046` (header L8) | `q = softmax_beliefs(res.final_beliefs)` → `q @ P(U2|B,U1)`; labeled BP posterior/APP approximation | Stale under the corrected contract; migrate or fail closed before any rerun as cross-layer APP; historical results unchanged | Physically yes (no live route); no as a live cross-layer path |
| 10 | v46 `v46_verification_semantics.py:1166` (header L8) | Same pattern | Same as #9 | Same as #9 |
| 11 | v47 `v47_h1_redundancy_compression.py:1091` (header L7) | Same pattern | Same as #9 | Same as #9 |
| 12 | v48 `v48_heldout_confirm.py:1170` | Same pattern | Same as #9 | Same as #9 |
| 13 | v50 `v50_l2_structure_factorial.py:1454` | Same pattern | Same as #9 | Same as #9 |
| 14 | v51 `v51_lane_c_label_nbace.py:1336` | Same pattern | Same as #9 | Same as #9 |
| 15 | v52 `v52_rate_adaptive_l2_rescue.py:1218` | Same pattern | Same as #9 | Same as #9 |
| 16 | v53 `v53_rate_adaptive_l2_heldout_confirm.py:1265` | Same pattern | Same as #9 | Same as #9 |
| 17 | v54 `v54_two_stage_incremental_l2_rescue.py:1314`; `get_l1_app_prior_l2` L432–450 (`out[i] = qi @ p_u2`) | Same pattern; the canonical L1→L2 APP mixer | Same as #9 | Same as #9 |
| 18 | v55 `v55_two_stage_rescue_independent_test.py:1428` | Same pattern | Same as #9 | Same as #9 |
| 19 | `methods/nbldpc_shell_adapter.py:254` (→ `get_l1_app_prior_l2` L259) | Same pattern in the live V63 shell adapter (PA proxy is a placeholder; no hidden claim) | Migrate or fail closed before any cross-layer APP run | No if executed cross-layer; not scheduled |
| 20 | `v72p2d3_gf32_contrast.py` L668–671 (fake-path fallback `np.log(prior_p)` — the log-prior neutral-element idiom), L688–689 (production extraction), L720–721 (dict output), L1351–1352 (`q = softmax_beliefs_history(l1["final_beliefs"])` → `build_l2_prior_from_l1`) | Passthrough + `q @ P` recombination on the production G-route | Propagate provenance; fail closed at recombination when not conditioned; the log-prior fallback is by construction `PRIOR_ONLY` and must be labeled so | No for a cross-layer run |
| 21 | D7-B harness `v72p2d7_gf32_easy_regime.py` `invoke_decoder` L516–547 (L538) → `posterior_stats` L554–578 → exact comparison L627–634 (`POST_TOL` L44 = 1e-10) | Consumes returned beliefs as a claimed exact posterior; fails it0 rows for lacking a conditioned posterior | D7-B R2 stays immutable. Any future rerun: record iteration-0/current beliefs only as `PRIOR_ONLY_CURRENT_BELIEF`, never posterior/APP; separate hard-decision success from belief calibration (E10 metric separation) | Yes now (result frozen); no for any future rerun of this metric |
| 22 | **Inventory discovery beyond D7-B review §2**: `scripts/execute_v64_fresh_verify.py:188` (→ `get_l1_app_prior_l2` L192) | Same unconditional L1 `softmax(final_beliefs)` → L2 prior pattern, in the one-off V64 guarded runner | Same as #9: migrate or fail closed before any rerun; V64 run is complete and not scheduled | Physically yes; no as a live cross-layer path |
| 23 | Sibling `nonbinary_v10_fftqspa.py` L444–450 | Different decoder: probability-domain `"beliefs"` built from `log_prior + c2v`; no v35 `DecoderResult`, no `final_beliefs` field | **Excluded.** This contract applies to the certified v35/D5 log-domain GF32 path; the sibling's separate probability-domain contract is out of scope | Yes — out of scope |
| 24 | Test-only constructs: D7-A tests (`test_v72p2d7_gf32_decoder_certification.py` L217–292), D5/v45–v55 test fakes and `SimpleNamespace`/dict stubs | Construct/consume `final_beliefs` for testing | Test-only, not production contract; update fakes during the future implementation so missing provenance is treated as not-conditioned | n/a — updated as needed by the implementation tests |

Count: 24 table rows = 22 `final_beliefs`-relevant production/interface
entries (rows 1–22) + 1 explicit sibling exclusion (row 23) + 1 test-only note
(row 24). Discovery beyond the D7-B review §2 list: entry #22
(`scripts/execute_v64_fresh_verify.py:188`).

## Alternatives

### A. Expose provenance only; consumers fail closed (recommended)

- Add the additive provenance field; populate it exactly at the producer;
  the migrated consumer requires `CHECK_UPDATED` for cross-layer APP and fails
  closed on `PRIOR_ONLY`/`None`/unknown.
- Tradeoffs: smallest honest contract correction; no decoder stopping change;
  no forced computation; no retroactive reinterpretation; fail-closed costs an
  aborted cross-layer call when L1 stops at iteration 0 with `PRIOR_ONLY`, which
  is exactly the case whose L2 evidence would have been silently wrong. It
  does not by itself make L1's iteration-0 early stop feed L2 at all; if a
  specific consumer truly needs a conditioned L1 APP in that case, that is
  decision B and must be frozen separately.

### B. Force/compute one check sweep when a conditioned APP is required

- When a consumer needs `q ≈ P(U1|B,s1)`, configure the L1 decode so at least
  one full sweep runs before the return (i.e. never return `PRIOR_ONLY` on that
  route), so the forwarded `q` carries `s1`.
- Tradeoffs: preserves a cross-layer APP prior in cases A would refuse; costs
  one extra sweep; touches stopping/schedule semantics (must not redefine v35's
  hard-decision stopping — ruling 1 — so it needs its own frozen design at the
  consumer/mode boundary); still not a calibrated posterior (E05: TREE 0.00689
  error after one sweep), so the label must remain "BP APP approximation", not
  exact posterior; changes numerics versus historical runs on that route.

### C. Keep prior-only fallback but prohibit APP/conditioned claims (documentation/guard only)

- Keep forwarding as today, but require that no artifact/consumer may label the
  result APP or a conditioned posterior.
- Tradeoffs: no behavior change at all and the least work; but it cannot
  enforce anything — the same silent `prior @ P` path remains live and can be
  reintroduced by any future caller, and existing consumers still *use* the
  value as APP. Weakest option; rejected as the sole correction.

**Recommendation: A first** (smallest honest contract correction), followed by
a separately frozen decision on whether a specific consumer requires B. C is
rejected as a standalone fix. None of A/B/C is implemented in this change.

## Acceptance tests for the future implementation (no implementation here)

Enumerated, for the future implementation task; IDs stable:

- PV-01: cold row-layered iteration-0 early-exit return carries
  `belief_provenance == "PRIOR_ONLY"` and `iterations == 0`.
- PV-02: a cold row-layered return after ≥1 completed sweep carries
  `CHECK_UPDATED`.
- PV-03: the flooding decoder's first return is not `PRIOR_ONLY`
  (carries `CHECK_UPDATED`).
- PV-04: a warm start without explicit provenance is
  `WARM_START_UNSPECIFIED`, never inferred from `iterations`.
- PV-05: existing hard-decision results are unchanged — on frozen fixtures the
  `x_hat`/`syndrome_ok`/`iterations`/`status`/`final_beliefs` values are
  identical with and without the field; the field is additive and defaulted.
- PV-06: a consumer requiring conditioned APP raises/fails closed on
  `PRIOR_ONLY`.
- PV-07: the same consumer fails closed on missing/`None`/unknown provenance
  (legacy dicts and `SimpleNamespace` fakes without the field cannot silently
  pass).
- PV-08: the migrated consumer does not compute the L2 APP prior from a
  `PRIOR_ONLY` q (spy/assert on `app_fed_l2_prior`/`get_l1_app_prior_l2`).
- PV-09: `CHECK_UPDATED` passes the guard and reproduces the existing `q @ P`
  result on a matched fixture.
- PV-10: D7-B-style diagnostics record an iteration-0 current belief only as
  `PRIOR_ONLY_CURRENT_BELIEF`, never posterior/APP; no conditioned-posterior
  tolerance is applied to an unconditioned belief.
- PV-11: provenance propagates through the D5 adapter dicts
  (`historical_g0_decoder`, `_bound_hist`, `bind_historical_decoder`) and
  `_decode_block`; v72p2d3's dict path carries it to `build_l2_prior_from_l1`.
- PV-12: no retroactive change — stored/historical artifacts are untouched;
  tests assert the new field does not alter existing stored values or
  previously published numbers.
- PV-13: hard-decision-only consumers that never request a cross-layer APP keep
  working without handling provenance.
- PV-14: import-graph test — the interface-rework implementation and the future
  D7-C oracle implementation share no import dependency in either direction.

## Gating rules (frozen)

- No historical result is retroactively changed. This includes the D7-B R2
  evidence/terminal/scope and all v45–v55 results.
- Interface implementation is **mandatory before the next sequential,
  alternating or joint cross-layer APP run**, but **not before D7-C
  single-layer oracle readiness/execution**.
- D7-C's implementation must not import or depend on the future
  interface-rework implementation; D7-C records exact/syndrome/iterations and
  may record current-belief confidence only, never feeding it into another
  layer or calling it conditioned posterior without provenance (ruling 8).
- This change does not start D7-C; its OpenSpec/implementation resumes only
  after independent review of this proposal reaches
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`.
