# Layer-interface belief provenance — tasks (activated for implementation (Delta R1))

> Activated by the D7-D/BP interface-readiness R1 packet §4 A09–A10 after D7-D
> bounded acceptance `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`
> (commit `ffb4e909`). Adopt alternative A; B is a separately frozen future
> scientific decision, C is rejected.
> **All BP-01…BP-08 checkboxes below remain unchecked.** Completion is marked
> only at the packet's closeout gate A19, after the independent implementation
> (A17) and readiness (A18) reviews PASS. No BP item is complete as of this
> delta.
> The **PV-01–PV-14 acceptance matrix in `proposal.md` (~L243–274) is
> authoritative for tests**; this file references it rather than restating it.
> Authorization fields remain false; this folder performs no implementation,
> calls no decoder, and creates no root.

## Delta R1 implementation subset (packet §5 mapping)

- **BP-01 (A11) — producer mapping.** Add the additive defaulted
  `belief_provenance` field and populate every v35 return site: cold
  row-layered `iterations == 0` → `PRIOR_ONLY`; row-layered after ≥1 completed
  sweep and flooding returns → `CHECK_UPDATED`; any warm-seeded return without
  explicit carried provenance → `WARM_START_UNSPECIFIED` (never inferred from
  `iterations`). No change to `x_hat`, syndrome, iterations, status, beliefs,
  stopping, damping, normalization, or the numerical recurrence.
- **BP-02 / BP-03 (A12) — plumbing and fail-closed boundary.** Carry
  provenance through D5 `_decode_block` and all three adapter dicts without
  removing or renaming keys. `_run_layered_block` may call `app_fed_l2_prior`
  only when L1 provenance is exactly `CHECK_UPDATED`; `PRIOR_ONLY`, missing,
  `None`, unknown and `WARM_START_UNSPECIFIED` raise a specific fail-closed
  error before L2 prior construction or L2 decode.
- **BP-04 (A13) — remaining consumers.** Migrate the live/likely reusable
  cross-layer boundaries: `v72p2d3_gf32_contrast.py` recombination,
  `methods/nbldpc_shell_adapter.py` cross-layer boundary, and the V64 runner
  `scripts/execute_v64_fresh_verify.py`. Historical v45–v55 modules receive the
  smallest scientifically honest treatment: additive propagation/guard where
  localized, otherwise a direct fail-closed guard at their cross-layer entry —
  each must either carry the same fail-closed guard before any future execution
  or be explicitly blocked at that entry. They are **not rerun here**, and no
  historical output is recomputed or reinterpreted.
- **BP-05 (A14) — labeling.** Future diagnostics label iteration-zero belief
  comparisons `PRIOR_ONLY_CURRENT_BELIEF`; hard-decision success and belief
  calibration stay separate (E10). D7-B R2 remains immutable and is not rerun.
- **BP-06 — warm-start boundary (frozen non-implementation).** No forced sweep
  or warm-start propagation is implemented. `WARM_START_UNSPECIFIED` is
  preserved as the runtime refusal token for conditioned cross-layer APP; the
  closeout marker for this non-implementation boundary is
  `WARM_START_DEFERRED`. Provenance is never inferred from `iterations`.
- **BP-07 — independent review and future Pre-EXECUTE.** Independent review of
  the migration against this frozen contract, then a separate Pre-EXECUTE
  before the first authorized cross-layer APP run. No execution is authorized
  by this change.
- **BP-08 — D7-C import-graph independence.** The interface-rework
  implementation and the D7-C oracle implementation share no import dependency
  in either direction (PV-14).

## Behavioral-edit allowlist (A10)

Behavioral edits are limited to the minimum files required by BP-01–BP-05 and
their directly corresponding tests, selected from:

- `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`
- `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`
- historical v45–v55 cross-layer consumer modules named in the accepted
  proposal (additive provenance propagation / fail-closed guards only)
- `scripts/execute_v64_fresh_verify.py`
- directly corresponding tests under `comparison_bench/tests/`

Excluded (must not be touched): frozen `src/`, `experiments/`, `tools/`, the
sibling `nonbinary_v10_fftqspa.py`, D7-A/C/D scientific logic, and all evidence
roots.

## Implementation tasks (activated Delta R1; ordered; not complete)

- [ ] BP-01 — **Producer provenance (v35)** — activated (Delta R1) / not complete. Add the
  additive defaulted `belief_provenance` field to `DecoderResult` and populate
  it at every return site: row-layered cold `iterations == 0` →
  `PRIOR_ONLY`; row-layered/flooding `iterations > 0` → `CHECK_UPDATED`;
  warm-seeded returns → `WARM_START_UNSPECIFIED`. Do not change hard-decision
  stopping or any existing field (ruling 1). Add PV-01–PV-05 tests; prove
  byte-identical hard-decision results on frozen fixtures.
- [ ] BP-02 — **D5 plumbing** — activated (Delta R1) / not complete. Carry provenance
  through `_decode_block` and the three adapter dicts
  (`historical_g0_decoder`, `_bound_hist`, `bind_historical_decoder`) without
  changing existing dict keys; add PV-11 tests.
- [ ] BP-03 — **D5 fail-closed guard** — activated (Delta R1) / not complete. Migrate
  `_run_layered_block` so a conditioned L2 APP prior is computed only from
  L1 returns with `CHECK_UPDATED` provenance; `PRIOR_ONLY` / `None` / unknown
  fails closed before `app_fed_l2_prior`. Add PV-06–PV-09 tests. This is the
  minimum mandatory consumer migration.
- [ ] BP-04 — **Remaining cross-layer APP consumers** — activated (Delta R1) / not complete.
  Before any rerun as a cross-layer route, migrate or fail-close:
  `v72p2d3` recombination (L1351–1352), `nbldpc_shell_adapter.py:254`, and the
  historical v45–v55 paths if ever rerun; `scripts/execute_v64_fresh_verify.py:188`
  follows the same rule. Historical results are not recomputed.
- [ ] BP-05 — **Diagnostic labeling** — activated (Delta R1) / not complete. Where a future
  diagnostic compares returned beliefs against an exact posterior (D7-B-style),
  record iteration-0/current beliefs only as `PRIOR_ONLY_CURRENT_BELIEF` and
  separate hard-decision success from belief calibration (E10). D7-B R2 remains
  immutable and is not rerun. Add PV-10 tests.
- [ ] BP-06 — **Warm-start provenance design** — activated (Delta R1) / not
  complete, out of scope until a route needs warm starts; must not be guessed
  from `iterations` (ruling 7). Frozen non-implementation boundary; closeout
  marker `WARM_START_DEFERRED`.
- [ ] BP-07 — **Independent implementation review and Pre-EXECUTE** —
  activated (Delta R1) / not complete. Independent review of the migration against the
  frozen contract, then a separate Pre-EXECUTE before the first authorized
  cross-layer APP run (frozen command, budgets, no-overwrite, focused tests,
  authorization explicit). No execution is authorized by this change.
- [ ] BP-08 — **D7-C independence check** — activated (Delta R1) / not complete. Import-graph
  test (PV-14): the future interface-rework implementation and the D7-C oracle
  implementation share no dependency; D7-C never feeds returned beliefs
  cross-layer.

## Non-goals (do not implement here)

- No v35 hard-decision stopping change (ruling 1).
- No forced extra sweep (alternative B) without a separate frozen decision.
- No change to `oracle_l2_prior` or to the sibling
  `nonbinary_v10_fftqspa.py` probability-domain contract.
- No retroactive restatement of D7-B R2, D7-A, or v45–v55 results.
- No D7-C OpenSpec or implementation work in this change.
