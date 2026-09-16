# D9 GF32 DE-decoder calibration batch — authorization A1

## 1. Authorization and boundary

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; do not switch.
- Track: `EXPLORE_HEAVY`.
- Required marker:
  `D9_DE_DECODER_CALIBRATION_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- Sending the paired prompt verbatim authorizes exactly one frozen 96-call D9
  calibration invocation.

No production/finite-length decoder, D7-H, CAL/VAL/raw/real data, n1024,
candidate/seed/population change, retry/resume, commit or push is authorized.

## 2. Read first and freeze

Read completely:

- `.workbuddy/tasks/D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`;
- `openspec/changes/v72p2d9-gf32-de-decoder-calibration/**`;
- `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/READINESS_R1.md`;
- `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/EXPLORATION_LOG.md`;
- `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/INDEPENDENT_REVIEW_R1.md`.

Frozen matrix:

- candidates: regular-DV3, lambda2 0.45, 0.50 and 0.55;
- seeds: `2026091601..1603` plus `2026091801..1805`;
- f1.2 primary: populations 4000 and 16000;
- f1.0 boundary diagnostic: population 4000 only;
- V26 parameters otherwise unchanged: max_iter 60, entropy tolerance 1e-4,
  streak 20, entropy/channel-entropy traces on;
- maximum 96 scientific DE calls, deterministic order, no adaptation.

Stability, eligibility, boundary-crossing and rank rules are exactly those in
the accepted OpenSpec/readiness. f1.0 never gates or ranks. D8 remains unchanged.

## 3. Pre-dispatch checks

Append raw outcomes to the existing `EXPLORATION_LOG.md`. STOP without repair
or execution if any fails:

1. accepted readiness marker present and calibration unexecuted;
2. all authorization/promotion flags false or, where no machine store exists,
   recorded authorization state is false;
3. future root absent;
4. accepted Model-F root CAL-only and unchanged;
5. plan introspection gives exactly four candidates, eight seeds and 96 calls;
6. primitive certification still reports `semantics_pass=True` and
   `ensemble_path_equivalence=False`;
7. f1.0 is `BOUNDARY_DIAGNOSTIC`, never an eligibility/rank input;
8. pre-create the task-owned pytest basetemp parent, then run only py_compile
   and the 20 focused D9 tests. Trust C11; no broad suite or D8 rerun.

Mismatch terminal: `D9_DE_CALIBRATION_BLOCKED_PRE_DISPATCH`.

## 4. Exact invocation and budgets

Run once from repository root:

```text
.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py --calibrate --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b
```

Budgets: <=96 DE calls, implemented setup count as recorded and <=12, total
wall <=1200 s, per-call <=300 s checked between/after calls, RSS <2 GiB strict,
single process, no retry/resume/seed extension/adaptive stop.

The per-call cap is not an interrupting watchdog. If a call returns over the
cap, retain the partial root and stop before another call; do not claim an
in-flight kill.

## 5. Carried findings and honest reporting

- F1: distinguish normative realized check-degree bound <=8 from this matrix's
  observed/planned maximum <=4.
- F2/F3: describe the f1.0 role as one effective margin criterion and retain
  Δ_min=0.05 as a design allowance, not an empirical uncertainty bound.
- F4: timing/resource enforcement is between/after calls.
- F5: do not use the unused `allow_partial` argument to turn missing records
  into an eligible result.
- F6: pointer offset is cosmetic and needs no execution edit.

DE uses V26 random nonzero-coefficient ensemble semantics. Nothing here proves
finite-length coefficient-stream, row-layered or decoder-terminal behavior.

## 6. Failure retention

Scientific stable-unconverged, ambiguous, boundary-crossing or select-one
terminals are valid completed EXPLORE outcomes. On crash, nonfinite, resource
breach or incomplete evidence, retain the fresh root and stop. Normal verifier
failure on a partial root must not cause cleanup, repair or rerun. A1 authorizes
no implementation correction and no second scientific invocation.

## 7. Independent batch-end review

After completion or early stop, dispatch one independent reviewer-go with
actual-root access. It must:

- run the read-only verifier and retain raw output;
- independently recount all 96 plan keys, calls and traces;
- recompute S4000/S16000, stability classes, f1.0 boundary crossings, DV3
  comparison, eligibility, deterministic rank and terminal;
- verify reproduction/new-seed partitions and population labels;
- verify primitive-semantics markers and `ensemble_path_equivalence=False`;
- verify budgets, post-call timing semantics, no retry/adaptation and evidence
  completeness;
- apply the exact claim ceiling and report `EVIDENCE_ACCESS`, verdict and
  blocking/non-blocking findings.

Trust a `VERIFIED` reviewer within scope; do not duplicate its calculations for
ceremony. A blocker prevents candidate selection or route advancement.

## 8. Return and authority boundary

Append execution and review to the single log and advance only to:

- `D9_DE_CALIBRATION_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`, or
- an exact `D9_DE_CALIBRATION_BLOCKED_*` state.

Do not self-accept/select a finite-length candidate, create its graph, run a
decoder, revive D7-H, update long-term memory, commit or push.

Return exactly `COMPLETE` or `BLOCKED`, reporting pre-dispatch checks, exact
command/exit, calls/resources/root inventory, per-candidate S4000/S16000 and
boundary diagnostics, stored terminal/eligible/rank output, independent
verdict/findings, authorization false, changed files and no-commit/no-push.
