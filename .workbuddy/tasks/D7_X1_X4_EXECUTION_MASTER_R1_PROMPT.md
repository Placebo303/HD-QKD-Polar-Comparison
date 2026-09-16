# OpenCode prompt — D7 X1–X4 execution master R1

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Read the entire packet before acting:

`D:\Code\HD-QKD_Polar_Comparison\.workbuddy\tasks\D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`

Start with **Phase P only**: close the real X1/X3/X4 entrypoints, run fake-injected T0/T1 checks, prepare the exact Pre-EXECUTE records, and obtain the required independent readiness review. Production decoder/CAL/VAL calls must remain zero. Stop at `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

Do not run X1, X2, X3, X4, G1, D7-H, real data, or n=1024 work. Do not alter historical evidence or unrelated dirty files. Do not push. The four X phases are dormant and separately user-authorized; no phase authorizes the next.

Return only `COMPLETE` after all P01–P10 items pass, or `BLOCKED` with the exact raw failure, authorization-consumption state, and one decision needed. Report deltas only.
