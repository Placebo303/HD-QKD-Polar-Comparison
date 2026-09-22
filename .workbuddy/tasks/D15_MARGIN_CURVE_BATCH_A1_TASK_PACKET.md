# D15 Paired Finite-Length Margin Curve — Batch A1 Task Packet

## 1. Identity and track

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Batch: `D15_MARGIN_CURVE_BATCH_A1`
- Track: `EXPLORE`
- Accepted readiness:
  `D15_MARGIN_CURVE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
- This packet freezes one run and one batch-end review. It grants no execution
  without the separate explicit user prompt.

## 2. Frozen scientific matrix

- n=128; unchanged candidate concentration-backoff generator/prior.
- L1 load `548.700215065776` bits; L2 load `412.508145233200` bits.
- Three matched row points:
  - point 0: L1 m110 / L2 m83;
  - point 1: L1 m114 / L2 m86;
  - point 2: L1 m118 / L2 m89.
- Effective-factor gaps L2−L1 are approximately
  `0.00367/0.00359/0.00350`; recompute rather than round for grading records.
- Arms: L1 L045, L1 L055, L2 DV3 ORACLE. There is no APP or transfer arm.
- L045 variable 71/57/E313; checks:
  m110 `2^17+3^93`, m114 `2^29+3^85`, m118 `2^41+3^77`.
- L055 variable 83/45/E301; checks:
  m110 `2^29+3^81`, m114 `2^41+3^73`, m118 `2^53+3^65`.
- L2 variable `3^128`/E384; checks:
  m83 `4^31+5^52`, m86 `4^46+5^40`, m89 `4^61+5^28`.
- Graph seeds are the exact nine four-seed sets `2026093801..3836` assigned
  per cell in the accepted manifest. Block seeds `2026093901..3908` are shared
  across all nine cells. Wrong-cell seeds are forbidden.
- Plan order: point ascending; L045, L055, L2_ORACLE; graph ascending; block
  ascending. Exactly 9×4×8=288 decoder calls, call_idx 0..287.
- L2 ORACLE is true-conditioned, diagnostic and ungraded. Exact/syndrome/
  undetected remain isolated. No predecessor records enter the gates.

## 3. Root, command and budgets

- Model-F input:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- Fresh result root:
  `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`
- Exact authorized command, once:

```bash
.venv/bin/python scripts/v72p2d15_margin_curve_development.py --d15-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2
```

- Scientific calls: exactly/at most 288.
- Setup: exactly/at most 46 (=36 graphs + 8 blocks + 2 plan/manifest).
- Wall ≤1800 s; each call ≤120 s; RSS strictly <2147483648 bytes.
- One foreground CPU process; no retry, resume, repair, seed search, tuning,
  adaptive stop or second invocation.

## 4. Pre-dispatch checks

Append raw evidence to the D15 exploration log before execution:

1. Accepted readiness marker and D15-R1510 VERIFIED review, no blocker.
2. Exact branch; commit `614a0e81` is an ancestor; scoped D15 implementation
   paths have no unexplained drift. Preserve unrelated dirt.
3. Official result root absent; Model-F root present, CAL-only and unchanged.
4. Recompute both entropy loads, all six effective factors, three pairing gaps,
   and nine socket tables; exact agreement with the accepted spec.
5. Reconfirm all 36 seed-to-cell assignments, eight shared block seeds, 288
   identities and no overlap with predecessor seed sets.
6. PROFILE_ONLY: 36/36 A1–A6 admitted, zero replacements, 288 plan, setup 46,
   decoder 0 and official root still absent.
7. Production adapter/signature probe resolves the accepted L1 and true-L2
   oracle helpers with zero calls and no Model-F load. Static/runtime proof shows
   no APP or transfer path.
8. Live unauthorized refusal against a fresh scratch target: rc=2 before
   root/bind/load.
9. `py_compile` and 25 focused D15 tests in a fresh writable basetemp. Do not
   treat D14N tests that require its now-materialized root to be absent as D15
   failures; rerun predecessor tests only if a focused D15 conflict appears.
10. Reconfirm exact command, matrix, terminals, budgets and unused one-shot
    authorization.

Any failure: STOP before the authorized command and report raw evidence. Do not
repair, substitute the root, alter a row/seed/threshold, or clean unrelated data.

## 5. Frozen classification

Per cell, using its four per-graph exact counts:

- ADEQUATE iff pool ≥24/32 and at least two graphs are ≥6/8.
- WEAK iff pool ≤16/32 and at least two graphs are ≤4/8.
- Otherwise the cell is MIDDLE.

Report monotonicity over increasing rows for each arm. Any decrease is retained
and prevents monotonicity-dependent claims; never smooth or repair it.

First-match terminal priority:

1. engineering/resource violation → `MARGIN_CURVE_ENGINEERING_BLOCKED`;
2. both L1 high-point cells weak, L2 high adequate, L1 monotonic →
   `MARGIN_CURVE_L1_SPECIFIC`;
3. L2 high weak, both L1 high adequate, L2 monotonic →
   `MARGIN_CURVE_L2_SPECIFIC`;
4. all low cells weak, all high cells adequate, all arms monotonic →
   `MARGIN_CURVE_FINITE_BACKOFF`;
5. all nine cells weak → `MARGIN_CURVE_BOTH_WEAK`;
6. otherwise → `MARGIN_CURVE_AMBIGUOUS`.

Wilson intervals and paired L045/L055 discordances are descriptive only and
never gate. Do not fit a threshold from three points. Stored terminal is evidence
awaiting main-thread route adjudication.

## 6. Independent batch-end review

One independent reviewer with actual artifact access shall:

- verify exact one-shot authorization, command, root inventory and no retry;
- independently recompute loads/factors/gaps, all 36 admissions, seeds,
  identities, call/setup accounting and resource limits;
- recount exact, syndrome and undetected per cell and graph;
- verify L2 records are ORACLE/ungraded and no APP/transfer path ran;
- recompute ADEQUATE/WEAK/MIDDLE, monotonicity, first-match terminal, Wilson and
  paired descriptive values;
- run the read-only verifier and confirm Model-F/predecessor roots unchanged;
- record `EVIDENCE_ACCESS`, verdict, blockers and findings in the single log.

Review FAIL blocks use of the evidence and grants no rerun.

## 7. Return contract

On reviewed completion return:

`D15_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`

Report exact command/exit/timestamps; 288/46 accounting; wall/max-call/RSS/
process; all nine cell totals and four-graph vectors; syndrome/undetected;
monotonicity; cell classes and terminal; descriptive intervals/discordances;
root inventory; verifier/reviewer verdict; authorization consumption; changed
files; no retry/commit/push; claim boundary and remaining route decision.

Do not commit/push batch results, revive D7-H, execute real data, or make FER,
leakage, SKR, qualification, optimality, publication or final route claims.
