# D7-E provenance-safe cross-layer discriminator — proposal

> Status: freeze only (Track B R14). Docs, no code, no execution, no
> authorization. All execution/promotion authorizations remain false.
> No D7-E root, no D7-E identifier. Predecessor D7-D acceptance is
> `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`.

## What

Freeze a development-only, single-pass, two-direction cross-layer transfer
discriminator (D7-E) on the exact D7-C frozen identities. It tests whether
one provenance-valid single-pass source-layer BP belief recovers a useful
fraction of D7-C's oracle ceiling on the target layer, in either direction,
without oracle truth or feedback.

## Why

- D7-C accepted scope (`D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`)
  shows true other-layer symbols materially improve recovery under the frozen
  priors, matrices, decoder, disclosures, n=64 and 16 paired blocks — a
  contextual ceiling only, not a bootstrap claim.
- D7-D accepted scope (`D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`)
  establishes no preregistered flooding advantage; D7-E therefore uses
  row-layered decoding only and carries no schedule comparison.
- The accepted BP Alternative A contract gates every cross-layer APP input:
  `PRIOR_ONLY`, missing/`None`/unknown and `WARM_START_UNSPECIFIED` cannot
  feed a conditioned cross-layer APP; only `CHECK_UPDATED` may do so.
- D7-E is the next mainline Track B step: a mechanism discriminator, not
  alternating/joint BP, not a sweep, not a performance estimate.

## Frozen scientific question (§3, verbatim in substance)

Question: on the exact D7-C frozen identities, can one provenance-valid
single-pass source-layer BP belief improve target-layer exact recovery over
the target marginal control, in either direction, without oracle truth or
feedback?

This tests only a one-pass mechanism:

```text
source marginal decode
  -> require belief_provenance == CHECK_UPDATED
  -> softmax(current log belief) as BP APP approximation
  -> combine with accepted joint Model-F conditional for the target
  -> one cold target decode
```

It does not claim calibrated posterior, alternating convergence, leakage,
protocol recovery or Bob-only FER.

## Scope (frozen R08–R13, detail in design.md / spec.md)

- Matrix R08: f `[1.0, 1.2]`; seeds `2026091300..2026091315` ascending
  (16/f); same blocks/graph seeds/rows/mothers/estimator as D7-C/D7-D;
  row-layered only GF(32) poly 37 cold `max_iter=90` damping `1.0`;
  directions `[L1_TO_L2, L2_TO_L1]`; no flooding; no oracle decoder calls
  (D7-C tables are contextual ceiling only); per-`(f,seed)` slot order
  `L1_TO_L2_SOURCE_L1_MARGINAL`, `L1_TO_L2_TARGET_L2_CONTROL_MARGINAL`,
  `L1_TO_L2_TARGET_L2_TRANSFER` (only if source CHECK_UPDATED),
  `L2_TO_L1_SOURCE_L2_MARGINAL`, `L2_TO_L1_TARGET_L1_CONTROL_MARGINAL`,
  `L2_TO_L1_TARGET_L1_TRANSFER` (only if source CHECK_UPDATED);
  192 slots = 128 mandatory + at most 64 eligible transfers; blocked =
  recorded non-invocation, never replacement/retry/fake.
- Formulas R09, eligibility R10, labels R11, terminal R12, budgets R13:
  frozen in design.md and spec.md; §§3–5 of the task packet are frozen in
  substance there and in the cycle prereg/execution packet.
- Estimator identity hard contract: only
  `prepare_model_f_prior_candidate` / `build_f_model_concentration` with
  per-Bob-column smoothing; legacy per-cell `build_f_model(counts + lambda)`
  forbidden (static + behavioral negative tests required).
- Root contract: fresh direct child
  `workspace/d7_e_cross_layer_discriminator_<uuid>/`, exactly seven scalar
  text files (`manifest.json`, `decoder_records.csv`, `transfer_pairs.csv`,
  `stratum_summary.csv`, `summary.json`, `report.md`, `command_log.txt`);
  no beliefs/priors/symbols/syndromes/vectors/digests persisted.

## Non-goals (frozen)

- No calibrated posterior, alternating/joint BP, feedback loop, joint factor
  graph, warm-start mechanism, forced extra sweep, tuning/search, or
  estimator change.
- No leakage/recovery/FER, reconciliation-efficiency, key-rate, CAL/real-data,
  qualification, promotion, R1d, G1/G2, or general GF32/NB-LDPC claim.
- No D7-E execution, identifier generation, result acceptance, or push under
  this change. R15–R19 (implementation, verifier, tests, reviews) are out of
  scope here; their frozen test plan (R17) and review tokens (R18/R19) are
  recorded in the cycle prereg for a later gate.
- No modification of accepted result roots, frozen baseline `src/`,
  `experiments/`, `tools/`; no overwrite of existing outputs.
