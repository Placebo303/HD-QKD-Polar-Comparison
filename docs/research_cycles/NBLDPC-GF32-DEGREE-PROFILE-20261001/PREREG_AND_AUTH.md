# Matched GF32 degree-profile mechanism — EXPLORE

State: FROZEN v1 / ongoing grant / independent PLAN pending.
UUID: 8c881d42-8d11-4867-8175-bc6f5c97f1f3.
Fresh root: workspace/gf32_degree_8c881d42.
Nearest accepted predecessors: SEARCH-DEPTH/ITER-CAP/ROW-ORDER; retain
unchanged source/math/decoder/observation semantics, with the deltas below.

## Question, boundary and scientific deltas

Compare two fixed degree-profile bundles at identical n128,m52,GF32/poly37,
rank52 and per-attempt260-bit syndrome disclosure. Control dv2x128,
dc4x4+5x48,E256. Candidate dv3x128,dc7x32+8x20,E384. Both socket sums match.
Interpretation is the entire degree profile plus the same fixed construction
and label-processing algorithm; dv and dc change together. This cannot
identify dv alone, prove topology causality universally, or isolate loopy-BP
error. Consumers: whether fixed-leakage graph design merits a successor.
It is not a binary comparator, real-channel qualification, or route closure.

Use D10 build_degree_sequence_peg/coefficients_for_edges/dense_from_edges
and structural_record, retaining accepted seed/coefficient construction
conventions. For graph seeds2026093901..2026093906 construct each profile
once. No replacement seed, retries, best-of graphs, fallback profile or
outcome-based selection. Profile-aware preflight requires actual n/m/E,
exact degree histogram, connectedness, valid nonzero GF32 coefficients,
rank52 and accepted constructor admission. Do not call old fixed-profile
preflight as the candidate authority. If any construction/admission fails,
retain both available matrices/diagnostics and STOP before decoder calls.

Both profiles use the exact accepted search-depth deep-label endpoint
(_candidate_pair_for_graph / build_candidate_pair), identical parameters,
source PMF, column order, label choices, tie rules and maximum sweep budget.
Admit deep H only on both sides; constructor H is provenance. No one-pass
vs deep mismatch, no fallback to raw H, no new objective or tuning. Retain
constructor/deep diagnostics and actual endpoint metadata. Label objective
J=sum of single-check marginal entropies is a heuristic, not joint syndrome
entropy, leakage reduction or performance evidence. A constructor or label
failure stops the batch; no science repair/rerun.

New source seed formula:
v10_seed('gf32-degree-v1:holdout:{graph_seed}:{stream}:{frame}').
192 pairs = six graph pairs x streams0/1 x16frames. All frame seeds unique
and disjoint from accepted preceding plans. Shared error truth/prior within
pair; each actual deep H gets its own mathematically correct syndrome.
Even frame control first, odd frame candidate first. No same-syndrome or
same-code assertion in this comparison. No row permutation in either arm.

PMF fixed p0=.550; p[e]=.450*count/4428 for
{1:2295,3:1126,7:557,15:304,31:146}; others0. Bob zero/iid synthetic
marginal shape/matched prior only, floor1e-15 with retained normalize/log.
v35 layered FFT-QSPA, max_iter90/alpha1/warm_start=None/field=None in both
arms. Truth only for synthetic syndrome before call and observation after
return, never supplied to decoder. Capture same returned raw result for
CSV and NPZ; no duplicate decode or hidden global arm state.

## Diagnostic screen and evidence ceiling

Exact means vector equality to truth AND independently valid arm syndrome.
Syndrome-valid wrong remains separate failure, not undetected measurement.
Returned iterations0..90; syndrome fail must reach90. Full per-arm/per-graph
counts and paired both/control-only/candidate-only/neither; control-fail to
candidate exact/wrong/stillfail. Delta=candidate-control exact counts,
delta_g same per graph. Report every admitted graph, no selective denominator.

Frozen diagnostic screen: control exact39..153 inclusive, delta>=12,
positive delta_g>=4/6, zero integrity/resource/auth violations =>
MECHANISM_SIGNAL. Outside control interval => UNINFORMATIVE; otherwise
NO_SUFFICIENT_SIGNAL. Incomplete => complete performance totals null.
No finite screen is a route kill, significance/causal assertion, FER/f_eff,
SKR/security/qualification/publication/real-channel claim. No cross-batch
ranking or void HDC/LB baseline, forbidden TABLE columns or measured tag.
Each attempted call discloses260bits including failure; full99840bits;
tag0,verification NOT_IMPLEMENTED,undetected NOT_MEASURED.

Candidate has50% more edges per iteration. Explicit per-arm iteration/wall
and sampled RSS costs; nominal edge-update proxy E*sum(iterations) is an
operation estimate, not measured operations or throughput. Complete cap
proxy:192*90*(256+384)=11,059,200 (control4,423,680/candidate6,635,520).
Matched-batch cap is25% above two E256 arms, not50%. Label/build costs
also measured separately where feasible; no wall-time prediction claim.

## Minimal implementation/evidence and stopping contract

Only new CLI comparison_bench/src/comparison_bench/cli/nbldpc_gf32_degree_probe.py
and new test comparison_bench/tests/test_nbldpc_gf32_degree_probe.py.
Reuse accepted pure helpers, no edits to preceding runners or frozen Polar.
Explicit required profile-aware graph/preflight/candidate/arm-decoder fake
bindings; tests cannot implicitly invoke production. Small paired loop and
focused mechanism fixtures, no generic framework/new dependency/checksum/
atomic-write/locking/retry/security/tamper-engineering expansion.

Five artifacts: manifest.json,frame_records.csv,summary.json,diagnostics.npz,
EXPLORATION_LOG.md. NPZ actual constructor and deep H for each graph/arm,
shared pair truth, arm-specific syndrome, actual returned raw vectors and
explicit pair/call/graph/stream/frame/seed/arm/vector maps. Retain only real
available vectors on partial run, no invented placeholders. CSV each
attempted call, including exceptions/malformed observations; incomplete
result totals null, retained partial rows separately inspectable.

Fresh root absent; no overwrite. Single attempt cap384BP/0OSD, total1800s
incl construction/labels/artifacts, synchronous after-return call120s,
sampled RSS4GiB,diagnostics20MiB. Sample/check around construction/label/call
and writes. On any integrity/error/cap violation stop next call, retain
original error and later resource markers/real rows/vectors. Explicit final
small summary/log boundary; no preemption guarantee or recursive recovery
framework. Write failure can exit nonzero with partial root, never accepted.
No rerun/resume/extra arms/graph seeds/repair after science starts.

## Authorization, ownership and complete acceptance items

Literal ongoing user grant/exclusions:
../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. This new bounded synthetic bundle
uses that grant only after frozen PLAN/implementation/R5/main dispatch.
No real/private/raw data, bigger cost class, route DECIDE/promotion/security
claim, destructive overwrite/external action or commit/push/merge/archive/
git add-A. Operators are not alone; preserve all unrelated dirty changes.

D1: exact profile-aware construction/admission, both actual deep-label
endpoints, source/newseed/decoder fixed, actual independent arm syndromes.
D2: actual-entry192pair fake384calls real sampler spy, correct alternating
shared truth/prior and distinct arm H/syndrome, NPZ identities/maps; tiny
outcomes/screen/wrong-isolation fixtures. Fake profiles and deep labels must
actually differ so a copied wrong arm/old profile fails the tests.
D3: vector-derived exact/syndrome,iteration bounds/failure-cap/nonmutation,
nominal edge proxy vs actual wall labels. No prefix/same-code gate.
D4: focused tiny admission failure before BP, second-arm exception/resource
STOP/partial real-vector mapping/null totals/no-next-call, existing-root
refusal and diagnostic cap. No predecessor full generic failure matrix.
D5: compile/focused tests/T0zero science/graph/input/artifact reads/writes,
rootabsence; independent PLAN/implementation and main one-shot dispatch.
D6: independent actual GF32/vectors/profiles/maps/seeds/leak/resources/screen
review then main acceptance and compact docs/project-memory triage.

Main owns requirements/OpenSpec/thresholds/dispatch/acceptance; designated
luna_worker owns only CLI, test worker only test, independent reviewer
read-only. No operator self-acceptance. Exact command after D5 PASS:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_degree_probe --execute --out-root workspace/gf32_degree_8c881d42`

## Retained label endpoint / construction-seed clarification

Both arms retain build_candidate_pair(dense,pmf,graph_seed=seed): one-pass
then at most8 total sweeps, unchanged coordinate order0..127/labels1..31,
TIE_TOL1e-12/MIN_SCORE_GAIN1e-10 and score-drift/monotonic/admission gates.
Deep endpoint on both sides, no fallback. The six existing graph seeds are
intentional fixed construction comparators; newly frozen frame namespace
is unique and disjoint. No selection of graph seeds by this batch outcome.
Cost proxy is mixed-arm11,059,200 at cap, not a both-E256/both-E384 total.

## Independent PLAN PASS / scoped implementation release

iter_contract D1–D6 PLAN PASS, no mandatory clarification; checked profiles,
socket sums/rank/leakage equivalence, retained deep endpoint, profile-aware
admission, own syndromes/shared errors, cost proxy, seeds/limits/grant/ceiling.
Official root and new CLI/test absent at review. Main accepts PLAN and
releases ONLY new CLI to iter_operator and ONLY new test to iter_tests.
No scientific dispatch before independent D5 PASS and main one-shot release.

## D1–D5 independent implementation PASS / main dispatch

iter_contract independent final focused suite11passed; T0dry-runPASS with
zero reads/writes/graph/label/decoder/science, rootsabsent. Reviewed actual
profiles/deep endpoint/own syndromes/seeds/metadata/partial RSS STOP/costproxy.
No remaining blocker. Main accepts implementation and dispatches exact
frozen command once under ongoing grant, UUID8c881d42-8d11-4867-8175-bc6f5c97f1f3.
No scientific repair/rerun/resume/extra arms. Actual batch independent D6
review and main scientific acceptance remain pending.
