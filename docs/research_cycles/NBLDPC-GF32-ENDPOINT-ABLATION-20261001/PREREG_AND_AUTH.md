# DV3 label endpoint ablation — EXPLORE

FROZEN v1; independent PLAN and implementation review pending.
UUID 67ca7191-3adc-4202-9d78-8bcd1a90a05a.
Root workspace/gf32_endpoint_67ca7191; contract gf32-endpoint-ablation-v1.

## Question and authorization

Does the deep label endpoint explain the extremely low recovery on the six
fixed DV3 graphs? Compare constructor and deep labels on identical supports.
This is a new bounded synthetic diagnostic, NOT a repair of a consumed batch.
The ongoing literal user grant is preserved in
../NBLDPC-CONTINUOUS-EXPLORE-20261001.md and applies to this new frozen packet.
Main dispatch only after independent PLAN/implementation PASS and main
acceptance of the upstream degree-admitted A5 evidence. One attempt only;
no repair, rerun, continuation, extra arms, tuning or replacement inputs.

## Frozen source and procedure

Only input: workspace/gf32_degree_admitted_a9352bc1/diagnostics.npz,
source UUID a9352bc1-ae56-443b-ae93-9dcfa85d4229. This is SAME-SAMPLE
paired diagnostic replay: the existing 192 truths/seeds are reused, not new
holdout or 192 additional independent samples. Read once inside the budgeted
execute path; T0/dry-run/fake tests must not read real input or bind production.
Use explicit profile_order/graph and pair maps, never incidental NPZ ordering.
Select ONLY candidate DV3 H_constructor and H_deep for logical graph IDs
2026093901..2026093906, preserving source constructor lineage (3905 candidate
index10/j1/seed2560859716). Verify actual common support, GF32 coefficients,
n128/m52/E384, dv3x128 and dc7x32+8x20; source rank/connectivity reuse is
explicitly upstream independently accepted evidence. Source/map/profile
mismatch => STOP before BP; no fallback matrix or new construction/search.

Control=constructor H; candidate=deep H. Reuse all 192 pair_truth and their
original pair_seed/graph/stream/frame indices, ordered by original pair_index.
Both arms share matched iid synthetic prior: p0=.550;
p[e]=.450*count/4428 for {1:2295,3:1126,7:557,15:304,31:146}, others0,
floor1e-15 then normalize/log. No sampling. Each endpoint uses its OWN
actual H*truth syndrome over GF32/poly37; truth never passed to decoder.
v35 row-layered FFTQSPA max_iter90, alpha1, cold/warmNone/fieldNone.
Even original frame constructor-first; odd deep-first. No row permutation,
same-code/same-syndrome/prefix constraint. Capture the same real return vector
for observation and artifact. Zero builders, label searches, OSD calls.

## Evidence and costs

Complete status COMPLETE, partial INCOMPLETE; no route-closing or promotion
threshold. Report raw exact counts (truth equality AND own syndrome),
syndrome-valid wrong separately as failure, raw failures, per-graph counts,
paired both/control-only/deep-only/neither and transitions. Delta=deep minus
constructor; per-graph denominator32, total192. Both endpoints low cannot
identify a label cause. A constructor advantage is only an association of
these frozen label endpoints on these reused samples, not general causality.
Deep advantage also does not resolve the upstream DV2-vs-DV3 comparison.

Record iter0..90 (failure90), wall per arm/call and total, sampled RSS,
violations and stop reason. Nominal E*sum(iterations) proxy ONLY; cap
13,271,040=384*90*384, not measured operations. Current source loading is
measured separately; build/search costs0. Prior upstream costs stay separate.
260 syndrome bits per attempted arm including failures; complete99,840 bits,
tag0, verification NOT_IMPLEMENTED, undetected NOT_MEASURED.
Cap384 BP calls/192 complete pairs, total1200s including read/preflight/writes,
per-call120s after return, sampledRSS4GiB, diagnostics20MiB. Cooperative
checks between phases/calls/writes, no hard-preemption claim. On STOP retain
actual calls/partial pairs/vectors; full-performance totals null if incomplete.

Five artifacts: manifest.json, summary.json, frame_records.csv,
diagnostics.npz, EXPLORATION_LOG.md. NPZ carries both actual H endpoints,
original truths, own syndromes, real raw outputs, call/pair/graph/arm/seed/
stream/frame/source lineage maps; never invent vectors for unattempted calls.
CSV records same outcomes/costs/source maps. Log is append-only; after the
single attempt only independent review/main acceptance can be appended.

## Implementation ownership and complete acceptance matrix

New CLI comparison_bench/src/comparison_bench/cli/nbldpc_gf32_endpoint_ablation_probe.py
owned by iter_operator. New test comparison_bench/tests/test_nbldpc_gf32_endpoint_ablation_probe.py
owned by iter_tests. Existing modules read-only; reuse paired_arm_data,
decode_observation and v35 production binding, no new generic runner framework.
API execute_batch requires diagnostic_reader, decode_fns, out_root; optional
repo_root/now/rss_fn/command only. Production reader is explicit in --execute.
Pure source extraction helper and verify_t0/dry_run never read real artifacts.
Implementation subagents are not alone; preserve all unrelated edits.

A1 independent PLAN: exact source/paired replay/maps/prior/decoder/budget/ceiling.
A2 focused fake tests: full192/384 entry path with fake source/decoder; endpoint
own syndromes and actual vectors; same-support different-coefficient fixture;
profile-major mapping; bad source before BP; source-free dry/T0; root refusal;
resource STOP preserving partial vectors/null totals; accounting/costs.
A3 independent implementation/T0/tests/scoped files/root absence/main dispatch.
A4 independent actual source equality/H/syndrome/vector/map/count/cost/resource
review, no construction, label or decoder rerun; main scientific acceptance.
A5 compact RESULT/INDEPENDENT_ACCEPTANCE/logEOF/tasks/project-memory triage,
independent milestone document consistency. Operator cannot self-accept.

Exact command after main dispatch:
wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_endpoint_ablation_probe --execute --out-root workspace/gf32_endpoint_67ca7191

No real/private/raw input, n256, security/FER/f_eff/SKR/throughput/publication/
qualification or route closure. No cross-batch rank/table, void baseline or
forbidden columns. No commit/push/merge/archive/add, frozen baseline edit or
output overwrite. Dirty-tree provenance always includes both batch UUIDs.

## Independent A1 / main implementation release

iter_contract independently reviewed this packet/PROMPT/OpenSpec and returned
A1 PASS. Main accepts the paired replay, fixed source, budgets and ceiling.
Upstream degree-admitted A5 actual-artifact review independently passed and
main accepted COMPLETE/NO_SUFFICIENT_SIGNAL, C144/deep-DV3 1, without route
closure. Implementation/new focused fake tests are released to their designated
owners. This is not decoder execution authorization; A3/main one-shot dispatch
is still pending. Total wall cap is1200s (20 minutes), not12 minutes.

## A3 implementation correction before any attempt

Independent A3 found one blocker: the implementation measured wall before
terminal summary/log/manifest writes and could wrongly mark an over-budget
write path COMPLETE. No scientific attempt has occurred. Owner must put the
completion wall/RSS check after all first-pass artifact writes; exceeding the
unchanged cap means INCOMPLETE/resource STOP with complete performance totals
null and actual calls/vectors retained. A focused fake-clock test must cover
terminal-writing overrun. The final small state-record rewrite that records
this checkpoint is explicitly after the measured completion checkpoint,
not recursively self-timed. Record that boundary; do not claim hard preemption
or inclusion of the final rewrite in its own measurement. No input/threshold/
budget/science change; A3 re-review is still required before dispatch.

## A2–A3 PASS / main one-shot dispatch

iter_tests final focused fake suite7passed; iter_contract independently ran
the same focused suite7passed, py_compile and allfive T0 checks PASS, official
root absent before/after. Independent A3 final PASS includes the corrected
terminal-write cap and explicit final log status; no real source/production
decoder was entered. Main accepts implementation and dispatches the exact
frozen command ONCE under the ongoing literal user grant, UUID67ca7191-3adc-
4202-9d78-8bcd1a90a05a. No repair/rerun/resume/extra samples/arms permitted.
Operator owns only this launched process; report actual terminal artifacts,
metrics and STOP. Independent A4 and main acceptance remain pending.

## A4 PASS / main accepted / closeout

The preceding pending statements are historical execution-gate states and
are superseded by this record. Independent iter_contract A4 actual-artifact
review PASS; main accepted COMPLETE/COMPLETE_DESCRIPTIVE_ONLY,192 pairs/
384 calls, constructor/deep exact1/1, delta0, paired1/0/0/191, zero violations.
This is the same192 synthetic samples, not fresh independent evidence; both
label endpoints near the floor do not identify the cause or close the route.
RESULT/INDEPENDENT_ACCEPTANCE and exploration-log EOF record actual evidence.
Independent milestone document-consistency review found no numerical/ceiling
discrepancy; its sole historical-pending clarification is resolved here.
T4/T5 complete; one-shot authorization consumed, no repair/rerun/resumption.
Final measured wall includes first-pass artifact writes; final state-record
rewrites and subsequent review append are after the completion checkpoint.
No commit/push/merge/archive or real/private/raw data execution occurred.
