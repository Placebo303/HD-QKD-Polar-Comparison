# Design: V34 corrected matched empirical-P finite control

> Draft for FR1. Candidate values below are not executable constants.

## 1. Causal contrast

V34 changes exactly one scientific variable relative to V32 B1: the block
generator. V32's uniform nonzero substitution at the aggregate SER is replaced
by direct empirical-joint sampling. The V31 QC packet, V28R decoder interface,
oracle-L1 treatment, layer-2 posterior, block length, iteration schedule, block
count, and mechanical success predicate remain fixed.

Existing V32 B1 is not rerun. Its archived records provide provenance only;
V34 is interpreted as a corrected control, not as a paired statistical trial.

## 2. Channel and posterior construction

For source `s`, load the frozen train count matrix `N_s[a,b]` and compute
`P_s(A=a,B=b)=N_s[a,b]/sum(N_s)`. Flatten in row-major `(A,B)` order. For each
fresh seed, initialize one NumPy PCG64 generator and draw exactly 1024 categorical
indices in one call, then recover `A=index//1024`, `B=index%1024`.

Apply F03: `U1=A>>5`, `U2=A&31`, with Bob side split identically. Construct
`P(U2|B,U1)` from the same `N_s`. A sampled positive-mass event with zero or
non-finite conditional denominator is a binding/probability defect and makes
the official result INCONCLUSIVE; do not smooth, skip, or substitute one-hot
mass.

## 3. Finite decoder control

- Reuse the V31 packet exactly: H1 has 16 rows; source H2 has 184/190/192 rows;
  all have `n=1024` over the frozen GF(32).
- Use the V32 `ProductionRunner` oracle branch and the V28R
  `decode_error_domain_posterior` identity.
- Do not execute L1. Supply true `U1` only to select each L2 prior row and mark
  every record `truth_used=true`, `truth_role=oracle_l1`,
  `operational=false`, `qualification=false`.
- Candidate decoder constants are `max_iter=30`, `streak=20`, matching V32 B1.
  No decoder parameter may be tuned after any block outcome is observed.

## 4. Frozen-matrix candidate

Order is source `1M`, `1p5M`, `2M`, then increasing seed. Each source has 20
blocks:

| source | candidate seeds | n | m2 |
|---|---:|---:|---:|
| 1M | 340101..340120 | 1024 | 184 |
| 1p5M | 340201..340220 | 1024 | 190 |
| 2M | 340301..340320 | 1024 | 192 |

Block success is `exact_l2 && syndrome_ok && tag_ok && !false_accept`.
Candidate source PASS is `successes >= 19/20`; overall PASS requires every
source PASS. Any ordinary block failure is recorded and execution continues.
Any evidence-integrity or binding defect makes overall INCONCLUSIVE. Otherwise
an unmet source threshold makes overall FAIL.

Proposed terminals:

- `matched_empirical_finite_control_pass`
- `matched_empirical_finite_control_fail`
- `matched_empirical_finite_control_inconclusive`

## 5. Exact-once evidence contract

The official execute entry point must refuse an existing `run_01`, write a
pre-execution manifest before the first block, enumerate exactly 60 unique
ordinals, and never resume, rerun, add seeds, or create `run_02`. A fatal stop
retains the partial root as INCONCLUSIVE. Tests use an explicitly injected fake
runner and workspace-only output.

Minimum evidence: manifest with binding identities and frozen matrix; one
record per attempted block; per-source summaries; final state; execution-auth
provenance; strict read-only replay; ER1 `readonly_review.json`; concise operator
handoff. Persisted terminal fields are claims and must be independently
reconstructed from block records and bound inputs.

Protected read-only roots include V25 run_04, V28R run_02_v28r, V31 run_01,
V32 finite-DE run_01, V32 operating-point-audit-v2 run_01, and V33 run_01.

## 6. Simplicity boundary

This is one research CLI plus focused tests. Reuse existing field, posterior,
packet, decoder, tag, and syndrome helpers where their semantics match. Do not
add a framework, cache, retry layer, lock, backup, checksum manifest, general
sampler abstraction, or compatibility layer. Recorded source hashes are
scientific input identities, not a new integrity subsystem.

## 7. FR1 decisions still open

FR1 must explicitly accept or revise all of the following before freeze:

1. direct 1024-iid draw semantics and exact PCG64 draw order;
2. fresh seed ranges and source/block enumeration order;
3. decoder identity plus `max_iter=30`, `streak=20`;
4. oracle-L1 markers and exact L2 success predicate;
5. source threshold: retain V32's development `>=19/20` or require `20/20`;
6. fatal versus ordinary-failure classification and no-resume behavior;
7. terminal labels, evidence fields, protected roots, and unique output root;
8. claim boundary and the prohibition on automatic successors.

