# Alternating cross-layer discriminator — proposal (freeze only, Phase B)

> Status: freeze only. Docs, no code, no execution, no authorization.
> Operator authority:
> `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_TASK_PACKET.md`
> §§3–9 only. All execution/promotion authorizations remain false. Basis HEAD
> `46141fcc`. Predecessor D7-G acceptance:
> `D7_G_EXTRINSIC_CONTRACT_ACCEPTED_AWAITING_D7_H_PACKET_FREEZE`. Implementation
> and execution come later under separate authority; no decoder call, no
> Model-F/real read, no root/UUID, no R1d/`--phase`/G1/G2, no push.

## What

Freeze the smallest alternating cross-layer discriminator that can run on the
certified D7-G code-factor extrinsic contract. For each frozen synthetic
identity, one forward `L1→L2` code-extrinsic transfer is followed by one
backward `L2→L1` code-extrinsic transfer, each invoked only when the preceding
stage yields admissible `CHECK_EXTRINSIC`, and the candidate is compared on
the same seeds against the single-pass forward reference.

```text
STAGE 0  cold decode L1 marginal                          (only unconditional mandatory call)
STAGE 1  CHECK_EXTRINSIC(L1) -> P(U2|B,s1) -> cold decode L2   (invoked only if STAGE 0 passes; reference endpoint)
STAGE 2  CHECK_EXTRINSIC(L2) -> P(U1|B,s2) -> cold decode L1_return (invoked only if STAGE 1 passes; candidate endpoint)
```

Call accounting: 1 unconditional mandatory call per identity (STAGE 0; minimum
32 actual calls) plus up to 2 gated calls (STAGE 1 gated on STAGE 0, STAGE 2
gated on STAGE 1); maximum `32 × 3 = 96` decoder calls.

## Why

- D7-E (accepted) shows a direction-dependent single-pass transfer lift and
  blocks `>2-stage alternating pending a cavity/extrinsic-message contract`.
  D7-F (accepted) shows reversing a single sequential pass does not convert
  that lift into complete two-layer recovery.
- D7-G (accepted) now supplies the missing cavity/extrinsic contract, so the
  smallest alternating schedule is unblocked: exactly one forward then one
  backward code-extrinsic transfer. Two transfers is the minimum implied by
  the accepted contracts; no third transfer is preregistered.

## Frozen scientific scope (from packet §3)

- Packet freeze only.
- Cold start; one forward code-extrinsic transfer then one backward transfer.
- Posterior back-transfer explicitly forbidden.
- Iteration-0 and warm-start ambiguity fail closed.
- Code/graph/rows/estimator/damping/iterations/thresholds/schedule/seeds,
  terminal semantics, stop rules, and no-rerun/no-tuning rules are frozen
  before any future decoder call.
- D7-H ends `FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`.

## Frozen matrix (from packet §6, reused verbatim from D7-E/F)

- `f ∈ [1.0, 1.2]`; seeds `2026091300..2026091315`, 16 per `f`.
- `n=64`; L1 rows 49/59, L2 rows 43/52 (`f=1.0`/`f=1.2`); D5-native mothers
  `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start, `max_iter=90`, damping `1.0`.
- Estimator: only `prepare_model_f_prior_candidate` /
  `build_f_model_concentration` (per-column
  `(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`); legacy
  `build_f_model` forbidden.

## Frozen transfer + no-returned-evidence rule (from packet §7)

- Transfer message is only explicit `CHECK_EXTRINSIC`, transported through
  `require_check_extrinsic_for_transfer`; posterior-based transfer and
  reconstructed-prior subtraction are forbidden.
- Backward prior is a function of L2's code-factor extrinsic only; the forward
  stage's L1 evidence cannot be returned to L1 (cavity property).
- Each decode invocation consumes its designated syndrome once; L1 is decoded
  twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing code extrinsic
  removes its entire incoming prior, including STAGE 0's L1 evidence, before
  STAGE 2 consumes L1 syndrome again.
- Fail-closed on `NO_CHECK_EVIDENCE` (including iteration-0 hard/syndrome
  success) / `WARM_START_UNSPECIFIED` / `None`/missing/unknown / nonfinite /
  shape mismatch: blocked non-invocation; all downstream stages for that
  identity blocked; never synthesized, replaced, retried, or resumed. Source
  hard exact is not an eligibility gate.

## Frozen labels, terminal, budgets (from packet §8)

- Paired labels: `COVERAGE_BLOCKED`, `ALTERNATING_REGRESSION`,
  `STRONG_ALTERNATING_LIFT`, `WEAK_ALTERNATING_LIFT`, `NO_ALTERNATING_LIFT`.
- Terminal priority: `D7_H_PRE_EXECUTION_BLOCKED`,
  `D7_H_WATCHDOG_TIMEOUT_VOID`, `D7_H_NONFINITE_OR_CRASH_BLOCKED`,
  `D7_H_RESOURCE_OVERRUN`, `D7_H_INCOMPLETE_MATRIX_BLOCKED`,
  `D7_H_PROVENANCE_COVERAGE_BLOCKED`, `D7_H_ALTERNATING_STRONG_LIFT`,
  `D7_H_ALTERNATING_WEAK_LIFT`, `D7_H_ALTERNATING_REGRESSION`,
  `D7_H_NO_USEFUL_ALTERNATING_LIFT`.
- Budgets: 1 unconditional mandatory call per identity plus up to 2 gated
  calls; hard cap `32 × 3 = 96` decoder calls (minimum 32); watchdog 120 s;
  stored wall <=1500 s;
  outer `timeout -k 30 1800`; VmHWM `< 2 GiB`; one fresh root; seven scalar
  files plus an independent read-only verifier.

## Exact future command (frozen, NOT run)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_alternating_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_h_alternating_discriminator_<uuid>
```

## Non-goals (frozen)

- No implementation, tests, runner, decoder call, root, UUID, or result in
  this change.
- No D7-H execution authorization; no promotion.
- No modification of accepted D7-B/C/D/E/F/G roots or the frozen baseline
  `src/`, `experiments/`, `tools/`; no overwrite of existing outputs.
- No `>2-stage` alternating; no posterior back-transfer; no tolerance
  loosening or renaming.

## Acceptance tests for the future implementation (IDs stable; detail in design.md)

- ALT-01 schedule/order and 96-call cap; blocked STAGE 1/STAGE 2
  non-invocations with downstream cascade.
- ALT-02 `CHECK_EXTRINSIC`-only transfer; helper rejection matrix; no
  posterior fallback.
- ALT-03 cavity/no-returned-evidence: forward L1 evidence excluded from the
  backward prior; returned prior invariant to the removed STAGE 0
  incoming-message component while sensitive to STAGE 1's own check evidence;
  iteration-0 no false lift; warm rejection; posterior back-transfer
  double-count is never reached.
- ALT-04 both-layer AND rules and per-invocation designated-syndrome
  accounting; paired-label boundaries and terminal priority.
- ALT-05 scalar-only seven-file writer, no-overwrite refusal, verifier
  tamper cases.
- ALT-06 compatibility: existing D7-E/F/G outputs and frozen roots untouched;
  current consumers retain prior behavior; no D7-H root/UUID exists.

## Gating rules (frozen)

- This freeze precedes any D7-H implementation.
- If the accepted D7-G contract cannot uniquely determine the minimal
  schedule, STOP; do not invent one.
- Neither this freeze nor any future review authorizes D7-H execution.
