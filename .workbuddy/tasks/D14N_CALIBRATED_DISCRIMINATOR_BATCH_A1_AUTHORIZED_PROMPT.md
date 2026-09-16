# D14N Calibrated L1/L2 Discriminator — Batch A1 Authorized Prompt

I explicitly authorize `D14N_CALIBRATED_DISCRIMINATOR_BATCH_A1` once on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_BATCH_A1_TASK_PACKET.md`

After all pre-dispatch checks pass, execute exactly once:

```bash
.venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/v72p2d14_discriminator/20260914_r1
```

This grant covers only the frozen n128 synthetic matrix: L045 and L055 at
m=110, L2 DV3 APP and ORACLE, six paired graph seeds, twelve paired block seeds,
exactly 288 decoder calls and 32 setup units. Budgets are 1800 s wall, 120 s per
call, RSS strictly below 2 GiB, one CPU process, with APP sourced only from L055.

The authorization is consumed when the command starts. No second invocation,
retry, repair, resume, seed search, tuning or adaptive change is authorized.
On any pre-dispatch mismatch, do not start. On execution failure, retain evidence
and STOP. After completion, obtain the packet's independent batch-end review and
return `D14N_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.

This grant does not authorize commit/push, D7-H, real data, G1/G2 rerun,
FER/leakage/SKR/qualification/publication claims, or a main-route decision.
