# OpenCode prompt — D9 calibration authorization A1

Repository: `D:\Code\HD-QKD_Polar_Comparison`

This user-sent prompt explicitly authorizes exactly one frozen D9 96-call
GF32 DE calibration batch. Read the complete packet first:

`D:\Code\HD-QKD_Polar_Comparison\.workbuddy\tasks\D9_DE_CALIBRATION_A1_TASK_PACKET.md`

Verify the accepted D9 readiness marker, authorization false, intact CAL-only
Model-F root, frozen four-candidate/eight-seed/96-call plan, semantics markers,
f1.0 boundary-only role, and absence of:

`workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`

Pre-create the task-owned pytest basetemp parent, then run only py_compile and
the 20 focused D9 tests. Trust the C11 independent review; do not rerun broad
suites or D8. On mismatch return `D9_DE_CALIBRATION_BLOCKED_PRE_DISPATCH`
without repair.

If all checks pass, run exactly once:

```text
.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py --calibrate --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b
```

No retry/resume/tuning/seed extension, alternate root, finite-length decoder,
D7-H, CAL/VAL/raw/real data, commit or push. Per-call <=300 s is a post-call
check, not an interrupting watchdog. f1.0 is reported only and never gates.
Retain partial evidence; do not use partial aggregation to create eligibility.

After the invocation, append the single exploration log and obtain one
independent reviewer-go batch-end review against the actual root. Do not
self-accept a candidate or select the next route.

Return only `COMPLETE` at
`D9_DE_CALIBRATION_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`, or
`BLOCKED` with raw evidence and one decision needed. Report deltas only.
