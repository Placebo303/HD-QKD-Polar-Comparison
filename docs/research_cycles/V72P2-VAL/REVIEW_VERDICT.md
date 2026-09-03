# V72P2 main review record

## Plan preparation, 2026-09-03

Main independently inspected the accepted V72P1 source/records, four OpenSpec artifacts, SOP and adapter code; luna_worker independently inspected prior/data registry and source existence without reading parquet. Live git ls-remote confirms base cd0b0e77c5cedbf3ac74d271cff3d6649f7043fc; tracked diff was empty before this new plan.

The bounded proposal follows the user's plan/execute delegation. Two successor corrections are explicit: first warm residual previously used magnitude; returned run_decoder APP previously used pre-update sums. Historical V72P1 acceptance is preserved as historical evidence, not proof these new semantics were already tested. No other algorithm optimization is included.

Awaiting plan commit binding. Implementation and real execution are not yet released. The main reviewer will record acceptance of this exact plan in the next milestone; the worker cannot selfaccept.

## Plan acceptance, 2026-09-03

Target plan SHA: a97b23cee38a83d32ad67cd56d6c722b7e8e3de6.
Main independently verified live remote equals local HEAD at this SHA following the user's explicit "允许推送并继续" authorization. Eight-file plan manifest only; no real data included. Verdict: PLAN_ACCEPTED for the bounded design and packet. Prior/CAL separation, fixed36VAL IDs, actual iteration accounting, current-candidate verification, monotonic disclosure and narrow adapter correction have been reviewed against source.

Release: luna_worker may implement the four listed Python files and run the frozen synthetic/fake tests. Real-data decoding remains unreleased until main Pre-EXECUTE. Acceptance here is the main reviewer's decision under the user's delegation, not an operator self-PASS. This record will be committed with the implementation candidate, per packet.

## Candidate review and explicit timing amendment

Main read the runner, focused tests and adapter diff. An operator's out-of-scope _factor_batch_numba optimization was discovered and removed; the final adapter diff is restricted to run_decoder (23 added/4 removed). The optimized diagnostic timing is excluded. Completed-iteration accounting on numeric failure and nonzero cross-block-reset tests are included. T0 compile/diff-check exit0; combined regression exit1 with29 passed/1 failed in66.77s. The failure is solely historical P1C one-iteration1.046s versus <1s, not the overall50.891s versus a30s bound. Actual three/ten-iteration1.297/1.313s pass. Main independently parsed workspace/v72p1_rework_tests/9651abe2/v72p1_results.json: finite/nonzero/hard_bits_ok/ck_ok true,72 checkpoints,144 total iterations; residuals and maxLLR finite/in bounds.

Main approves the explicit V72P2 plan amendment under AGENTS first principle: preserve and disclose that timing regression, keep all numerical gates and real deadlines, no optimization/timing-success claim. The old test remains FAILED. The corrected final readout requires additional local-factor work. Plan amendment and candidate code will be bound to their new committed SHA before any real read/decoder invocation. Pre-EXECUTE remains pending.

## Amended-plan acceptance and Pre-EXECUTE PASS, 2026-09-03

Main independently verified live git ls-remote and HEAD both equal b33664d00b5b22a02b61df95b00c99ae0a0368b8 on formal-ir-v72p1-addendum-clean. This commit contains the explicit amendment and reviewed implementation; accepted_plan_sha and implementation_sha both bind this commit. Original plan a97b23ce is retained as historical original_plan_sha, not the execution contract. The committed manifest is exactly11 task files. Tracked working tree was clean before these reviewer-owned records; executable files remain identical to this commit.

Checklist:
- User authorization: direct instruction to plan and execute V72 through luna_worker, bounded by the accepted nine-block packet; subsequent explicit approval of pushes of code/tests/plans/compact results to this repository/branch, excluding raw data/credentials.
- Output comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903 does not exist; no run_01 is created. No prior result overwrite.
- Exact source compile T0 exit0; T1-A..F and other critical regression29 PASS. The historical P1C1.046s/<1s timing FAIL is retained, solely non-blocking under the committed amendment. Main independently verified P1C finite/maxLLR/nonzero/hard_bits_ok/ck_ok,72 checkpoints,144 iterations and <=10 per checkpoint; no threshold was silently changed.
- Scientific parameters unchanged: mother9036x10240 nnz49620; natural-log Bob-only hierarchical prior; lambda selected solely CAL702..1725; fixed VAL1726..1761, nine groups of four, non-fresh, no replacements; clip20/tol1e-6/max10 per checkpoint720 per block. Existing64-bit protocol tag only.
- Four communication counters remain separate, tag charged on publication, failures retained, current syndrome/tag verification only; offline oracle and accepted-wrong isolated. CE denominator is selected CAL-CV model-relative, not a Shannon/security efficiency.
- Budget600s/block and7200s invocation including CAL; no rerun/tuning or other sources. Output excludes raw symbols, syndrome/tag arrays, fitted matrices and credentials. Results remain candidates until main Pre-RESULT.
- Scoped stale-template search in this cycle/change returned zero hits (historical references elsewhere are not execution bindings).

Release: one invocation only, by luna_worker, at the exact above implementation SHA:
`python scripts/v72p2_real_smoke.py --registry v71_data_registry.json --out-dir comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903 --execute-real`

These local reviewer records precede execution and will be committed with independently reviewed results, per the packet's SHA-binding protocol. The only uncommitted files permitted during execution are this review and cycle_state.yaml. Scientific promotion, V73,1.5M and2M remain unauthorized. Stop and retain failure if the invocation fails; do not repair and rerun within this release.

## Independent Pre-RESULT PASS, 2026-09-03

Operator's sole invocation (session12134) exited0 after all9 assigned blocks. Main independently read all four actual artifacts, reviewed the producer's dataflow/oracle boundary, and ran a separate PowerShell audit (exit0) without rerunning decoder or rereading raw data. Reviewed implementation and all three manifest code/plan bindings are b33664d00b5b22a02b61df95b00c99ae0a0368b8. All executable source remained clean. Only the prereview-owned docs were modified during execution.

Audit evidence:9 assigned/attempted,36 exact frozen VAL IDs and CAL702..1725,648 ordered checkpoint records,3037 actual iterations. Every checkpoint's residual count, cumulative iteration cap, finite/clip flags, convergence boolean, publication delta,64-bit tag charge,CONTINUE count and elapsed deadline were recomputed; current acceptance flags are coherent. CSV per-block counts match JSON; report summary matches JSON. CAL-only selected lambda221.22162910704503 minimizes the30 recorded scores; fixed reference CE7.135005172802673. Mean smoke CE7.202453237799434 is posthoc only. These CE values and f ratios are model-relative, not security efficiencies.

Observed result:0/9 protocol-accepted and0/9 exact accepted;0 accepted-wrong;9 LADDER_EXHAUSTED, no invalid/not-attempted/numeric error/timeout. Each final checkpoint has converged=true but syndrome_ok=false and tag_ok=false. Each block used9036 syndrome bits+64tag=9100 leak_IR bits, plus71 CONTINUE bits=9171 public bits. Totals81900/82539 bits; all-attempt ratios1.2455097837734632/1.2552274974710365; success-conditional ratios null. Total wall1057.375s including CAL. Block wall114.469..118.156s, iterations331..342; all within frozen limits. All9 final bit/symbol error counts equal their raw counts (totals27003 bits/5471 symbols); equal counts do NOT prove bitwise-identical candidates. No correction improvement is observed in these recorded counts.

Verdict: accept the validity and accounting of this bounded negative descriptive experiment, NOT algorithm qualification, information-limit attribution, zero-undetected-probability, FER inference, independent holdout confirmation, SKR or promotion. Zero accepted-wrong with zero accepts gives no successful verifier trial evidence. No automatic retry or45-block expansion. The historical synthetic timing regression remains disclosed; no threshold was rewritten.

Publication release: only the existing four compact artifacts (manifest15948B/results572364B/table2188B/report694B), this cycle's records, task completion marks and memory-agent triage may be committed/pushed. No raw symbol arrays, syndrome/tag bytes, fitted matrix, raw data or credentials are included. All execution authorization is consumed and now false. The prior V72P1 acceptance and evidence remain historical and unchanged.
