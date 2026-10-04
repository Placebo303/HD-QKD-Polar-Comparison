# Bounded MRB syndrome rescue — EXPLORE

2026-10-01. State **FROZEN v1 / ONGOING GRANT / MAIN DISPATCH**.
UUID `ebbbe5c2-f53f-4b92-a2ff-3eca358002de`.
Fresh root `workspace/gf32_mrb_rescue_ebbbe5c2/`.
User ongoing grant verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Apply ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. Independent synthetic
successor, not an extra arm of source-label or damping. No new human reply
needed; independent implementation PASS/main dispatch before science.
No scientific repair/rerun/resume/extra frames. This tests recovery versus
explicit extra computation, not a free label gain or qualified decoder.

## R1 Fixed graph, source and BP

Accepted SEARCH-DEPTH21cc2d44 deep H0D common to both arms: six seeds
2026093901..3906, D10 n128/m52/E256, GF32 polynomial37, variabledegree2,
check4x4+5x48, original construction/deep max8/no-change and all-six
support/degree/connected/rank52 admission. No source-label candidate.
Source p0=.550; p[e]=.450*{1:2295,3:1126,7:557,15:304,31:146}/4428,
others0, iid/Bob-zero matched prior, existing floor1e-15/normalization.
Both arms call same v35 layered FFT-QSPA max_iter90,damping_alpha1.0,
warmNone,fieldNone. Preserve the supplied probability prior. Derive the same
effective log-prior as v35: floor entries at1e-15, normalize each row, then
take logarithms. Use that fixed effective log-prior for rescue scoring.
Control returns raw BP result. Candidate only adds bounded MRB rescue.
No raw/private/real source, fitting, new graphs, label/prior/schedule change.

## R2 One bounded postprocessor

Use BP x_hat and final_beliefs in original variable order. Independently
recompute H*x_hat against original syndrome; if it matches, return raw
result unchanged, including syndrome-consistent wrong results. No truth
or exact flag may enter rescue trigger, enumeration, scoring or selection.
If it does not match, call existing nonbinary_v19_osd.osd_decode_candidates_mrb
with GF2mField(5,37), original H and syndrome, beliefs=raw.final_beliefs,
e_hat=raw.x_hat, order=1, top_info=None, top_symbols=None,
max_candidates=256. It solves H*x=s, not residual plus original prior.
The cap includes the order0 base. Frozen helper ordering is stable ascending
top1-minus-top2 BP log-gap column order, then stable free-column reliability
order and numeric symbol0..31 excluding current hard symbol. Do not reorder
to favor samples or add a second candidate budget/order. BP beliefs are
approximate beliefs; preserve/record provenance, not calibrated posterior.

Validate every returned vector's original syndrome. Invalid output or >256
vectors is a numerical integrity STOP. Score each valid vector by
math.fsum of the SAME effective input log-prior entries. Highest score wins;
exact equal score chooses lexicographically smallest original-coordinate
vector. No rescoring with BP beliefs, analytic-zero PMF or hidden truth.
If candidate list is empty retain raw BP output as failure. Otherwise
return a new DecoderResult via dataclasses.replace with selected x_hat,
syndrome_ok=True and explicit rescue status; do not mutate raw BP object.
Keep raw iterations/beliefs/provenance and BP runtime_s; actual total arm
wall is separately measured around BP+MRB. Stored beliefs remain BP beliefs,
not a claimed posterior for rescued x_hat. Record raw status/iterations,
raw syndrome check, rescue attempted, candidate count, selected prior score,
rescue wall and final syndrome; do not export error/prior/truth/belief arrays.

No first-feasible early selection: score every returned candidate, within
256 cap. GF32 n128 use is new; existing GF4/old generic q examples do not
constitute acceptance. Reuse field/RREF/solve helpers, not a new solver.
Simpler order0-only rescue is a future alternative, not a second arm here.

## R3 Paired samples and frozen practical screen

No pilot. Six graphs x2 streams x16 frames=192 pairs/384 BP calls, at most
192 rescue invocations/49152 returned candidate evaluations. Explicit
control/candidate adapter dispatch; same immutable H/error/prior/syndrome
within pair. Even frame control first; odd candidate first.
v10_seed('gf32-mrb-rescue-v1:holdout:{graph_seed}:{stream}:{frame}').
Success=exact AND independently recomputed syndrome_accept. Wrong outputs
are separate failures, never success. Verification NOT_IMPLEMENTED;
undetected NOT_MEASURED; tag0;260 syndrome bits per attempted arm including
failure, complete total99840. Rescue reveals no additional public message;
this accounting identity is not a security or secret-key claim.

Complete screen: control39..153 inclusive, Delta(candidate-control)>=12,
positive per-graph Delta>=4/6, zero integrity/resource/auth violations =>
MECHANISM_SIGNAL. Control outside range => CONTROL_RANGE_UNINFORMATIVE;
otherwise NO_SUFFICIENT_SIGNAL. Wrong outcomes are counted/reported
separately; nonzero wrong prohibits any qualification/verified-use claim
but is not concealed as an execution integrity violation. These screens
are not significance, causal attribution, FER/SKR or route decisions.
All six graphs retained, paired four states, raw/final wrong/syndrome states,
rescue counts/candidate scores and actual per-arm time/iterations reported.
Incomplete/orphan/STOP attempts retained but complete comparison/graph
performance/four-state totals null. No extra trials after outcome.

## R4 Costs, artifacts and acceptance

One process1800s total including reconstruction;4GiB RSS;120s per
synchronous BP+rescue arm after return, no hard timeout claim. Before/after
every arm and exception, and before/after each rescue invocation, sample
resources; no next call after STOP. Helper RREF is not time-bounded by
candidate cap. Persist batch_wall_s,max_call_wall_s,max_rss_bytes with
API/sampling scope, including STOP; preserve original error/resource markers.
Exactly manifest.json,frame_records.csv,summary.json,EXPLORATION_LOG.md,
fresh root refusal/no overwrite. No sampled source or beliefs exported.

Allowed new cli/nbldpc_gf32_mrb_rescue_probe.py and
comparison_bench/tests/test_nbldpc_gf32_mrb_rescue_probe.py only. Reuse
accepted deep/paired/observation/resource helpers and existing OSD/field.
No old decoder/OSD edits or generalized rescue framework. OpenSpec
explore-gf32-mrb-rescue precedes implementation. Exact command:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_mrb_rescue_probe --execute --out-root workspace/gf32_mrb_rescue_ebbbe5c2`
Forbidden raw/private/NPZ/TTBin/parquet reads, n256/new graphs/prior/labels,
orders>1/new caps/grids, pooled/ranked batches, void baseline/prohibited
TABLE use, FER/f_eff/SKR/throughput/qualification/publication/route DECIDE,
commit/push/merge/archive, frozen Polar or unrelated dirty file changes.

P1 frozen graph/source/decoder/paired seeds/input identity; P2 tiny GF32
field/RREF/MRB syndrome/column inverse/order0/base/order1/cap256/uniqueness,
belief shape/reliability/provenance; P3 raw syndrome trigger independent
truth, no trigger on syndrome-consistent wrong, helper parameters/original
syndrome, all-candidate matched-prior score/tie/empty/invalid/cap STOP,
raw-result nonmutation and original BP versus total wall semantics;
P4 explicit fake callbacks192pairs/order/seeds/exact+syndrome/wrong/leakage,
screen boundaries/all-six/paired states/rescue metadata; P5 preflight/
resource/postexception/partial/orphan/null/error retention/no nextcall/
actual cost persistence/rootrefusal; P6 focused fake/tiny tests/compile/T0
0 actual graph/decoder/OSD/artifact reads/writes; no default production from
tests; P7 independent plan/implementation/raw batch review; P8 main
acceptance/append-only projectmemory and decisionlog triage. WSL repo.venv,
pytest -p no:cacheprovider -o addopts='',fresh test root.
Workers not alone; preserve others. Operator != reviewer; main owns scope.

## Independent plan review / implementation release

faithful_contract PLAN PASS after readonly verification of the actual
GF32 field/OSD signatures, original-equation MRB, cap includingbase,
deterministic column/symbol order, syndrome-only trigger, all-candidate
scoring and raw-result preservation. R1 clarifies that the supplied prior
is a probability matrix; scoring derives its effective v35 log-prior by
the existing floor/row normalization/log formula, not log of BP beliefs.
This resolves representation wording before implementation/science; it
does not change source/prior inputs or selection criterion. Main accepts
and releases only the two named files to faithful_scope after source-label
implementation review; faithful_contract is independent MRB reviewer.
No actual MRB/decoder/graph batch before independent implementationPASS/
main dispatch. Source-label review takes priority when ready.

## Independent implementation acceptance / main dispatch

faithful_contract independent P1–P6 PASS after narrow correction to rescue-
exclusive wall measurement. Total arm wall was already correct; final
rescue wall now includes helper, verification, scoring/tie/final selection.
12 focused fake/tiny tests independently passed2.69s, compile/T0PASS;
fake slow scoring records helper1s/rescue4s, exception+RSS cap retains both
markers and stops further calls with unknown complete performance.
0 actual graph/decoder/MRB/input/artifact reads/writes in T0, root absent.
Main accepts review on intended formal-IR branch and dispatches the exact
frozen command once under ongoing grant. faithful_scope operates;
faithful_contract independently reviews actual batch. No source-label
candidate or failed batch data enters this separate rescue experiment.
