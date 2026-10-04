# NB-Polar track boundary and asset register

Date: 2026-09-11  
Status: PLAN_CANDIDATE / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED

This document records the role of the formal-IR Comparison checkout in the
NB-Polar effort. It is a decision and provenance pointer; it is not an
implementation specification and it does not authorize a decoder run.

## Project boundary

The three source checkouts plus the independent implementation worktree have
separate responsibilities:

| Checkout | Role in this track | Allowed change in this cycle |
|---|---|---|
| D:\Code\HD-QKD_Polar_Comparison | formal-IR/NB-LDPC history, accepted evidence, asset owner | documentation and future OpenSpec decisions |
| D:\Code\HD-QKD_Polar_Comparison-worktree-cascade-single | isolated binary Cascade exploration | documentation boundary only; no NB-Polar code |
| D:\Code\HD-QKD_Polar_Release | frozen binary Polar baseline and protocol reference | documentation boundary only; no baseline logic or result edits |
| D:\Code\HD-QKD_Polar_Comparison-nbpolar | independent NB-Polar implementation worktree | Phase 0–2 planning and later scoped implementation |

The canonical NB-Polar plan lives in
D:\Code\HD-QKD_Polar_Comparison-nbpolar\docs\nbpolar\. Its OpenSpec
candidate is formal-ir-nbpolar-mvp; it is still a plan candidate. The
Comparison mainline has moved past D7-E to the V80 NB-LDPC Jan-21 chain
(O1R A208 replicated PASS; next gate L1 construction + blind budget;
see docs/CURRENT_MAINLINE.md). NB-Polar does not replace, unlock, or
reinterpret V80, O1/O1R, P0, L1B, D7-E, D7-D, D7-C, D6, or D5.

## Accepted history that informs the design

- D5 showed that the tested two-layer rate-mother path did not provide a
  reliable finite decoder route. Its useful contribution is the explicit
  source/channel and leakage accounting, not the old graph topology.
- D6 exposed a structural degree-1 graph failure
  (D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED). This is a finite construction
  defect under the tested gate, not a theorem that GF32 or all NB-LDPC routes
  fail.
- D7-A independently certified GF32 arithmetic and decoder behavior.
- D7-B identified a provenance defect: a cold iteration-0 belief can be the
  untouched prior. D7-C established an oracle dependence diagnostic, and D7-D
  found schedule effect inconclusive. These results require every future
  decoder to expose the origin of its metric and to separate oracle inputs
  from decoder-generated inputs.
- No D5/D6/D7 result is a finite-length NB-Polar result. None supplies
  construction, polarization, SC/SCL, or NB-Polar performance evidence.

## Reusable Comparison assets

The following paths are the source-of-truth references for the new work:

| Asset | Location | Reuse decision |
|---|---|---|
| GF(2^m) arithmetic | comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py (FieldSpec, GF2mField) | Reuse arithmetic and tests after a thin Polar-neutral GF2mSpec wrapper; keep polynomial basis and GF32 polynomial 37 explicit |
| Model-F empirical source | comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py | Reuse counts/provenance and A/B packing; expose a Polar prior adapter rather than importing NB-LDPC method metadata |
| Concentration correction | comparison_bench/src/comparison_bench/formal_ir/v72p2d4r2_cal_gf32_model_rate_audit.py (build_f) | Reuse the per-Bob-column concentration contract; do not use the old per-cell pseudocount build_f_model as a silent substitute |
| Layer decomposition | D5 Model-F helpers (marginalize_p1, conditional p2, APP mixture) | Reuse as a diagnostic and first prior adapter; make layer ordering and conditioning explicit |
| Decoder provenance | v35 DecoderResult plus D7-B Alternative A | Reuse the idea of belief_provenance; NB-Polar gets its own metric/result type |
| IR protocol accounting | comparison_bench/src/comparison_bench/formal_ir/shared.py, FrameBatch, IRMethod, IRRunResult | Reuse transcript, disclosure, universal-tag, failure, and benchmark semantics through an adapter |
| Dataset/benchmark routing | comparison_bench/src/comparison_bench/io/, pipeline/, cli/ | Reuse after the NB-Polar method is a normal IRMethod; keep outputs additive |
| Binary Polar reference | sibling Release src/reconciliation/real_polar_sc_rescue.py, C++ SCL | Read-only reference for frozen/info organization, re-encode checks, and SCL path bookkeeping |

## Explicit non-reuse decisions

Do not carry the following into NB-Polar:

- NB-LDPC parity-check graph topology, degree search, PEG/ACE, window
  scheduling, flooding-vs-layered tuning, or graph seed searches. D6 already
  showed how a structural defect can dominate the interpretation.
- The old implicit cross-layer APP path that forwards a prior-only belief as
  if it were decoder output.
- A decoder-selected disclosure or verification path. A final Toeplitz tag
  may verify a candidate, but it must not select one.
- Binary Polar reliability order or bit-plane ordering as a q-ary construction.
- Direct GF(1024) arithmetic in the MVP. The physical label space (1024),
  GF32 layer alphabet (32), and Polar block length N are separate quantities.

## Required new modules

The independent worktree must add a native q-ary Polar transform and contracts:

1. GF adapter with addition/multiplication/inverse tables and a primitive
   element contract.
2. Symbol metric with normalized float64 log-probabilities of shape (N, q),
   -inf for exact zero, and finite-axis log-sum-exp checks.
3. Polar transform using the explicit GF32 kernel and natural index order.
4. Construction based on disjoint train/evaluation data and a deterministic
   reliability ordering; no inherited PW order.
5. q-ary SC decoder, then ordinary q-ary SCL as a separate enhancement.
6. Frozen/information symbol metadata, rate adaptation, and a protocol adapter
   that reports static and key-dependent leakage separately.

The interfaces and phase gates are specified in
D:\Code\HD-QKD_Polar_Comparison-nbpolar\docs\nbpolar\ARCHITECTURE.md,
ROADMAP.md, and VALIDATION_GATES.md.

## Archived draft

The former live draft formal-ir-future-nbpolar-app-transfer has been moved,
with all four original files retained, to:

openspec/changes/archive/2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded/

It proposed a hybrid NB-Polar upper layer feeding the old NB-LDPC lower
layer. It was never implemented, executed, qualified, or promoted. The archive
is historical input only. The independent native NB-Polar definition in the
new worktree supersedes it.

Other historical NB-Polar mentions in dated V32/V33 and Route B-lite documents
remain unchanged so that their original decision context is auditable. They
must be read as feasibility ideas or negative boundaries, not as current
implementation requirements.

## Current gate

No production NB-Polar module, real-data run, benchmark result, leakage claim,
or security claim exists as of this document. The next legitimate action is an
independent plan review of the Phase 0–2 packet in the NB-Polar worktree.
Implementation starts only after that review and an explicit scoped change;
real QKD prior integration starts only after a noiseless loopback and synthetic
channel SC gates pass.
