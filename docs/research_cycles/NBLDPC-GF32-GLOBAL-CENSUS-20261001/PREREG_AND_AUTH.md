# Fixed DV2 check-graph global census — EXPLORE

FROZEN v1, independent PLAN pending. UUID f4a0ff0d-b538-4fed-bb2d-41c398daa3fb.
Fresh root workspace/gf32_global_f4a0ff0d. Contract gf32-global-census-v1.
Ongoing literal user grant: ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md;
current user continuation: 可以继续. One new bounded synthetic diagnostic,
not rerun/repair of any consumed batch. Main dispatch after PLAN and focused
implementation review. No decoder, construction, labels, resampling or OSD.

## Input and question

Only source workspace/gf32_degree_admitted_a9352bc1/diagnostics.npz, source
UUID a9352bc1-ae56-443b-ae93-9dcfa85d4229. Select the control DV2 constructor
H for each graph ID2026093901..3906 using explicit constructor profile/graph
maps; never incidental row order. Keep source matrix_index/attempt_j/seed/
graph_id/path/UUID lineage (3905 control matrix_index9,j1,seed2560859716).
Source and all matrices are from accepted synthetic batches. Read NPZ once
inside budgeted execute; no reading on T0/dry-run/tests except explicit fake.
Do not access truth, posterior or raw decoder results for analysis.

Rank52/connectivity admission is upstream independent A5 evidence. Recheck
actual shape52x128, integer GF32 symbols0..31, each column degree2, check
histogram4x4+5x48/E256. Recompute support connectedness by BFS and exact
multigraph joins. A mismatch STOP before metrics; no alternative source,
seed or replacement. Input extraction shall use actual writer key schema.

Question: do these six fixed DV2 supports exhibit small global connection
metrics that warrant a later topology-treatment hypothesis? This census
reports metrics only; no route threshold, ranking or intervention is granted.

## Frozen mathematics

Each column is one edge joining its two distinct nonzero check positions;
preserve column as edge ID. 52-node undirected multigraph,128 edges, no loops.
A_ij=edge multiplicity for i!=j,A_ii=0; d=A.sum(axis=1),D=diag(d).
Lnorm=I-D^(-1/2) A D^(-1/2). Use numpy.linalg.eigh on this real symmetric
matrix, eigenvalues ascending. Record all eigenvalues, lambda2, lambda3-lambda2,
and eigensystem residual. Numeric tolerance1e-10 for lambda1 near0, spectral
range0..2, eigen residual and degeneracy. Actual disconnected support is STOP;
near-degenerate lambda2 eigenspace is FLAGGED, not silently excluded/repaired.

Fiedler u2=eigenvector for lambda2. Sign convention: maximum abs component,
ties exact abs equality then smallest check ID, must be nonnegative. Record
sign flip. x_i=u2_i/sqrt(d_i); sort by (x_i,check ID), check all51 nonempty
proper prefixes S_k. cut=sum A_ij across S/complement, volumes=sum degrees;
phi_k=cut/min(volS,volComplement). Find minimum by integer cross products
of cut/denominator (not rounded floats), exact tie chooses smallest k.
Save complete order, all51 integer cuts/volumes/ratios, best subset and phi.
Near degeneracy abs(lambda3-lambda2)<=1e-10 => FIEDLER_DEGENERATE; the chosen
sweep depends on numerical basis, not a stable invariant. Do not choose a
different eigenvector to improve the result.

phi_sweep is an upper bound on global minimum conductance, not an exact
global minimum cut or expansion certificate. Neither lambda2 nor phi_sweep
predicts FER, BP success, minimum distance, causal gains or real-data utility.
Topology treatment remains a separately frozen future hypothesis, not an
automatic conditional arm. No cross-batch graph or algorithm ranking.

## Execution and artifacts

Cap120s total through first-pass writes, sampledRSS1GiB, outputs2MiB; six
graphs maximum. Cooperative phase/graph/write checks, no hard preemption.
One attempt only, no repair/rerun/resume. On source/numeric/resource failure
retain actual completed graphs plus concrete STOP; missing metrics null,
never fabricated as zero. Zero decoder/build/search/OSD calls and zero
new experimental disclosure (not a security/efficiency result).

Three artifacts manifest.json,census.json,EXPLORATION_LOG.md. Include batch/
source identity, command, source-selected maps, actual edge endpoints/A/d,
full frozen mathematical outputs, completed count/status/STOP/resources.
Complete => COMPLETE/DESCRIPTIVE_STRUCTURE_ONLY. Partial => INCOMPLETE.
After first-pass artifacts, one final wall/RSS/size checkpoint; overcap
changes final state to INCOMPLETE. The small state-record rewrite and later
independent-review EOF append are explicitly after this measured checkpoint,
not recursively self-timed. Log final state supersedes initial states.

## Ownership and complete acceptance matrix

One new CLI comparison_bench/src/comparison_bench/cli/nbldpc_gf32_global_census.py,
one new test comparison_bench/tests/test_nbldpc_gf32_global_census.py. Existing
code/baselines/results and four source science artifacts read-only. No generic
framework, new dependency, checksum, atomic-write or retry layer.
API compute_graph_metrics(H) pure (small graphs allowed only for known-limit
tests); execute_batch requires source_reader,out_root, optional repo_root/now/
rss_fn/command. Production np.load reader bound ONLY in --execute. No decoder
binding anywhere. Fake fixtures explicit; operator cannot self-accept.

C1 independent PLAN/source/static schema/ongoing grant/ceiling.
C2 focused tests: triangle lambda2=1.5/phi1, path4 lambda2=.5/phi1/3,
parallel edges/column identity, determinism/degenerate flag; fake source
reordered profile/graph mapping and3905 lineage; source-free T0/dry/root
refusal; full6-graph fake execution; invalid degree/support STOP; fake terminal
write wall overcap retaining metrics with explicit INCOMPLETE log state.
C3 independent implementation/tests/T0/root absence/main dispatch.
C4 actual source equality/edge adjacency/degrees/spectral residual and
independent51-cut arithmetic/source maps/resources/status/ceiling review.
No graph creation or decoder rerun; independent arithmetic recomputation OK.
C5 main acceptance; RESULT/IA/logEOF/tasks/project-memory triage of accepted
facts only, proportional milestone document review.

Exact command after one-shot main dispatch:
wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_global_census --execute --out-root workspace/gf32_global_f4a0ff0d

No real/private/raw input,n256,DECIDE route closure/qualification/promotion/
FER/f_eff/SKR/publication claims; no commit/push/merge/archive/add or baseline
edit. Dirty-tree provenance includes batch and source UUIDs.

## Static source schema clarification before implementation

Read-only census_scope verified the existing writer: NPZ identity keys are
batch_uuid, contract, seed_namespace; input contract
NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md,
seed_namespace gf32-degree-admitted-v1,
input batch_uuid a9352bc1-ae56-443b-ae93-9dcfa85d4229, graph_input_kind
admitted_source. The API parameter contract_id is NOT the NPZ key name.
Use profile_order/control plus constructor_profile_index and
constructor_graph_index joined to graph_seed, not physical array order.
Constructor lineage uses constructor_source_uuid/path/matrix_index/attempt_j/
seed/graph_id; its UUID a9a18abe-3547-4d16-aa50-1f7150182f31 differs from
the input batch UUID. No NPZ content or new science was read/executed by this
static check. C1 review remains pending; usage-limit interruption was not PASS.

## C1 independent PASS / main implementation release

census_review independently reviewed packet/prompt/OpenSpec/ongoing grant,
cycle SOP and static writer schema; C1 PASS without blocker. Main accepts
PLAN and releases the designated new CLI and focused fake tests only.
Precision: eigensystem residual is max absolute entry of Lnorm@U-U*lambda,
with eigenvectors as columns and eigenvalue multiplying each column; record
this norm definition in outputs, keep tolerance1e-10 unchanged. This spectrum
belongs to the52-node check multigraph, not the complete Tanner graph.
C3/main one-shot dispatch remains pending; no scientific execution authorized.

Pre-execution static identity correction: source adapter CONTRACT is the
full upstream packet identifier above; gf32-degree-admitted-v1 is only its
seed namespace. The earlier scope report conflated these values. Corrected
before source reading or science, unchanged sourceUUID/matrices/hypothesis/
budget. Independent C3 must verify the exact binding against the writer.

## C2–C3 PASS / main one-shot dispatch

census_tests focused fake suite7passed; independent census_review repeated
fake suite7passed, T0/dry source_reads0/writes0, officialroot absent before/
after, all static frozen science/partial/budget/map paths PASS. The source
contract binding correction was independently verified against the adapter
and writer, not inferred from the earlier mistaken report.
Main accepts implementation and dispatches exact frozen command ONCE under
ongoing literal user grant, UUIDf4a0ff0d-b538-4fed-bb2d-41c398daa3fb. No
repair/rerun/resume/extra source/graphs/tuning. This authorizes the six-graph
decoder-free census only, not construction or performance experiment.
Actual C4 independent review/main acceptance remain pending.

## Post-attempt resource-unit defect / no rerun

The one attempt completed6/6. Main identified implausible33072 B RSS;
operator read-only confirmed Linux getrusage.ru_maxrss is KiB and the
implementation incorrectly left it unconverted when /proc exists. Raw33072
means33865728 B (~32.29 MiB), a high-water peak, not instantaneous RSS.
Original census/manifest records remain unchanged as failed-unit evidence;
C4 must independently convert raw RSS and verify the actual1GiB cap. No
acceptance from the operator or automatic zero-resource-violation inference.
Only the default RSS implementation may receive the minimal KiB-to-byte fix
plus a mock-unit test; no source/metric/budget/scientific change, no census
rerun, repair, continuation or overwrite. Existing recorded science metrics
belong to the pre-fix one-shot implementation. Final review/RESULT must carry
the unit correction and distinguish observed budget from the defective gate.

## C4/main acceptance supersedes historical pending states

Independent census_review source/adjacency/all51-cut/full-spectrum/map review
PASS_WITH_FINDING; main accepted six completed descriptive records with
RESOURCE_UNIT_CORRECTED_POST_HOC qualification. Linux peak raw33072 KiB
is33865728 B=32.296875 MiB; actual bound is verified retrospectively, not a
correctly functioning original runtime guard. Original JSON remains unchanged;
log EOF/RESULT/INDEPENDENT_ACCEPTANCE carry authoritative correction. Code-only
unit fix and focused mock suite8passed; no scientific rerun. Prior PLAN/C3/C4
pending phrases record historical states and are superseded by this acceptance.
One-shot grant consumed, no repair/resume/extra arm. C5 document consistency
review remains the only outstanding milestone check, not new execution.

C5 independent document-consistency review passed all numerical/provenance/
ceiling/unit checks. One ambiguous log phrase "no source edit" was clarified
by append-only EOF: no source-data/matrix edit, while the recorded code-only
RSS helper fix did occur. Main accepts closeout; no outstanding batch work.
