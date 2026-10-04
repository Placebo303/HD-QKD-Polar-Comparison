# GF32 label alignment — L1 synthetic EXPLORE batch

Date: 2026-09-30. Batch UUID: `a74e912c-4bac-4d7d-9fe9-2358bd8a85d1`.
Track: **EXPLORE**. Main-thread frozen contract, version 1.
Root: `workspace/gf32_label_a74e912c/` (must be absent at execution start).

## AUTH and scope

The user explicitly granted the mechanism in this chat (verbatim):

> 可以授权“下一步最值得检验的主线机制是**固定图结构、先验和译码器，只改变 GF(32) 边标签分配**  ”

and subsequently instructed “请继续”. This grant is used for this bounded
pure-synthetic mechanism batch only. It does not grant private/real aggregate
reads, Model-F fitting, n256, route closure, or qualification. The operator
must finish implementation-only tests and independent plan/implementation
review before consuming this one-shot grant. Any scientific change requires
STOP and a new packet/grant. No commit/push/merge.

All EXPLORE conditions hold: invented non-sensitive synthetic inputs; one new
root; bounded/reversible; no FER/SKR/qualification/publication claim; no
overwrite or external action. The result concerns L1 only; it cannot establish
full U1+U2 recovery or relabel prior N2048/Joint terminals.

## F1 Fixed method and inputs

- Width n=128, GF32 polynomial 37. Six CONTROL_L055_PEG supports from
  `nbldpc_l1_degree2_layout.build_control_l1(128, seed)` for graph seeds
  `2026093701..2026093706`. m=118 and E=301; use each builder's original D10
  nonzero coefficients. No D2-directed support, new graph search, or H2.
- Decoder: `nbldpc_l1d2_production_decode.production_decode_fn`, which calls
  `v35_algorithm_development.decode_row_layered_fftqspa`, max_iter=90,
  damping=1.0, warm=None, field=None. Both arms call the same function.
- Bob is the all-zero GF32 vector. Unknown Alice/error e is iid from the
  declared PMF; matched prior is the PMF repeated across all n columns.
  This is a constructed additive channel, not a measured source law.
- Frozen PMF grid in order, indexed 0,1,2: p0=0.20, 0.25, 0.30; p1=0.10;
  p[e]= (0.90-p0)/30 for e=2..31. No fitted prior/floor except the existing
  decoder behavior; every entry is positive. Record each exact formula and
  Shannon entropy, do not call entropy a measured value.

## F2 Label rule (one candidate, no test-frame selection)

Candidate is Hc=H0 D with edge coefficient hc_cv=h0_cv*Dv in GF32,
D diagonal nonzero GF32 elements. Initialize every Dv=1.
Visit v=0..127 exactly once. At each v, evaluate all beta=1..31, replacing Dv
by beta while holding all other D fixed. Maximize J=sum over checks of H(S_c),
where S_c is the XOR sum of independent label-weighted errors from the frozen
PMF. Compute 32-bin distributions exactly by GF32 multiplication permutations
and XOR convolution. Compare float scores with tolerance 1e-12; prefer the
current value on a tie, then the smallest beta. No second pass, restart, label
seed, decoder-based scoring, or frame-dependent adaptation.

Only adjacent checks need recomputation. J is an analytic marginal proxy,
not decoder gain. Hc preserves support and column scaling preserves rank and
cycle-gain class; this tests alignment of a fixed nonuniform source with a
coordinate-equivalent code. It is not a new cycle-gain mechanism. Require
at least one Dv!=1 and Jc>J0+1e-10 for each admitted graph, otherwise STOP
`NO_NONTRIVIAL_LABEL_CANDIDATE`, with all diagnostics retained.

## F3 Conditional sequence and independent samples

1. T0 before decoder: field multiplication/inverse, XOR-convolution PMF
   normalization, exact two-edge example (P(0)=0.8,P(1)=0.2, other mass=0:
   labels (1,1) give mass {0:0.68,1:0.32}; labels (1,2) give
   {0:0.64,1:0.16,2:0.16,3:0.04}), QSC single-check invariance, and
   Hc D^-1=H0 on a fixed tiny example. QSC is not a whole-graph
   neutral-performance gate. Any T0
   failure STOP `MATH_OR_MAPPING_FAILURE`.
2. Preflight all six baseline graphs; retain full-rank evidence. No
   replacement seeds or omission.
3. Pilot CONTROL only, PMFs in order. Per PMF: six graphs x four frames =24
   calls. Seed is v10_seed('gf32-label-v1:pilot:{pmf_index}:{graph_seed}:{frame}')
   with frame=0..3. Stop pilot grid at first PMF with aggregate exact successes
   5..19 inclusive. No candidate decoder runs during selection. If none,
   STOP `CONTROL_RANGE_UNINFORMATIVE`. Retain every attempted pilot row.
4. Build/admit all six candidates for selected PMF before generating holdout;
   verify full-rank, same support and Hc D^-1=H0 for each graph.
   Holdout: six graphs x two stream IDs (0,1) x sixteen frames =192 paired
   frames, 384 L1 calls. Seed is
   v10_seed('gf32-label-v1:holdout:{graph_seed}:{stream}:{frame}').
   Same sampled e and same prior for both arms; each arm computes its actual
   syndrome. Alternate arm order by paired frame index parity.
5. STOP once any gate/resource/integrity/authorization issue fires; never
   resume or reduce sample count. No repair+rerun is granted for this batch;
   retain any failed attempt in the same log and return its concrete blocker.
   Syndrome-consistent wrong decoding is an ordinary recorded failure, not
   a STOP trigger.

## F4 Metrics and classification

Record phase, PMF, graph, stream/frame, seed, arm, exact, syndrome_accept,
syndrome_consistent_wrong=(syndrome_accept and not exact), status, iterations,
wall_s, rss_b, syndrome_bits=5*118=590. Only exact AND syndrome_accept counts
as success. A syndrome match alone never counts. Syndrome-consistent wrong
rows remain exact=False failures and are separately counted per arm.
No physical acceptance/verifier is implemented: tag_bits=0,
verification_status=NOT_IMPLEMENTED, undetected_status=NOT_MEASURED. Neither
syndrome acceptance nor a truth-based diagnostic is physical verification.
Failures retain the full attempted syndrome disclosure count of 590 bits;
syndrome values need not be stored (frozen seeds/H/PMF permit reconstruction).
A not-started arm has no
row. No FER, f_eff, full-pair, net-key or throughput certification.

For a complete holdout report paired control-only/candidate-only/both/neither,
Delta=candidate_exact-control_exact and Delta_g for each of six graphs.
`MECHANISM_SIGNAL` requires Delta>=12, positive Delta_g in >=4/6 graphs,
control total 39..153 inclusive, all 192 pairs complete and zero integrity,
authorization or resource violations. Otherwise classify
`NO_SUFFICIENT_SIGNAL` or `CONTROL_RANGE_UNINFORMATIVE` as applicable.
This is a preregistered practical screening gate, not a significance test,
route-closing decision, or license to n256. Partial batches have no complete
performance denominator. Neither outcome settles the NB-LDPC family.

## F5 Resources, artifacts, commands, acceptance

Single process; total wall<=1800 s from beginning of T0/preflight through
decoding (setup included), each synchronous decoder call<=120 s, RSS<=4 GiB.
Check total cap before each next call and classify call overrun after return.
Maximum calls=72 pilot +384 holdout=456. No timeout-based hidden continuation.

Root contains `manifest.json`, `frame_records.csv`, `summary.json`,
`EXPLORATION_LOG.md` only; manifest includes graph/PMF/D/J/rank and attempted
call counts, exact command and dirty-tree batch UUID. Do not save truth/prior
arrays, reuse old machine outputs, or alter old roots. One append-only log
retains attempts, terminal and independent batch-end review.

Command (after independent implementation review, no write on dry-run):
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_label_probe --execute --out-root workspace/gf32_label_a74e912c`

Acceptance IDs: A1 F1 pairing/decoder unchanged; A2 F2 exact deterministic
candidate; A3 F3 seeds/order/sample roles and gates; A4 F4 counting/accounting;
A5 F5 budgets/no overwrite/artifacts; A6 fake-only focused tests; A7 independent
reviewer != operator; A8 main-thread evidence acceptance and memory triage.
Operator cannot self-accept. This packet supersedes the draft's suggested
full-pair synthetic design for this batch only; source mapping and full-pair
work remain future packets.

## Review and dispatch record (2026-09-30)

Independent Luna reviewer `label_plan_review` (not operator `label_operator`)
gave PLAN PASS after correcting decoder binding, PMF indices, and diagnostic
semantics, then IMPLEMENTATION PASS A1-A7. Reported focused fake/math tests:
15 passed; standard dry-run T0 6/6, decoder_calls=0, writes=0. Main thread
accepts that implementation review and dispatches the one-shot F5 command
under the verbatim grant above. Intended branch verified:
`formal-ir-v72p1-addendum-clean`; target UUID root absent before dispatch.
Scientific result remains unaccepted until the independent batch-end review.
