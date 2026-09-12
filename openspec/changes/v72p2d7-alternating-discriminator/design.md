# Alternating cross-layer discriminator — design (freeze only, Phase B)

> Status: design freeze. No code, no decoder call, no root, no execution.
> All authorizations false. Predecessor D7-G acceptance:
> `D7_G_EXTRINSIC_CONTRACT_ACCEPTED_AWAITING_D7_H_PACKET_FREEZE`. Conventions
> mirror the D7-E/F discriminators and the D7-G extrinsic contract.

## Frozen schedule

Per `(f, seed)`, up to three decoder calls: STAGE 0 is the only unconditional
mandatory call; STAGE 1 is gated on STAGE 0's admissible `CHECK_EXTRINSIC` and
STAGE 2 on STAGE 1's:

```text
STAGE 0  SOURCE_L1_MARGINAL   (only unconditional mandatory call; shared)
  cold row-layered decode of L1 from its own channel marginal
  gate: extrinsic_provenance == CHECK_EXTRINSIC
  NO_CHECK_EVIDENCE (including iteration-0 hard/syndrome success) /
  WARM_START_UNSPECIFIED / None/missing/unknown / nonfinite / shape mismatch
  => blocked non-invocation; all downstream stages for that identity blocked,
  never synthesized, replaced, retried, or resumed; source hard exact is not
  an eligibility gate

STAGE 1  FORWARD_L1_TO_L2     (gated on STAGE 0; reference endpoint)
  invoked only if STAGE 0 yields finite, shape-valid, non-crashed, exact CHECK_EXTRINSIC
  q1_ext = softmax(extrinsic_log_beliefs of STAGE 0)
  P_transfer(U2|B,s1) = sum_u1 q1_ext(u1|B,s1) P(U2|B,u1)
  cold row-layered decode of L2 from P_transfer(U2|B,s1)
  reference both_layers_exact = L1_exact AND L2_exact

STAGE 2  BACKWARD_L2_TO_L1    (gated on STAGE 1; candidate endpoint)
  invoked only if STAGE 1 yields finite, shape-valid, non-crashed, exact CHECK_EXTRINSIC
  gate: L2 extrinsic_provenance == CHECK_EXTRINSIC
  q2_ext = softmax(extrinsic_log_beliefs of STAGE 1)
  P_transfer(U1|B,s2) = sum_u2 q2_ext(u2|B,s2) P(U1|B,u2)
  cold row-layered decode of L1_return from P_transfer(U1|B,s2)
  candidate both_layers_exact = L2_exact AND L1_return_exact
```

- Minimality: D7-E prereg §9 and D7-F prereg §2/B04 block `>2-stage
  alternating pending a cavity/extrinsic-message contract`. D7-G supplies it,
  so two transfers is the smallest unblocked schedule. No third transfer is
  preregistered.
- `candidate_only` = candidate both-exact and reference not; `reference_only`
  = reference both-exact and candidate not; `both`; `neither`.
- Call accounting: 1 unconditional mandatory call per identity (STAGE 0;
  minimum 32 actual calls) plus up to 2 gated calls (STAGE 1 gated on STAGE 0,
  STAGE 2 gated on STAGE 1); maximum `32 × 3 = 96` decoder calls. A blocked
  stage is a recorded non-invocation, never a replacement, retry, or
  fabricated result, and it blocks all downstream stages for that identity.

## Frozen transfer message (certified D7-G contract)

- Admissible transfer message is only the explicit `CHECK_EXTRINSIC`
  code-factor extrinsic `L_code_ext = L_post − log(p_in)`, stored row-
  normalized by log-sum-exp, transported by stable softmax.
- Transport goes through the narrow helper `require_check_extrinsic_for_transfer`;
  posterior `softmax(final_beliefs)` is never a transfer message, and no
  consumer reconstructs a prior by subtracting an unknown/reconstructed value.
- Fail-closed: `NO_CHECK_EVIDENCE` (including iteration-0 hard/syndrome
  success), `WARM_START_UNSPECIFIED`, `None`/missing/unknown provenance,
  nonfinite, or shape mismatch produce a blocked non-invocation before any
  cross-layer prior is computed; all downstream stages for that identity are
  blocked, never synthesized, replaced, retried, or resumed. Source hard exact
  is not an eligibility gate.

## Cavity / no-returned-evidence rule (decisive)

- The backward prior is a function of L2's code-factor extrinsic only, never
  L2's posterior, so the forward stage's L1 incoming evidence is excluded from
  the message returned to L1.
- Each decode invocation consumes its designated syndrome once: L1 is decoded
  twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing code extrinsic
  removes its entire incoming prior, including STAGE 0's L1 evidence, before
  STAGE 2 consumes L1 syndrome again. No target posterior is fed back,
  blended, multiplied, or reused.
- Required demonstrations: (a) forward-stage L1 evidence excluded from the
  backward prior; (b) iteration-0 neutral extrinsic cannot create a false
  lift; (c) warm/unknown provenance rejected; (d) a posterior-based
  back-transfer double-count is never reached; (e) the returned prior is
  invariant to the removed STAGE 0 incoming-message component while remaining
  sensitive to STAGE 1's own check evidence.

## Frozen matrix, decoder, estimator

- `f ∈ [1.0, 1.2]`; seeds `2026091300..2026091315` (16 per `f`); `n=64`.
- L1 rows 49/59, L2 rows 43/52 (`f=1.0`/`f=1.2`); D5-native mothers
  `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start, `max_iter=90`, damping `1.0`.
- Estimator identity is a hard pre-execution contract: the joint is obtained
  only through `prepare_model_f_prior_candidate` / `build_f_model_concentration`
  (per-Bob-column `(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`); the
  historical per-cell `counts + lambda` builder is forbidden and must be
  statically and behaviorally unreachable.

## Root contract and seven-file schema

Future root `workspace/d7_h_alternating_discriminator_<uuid>/`: fresh, no
overwrite, no subdirectories, exactly seven compact scalar text files:
`manifest.json`, `decoder_records.csv`, `arm_pairs.csv`, `stratum_summary.csv`,
`summary.json`, `report.md`, `command_log.txt`.

- `decoder_records.csv`: STAGE 0 rows for all identities plus only invoked
  eligible STAGE 1/STAGE 2 rows; blocked stages are non-invocations recorded
  elsewhere.
- `arm_pairs.csv`: one row per reference/candidate pair per `(f,seed)` with
  shared-identity pins, per-stage eligibility/provenance, L1/L2/L1_return
  exact/syndrome separately, and both `*_both_layers_exact`.
- `stratum_summary.csv`: 2 rows (one per `f`) with one complete-chain coverage
  count, explicit blocked-at-stage1/blocked-at-stage2 counts,
  `candidate_only`/`reference_only`/`both`/`neither`, `stratum_label`.
- Writer/verifier split: the verifier reads only the seven files and
  independently recomputes stage order, the unconditional STAGE 0 count (=32),
  the invoked STAGE 1 and STAGE 2 counts, uniqueness, no replacement, pair
  identity, the `CHECK_EXTRINSIC` gate, exact/syndrome isolation, both-layer
  AND rules, per-invocation designated-syndrome accounting, the
  no-returned-evidence rule, labels, terminal, wall/RSS and schema; it never
  calls a decoder and never loads Model-F.
- Persist no beliefs, priors, symbols, syndromes, block vectors, or extrinsic
  arrays; all `belief_*`/`extrinsic_*`-style fields, if any, are scalars only.

## Frozen implementation file map (names fixed for the later implementer)

- Module:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_alternating_discriminator.py`.
- Tests:
  `comparison_bench/tests/test_v72p2d7_gf32_alternating_discriminator.py`.
- Script: `scripts/v72p2d7_gf32_alternating_discriminator.py`.
- Reuse D7-E/F loaders, estimator, provenance, RSS, scalar-writer and verifier
  conventions via narrow imports (no predecessor copies); consume D7-G
  `extrinsic_log_beliefs` / `extrinsic_provenance` and
  `require_check_extrinsic_for_transfer`. Lazy binding + DI required.

## Alternatives (decision frozen)

| Alt | Verdict |
|---|---|
| Posterior-based transfer (`softmax(final_beliefs)`) | Rejected: D7-G forbids it; passes no cavity property |
| Reconstruct prior by subtracting an unknown/cleaned prior | Rejected: D7-G forbids it |
| Run `>2-stage` / iterate to convergence | Blocked: no accepted contract implies more than two transfers |
| Compare alternating against exact MAP/oracle | Forbidden: discriminator is paired vs single-pass reference only |
| Persist extrinsic/belief arrays in the evidence root | Rejected: no-persistence rule |

## Implementation outline (not started here)

Ordered tasks live in `tasks.md`. This design fixes semantics, fixtures,
budgets, terminals, and file paths only.
