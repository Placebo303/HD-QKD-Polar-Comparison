# D17 Production DE Binding Repair R2 + Fresh Rerun — Task Packet

## 1. Decision, identity, and track

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change amendment: `v72p2d17-asymptotic-finite-scaling` R2
- Batch: `D17_DE_BINDING_REPAIR_R2_AND_RERUN_A2`
- Track: `EXPLORE_HEAVY` (one bounded engineering repair followed by one fresh
  scientific rerun)
- Predecessor terminal accepted as failure evidence:
  `D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION`.
- The A1 root is immutable failure evidence. A1 produced 0/240 scientific
  calls and supplies no DE threshold or scaling-fit evidence.
- This packet plus its companion prompt authorizes the exact R2 repair,
  focused validation, one fresh 240-call rerun, and one independent batch-end
  review. It does not authorize any further repair or rerun.

## 2. Frozen repair scope

OpenSpec amendment first, then change only the D17 adapter/runner/tests and the
single D17 exploration log as needed.

### R201 — L1 tuple-to-sampler binding

- Call the accepted `load_l1_channel(model_f_root)` exactly once and require
  an exact three-item `(pb, p_f, p1)` result with finite, shape-compatible
  arrays.
- Call the already-bound accepted `build_l1_sampler(pb, p_f, p1)` exactly once.
- Require its return to be callable and, in the zero-scientific-call contract
  test, prove a tiny invocation returns finite normalized `(k,32)` centered
  rows. The tiny invocation is test/probe evidence, never a V26 DE call.

### R202 — true-conditioned L2 oracle sampler

- Build `p2` exactly once with the already-bound
  `conditionalize_f_to_p2(p_f)`.
- Add one minimal D17 adapter that samples `(A,B)` from the same
  `pb[B]*p_f[A,B]` joint as the accepted L1 sampler, sets
  `u1=A//32`, `u2=A%32`, obtains the prior exclusively through the bound
  `oracle_l2_prior(p2, B, u1)`, applies the accepted D9/D5 floor-normalize
  convention, and XOR-centers each row on true `u2` for the V26 consumer.
- Fail closed on nonfinite/invalid mass, incompatible shapes, non-callable
  result, or a row that is not finite, normalized, and `(k,32)`.
- Do not reuse V36/V37 empirical-count samplers: their source channel is not
  the current Model-F candidate chain.

### R203 — profile dispatch

- `L1_L045` and `L1_L055` must receive only the L1 callable.
- `L2_DV3_ORACLE` must receive only the true-conditioned L2 callable.
- Dispatch is selected from the frozen plan entry's profile before every
  `run_de_call`; unknown/mislabelled profiles fail before a scientific call.
- Preserve dependency injection for fake tests, but represent the injected
  channels in a form that makes profile selection explicit. A single callable
  silently shared by all three production profiles is forbidden.

### R204 — no other scientific change

Retain exactly: all 15 row points; seeds `2026094201..08`; populations
`4000/16000`; lambda/rho construction; V26 kernel; 60 iterations; 1e-4
convergence threshold; streak 20; bracket/flag/delta_DE rules; plan order;
240-call and resource ceilings; claim ceiling; banned D16 identities.

## 3. Required R2 validation before rerun

Use fakes/tiny probes only; write no official R2 root during validation.

1. Reproduce A1 failure mechanically from persisted code/evidence; never
   modify, verify-as-complete, delete, or reuse the A1 root.
2. Production binder resolves every accepted callable with zero V26 DE calls.
3. Stub the Model-F loader with finite asymmetric arrays and prove:
   - loader result is unpacked once;
   - L1 builder returns a callable and receives `(pb,p_f,p1)`;
   - L2 conditionalizer and oracle mixer are both actually invoked;
   - L1 and L2 output rows are `(k,32)`, finite, normalized, centered on the
     respective true symbol, and observably non-identical on an asymmetric
     fixture.
4. Fake the DE call over the complete 240-row plan and prove every L1 entry
   receives the L1 sampler and every L2 entry receives the L2 sampler; swapped,
   missing, tuple, unknown-profile, invalid-shape, and nonfinite channels fail.
5. Exercise the real production bind/signature/load/build/dispatch chain with
   V26 `run_de_call` replaced by a zero-call spy. It must load/build both
   samplers and stop before any scientific DE call.
6. `py_compile`; focused D17 tests including the new regression tests in one
   fresh writable basetemp. Run broader predecessor suites only on a concrete
   compatibility conflict.
7. Independent reviewer with actual file access confirms R201–R204 and the
   zero-call production-chain proof. Record findings in the one D17 log; no
   separate ceremonial document is required.

Any test or review blocker is STOP before rerun. One implementation correction
within R201–R203 is allowed before the reviewer closes the repair, provided the
scientific contract R204 is unchanged and the failed attempt stays in the log.

## 4. Fresh rerun root, command, and budgets

- A1 failed root, read-only:
  `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`
- Fresh A2 result root (must be absent):
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
- Model-F root:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- Execute exactly once after all R2 validation passes:

```bash
.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24
```

- Exactly 240 scientific DE calls; setup at most 12.
- Wall at most 1200 s; per-call at most 300 s by the implemented between-call
  check; RSS strictly below 2147483648 bytes; one CPU process.
- No retry, resume, seed/grid extension, binary search, adaptive stop, or
  second engineering repair after command start.

## 5. Mandatory pre-dispatch

Append raw evidence to
`docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`:

1. A1 failure-review `VERIFIED/PASS`, exact stored error, 0/240, and consumed
   grant; A1 six-file root present and unchanged.
2. Exact branch and scoped R2 diff. Preserve unrelated dirt. Record the R2
   implementation revision if committed, but do not require HEAD equality.
3. A2 root and D16 official root absent; Model-F root unchanged.
4. R201–R203 focused tests and independent repair review PASS with no blocker.
5. Full frozen matrix equality to A1: 15 points, 240 identities, seeds,
   populations, rates/rhos, DE parameters, bracket rules, budgets, and banned
   identities.
6. `PROFILE_ONLY` and unauthorized-refusal checks against fresh scratch roots;
   zero scientific calls and no official-root write.
7. Zero-call production bind/load/build/dual-dispatch proof, including an
   explicit L2 oracle-mixer hit and `run_de_call` spy count zero.
8. Exact fresh-root command and unused A2 grant.

Any failure is STOP. Do not fall back to the A1 root or a common L1/L2 sampler.

## 6. Independent batch-end review

The independent reviewer must:

- verify repair provenance, pre-dispatch proof, one-shot A2 grant, fresh root,
  exact command, no retry, and A1 immutability;
- independently recount all 240 rows and confirm profile-specific L1/L2
  sampler dispatch from artifacts/code;
- recompute per-profile/m/population convergence, brackets, flags and
  `delta_DE`; run the read-only verifier;
- confirm D16 remains absent/outcome-blank, banned identities are absent,
  Model-F unchanged, and no decoder/CAL/VAL/real-data path ran;
- check resource ceilings and append `EVIDENCE_ACCESS`, verdict, blockers, and
  findings to the single D17 log.

Review failure blocks use of A2 evidence and grants no rerun.

## 7. Return contract

If A2 completes and review passes, return:

`D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`

Report the exact repair delta; production-chain/L2-dispatch proofs; tests and
repair review; command/exit/timestamps; calls/setup/wall/max-call/RSS/process;
per-profile/m/population convergence; brackets/flags/`delta_DE`; both root
inventories with A1 unchanged; verifier and batch-end verdict; authorization
consumption; no retry/commit/push state.

If implementation, pre-dispatch, execution, or review fails, retain evidence
and return one exact `D17_DE_R2_*_BLOCKED_AWAITING_DECISION` terminal with the
single decision needed.

Do not run the scaling fit, write D16 predictions, run D16, revive D7-H, select
a route, or make FER/leakage/SKR/qualification/optimality/publication claims.
