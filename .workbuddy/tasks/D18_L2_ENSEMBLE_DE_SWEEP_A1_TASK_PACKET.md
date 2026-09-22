# D18 Current-Channel L2 Ensemble DE — Sweep A1 Task Packet

## 1. Identity and boundary

- Repository `HD-QKD_Polar_Comparison`; branch
  `formal-ir-v72p1-addendum-clean`; batch `D18_L2_ENSEMBLE_DE_SWEEP_A1`;
  track `EXPLORE_HEAVY`.
- Accepted readiness marker:
  `D18_L2_ENSEMBLE_DE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- This packet plus its prompt grants one Stage-S → mechanical Stage-C sweep
  and one independent review. It grants no manual substitution, second run,
  finite graph construction, or route selection.

## 2. Frozen plan

- Current candidate Model-F, true-U1-conditioned L2 oracle, XOR-centered U2,
  GF32/poly37; corrected D17 R2 sampler only.
- Exactly 21 `lambda={2:x,3:1-x}`, x=0.00..1.00 step0.05; x=0 DV3.
- Grid m `{89,94,99,104,109}`; rho from exact rate; no CE/f axis.
- Stage S: 21 × m{94,104} × seeds4301..4304 × pop4000 = 168.
- Rank `(S94 desc,S104 desc,worstH94 asc,worstH104 asc,id asc)`; select top
  three executable non-DV3 plus DV3.
- Stage C: selected four × full grid × seeds4301..4308 × pops4000/16000.
  Reuse 32 Stage-S overlaps without rerunning; 288 new, 456 total.
- V26 max_iter60, tol1e-4, streak20; no extension/search/retry/resume.
- Eligible iff clean stable `DE_BRACKET`, no refusal, and
  `delta_DE<=0.5077488653656221`. Rank by
  `(delta_DE asc,worstH_hi asc,max_dc asc,id asc)`.
- DV3 must reproduce m94/m99 and `delta_DE=0.5468113653656221`; otherwise
  `D18_L2_DE_BASELINE_DRIFT`.

## 3. Command and budgets

- Model-F: `workspace/v72p2d5_model_f_input/20260907_r1`
- Fresh root:
  `workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901`

```bash
.venv/bin/python scripts/v72p2d18_ensemble_development.py --de-sweep --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901
```

- DE≤456; setup≤16; wall≤1800s; per-call≤300s; RSS<2147483648 bytes;
  one CPU; no decoder/CAL/VAL/APP/L1/real data.

## 4. Mandatory pre-dispatch

Append raw evidence to the D18 exploration log:

1. Acceptance marker plus D18-R108 VERIFIED PASS_WITH_FINDINGS, no blocker.
2. Exact branch and clean scoped D18 paths; preserve unrelated dirt.
3. Root absent; Model-F/D17-A2 present; D16/D17 artifacts unchanged.
4. Recompute 21 candidates, 105/105 feasible, Stage-S168, Stage-C320,
   overlap32, new288, maximum456 without duplicate identities.
5. Prove seeds4301..4308 disjoint; no D16/finite-fit outcome enters DE.
6. PROFILE_ONLY rc0, correct counts, zero calls/bind, root absent.
7. Zero-call production probe resolves corrected L2 oracle sampler; V26 spy0;
   no L1/APP path.
8. Unauthorized refusal rc2 before root/bind/load.
9. `py_compile` and 26 focused tests in a fresh writable basetemp.
10. Reconfirm command, gates/ranks/terminals/budgets/verifier, unused grant.

Any failure is STOP. Do not alter candidates or select Stage C manually.

## 5. Execution behavior

- Persist complete Stage S before computing selection exactly once.
- Persist selected IDs before Stage C. Never call the 32 overlaps twice.
- Call/resource failure stops and retains `D18_L2_DE_ENGINEERING_BLOCKED`;
  no repair/rerun.
- Complete run returns exactly SELECT_ONE, NO_IMPROVING, or BASELINE_DRIFT.
  Terminal is evidence only.

## 6. Independent batch-end review

Reviewer with artifact access verifies one-shot grant/command/root/budgets;
reconstructs feasibility, Stage-S counts/rank/selected four; proves overlap32
not rerun and recounts Stage C/total; recomputes brackets/flags/delta_DE,
baseline drift, eligibility/winner/terminal; proves corrected L2-only sampler
and no APP/L1; runs verifier; confirms inputs unchanged; appends
`EVIDENCE_ACCESS`, verdict, blockers, findings. Failure grants no rerun.

## 7. Return

Return:

`D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`

Include command/resources; Stage-S counts/rank/selection; overlap/new/total;
selected candidates' per-m/pop convergence and brackets; DV3 comparison;
eligible/winner/terminal; root/verifier/reviewer; grant; no retry/commit/push.

Do not run finite L2 graphs, rerun D18, revive D7-H, use APP, run real data, or
make FER/leakage/SKR/qualification/optimality/publication claims.
