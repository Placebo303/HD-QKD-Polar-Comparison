# Local cycle/source overlap diagnostic — EXPLORE

2026-10-01. State **CLOSED / MAIN ACCEPTED WITH COMMENTS**.
UUID `202e39a1-bf55-436a-ad3f-cad2d539e683`.
Fresh root `workspace/gf32_cycle_overlap_202e39a1/`.
User ongoing grant verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Apply ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md. No new per-batch reply within
this frozen synthetic scope. Execute once only after accepted complete census
475c2ad3,independent implementation PASS/main dispatch. No sampledsource,
production graph/decoder,relabeling,rerun/repair/resume or automatic cancellation.

## O1 Inputs, question and derivation

Readonly accepted census root workspace/gf32_cycle_census_475c2ad3/,
manifest.json,summary.json,cycles.csv for six3901..3906 graphs and both
deep control/accepted edge matrices. Frozen cycle scope ell2..6 unchanged.
Do not reconstruct any graph or label candidate. No source fitting/raw input.
Use exact analytic32-symbol PMF p0=.550,p[e]=.450*q[e],nonzero
q={1:2295,3:1126,7:557,15:304,31:146}/4428,others exactly0,poly37.
The decoder's1e-15 floor is NOT applied to this mathematical diagnostic.

For GF32 additive XOR shift z, B(z)=sum_e sqrt(p(e)*p(e XOR z)).
For each valid unit-cycle normalized nonzero local codeword c,
W(c)=sum_{lambda=1..31} product_{v in cycle} B(GFmul(lambda,c[v])).
For iid P(E)=product_v p(E_v), the overlap between P and its fixed codeword
shift factorizes exactly as product_v B(c_v); B(0)=1 on other coordinates.
Thus W is the sum of31 shifted-source Bhattacharyya coefficients for this
local codeword orbit. It is NOT error probability,FER,decoder success or a
claimed global MAP bound. No sum-W to FER conversion; no security/SKR use.
Pcycle=1 establishes algebraic codeword support but may have W=0 under the
frozen sparse source. The diagnostic tests that distinction before choosing
a future cancellation experiment. No causal or route claim.

## O2 Evidence and duplicate convention

For each unit witness on each matrix, verify nonzero local coefficients and
check equations using saved ordered edge coefficients and GF32 arithmetic;
do not call actual graph builder. Normalize orbit key by sorting variable IDs
and scaling value at smallest variable to1. Duplicate orbit keys within a
graph/matrix are counted once in graph totals; retain each inputcycle row
and explicit duplicate flag. Lambda set covers31 distinct nonzero multiples.
Record W and number of strictly positive overlap terms0..31. Nonunit cycle
has no local codeword orbit: W=null (not a measured zero); distinguish this
from unit+ZERO_SOURCE_OVERLAP W=0. Report pergraph/perell unit count,unique
orbit count,positive/zero source-overlap orbit counts and sumW separately for
control/edge. No graph subset chosen by these values; no crossbatch ranking.
Canonicalization/norm/scalar invariance follow frozen census conventions.
No longercycle search, joint-cycle inventory or new PMF.

## O3 Runtime, artifacts and outcomes

Singleprocess600s total,4GiB RSS,600,000 inputcycle-row maximum. Stream CSV,
check resources before/after input and every1024 rows. Error/cap/resource or
predecessor incompleteness STOP, retain rows/log and no retry; fullbatch
summaries null/unknown when incomplete. Completed ZERO/POSITIVE_OVERLAP
are availability diagnostics only, not mechanism/pass gates. Empty unit
inventory is a valid complete diagnostic with0 unit orbits,not route denial.
Exactly manifest.json,source_overlap.csv,summary.json,EXPLORATION_LOG.md.
Expose frozen p/B and mathematical units (dimensionless overlap),inputuuid,
codeword algebraic witnesses only; no sampled error/truth/prior arrays.

Allowed new cli/nbldpc_gf32_cycle_source_overlap.py and
comparison_bench/tests/test_nbldpc_gf32_cycle_source_overlap.py only. Minimal
math/read/write probe with pure GF/census helpers,not generic audit framework.
No old modules/results edits/global mutation; no real/private/NPZ/TTBin/
parquet data,decoder calls,n256,FER/f_eff/SKR/throughput,qualification,
publication,route DECIDE,commit/push/merge/archive or oldprohibited TABLE use.
OpenSpec explore-gf32-cycle-source-overlap precedes implementation.
Exact command after independent PASS/accepted census/main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_cycle_source_overlap --execute --out-root workspace/gf32_cycle_overlap_202e39a1`

## O4 Complete acceptance matrix

P1 frozenPMF/field/root/inputuuid/sixgraphs/cyclescope and0graph/decoder;
P2 B direct32term formula/symmetry/B0=1,delta-source Bnonzero0,uniform B=1;
P3 W direct two-symbol shifted-source sum vsfactorization,unit-witness
checkequations,31scalar distinctness,rescaling/order invariance,uniform W31,
delta W0,duplicate orbit normalization; P4 fakecomplete input two matrices
pergraph/perell counts/no-unit/positive-zero/nonunit-null/duplicatecase,
zerooverlap distinct nonunit,partial/null totals and no subsets;
P5 missing/incomplete predecessor,invalid savedwitness,rowcap/totalwall/RSS
STOP/exception/root refusal/nooverwrite; P6 focused fake/tiny tests and
dryrun0 artifact read/graph/decoder/writes; P7 independent plan/implementation
review and batch-end inputrows/GF/math/count/resource/grant/ceiling review;
P8 mainacceptance and append-only projectmemory/decisionlog triage.
WSL repo .venv,focused pytest -p no:cacheprovider -o addopts='',freshroot.
Workers notalone,preserve others; return frozen items complete or exactblocker.
Independentreviewer != operator; main owns scientific priorities/acceptance.

## Independent planning review / implementation release

faithful_scope O1–O4 PLAN PASS on2026-10-01: exact iid factorization,
unit/nonunit-null/zero distinctions,scalar/orbit invariance,dedup,input
scope and600k rowcap align with census contract. Main accepts and releases
two-file implementation/fake tests. faithful_contract owns both new CLI/test;
faithful_scope independent review; main owns acceptance. Actual execution
still waits for accepted complete census and independent implementation
PASS/main dispatch. No change to frozen census or automatic cancellation.

## Independent implementation review / main dispatch

faithful_scope finalP1–P7PASS after narrow engineering correction to
terminal-resource sampling on error/STOP,originalreason retained. No
scientific attempt preceded this correction.13focusedfake tests passed
in2.51s;onlyknowncache_dir warning. Dryrun0reads/rows/graphs/decoder/writes,
rootabsent. ExactPMF/B/W/orbit/witness/partial semantics conform; RSS
statistics are observed checkpoint samples,not an unobserved absolutepeak.
Census475c predecessor independently reviewed/mainacceptedwithcostmetadata
comments and closed. Main verified formal-IR branch/no tracked frozenbaseline
differences/absent root, accepts scoped review and dispatches exactcommand
once under ongoinggrant. Source-overlap evidence stillpending batchreview/
mainacceptance,noimplicitcancellation/decoder or FER interpretation.

## Batch-end review and main acceptance

`faithful_scope` independently passed P1–P7 (reviewer != operator). Main accepts only the finite six-graph synthetic iid marginal-proxy inventory: 3026/3026 rows, 105 control and 121 edge-candidate unique unit orbits, with positive/zero counts 36/69 and 76/45 respectively; the corresponding `sum_W` values are 0.028521162905751574 and 0.035753425835366386. Nonunit-cycle `W` remains null, distinct from unit/zero-overlap. Reviewer recomputation differences were at most 1.73e-18 for W and 5.55e-17 for B(z); no duplicate normalized unit orbit was found. The batch completed with zero graph constructions, decoder calls, and sampled frames. Wall was 0.412950788 s; maximum RSS was 101978112 B at sampled high-water-RSS checkpoints, not an absolute peak. The one-run grant is consumed; no rerun or extra scope is authorized by this packet. Claim ceiling and exclusions remain as stated above.
