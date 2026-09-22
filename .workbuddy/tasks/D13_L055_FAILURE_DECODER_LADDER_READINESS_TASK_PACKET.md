# D13 L055 Failure Decoder Ladder — readiness task packet

## 1. Purpose and authority

Track: implementation/readiness only; future batch is `EXPLORE`.
Predecessor: `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`.

All 56 frozen L055 failures reached iteration 90. Determine whether they are
decoder-dynamics failures before changing the code ensemble. This task
authorizes OpenSpec/code/docs, focused fake tests and no-decoder planning only;
zero scientific calls.

## 2. Frozen diagnostic

Input root (read-only):
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Select exactly its L055 records with `exact=false`: 30 at n128 and 26 at n256.
Preserve graph/block identities, degree tables, coefficients, Model-F prior,
GF32/poly37 and cold initialization. No successful D12 record enters the ladder.

Reconstruct each input and first replay `ROW_LAYERED_90_ALPHA_1`. Every replay
must match the stored baseline fields relevant to exact, syndrome, iterations,
provenance and failure identity. First mismatch blocks all ladder calls.

Then run exactly these three arms on every selected failure:

1. `ROW_LAYERED_360_ALPHA_1`;
2. `ROW_LAYERED_360_ALPHA_0_7`;
3. `FLOODING_360_ALPHA_1`.

Audit and reuse existing D7-X3 row-layered/flooding binders and D12 reconstruction;
do not implement another decoder. CHECK_UPDATED provenance is mandatory. Exact,
syndrome-valid and undetected remain separate. Total scientific ceiling:
56 baseline replay + 56×3 ladder = 224 calls.

For each ladder arm count rescues by width and total. `MATERIAL_RESCUE` means
total rescues ≥12 and ≥4 at each width. `MODEST_RESCUE` means total 3--11 with
at least one rescue at each width. `NO_RESCUE` means total ≤2. Other asymmetric
results are `RESCUE_AMBIGUOUS`. If multiple MATERIAL arms exist, rank by total
rescues, then worst-width rescues, then mean iterations among rescues, then
fixed arm order above.

Terminals: `D13_SELECT_RL360`, `D13_SELECT_RL360_DAMP07`,
`D13_SELECT_FLOOD360`, `D13_MODEST_DECODER_RESCUE`,
`D13_NO_MATERIAL_DECODER_RESCUE`, `D13_DECODER_RESCUE_AMBIGUOUS`, or explicit
engineering/resource blocked. A selected arm requires MATERIAL_RESCUE.

Future root:
`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`.
Budgets: ≤224 scientific calls; ≤8 setup; ≤1800 s wall; ≤120 s/call; RSS
<2147483648 B; one process; no retry/resume/repair/seed search/tuning.

Claim ceiling: frozen synthetic L1 decoder diagnostic only; no ensemble
optimality, forward/L2, FER/leakage/SKR, real data, D7-H or qualification.

## 3. Readiness tasks D1301--D1310

- D1301: create D13 OpenSpec proposal/design/tasks/spec before behavior edits.
- D1302: read-only audit D12 root and freeze the exact 56 identities plus stored
  baseline fields; independently confirm 30/26 and iteration=90.
- D1303: audit/import D12 reconstruction and existing accepted RL/flooding
  binders; record semantic map and reject decoder duplication.
- D1304: implement thin additive selector/replay/ladder/gate/verifier with plan
  built before any binding; first replay mismatch stops later calls.
- D1305: require explicit default-false CLI execution flag and refuse before
  root creation, decoder binding or Model-F load.
- D1306: write a fresh never-overwrite minimal root; verifier independently
  checks selection, replay, calls, rescues, ranking, terminal and budgets.
- D1307: focused fake tests for exact selection, exclusion of successes,
  56+168 accounting, first-mismatch stop, provenance, all rescue boundaries,
  ranking, exact/syndrome/undetected isolation and unauthorized refusal.
- D1308: `py_compile` and focused D13 plus directly affected D12/X3 tests in a
  fresh workspace basetemp; no broad suite absent focused external failure.
- D1309: PLAN_ONLY reconstruction metadata for all 56 with zero decoder calls,
  deterministic identities, input root unchanged and future root absent.
- D1310: independent reviewer-go readiness review with
  `EVIDENCE_ACCESS: VERIFIED`, recomputing selection, frozen replay contract,
  decoder bindings, gates/rank, budgets and no-production boundary; append one
  log/readiness record and perform memory triage.

## 4. STOP and return

STOP on identity/count mismatch, reconstruction ambiguity, missing accepted
decoder binder, predecessor modification, decoder/scientific entry, root
creation, failed review or dirty-file conflict. Do not execute D13, tune damping,
add arms, alter D12, run L2/D7-H, commit or push.

Return `D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION` only
when D1301--D1310 pass with zero scientific calls and no blocker. Otherwise
return the exact blocker with raw evidence and one decision.
