# Historical-shape GF32 label alignment — synthetic EXPLORE

2026-09-30. Track **EXPLORE**. Frozen v1. State at dispatch **REVIEW PASS / MAIN DISPATCH**; current state **CLOSED / ACCEPTED — terminal CONTROL_RANGE_UNINFORMATIVE**.
UUID `fd01e03e-3832-4f01-bdb1-eecd744e4b40`.
Fresh root `workspace/gf32_shape_fd01e03e/`.

## Grant, scope and scientific delta

New user grant, verbatim, after the suggested source-inspired distinguishable
synthetic successor:

> 可以继续

This authorizes one bounded synthetic successor after independent plan and
implementation review and main dispatch. Earlier batch grants are consumed.
No real NPZ/raw/parquet/TTBin/heldout reads, prior fitting, Model-F transfer,
H2, n256, route closure, qualification, publication, commit/push/merge.

Compared with a74e912c: freeze a new lower-redundancy synthetic graph profile,
replace the invented diffuse PMF by one historical-source-inspired **marginal
shape proxy**, and use new seed namespaces. The previous L055 graph is not
changed or reused as a baseline. Old/new batch results are not commensurable
for ranking. Within each new paired arm, graph support, source PMF, priors,
decoder and sampled error are fixed; only GF32 coefficients differ.

This is not a reconstruction of the historical conditional channel E1|B.
Bob remains zero and symbols iid; the historical B dependence and temporal
structure are absent. The synthetic zero probability deliberately differs
from observed p_zero. Do not call the model a qualified or faithful real
channel, or infer current Model-F performance.

## F1 Frozen graph, shape and decoder

- n=128, m=52, GF32 polynomial37; variable degree2 x128, check degree4 x4
  and degree5 x48; E=256. Construct once per graph using existing
  `v72p2d10_mixed_degree_l1.build_degree_sequence_peg` with graph seeds
  `2026093801..2026093806`. Generate original nonzero coefficients with
  existing `coefficients_for_edges(edges, 128, graph_seed)` using that same
  graph seed (no separate offset or search), then `dense_from_edges` as H0.
  The custom profile has no prior construction acceptance. Require exact
  socket/degree counts, no duplicate edge, single connected support,
  structural rank52 and GF32 rank52 before any decoder. On failure STOP
  `GRAPH_PREFLIGHT_FAILED`; no alternate seed, profile, row truncation or repair.
- Historical provenance is the already accepted aggregate 2M marginal in
  `NBLDPC-GF32-SOURCE-MAPPING-DRAFT/RESULT.md`, UUID
  `6f821d0b-71e3-46c1-ae84-2da374edbcc2`. Use fixed nonzero counts
  `{1:2295,3:1126,7:557,15:304,31:146}`, total4428. No pooling, new data
  read, likelihood fitting or shape selection. Define q[e]=count[e]/4428
  on these five symbols, q[e]=0 for other nonzero symbols.
- Grid p0 in exact order `[0.85,0.65,0.45,0.25]`, indexed0..3.
  PMF[0]=p0 and PMF[e]=(1-p0)*q[e] for e>0. Keep exact zero entries;
  no invented diffuse floor. Record all formulas and Shannon entropy as
  constructed values. Bob=zero, iid Alice/error e drawn from this PMF;
  matched prior is the same PMF repeated over columns for both arms.
- Decoder unchanged: `nbldpc_l1d2_production_decode.production_decode_fn`
  -> `v35_algorithm_development.decode_row_layered_fftqspa`; max_iter90,
  damping1.0, warm=None, field=None. Existing internal numerical handling
  of zero priors (`max(priors,1e-15)` followed by row normalization) must be
  documented, not changed or described as measured
  channel mass. No new decoder or algorithm defaults.

The old L055 syndrome density is 590/128=4.609375 bits/symbol, above the
six-symbol support entropy upper bound log2(6). The new density is
260/128=2.03125. This motivates the profile, not a capacity or success claim.

## F2 One deterministic label candidate

Reuse `nbldpc_gf32_label_alignment.align_labels` unchanged: Hc=H0 D,
initialize Dv=1, visit v=0..127 once, evaluate beta=1..31, maximize sum
of check marginal entropies from the selected PMF by exact GF multiplication
permutations/XOR convolution. Tie tolerance1e-12, prefer current then smallest
beta. No restart, second pass, decoder scoring or frame adaptation.

Require every graph has some Dv!=1, Jc>J0+1e-10, identical support/degrees,
full GF32 rank52 and Hc D^-1=H0; otherwise STOP
`NO_NONTRIVIAL_LABEL_CANDIDATE`. Candidate admission occurs before holdout.
This preserves rank and cycle-gain class. With the same untransformed
nonuniform prior it tests source/coordinate alignment with the finite-iteration
decoder; it is not a new cycle-gain class, code-distance or MAP-optimality claim.

## F3 Frozen conditional sequence

1. Run existing pure-math T0: GF multiply/inverse, normalized XOR convolution,
   exact two-edge example and gauge identity; QSC single-check invariance is
   mathematical only. Add sparse-PMF normalization/entropy support checks.
   Failure STOP `MATH_OR_MAPPING_FAILURE`, no decoder entered.
2. Preflight all six new graphs, retain metrics even on STOP. Do not omit a
   failing graph or try another seed.
3. CONTROL-only pilot: PMFs in frozen order, each six graphs x4 frames=24
   calls, frame0..3. Seed is
   `v10_seed('gf32-shape-v1:pilot:{pmf_index}:{graph_seed}:{frame}')`.
   Select first PMF with aggregate exact-and-syndrome successes5..19 inclusive;
   stop scanning after selection. Candidate is never decoded/scored for
   selection. If none, STOP `CONTROL_RANGE_UNINFORMATIVE`; retain all attempts.
4. Build/admit six candidates, then independent holdout: six graphs x2 streams
   x16 frames=192 pairs, 384 calls. Seed is
   `v10_seed('gf32-shape-v1:holdout:{graph_seed}:{stream}:{frame}')`.
   Pair identical errors and priors, compute each arm's actual syndrome,
   alternate arm order by pair index parity. No reuse of pilot samples.
5. Any structural/math/integrity/authorization/resource issue stops the batch.
   No rerun, repair, resume or tuning is granted. Wrong syndrome-consistent
   output is an ordinary separately recorded failure, not a STOP.

## F4 Accounting, classification and claims

Use predecessor frame fields: phase, PMF index, graph, stream/frame, seed, arm,
exact, syndrome_accept, syndrome_consistent_wrong, status, iterations, wall_s,
rss_b, syndrome_bits. Success requires exact AND syndrome_accept. Separately
report truth_exact if needed to avoid confusing an inconsistent fake result.
Wrong=syn_accept AND NOT exact; never include it in success. Each attempted
call discloses actual syndrome_bits=5*52=260, including failures; no tag is
implemented (tag_bits0, verification NOT_IMPLEMENTED, undetected NOT_MEASURED).
No row or disclosure denominator for an unstarted arm. No FER, f_eff, SKR,
throughput, full U1+U2 or physical-verification claim.

Only on complete holdout report both/control-only/candidate-only/neither,
per-graph success/Delta_g, and Delta=candidate_success-control_success.
`MECHANISM_SIGNAL` requires all192 pairs, Delta>=12, positive Delta_g in
>=4/6 graphs, control39..153 inclusive, zero integrity/resource/authorization
violations. Otherwise `NO_SUFFICIENT_SIGNAL` or
`CONTROL_RANGE_UNINFORMATIVE`, as applicable. These are practical screening
labels, not statistical significance, random-graph population inference,
route life/death decisions or automatic progression. Incomplete holdout has
no complete performance denominator; preserve unknown/unstarted evidence.

## F5 Budget, files, commands and acceptance

Single process, total wall<=1800s from T0/construction through final decode,
each synchronous decoder call<=120s measured after return, RSS<=4GiB.
Check total/RSS before each next call and after setup/call. Maximum calls:
96 pilot +384 holdout=480. No hidden timeout continuation or parallel decoder.

Exactly four output files: manifest.json, frame_records.csv, summary.json,
EXPLORATION_LOG.md. Record profile, graph seed/coefficients or sufficient
deterministic construction provenance, PMF/entropy, D/J/rank, attempted calls,
all gates and resources, exact command and this dirty-tree UUID (not a hash).
Do not save errors/truth/prior/conditional/input arrays. Fresh root only;
no writes to old outputs. One append-only exploration log records execution,
retained failure, independent batch-end review and main acceptance.

Exactly two new implementation files, no edits to predecessor/decoder:
`comparison_bench/src/comparison_bench/cli/nbldpc_gf32_shape_probe.py` and
`comparison_bench/tests/test_nbldpc_gf32_shape_probe.py`.
Reuse accepted math/decoder and current runner helpers where possible;
no generic configuration framework or dependencies.

Command after independent plan/implementation PASS and main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_shape_probe --execute --out-root workspace/gf32_shape_fd01e03e`

Dry-run may run pure-math T0 only: decoder_calls0, real_inputs0, writes0.
Focused tests fake runner only: custom sockets/preflight guards; five-bin
shape/zeros/normalization and grid order; pilot control-only first eligible
selection; namespaces/paired errors/priors/order; arbitrary m accounting260;
wrong-success separation; graph/candidate/no-control-point STOP; budget STOP;
fresh-root refusal and zero-write dry-run. A fake construction may replace
production construction in tests; never call a default scientific decoder.

Acceptance IDs: P1 F1 graph/shape/decoder; P2 F2 candidate/gauge;
P3 F3 pilot/holdout gates and independent samples; P4 F4 accounting/claims;
P5 F5 budgets/artifacts; P6 fake/math tests and dry-run; P7 independent
plan/implementation and batch-end review (reviewer != operator); P8 main
evidence acceptance and repo memory triage. Operator cannot self-accept.
The user grant covers this frozen conditional sequence only; terminal STOP
does not authorize another profile/grid/shape or new scientific batch.

## Independent plan review — 2026-09-30

Reviewer `/root/faithful_scope`, separate from operator `/root/faithful_contract`,
reported PLAN PASS P1–P7: profile/socket counts, six graph seeds, one accepted
2M marginal shape, CONTROL-only grid, paired accounting, budget/root and narrow
gauge mechanism are coherent. The latest quoted grant covers only this bounded
synthetic successor. Main accepts this plan review. Implementation review and
explicit main dispatch remain required before the one-shot scientific command.

## Implementation review and main dispatch — 2026-09-30

Independent reviewer `/root/faithful_scope` reported IMPLEMENTATION PASS
P1–P7 after reading the two new files. Same-seed construction, graph gates,
sparse PMF and numerical prior floor, CONTROL-only selection, independent
paired samples, 260-bit disclosure, all resources and four-file root match.
Reviewer independently ran focused fake tests: 11 passed in3.38s, only existing
pytest cache_dir configuration warning. Dry-run T0 passed7/7 with zero graph
construction, decoder calls, empirical reads and writes; target root absent.
Operator reported11 passed in3.42s. Main verified intended branch and absent
root, accepts this scoped implementation review and dispatches exactly the
F5 one-shot command under the quoted new user grant. No real data/repair/rerun
or successor is granted. Result acceptance remains pending independent
batch-end review and main evidence adjudication.
## Execution closeout — 2026-09-30

The one authorized synthetic run completed all 96 CONTROL-only pilot calls and stopped with `CONTROL_RANGE_UNINFORMATIVE`. Independent batch-end review `faithful_scope` passed P1–P7, and the main thread accepted only this bounded pilot STOP record. The user grant is consumed. The candidate was not built, holdout was not run, and candidate/control comparison, delta, and per-graph delta remain unknown (`null`), not zero. See `RESULT.md` and the appended `workspace/gf32_shape_fd01e03e/EXPLORATION_LOG.md` review/acceptance record.

The separate `NBLDPC-GF32-SHAPE-FINE-DRAFT` is only an ungranted planning pointer; this packet does not accept its conclusions or authorize its execution. Any successor requires a new packet and explicit grant.
