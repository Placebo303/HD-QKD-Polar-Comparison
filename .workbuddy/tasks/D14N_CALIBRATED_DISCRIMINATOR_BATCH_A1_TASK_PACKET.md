# D14N Calibrated L1/L2 Discriminator — Batch A1 Task Packet

## 1. Identity and track

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Batch: `D14N_CALIBRATED_DISCRIMINATOR_BATCH_A1`
- Track: `EXPLORE`
- Accepted readiness:
  `D14N_R2_EXECUTION_PATH_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
- One authorization covers exactly one frozen 288-call run and its batch-end
  review. This packet alone grants no execution.

## 2. Frozen scientific contract

- Width n=128 only.
- L1 L045 control: m=110, n2/n3=71/57, E=313, checks `2^17+3^93`.
- L1 L055 challenger: m=110, n2/n3=83/45, E=301, checks `2^29+3^81`.
- L2 DV3: m=104, E=384, checks `3^32+4^72`.
- Graph seeds: L1 `2026093401..06`; L2 `2026093501..06`.
- Block seeds: `2026093601..12`; fully paired across all four arms.
- Calls: 72 each L045, L055, L2 APP, L2 ORACLE; exactly 288.
- APP source profile: L055 only. CONTROL is descriptive. ORACLE is diagnostic
  and excluded from grading.
- Accepted candidate concentration-backoff prior; GF32/poly37; row-layered
  cold decoder max_iter=90 and damping=1.0.
- Every non-oracle APP transfer must carry `CHECK_UPDATED`; no prior-only or
  uniform fallback.
- Exact, syndrome, L1 source, L2 target, joint and `undetected` remain distinct.
- Frozen thresholds, six terminals and first-match priority are those in the
  accepted D14N spec; no outcome-adaptive change is permitted.

## 3. Inputs, root and command

- Model-F CAL-only input:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- Fresh result root:
  `workspace/v72p2d14_discriminator/20260914_r1`
- Authorized command, exactly once:

```bash
.venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/v72p2d14_discriminator/20260914_r1
```

The manifest may retain the accepted flag-free scientific command identity;
the operator record must preserve the actual command including
`--execution-authorized`.

## 4. Mandatory pre-dispatch checks

Append raw results to the existing D14 exploration log before execution:

1. Accepted R2 marker and R207 VERIFIED review exist with no blocking finding.
2. Branch is exact; R2 commit `3f874bb` is an ancestor; inspect scoped paths and
   preserve unrelated dirty files.
3. Result root is absent. Model-F input is present, CAL-only and unchanged.
4. Reconfirm the current working-tree D5 production wiring: P0/G1/G2 each call
   `prepare_model_f_prior_candidate` exactly once and do not call the legacy
   estimator. Because those hunks are excluded from commits, any drift is STOP.
5. Reconfirm `APP_SOURCE_PROFILE == "L055"`; adapters and signatures resolve;
   binding probe performs zero decoder calls and no Model-F load.
6. PROFILE_ONLY: 18/18 admitted, amended tables exact, zero replacements,
   288 deterministic identities, setup accounting 32, decoder 0, root absent.
7. Live unauthorized command against a fresh scratch target returns rc=2 before
   root/bind/load. Do not touch the official root.
8. `py_compile` plus the 7 authorized-path and 22 D14N focused tests in a fresh
   writable basetemp. Trust unchanged D11/D12 reviewer evidence unless a focused
   conflict appears.
9. Reconfirm actual command, seeds, four arms, gate priority, six terminals,
   budgets and no prior authorization consumption.

Any failure: STOP before the real command; report raw evidence. Do not repair,
retry, change a seed, substitute a root, or stage unrelated files.

## 5. Budgets and execution rules

- Scientific decoder calls: exactly planned 288; hard ceiling 288.
- Setup units: exactly 32; hard ceiling 32.
- Wall: ≤1800 s.
- Per-call wall: ≤120 s.
- RSS: strictly <2147483648 bytes.
- One foreground CPU process.
- No retry, resume, repair, seed search, tuning, adaptive stop or second run.
- Existing root, admission failure, malformed/non-CHECK_UPDATED provenance,
  nonfinite output, call-order mismatch, budget breach or writer failure: STOP
  and retain all available evidence. Authorization is consumed when the command
  starts even if it fails.

## 6. Frozen result interpretation

Recompute from records, never only from stored summary:

- `L1-ADEQUATE`: L055 exact ≥18/72 and at least 5/6 graphs have ≥2 exact.
- `ORACLE-ADEQUATE`: L2 ORACLE exact ≥18/72.
- `L2-JOINT-GOOD`: L2 APP joint-both-exact ≥9/72.
- First-match terminals:
  1. engineering violation → `N_ROUTE_BLOCKED_ENGINEERING`;
  2. not L1-ADEQUATE → `N_ROUTE_L1_CONSTRUCTION`;
  3. L1 adequate, APP not good, oracle not adequate → `N_ROUTE_L2_DEGREE`;
  4. L1 and oracle adequate, APP not good →
     `N_TRANSFER_BOTTLENECK_RECORDED`;
  5. L1 adequate and APP good → `N_ROUTE_SCALE_VALIDATION`;
  6. otherwise → `N_ROUTE_AMBIGUOUS`.

Report L045/L055 paired discordances descriptively only. A stored terminal is
evidence awaiting main-thread route adjudication; it authorizes nothing.

## 7. Independent batch-end review

One independent reviewer with actual artifact access must:

- verify exact one-shot authorization, command, root inventory and no retry;
- recompute 18 graph admissions, 288 identities and setup=32;
- recount all four arms per graph and pool with exact/syndrome/undetected
  isolation and CHECK_UPDATED/ORACLE semantics;
- confirm APP source is L055 and oracle is excluded from grading;
- recompute the three predicates, priority and terminal;
- verify resource budgets, Model-F immutability, no D7-H/real-data path and
  read-only verifier PASS;
- record `EVIDENCE_ACCESS`, verdict, blocking and non-blocking findings in the
  single D14 exploration log.

Review FAIL blocks use of evidence and does not authorize a rerun.

## 8. Return contract

On reviewed completion return:

`D14N_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`

Report exact command/exit/timestamps; calls/setup/wall/max-call/RSS/process;
per-arm/per-graph exact and syndrome counts; undetected; APP source/provenance;
three predicates and stored terminal; root inventory; verifier and independent
verdict; authorization consumption; changed files; no retry/commit/push; claim
boundary and remaining route decision.

Do not commit or push batch results, execute D7-H/real data, or make FER,
leakage, SKR, qualification, optimality, publication or final route claims.
