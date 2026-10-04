# Edge-label update beyond column scaling

2026-10-01. Track **EXPLORE**. State **CLOSED / MAIN ACCEPTED**.
UUID `1efed423-10c8-4c51-a119-844f2b922ab5`.
Fresh root `workspace/gf32_edge_label_1efed423/`.
New user grant verbatim, directly referring to the preceding edge-label proposal:

> 可以继续

One bounded synthetic batch after independent implementation review and main
dispatch. Previous grants consumed; no rerun/repair/resume/additional frames
or automatic successor. All actual graph/decoder work waits for dispatch.

## F1 Authority, hypothesis and fixed conditions

Retain from ../NBLDPC-GF32-SEARCH-DEPTH-20261001/PREREG_AND_AUTH.md:
n128,m52,E256,GF32 poly37,D10 PEG,variable degree2x128/check4x4+5x48,
fixed seeds2026093901..2026093906 and same-seed coefficients; all-six
degree/socket/connected/no-duplicate/structural and GF32 rank52 gates.
Retain p0=.550 and nonzero shape{1:2295,3:1126,7:557,15:304,31:146}/4428,
exact other zeros, iid/Bob-zero matched prior. No real input, fitting,
conditional model, pilot/grid/noise selection. Decoder unchanged production
adapter/layered FFT-QSPA maxiter90,damping1,warmNone,fieldNone with existing
1e-15 prior floor/normalization. Previous batch NO_SUFFICIENT_SIGNAL
onepass146/deep149,Delta3 remains unchanged; no pooling/ranking across batches.

Control reconstructs accepted deep H0D using unchanged search-depth helper,
max8 total sweeps/no-change stop and all accepted admission/drift rules.
Candidate starts from this control matrix and performs exactly one
deterministic row-major sweep over all256 nonzero edges. For each edge
(r,v), try absolute GF32 coefficients beta1..31, maximize the same analytic
check-entropy objective J=sum_r H(XOR_v h[r,v]E_v). Only row r changes;
use accepted GF multiplication/PMF permutation/XOR convolution and entropy.
Tie tolerance1e-12, retain current coefficient if in tie set, otherwise
smallest tied beta. No decoder scores, data-dependent labels, restart,
second sweep, graph replacement or alternative objective.

Record control reconstruction trajectory, candidate initial/final J,
per-edge chosen coefficient/change count and sweep count1. Full recomputed
J versus accumulated row-entropy increments drift>1e-10 or J decrease
>1e-10 is construction STOP, no rollback/repair. Candidate must retain
support/degrees and full GF32 rank52. Nontriviality, J gain and leaving
gauge class are diagnostics, not admission filters: unchanged/no-J-gain/
gauge-equivalent candidates remain in the full paired comparison.

Question: does this fixed edge-wise update yield a practical signal beyond
the accepted column-scaling control, and does it actually change cycle
invariants? J growth alone is not success, causal mediation or distance gain.

## F2 Full row-column gauge diagnostic

Compare candidate B to control A on identical connected bipartite support.
For each edge form R[r,v]=B[r,v]/A[r,v] in GF32. Fix row potential a[0]=1.
Use deterministic BFS spanning tree rooted row0 with ascending neighbor
indices; propagate R=a[r]*d[v] on tree edges. For each of the77 non-tree
edges (E-(m+n-1)), record residual R/(a[r]*d[v]). All residuals1 iff
B=diag(a) A diag(d); a nonunit residual witnesses a changed independent
cycle product. Record tree edges/potentials/non-tree residuals and witness
edge, not just a boolean. Zero/unreached/inconsistent support is STOP.
An altered column-edge ratio or being outside H0D alone cannot prove leaving
the full row+column gauge class. No universal new-cycle/distance claim.
Report equivalent/non-equivalent per graph; do not remove any graph based
on this diagnostic. A same-gauge result leaves this mechanism unresolved.

## F3 Paired execution and interpretation

No-write T0; all6 graph/control/candidate admissions; then6 graphs x2
streams x16frames=192pairs/384calls. New seed
v10_seed('gf32-edge-label-v1:holdout:{graph_seed}:{stream}:{frame}').
Identical sampled error/prior within pair, each matrix's own syndrome;
even frames control(deep) first, odd frames candidate(edge) first. No arrays
exported. Exact AND syndrome acceptance defines success; syndrome-consistent
wrong isolated failure. Verification NOT_IMPLEMENTED,undetected NOT_MEASURED,
tag0,260syndrome bits per attempted call including failed attempts.

Complete192pair practical mechanism screen: control39..153 inclusive,
Delta(edge-deep)>=12,positive Delta_g>=4/6,zero integrity/resource/auth
violations,AND at least4 graphs have a nonunit full-gauge cycle residual.
All true MECHANISM_SIGNAL; control outside range CONTROL_RANGE_UNINFORMATIVE;
otherwise NO_SUFFICIENT_SIGNAL. Report every component separately, including
gain-without-cycle-change; no changed-graph subgroup selection or significance
test. A passed screen is limited to this frozen synthetic setup, not causal
attribution, route decision or random-graph population law. No threshold or
source changes after observing anything.
Partial attempts/pairs remain visible but comparison/per-graph comparison/
four-state aggregates are null/unknown; orphan attempts never pair gain.
Construction/resource/exception STOP is not a complete performance screen.

## F4 Cost, scope and artifacts

Retain singleprocess1800s total including setup/search,120s per synchronous
call after-return,4GiB RSS,384call cap. Resource checks before/after every
return including exceptions; retain original error/status and resource
markers, no subsequent call after STOP. Candidate search never consumes
holdout. No scientific repair/retry/rerun/resume. Fresh root only, four files:
manifest.json,frame_records.csv,summary.json,EXPLORATION_LOG.md. No saved
truth/prior/error/input arrays; expose exact seed/arm/provenance/accounting.

Additive code ownership only cli/nbldpc_gf32_edge_label_probe.py and
comparison_bench/tests/test_nbldpc_gf32_edge_label_probe.py. Reuse pure
helpers; no old module-global mutation/old code or result edits. OpenSpec
explore-gf32-edge-label-update precedes implementation. Forbidden NPZ/raw/
TTBin/parquet/private/real reads,n256,newsource,FER/f_eff/SKR/throughput,
qualification/publication/route claims,cross-batch ranking/pooling,void
baselines,old prohibited TABLE columns,commit/push/merge/archive. Preserve
frozen Polar directories and unrelated dirty files; no git add -A.

Exact command only after independent implementation PASS/main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_edge_label_probe --execute --out-root workspace/gf32_edge_label_1efed423`

## F5 Complete acceptance matrix

P1 unchanged graph/source/decoder/control reconstruction, current UUID/arm
mapping/new seed namespace,192pairs384calls; P2 pure tiny-matrix edge sweep
absolutebeta/tie/determinism/onepass count/support/J/drift STOP and no rank
filtering during optimization; P3 full gauge test on identity,column-only,
row-only,row+column scales and single closing-edge change, plus exact
deterministic tree residual witnesses; disconnected/zero/support error;
P4 paired identicalerror/prior,ownsyndrome/order,exact+syndrome/wrong,
260bits/attempt,complete Delta12vs11,positive4vs3,control bounds,gauge4vs3,
no subgrouping,unchanged candidate still full384 calls; P5 graph/candidate
STOP,partial completedpair+orphan null aggregates,all three resource caps
and decoder exception after-return stop,rootrefusal; P6 focused fake/tiny
tests and no-write dry-run,production D10 graph/decoder never called from
tests; P7 independent plan/implementation review then batch-end raw counts,
gauge witnesses,J/accounting/resources/authorization/ceiling review;
P8 main acceptance and append-only projectmemory/decisionlog triage.

WSL repo .venv,pytest -p no:cacheprovider -o addopts='',fresh test root.
No broad tests absent concrete reason. Operator cannot self-accept or redefine
packet. Main owns science/scope. Workers are not alone; preserve others'
edits, return all frozen items complete or exact blocker and one decision.
One append-only exploration log includes attempts and independent batch review.

## Independent plan review and implementation release

2026-10-01 faithful_scope PLAN P1–P7 PASS; main accepts and releases scoped
implementation. The three graph/gain conditions are separate practical gates,
not proof that cycle changes caused gains; report their per-graph overlap
descriptively without changing thresholds. Single edge sweep is not convergence
or global optimum. Full-gauge tree/residual witnesses are the applicable
algebraic test. Independent implementation PASS/main dispatch still required.

User has additionally granted ongoing bounded synthetic continuation in
../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. This batch retains its own original
verbatim grant and all frozen limits; successors need independent frozen
packets and reviews, but no new per-batch reply within that ongoing scope.

## Independent implementation review / main dispatch

faithful_scope independently reported P1–P7 PASS: focused fake/tiny tests
26passed in4.18s; only known pytest cache_dir warning. T0 dry-run reports
0graph/decoder/empirical input/writes and absent root; gauge cases all pass.
Partial performance remains unknown while completed construction diagnostics
may be retained, wrong isolated from exact+syndrome success. Main verified
formal-IR branch, absent root and no tracked frozen-baseline differences,
accepts scoped review and dispatches the exact frozen command once. Science
evidence remains pending independent batch review/main acceptance. No
posthoc tuning or same-batch rerun; ongoing grant applies only to separately
frozen reasonable successors, not changes to this batch.

## Batch-end closeout and main acceptance

Independent `faithful_scope` batch-end review returned P1–P7 PASS; the
reviewer was not the operator. Main accepted the completed 192-pair/384-call
batch as `NO_SUFFICIENT_SIGNAL`, limited to the frozen synthetic iid
marginal-shape observation. Full measurements, accounting, per-graph J and
cycle diagnostics, review limits, and successor boundaries are recorded in
`RESULT.md`. The immutable dispatch and grant history above is retained.
