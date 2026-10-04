# D11 Canonical Forward APP Integration — Proposal

- Change: `v72p2d11-forward-app`
- Cycle: `V72P2D11-FORWARD-APP` (successor of `V72P2D10-R3-FRESH-SCALING`)
- Track: **implementation/readiness** (zero scientific calls; no D11 batch, no L2
  results, no D7-H, no real data, no commit/push). The future batch is
  `EXPLORE_HEAVY`.
- Authority (read fully first, frozen): 
  `.workbuddy/tasks/D11_FORWARD_APP_INTEGRATION_READINESS_TASK_PACKET.md`
  (§1–§4), `AGENTS.md` §1.2/§3/§5/§10.1.
- Predecessor (immutable, read-only context, no rerun, never pooled into D11):
  `D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`
  (machine terminal `D10_R3_WIDE_L1_SIGNAL_REPRODUCED`, VERIFIED PASS;
  root `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`).

## Goal

Build the smallest experiment that answers whether the reproducible mixed-L1
signal survives one canonical L1→L2 APP transfer, while separately measuring
the L2 decoder ceiling — and freeze that experiment in OpenSpec before any
behavior edit. D7-H is explicitly out of scope: a forward pass plus L2 oracle
must be resolved before reverse/alternating feedback can be interpreted.

## Non-Goals

- No D11 execution/batch, no decoder or scientific call, no root creation.
- No D7-H (reverse/alternating feedback), no L2 mixed-degree work (no mixed
  degree on L2 without separate calibration).
- No FER, leakage, SKR, real-data, qualification, promotion, optimality, or
  publication claim (claim ceiling: synthetic two-layer forward diagnostic only).
- No modification of predecessor roots, frozen baselines, `AGENTS.md`, or
  decision-log; no commit or push.

## Impact Scope

- Added only: `openspec/changes/v72p2d11-forward-app/` (this proposal,
  `design.md`, `tasks.md`, `specs/forward-app/spec.md`).
- Read-only context: D10 R3 root + `EXPLORATION_LOG.md`, R2/R3 graph-decoder
  modules, D5/D7 transfer/provenance/oracle helpers, v35 decoder helpers,
  Model-F input root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Forbidden for this change: code/scripts/tests/roots/results/predecessor
  artifacts/`AGENTS.md`/decision-log.

## Acceptance Criteria

- D1101: this OpenSpec change exists with packet §2 frozen verbatim
  (widths, seeds, blocks, replay gate, L2 tables, constructor/admission/coeff
  rule, field/prior/decoder, three branches, 72 cells / 360 calls per width,
  metric isolation, CHECK_UPDATED fail-close, gate equations, mutual priority,
  terminals, future root, budgets, claim ceiling); `tasks.md` shows
  D1101+D1102 `[x]`, D1103–D1110 `[ ]`.
- D1102: exact reuse map with `path:line` for (a) L1→L2 forward transfer +
  message/provenance semantics, (b) CHECK_UPDATED emission/check,
  (c) q/APP helpers, (d) D6-chain oracle definition; explicit semantic
  duplication rejection (D11 must import unchanged); L2-seed + future-root
  absence scan raw output recorded. Audit found all canonical helpers —
  no BLOCKED condition met.
- D1103–D1110 remain `[ ]`, packet-exact, for successor execution.
- Zero scientific calls; zero decoder calls; no root created; no commit/push.

## Preserved-items checklist

- [x] Packet §1–§4 read fully; §2 frozen verbatim into `design.md` +
  `specs/forward-app/spec.md` (no rewording of thresholds/labels/vectors).
- [x] D10 R3 signal accepted as immutable predecessor; A1/R3 evidence never
  pooled into D11 (D11 replays R3 L1 vectors as a hard validity gate only).
- [x] Reuse map recorded with exact `path:line`; duplication explicitly
  rejected (see `design.md` §5).
- [x] 12 L2 seeds + future-root UUID verified absent from repo (raw output in
  `design.md` §6; only the packet itself references them).
- [x] Future root absent (read probe: no such path); OpenSpec target dir was
  absent before creation; branch `formal-ir-v72p1-addendum-clean` confirmed
  via `.git/HEAD`, no switch.
- [x] Allowed-files boundary kept: only
  `openspec/changes/v72p2d11-forward-app/**` written.
- [x] Execution false; decoder calls 0.
