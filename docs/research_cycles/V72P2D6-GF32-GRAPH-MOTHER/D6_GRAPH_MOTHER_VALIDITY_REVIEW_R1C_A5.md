# D6 graph/mother validity review R1c-A5 (read-only)

Reviewer: independent re-check pass over the Track A evidence
(`D6_GRAPH_MOTHER_VALIDITY_R1C_A5.md/.csv`,
`D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md/.csv`,
`D6_GRAPH_MOTHER_R1D_READINESS_R1C_A5.md`, commit `fda539b`).
No files edited during review (this file excepted at commit time).
Independence mechanism: fresh recomputation with a newly written script
(`workspace/d6_r1c_a5a6_review_df9628e0bf234010a6d9f80d3b5895c5/
review_recompute.py`, sharing no code with the operator harness) plus
direct reads of the committed CSVs against the prereg text. This review
never authorizes execution; the readiness package stays `NOT_AUTHORIZED`.

## Re-checks

1. Sampled cells recomputed (6 cells: T3 n64-L1-k59, M1 n64-L2-k52,
   T1 n256-L2-square, B0 n128-L2-k86, M2 n256-L2-square, T4 n256-L1-k236):
   `row_degree_min`, `rows_below_degree_2`, rank, frozen `eligible`, and
   I1 verdict all match the matrix. 6/6 PASS.
2. Main-thread cross-check claim re-verified: the 12 T2 n128/n256 cells are
   absent from `row_degree_audit.csv` (NOT_DISPATCHED design), all other
   132 cells agree — the "zero disagreement" statement holds on the shared
   set; the extension is labeled, not smuggled. PASS.
3. A5-A02 re-verified: frozen-eligible map recomputed from the CSV equals
   the committed `selected_arms.json` map on all 8 arms; T-rank order
   (T1<T3<T4) and selection {B0,B1,T1,T3,M1} reproduce it. PASS.
4. Per-family proofs re-checked: M1 counting bound re-derived numerically
   at 4 (n,layer) points (observed below-degree-2 counts 14/20/29/83 vs
   zone-1 bounds 14/20/29/83 — equality at every re-derived point, and at
   all 6 cells per the validity doc); T3/T4 single-hit mechanism and M2 tail-starvation match the
   matrix's exact degree-1 row sets; T2 square ranks (63/62, 123/122,
   246/240) confirmed in-CSV; B0/B1 bounds (n128-L2 dup, n256 f1.0
   disconnection, B0 n256-L1-square rank 255) confirmed in-CSV. PASS.
5. Repair admissibility re-audited rule by rule from the matrix CSV against
   prereg R1-R5: R1 replay holds 10/10; R3 (I1 AND gates at all 6 cells)
   fails 10/10 — re-derived verdict agrees with every stored
   `admissible=False` (60/60 cells, 10/10 rules). The frozen evaluation
   order is correctly reported moot. Identity finding (`-03`/`M1-01`
   changed-entries 0) confirmed in-CSV. PASS.
6. `STRUCTURALLY_INFEASIBLE_AS_FROZEN` follows: no rule passes R3, and the
   M1 bound proves no R2-compliant rule can (for M1); the menu has exactly
   3 options, each naming its knob lift, consequences, and minimality, all
   marked `REQUIRES_MAIN_THREAD_RULING`, none landed. PASS.
7. Sandbox/production separation: production builders byte-identical
   (replay evidence + untouched-builder diff in the implementation review);
   sandbox confined to its module; T1/B0/B1 I1-clean everywhere in-CSV.
   PASS.
8. Readiness package: NOT_AUTHORIZED marking present; candidate branches
   (lift-or-eligible-only) match the study outcome; no-reuse rule,
   crash-precedence semantics, approval-required schema list, Pre-EXECUTE
   checklist, and claim ceiling all present and consistent with the
   evidence; `cycle_state.yaml` advanced `next_gate`-only with all auth
   false and evidence_root/terminal null (diff-checked). No R1d root
   exists. PASS.

## Findings

- One advisory (non-blocking): the M2 story is ordering-empirical rather
  than counting-exact (unlike M1); the infeasibility verdict for M2 rests
  on preregistered-rule exhaustion, which is what the packet asks for. No
  change requested.
- No blocking finding. Zero rework rounds used.

## Verdict

`D6_R1C_A5_REVIEW_PASS_ELIGIBLE_ONLY_BRANCH` — validity closure is proven
and reproduced; repair is infeasible as frozen with a ruled menu awaiting
the main thread; the only R1d-viable path without a ruling is the
eligible-only {B0,B1,T1} branch, itself not authorized here.
