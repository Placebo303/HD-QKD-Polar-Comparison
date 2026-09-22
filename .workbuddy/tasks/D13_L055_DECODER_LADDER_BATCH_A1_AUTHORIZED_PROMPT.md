# D13 L055 Decoder Ladder — Batch A1 Authorized Prompt

I explicitly authorize `D13_L055_DECODER_LADDER_BATCH_A1` once, on branch
`formal-ir-v72p1-addendum-clean`, under
`.workbuddy/tasks/D13_L055_DECODER_LADDER_BATCH_A1_TASK_PACKET.md`.

Use immutable inputs
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
and `workspace/v72p2d5_model_f_input/20260907_r1`, and create only the fresh root
`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`.

After all packet pre-dispatch checks pass, run exactly once:

```bash
.venv/bin/python scripts/v72p2d13_development.py --d13-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e
```

The authorization covers exactly the 56 frozen D12 L055 failures, strict RL90
baseline replay, and the three frozen arms RL360 alpha=1, RL360 alpha=0.7, and
flooding-360: at most 224 scientific calls, 8 setup units, 1800 s wall,
120 s per call, RSS strictly below 2 GiB, one process, no retry/resume/repair,
no seed search, and no adaptive arm.

If any pre-dispatch check or replay comparison fails, STOP, retain evidence, and
report the raw mismatch. Do not substitute inputs or roots. After a completed
run, obtain one independent batch-end review with actual artifact access and
return `D13_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` with the
packet's exact evidence contract.

This grant does not authorize commit/push, L2, D7-H, real data, FER/leakage/SKR,
qualification, optimality claims, or a main-route decision.
