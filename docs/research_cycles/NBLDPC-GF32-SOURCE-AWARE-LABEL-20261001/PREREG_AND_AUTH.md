# Source-aware edge-label objective — EXPLORE

2026-10-01. State **CLOSED / RETAINED FAILURE / MAIN ACCEPTED**.
UUID `f6fbf8cf-8773-4099-af68-54136326b60d`.
Fresh root `workspace/gf32_source_label_f6fbf8cf/`.
User ongoing grant verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Apply ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. One bounded synthetic
successor; no new user reply required. Execution awaits accepted complete
source-overlap202e39a1, independent implementation PASS and main dispatch.
No scientific repair/rerun/resume/extra frames or adaptive grid.

## S1 Fixed comparator, inputs and single change

Reuse SEARCH-DEPTH21cc2d44 accepted deep H0D as control and candidate start,
six seeds2026093901..3906, D10 n128/m52/E256, GF32 polynomial37,
variabledegree2x128/check4x4+5x48, same graph construction/deep max8/no-change
rules and all-six support/degree/connected/rank52 admission. Reuse accepted
census475c2ad3 canonical support cycles ell2..6 and accepted source-overlap
202e39a1 exact PMF/B formula. Read only these derived artifacts; no raw data.
At science time reconstruct accepted deep H deterministically and check every
saved control cycle coefficient against its actual (row,column) incidence.
Check six complete inventories and distinct sorted variable-support tuples
within each graph. If these do not hold, STOP; do not silently deduplicate.
For degree-two simple cycles, distinct support establishes distinct orbits;
thus the objective below is exactly the unique-orbit sum for this inventory.

Source p0=.550, p[e]=.450*{1:2295,3:1126,7:557,15:304,31:146}/4428;
all other probabilities exactly0. Mathematical B uses no decoder floor.
B(z)=sum_e sqrt(p(e)*p(e XOR z)). For a unit-product cycle with normalized
local codeword c, W(c)=sum_lambda=1..31 product_v B(GFmul(lambda,c[v])).
Nonunit cycle has contribution0 internally and reported W=null. Unit W=0
remains distinct from nonunit. F_g=sum of cycle contributions, dimensionless.
No probability, FER, global MAP bound, distance or security interpretation.

Candidate replaces the entropy-J coordinate objective with F_g minimization.
It does NOT start from the previous EDGE candidate and does NOT add another
J sweep. No pivot-column freezing, rank-preserving search constraint or
global graph/source/decoder changes. Final rank52 is an admission gate,
not an optimized performance score. The materially simpler alternative is
unit-cycle-count minimization; it ignores the frozen source's zero overlaps
and is deferred, not included as another arm.

## S2 One deterministic coordinate pass

Visit all256 nonzero edges once in sorted (row,column) order. For each edge
evaluate absolute nonzero GF32 labels beta=1..31, including current beta.
Only cycles containing that edge change; recompute their exact GF product,
unit witness and W, retaining all other contributions. Sum with math.fsum.
Freeze dimensionless TIE_TOL=1e-14: find smallest numeric F; if current F is
within TIE_TOL of that minimum, retain current beta, otherwise choose the
smallest beta within TIE_TOL of minimum. Commit only if current-minus-chosen
F>TIE_TOL. No revisits, early target stop, rollback or extra sweep. Edges
in no enumerated cycle retain current. At most256 changes per graph.
For each committed coordinate recompute full F from the same fixed cycle
list as a reference; drift>1e-12 or material increase>1e-12 triggers STOP.
Final full-reference F, cycle products/unit counts/W and rank are recorded.
Do not clamp negative costs or silently restore a different candidate.
Final support/degree/connected/rank52 must hold for every graph; otherwise
entire batch stops before decoder sampling. Unchanged/zero-improvement and
row-column-gauge-equivalent candidates remain in all192 pairs if admitted.
Report full row+column gauge status using accepted edge-label witness helper
as a diagnostic; gauge status is not a performance gate for nonuniform P.

## S3 Paired decoder measurement and frozen screen

Both arms use the same existing layered FFT-QSPA, max_iter90,
damping_alpha1.0, warmNone, fieldNone, prior numerical floor1e-15 and its
existing normalization. No damping change from the separate damping batch.
No pilot. Six graphs x2 streams x16 frames=192 pairs/384 attempted calls.
Seed v10_seed('gf32-source-label-v1:holdout:{graph_seed}:{stream}:{frame}').
Same immutable error/prior within pair; arm-specific syndrome from its H;
even frame control first, odd candidate first. No sampled arrays exported.
Success=exact AND independently recomputed syndrome_accept. Syndrome-
consistent wrong remains a separate failure; decoder status is not truth.
Verification NOT_IMPLEMENTED; undetected NOT_MEASURED; tag0; syndrome
260 bits per attempted call including failure, complete total99840 bits.

Complete screen requires control39..153 inclusive, Delta(candidate-control)
>=12, positive per-graph Delta>=4/6, F reduction>TIE_TOL in>=4/6 graphs,
and zero integrity/resource/authorization violations: MECHANISM_SIGNAL.
Control outside range: CONTROL_RANGE_UNINFORMATIVE; otherwise completed
NO_SUFFICIENT_SIGNAL. These are practical EXPLORE screens, not statistical
significance, causality, FER/SKR qualification or route-closing decisions.
Report all six graphs, paired four states, objective reductions, unit/zero/
positive inventory, iteration counts and per-arm costs; no subset selection.
Incomplete pair/orphan/STOP retains attempts but batch/per-graph performance
and paired totals are null/unknown. Do not convert availability into gain.

## S4 Budget, artifacts, exact scope

One process1800s total including reconstruction/label search; 4GiB RSS;
120s synchronous decoder call checked after return; 384-call cap;
47616 label trials maximum; 2,000,000 affected-cycle evaluations maximum.
Check resources before/after each coordinate and decoder call, including
exception returns; no next coordinate/call after STOP. Retain original
error plus any resource marker. Persist actual batch_wall_s, max_call_wall_s
and max_rss_bytes with accepted API/sampling scope, including STOP.
Exactly manifest.json, frame_records.csv, summary.json, EXPLORATION_LOG.md.
Summary records all coordinate updates and objective/full-reference checks,
cycle coefficients/products/witness/W, final gauge evidence and actual costs.
No dense sampled source/truth/prior arrays. Fresh root refusal/no overwrite.

Allowed new cli/nbldpc_gf32_source_label_probe.py and
comparison_bench/tests/test_nbldpc_gf32_source_label_probe.py only. Reuse
accepted pure graph/deep/cycle/overlap/observation helpers, minimal local
algorithm; no generic optimizer, Counter framework or old module edits.
OpenSpec explore-gf32-source-aware-label precedes implementation.
Exact science command after independent PASS/main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_source_label_probe --execute --out-root workspace/gf32_source_label_f6fbf8cf`

Forbidden real/private/raw/NPZ/TTBin/parquet reads, newgraphs/n256/newprior,
maxiter/damping/schedule changes, longer/joint cycles, source fitting,
cross-batch pooling/ranking, void baseline/prohibited TABLE use,
FER/f_eff/SKR/throughput/publication/qualification/route DECIDE,
commit/push/merge/archive and frozen Polar/unrelated dirty file edits.

## S5 Complete acceptance matrix

P1 exact predecessor, six graph/source/cycle inventories, source-support
uniqueness and coefficient-incidence match; P2 direct B/W GF math, scalar
orbit invariance, unit-zero/nonunit-null distinction and deterministic ties;
P3 tiny fixed-cycle coordinate pass, all31 absolute labels, single sweep,
incremental/full F agreement, tolerance boundary, no cycle/no improvement,
rank-fail STOP and all admitted graphs retained; P4 explicit paired fake
callbacks, new seeds/order/shared errors/arm syndromes, truth/status/wrong,
260 bits per attempt and screen boundaries including F-reduction count;
P5 construction/search/reference/resource/exception STOP, partial/orphan
null summaries, no next call, caps/cost persistence and existing-root refusal;
P6 focused fake/tiny tests, compile, no-write T0 with0 input/actual graph/
decoder/write calls; tests never default to production runners;
P7 independent plan/implementation and raw batch math/coefficient/parameter/
screen/disclosure/resources/grant/ceiling review; P8 main acceptance and
append-only projectmemory/decisionlog triage. No new checksums/framework.
WSL repo .venv, pytest -p no:cacheprovider -o addopts='', fresh test root.
Workers are not alone; preserve others. Return complete frozen matrix or
concrete blocker. Operator != independent reviewer; main owns acceptance.

## Independent plan review / implementation release

faithful_scope PLAN P1–P7 PASS: degree-two unit-cycle witnesses extend by
zero to full codewords; distinct supports imply distinct scalar orbits.
Affected-cycle evaluation upper estimate1075886 stays below2M cap; full
reference recomputations after commits are separate, at most4647936 cycle
calculations by the conservative whole-inventory estimate. Record both
counters separately; both remain inside1800s total resource budget. This is
a counting clarification, not an extra sweep or changed scientific input.
Main accepts plan and releases two-file implementation/fake tests to
faithful_contract after its damping narrow review. faithful_scope reviews
source-label implementation and final batch independently. Actual run still
requires independent implementation PASS/main dispatch. Source-overlap202e39a1
is independently reviewed/main accepted; scoped closeout underway.

## Independent implementation acceptance / main dispatch

faithful_scope independent P1–P6 PASS,20 focused fake tests/compile/T0
passed;0 actual census/empirical reads,graph/decoder/write calls,root absent.
Delta checks cover coefficient-incidence/support uniqueness,exact PMF/W,
all31-label one-pass/ties/full reference/final rank,paired observations,
disclosure/screens and partial/resource semantics. Before first science,
CLI operator fixed no-cycle graph_seed retention and actual accepted row
helper binding; test operator corrected an inconsistent fake syndrome flag.
No scientific attempt preceded these engineering fixes. Source-overlap
202e39a1 is closed/mainaccepted. Main accepts the independent review and
dispatches exact frozen command once under ongoing grant on formal-IR branch.
faithful_contract operates; faithful_scope independently reviews final batch.
No extra implementation review by the CLI operator is required or allowed
as self-acceptance. Costs/objectives are still exploratory until batch review.

## Retained failed attempt, independent review, and main closeout

The one dispatched attempt stopped at predecessor loading with
`PREDECESSOR_STOP`: `comparison_bench.cli.nbldpc_gf32_cycle_census` has no
`load_predecessor` attribute. The six fixed control graphs had already been
constructed and admitted at GF(32) rank 52; this was not a zero-graph attempt.
No cycle inventory was loaded, so the source-label pass did not start. Label
trials, affected-cycle evaluations, full-reference evaluations, decoder calls,
frame rows, and actual syndrome disclosure were all zero. Control/candidate
successes, delta, per-graph performance and all paired states remain unknown
(`null`); no performance or objective result was measured.

The retained attempt used 49.0868816 s wall time and 101711872 B maximum
sampled RSS over 27 samples; maximum decoder-call wall time is null because no
decoder call occurred. Integrity, resource and authorization violations were
zero. The four original machine artifacts are retained; this closeout only
appends review/acceptance to the exploration log and does not overwrite them.

Independent `faithful_scope` failure review found that the earlier
implementation record overstated P1 loader coverage: the accepted-loader
binding was not exercised by the fake tests. The earlier P1 loader-coverage
PASS is withdrawn. Main accepts this batch only as a retained
`PREDECESSOR_STOP` / `INCOMPLETE` failure record. This is not a source-label
performance result, a scientific-mechanism rejection, a route decision, or
promotion. No repair or rerun is made under this packet. The preceding
implementation-acceptance/dispatch section remains as history of what was
recorded before the independent failure review; this closeout supersedes its
P1 loader-coverage claim.
