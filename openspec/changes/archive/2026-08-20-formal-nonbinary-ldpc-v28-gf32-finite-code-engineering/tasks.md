# V28R Tasks — repair and independent acceptance

The historical V28 acceptance is superseded by independent review. `run_01`
remains unchanged and is invalid for V29.

Status: **V28R ACCEPTED / P102 [x]** — main-thread independent acceptance
recorded 2026-08-20. Canonical engineering evidence is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`;
the historical `run_01` and original V28 acceptance remain retained but are
`superseded_invalid_for_v29`. This change is engineering-only, not FER,
qualification, or promotion.

## A1 — OpenSpec supersession and freeze

Record the historical status, V28R scope, forbidden inputs, and exact
tag/matrix/sequential contracts.

- **Accept**: four documents consistently say no row-prefix and no alternate
  tag; T3 requires syndrome consistency, not the false uniqueness claim.
- **Status: [x]** — V28R documents and the canonical run manifest bind the
  repaired contracts; the historical acceptance is explicitly superseded.

## A2 — L1 topology

Build lexicographic 15 pairs repeated 68 times plus four tail pairs, with two
endpoint coefficients per variable.

- **Accept**: 6×1024, 2048 edges, column degree 2, row histogram
  `{341:4,342:2}`, 15 unique pairs, rank 6.
- **Status: [x]** — rebuilt and verified in `run_02_v28r/readonly_verify.json`
  (`ok=true`).

## A3 — independent L2 topology

Build one graph per source using the k=1..5 simple-circulant order and opposite
matching completion; never slice a mother matrix.

- **Accept**: 194/200/202×1024, 1024 unique pairs, 2048 edges, column degree 2,
  exact row histograms, and full source-specific ranks.
- **Status: [x]** — source-specific matrices and rank/degree contracts are
  recorded in the canonical evidence and independently rebuilt by the verifier.

## A4 — coefficient and API binding

Use `_coefficient(q, seed, variable_index, endpoint_slot)` with the frozen
seeds. `build_matrices` returns L1 plus the source mapping and `layer_matrix`
selects it.

- **Accept**: deterministic replay and manifest record call semantics;
  row-prefix input is rejected.
- **Status: [x]** — coefficient/topology/API bindings are persisted and covered
  by the focused V28R tests and read-only verifier.

## A5 — posterior decoder

Implement `decode_error_domain_posterior` by reusing V10 FFT-QSPA. Form the
error syndrome, reconstruct, and fail closed on syndrome inconsistency.

- **Accept**: `(n,32)` prior, noiseless recovery, invalid-prior/fail-closed
  test, and no new BP implementation.
- **Status: [x]** — posterior wrapper and fail-closed behavior passed the
  focused tests; verifier terminal is engineering-only.

## A6 — Bob-only sequential adapter

Call V26 L1 posterior centered by Bob `Y1`; after verified L1 success call V26
L2 posterior with returned `x1_hat`, centered by `Y2`; L1 failure makes L2
`not_run`.

- **Accept**: spy/fake adapter proves call order and exact predecessor value;
  no Alice truth appears in decoder path.
- **Status: [x]** — sequential spy/fake checks and canonical noiseless replay
  prove L2 receives the returned L1 estimate.

## A7 — synthetic evidence

Run deterministic noiseless and fixed controlled-error smoke on the additive
V28R run root. Controlled output is fail-closed-only.

- **Accept**: default frozen evidence calls empirical V26 adapter and records
  source/delay binding, leakage, tag, layer order, and no raw/holdout.
- **Status: [x]** — `run_02_v28r/gate.json` is
  `engineering_ready_for_retrospective_gate`; its verifier records
  `holdout_read=false` and `raw_ttbin_read=false`.

## A8 — independent verifier

Rebuild matrices from config; rerun structural checks and sequential noiseless
replay through a recording adapter.

- **Accept**: `readonly_verify.json` exists, `ok=true`, gate/manifest/evidence
  agree, and terminal is the sole ready state.
- **Status: [x]** — canonical `readonly_verify.json` is `ok=true` with no
  problems and matching recomputed/persisted terminal.

## A9 — tests and scope audit

Cover A2–A8 with synthetic/fake adapters; leave V27 tests green. Use
`pytest -p no:cacheprovider` and a writable test root.

- **Accept**: no changes under frozen `src/experiments/tools`, no holdout,
  pairs.parquet, raw ttbin, DE, FER, commit, archive, or push.
- **Status: [x]** — focused tests passed and the canonical evidence is limited
  to engineering smoke; no FER/qualification/promotion claim is made.

## A10 — handoff

Return changed files, commands/results, generated `run_02_v28r` evidence, and
any incomplete IDs. Main-thread review owns acceptance and later V29 freeze.
- **Status: [x]** — handoff delivered; main-thread independent acceptance and
  V29 freeze review are recorded separately.
