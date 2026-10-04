# Fixed-graph label-search depth probe

2026-10-01. Track **EXPLORE**. State **CLOSED / MAIN ACCEPTED / GRANT CONSUMED**.
UUID `21cc2d44-6aa6-4619-b8e2-7f95615bebe2`.
Fresh root `workspace/gf32_search_depth_21cc2d44/`.
User grant verbatim, referring to the preceding search-depth proposal:

> 可以继续往下

This authorizes one bounded synthetic search-depth batch, after scoped
implementation review and main dispatch. Previous grants are consumed.
No scientific repair, rerun, resume, extra frames or automatic successor.

## Question and retained authority

The independent replica 7d6e57f0 was accepted NO_SUFFICIENT_SIGNAL:
baseline139/candidate147 of192, Delta+8, positive3/6. Its classification
remains unchanged. Do not pool counts or rank batches.

Test only whether additional deterministic coordinate sweeps improve the
one-pass candidate under the same analytic check-entropy objective. Compare
onepass versus deep directly; omit a repeated baseline arm. This isolates
search depth in this fixed setup. It cannot establish causal mediation,
an optimal objective, population performance or a NB-LDPC route verdict.

Retain from ../NBLDPC-GF32-INDEPENDENT-REPLICA-DRAFT/PREREG_AND_AUTH.md:
n128/m52/E256, GF32 poly37; variable degree2x128/check4x4+5x48;
D10 PEG, coefficients generated with the same graph seed; seeds
2026093901..2026093906; all-six degree/socket/no-duplicate/connected,
structural/GF32 rank52 gates. Reconstruct these fixed graphs, no graph change.
Retain p0=.550 and nonzero shape {1:2295,3:1126,7:557,15:304,31:146}/4428,
other probabilities exactly zero, iid/Bob-zero matched prior. No pilot/grid.
Retain production_decode_fn/decode_row_layered_fftqspa, maxiter90,damping1,
warm=None,field=None and existing numerical prior floor1e-15 plus normalization.
No actual input read, fitted prior, conditional or temporal source model.
Retain exact AND syndrome success; syndrome-consistent wrong is isolated
failure, not success. Physical verification NOT_IMPLEMENTED, undetected
NOT_MEASURED, tag0;260 syndrome bits per attempted call including failures.
Retain serial resource checks before/after every call, including exceptions:
1800s total including construction/search,120s per synchronous call measured
after return,4GiB RSS. Preserve exception and resource markers, no next call
after STOP. No overwrite and exactly four machine files.

## F1 Candidate generation

Control is the accepted one-pass align_labels(H0,p) result. Deep starts with
the same all-one D and follows the same first sweep exactly, then continues
the same objective, variable order0..127 and beta order1..31 for at most
8 total sweeps (first included). Retain accepted exact GF permutations/XOR
convolution, tolerance1e-12 and current-label-first/smallest tie behavior.
After each complete sweep, stop if no labels changed. Never change labels
for a decoder score or use holdout data in search. Freeze no restarts,
random order, alternative initialization or extra sweeps.

First-sweep labels/matrix/J must equal the accepted helper result. Record
per-sweep J, changed-label counts, final D, sweep count and termination
NO_CHANGE or MAX_SWEEPS; report tolerance-level drift transparently.
Any inconsistency or material J decrease beyond1e-10 is construction STOP,
not permission to silently repair. Each candidate must retain support,
degrees, full rank52 and Hcandidate D^-1=H0. The onepass original
nontrivial/Jgain gates remain; deep may equal onepass and need not improve J.
If no graph improves J by>1e-10, record SEARCH_SATURATED as an auxiliary
diagnostic, retain full paired evaluation and mechanical terminal below.
These are H0D candidates in the same gauge/cycle-gain class, not new distance
or cycle-gain claims. Eight-sweep cap is not proof of local/global optimality.

## F2 Execution and samples

Sequence: no-write tiny-math T0; all6 graph and candidate admission;
then6 graphs x2 streams x16 frames=192 pairs/384 calls maximum.
Seed v10_seed('gf32-search-depth-v1:holdout:{graph_seed}:{stream}:{frame}').
Use identical sampled error and prior arrays within each pair, each arm's
own syndrome. Even frame: onepass first; odd frame: deep first. No pilot,
noise selection, tuning or additional sample after observing outcomes.
The arrays stay local; do not export truth/prior/input arrays.

## F3 Frozen interpretation

Control means onepass, candidate means deep. Complete192-pair screen:
control39..153 inclusive, Delta(deep-onepass)>=12, positive Delta_g>=4/6,
zero integrity/resource/authorization violations. All true:
MECHANISM_SIGNAL; control outside range: CONTROL_RANGE_UNINFORMATIVE;
otherwise NO_SUFFICIENT_SIGNAL. These are practical exploratory screens,
not statistical tests, significance, route-closing or qualification gates.
Also report four paired states, per-graph exact counts, J increments and
search termination; never select/subset graphs using J or decoder results.
J increase with no exact increase is only objective/decoder mismatch
evidence in this finite setup; J and exact co-improvement does not prove
causal mediation. No J increase leaves objective quality unresolved.
Partial execution retains rows/attempts/completed pairs but all comparison,
per-graph comparison and pair-state aggregates remain null/unknown; orphan
calls never count as pair gain. Graph/candidate/resource/exception STOP
cannot be relabeled as a completed screen. No physical-undetected claim.

## F4 Scope, artifacts and exact command

OpenSpec change explore-gf32-label-search-depth before implementation.
Allowed additive code: cli/nbldpc_gf32_search_depth_probe.py and
comparison_bench/tests/test_nbldpc_gf32_search_depth_probe.py. Reuse pure
accepted helpers, no old module-global mutation or old code/result edits.
Root artifacts: manifest.json,frame_records.csv,summary.json,
EXPLORATION_LOG.md only. Metadata must expose UUID, seeds, objective,
max8 sweeps, exact call/disclosure caps and the onepass/deep arm mapping.

Frozen scientific command after independent review PASS/main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_search_depth_probe --execute --out-root workspace/gf32_search_depth_21cc2d44`

Forbidden: actual NPZ/raw/private/TTBin/parquet reads, real/new source,
fitting, source-conditional model, n256, other seeds/profile/source/decoder,
FER/f_eff/SKR/throughput, qualification/publication/route claims, cross-batch
pooling/ranking, old TABLE columns, void baseline, commit/push/merge/archive.
Frozen Polar directories and unrelated dirty files remain untouched.

## F5 Complete acceptance matrix and ownership

P1 fixed scientific constants, graph seeds/source, new sample namespace;
P2 accepted first-sweep equivalence, deterministic tie behavior, no-change
termination/max8, J diagnostics, same-support/fullrank/gauge admission;
P3 same sample/prior, own syndromes, alternating arms and384-call cap;
P4 exact+syndrome/wrong isolation,260bits/call, complete screen Delta12
versus11/positive4 versus3/control range, actual fixed-seed per-graph counts;
P5 graph/candidate STOP, partial pair+orphan null aggregates, exceptions
and all3 resource checks before/after return, root refusal;
P6 focused fake tests and no-write dry-run, no implicit production decoder
or graph. Tiny GF arithmetic/search tests allowed; production D10 graphs
and scientific decoder must not run from tests. Test convergence, cap and
first-pass equality on tiny matrices, including unchanged-depth candidates;
P7 independent implementation review before main dispatch and independent
batch-end raw-artifact/count/accounting/gate/ceiling review; P8 main acceptance
and append-only project-memory/decision-log triage after review.

Use Linux repo .venv, pytest -p no:cacheprovider -o addopts='', fresh test
root. No broad regression unless a concrete concern requires it. Independent
reviewer is not the operator. Main owns requirements and scientific acceptance.
Workers are not alone; preserve others' files. Return all scoped IDs complete
or a concrete blocker with command/error and one required main decision.
One append-only exploration log retains attempts and batch-end review.

## Independent planning review / main implementation release

Independent faithful_scope reported PLAN P1–P7 PASS on2026-10-01. Main
accepts and releases additive implementation. Clarification binding to F1:
control uses unchanged align_labels(H0,p); deep first sweep is that result.
Later sweeps operate on fixed H0 and current absolute D, beta1..31 are
absolute labels, current absolute D_v is the tie-preferred current label.
Do not call align_labels(H0D,p) recursively or perform nonregistered rollback.
Check adjacent and onepass-reference J drift; decrease>1e-10 is STOP.
SEARCH_SATURATED remains auxiliary and never shortens paired evaluation.
The control-range ceiling may make this fixed setup uninformative; no
posthoc ceiling relaxation or source selection is granted. Implementation
review/main dispatch remain required before any scientific execution.

## Independent implementation review and main dispatch

2026-10-01 faithful_scope independent P1–P7 PASS. Focused fake/tiny tests
22passed in3.87s, only existing pytest cache_dir warning. T0 dry-run passed
with0 production graph/decoder/empirical reads/writes,192pairs/384calls,
max8 sweeps and absent output root. Review confirms absolute-D tie rules,
first-pass equivalence, no nonregistered rollback, no-change/cap behavior,
J-drift STOP, unchanged candidates admitted, partial masking, exact/syndrome
separation and exception/resource checks. Main verified intended formal-IR
branch, absent root and no tracked frozen-baseline differences. Main accepts
implementation review and dispatches the frozen command exactly once under
the verbatim new grant. Scientific evidence remains pending independent
batch-end review and main acceptance; no successor/repair/rerun is granted.

## Independent batch-end review and main acceptance

Independent `faithful_scope` (reviewer != operator `faithful_contract`)
passed P1–P7. Main accepts only this frozen synthetic iid marginal-shape
search-depth observation and the mechanical terminal
`NO_SUFFICIENT_SIGNAL`. The 192-pair holdout had onepass=146, deep=149,
Δ=+3; paired both/candidate-only/control-only/neither=136/13/10/33.
Per-graph onepass→deep counts for seeds 2026093901–2026093906 were
27→28, 23→21, 19→20, 27→28, 25→26, and 25→26. Positive differences were
5/6; the control-range and positive-graph gates passed, while Δ≥12 failed.

All six graph/candidate gates passed. Deep search ended `NO_CHANGE` after
4/5/6/5/4/4 total sweeps, with final changed-label count 0. Deep-minus-onepass
J increments were 0.257821753652/0.359428366612/0.412678706360/0.461394163165/
0.318499858253/0.287716897104 bits; adjacent/reference drift was at most
5.7e-14 bits. No rollback was applied. The complete batch made 384 calls and
disclosed 99840 syndrome bits (260/call); wall 115.787441 s, max call
0.572914 s, peak RSS 102256640 bytes; integrity/resource/authorization
violations=0. Wrong rows=0, verification=`NOT_IMPLEMENTED`, and
undetected=`NOT_MEASURED`.

The four machine artifacts do not store truth/prior arrays. Review checked
paired keys, shared-seed roles, formula, and arm order, but cannot reproduce
the vectors value-by-value from those artifacts. This small positive
finite-setup observation is not proof of mechanism benefit, causal mediation,
or a route result; do not pool/rank across batches or claim conditional-channel,
FER, `f_eff`, SKR, throughput, qualification, or publication results. The
one-shot grant is consumed; no rerun, repair, extra frames, restart, or
successor batch is authorized.
