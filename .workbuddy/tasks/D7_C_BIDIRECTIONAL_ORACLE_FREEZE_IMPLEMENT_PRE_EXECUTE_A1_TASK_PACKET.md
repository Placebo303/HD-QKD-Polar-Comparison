# D7-C heavy readiness Addendum A1 — resolve D7-B interface proposal first

## A1.0 Supersession and reviewed input

This addendum precedes and then resumes:

`D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`

The completed D7-B audit has independent verdict:

`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`

and accepted outcomes:

- primary `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`;
- secondary `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP`;
- current gate `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`;
- decoder hard-decision correctness remains accepted;
- v35 `final_beliefs` honestly returns current log-belief state and makes no
  unconditional promise of syndrome-conditioned posterior;
- D5 cold iteration-0 consumption silently forwards prior-only beliefs as APP.

Therefore R1 §0's deferred-start review gate is satisfied, but D7-C must not
start T1 until the required layer-interface correction proposal is frozen and
independently reviewed. No interface implementation is required before D7-C,
because D7-C constructs its four priors directly from the accepted joint model
and does not consume decoder-returned beliefs across layers.

## A1.1 Main-thread architecture ruling

Freeze these boundaries in the proposal:

1. Do not redefine or patch v35 hard-decision stopping in this task.
2. `final_beliefs` is a current log-belief state, not inherently a calibrated
   syndrome-conditioned posterior.
3. A cold-start return with zero completed check sweeps is `PRIOR_ONLY`.
4. A consumer must not label `PRIOR_ONLY` as syndrome-conditioned APP.
5. Sequential/alternating/joint consumers must carry explicit belief
   provenance before using returned beliefs as cross-layer evidence.
6. `iterations > 0` is sufficient to show at least one check sweep in the
   current cold row-layered decoder, but the durable contract should use an
   explicit provenance field rather than making every consumer infer it.
7. Warm-start provenance is separate and must not be guessed from iterations;
   it remains out of scope until a route actually needs warm starts.
8. D7-C is single-layer oracle diagnosis. It records exact/syndrome/iterations
   and may record current-belief confidence, but must never feed those beliefs
   into another layer or call them conditioned posterior without provenance.

This ruling permits D7-C readiness after proposal review. It does not accept a
specific interface implementation and does not authorize D7-C execution.

## A1.2 Phase P — correction proposal before D7-C

Create OpenSpec proposal:

`openspec/changes/v72p2d7-layer-interface-belief-provenance/`

Create:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md`

The proposal must include:

- the immutable D7-B R2 evidence and 49/15 iteration split;
- the distinction among hard decision, current belief, conditioned belief and
  downstream APP;
- a proposed minimal provenance enum/field with at least `PRIOR_ONLY`,
  `CHECK_UPDATED`, and `WARM_START_UNSPECIFIED`;
- compatibility analysis for v35 `DecoderResult`, D5 adapter and all inventoried
  `final_beliefs` consumers;
- alternatives:
  A. expose provenance only and make consumers fail closed;
  B. force/compute one check sweep when a conditioned APP is required;
  C. keep prior-only fallback but prohibit APP/conditioned claims;
- recommendation and concrete acceptance tests, without implementation;
- explicit rule that no historical result is retroactively changed;
- rule that implementation is mandatory before the next sequential,
  alternating or joint cross-layer run, but not before D7-C single-layer oracle
  readiness/execution.

Preferred recommendation for proposal review is A as the smallest honest
contract correction, followed by a separately frozen decision on whether a
specific consumer requires B. Do not implement A/B/C here.

## A1.3 Independent proposal review

Use an independent reviewer. It must verify the proposal against v35 and the
complete D7-B consumer inventory, challenge whether D7-C truly avoids the
defective interface, and confirm no production code/decoder/root change.

Allowed PASS verdict:

`D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`

Create:

`D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_REVIEW_R1.md`

under the D7-B cycle directory. If review FAILS/BLOCKS or finds that D7-C uses
returned beliefs cross-layer, STOP and do not begin D7-C.

Commit Phase P docs/OpenSpec/review and the factual gate transition separately,
with all authorization false:

`docs(d7-b): freeze belief-provenance correction proposal before D7-C`

Set the D7-B documented next route to
`D7_C_BIDIRECTIONAL_ORACLE_PACKET_FREEZE_INTERFACE_REWORK_DEFERRED` and record
that interface implementation remains mandatory before any cross-layer APP
route.

## A1.4 Resume the R1 heavy package

Only after A1.3 PASS, execute R1 from its baseline/protected-state audit through
OpenSpec, implementation, C01–C20, independent implementation review and
Pre-EXECUTE.

R1 is amended as follows:

- starting HEAD is the Phase-P commit descending from `212f69ba`;
- H01 requires both the D7-B audit PASS and A1.3 proposal PASS;
- H02 must cite the primary MIXED outcome and show D7-C does not consume
  cross-layer returned beliefs;
- C14 must enforce provenance-aware labels: iteration-0/current beliefs may be
  recorded only as `PRIOR_ONLY_CURRENT_BELIEF`, never posterior/APP;
- D7-C implementation must not import or depend on the future interface-rework
  implementation;
- D7-C Pre-EXECUTE must verify direct four-prior construction and absence of
  `final_beliefs -> other layer` data flow;
- final closeout records two parallel states:
  `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` and
  `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP`.

All other R1 scientific matrix, thresholds, budgets, tests, review, execution
prohibitions and exact ending remain unchanged.

## A1.5 Acceptance items

- A1-01 audited D7-B outcome and gate verified at HEAD descendant of `212f69ba`
- A1-02 correction proposal freezes the eight architecture rulings
- A1-03 alternatives A/B/C and compatibility inventory are complete
- A1-04 proposal selects no hidden implementation or scientific parameter
- A1-05 independent proposal review gives the sole allowed PASS
- A1-06 D7-C direct-prior path is proven independent of returned beliefs
- A1-07 Phase-P commit precedes D7-C OpenSpec/implementation commits
- A1-08 R1 H01–H20 complete with A1 provenance labels
- A1-09 zero decoder/Model-F content/scientific execution and all auth false
- A1-10 no push, protected roots unchanged, R1d/G1/G2 absent/unauthorized

## A1.6 Return

Report Phase-P files/review/commit first, then the complete R1 §12 delta. Include
A1-01–A1-10 and H01–H20. Explicitly state that interface implementation remains
deferred and D7-C does not depend on that interface.

Use the R1 exact ending:

`D7-C bidirectional oracle 已完成冻结、实现和独立 Pre-EXECUTE；尚未授权、未执行，D7-B 根保持 immutable，R1d、G1、G2 均未授权。`

