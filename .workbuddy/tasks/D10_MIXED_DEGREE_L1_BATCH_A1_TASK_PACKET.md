# D10 Mixed-Degree L1 Batch A1 — execution task packet

## Gate and scope

Track: `EXPLORE`. Repository/branch: `HD-QKD_Polar_Comparison` /
`formal-ir-v72p1-addendum-clean`. Hard prerequisite:
`D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
This packet freezes but does not authorize execution. Start only after the user
explicitly authorizes `D10_MIXED_DEGREE_L1_BATCH_A1`, the branch, root,
conditional widths and budgets below.

## Frozen run

Root, which must be absent:
`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`.

Exact command, once:

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
```

Use the accepted R2 OpenSpec unchanged: two arms, exact degree tables, graph
seeds `2026092201..09`, block seeds, coefficients, priors, decoder
(`max_iter=90`, damping 1.0, cold), pairing, thresholds and claim ceiling.
Dispatch n64 first (48 calls), n128 iff n64 is POSITIVE, and n256 iff n128 is
POSITIVE. Control never advances independently.

Budgets: ≤144 scientific L1 calls, ≤44 setup units, wall ≤1800 s, each call
≤120 s, RSS strictly <2147483648 B, one process. No retry/resume, seed
replacement/search, tuning or scientific-input change.

## Pre-dispatch record

Append seven checks to the existing `EXPLORATION_LOG.md` before execution:

1. accepted R2 marker and R211 verified PASS/no blocker;
2. exact branch and scoped code/packet unchanged;
3. result root absent and Model-F CAL-only root present/unchanged;
4. plan, seeds, arms, thresholds, command and budgets match OpenSpec;
5. all 18 graph structures still pass A1--A6, zero replacements;
6. `py_compile` and both focused D10 tests pass in a fresh basetemp;
7. unrelated output and authorization state untouched.

Any failure: STOP before using `--execution-authorized` and return raw evidence.

## Execute and review

Run the exact command once. Retain any failed partial root; A1 permits no repair
or rerun. Record command/exit/timestamps, calls/setup, wall/per-call/RSS, graph
admission, paired per-graph and pooled exact and syndrome-valid counts, width
gates and stored terminal. Keep exact and syndrome-valid outcomes separate.

Then obtain one independent EXPLORE batch-end review with
`EVIDENCE_ACCESS: VERIFIED`. It independently recomputes root completeness,
call identities, A1--A6, paired counts, frozen predicates, conditional
progression, terminal and budgets; confirms no replacement/retry/tuning; and
checks the claim ceiling. Review failure blocks use of evidence and grants no
rerun.

Valid scientific terminals are the frozen OpenSpec terms:
`D10_L1_CANDIDATE_REPRODUCIBLE`, `D10_L1_FINITE_SIZE_SIGNAL`,
`D10_L1_NO_MATERIAL_ADVANTAGE`, `D10_L1_AMBIGUOUS`, or its specified
engineering/resource blocked terminal. They are evidence, not route acceptance.

## Boundaries and return

Use the one append-only exploration log and perform memory triage after review.
Do not run L2/APP, D7-H, DE, CAL/VAL, real data or claim-bearing work. Do not
commit/push unless asked.

Return `D10_MIXED_DEGREE_L1_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`
only after a completed run and passing review. Otherwise return the exact
blocked terminal and one needed decision. Report deltas, command/exit, root,
calls/resources, all counts/gates, independent verdict, authorization
consumption and commit/push state.
