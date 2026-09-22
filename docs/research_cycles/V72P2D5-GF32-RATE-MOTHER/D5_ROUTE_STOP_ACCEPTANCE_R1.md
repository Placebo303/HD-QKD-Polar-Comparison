# D5 route-stop acceptance R1 — current fixed-decomposition two-layer rate-mother/BP path

- repo: `D:\Code\HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`
- review: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_REVIEW_R1.md` (landed unchanged)
- packet: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_AND_DECOMPOSITION_SUCCESSOR_R1_TASK_PACKET.md` (FROZEN_TASK_PACKET)
- status: `DEVELOPMENT_ONLY / NO_FORMAL_EXECUTION_AUTHORIZATION`

## Acceptance statements

1. `D5_ROUTE_STOP_REVIEW_PASS` is accepted.
2. Terminal: `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED`.
3. Reason: `ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY`.
4. Scope is exactly the current fixed high-five/low-five (`A = 32*U1 + U2`, `S1=(5,6,7,8,9)`), two-layer rate-mother/BP path.
5. GF32/NB-LDPC remains open.
6. Formal G1 remains accepted as completed-no-signal failure and is not rewritten.
7. G2 remains unauthorized and absent.
8. The chosen successor is the reversible 5+5 bit-partition decomposition discriminator (252 ordered partitions, CAL-only selection, bounded paired development decoder discriminator; graphs/mothers/schedules out of scope until its terminal).

## State

- `d5_route_stop_review: PASS_R1`
- `d5_current_path_stopped: true`
- `d5_stop_scope: CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH`
- `d5_stop_reason: ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY`
- `next_gate: D5_DECOMPOSITION_SUCCESSOR_PREREG`

No formal execution authorized. No push.
