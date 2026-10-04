# Admitted-matrix degree-profile comparison — EXPLORE

FROZEN v1 / ongoing grant / independent PLAN pending.
UUID a9352bc1-ae56-443b-ae93-9dcfa85d4229.
Root workspace/gf32_degree_admitted_a9352bc1 (fresh/absent).
Contract gf32-degree-admitted-v1; frame namespace gf32-degree-admitted-v1.
New batch, not repair/rerun/resumption of consumed degree-profile attempt.

## Retained contract and explicit deltas

Retain scientific/source/label/decoder/screen/leakage/resource/partial/ceiling
clauses of ../NBLDPC-GF32-DEGREE-PROFILE-20261001/PREREG_AND_AUTH.md,
except construction stage/identity/frame namespace as explicitly replaced here.
Retain same six logical graph IDs2026093901..3906 and192 pairs (2streams0/1,
16frames each),384BP/0OSD. No new D10 constructor call in this batch.

Fixed input is ONLY the12 selected constructor matrices in accepted canary
workspace/gf32_construct_a9a18abe/constructions.json, UUID
a9a18abe-3547-4d16-aa50-1f7150182f31, independently C4 reviewed full-rank,
connected and exact profiles. Read once at execute; no input-artifact read
on dry-run/tests. Select by the canary's frozen group selected matrix indices,
not by performance/J/cycles. For3905 both profiles constructor seed2560859716
and j1; other groups graphID seed/j0. Logical graphID and construction seed
must remain distinct and both recorded, with sourceUUID/path/matrix index/j.
Source metadata must be COMPLETE/CONSTRUCTION_FEASIBLE with six selected
common-seed pairs. Missing/mismatched source/index/profile/seed => STOP before
labels/BP; no extra source, graph or replacement selection.

Recheck actual profile-aware structural admission on these arrays before
labels: n128/m52/rank52/nonzeroGF32/poly37/connected; control dv2x128,
dc4x4+5x48/E256; candidate dv3x128,dc7x32+8x20/E384. Apply accepted
build_candidate_pair(deep endpoint, same parameters) to BOTH arms, using
logical graphID for label diagnostics and separately retaining constructor
seed. At most8 total sweeps, column0..127/labels1..31, TIE_TOL1e-12,
MIN_SCORE_GAIN1e-10/unchanged monotonic/reference/admission gates. Only deep
matrices used in both decoder arms; source constructorH is provenance.
Any label/admission failure STOP, no raw/one-pass fallback or added search.
J=sum single-check marginal entropies is heuristic, not joint syndrome
entropy, leakage or decoder result.

PMF fixed p0=.550; p[e]=.450*count/4428,
{1:2295,3:1126,7:557,15:304,31:146}, all other0. Synthetic iid/Bobzero/matched
prior/floor1e-15 and retained normalize/log only. New frame seed:
v10_seed('gf32-degree-admitted-v1:holdout:{graph_id}:{stream}:{frame}'), unique
and disjoint from all prior accepted frame plans, including consumed degree-v1
plan even though that attempt had0BP. Source canary had no frames.
Every pair sample once, shared truth/prior; each actual deepH own syndrome.
Even frame controlfirst, odd candidatefirst. v35 layeredFFTQSPA90/alpha1/
warmNone/fieldNone both arms. No row permutation, same-code/same-syndrome or
prefix-equality gate. Truth absent from decoder; same raw return for CSV/NPZ.

## Metrics, diagnostic screen and costs

Exact=truth equality AND independent actualarm syndrome valid. Valid-wrong
separatefailure; iter0..90/failure90. Delta=candidate-control exact counts;
pergraph/paired/transitions full denominators. Control39..153 inclusive,
delta>=12,positive delta_g>=4/6,zero violations => MECHANISM_SIGNAL;
outside controlrange => UNINFORMATIVE; else NO_SUFFICIENT_SIGNAL.
Partial=>INCOMPLETE, complete performance totals null. Each attempted arm
260syndromebits including failure; complete99840;tag0/verification
NOT_IMPLEMENTED/undetected NOT_MEASURED. Per-arm iterations/wall and RSS;
nominal E*sum(iterations) proxy only, cap11,059,200=192*90*(256+384).
Constructor work NOT performed here; accepted source cost separate, never
silently fold into a wall/performance claim. Total currentbatch1800s includes
source read/preflight/labels/BP/artifacts;after-return120s percall,4GiBsampled,
20MiBdiagnostics;384BP/0OSD. Retain failures/row/vector maps/no-next-call,
sample around phases/writes; finalsmallsummary/logboundary explicit.

Whole degree-profile bundle with matched label/decoder, conditional on this
common-admission constructor protocol/sample. Cannot isolate dv alone or
claim random-graph population, causal significance, FER/f_eff/SKR/security,
qualification/publication/real-channel/route closure. No crossbatch ranking,
voidHDC/LBbaseline/forbiddenTABLEcolumn use. No fresh real/private/raw input.

## Minimal implementation / immutable-default reuse

Allowed code ONLY:
1 comparison_bench/src/comparison_bench/cli/nbldpc_gf32_degree_probe.py
2 new comparison_bench/src/comparison_bench/cli/nbldpc_gf32_degree_admitted_probe.py
3 new comparison_bench/tests/test_nbldpc_gf32_degree_admitted_probe.py
Existing degree tests may be read/run but not edited unless main narrow release.
All prior artifacts/other runners/frozen Polar files untouched.

Reuse accepted execute_batch, not a copied runner. Small explicit optional
execution identity/path/seed-plan inputs with DEFAULTS EXACTLY preserving
old degree CLI behavior; command injection already exists. Within one execute,
freeze one local identity and seed plan passed through every summary/manifest/
log/CSV/NPZ/root check; no global mutation, hidden namespace or source identity
inheritance. Seed plan must match namespace formula/192slots/order and prior
disjoint; do not permit an inconsistent arbitrary plan silently. Thin newCLI
passes literal newbatch identity/root/namespace, fixed-source graph callback,
accepted profile/label/decoder bindings. Tests explicitfake callbacks/readers,
no implicitsource/production access. No generic framework/newdependencies/
checksums/atomicwrites/locks/compatibility abstractions/tamper expansion.

Five actual output artifacts retained manifest/CSV/summary/NPZ/log. Actual
source constructorH and deepH perprofile/graph, truth, ownsyndrome/rawxhat and
allpair/call/graph/arm/frame/stream/seed/vector maps. SourceUUID,selectedmatrix
index,j,constructionseed/logicalgraphID provenance included in machine output.
Partial only real vectors/maps, no invented placeholders. Fresh output root
absent; no overwrite/newscientificrepair/rerun/resume/extraseed/profile.

A1 source frozen selection/actualprofiles/deependpoints/ownsyndrome/provenance;
A2 parameterized identity defaults preserve old11tests; newidentity exact
through everyartifact and newframe plan; no globals/rootcollision.
A3 actualentry192fakepairs384calls realsampler,distinct profile/deeplabels,
sharedinputs/actualrawclassification/maps/cost/wrongisolation; tiny source
rejection/partial resource/label failure nofallback/source-no-read dryfixtures.
A4 compile/focused old+newtests/T0zero source/artifact reads/graph/labels/BP/
writes/officialrootabsence and independentPLAN/implementation/mainone-shot.
A5 actual independent rawGF32/sourceequality/profiles/deep/seed/vector/leak/
cost/resource/screenreview, mainacceptance then compactdocs/projectmemorytriage.
Reuse predecessor proven partial/resource tests; no new full genericfaultsuite.

## Authorization and command

Ongoing literal user grant/exclusions ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md.
Main owns scope/packets/OpenSpec/thresholds/dispatch/acceptance; lunaoperator
owns releasedcode, testworker onlynewtest, independentreviewer read-only.
Notalone/readbeforeedits/preserve unrelateddirtytree. No commit/push/merge/
archive/gitadd-A/destructive/external/globalmemory action. Main dispatch
only after A4PASS; no operator self-acceptance.

`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_degree_admitted_probe --execute --out-root workspace/gf32_degree_admitted_a9352bc1`

## Explicit graph-input cost semantics and source joins

Additional minimal execution input graph_input_kind defaults to existing
constructed behavior; thin newCLI supplies admitted_source. Newbatch
profile_costs graphs_built=0/graph_build_wall_s=0, graphs_loaded=6perarm and
load callback elapsed graph_load_wall_s; totalbatch includes first lazy read
inside execute, not an uncounted pre-execute source read. Reading JSON once
within the local callback/closure is input loading, not a custom cache system.
Legacy mode fields/default computation remain unchanged. Loaded source H is
not measured construction, and source canary work is separately referenced.
Source selected indices join matrices[].matrix_index and attempts[].matrix_index
explicitly (not attempt position); constructor record supplies original edges/
coefficients/preflight plus separate constructorseed/j/source metadata, while
runner graph_seed retains logicalgraphID. Preserve source provenance in all
needed machine graph diagnostics. No extra lifecycle/generalization is added.

## Independent A1–A5 PLAN PASS / implementation release

iter_contract PLAN PASS including fixed-source joins/provenance/inputloadcost,
legacy-default compatibility/localidentity/newseed/recheckprofiles/budgets/
conditionalceiling/grant. Main accepts PLAN and releases only allowed code
files to iter_operator and only new admittedtest to iter_tests. Old degree
11tests are run unchanged; no oldartifact/otherfile writes. SourcecanaryP7
independentdocsPASS accepted, sourceJSONunchanged. No science until A4PASS
and main one-shot dispatch.

## Frozen minimal interfaces (implementation/test coordination)

Existing degree execute_batch gains only these optional local execution inputs:
batch_uuid=BATCH_UUID, contract_id=CONTRACT_ID, seed_prefix=SEED_PREFIX,
seed_rows=None, out_root_relative=OUT_ROOT_RELATIVE,
graph_input_kind='constructed'. Omitted inputs preserve prior behavior;
seed_rows=None derives once from the supplied prefix. Existing explicit fake
callbacks/now/rss/command/repo_root remain unchanged.
New admitted CLI execute_batch requires explicit source_reader (no-argument
call returning the source JSON document), candidate_builder,
profile_preflight_fn,decode_fns, plus out_root and optionalrepo_root/now/rss/
command. It delegates to the existing loop with fixed newexecution inputs.
source_reader is called once lazily inside the graph callback during execute;
no read on wrapperconstruction/T0dryrun/tests unless an explicitfake is passed.
Pure selected_graphs(source_doc) validates/index-joins selection and returns
lookup keyed by (logicalgraphID,profile). New verify_t0()/dry_run preserve
zero source/production binding calls. No speculative interfaces added.

Compatibility precision: identity/root/prefix optional signature defaults may
be None, resolved from legacy module constants once at call entry, preserving
existing call-time defaults and legacy fake-test monkeypatch seams. This is
semantically the legacy-default rule, not a new science setting. The new thin
CLI passes all fixed new literals explicitly; no moduleglobal mutation.

## A1–A4 independent implementation PASS / main one-shot dispatch

iter_contract independently verified current old+new suite18passed, T0true,
newdry-runzero source/artifact reads/writes/graph/label/decoder, rootabsent
beforeafter, intendedbranch formal-ir-v72p1-addendum-clean and scopedfiles.
Localidentity/seed/default/sourcejoin/loadbudget/deeppair paths PASS.
Preflight boundary: actualH shape/symbols/degree/E/coeff checks are current;
rank/connected gates read fixed source structure, whose actual12H ranks/
connectivity were independently C4-recomputed. Main accepts this reuse of
upstream fixed-source evidence; do not claim fresh rank recomputation in
preflight. A5 actual-source equality/GF32/deep/vector review remains required.
No concrete source drift was identified; accepted sourceJSON is unchanged.
Main accepts implementation and dispatches exact frozen command once under
ongoing grant, UUIDa9352bc1-ae56-443b-ae93-9dcfa85d4229. No new construction/
repair/rerun/resume/extra frames/seed/profile/fallback. Actual evidence
acceptance awaits independent A5 and main adjudication.
