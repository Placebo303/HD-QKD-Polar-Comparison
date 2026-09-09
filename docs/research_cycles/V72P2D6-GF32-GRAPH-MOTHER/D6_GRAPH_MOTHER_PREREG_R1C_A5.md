# D6 graph/mother — preregistration R1c-A5 (validity closure, admissible repair, R1d readiness)

Status: `FROZEN_PREREG_R1C_A5`. Branch `formal-ir-v72p1-addendum-clean`, base `1a09220a`.
Predecessor gate `D6_GRAPH_MOTHER_R1C_A3_BLOCKED_AWAITING_MAIN_THREAD_ROUTE` (R1c-A3 `PASS_BLOCKED_RUN`, stored topology unsupported, 184 calls zero reuse; R1c-A4 `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` structure path only). Zero decoder calls in A5 (structure-only, production gate code, fake-only tests, docs). No `--phase`/G1/G2/VAL/real/raw/new sample. No R1d execution/rerun/resume. No six-file schema landing (proposed only in readiness package).

Frozen science carried forward verbatim: 8 arms, seeds by role, row budgets/prefixes, E2 prior, historical decoder/schedule/damping, coefficient stream `(n,layer,column,edge_index)` seeds L1 `202609120100+n` / L2 `202609120200+n`, SC widths 4/8, M `N2` rules, two-zone split, selection/advancement/ordering, terminals thresholds, budgets 2500 calls / 12h / 120s / RSS <2GiB / no retry. Frozen knobs, T2 key/order/candidate/greedy, float-approx/top-K prohibitions per mother packet §2.

## A5-01 independent validity matrix (own implementation, no import of main-thread artifact)

Cover every arm x {64,128,256} x {L1,L2} x every frozen prefix + T2 n128/n256 structure-only. Per cell: `row_degree_min`, rows degree<2, row-degree histogram, `variable_degree_min`, rank, zero rows/cols, components, largest-component fraction, duplicate projective columns, base-pair/triple duplicates, M degree-2 cycle rank, girth/`NOT_COMPUTED`, determinism replay, frozen `eligible`. Deliver `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv` + human table in `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.md`. Cross-check main-thread `workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/` only after; report disagreement. Acceptance A5-A01/A5-A02: matrix complete/reproducible; frozen `eligible` + A2 five-arm `{B0,B1,T1,T3,M1}` reproduced exactly.

## A5-02 root cause + decoder precondition inventory

Code-independent proof + structure-only rebuild per family (A3 style): T3/T4 uncovered rows in `[k_min,m_max)`; M1/M2 forced by frozen `N2` + two-zone split + forest; T2 n64 rank 63/62; B0/B1 n128-L2 base-pair dup + n256 disconnection (controls, must not be modified, dispatchable-set bounds). Decoder precondition inventory maps every historical decoder/adapter structural precondition to frozen gate or I1, closing the gate-gap class.

## A5-03 invariant I1 (production, fail-closed)

I1 (frozen): every dispatched `(arm,n,layer,prefix)` has every check row degree >=2, plus all frozen hard gates. (1) D6 `audit_extra`: compute `row_degree_min`/`rows_below_degree_2`, expose. No D5 edits. (2) Runner `eligible`: frozen condition AND `row_degree_min>=2`. (3) Build-time fail-closed: violating dispatched prefix => structurally ineligible, never dispatchable. (4) Dispatch-time guard: no decoder cell from violating matrix; fail-closed error. (5) `--verify`: independent I1 recompute over `structure_records.csv`; historical root INFO (predates gate), post-packet roots PASS/FAIL. Never rewrite historical root/fields. Fake-only tests (task basetemp): degree-1 detected, degree-2 boundary accepted, degree-0 still zero-row blocked, ineligibility propagates to selection, guard refuses dispatch, historical six-file root verifies unchanged, diagnostic not persisted into frozen schema. Acceptance A5-A03/A5-A04/A5-A05.

## A5-04 admissible repair study (sandbox only, no decoder)

Admissibility R1-R5 per mother packet §3.4 (determinism/prereg ≤3 rules per family, frozen knobs, full-matrix I1+gates, no new defects, exact diff disclosure). Order frozen: fewest changed support entries, then lower max row degree, then rule ID. No decoder criterion. Sandbox module/section only; production `build_support` byte-identical every `(arm,n,layer)`. If no R1-R5 rule: `STRUCTURALLY_INFEASIBLE_AS_FROZEN` + proof + redefinition menu (<=3, knob change + consequences + minimality) marked `REQUIRES_MAIN_THREAD_RULING`, not landed. Preregistered candidates (uniform per family, frozen coefficient stream, no seed search):

- T3_SC_W4: R-T3-01 windowed least-degree with degree-1-risk global overflow; R-T3-02 reverse variable order same windows; R-T3-03 base-window + expansion least-degree-in-window with triple-skip priority swapped (still windowed, w=4).
- T4_SC_W8: R-T4-01/02/03 mirrors of T3 with w=8.
- M1_MAX: R-M1-01 degree-3 base-pair global least-degree with chain fixed; R-M1-02 expansion least-degree with base-pair order swapped. (Counting proof predicts infeasibility: expansion-only rows need 2*(m-k) edges, only (m-k+1) expansions exist.)
- M2_HALF: R-M2-01/02 mirrors of M1.
- T2 rank: no admissible rule (key/order frozen); recorded as bound unless a key-preserving rank fix emerges (none preregistered).
- B0/B1: no repair (controls).

Deliverable `D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md` + matrix/CSV. Acceptance A5-A06/A5-A07/A5-A08.

## A5-06 execution-integrity terminal (land, tests only)

Any attempted non-placeholder crash/nonfinite cell forces `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (degree invariant) or `D6_GRAPH_ATTEMPTED_CELL_INVALID` (other), overriding recovery/no-recovery; `call_idx=-1` never counts; historical root never re-run/rewritten, verify still stored-vs-recomputed + agreement. Fake-only canary/scaling/confirmation tests. Acceptance A5-A11/A5-A12.

## A5-10 structure-cost guard

Fresh-root structure builds at every dispatched width (zero decoder), project vs chunk `>=5400s` dispatch block + 12h wall. Breach => route to Track B numbers or declare width-inadmissible with structural reason. Acceptance A5-A18.

## A5-08 R1d readiness (no execution, no authorization)

`D6_GRAPH_MOTHER_R1D_READINESS_R1C_A5.md` marked `NOT_AUTHORIZED / REQUIRES_MAIN_THREAD_RULING_AND_AUTHORIZATION`: candidate set (controls + repaired families + eligible-only branch), required validity matrix, unchanged science, schema change as approval-required list, crash-precedence semantics, no-reuse rule, Pre-EXECUTE checklist (output-root absence, auth keys, G2 absence, protected-root metadata, test set, exact command), claim ceiling. `cycle_state.yaml` `next_gate` only; all auth false; evidence_root/terminal null. No R1d root. Acceptance A5-A14/A5-A15.

Stop: ambiguity => STOP; production test failure => STOP; one rework per review max; forbidden per mother packet §2.
