# V34 formal 60-block matched finite-control closeout — 2026-08-24

## Outcome

V34 completed its one authorized official execution on accepted HEAD
`c8cc1fbe6ef37bc2735de3f6795c29d7042670ff`. The unchanged frozen matrix digest
was `d30335b4d0d74df3e7729e01b02ae1ae73e43035652c59e81f871a5545fe73bb`.
All 60 source-major blocks completed, no fatal event occurred, and independent
ER1 returned `ACCEPT_ER1`.

Overall terminal: `matched_empirical_finite_control_fail`.

| source | success | initial L2 errors mean (range) | final L2 errors mean (range) | mean runtime/block | status split |
|---|---:|---:|---:|---:|---:|
| 1M | 0/20 | 249.25 (212–269) | 168.45 (139–196) | 10.1936 s | 12 converged-no-syndrome, 8 max-iter |
| 1p5M | 0/20 | 261.35 (239–288) | 181.10 (158–216) | 10.0084 s | 13 converged-no-syndrome, 7 max-iter |
| 2M | 0/20 | 256.90 (238–290) | 174.05 (137–196) | 9.9852 s | 12 converged-no-syndrome, 8 max-iter |

The decoder reduced the mean L2 symbol error count by 32.42%, 30.71%, and
32.25%, respectively, but produced no exact, syndrome-valid, or tag-valid
block. There were no false accepts.

## Accounting correction and acceptance

Before execution, V34 was corrected so `runtime_s` is the monotonic elapsed
time around exactly one runner call and `l2_errors_final` is recomputed from
the legal `x2_hat` and true GF(32) `x2`. Complete `x2_hat` arrays are persisted.
The correction did not alter seeds, source order, packet, rates, threshold,
decoder schedule, or the call-matrix digest.

Candidate acceptance evidence on the exact HEAD:

- compile, selfcheck and real-input read-only prepare: PASS;
- focused P4A accounting tests: 3 passed;
- complete V34 fake suite: 45 passed, one intentional overflow warning;
- independent implementation review: `ACCEPT_IR1_P4A`;
- user authorization: `user-v34-execute-auth-20260824-01`;
- official execute: exactly once, 60/60 records;
- absolute-path strict verify: `consistent`, `problems=[]`, 60 records;
- independent post-run review: `ACCEPT_ER1`;
- `run_02`: absent.

The first read-only verifier invocation used a relative root while the manifest
stores the absolute root and therefore reported only `run_root_mismatch`.
Repeating the read-only verifier with the manifest's absolute path returned
fully consistent. Neither invocation called the decoder or wrote evidence.

## Scientific interpretation

Direct empirical-P sampling removes V32 B1's generator/posterior mismatch, yet
the fixed V31 QC packet plus current V28R FFT-QSPA conversion still failed all
60 matched blocks under oracle L1 and `max_iter=30`. This is a stronger bounded
negative result for that fixed finite realization than V32 B1, but it does not
show that NB-LDPC, the empirical-P ensemble, or all finite graphs fail.

The result is not “the posterior has no information”: mean final errors are
about 31–32% below the initial errors. The dominant observation is instead
partial movement toward the truth without reaching any valid syndrome. The
37 `converged_no_syndrome` records and 23 `max_iter_reached` records motivate
finite-graph/iterative-decoder structure work. They do not yet distinguish
trapping/absorbing structures, the degree-2 realization, schedule saturation,
or insufficient/adaptively misplaced redundancy.

## Performance-first next plan

No V34 rerun or parameter tuning is planned. The next change should implement
algorithm work, not verifier work:

1. Reuse the 60 persisted residuals to localize residual errors against the
   Tanner graph: short-cycle participation, unsatisfied-check neighborhoods,
   repeated support patterns, prior rank/probability, and status class. This is
   a read-only design diagnostic and needs no new decoder call.
2. Build one empirical-P-informed protograph/MET candidate that avoids an
   all-degree-2 finite realization and explicitly limits the structures found
   in step 1. Perform ensemble screening before one finite lifting.
3. In parallel, design one rate-adaptive/incremental-syndrome mother-code path.
   Its purpose is to trade only the required extra leakage for accepted frames,
   not merely to add iterations to the same failed packet.
4. Compare candidates by exact success/FER, total leakage, runtime/throughput,
   memory, and accepted-frame net key contribution. A one-off higher-iteration
   diagnostic may be proposed only as a new bounded experiment; it is not a
   V34 retry.

Relevant literature supports these directions without proving them for this
dataset:

- Mueller et al., “Efficient information reconciliation for high-dimensional
  quantum key distribution,” *Quantum Information Processing* 23 (2024),
  DOI `10.1007/s11128-024-04395-w`: NB-LDPC and HD-Cascade near the
  Slepian–Wolf bound on q-ary symmetric models; EMS/TEMS are suggested for
  throughput/longer-code tradeoffs.
- Karimi and Banihashemi, “On Characterization of Elementary Trapping Sets of
  Variable-Regular LDPC Codes,” *IEEE Transactions on Information Theory*
  (2014), DOI `10.1109/TIT.2014.2334657`: short cycles and layered trapping-set
  structures provide concrete finite-graph design targets.
- Martínez-Mateo and Elkouss, “Efficient reconciliation of continuous variable
  quantum key distribution with multiplicatively repeated non-binary LDPC
  codes,” *EPJ Quantum Technology* (2025), DOI
  `10.1140/epjqt/s40507-025-00376-9`: a simple inherently rate-adaptive
  nonbinary mother-code family motivates the incremental-redundancy branch.
- Mao, Qiao and Li, “High-Efficient Syndrome-Based LDPC Reconciliation for
  Quantum Key Distribution,” *Entropy* 23, 1440 (2021), DOI
  `10.3390/e23111440`: syndrome reuse and fewer interaction rounds motivate
  leakage-aware adaptive reconciliation.

## Stop boundary

V34 is closed as an ER1-accepted bounded FAIL. Do not execute, resume, create
`run_02`, replace seeds, raise the iteration limit inside V34, or infer FER,
net-key, qualification, promotion, or general NB-LDPC failure. A successor
requires its own small algorithm-centered OpenSpec and explicit authorization.
