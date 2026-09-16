# D7-B easy-regime R1 — Addendum A1: feasible TREE_6

## A1.0 Ruling

This addendum narrowly supersedes §3.3 item 2 of:

`D7_B_EASY_REGIME_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`

The R1 operator correctly stopped before writes because the frozen `TREE_6`
contract was impossible:

- `n=6`, `m=3` gives 9 Tanner vertices;
- row degrees `[2,3,2]` give 7 edges;
- a connected graph on 9 vertices needs at least 8 edges;
- a connected acyclic graph needs exactly 8 edges.

The main thread selects option (b): retain `n=6`, `m=3`, connected, acyclic,
and no isolated variables; revise the row-degree sequence to `[3,3,2]`.

This is a pre-observation feasibility correction. The stopped attempt produced
zero commits, zero file changes, zero decoder calls, zero result roots and no
scientific observations. It does not consume any future D7-B execution
authorization.

All other R1 requirements remain binding. This addendum grants no scientific
decoder execution authority.

## A1.1 Replacement TREE_6 contract

Replace R1 §3.3 item 2 in full with:

> `TREE_6`: `n=6, m=3`, one connected acyclic Tanner graph with row degrees
> `[3,3,2]`, no isolated variable and exactly 8 edges. Freeze the incidence
> pattern, in row order, as:
>
> - check 0: variables `[0,1,2]`
> - check 1: variables `[2,3,4]`
> - check 2: variables `[4,5]`
>
> This has 9 vertices and 8 edges; the two shared variables connect all three
> checks without forming a Tanner cycle. Independently assert connectedness,
> acyclicity, row degrees, no isolated variables and GF32 row rank 3 before any
> decoder dispatch. Use fixed nonzero coefficient rows:
>
> - check 0 coefficients on `[0,1,2]`: `[1,7,13]`
> - check 1 coefficients on `[2,3,4]`: `[29,1,7]`
> - check 2 coefficients on `[4,5]`: `[13,29]`
>
> Exact posterior and MAP must be computed by tree factor elimination / message
> passing verified against a smaller enumerable projection or another
> independent calculation. Do not enumerate all `32^6` assignments. The
> independent exact calculation must not call the production decoder or its
> FFT check update.

The truth vectors and syndromes remain determined by fixture seeds
`2026091200..2026091203` under the R1 construction rules. Priors, schedules,
iteration caps, tolerances, budgets, classifications and claims are unchanged.

## A1.2 Mandatory feasibility tests

Before committing the D7-B preregistration, add a pure structural proof/test
that checks:

1. Tanner vertex count = 9;
2. edge count = 8;
3. row degrees exactly `[3,3,2]` in order;
4. variable degrees exactly `[1,1,2,1,2,1]` in variable order;
5. one connected component;
6. acyclic (`E = V - 1` plus explicit traversal with no back-edge);
7. no isolated check or variable;
8. all listed coefficients nonzero and in `1..31`;
9. independent GF32 rank = 3.

Include a negative test showing the superseded `[2,3,2]`/7-edge specification
cannot satisfy connectedness. This is a specification-regression test; it must
not become a runtime graph search.

If any of items 1–9 fails for the literal replacement topology, STOP and return
the exact calculation. Do not select another topology, coefficient set or seed.

## A1.3 Resume point and permitted work

The prior T0 baseline audit may be reused because the stopped run reported:

- branch and HEAD remained `formal-ir-v72p1-addendum-clean` / `f98dde08`;
- no scoped commit, stage, file edit or result root;
- no decoder call;
- protected roots unchanged;
- all authorization keys false and G2 absent.

Freshly recheck those facts. If unchanged, resume at R1 T1 and execute through
T6. Do not redo broad historical review merely for ceremony.

In the new OpenSpec/prereg/execution packet, record both:

- the superseded impossible R1 tuple and its `7 < 8` proof;
- the accepted A1 replacement and its explicit 8-edge tree proof.

The durable D7-B scientific documents must use only the A1 topology as active.
Do not leave `[2,3,2]` as an alternative dispatch path.

## A1.4 Scope and lifecycle

This addendum changes only one frozen scientific fixture definition plus the
tests and documentation needed to prove it. It does not change:

- the other three structure tiers;
- four prior families or four fixture seeds;
- 64-cell schedule;
- cap ladder or early stop;
- 420-call cap;
- 120/1500/1800-second limits or `<2GiB` RSS rule;
- diagnostic schema;
- terminal priority or acceptance thresholds;
- historical decoder, D7-A oracle, schedule, damping or cold start;
- authorization, R1d, G1, G2, data-role or claim boundaries.

No code or document from the stopped attempt exists to salvage. Follow the R1
allowed paths and commit plan/implementation/reviews in the R1 order. Keep the
pending SOP/workbuddy administrative changes out of all commits.

## A1.5 Additional acceptance items

- A1-01 R1 STOP is recorded as a packet-specification feasibility defect
- A1-02 no D7-B execution authorization was consumed
- A1-03 active TREE_6 row degrees are exactly `[3,3,2]`
- A1-04 active incidence and coefficients match A1.1 literally
- A1-05 all nine feasibility checks pass independently
- A1-06 superseded 7-edge topology is rejected by a regression test
- A1-07 no dynamic topology/label/seed search is introduced
- A1-08 R1 B01–B20 are completed under the corrected contract

## A1.6 Hard stop and return

All R1 hard STOP rules remain active. In addition, STOP if any active document,
code path or manifest still dispatches TREE_6 with `[2,3,2]`, or if the literal
A1 topology fails any feasibility test.

At completion, report A1-01–A1-08 followed by R1 B01–B20. Explicitly state the
old/new edge arithmetic and confirm zero D7-B scientific decoder calls.

Use the R1 §10 return format and exact ending:

`D7-B easy-regime 已完成冻结、实现与独立 Pre-EXECUTE 评审；尚未授权、未执行，R1d 继续暂停，G1/G2 均未授权。`

