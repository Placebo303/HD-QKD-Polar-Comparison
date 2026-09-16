# D17 Current-Channel Asymptotic DE — Batch A1 Authorized Prompt

I explicitly authorize `D17_ASYMPTOTIC_DE_BATCH_A1` once on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D17_ASYMPTOTIC_DE_BATCH_A1_TASK_PACKET.md`

First record the main-thread readiness acceptance marker
`D17_DE_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`, then run
all mandatory pre-dispatch checks. Only if every check passes, execute exactly
once:

```bash
.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718
```

This grant covers only the frozen three-profile, five-point, eight-seed,
two-population current-channel MC-DE matrix: exactly 240 scientific DE calls
and at most 12 setup units. Budgets are 1200 s wall, 300 s per call by the
implemented between-call check, RSS strictly below 2 GiB, one CPU process.

Authorization is consumed when the command starts. No second invocation,
retry, resume, grid extension, seed search, binary search, adaptive stop, or
scientific repair is authorized. On pre-dispatch failure, do not start. On run
failure, retain the partial evidence and STOP. Then obtain one independent
batch-end review and return
`D17_DE_BATCH_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`.

This grant does not authorize finite-length fitting, D16 prediction writing,
D16 execution, decoder/CAL/VAL/real-data work, commit/push, route selection,
D7-H, or FER/leakage/SKR/qualification/optimality/publication claims.
