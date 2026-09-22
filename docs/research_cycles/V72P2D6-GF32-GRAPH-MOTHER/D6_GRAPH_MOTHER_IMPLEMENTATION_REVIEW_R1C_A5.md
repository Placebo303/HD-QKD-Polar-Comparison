# D6 graph/mother implementation review R1c-A5 (read-only)

Reviewer: independent re-check pass over landed commit `1f1622a7`
(Track A gate). No files edited during review (this file excepted at
commit time). Independence mechanism: no reviewer tool exists in this
environment; independence is constructed by (i) fresh reads of the landed
diff (never the operator's notes), (ii) re-execution of the 5 A5 gate tests
in a fresh basetemp (`workspace/d6_r1c_a5a6_review_df9628e0bf234010a6d9f80d3b5895c5/a5retest`,
5/5 green), (iii) line-level mapping of every prereg A5-03/A5-06 requirement
to a diff hunk. This review never authorizes execution.

## Scope

`comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
(+62), `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (+221),
`scripts/v72p2d6_graph_mother_development.py` (+137).

## Re-checks (prereg A5-03 items 1-5; A5-06)

1. `audit_extra` exposes `row_degree_min`/`rows_below_degree_2` — hunk
   `@@ -636,6 +636,9 @@` (+2 lines, pure addition; no D5 edit anywhere
   in the commit). PASS.
2. Runner `eligible` is frozen-AND-`row_degree_min>=2` in BOTH
   `build_structures` and `build_structures_parallel` (two identical hunks;
   sequential/parallel consistent). PASS.
3. Build-time fail-closed: violating dispatched prefixes record
   structurally ineligible (verified by
   `test_r1c_a5_ineligibility_propagates_to_selection`: T3 n64 f1.2/square
   ineligible, T-pool eligibility map drops T3, T1 stays). PASS.
4. Dispatch-time guard: `assert_dispatchable_matrices` raises on T3
   violating slices, passes on T1 clean slices; `run_cell` calls it before
   any decoder invocation (fake `_NoCall` proves zero calls/records on
   refusal). PASS.
5. `--verify`: `verify_I1_structure` recomputes I1 from frozen builders;
   historical root resolves to INFO-only (`I1_VERIFY_INFO_SKIP` names
   exactly the 4 T2 scaling groups); post-packet roots PASS/FAIL with
   `FAIL I1-check-degree` gating the exit (both behaviors covered by
   `test_r1c_a5_historical_verify_unchanged_and_schema_stable`, incl.
   byte-identical six files before/after and absent I1 columns). PASS.
6. Builder math untouched: the module diff contains no `_build_*`,
   `build_support`, or `assign` hunks (only `audit_extra` + new I1/execution
   functions). Production `build_support` outputs unchanged (operator part4
   replay + `-03`/`M1-01` identity corroborate). PASS.
7. Execution integrity (A5-06): `execution_block_terminal` maps counted
   crash/nonfinite rows to `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (degree
   substring) else `D6_GRAPH_ATTEMPTED_CELL_INVALID`; placeholders excluded
   (`call_idx>=0` filter at the single call site); wired at the shared
   terminal point so all stages (canary/scaling/confirmation) inherit it,
   overriding science labels while resource blocks (RSS>WALL>CHUNK) still
   govern above. Unit branches (clean/placeholder/degree/other/nonfinite/
   precedence) all asserted in
   `test_r1c_a5_execution_terminal_precedence`. PASS.
8. Packet test-requirement coverage: degree-1 detected, degree-2 boundary
   accepted, degree-0 still zero-row-blocked (test 1); propagation (test 2);
   guard (test 3); precedence branches (test 4); historical unchanged +
   schema stable + post-packet FAIL (test 5). Complete. PASS.

## Findings

- One advisory (non-blocking): integrity-vs-resource precedence
  (resource blocks above integrity) is a documented operator choice the
  prereg does not pin; either order defends the science labels. No change
  requested.
- No blocking finding. Zero rework rounds used.

## Verdict

`D6_R1C_A5_REVIEW_PASS_ELIGIBLE_ONLY_BRANCH` — the I1 gate, the
execution-integrity fix, and their tests are landed and correct;
production builders are unchanged. R1d scope is constrained to the
eligible-only branch by the validity outcome (companion validity review),
not by any defect here.
