# Single-symbol soft-prior restart — EXPLORE

FROZEN v1; independent PLAN pending. Cost annotation EXPLORE_HEAVY,
not a third track. UUID31dca97b-808c-4205-ac01-7c5ab7b9e9b5.
Root workspace/gf32_softprior_31dca97b. Contract identifier
NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/PREREG_AND_AUTH.md.
Namespace gf32-softprior-v1. Ongoing literal grant in
../NBLDPC-CONTINUOUS-EXPLORE-20261001.md plus user 可以继续 covers this
fresh bounded synthetic successor. Main dispatch only after independent
PLAN/implementation PASS. One attempt; no repair/rerun/resume/extra arm.

## Retained source and fresh frames

Only source workspace/gf32_degree_admitted_a9352bc1/diagnostics.npz,
batch UUIDa9352bc1-ae56-443b-ae93-9dcfa85d4229, contract
NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md, seed_namespace
gf32-degree-admitted-v1, graph_input_kind admitted_source. Read once inside
budgeted execute. Select six CONTROL/DV2 H_deep by explicit profile_order,
deep_profile_index/deep_graph_index joins to graph_seed2026093901..3906,
not physical array order. Preserve constructor lineage UUIDa9a18abe-
3547-4d16-aa50-1f7150182f31/path/index/j/seed/logicalID;3905 index9/j1/
seed2560859716. Shape52x128/GF32 symbols0..31/dv2x128/dc4x4+5x48/E256
and actual connected support rechecked. Rank52/deep-label correctness reused
from independent upstream A5; source equality rechecked at batch-end review.
No new graph, label search, row order, OSD, or old decoder rerun.

192 fresh pairs: six graphs xstreams0/1 xframes0..15. Seed formula
v10_seed('gf32-softprior-v1:holdout:{graph_id}:{stream}:{frame}'). Freeze one
192-row plan at entry; verify keys/order/unique/disjoint from the nearest
finite predecessor seed plans frozen below, including degree-admitted192 rows.
Also include any later distinct accepted holdout plan identified by static
registry check before implementation review; the exclusion list must be
written into this packet before dispatch, not changed after execution.
No seed collision replacement; STOP on collision. Endpoint replay/census
created no new frame plan. Existing frames/truths are never reused.

PMF p0=.550; p[e]=.450*count/4428,
{1:2295,3:1126,7:557,15:304,31:146}, other0. Bobzero/iid synthetic,
original probability prior repeated128 rows. Effective original prior P_eff
=max(P,1e-15), row-normalize, exactly matching v35. Truth sampled once per
pair; own syndrome H*truth over GF32/poly37 computed once. Truth never enters
decoder, uncertainty selection, branch condition, scoring or output choice.

## One frozen conditional algorithm

Baseline: v35 row-layered FFTQSPA max_iter90/alpha1/warmNone/fieldNone.
Capture actual returned x_hat/iterations/final_beliefs/provenance/cost.
Operational baseline-valid means H*x_hat equals GIVEN syndrome, not zero
syndrome and not truth equality. If valid, candidate passes through the same
vector/call index (even if evaluation later calls it valid-wrong). No rescue.

If baseline syndrome-invalid: require finite128x32 final_beliefs with
CHECK_UPDATED provenance. These are log-space BP approximations, not calibrated
posteriors. Compute each row's stable softmax then entropy in bits. Find the
set of variables adjacent to violated checks of the actual baseline x_hat.
Choose maximum entropy in that set; within1e-12 of maximum choose smallest
column index. Empty set/bad beliefs/source => STOP, no fallback selection.

Run ALL six branches in ascending guessed symbol order {0,1,3,7,15,31}.
Each copies original probability prior P and replaces only that selected row
with one-hot at guessed symbol. Cold BP90/alpha1/warmNone/fieldNone, SAME H
and SAME given syndrome. v35 floors to1e-15 and updates beliefs, so this is
SOFT-prior restart, NOT hard clamp. Record guessed and returned selected
symbol; do not require them equal or silently assert locking. No warm start.

After all six return, retain actual syndrome-valid vectors. Score each by
sum_i log(P_eff[i,x_hat_i]) using ORIGINAL effective prior, not branch prior.
Within1e-12 of maximum score choose lowest branch index. No valid branch:
candidate keeps baseline failure vector/index. Select before truth-based
evaluation. No first-valid shortcut, oracle choice, truth threshold, support
filter or additional decoding branch. Invalid/unfinished pair has no selected
candidate; partial records retained, no fabricated vector.

## Outcomes, accounting and costs

Exact means truth equality AND own syndrome; syndrome-valid-wrong stays
separate failure. Full192-pair totals/pergraph/paired transitions reported.
Candidate baseline passthrough implies no lost control exact frames; violation
of that invariant is STOP. Control exact outside39..153 =>
CONTROL_RANGE_UNINFORMATIVE. Otherwise delta_exact>=12 and positive pergraph
delta>=4/6 gives MECHANISM_SIGNAL if candidate valid-wrong<=control valid-wrong;
if wrong increases use EXACT_GAIN_WITH_SELECTION_RISK, never clean signal.
Otherwise NO_SUFFICIENT_SIGNAL. All signal labels require zero data/auth/
resource violations; incomplete => INCOMPLETE/full comparison totals null.
No route closing/qualification follows; observed zero wrong is not certification.

Let F be actual baseline syndrome failures. Physical calls192+6F (max1344);
logical standalone control calls192, candidate192+6F. Shared baseline is one
physical call, not384+6F. Candidate pipeline cost includes baseline and rescue;
control baseline costs separate; actual batch wall also reported. Each call
iteration0..90, failure90; nominal E*sum(physical iterations) proxy only,
cap256*90*1344=30965760, not measured operations or throughput.

Public syndrome disclosure260 bits per METHOD frame, regardless internal
restarts: each pipeline receives the same fixed rank52 syndrome once.
Control+candidate logical benchmark accounting520 bits/pair, full99840.
Internal branch disclosure increment0; do not multiply leak by physical BP
calls. tag0/verification NOT_IMPLEMENTED/undetected NOT_MEASURED; no f_eff,
SKR or security claim. Counterfactual logical costs and physical calls separate.

Budget1800s total through first-pass artifact writes, sampled peakRSS4GiB,
diagnostics20MiB,1344 physical calls,0OSD/build/search. Cooperative phase/call/
write checks, per-call120s after return (not preemption). Default Linux RSS
ru_maxrss KiB must convert*1024; name high-water semantics. Budget failure
stops before next call. Final checkpoint after first-pass artifacts can change
status to INCOMPLETE and null full comparison; final small state-record
rewrites/review EOF appends are after measured checkpoint, not self-timed.

## Artifacts and complete acceptance matrix

Five artifacts manifest.json,summary.json,frame_records.csv,diagnostics.npz,
EXPLORATION_LOG.md. Call records mark baseline/branch, pair/graph/stream/frame/
seed, chosen variable, guess, actual vector/own validity/iterations/wall/RSS.
NPZ stores six actual H,192 actual truth/syndrome/prior roles, every actual
call raw vector/maps, baseline failure beliefs/provenance/maps, selector
entropy/violated-check/score records and candidate selected-call index.
Pass-through references existing vector; no duplicated physical call count,
made-up beliefs, missing-call zero vectors or truth-conditioned selection.
Partial calls/pairs explicit; append-only log is sole batch review record.

New CLI comparison_bench/src/comparison_bench/cli/nbldpc_gf32_softprior_rescue.py
and new test comparison_bench/tests/test_nbldpc_gf32_softprior_rescue.py only.
Existing modules/source/results read-only; no v35 modification/hard clamp.
API execute_batch requires source_reader,sampler,decode_fns,out_root; optional
repo_root/now/rss_fn/command. Production reader/sampler/decoder explicitly
bound ONLY by --execute; T0/dry/test use no source or production bindings.
Pure uncertainty-selector and original-prior branch-selector helpers.
No generic framework/checksum/atomic/retry/compatibility layers.

S1 independent PLAN/input/finite prior exclusion list/math/auth/ceiling.
S2 fake tests: stable-log entropy/active-variable/ties; original-vs-branch
prior scoring/all-six selection/ties; no-truth kwargs/soft-row prior/cold
settings; full192 mixed valid/invalid frame entry, physical vs logical calls/
cost/leak and raw-vector/selected-index/failed-belief maps; valid-wrong
passthrough and wrong rescue isolated; source-map3905 and namespace plan;
T0/dry/root refusal; bad source/beliefs STOP; partial branch/resource STOP,
terminal writing overcap/null totals/log finalstatus; mocked Linux RSS units.
S3 independent implementation/tests/T0/scoped files/root absence/main dispatch.
S4 independent actual source/maps/seed/entropy selection/branch-score/own-
syndrome/raw-vector/counters/thresholds/disclosure/resources/ceiling review,
no production decoder/sample rerun. Arithmetic recomputation allowed.
S5 main acceptance/compactRESULT+IA/logEOF/tasks/project-memory triage of
accepted facts only, independent proportional milestone docs review.

Nearest negative evidence: MRB-TOP6 did no cold BP restarts and delta0, each
arm41 valid-wrong (1 passthrough+40 wrong rescues); separate MRB rescue had
candidate43 wrong rescues vscontrol0. This new BP-trajectory hypothesis is
untested, not an established gain. No binary-baseline, cross-batch ranking,
universal FER,real/private/raw data,n256,DECIDE promotion/publication/route
closure. No commit/push/merge/archive/add, overwrite or frozen baseline edit.

Exact command after main dispatch:
wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_softprior_rescue --execute --out-root workspace/gf32_softprior_31dca97b

## Frozen finite seed exclusions — S1 completion input

Let R=comparison_bench.cli.nbldpc_gf32_roworder_probe and
D=comparison_bench.cli.nbldpc_gf32_degree_probe. Use these exact source-free
plan generators, not an assumed generic _PRIOR variable or namespace-only
argument. Each generator's accepted frozen domain/formula is retained.

| Plan generator | Unique rows |
| --- | ---: |
| R.prior_runner._seed_plan() | 264 |
| R.search_runner.fine_runner.predecessor.seed_plan() | 288 |
| R.search_runner.fine_runner.seed_plan() | 360 |
| R.search_runner.replica_runner.seed_plan() | 192 |
| R.search_runner.seed_plan() | 192 |
| R.iter_cap_runner.resource_runner.seed_plan() | 192 |
| R.iter_cap_runner.seed_plan() | 192 |
| R.seed_plan() / gf32-roworder-v1 | 192 |
| D.seed_plan() / gf32-degree-v1 | 192 |
| D.seed_plan(seed_prefix='gf32-degree-admitted-v1') | 192 |
| nbldpc_gf32_mrb_rescue_probe.seed_plan() / gf32-mrb-rescue-v1 | 192 |
| nbldpc_gf32_mrb_top6_probe.seed_plan() / gf32-mrb-top6-v1 | 192 |
| nbldpc_gf32_mrb_reachability_probe._seed_plan() / gf32-mrb-reachability-v1 | 192 |

The last3 namespaces use graph IDs2026093901..3906,streams0/1,frames0..15.
MRB-TOP6 and reachability are accepted FRESH holdouts; earlier messages that
treated TOP6 as replay were wrong and are superseded. Endpoint ablation is
same-sample replay and GLOBAL-CENSUS generated0 frames, so neither adds seeds.

census_tests performed pure plan/v10_seed arithmetic, no sample/NPZ/decoder
operation: each13-plan internally unique, finite union2832 unique, new
gf32-softprior-v1 plan192 unique, overlap0 against each and the union.
This is the exact nearest degree/roworder chain plus confirmed subsequent
fresh MRB/admitted plans, not a claim to exhaust all project historical seeds.
Implementation/C3 must retain these generators/counts and check all192 new
seeds against this union before any sampling; no collision replacement.
Overall S1 awaits independent review of this completed finite table.

## S1 disposition and implementation release
2026-10-01: independent census_review S1 PLAN PASS. Independently expanded all 13 frozen generators: 2832 rows/unique seeds, no internal or cross-plan collision; new 192 unique seeds disjoint from each and the union. Scope/source interface, scientific contract, costs, authorization and claim ceiling reviewed. Main accepts S1 and releases implementation only to census_scope (new CLI) and census_tests (new focused tests). No scientific execution dispatch yet; S3 independent review and main one-shot dispatch remain required.


Implementation clarification (unchanged scientific inputs/thresholds): the pure uncertainty selector receives the GIVEN syndrome explicitly and detects violated checks by H*x_hat != syndrome. It must not substitute zero syndrome. Helper argument ordering is coordinated by code/test owners; use explicit named inputs where useful.


## S2 implementation/fake-test return
2026-10-01: census_scope returned the sole new CLI; census_tests returned the sole new focused test. Final explicit-fake suite 17 passed in 5.75s, including mismatch plus per-call overcap yielding INCOMPLETE/null comparison totals and retained integrity/resource events. Command: wsl.exe -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m pytest comparison_bench/tests/test_nbldpc_gf32_softprior_rescue.py -p no:cacheprovider --basetemp workspace/softprior_s2_resourcecap_20261001_14d8ca. Earlier fake failures were corrected before any scientific attempt (baseline raw-belief retention, peak_rss closure, partial integer sentinels, after-return resource gates/event duplication). Existing unknown cache_dir pytest warning non-blocking. Source/production sampler/decoder execution count remains zero. S3 independent final verdict pending.


## S3 independent PASS and main one-shot dispatch
2026-10-01: census_review independently reports S3 FINAL PASS, focused 17 passed in 6.03s; T0 PASS and dry-run DRY_RUN (192 frames/13 excluded plans/2832 rows; source/sampler/decoder/writes all zero). Target workspace/gf32_softprior_31dca97b absent after both. Intended branch formal-ir-v72p1-addendum-clean; scoped CLI/test untracked and explicitly admitted under this UUID; unrelated dirty paths excluded. Source metadata-only review; scientific decoder/sample count zero. Main accepts S3 and dispatches exactly one frozen attempt under the literal continuing user grant and latest 可以继续. No repair/rerun/resume/extra arm. Exact command follows; this dispatch covers only this EXPLORE batch and does not grant DECIDE/real data/n256/publication/Git actions.
wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_softprior_rescue --execute --out-root workspace/gf32_softprior_31dca97b

Execution ownership: main launched the exact command; unified exec session_id=37982. Initial WSL localhost-proxy/NAT warning only; process running. Do not launch a second process or touch this output root.


## One-shot terminal record (S4 pending)
Main-owned unified exec session37982 ended exit0. No second invocation/repair/resume. Operator artifacts report COMPLETE192 and CONTROL_RANGE_UNINFORMATIVE (control155 exceeds frozen153 upper bound), control155/candidate167/delta12, pergraph deltas5/1/2/1/2/1, valid-wrong0/0. These are provisional pending independent S4; no screen relabeling or promotion. Initial terminal totals: physical414 calls, baseline192/rescue222, wall145.379913883s, high-water RSS138113024 bytes. Raw stdout was oversized/truncated by tool; actual frozen artifacts, not stdout, govern acceptance. S4 reviewer dispatched read-only actual arithmetic/source equality; no sampler/decoder rerun.

S4 FINAL PASS/main acceptance recorded in RESULT.md and INDEPENDENT_ACCEPTANCE.md; accepts finite description plus CONTROL_RANGE_UNINFORMATIVE only. One-shot session37982 grant consumed. No threshold change or promotion.

