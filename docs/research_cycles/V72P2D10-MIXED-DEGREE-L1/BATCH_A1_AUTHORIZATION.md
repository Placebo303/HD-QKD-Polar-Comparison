# D10 Mixed-Degree L1 Batch A1 — explicit authorization

Date: 2026-09-14

Status: `D10_MIXED_DEGREE_L1_BATCH_A1_AUTHORIZED_ONCE`

The main thread explicitly authorizes one execution under
`.workbuddy/tasks/D10_MIXED_DEGREE_L1_BATCH_A1_TASK_PACKET.md`.

- Branch: `formal-ir-v72p1-addendum-clean`
- Root: `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
- Sequence: n64; n128 only iff n64 POSITIVE; n256 only iff n128 POSITIVE
- Ceiling: 144 scientific L1 calls; 44 setup units; 1800 s wall; 120 s/call;
  RSS strictly below 2147483648 B; one process
- Command: exactly the packet §Frozen run command, once
- Afterward: one independent `EVIDENCE_ACCESS: VERIFIED` batch-end review

The authorization is consumed when the command begins. No retry, repair, seed
replacement/search, tuning, input change, L2/APP, D7-H, real data, commit or
push is authorized. A pre-dispatch mismatch blocks execution and leaves this
grant unconsumed until the main thread adjudicates the mismatch.
