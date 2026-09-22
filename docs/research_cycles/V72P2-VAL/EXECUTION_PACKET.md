# V72P2-VAL frozen operator packet

## Scope and ownership

Root/main owns OpenSpec, scientific decisions, review, authorization records. luna_worker owns only the four Python files below, focused test execution and later the explicitly released real invocation. Do not edit concurrently owned files, unrelated untracked evidence or Git branches/worktrees. Preserve baseline cd0b0e77c5cedbf3ac74d271cff3d6649f7043fc and accepted V72P1 evidence.

Read all four OpenSpec files in openspec/changes/formal-ir-v72p2-val-descriptive-smoke/. This packet plus that design is the full frozen contract; do not invent alternative priors, new graph optimizations, generators, datasets or numerical thresholds.

## Exact manifest

Worker code changes:
1. NEW scripts/v72p2_real_smoke.py
2. NEW test_v72p2_real_smoke_small.py
3. MODIFY comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py: only run_decoder final readout and first-iteration residual/docstring.
4. MODIFY test_v72p1_soft_joint_adapter_small.py: only the changed final-snapshot assertion in test_T_DATAFLOW_4 and explanatory comment; no weakened tests or timing thresholds.

Main-owned records: the four new OpenSpec files; this cycle's REVIEW_ENTRYPOINT.md, EXECUTION_PACKET.md, REVIEW_VERDICT.md, cycle_state.yaml; post-review OPERATOR_RETURN.md and RESULT_SUMMARY.md. After result acceptance, memory triage may append AGENT_PROJECT_MEMORY.md only. No decision-log rewrite.

Output (only after released Pre-EXECUTE): comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903/ containing manifest.json, results.json, table.csv, report.md. Directory must be absent before the invocation; no run_01. No other production output. Scratch tests: fresh workspace/v72p2_tests/<unique>/; preserve failed test evidence. stdout progress is allowed and should report block completion without raw symbols/tags.

Forbidden: original src/, experiments/, tools/, results/, existing outputs, V70/V71/V72P0 code, accepted V72P1 docs, any raw data mutation, other sources/TEST/2M, new dependencies, SHA/MD5 artifact hashing or schema framework. Existing64-bit reconciliation tag is reused as specified; no universal-hash/security claim.

## Implementation details

CLI: python scripts/v72p2_real_smoke.py --registry v71_data_registry.json --out-dir comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903 --execute-real
No real execution on import or without --execute-real. Fake tests explicitly inject fake decoder; library helpers do not silently launch production work. Resolve data path from registry relative to repository, not a new absolute-path default. Read only the one registered1M file, selecting CAL and fixed36VAL frames (predicate pushdown where supported); do not call historical main() or fit other sources. Registry remains unchanged; new manifest explicitly declares V72P2 data roles and IDs.

Use existing V70 select_lambda/hierarchical_P. Input validation must catch realistic missing/duplicate pair/frame/symbol errors, not build a generalized verifier. Model probabilities lower-bounded1e-300 then normalized, natural log for BP. selected CAL-CV CE is model-relative reference; report all lambda CV scores for reproduction, no VAL-driven choice. Numerical parameters/checkpoints/mother preserved.

Real decoder function signature is run_decoder(prior_logp,syndrome_target,indptr=None,indices=None,max_iter=10,warm_start_c2v=None), dictionary return. get_mother_csr returns (indptr,indices,nnz_integer). Reuse caller prefix slices and count len(ret['residuals']). Keep returned v2c as last-transmitted data, final c2v-derived factor/APP readout as specified.

Per checkpoint scalar evidence: rows/new_rows/cumulative counters, iterations/total_iterations, residuals/converged/finite/max_llr, syndrome_ok/tag_checked/tag_ok/protocol_accepted, elapsed time. Do not store message arrays in logs. Per-block offline raw/final symbol/bit errors and oracle_exact are allowed as aggregates only after stopping.

Budgets: seed20260902 for synthetic tests, max10/checkpoint720/block; soft600s/block and7200s/invocation measured via monotonic and checked before/after checkpoint. No posthoc budget revision; report overruns. Bad CAL/preparation stops without decoder; invalid smoke slot continues with INVALID_INPUT, no substitute. Numeric/decoder error/resource halt stops invocation and remaining slots are NOT_ATTEMPTED. Ordinary ladder_exhausted proceeds through9. Exit0 means completed bounded experiment, NOT correction success. Incomplete/error => nonzero with retained four artifacts. No auto rerun.

## Tests and release sequence

T0 command: python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py scripts/v72p2_real_smoke.py test_v72p2_real_smoke_small.py test_v72p1_soft_joint_adapter_small.py

T1/T2 command: pytest -p no:cacheprovider test_v72p2_real_smoke_small.py test_v72p1_soft_joint_adapter_small.py --basetemp workspace/v72p2_tests/<unique>/pytest

Implement all T1-A..F from tasks.md. Explicitly test invalid seventh frame no substitution, true warm delta/current readout, final legal iteration acceptance, zero budget zero communication, undetected isolation, failed-disclosure accounting and strict prefix CSR/new edges. Apply the design's explicit main-review timing amendment:29 tests and independent P1C numerical/structural checks must pass; retained historical1.046s/<1s failure alone is non-blocking and must not be relabeled PASS. Do not change historical thresholds or kernel. No real output until main review.

Root records plan acceptance and accepted_plan_sha in the next milestone after the plan commit. Worker may perform exact-add plan/implementation commits and ordinary pushes ONLY when instructed by root. Before any push check git diff --check, cached manifest, branch and HEAD. Never git add -A/stash/reset/switch/clean.

After code review/tests, commit/push the implementation candidate and verify exact HEAD==remote==implementation SHA. Root then writes the Pre-EXECUTE checklist and authorization into these cycle documents before releasing execution. Only these reviewer-owned documentation records may be uncommitted; all executable task files must match the reviewed commit. The release message specifies that exact implementation SHA; runtime manifest captures git rev-parse HEAD and plan commit from cycle state. This avoids self-SHA recursion; review records are committed with the subsequently reviewed result. Old template SHA search is scoped to this cycle/change, not historical docs.

Only then run the above command once. Return exact command/exit, output path and concise status without selfacceptance. Root independently performs Pre-RESULT on artifacts before any output commit or scientific result publication. Memory triage then exact-add four accepted artifacts + records; ordinary push. Stop at V72P2, no V73.
