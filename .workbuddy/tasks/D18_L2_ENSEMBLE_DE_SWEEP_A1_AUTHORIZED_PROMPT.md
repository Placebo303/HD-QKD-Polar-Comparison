# D18 L2 Ensemble DE — Sweep A1 Authorized Prompt

I accept `D18_L2_ENSEMBLE_DE_READY_AWAITING_EXPLICIT_AUTHORIZATION` and record
`D18_L2_ENSEMBLE_DE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.

I explicitly authorize `D18_L2_ENSEMBLE_DE_SWEEP_A1` once on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D18_L2_ENSEMBLE_DE_SWEEP_A1_TASK_PACKET.md`

Run all pre-dispatch checks. Only if all pass, execute exactly once:

```bash
.venv/bin/python scripts/v72p2d18_ensemble_development.py --de-sweep --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901
```

This grant covers Stage S and mechanically selected Stage C with 32 reused
overlaps, ≤288 new and ≤456 total DE calls, setup≤16, wall≤1800s,
per-call≤300s, RSS<2GiB, one CPU, plus one independent review.

Consumed at command start. No second invocation, retry/resume, manual candidate
replacement, extra seed/grid, search, adaptive extension, or repair. Retain and
STOP on failure. After review return
`D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.

No finite L2 construction, decoder/APP/L1/real-data work, commit/push, route
selection, D7-H, or FER/leakage/SKR/qualification/optimality/publication claim
is authorized.
