# Alternating cross-layer discriminator — tasks (freeze only, Phase B)

> Operator authority: Phase B (freeze) only, per
> `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_TASK_PACKET.md`
> §§3–9. Docs only, zero decoder calls, zero Model-F content reads, zero
> roots, zero identifiers, zero push. The ALT-01–ALT-06 acceptance matrix in
> `proposal.md` and the schedule/fixtures in `design.md` are authoritative for
> the later implementation; this file references them rather than restating
> them.

- [x] B-freeze — **Freeze before code (docs only, this change).** This change
  folder (`proposal.md`, `design.md`, `specs/`, `tasks.md`) freezing packet
  §§3–9 in substance (schedule, transfer message, cavity rule, matrix,
  estimator, labels, terminal, budgets, file map, D7-H closed) plus the cycle
  directory `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/`
  with `D7_H_PREREG_R1.md` and `cycle_state.yaml` (D7-G keys adapted to D7-H;
  all authorization/promotion/decoder/result false; attempts zero; no
  identifier/root; predecessor D7-G acceptance;
  `next_gate: D7_H_IMPLEMENTATION_PENDING`). The D7-H packet pair under
  `.workbuddy/tasks/` is created by the same freeze, plus one linkage line in
  the D7-G `cycle_state.yaml`. The corrected freeze commit is authorized by
  `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md` (Phase A)
  and not by this freeze itself; implementation and execution remain
  unauthorized by this freeze.
- [ ] H01 implementation — **NOT AUTHORIZED.** Module/tests/script at the
  frozen paths; consume the D7-G extrinsic fields and helper; no change to
  decoder numerics, hard decisions, stopping, or iteration counts. Requires a
  future explicit authorization.
- [ ] H02 tests — **NOT AUTHORIZED.** ALT-01–ALT-06 coverage (schedule/call
  cap, `CHECK_EXTRINSIC`-only transfer, cavity/no-returned-evidence,
  both-layer AND rules, scalar seven-file writer/verifier, compatibility).
- [ ] H03 implementation review — **NOT AUTHORIZED.**
  `D7_H_IMPLEMENTATION_REVIEW_PASS|FAIL`.
- [ ] H04 Pre-EXECUTE review — **NOT AUTHORIZED.**
  `D7_H_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION|FAIL`.
- [ ] H05 execute — **NOT AUTHORIZED.** Exactly one invocation under a
  verbatim user authorization bound to one identifier.
- [ ] H06 Pre-RESULT review + result acceptance — **NOT AUTHORIZED.**

## Non-goals

- No execution authorization, no D7-H run, no result acceptance in this
  change.
- No implementation, tests, oracle, decoder calls, or certification results in
  this change.
- No `>2-stage` alternating, no posterior back-transfer, no promotion, no
  R1d/G1/G2 work; no modification of accepted D7-B/C/D/E/F/G roots or the
  frozen baseline `src/`, `experiments/`, `tools/`; no overwrite of existing
  outputs.
