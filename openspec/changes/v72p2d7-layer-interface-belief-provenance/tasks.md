# Layer-interface belief provenance — tasks (future implementation; all deferred)

> Every task below is **not started / deferred — must precede any cross-layer
> APP route**. This change folder performs no implementation, calls no decoder,
> creates no root, and claims no execution. Authorization fields are false.
> Adopt alternative A first (see `design.md`); B is a separately frozen
> decision, C is rejected.

## Future implementation tasks (ordered, deferred)

- [ ] BP-01 — **Producer provenance (v35)** — not started / deferred. Add the
  additive defaulted `belief_provenance` field to `DecoderResult` and populate
  it at every return site: row-layered cold `iterations == 0` →
  `PRIOR_ONLY`; row-layered/flooding `iterations > 0` → `CHECK_UPDATED`;
  warm-seeded returns → `WARM_START_UNSPECIFIED`. Do not change hard-decision
  stopping or any existing field (ruling 1). Add PV-01–PV-05 tests; prove
  byte-identical hard-decision results on frozen fixtures.
- [ ] BP-02 — **D5 plumbing** — not started / deferred. Carry provenance
  through `_decode_block` and the three adapter dicts
  (`historical_g0_decoder`, `_bound_hist`, `bind_historical_decoder`) without
  changing existing dict keys; add PV-11 tests.
- [ ] BP-03 — **D5 fail-closed guard** — not started / deferred. Migrate
  `_run_layered_block` so a conditioned L2 APP prior is computed only from
  L1 returns with `CHECK_UPDATED` provenance; `PRIOR_ONLY` / `None` / unknown
  fails closed before `app_fed_l2_prior`. Add PV-06–PV-09 tests. This is the
  minimum mandatory consumer migration.
- [ ] BP-04 — **Remaining cross-layer APP consumers** — not started / deferred.
  Before any rerun as a cross-layer route, migrate or fail-close:
  `v72p2d3` recombination (L1351–1352), `nbldpc_shell_adapter.py:254`, and the
  historical v45–v55 paths if ever rerun; `scripts/execute_v64_fresh_verify.py:188`
  follows the same rule. Historical results are not recomputed.
- [ ] BP-05 — **Diagnostic labeling** — not started / deferred. Where a future
  diagnostic compares returned beliefs against an exact posterior (D7-B-style),
  record iteration-0/current beliefs only as `PRIOR_ONLY_CURRENT_BELIEF` and
  separate hard-decision success from belief calibration (E10). D7-B R2 remains
  immutable and is not rerun. Add PV-10 tests.
- [ ] BP-06 — **Warm-start provenance design** — not started / deferred, out of
  scope until a route needs warm starts; must not be guessed from `iterations`
  (ruling 7).
- [ ] BP-07 — **Independent implementation review and Pre-EXECUTE** —
  not started / deferred. Independent review of the migration against the
  frozen contract, then a separate Pre-EXECUTE before the first authorized
  cross-layer APP run (frozen command, budgets, no-overwrite, focused tests,
  authorization explicit). No execution is authorized by this change.
- [ ] BP-08 — **D7-C independence check** — not started / deferred. Import-graph
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
