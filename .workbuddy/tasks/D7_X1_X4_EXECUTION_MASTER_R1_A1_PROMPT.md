# OpenCode prompt — execute D7 X1–X4 master R1 A1

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Read both files completely before acting:

1. `D:\Code\HD-QKD_Polar_Comparison\.workbuddy\tasks\D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
2. `D:\Code\HD-QKD_Polar_Comparison\.workbuddy\tasks\D7_X1_X4_EXECUTION_MASTER_R1_A1_TASK_PACKET.md`

The user explicitly authorizes one sequential attempt of X1–X4. Execute them serially with the frozen commands, roots, budgets, phase flags, outer watchdogs, and STOP rules. Restore each flag false immediately after its attempt. Obtain an independent Pre-RESULT review between phases; if an independent reviewer is unavailable or any gate fails, stop the entire chain. Never retry, resume, tune, replace seeds/roots, clean partial evidence, run D7-H/G1/real/n=1024 work, push, or promote results.

Return only `COMPLETE` after every applicable X phase and independent review is complete, or `BLOCKED` at the first failing gate with raw evidence and one decision needed. Report deltas only.
