# BP stopping cap90 versus250 — EXPLORE

2026-10-01. FROZEN v1 / ONGOING GRANT / PLAN REVIEW PENDING.
UUID eb0eb231-b295-4c1c-9ddd-4d775bc74352.
Fresh root workspace/gf32_itercap_eb0eb231/.
User ongoing grant verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Apply ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. This is a new bounded
synthetic successor,not a repair/replay of consumed earlier batches. Independent
PLAN/implementation/main dispatch and batch-end review remain required; no
new per-item user reply within this ongoing scope. Nearest planning draft
../NBLDPC-NEXT-MECHANISM-20261001.md is superseded for THIS experiment by I1–I3.
Accepted c4fab9ba observed46rawfail frames whose MRB order1 sets excluded
truth; motivation only,not a pooled baseline or route decision. Old M3D
250vs300 uses a different decoder/input contract and grants are not reused.

## I1 Fixed inputs and the sole experimental delta

Six accepted deep H0D graphs from SEARCH-DEPTH21cc2d44: seeds2026093901..3906,
GF32poly37,n128,m52,E256,variabledegree2/checkdegrees4x4+48x5,fullrank52,
same support/degrees/connected admission. Build/admit each graph and deep
candidate once,share same deepH in both arms. Retain search_runner graph
builder/preflight/_candidate_pair_for_graph behavior,no new label/graph search.
PMF p0=.550; other nonzero errors1/3/7/15/31 use .450 times
2295/1126/557/304/146 divided4428; all other symbols0. Synthetic iid marginal-
shape proxy only,Bobzero/matched prior,v35 floor1e-15/normalize/log retained.
No real/private/raw input read,prior fitting or channel qualification.

Same v35 decode_row_layered_fftqspa updates,damping_alpha1.0,warm_beliefsNone,
fieldNone. Control max_iter90,candidate250 ONLY. Explicit arm callbacks bind
the two caps; no global MAX_ITER mutation/call-order-derived arm/hidden rescue.
No MRB/OSD/otherdecoder/extra damping/iterations scan/dependency installation.
One seed per pair from
v10_seed('gf32-itercap-v1:holdout:{graph_seed}:{stream}:{frame}'),
sixgraphs x2streams x16frames=192pairs/384BPcalls. New namespace/unique seeds;
disjoint from prior accepted namespaces. Evenframe control first,oddframe
candidate first. Pair H/prior/syndrome immutable equal values,synthetic truth
used to generate syndrome then read by observation AFTER BP only. BP receives
only H/prior/syndrome. Retain same original truth; no second sampling/decoding
for evidence. Save raw_x_hat from the SAME returned DecoderResult.

Independent GF32 syndrome recomputation and raw-symbol equality with truth
determine exact AND syndrome success. Syndrome-valid wrong stays separate
failure; decoder `converged_exact` never means truth-exact. Record status,
iterations,cap,raw symbol equality,syndrome,exact,wrong,full arm wall/RSS and
input/graph/frame/seed/arm lineage. Cap bounds0..cap and raw-syndrome-fail
iterations==cap required. Same-input prefix guards: control syndrome-pass
implies candidate same raw vector/status/iteration; control syndrome-fail
implies candidate cannot first pass at<=90iterations. Violation STOP with
both rows/evidence retained,no integrity claim promotion.

## I2 Reporting, practical screen and artifacts

Report allsixgraph counts/Delta_g,paired both/controlonly/candidateonly/neither,
perarm exact/validwrong/fail/iterations/cost and full denominators. Report
control90fail→candidate250exact/validwrong/stillfail transitions; also
control-valid outcomes' prefix consistency. No selected best graphs or samples.
Frozen practical screen: controlexact in[39,153] inclusive,Delta>=12,
positiveDelta_g>=4/6,zero integrity/resource/auth violations =>MECHANISM_SIGNAL;
outofrange=>CONTROL_RANGE_UNINFORMATIVE;otherwiseNO_SUFFICIENT_SIGNAL.
This is only this finite synthetic screen,not significance/causal/route gate.
Partial/orphan/STOP retains attempted rows and vectors; complete performance/
pergraph/paired/transition totals null. No posthoc grid/threshold changes.

Tag0,verificationNOT_IMPLEMENTED,undetectedNOT_MEASURED;260syndromebits per
attempted arm inclfailure,complete99840bits. No FER/f_eff/SKR/throughput/
security/qualification/publication/realchannel/route/crossbatch pooled ranking.
Zero wrong is not a verification/undetected bound. Keep each independent batch
separate; no HDC/LB void baselines or permanently forbidden TABLE columns.

Exactly five files in freshroot: manifest.json,frame_records.csv,summary.json,
EXPLORATION_LOG.md,diagnostics.npz. Identity/contract/newseed/armcaps/track
consistent in returned/persisted summary/manifest/log. NPZ stores sixpublicH,
synthetic pairtruth/syndrome,percallraw_x_hat and explicit pair/call/arm/cap/
graph/stream/frame/seed mappings. No beliefs/MRB distances needed. Save only
available validated vectors with explicit mapping for failed/unmapped rows;
do not invent zeros as successful observations. Payload cap20MiB; independent
peer can reconstruct every exact/syndrome/wrong outcome without rerunning BP.

## I3 Budget, implementation and independent gates

One process1800s inclconstruction/artifacts,4GiB sampledRSS,120s synchronous
full arm afterreturn,384BP/0OSD calls. Budgets are limits,not runtime estimates.
Check before/after graph/deepconstruction and each arm,on exceptions,around
finalwrites. Preserve original error plus all observed resource STOP markers,
even if later writecap follows earlier exception; stop nextcall. Record actual
batchwall/maxarm/RSS samples/scope and write-boundary exclusions explicitly;
small finalsummary/log cost need not trigger recursive rewrites. Trusted-local
I/O error may nonzeroexit with partialroot; no incomplete five-artifact set
accepted. Freshroot refusal/no overwrite,zero science repair/rerun/resume/
extra samples. Ordinary pre-science fake-test corrections permitted with
unchanged packet. Numerical/graph/rank/prefix/cap/resource mismatch STOP.

Allowed ONLY new cli/nbldpc_gf32_itercap_probe.py and
comparison_bench/tests/test_nbldpc_gf32_itercap_probe.py. Minimal local paired
loop plus accepted pure graph/PMF/sample/armorder/GF helpers; do not clone an
800line runner wholesale or patch old modules. Local explicit raw-result
observation/NPZ capture necessary,not a generalized runner/config framework.
No hashes/locks/atomicwrites/retry/backup/schemaframework or newdependency.
Frozen Polar/results,unrelated dirtyworktree,old artifacts unchanged. No
commit/push/merge/archive/add-A. Operator iter_operator owns only CLI;
designated test operator owns only newtest after explicit root release.
iter_contract independent reviewer; root scope/threshold/acceptance. Workers
notalone,preserve others; operators cannot selfaccept. Tests must use explicit
fake graph/preflight/deep/BP; never invoke production work implicitly.

Exact command after independent implementationPASS/T0/rootabsence/mainDISPATCH:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_itercap_probe --execute --out-root workspace/gf32_itercap_eb0eb231`

P1 retainedgraph/source/field/newseed/caps/armbinding,productionspy only cap
differs/no globals/noMRB; P2 actualexecute fake384calls/192pairs with real
sampler spy,sharedinputs/alternation/newseed,all outcome transitions/wrong/
disclosure,real returned/disk/manifest/log identities and NPZ mapping (never
stub actualsummary); P3 vector-derived exact/syndrome,prefix guards/bounds/
failure-at-cap with nonmutation; P4 partial/orphan/unmappedvector/nulltotals,
call/total/RSS exception/postprocess/writecap STOP including primaryerror+
laterresource marker,no nextcall/rootrefusal; P5 focused tests/compile/T0zero
inputreads/writes/science/graph/BP/OSD and rootabsence; P6 independentPLAN/
implementation/actualvector+math/resources/ceilings batch review; P7 main
acceptance and compact RESULT/INDEPENDENT_ACCEPTANCE/projectmemorytriage.
WSLrepo.venv pytest -p no:cacheprovider -o addopts='',fresh writable testroot.

## Independent PLAN / implementation release

iter_contract I1–I3/P1–P7 PLAN PASS,no blocker. Actual v35 cap/prefix semantics,
fixed science/screen,vector evidence,partial/resource/no-rerun limits and
OpenSpec consistency checked. Root/newtwofiles absent before implementation.
120s synchronous cap is an after-return check,not a decoder-interruption
mechanism; no stronger enforcement claim. Main accepts PLAN and releases
ONLY newCLI to iter_operator and ONLY newtest to iter_tests. Explicit required
graph/candidate/preflight/decoder callback API means fakeentry cannot default
to production. Same-call local capture through accepted observation helper
is permitted; no second decoder call/hidden globalstate. Independent reviewer
iter_contract edits neither file. Main dispatch/actual scientific acceptance
remain pending. Scientific inputs/thresholds/UUID/seeds/root unchanged.

Fake evidence matrix clarification: the192-pair real-sampler-spy execute
test need not produce a practical mechanism signal or every transition. A
truth-blind fake with rank52 H=[I52|0] cannot infer76kernel symbols from
syndrome. Retain that actual-entry/input-seam test; cover exact/alltransition/
screen branches with tiny pure observation/actual-summary scripted-vector
fixtures or a separately explicit test-only scripted source. No hidden truth
oracle in BP. Combined P2/P3 coverage satisfies the frozen matrix; scientific
inputs/decoding/output requirements are unchanged.

## Main implementation acceptance and one-shot dispatch — 2026-10-01

Independent iter_contract P1–P5 PASS: focused suite 18 passed in 3.28s,
exit 0 (only existing pytest cache_dir warning); dry-run DRY_RUN, all T0
true, zero reads/science/graph/decoder/OSD/writes, official root absent
before and after. Reviewed fixes and full frozen fake matrix; no blocker.
Main accepts implementation only and dispatches the exact frozen command
under the ongoing user grant for UUID eb0eb231-b295-4c1c-9ddd-4d775bc74352.
One attempt only; no science repair/rerun/resume/extra arms. Operator retains
all artifacts and returns execution evidence without self-acceptance.
Actual batch independent review and main scientific acceptance remain pending.
