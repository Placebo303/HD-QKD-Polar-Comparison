# D7-H alternating cross-layer discriminator preregistration R1 (frozen before any implementation, root, or decoder observation)

> R1A1 revision (authority: `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md` §2): STAGE 0 is the only unconditionally mandatory call; STAGE 1/STAGE 2 are gated with downstream-cascade blocking; coverage counts complete three-stage chains; per-invocation designated-syndrome accounting is adopted; the R1A1 packet authorizes the corrected freeze commit only — implementation and execution remain unauthorized.

- Branch `formal-ir-v72p1-addendum-clean`; basis HEAD `46141fcc`. Provenance
  only; no remote-equality requirement.
- Packet binding:
  `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_TASK_PACKET.md`
  (R1) §§3–9. This prereg is the D7-H freeze. R1 binds fully.
- Status: `FROZEN_PREREG_R1` and `NOT_AUTHORIZED_NOT_EXECUTED`.
  **Observation ordering:** this prereg and its OpenSpec change exist before
  any D7-H implementation, decoder observation, root, or certification
  number. No D7-H decoder call, no Model-F binary content read, no output
  root, and no D7-H identifier exist at freeze time.
- Predecessor facts (immutable): D7-G accepted scope
  `D7_G_EXTRINSIC_CONTRACT_ACCEPTED_AWAITING_D7_H_PACKET_FREEZE` — the
  code-factor extrinsic contract is certified as interface/certification only
  (`D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS` +
  `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS`); the explicit per-row message
  `L_code_ext = L_post − log(p_in)`, stored row-normalized by log-sum-exp, is
  transported by stable softmax; the extrinsic-provenance namespace is
  `NO_CHECK_EVIDENCE` / `CHECK_EXTRINSIC` / `WARM_START_UNSPECIFIED`; the
  narrow helper `require_check_extrinsic_for_transfer` accepts only explicit
  finite shape-correct `CHECK_EXTRINSIC` and is unwired from D5/D6/D7
  production. Accepted D7-E facts
  (`D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`) and
  D7-F facts
  (`D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`) are reused
  context only. BP Alternative A remains the current interface contract
  (`PRIOR_ONLY` / `CHECK_UPDATED` / `WARM_START_UNSPECIFIED`). The D7-E, D7-F
  and D7-G roots are immutable. All authorization false. No
  `workspace/d7_h_alternating_discriminator_*` root exists.
- D7-H never constructs an oracle prior and never calls an oracle decoder.
  Accepted D7-C tables are a contextual ceiling only.

## 1. Frozen scientific question (packet §3 in substance)

Question: on the exact D7-E/F frozen identities, does a minimal two-transfer
alternating sequence — one forward `L1→L2` code-extrinsic transfer, then one
backward `L2→L1` code-extrinsic transfer, both consuming only the certified
explicit `CHECK_EXTRINSIC` message — recover both layers exactly on more seeds
than the single-pass forward reference, without returning a layer's incoming
evidence to itself and without oracle truth or feedback?

This tests only a two-transfer alternating mechanism:

```text
STAGE 0  cold decode L1 marginal                         (only unconditional mandatory call)
  -> require extrinsic_provenance == CHECK_EXTRINSIC (gate)
STAGE 1  q1_ext = softmax(CHECK_EXTRINSIC of L1)         (invoked only if STAGE 0 gate passes)
  -> P_transfer(U2|B,s1) = sum_u1 q1_ext(u1|B,s1) P(U2|B,u1)
  -> cold decode L2                                      (reference endpoint)
STAGE 2  q2_ext = softmax(CHECK_EXTRINSIC of L2)         (invoked only if STAGE 1 gate passes)
  -> P_transfer(U1|B,s2) = sum_u2 q2_ext(u2|B,s2) P(U1|B,u2)
  -> cold decode L1_return                               (candidate endpoint)
```

It does not claim calibrated posterior, alternating convergence, leakage,
protocol recovery, or Bob-only FER.

## 2. Frozen schedule and why it is minimal (packet §4)

- D7-E (accepted) invokes exactly one transfer per arm and its prereg §9
  states `>2-stage alternating stays blocked pending a cavity/extrinsic-
  message contract capable of excluding returned syndrome evidence`; D7-F
  prereg §2/B04 restates the same block.
- D7-G (accepted) supplies that contract. Therefore the smallest alternating
  schedule that is no longer blocked is exactly two transfers: forward
  `L1→L2`, then backward `L2→L1`. No third transfer is implied by any accepted
  contract; the frozen candidate stops after the single return decode.
- `candidate_only` = candidate both-exact and reference not; `reference_only`
  = reference both-exact and candidate not. Reference
  `both_layers_exact = L1_exact AND L2_exact`; candidate
  `both_layers_exact = L2_exact AND L1_return_exact`.

## 3. Frozen matrix, decoder, estimator (packet §6)

- `f` order `[1.0, 1.2]`; seeds `2026091300..2026091315`, ascending, exactly
  16 per `f`.
- `n=64`; L1 rows 49 (`f=1.0`) / 59 (`f=1.2`); L2 rows 43 (`f=1.0`) / 52
  (`f=1.2`); D5-native mothers
  `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start, `max_iter=90`, damping `1.0`.
- No flooding, no oracle, no CAL/VAL, no real/raw, no graph/mother change.
- Estimator identity is a hard pre-execution contract: the joint is obtained
  only through `prepare_model_f_prior_candidate` / `build_f_model_concentration`
  (per-Bob-column `(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`); the
  historical `build_f_model` `counts + lambda` per-cell rule is forbidden and
  must be statically and behaviorally unreachable.

## 4. Frozen transfer message and no-returned-evidence rule (packet §7)

- The only admissible cross-layer transfer message is the explicit
  `CHECK_EXTRINSIC` code-factor extrinsic, transported through
  `require_check_extrinsic_for_transfer`. Posterior `softmax(final_beliefs)`
  may not be a transfer message; no consumer may reconstruct a prior by
  subtracting an unknown/reconstructed value.
- The backward prior is a function of L2's code-factor extrinsic only, never
  L2's posterior, so the forward stage's L1 incoming evidence cannot be
  returned to L1 (cavity property). Posterior back-transfer is explicitly
  forbidden.
- Each decode invocation consumes its designated syndrome once; L1 is decoded
  twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing code extrinsic
  removes its entire incoming prior, including STAGE 0's L1 evidence, before
  STAGE 2 consumes L1 syndrome again.
- `NO_CHECK_EVIDENCE` (including iteration-0 hard/syndrome success),
  `WARM_START_UNSPECIFIED`, `None`/missing/unknown, nonfinite, or
  shape-mismatched extrinsic are fail-closed blocked non-invocations; all
  downstream stages for that identity are blocked, never synthesized,
  replaced, retried, or resumed. Source hard exact is not an eligibility gate.
- Tests must prove: (a) forward-stage L1 evidence is excluded from the
  backward prior; (b) iteration-0 neutral extrinsic cannot create a false
  lift; (c) warm/unknown provenance is rejected; (d) a posterior-based
  back-transfer would double-count and is never reached; (e) the returned
  prior is invariant to the removed STAGE 0 incoming-message component while
  remaining sensitive to STAGE 1's own check evidence.

## 5. Frozen labels, terminal, budgets (packet §8)

- Paired labels per `f` (first match): `COVERAGE_BLOCKED` (fewer than 12/16
  identities with a complete chain — all three stages invoked and
  finite/shape-valid; one complete-chain coverage count plus explicit
  blocked-at-stage1/blocked-at-stage2 counts are recorded);
  `ALTERNATING_REGRESSION` (`reference_only >= 2`
  and `candidate_only == 0`); `STRONG_ALTERNATING_LIFT` (`candidate_only >= 4`
  and `reference_only == 0`); `WEAK_ALTERNATING_LIFT`
  (`candidate_only > reference_only`, strong not met); `NO_ALTERNATING_LIFT`
  otherwise. Synthetic diagnostic labels, not FER thresholds.
- Run terminal priority (first applicable): `D7_H_PRE_EXECUTION_BLOCKED`;
  `D7_H_WATCHDOG_TIMEOUT_VOID`; `D7_H_NONFINITE_OR_CRASH_BLOCKED`;
  `D7_H_RESOURCE_OVERRUN`; `D7_H_INCOMPLETE_MATRIX_BLOCKED`;
  `D7_H_PROVENANCE_COVERAGE_BLOCKED`; `D7_H_ALTERNATING_STRONG_LIFT`;
  `D7_H_ALTERNATING_WEAK_LIFT`; `D7_H_ALTERNATING_REGRESSION`;
  `D7_H_NO_USEFUL_ALTERNATING_LIFT`. No automatic successor is encoded.
- Budgets: 1 unconditional mandatory call per identity (STAGE 0; minimum 32
  actual calls) plus up to 2 gated calls; hard cap 96 decoder calls; sequential
  only; no concurrency/retry/rerun/resume; per-call watchdog 120 s; stored
  scientific wall <=1500 s;
  outer GNU `timeout -k 30 1800`; `.venv/bin/python` only; Linux/WSL peak RSS
  from `/proc/self/status` VmHWM (kB, `< 2 GiB`, fail-closed); one fresh
  identifier; fresh direct-child root
  `workspace/d7_h_alternating_discriminator_<uuid>/` with no overwrite and no
  subdirectories; exactly seven scalar text files plus an independent
  read-only verifier.

## 6. Exact future WSL command (frozen, NOT run in this task)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_alternating_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_h_alternating_discriminator_<uuid>
```

- Status `NOT_AUTHORIZED`: frozen but unauthorized and not executed; no
  identifier generated here.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_H_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read, or root
  creation. `--out-root` must be a fresh direct child of `workspace/` named
  `d7_h_alternating_discriminator_<uuid>`; the writer refuses overwrite and
  refuses subdirectories. Operational precondition: cwd is the repository
  root and `.venv/bin/python` imports the project dependencies; do not use
  bare `python`/`python3`, add `PYTHONPATH`, or alter child argv.

## 7. Frozen implementation file map (names fixed here for the later implementer)

- Module:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_alternating_discriminator.py`.
- Tests:
  `comparison_bench/tests/test_v72p2d7_gf32_alternating_discriminator.py`.
- Script: `scripts/v72p2d7_gf32_alternating_discriminator.py`.
- Reuse D7-E/F loaders, estimator, provenance, RSS, scalar-writer and verifier
  conventions via narrow imports (no predecessor-module copies); consume the
  D7-G `extrinsic_log_beliefs` / `extrinsic_provenance` fields and the
  `require_check_extrinsic_for_transfer` helper. Lazy binding + DI required.

## 8. Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/cycle_state.yaml`
  holds all execution authorization and promotion fields false
  (`decoder_executed: false`, `result_created: false`); attempts zero; no
  identifier, no root.
- The future implementer/runner works only from the frozen file map above and
  refuses before any work, Model-F read, decoder bind, or root creation while
  the key is false. A future verbatim user authorization flips the key for
  exactly one identifier and is consumed on the first decoder attempt
  regardless of outcome; no retry, rerun, resume, or reuse. Import, `--help`,
  `--dry-run`, and unauthorized runs bind no decoder, read no Model-F, and
  create no root.
- Explicit future authorization is required for implementation and for
  execution; none is granted by this prereg.

## 9. Nonclaim boundaries

Alternating classifications are route discriminators, not FER estimates. No
result of D7-H may be described as protocol recovery, leakage,
reconciliation-efficiency, key-rate, CAL/real-data, qualification, promotion,
R1d, G1/G2, or general GF32/NB-LDPC performance. D7-E/D7-F/D7-G accepted facts
above are the only reused claims. This freeze accepts no algorithm result —
only the frozen packet for a later gate. No alternating-convergence claim is
supported.

## 10. Freeze statement

This prereg froze every callable, constant, seed, row, formula, order, budget,
threshold, terminal and label rule above at basis HEAD `46141fcc`, before any
D7-H implementation, root, or decoder observation. All authorizations are
false; no identifier exists; no
`workspace/d7_h_alternating_discriminator_*` root exists.
