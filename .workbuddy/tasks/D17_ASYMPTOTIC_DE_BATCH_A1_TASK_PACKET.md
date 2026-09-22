# D17 Current-Channel Asymptotic DE — Batch A1 Task Packet

## 1. Identity and authorization boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Batch: `D17_ASYMPTOTIC_DE_BATCH_A1`
- Track: `EXPLORE_HEAVY` (an `EXPLORE` cost annotation)
- Accepted readiness: `D17_DE_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
- Authority: this packet plus its companion authorized prompt.
- One explicit grant covers one frozen 240-call DE run and one independent
  batch-end review. Authorization is consumed when the command starts.
- This batch does **not** authorize the finite-length fit, D16 prediction
  freeze, D16 execution, decoder execution, route selection, or D7-H.

## 2. Frozen scientific matrix

- Exact current Model-F candidate generator/prior, `GF32`, polynomial 37.
- Profiles and n=128 reference row grids:
  - `L1_L045`: m `{106,110,114,118,122}`;
  - `L1_L055`: m `{116,119,122,124,126}`;
  - `L2_DV3_ORACLE`: m `{89,94,99,104,109}`, true-U1 conditioned.
- Rate axis: `R=1-m/128`; disclosure `d=5m/128`; independent variable
  `delta=d-H_layer`. Derive `rho` from the exact rate using the frozen D9 rule.
- Seeds `2026094201..2026094208`; populations `{4000,16000}`.
- V26 MC-DE kernel through the accepted D9 adapter; `max_iter=60`,
  `tol=1e-4`, streak 20.
- Plan is fixed before binding: `3*5*8*2=240` calls in the implementation's
  deterministic order. No grid extension, binary search, seed search,
  adaptive stop, retry, resume, or scientific repair.
- D16 graph seeds `2026094001..4012`, block seeds `2026094101..4108`, its
  official root, and `workspace/d16_align_20260915_a/` are forbidden inputs.

## 3. Root, command, and budgets

- Model-F root:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- Fresh DE result root:
  `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`
- Execute exactly once:

```bash
.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718
```

- Scientific DE calls exactly 240; setup at most 12.
- Wall at most 1200 s; each call at most 300 s by the implemented
  between-call check; RSS strictly below 2147483648 bytes.
- One CPU process. No production decoder, CAL/VAL, or real-data calls.

## 4. Mandatory pre-dispatch record

Append the following raw evidence to
`docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md` before execution:

1. Main-thread readiness acceptance marker, D17-R207
   `EVIDENCE_ACCESS VERIFIED / PASS_WITH_FINDINGS`, and no blocker.
2. Exact branch; `73c6275b` is an ancestor; scoped D17 code, tests, OpenSpec,
   and cycle documents have no unexplained drift. Preserve unrelated dirt.
3. DE root and D16 official root are absent. Model-F root is present, CAL-only,
   and unchanged.
4. Recompute the channel entropies and all 15 `(profile,m,R,delta,rho)` plan
   points; prove the plan has 240 unique ordered identities.
5. Reconfirm the eight DE seeds are disjoint from every predecessor and every
   banned D16 identity; no fit/validation root is read as DE input.
6. Run `PROFILE_ONLY`: 15 points, 240 planned calls, zero scientific calls,
   counters zero, official roots still absent.
7. Run a live unauthorized refusal on a fresh scratch target: rc2 before root,
   kernel binding, or Model-F load.
8. Run `py_compile` and the 30 focused D17 tests in a fresh writable basetemp
   with `-p no:cacheprovider`. Trust D17-R207 predecessor checks unless a
   concrete conflict appears.
9. Reconfirm exact command, populations, convergence rule, flags, budgets,
   verifier contract, and unused one-shot grant.

Any failure is STOP before the real command. Do not repair the scientific grid,
change seeds/root/rules, run D16, clean unrelated files, or consume the grant.

## 5. Frozen DE reduction

For each profile and population:

- `S_pop = count(H60 < 1e-4)` over the eight frozen seeds.
- Derive the reviewed bracket and `delta_DE` only by the frozen implementation:
  midpoint of the predeclared pop-16000 bracket pair, with its exact
  `DE_BRACKET`, `DE_SOFT_BRACKET`, `DE_ONE_SIDED_LOW`,
  `DE_ONE_SIDED_HIGH`, and `POP_UNSTABLE` semantics.
- Never add or interpolate DE calls. Record full trajectory summaries, but do
  not claim DE-to-row-layered or DE-to-finite-FER equivalence.
- If a profile is one-sided or population-unstable, retain that outcome. It is
  input to the later identifiability decision, not permission to re-grid.

## 6. Independent batch-end review

One independent `reviewer-go` (or explicitly identified independent backup)
with actual artifact access must:

- verify the one-shot grant, exact command, no retry, root inventory, and
  authorization consumption;
- independently recount 240 identities, profile/m/seed/population coverage,
  convergence counts, brackets, flags, and `delta_DE` values;
- recompute rate/delta/rho and confirm current-channel/kernel-adapter identity;
- verify banned D16 seeds/root did not enter and D16 remains outcome-blank;
- run the read-only D17 verifier and check all resource ceilings;
- confirm Model-F was unchanged and no decoder/CAL/VAL/real-data path ran;
- append `EVIDENCE_ACCESS`, verdict, blockers, and findings to the one D17 log.

A review failure blocks use of the DE evidence and grants no rerun.

## 7. Return contract

On reviewed completion return only:

`D17_DE_BATCH_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`

Report command/exit/timestamps; 240/setup/wall/max-call/RSS/process; per-profile,
per-m and per-population convergence counts; brackets, flags and `delta_DE`;
root inventory and verifier; independent verdict; authorization consumption;
no retry/commit/push; D16 root absence and outcome-blank status.

Do not fit the finite-length model, write D16 predictions, run D16, select a
route, revive D7-H, or make FER/leakage/SKR/qualification/publication claims.
