# D15 Paired Finite-Length Margin Curve — Batch A1 Authorized Prompt

I explicitly authorize `D15_MARGIN_CURVE_BATCH_A1` once on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D15_MARGIN_CURVE_BATCH_A1_TASK_PACKET.md`

After every pre-dispatch check passes, execute exactly once:

```bash
.venv/bin/python scripts/v72p2d15_margin_curve_development.py --d15-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2
```

This grant covers only the frozen n128 synthetic margin curve: L1 L045/L055 at
m=110/114/118 and L2 DV3 ORACLE at m=83/86/89, four graphs per cell, eight
shared blocks, exactly 288 decoder calls and 46 setup units. Budgets are 1800 s
wall, 120 s/call, RSS strictly below 2 GiB and one CPU process.

Authorization is consumed when the command starts. No second run, retry,
repair, resume, seed search, tuning or adaptive change is authorized. If a
pre-dispatch check fails, do not start. If execution fails, retain evidence and
STOP. After completion obtain the packet's independent batch-end review and
return `D15_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.

This grant does not authorize commit/push, APP, D7-H, real data, route choice,
FER/leakage/SKR/qualification/optimality or publication claims.
