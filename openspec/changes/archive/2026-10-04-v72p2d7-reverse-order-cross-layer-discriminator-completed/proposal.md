# D7-F reverse-order cross-layer discriminator — proposal

> Status: freeze only (Phase B). Docs, no code, no execution, no
> authorization. All execution/promotion authorizations remain false.
> No D7-F root, no D7-F identifier. Predecessor D7-E acceptance is
> `D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`.

## What

Freeze a development-only, paired complete-two-layer discriminator (D7-F)
on the exact D7-E frozen identities. For every `(f, seed)` it executes two
ordered arms — `FORWARD_L1_TO_L2` (L1 marginal, then gated cold L2) and
`REVERSE_L2_TO_L1` (L2 marginal, then gated cold L1) — and compares
complete two-layer recovery (`both_layers_exact`) of the reverse candidate
against the forward reference, per f, without feedback or oracle truth.

## Why

- D7-E accepted scope
  (`D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`)
  shows useful transfer is direction-dependent and strongest in `L2_TO_L1`
  at `f=1.2` (control `3/16`, transfer `7/16`, four transfer-only, zero
  control-only, `STRONG_TRANSFER_LIFT`) under the frozen synthetic
  Model-F/decoder/matrix/seed contract — a directional diagnostic only,
  not a success, FER, leakage, or key-rate claim.
- The route ruling out of D7-E acceptance requires testing whether the
  directional lift survives as complete two-layer recovery when reversing
  the sequential order, without implementing a feedback cycle yet.
- Existing provenance proves a posterior consumed checks, but it does not
  expose cavity/extrinsic messages needed to prevent syndrome evidence
  from returning to its source layer; >2-stage alternating therefore stays
  blocked pending a cavity/extrinsic-message contract.

## Frozen scientific question (§3 of the task packet, verbatim in substance)

Question: on the exact D7-E frozen identities, does reverse order
`L2→L1` recover both layers exactly on more seeds than forward order
`L1→L2`, when each arm is a complete two-pass sequence (source marginal,
then one gated cold target decode from the transfer prior), without
oracle truth or feedback?

This tests only a paired order mechanism:

```text
FORWARD_L1_TO_L2:  decode L1 marginal
  -> gate finite/non-crash/shape-valid + provenance == CHECK_UPDATED
  -> transient P(U2|B,s1) -> one cold L2 decode
REVERSE_L2_TO_L1:  decode L2 marginal
  -> same gate
  -> transient P(U1|B,s2) -> one cold L1 decode
```

It does not claim calibrated posterior, alternating convergence, leakage,
protocol recovery or Bob-only FER.

## Scope (frozen B01–B07, detail in design.md / spec.md)

- Matrix B01: f `[1.0, 1.2]`; seeds `2026091300..2026091315` ascending
  (16/f); same corrected per-Bob-column estimator, accepted Model-F root,
  D7-C/D7-E block identity, H/mother prefixes, rows, GF32 poly 37, cold
  row-layered `max_iter=90` damping `1.0`; no oracle/flooding/CAL/VAL/
  real/raw/graph changes.
- Arms B02: per `(f,seed)` order `FORWARD_L1_TO_L2` then
  `REVERSE_L2_TO_L1`; gate = finite/non-crash/shape-valid + provenance
  exactly `CHECK_UPDATED`; source exact NOT a gate; ineligible second
  stage = blocked non-call, never replaced; no transfer back to source;
  max `32×4=128` calls.
- Accounting B03, evidence-use B04, paired labels B05, terminals B06,
  budgets/output B07: frozen in design.md and spec.md; §§5 B01–B07 of the
  task packet are frozen in substance there and in the cycle prereg/
  execution packet.
- Estimator identity hard contract: only
  `prepare_model_f_prior_candidate` / `build_f_model_concentration` with
  per-Bob-column smoothing; legacy per-cell `build_f_model(counts +
  lambda)` forbidden (static + behavioral negative tests required).
- Root contract: fresh direct child
  `workspace/d7_f_reverse_order_discriminator_<uuid>/`, exactly seven
  scalar text files (`manifest.json`, `decoder_records.csv`,
  `arm_pairs.csv`, `stratum_summary.csv`, `summary.json`, `report.md`,
  `command_log.txt`); no beliefs/priors/symbols/syndromes/vectors/digests
  persisted.
- Planned code paths (for the implementer, frozen names): module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py`,
  tests
  `comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py`,
  script `scripts/v72p2d7_gf32_reverse_order_discriminator.py`; reuse D7-E
  loaders/estimator/transfer/provenance/RSS/scalar/verifier conventions
  via narrow imports, no predecessor-module copies; lazy binding + DI
  required.

## Non-goals (frozen)

- No feedback loop, alternating BP, third decoder stage, joint factor
  graph, generalized turbo framework, warm start, forced extra sweep,
  tuning/search, or estimator change.
- No leakage/recovery/FER, reconciliation-efficiency, key-rate, CAL/VAL/
  real-data, qualification, promotion, R1d, G1/G2, or general
  GF32/NB-LDPC claim.
- No D7-F execution, identifier generation, result acceptance, or push
  under this change. Implementation, verifier, tests, and reviews are out
  of scope here; their frozen test plan and review tokens are recorded in
  the cycle prereg for a later gate.
- No modification of accepted D7-B/C/D/E roots, frozen baseline `src/`,
  `experiments/`, `tools/`; no overwrite of existing outputs.
