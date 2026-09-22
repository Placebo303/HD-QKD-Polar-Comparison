# OpenCode prompt — D6 R1d EXPLORE execution A1

Repository: `D:\Code\HD-QKD_Polar_Comparison`

This user-sent prompt is explicit authorization for exactly one frozen D6 R1d EXPLORE batch invocation. Read this task packet completely before acting:

`D:\Code\HD-QKD_Polar_Comparison\.workbuddy\tasks\D6_R1D_EXPLORE_EXECUTION_A1_TASK_PACKET.md`

Verify the accepted repository-wide workflow marker, the readiness terminal, all authorization flags false, the exact CAL-only Model-F root, and absence of:

`workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d`

Run only the packet's small focused drift preflight. Trust the recorded H45 reviewer-go independent 343-test rerun; do not repeat it for ceremony. If any pre-dispatch check fails, return `BLOCKED_PRE_DISPATCH` without repair or execution.

If checks pass, authorize and run exactly once:

```text
.venv/bin/python scripts/v72p2d6_graph_mother_development.py --r1d --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d --workers 18
```

Only the frozen RSS pilot downgrade `18→14→12→8` is allowed. No retry, resume, tuning, seed search, alternate root or scientific substitution. Do not run D7-H, G1/G2, T2/T3/T4/M1/M2, real/VAL/raw data or n1024. Do not commit or push.

After the run, restore all authorization flags to false, retain every failure/partial artifact, append the result to the single `EXPLORATION_LOG_R1D.md`, and obtain one independent reviewer-go batch-end review against the actual root. The reviewer must run the read-only verifier and independently recount gates, records and budgets. Do not self-accept or select the next route.

Return only `COMPLETE` at `D6_R1D_EXPLORE_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`, or `BLOCKED` with the raw failure and one decision needed. Report deltas only.
