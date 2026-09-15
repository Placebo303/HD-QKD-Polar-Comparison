# D15 Paired Finite-Length Margin Curve — EXPLORE log (append-only)

- Authority: `.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md` (§§1–§7, sole authority; §7 return contract).
- Track: documentation-only (no code, no execution, no D15 batch, no decoder/scientific calls, no root creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This is the single append-only log root for D15. Detail record: `READINESS_R1.md` in this directory.
- Predecessor pointer: `docs/research_cycles/D14_VALIDITY_RESET/EXPLORATION_LOG.md` (D14N accepted `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`; routes to margin curve).
- This call (D1510B): documentation-only close (two new record files in this directory, one pointer append to the D14 log, D15 OpenSpec `tasks.md` D1503–D1510 checkbox update). No code, no execution, no decoder/DE/real-data calls, no staging/commits, no push.

## 2026-09-15 — D15 readiness R1 close (no execution)

### Authorization boundary

- This call performed no code edit, no D15 execution, no decoder or scientific call, no root creation, no commit, no push.
- The frozen 288-call margin-curve batch remains unauthorized. It requires a separate explicit batch grant. No authorization was granted by readiness or by D15-R1510.
- No-execution-authorized statement: **no D15 execution is authorized by this close; the future root remains absent and the frozen command remains an unauthorized string.**

### D1501–D1509 evidence (trusted VERIFIED, do not rerun)

- Arithmetic: loads 548.700215065776 / 412.508145233200; factors L1 1.00237/1.03882/1.07527 + L2 1.00604/1.04240/1.07877; pairing gaps +0.00367/+0.00359/+0.00350; sockets L045 313 / L055 301 / L2 384; all nine allocs count-sum=m + socket-sum=E.
- Admission 36/36 (A1–A6, replay, 1 component, srank==m, gf32==m; L1 min_dc 2, L2 min_dc 4); replacements 0; wall ~2.39 s double-build.
- Seeds: 36 graph + 8 blocks 3901–08 exact, disjoint from priors; plan 288 (9×32, point-major) + batch-tag d15-margin-curve-v1.
- Reuse is-identical, no copied kernels; No-APP 0 hits, ARMS len 3, oracle diagnostic-only ungraded.
- Tests 25/25 + py_compile 3/3; PROFILE_ONLY 36 graphs + 288 plan, decoder 0; fake summary setup 46/calls 288; budgets 288/46/1800/120/2GiB/1-proc.
- Refusal rc=2 pre-write/bind/load (reviewer ran); future root absent pre/post; FROZEN_COMMAND verbatim.

### D1510 verdict/findings (trusted VERIFIED)

- EVIDENCE_ACCESS VERIFIED; VERDICT PASS_WITH_FINDINGS; BLOCKING none.
- D14N-3FAIL adjudication: ENVIRONMENTAL NON-BLOCKING, out of D15 scope.
- Non-blocking: stale runner comment (flag wording contradicts actual — code correct, later docs touch); additive-clean scope.

### Terminal

`D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`. Next gate: separate explicit batch grant. No route/investment/D7-H/FER claims.
