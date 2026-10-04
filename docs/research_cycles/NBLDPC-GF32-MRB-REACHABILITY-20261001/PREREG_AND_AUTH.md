# CLOSED / MAIN ACCEPTED — MRB order-1 reachability diagnostic (EXPLORE)

2026-10-01. State CLOSED / MAIN ACCEPTED; this dispatched batch's authorization is consumed.
UUID c4fab9ba-ead1-4c64-8d0b-82177ace721c.
Fresh root workspace/gf32_mrb_reachability_c4fab9ba/.
User ongoing grant verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Apply ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. Independent bounded synthetic
successor, no prior batch repair/rerun/replay. Accepted top6 df44e589 observed
151/151 exact, Delta0 in its own test; motivation only, no pooled comparison.
Reason for this diagnostic: distinguish an order-1 set incapable of containing
truth from a merely truncated enumeration. Simpler coverage-first enumeration
is deferred until reachability is understood, not rejected scientifically.

## R1 Fixed scientific inputs and post-BP diagnostic

Reuse MRB-RESCUE20261001 accepted deep H0D construction/admission: six graph
seeds2026093901..3906, D10 n128/m52/E256/GF32 polynomial37, rank52, same
support/degrees/connected admission. No label search/candidate changes.
p0=.550; for errors1,3,7,15,31 use .450 times2295,1126,557,304,146 divided
by4428; all other symbols0. iid synthetic error/Bob-zero/matched prior only.
Retain v35 floor1e-15, normalize/log; layered FFTQSPA max_iter90,alpha1,
warmNone,fieldNone. No decoder modifications, no true-symbol side channel.
Call raw BP once per frame with H/syndrome/prior only; only after return may
the diagnostic read synthetic truth. No OSD/MRB candidate enumeration,
candidate selection/scoring, rescue, order2, solver or new dependency.

Use the EXACT existing osd_decode_candidates_mrb basis semantics:
reliability=max-minus-second over ORIGINAL final_beliefs, stable ASCENDING
column reliability as the actual helper (least reliable first; equal values
retain original column order), augmented GF32 RREF of
H[:,perm] with original syndrome via gf_rref. Preserve final_beliefs unchanged,
including zeros/ties. free_cols are permuted indices, not original columns.
raw hard is raw.x_hat. D_free counts unequal GF32 symbols between
raw.x_hat[perm[j]] and truth[perm[j]] for j in free_cols. No binary/Gray
distance. Inspect actual helper field, permutation and RREF return semantics
before implementation; use existing GF primitives, not a second decoder.

Require rank52/free76, truth syndrome equality and independent reconstruction
from truth free values using solve_with_free, then inverse permutation and
syndrome equality. Also reconstruct base from raw-hard free values; base need
not equal raw hard. Check D0 iff base equals truth. Truth cannot enter BP,
permutation, base construction or any candidate-selection path. Numerical/
rank/reconstruction inconsistency STOP, never silently omit a frame.

Under these premises D0 implies base=truth; D1 implies truth is in the FULL
all-symbol order1 set, not necessarily top6/cap256 or selected; D>=2 excludes
truth from any order<=1 set in THIS MRB basis. This is finite algebraic
reachability, not a decoding/FER/capacity/security/route result. Do not compute
top6 membership/rank, optimize bases, fit thresholds or expand diagnostics.

## R2 Samples, evidence and reporting

Single arm six graphs x2streams x16frames=192 raw BP calls, new seed
v10_seed('gf32-mrb-reachability-v1:holdout:{graph_seed}:{stream}:{frame}').
Graph/stream/frame fixed ascending; no pairs or comparison pooling. For each
frame record call index/seed, graph/stream/frame, raw status/iterations,
independently checked raw exact/syndrome, stratum raw-exact / raw-syndrome-
valid-wrong / raw-syndrome-fail, rank/free count/D_free, truth-syndrome and
reconstruction/base checks, BP and full diagnostic wall/RSS. Exact AND
syndrome determines raw-exact; inconsistent exact-with-failed-syndrome STOP.

Primary denominator raw-syndrome-fail; report D0/D1/D>=2 and full0..76 histogram
within each stratum, each graph and total, with all denominators. No signal
threshold or route gate. Complete status REACHABILITY_DIAGNOSTIC_COMPLETE;
partial/STOP retains rows but full histograms/complete counts are null.
Verification NOT_IMPLEMENTED,undetected NOT_MEASURED,tag0; disclosure260bits
per attempted BP call incl failures,complete49920bits. No FER/f_eff/SKR/
throughput/crossbatch ranking/qualification/publication/causal/route claim.

Exactly five fresh artifacts: manifest.json,frame_records.csv,summary.json,
EXPLORATION_LOG.md,diagnostics.npz. This NEW synthetic packet explicitly
permits arrays for independent numerical review; old no-array batches remain
unchanged. NPZ saves public H matrices uint8[6,52,128], per-frame synthetic
truth/raw hard uint8[N,128],syndrome uint8[N,52],original final_beliefs
float64[N,128,32],and frame-to-graph/stream/frame/seed mapping. Expected full
array payload about6.4MB (6.1MiB), allowed artifact20MiB. No private/real/raw
data. Incomplete stores completed diagnostic arrays only with mapping; failed
row without diagnostics explicitly distinguished. Independent reviewer must
derive permutation/RREF/rank/distance/unique reconstruction from arrays, not
only trust saved booleans. No saved full RREFs or generic evidence framework.

## R3 Costs, implementation, gates

One process900s incl construction/final artifact writes,4GiB sampledRSS,
120s synchronous BP+diagnostic arm after return;192BP/0OSD/candidate calls.
Resource check before/after each arm, on exceptions and around final writes;
preserve STOP/failed attempt/error/resource markers and stop nextcall.
Record full batch wall, maxcall and maxRSS measurement scope; no invented
absolute peak/throughput. Root refusal/no overwrite,0scientific repair/
rerun/resume/extra frames. Ordinary implementation/fake-test corrections may
occur before first science with packet unchanged; concrete blocker to main.

Allowed ONLY new cli/nbldpc_gf32_mrb_reachability_probe.py and
comparison_bench/tests/test_nbldpc_gf32_mrb_reachability_probe.py. Reuse nearest
accepted graph/source/BP/admission/GF/RREF helpers. Minimal local single-arm
loop, not shared-runner surgery or a generic config/qualification framework.
No old module changes/global mutation, frozen Polar/results edits, checksums,
atomic/locking/retry/backup machinery, package install, commits/push/merge/
archive. shape_closeout operator; faithful_scope independent reviewer; main
owns scope/acceptance. Workers not alone, preserve unrelated work.

Exact science after independent PLAN+implementationPASS/T0/main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_mrb_reachability_probe --execute --out-root workspace/gf32_mrb_reachability_c4fab9ba`

P1 actual basis/field/permutation/free/base semantics, fixed science/newseed;
P2 tiny actual GF32 D0/D1/D2 cases with nontrivial permutation, pivot-changing
base, truth unique reconstruction, rank/numerical STOP; full tiny order1
enumeration allowed only as pure math fixture, not actual graph/decoder;
P3 actual fake BP batch proves no truth passed/no OSD,192 seeds/strata/
denominators/disclosure, original beliefs and NPZ mappings, real summary/
manifest/log identities; P4 partial/failed array mapping,null totals,resource
exceptions/postprocessing/write timing STOP/root refusal; P5 focused tests/
compile/T0zero graph/BP/OSD/science/reads/writes/newroot absence; P6 independent
PLAN/implementation/array-level batch review; P7 main acceptance and accepted-
fact documentation/projectmemory triage. WSLrepo.venv pytest
-p no:cacheprovider -o addopts='', fresh writable testroot. Fake callbacks
mandatory in all execution tests; production decoder never implicit.

## Independent PLAN / implementation release

faithful_scope P1–P7 PLAN PASS after main corrected the originally misstated
descending permutation to actual helper stable ASCENDING reliability. No
implementation/scientific execution preceded that correction. Actual GF32
RREF/solve/inverse mapping,D0/D1/D>=2 premises,truth-after-BP boundary,
single-arm/no-OSD scope,synthetic NPZ payload and partial/resource gates checked.
Full array payload6390528B (~6.10MiB) below20MiB. Final-write resource checks
must be enforced; measured cost may state the small final summary/log write
boundary without self-referential endless summary refresh. Main accepts PLAN
and releases ONLY the two new implementation/test files to shape_closeout.
Independent implementationPASS/T0/absentroot/main DISPATCH still precede the
one scientific command. No original modules or completed batch artifacts edit.

Implementation ownership update (no scientific delta): the initial operator
spent excessive time in planning and confirmed zero writes/science before
handoff. Short-context luna reach_operator produced P2; faithful_contract
independently PASSed5tinytests plus63-candidate full order1 math fixtures
(D0/D1 reachable,D2 excluded). To parallelize remaining work, reach_operator
now owns ONLY new CLI; shape_closeout owns ONLY its test file, retaining P2
and adding frozen P3–P5. Both share explicit callback API and preserve others'
edits. faithful_scope independently reviews both implementation and arrays;
main scientific gates/inputs/root/UUID/caps remain unchanged.

## Independent implementation acceptance / one diagnostic DISPATCH

faithful_contract P2 mathematical PASS (5tests plus tiny fullorder1 proof).
faithful_scope P1/P3–P6 independent PASS: actual production graph/BP wiring,
real source sampler spy and truth-after-BP/noOSD boundaries,192frame fake
NPZ/CSV mappings,strata/disclosure,partial unknown aggregates and resources.
Independent focused11passed,compile/T0all6checks true/zero scientific input
reads,writes,graph/BP/OSD and root absence. Actualfake caught sampler binding
and postwrite-resource accounting bugs before any scientific attempt; both
were repaired and independently checked with retained fake regression cases.
Main accepts implementation only. Branch formal-ir-v72p1-addendum-clean;
root c4fab9ba absent at maincheck. Ongoing user grant applies. Main DISPATCHes
exact R3 command once to reach_operator,900s/4GiB/120s/192BP/0OSD; no rerun/
resume/extra samples. Independent array-level review and main scientific
acceptance remain pending. Operator must not write RESULT/selfaccept/memory.

## Independent array-level P6 / main acceptance

faithful_scope independently recomputed from five artifacts/NPZ all192
truth/raw syndromes,original-belief stableascending permutations,GF32 RREF,
rank52/free76,raw-free base and unique truth reconstruction. All row fields,
strata/graph/fullhistograms agree. Public sixH support/degrees/E256 checked;
seeds/CSV-NPZ mapping complete and unique. Totals146rawexact/D0,0raw-syndrome-
valid-wrong,46raw-syndrome-fail,all46D>=2,D1=0. Pergraph exact/fail26/6,
23/9,24/8,25/7,22/10,26/6. P6 PASS,actual vector/basis evidence,not only
stored booleans. Disclosure49920/tag0;192BP/0OSD,verificationNOT_IMPLEMENTED,
undetectedNOT_MEASURED. Wall89.9558s excluding terminal summary/manifest/log,
maxarm.5948s,sampledRSS121819136B/795checkpoints,NPZ6402852B,zero resource
markers/violations within frozen caps. Main ACCEPTS this diagnostic only.
For these46 observed failure frames,their actual MRB bases' order<=1 sets
cannot contain truth. No global code/decoder/route claim or permission for
order2/newscience/realdata is implied. No FER/f_eff/SKR/security/qualification/
publication/crossbatch comparison. P7 scoped documentation/memory triage
released to shape_closeout; manifest, CSV, summary, NPZ, and the original 192
scientific log entries remain unchanged.

## P7 documentation and memory closeout

`RESULT.md` and `INDEPENDENT_ACCEPTANCE.md` record the P6 vector-level review and main acceptance. Only the independent-review/main-acceptance prose was appended to the machine log; its 192 original call entries and the manifest, CSV, summary, and NPZ were not modified. OpenSpec T5 and durable project pointers are complete. This closeout adds no scientific execution or extension authority.
