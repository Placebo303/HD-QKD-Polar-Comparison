# D7-B layer-interface correction proposal R1 (proposal only; zero implementation)

- Task source: D7-C heavy readiness Addendum A1 §A1.1 (frozen main-thread
  architecture ruling) and §A1.2 (Phase P correction proposal), superseding
  nothing else in R1; A1 takes precedence over R1 on conflict. D7-C R1 is not
  started here.
- Inputs (read-only): `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md`,
  `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_R1.md`,
  `D7_B_RESULT_ACCEPTANCE_R2.md`, `D7_B_PREREG_R1.md`, frozen R2 root scalars,
  and re-verified source at HEAD `212f69ba`
  (branch `formal-ir-v72p1-addendum-clean`).
- OpenSpec change: `openspec/changes/v72p2d7-layer-interface-belief-provenance/`
  (proposal/design/tasks/spec delta). Recommended alternative: **A**.
- Status: proposal for independent review; **no implementation**. All
  authorizations false. The required independent review document
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_REVIEW_R1.md` does not yet exist
  (placeholder below); the sole allowed PASS is
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`.

## 1. Immutable evidence and verdicts

- Accepted D7-B R2 root
  `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/` (five
  files), lifecycle authorize `0327c65` → one invocation → revoke `3fe63ef`,
  accepted by `D7_B_RESULT_ACCEPTANCE_R2.md`.
- Stored terminal `D7_B_RESOURCE_OVERRUN`; 64 invoked rows; `calls_not_needed`
  384; `confirmed/partial false`.
- Audited verdict `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`; primary
  outcome `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`; secondary
  `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP`; accepted scope exactly
  `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`.
- Hard decision accepted: 64/64 exact + 64/64 syndrome-consistent at cap 1.
- Posterior-tolerance failure: 25 tractable iteration-0 rows fail max-abs
  ≤ 1e-10 (0.500 SINGLE PAIR / 0.400 TREE P60), plus 4 TREE PAIR iteration-1
  rows at 0.00689; 3 SINGLE PAIR iteration-1 rows pass; MAP agreement 32/32.
- RSS telemetry gap: 64/64 invoked rows store empty `rss_bytes` (psutil absent
  in the WSL venv); no measured breach; no `<2GiB` PASS claimed; the terminal
  stands and is not upgraded.
- **No historical result is retroactively changed by this proposal.**

## 2. The 49/15 split (reproduced)

Iteration counter over the 64 invoked rows: `{'0': 49, '1': 15}` —
48 truth-centered P99/P90/P60 cells at iteration 0 (their priors peak uniquely
at the true word, so the initial MAP satisfies the syndrome by construction;
an initial-MAP sanity region, not iterative BP gain), the single all-even-truth
PAIR cell (SINGLE_CHECK_D3 seed 2026091202, tie broken to `min(x, x^1)`;
mechanism independently re-derived in review §1), and 15/16 PAIR cells at
iteration 1. Source: R2 `decoder_records.csv`; audit E01/E05; review §1.

## 3. Exact defect chain E02/E03/E08/E09 (re-verified from source)

All line references re-checked at HEAD `212f69ba`.

- **E02 — iteration-0 return contains no check message.**
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
  `decode_row_layered_fftqspa` L636–747: L659–665 initialize
  `beliefs = log(priors_clean)` (floor 1e-15 + renormalize; warm copy
  otherwise); L676–678 keep `check_to_var` all zeros; L681 `best_x =
  argmax(beliefs)`; L683–692 on syndrome match return `iterations=0`,
  `status="converged_exact"`, `final_beliefs=beliefs` — the untouched
  log-prior. `decode_flooding_fftqspa` has no such path (loop starts `it=1`,
  L591; first return L607–616 follows a full check-update round). D7-B binds
  the row-layered decoder cold (damping 1.0, `warm_beliefs=None`).
- **E03 — softmax of the it0 return equals the input prior.** Prior entries
  exceed the 1e-15 floor by ≥8 orders, so flooring is identity;
  `softmax(final_beliefs₀)` differs from the prior by ~1e-16. The decoder
  returned the input prior, relabelled.
- **E08 — D5 contract expects a conditioned APP.**
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  `app_fed_l2_prior` L353–375 (docstring L354: "Production L2 prior `q @ P`
  from L1 APP beliefs"; `einsum("nq,qnv->nv")` L374) has contract input
  `q ≈ P(U1 | B, s1)` — channel observations AND the disclosed syndrome.
  `oracle_l2_prior` L378–397 (L381: production must use `app_fed_l2_prior`)
  confirms production L2 may see syndrome evidence only through `q`.
- **E09 — the silent omission.** D5 `_run_layered_block` L1341–1364:
  `bel = ...` (L1348), `q = _softmax_rows(bel)` (L1349; `_softmax_rows`
  L948–952), `prior_l2 = app_fed_l2_prior(p2, block["bob"], q)` (L1352), all
  unconditional; `it1` is available (L1344) but never checked. On an
  iteration-0 return the L2 prior becomes `prior @ P` instead of `APP @ P`:
  the disclosed `s1` is silently dropped while L1 reports a valid codeword.
  Latent in practice, structural in code. Repo-wide grep confirms no consumer
  guards `iterations == 0`.

Four distinct concepts: (1) hard decision — 64/64 correct, the decoder's real
objective, not redefined here; (2) current belief state — `final_beliefs`,
a log-domain current state with no conditioning promise (`DecoderResult`
L519–526; docstring L645–649); (3) syndrome-conditioned belief / APP —
`P(U1 | B, s1)`, requires ≥1 completed check sweep; (4) downstream cross-layer
APP input — what a consumer feeds another layer, which is where (2) was
silently sold as (3).

## 4. Provenance contract proposal (frozen main-thread rulings applied)

Field `belief_provenance` on the returned result; exact tokens
`PRIOR_ONLY` / `CHECK_UPDATED` / `WARM_START_UNSPECIFIED`; `None`/absent =
unspecified/legacy, never upgraded. Cold it0 zero-sweep → `PRIOR_ONLY`;
`iterations > 0` (and all flooding returns) → `CHECK_UPDATED`; warm-seeded
returns → `WARM_START_UNSPECIFIED` (never inferred from iterations). Hard-
decision fields and stopping unchanged.

The eight frozen main-thread rulings (A1 addendum §A1.1) are carried verbatim
in `proposal.md`; the operational delta is: `PRIOR_ONLY` must not be labeled
syndrome-conditioned APP; cross-layer consumers must carry explicit provenance
and fail closed; warm-start provenance is out of scope until needed; D7-C is
single-layer only.

## 5. Consumer inventory (complete; re-verified)

24 table rows = 22 `final_beliefs`-relevant production/interface entries
(rows 1–22) + 1 explicit sibling exclusion (row 23) + 1 test-only note
(row 24). Full analysis with "current / under A / untouched" columns:
`proposal.md`; frozen matrix: `design.md`.

| # | Consumer (file:line) | Current reading |
|---|---|---|
| 1 | v35 `DecoderResult` + `decode_row_layered_fftqspa` (L519–526, L636–747; damped variant L750–766 delegates) | current log-beliefs; it0 = log-prior |
| 2 | v35 `decode_flooding_fftqspa` (L529–633; first return L607–616) | first return after full check round |
| 3 | D5 `_run_layered_block` (L1341–1364) | unconditional `softmax → app_fed_l2_prior` (E09) |
| 4 | D5 `_decode_block` (L1026–1059; L1053) | extracts beliefs + iterations |
| 5 | D5 `app_fed_l2_prior` (L353–375) | accepts any `q` as `P(U1|B,s1)` |
| 6 | D5 `historical_g0_decoder` (L1085–1111) | verbatim dict passthrough |
| 7 | D5 `_bound_hist` (L1616–1632) | verbatim passthrough |
| 8 | D5 `bind_historical_decoder` (L2453–2475) | verbatim passthrough |
| 9 | v45 `v45_l1_app_soft_transfer.py:1046` (header L8) | `softmax(final_beliefs)` → `q @ P` as APP |
| 10 | v46 `v46_verification_semantics.py:1166` (header L8) | same |
| 11 | v47 `v47_h1_redundancy_compression.py:1091` (header L7) | same |
| 12 | v48 `v48_heldout_confirm.py:1170` | same |
| 13 | v50 `v50_l2_structure_factorial.py:1454` | same |
| 14 | v51 `v51_lane_c_label_nbace.py:1336` | same |
| 15 | v52 `v52_rate_adaptive_l2_rescue.py:1218` | same |
| 16 | v53 `v53_rate_adaptive_l2_heldout_confirm.py:1265` | same |
| 17 | v54 `v54_two_stage_incremental_l2_rescue.py:1314`; `get_l1_app_prior_l2` L432–450 | same; canonical mixer |
| 18 | v55 `v55_two_stage_rescue_independent_test.py:1428` | same |
| 19 | `methods/nbldpc_shell_adapter.py:254` (→ L259) | same pattern (V63 shell) |
| 20 | `v72p2d3_gf32_contrast.py` L668–671 / L688–689 / L720–721 / L1351–1352 | passthrough + `q @ P` recombination; fallback `np.log(prior_p)` |
| 21 | D7-B `v72p2d7_gf32_easy_regime.py` L538 → L554–578 → L627–634 | beliefs vs exact posterior (tol 1e-10) |
| 22 | **Discovery beyond review §2**: `scripts/execute_v64_fresh_verify.py:188` (→ L192) | unconditional `softmax → get_l1_app_prior_l2` |
| 23 | Sibling `nonbinary_v10_fftqspa.py` L444–450 (excluded) | different probability-domain decoder, no `final_beliefs` field |
| 24 | Test-only fakes (D7-A/D5/v45–v55 tests) | construct/consume `final_beliefs`; not production contract |

Review §2 previously reported "no further production consumer"; the V64
runner entry #22 is the one additional execution-harness consumer found by
this re-sweep (`comparison_bench/src`, `scripts/`, `tools/`, `src/`,
`experiments/`; no hits in `analysis/`). No live cross-layer route uses it;
migration/fail-closed applies before any rerun.

## 6. Alternatives and recommendation

- **A (recommended)** — expose provenance only; cross-layer APP consumers fail
  closed. Smallest honest contract correction; no stopping change; no forced
  computation; no retroactive reinterpretation. Cost: a `PRIOR_ONLY` early stop
  cannot feed L2 on that route at all.
- **B** — force/compute one check sweep when a conditioned APP is required.
  Preserves an L1 APP for L2 in early-stop cases, but touches
  schedule/stopping semantics (needs its own frozen decision at the
  consumer/mode boundary), costs a sweep, still only an approximation
  (TREE 0.00689 after one sweep), and changes numerics versus historical runs.
- **C** — keep prior-only fallback but prohibit APP/conditioned claims.
  No behavior change, but unenforceable; the silent `prior @ P` path remains
  live. Rejected as a standalone fix.

Recommendation: **A**; B becomes a separately frozen decision only if a
specific consumer requires it. None of A/B/C is implemented in Phase P.

## 7. Acceptance tests for the future implementation

PV-01 it0 cold return carries `PRIOR_ONLY`; PV-02 post-sweep return carries
`CHECK_UPDATED`; PV-03 flooding first return is not `PRIOR_ONLY`; PV-04 warm
start without provenance is `WARM_START_UNSPECIFIED`; PV-05 existing
hard-decision results unchanged and the field additive; PV-06 APP-requiring
consumer fails closed on `PRIOR_ONLY`; PV-07 fails closed on `None`/absent/
unknown; PV-08 no L2 APP prior computed from a `PRIOR_ONLY` q (spy/assert);
PV-09 `CHECK_UPDATED` reproduces the existing `q @ P` result; PV-10 D7-B-style
diagnostics label it0 only `PRIOR_ONLY_CURRENT_BELIEF` and do not apply a
conditioned-posterior tolerance; PV-11 provenance propagates through D5
adapters/`_decode_block` and v72p2d3's dict path; PV-12 no retroactive change
to stored/historical values; PV-13 hard-decision-only consumers remain
unaffected; PV-14 import-graph independence between the interface rework and
the future D7-C oracle. Full text: OpenSpec `proposal.md`.
No implementation is written to satisfy these tests in this phase.

## 8. Gating and non-retroactivity rules

- No historical result is retroactively changed (D7-B R2 evidence/terminal/
  scope, D7-A, v45–v55, every stored artifact).
- Interface implementation is mandatory before the next sequential, alternating
  or joint cross-layer APP run, and **not** before D7-C single-layer oracle
  readiness/execution.
- D7-C's implementation must not import or depend on the future
  interface-rework implementation; D7-C records exact/syndrome/iterations and
  at most current-belief confidence, never cross-layer beliefs (ruling 8).
- D7-C may start T1 only after this proposal is frozen and the independent
  review below reaches the sole allowed PASS. No D7-C work is created here.

## 9. No-change statement and authorizations

Phase P performed documentation/OpenSpec work only. No production code, test,
script, source, or config file was changed; no decoder was called; no Model-F
binary content was read (names/metadata only, and none in this phase); no
`workspace/` root was created; no UUID was generated; no commit was made; no
`--phase`; no R1d/G1/G2/CAL/VAL/real/raw/VOID action. All authorization and
permission fields remain false.

## 10. Review placeholder and signature

- Independent review required:
  `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_REVIEW_R1.md`
  — status: **not yet created / pending**. The reviewer must verify this
  proposal against v35 and the complete D7-B consumer inventory, challenge
  whether D7-C truly avoids the defective interface, and confirm no production
  code/decoder/root change.
- Sole allowed PASS verdict: `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`.
- Main-thread signature (Phase P planning, all authorizations false):
  `____________________`
