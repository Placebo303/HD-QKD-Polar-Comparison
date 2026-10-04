# D7 root-cause and route-reset R1 — design

> Frozen implementation contract for Phases A–F of
> `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md`.
> No threshold, seed, arm, evidence meaning, or G2 semantics may change
> without a packet revision.

## 1. Canonical transfer helpers (B01)

The smallest shared surface that lets G1 and D7 form `q_L1` and `P(U2|B)`
through one canonical implementation is exposed in the accepted D5 module
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`:

- `canonical_source_q(log_beliefs)` — validates a finite 2-D `(n, q>=2)`
  log-belief matrix (the frozen contract uses `q = 32`) and returns the
  rowwise softmax; this is the single canonical `q_L1` / `q_L2` probability
  conversion. It delegates to the existing `_softmax_rows` (identical
  operation order to the accepted D7 `softmax_source_q` / `_softmax_rows`
  implementations).
- `canonical_transfer_l2_prior(p2, bob_symbols, q_l1)` — the single canonical
  `P(U2|B) = sum_u1 q_L1(u1) P2(u1,b,u2)` mixer with the accepted
  floor/renormalize once. It delegates to the existing `app_fed_l2_prior`.

`_run_layered_block` uses `canonical_source_q` for the source conversion and
the same `app_fed_l2_prior` implementation that `canonical_transfer_l2_prior`
exposes for the transfer prior (no operation order change, no decoder
rewrite).

## 2. Same-input comparison contract (B02/B03/B04)

The consistency harness lives in the new module
`comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`
and compares, for the same in-memory graph, block, priors, and injected
decoder result:

1. L1 input prior,
2. L1 posterior-to-probability conversion `q`,
3. L2 transfer prior,
4. target syndrome,
5. decoded target,
6. per-layer counters.

Frozen comparison semantics, pre-registered before the tests run:

- **Exact equality** (`np.array_equal`) is required for `q`, both target
  syndromes, the decoded target, and the per-layer counters. These are
  produced by identical operations or identical injected results.
- **Numerical equality within `atol=1e-12`** (`rtol=0`) is required for the
  two probability tensors computed by algebraically identical formulas in
  different operation order (L1 input prior and L2 transfer prior). The
  rationale is float reassociation only; a real formula mismatch is
  `O(1)`, four orders of magnitude above the bound. This matches the
  accepted precedent `test_pv_09` / `test_run_layered_block_bridge`
  (`np.allclose(..., atol=1e-12)`).
- Every comparison records the maximum absolute difference. The harness
  returns a localized first mismatch (tensor name, flat index, both values)
  whenever the frozen criterion fails; per B04 the operator then STOPs, does
  not compensate, and does not tune.

The harness also covers the provenance boundary (B03): exact `CHECK_UPDATED`,
missing key, explicit `None`, `PRIOR_ONLY`, an unknown token, and a valid
zero-iteration prior-only return. Every non-`CHECK_UPDATED` case must fail
closed before the L2 mixer and before the L2 decoder on both the G1 path
(`_run_layered_block`, default mode) and the D7 path (`require_check_updated`
/ `check_source_eligibility`).

## 3. Additive G1 evidence schema (B05)

`_run_layered_block` gains a keyword-only `on_blocked_transfer="raise"`
(default) so the accepted fail-closed raise contract is unchanged for all
existing callers; `"record"` is used only by the evidence scan and returns a
blocked record with `transfer_invoked=False` and a named
`transfer_blocked_reason` (no mixer call, no L2 decoder call).

Per-block success records add: `app_l2_exact`, per-layer syndrome flags,
per-layer iterations, `app_l1_provenance`, `transfer_invoked`,
`transfer_blocked_reason`.

Per-`f` G1 aggregates add: `app_l1_exact_count`, `app_l2_exact_count`,
`app_l1_syndrome_ok_count`, `app_l2_syndrome_ok_count`,
`app_l1_iterations_total`, `app_l2_iterations_total`,
`provenance_check_updated_count`, `transfer_invoked_count`,
`transfer_blocked_count`.

`write_g1_evidence` copies the new fields additively: existing keys, existing
file names, and existing column order are preserved; new columns are
appended.

## 4. No-write decoder probe (B06)

`probe_historical_decoder_provenance(*, decode_fn=None, ...)` in the D5 module
is a pure callable that:

- resolves the historical adapter only when `decode_fn is None`
  (`bind_historical_decoder()`, no import of the decoder beyond the accepted
  lazy bind);
- performs at most one decode on an explicit in-memory fixture (provided or
  the existing tiny G0 fixture);
- reports `is_historical`, the provenance token, whether it equals
  `CHECK_UPDATED`, iterations, and shape validity;
- creates no output root, writes no file, starts no phase, and reads no
  authorization state.

A–F tests always inject a fake decoder; the production decoder call count
stays zero. Running it without injection is an X1 decision.

## 5. Multi-graph exploratory design (Phase C, frozen)

Module: the new consistency/multi-graph module. CLI:
`scripts/v72p2d7_consistency_multigraph.py` (no default output root).

### 5.1 Frozen matrix

- graph pairs, in order: `(2026090501, 2026090502)` baseline,
  `(2026091401, 2026091402)`, `(2026091501, 2026091502)`; no graph search or
  replacement after observation.
- block seeds `2026091300..2026091315` (16) for every graph pair.
- n = 64; f = 1.2 primary with rows L1 = 59 / L2 = 52; f = 1.0
  negative-margin sanity with rows L1 = 49 / L2 = 43.
- arms: marginal L1, L1-to-L2 transfer, marginal L2, L2-to-L1 transfer, plus
  forward and reverse joint outcomes. Maximum calls
  `3 graphs * 2 f * 16 blocks * 4 arms = 384`.
- mothers per graph pair: D5-native `build_dv3_nested_support(64, 64, 49,
  l1_seed)` + `assign_gf32_coefficients(sup, l1_seed, None, 64)` for L1 and
  `(64, 64, 43, l2_seed)` + coefficients for L2.
- estimator: accepted Model-F root
  `workspace/v72p2d5_model_f_input/20260907_r1` through
  `prepare_model_f_prior_candidate` (the accepted D7 concentration/backoff
  contract used by D7-C/D/E/F/H); `max_iter=90`, `damping_alpha=1.0`, cold,
  row-layered, GF32 poly 37.
- transfer gating: a transfer arm is invoked only when the source arm's
  return is non-crash, finite, shape-valid, and has provenance exactly
  `CHECK_UPDATED`. Source exactness never gates. A blocked transfer is a
  recorded non-invocation, never replaced.
- oracle priors are not used in this diagnostic.

### 5.2 Output (fresh user-specified `workspace/` root; never overwrite)

`manifest.json`, `call_records.csv`, `block_pairs.csv`, `graph_summary.csv`,
`across_graph_summary.json`, `report.md`, `command_log.txt`.

### 5.3 Statistics (descriptive only)

- Raw paired discordant counts per graph and per f: `forward_only`,
  `reverse_only`, `both`, `neither`, where forward means the L1 marginal
  decoded exactly and the gated L1-to-L2 transfer decoded exactly, and
  reverse is the symmetric L2-origin chain.
- Exact two-sided McNemar/binomial p-value on `(forward_only, reverse_only)`
  with `p=0.5` (stdlib `math.comb`).
- Wilson 95% confidence interval of `forward_only / (forward_only +
  reverse_only)` when the denominator is positive, else `None`.
- No pass/fail decision uses only a p-value; no pooling hides graph (or f)
  heterogeneity.

### 5.4 Terminal vocabulary (C07)

Exactly one terminal, each carrying
`EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`:

- `GRAPH_SENSITIVITY_OBSERVED` — at the primary f = 1.2 the three per-graph
  paired vectors `(forward_only, reverse_only, both, neither)` are not all
  identical;
- `NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE` — the three primary
  vectors are identical;
- `INCONCLUSIVE` — coverage incomplete (missing/crashed/nonfinite slot) or
  the primary cells cannot be formed;
- `MULTIGRAPH_ENGINEERING_BLOCKED` — engineering/resource blocker (wall
  budget exhausted or RSS ceiling exceeded).

### 5.5 Authorization

The runner refuses before any Model-F read, decoder bind, or root creation
unless `x2_multigraph_execution_authorized` is true in the cycle state and
the caller passes `authorized=True`. No production execution is performed by
this change.

## 6. Bounded reference ladder (Phase D)

In the new module, dormant until X3 authorization:

- arm `ROW_LAYERED_90`: the existing row-layered decoder at `max_iter=90`;
- arm `ROW_LAYERED_360`: the same existing decoder at the frozen ceiling
  `max_iter=360`;
- arm `FLOODING_90`: the existing materially different flooding schedule at
  `max_iter=90`; included only because it already exists and accepts the same
  `(H, prior, syndrome)` contract (D7-D bind). No new decoder family.

Per arm record: exact, syndrome-valid, residual syndrome weight, iterations,
finite/crash status, and whether the arm changes the outcome relative to
`ROW_LAYERED_90`. The exact posterior score of truth and of the returned
candidate under the input prior and hard check factors is reported only where
exactly computable (tiny enumeration); otherwise it is `None` with
`posterior_score_computable=False`.

`exact_posterior_scores` enumerates syndrome-consistent candidates for tiny
`n` (cap `32**n <= 32768`), scores each candidate by its prior probability,
normalizes over the syndrome-consistent set, and returns posterior mass and
rank for requested candidates. Tiny tests cross-check it against an
independent brute-force loop. n=64 results are labeled
`STRONG_REFERENCE_DIAGNOSTIC`, never ML proof or information-theoretic
feasibility.

The ladder is applicable only to the frozen multi-graph blocks that fail at
f=1.2; no adaptive seed replacement.

## 7. G2 reconciliation (Phase E)

The current implementation already matches the accepted D5 plan:

- n = 256; f = `(1.0, 1.1, 1.2)`; rows L1 `{196, 215, 235}`, rows L2
  `{172, 189, 206}`; block seeds `2026091000..2026091199` (200); graph seeds
  L1 `2026090501` / L2 `2026090502`; APP 200 and oracle 40 per f (1320 calls
  total); four-state grading `G2_SYNTHETIC_QUALIFIED / G2_INCONCLUSIVE /
  G2_CURRENT_CONFIGURATION_FAILED / IMPLEMENTATION_OR_NUMERICAL_BLOCKED`.

Additive reconciliation deltas:

- `run_g2_phase` records `wall_seconds` and run `peak_rss_bytes`;
- `_grade_g2` accepts optional `wall_seconds` / `peak_rss_bytes` and returns
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED` when the frozen G2 wall ceiling
  (`3600 s`) or RSS ceiling (`< 2 GiB`) is exceeded;
- `write_g2_evidence` copies the new per-layer metrics and the wall/RSS
  fields additively (existing keys and file names preserved).

No unconditional `ROUTE_DEAD` wording is added. `G2_RUNTIME_UNVERIFIED` is the
runtime status: no runtime estimate is claimed until measured/scaled probes
are explicitly authorized; P0's 485-second projection is not treated as a
reliable G2 estimate.

## 8. Lifecycle and review

Terminal for this change after implementation is
`IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`. The operator does not
self-accept, does not run X1–X4, and does not draw route or scientific
conclusions. `REVIEW_ENTRYPOINT.md` and the scoped changed-file manifest are
prepared in the cycle folder for the independent reviewer.

## 9. Phase P operational closeout (master R1 packet; no science change)

Phase P closes the real X1/X3/X4 entrypoints on the master R1 packet without
redefining any threshold, seed, arm, evidence meaning, or G2 semantics.

- **X1**: `--historical-provenance-probe` calls
  `probe_historical_decoder_provenance(decode_fn=None)` exactly once and
  emits one JSON record; exit 0 only for exact `CHECK_UPDATED` + finite +
  shape-valid beliefs + `iterations >= 1`; no file, no root. `--consistency`
  is explicitly `same-input synthetic consistency`, never X1.
- **X3**: reads only the immutable X2 root; selects every f=1.2 executed
  non-crash finite non-exact call record preserving identity exactly; plans
  `3` ladder arms per record (`<= 576`) before binding; deterministically
  reconstructs H/prior/syndrome/truth (TARGET priors via a verified
  `ROW_LAYERED_90` source replay, <= 96, cached per source slot); a
  field-exact baseline replay is a hard gate; evidence is a fresh seven-file
  root, never overwritten, labelled `STRONG_REFERENCE_DIAGNOSTIC`.
- **X4**: `--g2` requires the X4 grant and every D5 execution flag false,
  calls the existing `run_g2_synthetic(authorized=True)` exactly once, and
  writes only the frozen fresh G2 root; the D5 `g2_execution_authorized`
  flag is never set.
- **Accounting note**: the frozen "max 576 calls" is enforced for the
  three-arm ladder; TARGET reconstruction replays are deterministic
  reconstruction calls bounded by the 96 f=1.2 source slots and are reported
  separately in the X3 manifest/summary. The readiness record flags this
  single interpretation for the Phase P independent review.

Lifecycle after Phase P implementation and tests is
`X_PHASE_READY_PENDING_INDEPENDENT_READINESS_REVIEW`; P10 remains with the
orchestrator and is not self-accepted.
