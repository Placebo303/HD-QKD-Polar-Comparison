# D6 graph/mother Option C acceptance R1 (main-thread ruling record)

Status: `OPTION_C_ACCEPTED_R1D_FROZEN` (ruling + freeze; not an authorization).
Branch `formal-ir-v72p1-addendum-clean`, base HEAD `85a5551d`.
Prior gate: `D6_GRAPH_MOTHER_R1C_A5A6_COMPLETE_AWAITING_MAIN_THREAD_RULING`.

## 1. Ruling (main thread, NOT re-votable)

From `D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md` (0/10 rules admissible,
`STRUCTURALLY_INFEASIBLE_AS_FROZEN`), the main thread selects **Option C**:

- no SC or M knob lift;
- SC (`T3_SC_DV3_W4`, `T4_SC_DV3_W8`) and accumulator (`M1`, `M2`) families are
  structurally inadmissible as frozen;
- R1d candidate set is exactly `{B0_D5_DV3_NATIVE, B1_D5_DV3_COMMON_LABELS,
  T1_PEG_DV3}`;
- `T2_CYCLE_GREEDY_DV3` remains excluded, recorded only as a rank-bound result
  (square ranks n64 63/62, n128 123/122, n256 246/240);
- no R1c-A2 decoder call or root may be reused as successor evidence.

Evidence schema revision approved for NEW R1d roots only: add `row_degree_min`,
add `rows_below_degree_2`, add an explicit eligible-semantics/schema version
marker (`structure_schema=r1d-v2`, `eligible_semantics=frozen-AND-I1`).
Historical A2 files remain immutable with the old schema.

This ruling authorizes planning, OpenSpec, implementation, tests, independent
code review, and independent Pre-EXECUTE review. It does NOT authorize R1d
decoder execution.

## 2. Rejected options (reasons)

- Option A (SC lift: +1 expansion edge per window-covering variable, degree
  3→4): rejected — changes the variable-degree profile (R2 lift), shifts §6
  selection-key inputs (sumsq/rmax) forcing a selection re-freeze, and reopens
  tuned-repair research the packet explicitly excludes.
- Option B (M lift: degree-3 base pairs allowed into zone rows): rejected —
  weakens the M-over-B identity, shifts selection keys, and likewise reopens
  repair research with a re-freeze requirement.
- Both would convert R1d from "does valid T1 improve over controls" into a new
  repair program. Option C needs zero science change and zero re-freeze.

## 3. R1d question (only)

> Under the unchanged E2 prior, decoder, rows, seeds, schedule, and thresholds,
> does the structurally valid T1 PEG mother improve over B0/B1 controls without
> invariant failures?

B0/B1 are controls and cannot win advancement. T1 is the sole new arm.
Scaling fallback, if reached, is T1 only (no eligible M arm exists under I1).

## 4. R1d cell schedule × validity proof (§3 gate)

Unchanged schedule per prereg §8, restricted to the Option C set. Roles:
canary seeds `2026091000..03` (mandatory, points f1.2+square);
confirmation seeds `2026091010..25` (conditional on T1 advancement, points
f1.0/f1.2/square); scaling seeds `2026091100..03` (conditional on n64 silence,
T1 only, points f1.2+square, stop at first signaling width).
Prefixes: n64 L1 (49,59,64) / L2 (43,52,64); n128 L1 (98,118,128) /
L2 (86,104,128); n256 L1 (196,236,256) / L2 (172,208,256).

Every distinct `(arm,n,layer,prefix)` below is `frozen_eligible=True` AND
`i1_pass=True` (`new_eligible=True`) in the accepted
`D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv` (144 rows). Checked 2026-09-10 by direct
CSV read (zero decoder): **26/26 pass, 0 conflicts** — no STOP, no dropped or
replaced rows/seeds/gates.

| arm | n | layer | prefix_rows | role | frozen/I1 | new | rmin | nbelow |
|---|---|---|---|---|---|---|---|---|
| B0 | 64 | L1 | 59 | canary | True/True | True | 3 | 0 |
| B0 | 64 | L1 | 64 | canary | True/True | True | 3 | 0 |
| B0 | 64 | L2 | 52 | canary | True/True | True | 3 | 0 |
| B0 | 64 | L2 | 64 | canary | True/True | True | 3 | 0 |
| B1 | 64 | L1 | 59 | canary | True/True | True | 3 | 0 |
| B1 | 64 | L1 | 64 | canary | True/True | True | 3 | 0 |
| B1 | 64 | L2 | 52 | canary | True/True | True | 3 | 0 |
| B1 | 64 | L2 | 64 | canary | True/True | True | 3 | 0 |
| T1 | 64 | L1 | 59 | canary | True/True | True | 2 | 0 |
| T1 | 64 | L1 | 64 | canary | True/True | True | 2 | 0 |
| T1 | 64 | L2 | 52 | canary | True/True | True | 2 | 0 |
| T1 | 64 | L2 | 64 | canary | True/True | True | 2 | 0 |
| T1 | 64 | L1 | 49 | conf | True/True | True | 3 | 0 |
| T1 | 64 | L1 | 59 | conf | True/True | True | 2 | 0 |
| T1 | 64 | L1 | 64 | conf | True/True | True | 2 | 0 |
| T1 | 64 | L2 | 43 | conf | True/True | True | 3 | 0 |
| T1 | 64 | L2 | 52 | conf | True/True | True | 2 | 0 |
| T1 | 64 | L2 | 64 | conf | True/True | True | 2 | 0 |
| T1 | 128 | L1 | 118 | scal | True/True | True | 2 | 0 |
| T1 | 128 | L1 | 128 | scal | True/True | True | 2 | 0 |
| T1 | 128 | L2 | 104 | scal | True/True | True | 2 | 0 |
| T1 | 128 | L2 | 128 | scal | True/True | True | 2 | 0 |
| T1 | 256 | L1 | 236 | scal | True/True | True | 2 | 0 |
| T1 | 256 | L1 | 256 | scal | True/True | True | 2 | 0 |
| T1 | 256 | L2 | 208 | scal | True/True | True | 2 | 0 |
| T1 | 256 | L2 | 256 | scal | True/True | True | 2 | 0 |

Worst-case decoder budget: canary 3×4×2×3=72 + n64-confirm 1×16×3×3=144 +
scaling 2 widths ×(1×4×2×3=24) + scaling-confirm 2×144 = 552 ≤ 2500.
Fail-closed reference cell (invalid by I1): `T3_SC_DV3_W4` n64 L1 k59
(frozen True, I1 False, rmin 1, nbelow 10) — MUST refuse pre-decoder-binding.

## 5. Terminal priority (landed, A3/A5, reused unchanged)

Any attempted non-placeholder (`call_idx>=0`) crash/nonfinite cell forces
`D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (degree `ValueError`) or
`D6_GRAPH_ATTEMPTED_CELL_INVALID` (other), overriding recovery/no-recovery
classification; placeholders never count; stored vs recomputed terminals
reported with the agreement flag (recomputed governs).

## 6. Claim ceiling

At most: T1-vs-controls APP-exact comparison under the frozen contract with
I1-gated dispatch, plus the no-reuse and schema-version facts. No SC/M/T2
claim, no recovery claim beyond the registered terminals, no performance claim
beyond measured structure costs, no authorization claim. Mandatory independent
Pre-RESULT review before any result solidification.
