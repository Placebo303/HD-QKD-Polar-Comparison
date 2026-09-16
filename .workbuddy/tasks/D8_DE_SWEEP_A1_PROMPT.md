# OpenCode prompt — D8 DE sweep authorization A1

Repository: `D:\Code\HD-QKD_Polar_Comparison`

This user-sent prompt explicitly authorizes exactly one frozen D8 rate-aligned
GF32 DE sweep. Read the complete task packet first:

`D:\Code\HD-QKD_Polar_Comparison\.workbuddy\tasks\D8_DE_SWEEP_A1_TASK_PACKET.md`

Verify the accepted D8 readiness marker, all authorization flags false, the
accepted CAL-only Model-F root, frozen 21×2×3 plan, carried F2–F4 semantics,
and absence of:

`workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`

Run only the small focused drift preflight. Trust the existing independent
review; do not repeat broad tests or the 56-check audit. On any mismatch return
`D8_DE_BLOCKED_PRE_DISPATCH` without repair.

If checks pass, run exactly once:

```text
.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405
```

No retry, resume, tuning, alternative root/grid/seed, finite-length decoder,
D7-H, CAL/VAL/raw/real data, n1024, commit or push. The 120 s call limit is a
post-call check, not an interrupting watchdog. The DE uses V26 random nonzero
coefficient-ensemble semantics, not finite-length coefficient seeds. Retain any
partial root; normal verification may fail closed and must not trigger cleanup
or rerun.

After the invocation, append to the single exploration log and obtain one
independent reviewer-go batch-end review against the actual root. Do not
self-accept the scientific result or choose the successor route.

Return only `COMPLETE` at
`D8_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`, or `BLOCKED`
with the raw failure and one decision needed. Report deltas only.
