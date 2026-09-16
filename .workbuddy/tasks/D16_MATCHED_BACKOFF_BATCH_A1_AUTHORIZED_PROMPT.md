# SUPERSEDED — DO NOT USE AS AUTHORIZATION

This prompt was withdrawn before execution on 2026-09-15. D16 is now a held-out
validation point for the D17 finite-length scaling model. Copying the text below
does not constitute a current authorization.

# D16 One-Point Matched-Backoff — Batch A1 Authorized Prompt

I explicitly authorize `D16_MATCHED_BACKOFF_BATCH_A1` once on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D16_MATCHED_BACKOFF_BATCH_A1_TASK_PACKET.md`

After all pre-dispatch checks pass, execute exactly once:

```bash
.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a
```

This grant covers only L045/L055 at L1 m125 and true-conditioned L2 DV3 at
m94, four fresh graphs per arm, eight shared blocks, exactly 96 decoder calls
and 22 setup units. Budgets: 900 s wall, 120 s/call, RSS strictly below 2 GiB,
one CPU process; no APP/transfer.

Authorization is consumed when the command starts. No second invocation,
retry, repair, resume, seed search, tuning or adaptive change is authorized.
On pre-dispatch failure, do not start. On execution failure, retain evidence and
STOP. After completion obtain the independent batch-end review and return
`D16_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.

This grant does not authorize commit/push, D7-H, real data, route selection,
FER/leakage/SKR/qualification/optimality or publication claims.
