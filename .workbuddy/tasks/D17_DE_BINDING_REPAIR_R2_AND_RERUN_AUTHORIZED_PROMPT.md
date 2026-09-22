# D17 Production DE Binding Repair R2 + Fresh Rerun — Authorized Prompt

I accept the independently verified A1 engineering failure and explicitly
authorize `D17_DE_BINDING_REPAIR_R2_AND_RERUN_A2` on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D17_DE_BINDING_REPAIR_R2_AND_RERUN_TASK_PACKET.md`

Implement only R201–R203 after the R2 OpenSpec amendment; preserve R204
scientific inputs exactly. Validate the real production binding chain with a
zero-DE-call spy, including both tuple-to-L1-sampler construction and actual
true-conditioned L2 oracle-sampler dispatch. Obtain the scoped independent
repair review in the single D17 log.

Only if every repair and pre-dispatch check passes, execute exactly once:

```bash
.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24
```

This is a fresh A2 grant for exactly 240 DE calls and at most 12 setup units;
budgets are 1200 s wall, 300 s per call by the implemented between-call check,
RSS strictly below 2 GiB, one CPU process. The A1 failure root remains
immutable and is never resumed or overwritten.

The A2 grant is consumed when the command starts. No second invocation, retry,
resume, grid/seed extension, binary search, adaptive stop, or post-start repair
is authorized. On a blocker, retain evidence and STOP. After success obtain the
independent batch-end review and return
`D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`.

This grant does not authorize the scaling fit, D16 prediction writing, D16
execution, decoder/CAL/VAL/real-data work, commit/push, route selection, D7-H,
or FER/leakage/SKR/qualification/optimality/publication claims.
