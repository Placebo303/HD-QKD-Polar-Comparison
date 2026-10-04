# Fixed-code probability damping mechanism — EXPLORE

2026-10-01. State **CLOSED / MAIN ACCEPTED**.
UUID `a3444f81-f091-4ffd-9c16-393c6062f6e3`.
Fresh root `workspace/gf32_damping_a3444f81/`.
User ongoing grant verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Within ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md, one bounded synthetic
successor,no new user reply needed. Independent implementationPASS/main
dispatch required. No scientific repair/rerun/resume/extra frames or scan.

## D1 Fixed conditions and single change

Keep accepted deep H0D from SEARCH-DEPTH21cc2d44 as the common matrix for
both arms, same frozen six3901..3906 D10 graph seeds,n128,m52,E256,
poly37,degree2x128/check4x4+5x48,all-six original graph/controlrank52/
support/connected/admission and max8/no-change reconstruction rules.
Keep exact sparsePMF p0=.550,p[e]=.450*{1:2295,3:1126,7:557,15:304,31:146}/4428,
others0,iid/Bob-zero matchedprior,existing1e-15 numericalfloor/normalization,
layeredFFT-QSPA maxiter90,warmNone,fieldNone and stopping/iteration schedule.
No label optimization beyond accepted deep reconstruction,no newgraph/source,
no actual source read,fitting,conditional model,pilot/grid/noise selection.

Control uses existing production_decode_fn damping1.0. Candidate local thin
adapter calls the exact same v35 decoder with ONLY damping changed to0.5;
return its DecoderResult unchanged. Code uses alpha<.999 probability-domain
mix p_damped=(1-alpha)*softmax(old)+alpha*softmax(new),then existingfloor,
normalization/log. Freezealpha=.5,not an adaptive schedule or extra iteration.
Preserve external keyword mapping from actual source; no olddecoder edits.
This tests fixed smoothing's recovery effect,not observed oscillation,
convergence theory or MAP optimality. No claim that code geometry improved.

## D2 Sequence, samples and measured semantics

No-write tiny T0; all6 graph/control admission; then6graphs x2streams
x16frames=192pairs/384calls. New seed
v10_seed('gf32-damping-v1:holdout:{graph_seed}:{stream}:{frame}').
Same immutable H,error,prior,syndrome within pair; evenframe controlfirst,
oddframe candidatefirst. Explicit arm decoder dispatch; never infer arm
frommatrix content/id or mutable call-order state. No production decoder
fromtests; explicit fake callbacks required on botharms. No sampled arrays
exported. Record decoder branch/damping/maxiter/iterations/status alongside
accepted observation flags. Iterations0 initialsyndromehit is valid,<=90.
Success=exact AND syndrome_accept; syndrome-consistent-wrong independent
failure. status converged_exact alone is not truth exact. Verification
NOT_IMPLEMENTED,undetected NOT_MEASURED,tag0,260syndromebits perattempt
including failures. Disclosure total99840 ifcomplete,not a security claim.

## D3 Frozen practical screen and incomplete outcomes

Complete192pair screen: control39..153 inclusive,Delta(damp.5-damp1)>=12,
positiveDelta_g>=4/6,zerointegrity/resource/authviolations. Alltrue
MECHANISM_SIGNAL; controloutside CONTROL_RANGE_UNINFORMATIVE;otherwise
NO_SUFFICIENT_SIGNAL. No gauge gate because matrices identical. These are
practical EXPLORE screens,not significance/route/qualification/real-data
claims. Report everygraph,pairedfourstates,actualiterations and perarm
runtime; no best-arm/source selection or comparison pooled with priorbatches.
Partial attempts/pairs retained but comparison/pergraphperformance/fourstates
unknownnull; orphan cannotgain. Resource/exception/admission STOP not a
completed performance screen. Never add iterations or alteralpha afteroutcome.

## D4 Resources, scope and artifacts

Singleprocess1800s totalincludingconstruction,120s synchronouscall afterreturn,
4GiB RSS,384call cap; resourcechecks before/after everyreturn evenexceptions,
preserveerror/resource markers and no nextcall. Persist actual batch_wall_s,
max_call_wall_s and max_rss_bytes using acceptedmeasurementAPI,includingSTOP;
describe RSS measurement scope,do not invent historicalmissingvalues.
Freshroot manifest.json,frame_records.csv,summary.json,EXPLORATION_LOG.md only.
No overwrite/retry/resume. Allowed new cli/nbldpc_gf32_damping_probe.py and
comparison_bench/tests/test_nbldpc_gf32_damping_probe.py only. Reuse pure
helpers and two explicit decoders,avoid generic scanframework/globalmutation.
OpenSpec explore-gf32-fixed-damping precedes implementation.

Exact scientific command after independentPASS/maindispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_damping_probe --execute --out-root workspace/gf32_damping_a3444f81`

Forbidden real/private/raw/NPZ/TTBin/parquetreads,n256,newgraph/prior/label/
schedule,maxiterchange,FER/f_eff/SKR/throughput,qualification/publication,
route DECIDE,pooling/rankingacrossbatches,voidbaseline,prohibitedTABLEcolumns,
commit/push/merge/archive. FrozenPolar and unrelateddirty files preserved.

## D5 Complete acceptance matrix

P1 sameaccepteddeepcode/source/prior/syndrome/field/maxiter/warm,UUID/newseeds,
192pairs384cap; P2 fake spy v35 adapters only differdamping1/.5,rawresult
preserved,convexmix alpha semantics,explicitarmdispatch no id/state tricks;
P3 fake paired sharedinputs/order,newunique seednamespace,0/90iterations
andbranchmetadata,exact+syndrome/wrong,status nottruth,260bitsperattempt;
P4 fullDelta12vs11/positive4vs3/controlrange/zero violations,no gaugetest
asperformancegate,all6 pergraphcounts andfourstates,no subsets;
P5 graph/controlSTOP,partialpair+orphan nullaggregates,postexception
call/total/RSScaps,no nextcall,actual persistedtimingRSS/rootrefusal;
P6 focusedfake/tiny tests,dryrun0graph/decoder/input/writes,no accidental
production defaults in tests; P7 independentplan/implementation then raw
batch math/inputs/decoderparam/accounting/resources/grant/ceiling review;
P8 mainacceptance/append-onlyprojectmemory/decisionlogtriage.
WSL repo.venv,focusedpytest -p no:cacheprovider -o addopts='',freshtestroot.
Workers notalone/preserveothers/return complete matrix or exactblocker.
Independent reviewer!=operator; main owns scientificscope/acceptance.

## Independent plan review / implementation release

faithful_scope D1–D5 PLAN PASS. Actual v35 keyword binding is max_iter=90,
damping_alpha=1.0(control) or0.5(candidate),warm=None,field=None. Candidate
returns the same rawresult type; only damping_alpha differs. Main accepts
and releases two-file implementation/fake tests. shape_closeout owns both
new damping CLI/test after census closeout,faithful_scope independent review.
No actual graph/decoder run before independent implementationPASS/main
dispatch. No new user reply within ongoing boundedsynthetic grant.

## Independent implementation acceptance / main dispatch

faithful_contract P1–P6 PASS after fake-only endpoint coverage correction:
16 focused tests independently passed in3.50s, compile/dry-run PASS,
0 input/graph/candidate/decoder/write, fresh result root absent. The only
gap was legal raw iterations=90 coverage, now explicitly checked in both
arms with truth/syndrome/status/disclosure semantics; CLI unchanged.
Old R21 S0/m100/shifted-source NO-DAMP-GAIN remains accepted in its own
scope. faithful_scope independently confirmed its graph/source contract
differs from the current deep GF32/p0=.55 batch; no reopening or overturning
is claimed. Main verifies intended formal-IR branch, no tracked frozen
baseline differences and output absence, accepts implementation and
dispatches exact frozen command once under ongoing grant. Operator is
shape_closeout; faithful_scope performs independent batch review.

## Independent batch-end review and main acceptance

`faithful_scope` independently passed P7; reviewer != operator. Main accepts the completed 192-pair/384-call observation with terminal `CONTROL_RANGE_UNINFORMATIVE` (control=154 is above the frozen maximum 153). Exact successes were control=154 and candidate=153, Δ=−1; paired states both/candidate-only/control-only/neither=153/0/1/38. Per-graph deltas for seeds 2026093901–2026093906 were `[0,0,-1,0,0,0]`. Iteration totals were 4533/5663; per-arm decoder-wall sums were 27.204686/43.927295 s. Batch wall=121.964675789 s, max call=0.712394023 s, API-sampled max RSS=102313984 B. Wrong rows=0, verification=`NOT_IMPLEMENTED`, undetected=`NOT_MEASURED`, disclosure=99840 bits, tag=0, and integrity/resource/authorization violations=0. The reviewer checked seed/metadata/lineage but did not re-create unsaved truth/prior vectors value by value. No sufficient evidence supports recommending alpha=0.5; retain alpha=1.0 as the source-label frozen decoder setting without treating this as a route decision. Historical R21 S0/m100/shifted-source `NO-DAMP-GAIN` remains unchanged in its separate scope. No further run, resume, iteration increase or alpha change follows this packet.
