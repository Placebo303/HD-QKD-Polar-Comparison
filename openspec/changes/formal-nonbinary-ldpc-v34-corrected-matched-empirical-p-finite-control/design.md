# Design: V34 corrected matched empirical-P finite control

> FR1 accepted the revised packet. Independent science review then required the
> narrow statistical/environment amendments now incorporated here. Values remain
> non-executable until amendment re-review and main-thread `ACCEPT_FREEZE`.

## 1. Causal contrast

V34 changes exactly one channel-law variable relative to V32 B1: the block
generator law. V32's uniform nonzero substitution at the aggregate SER is replaced
by direct empirical-joint sampling. The V31 QC packet, V28R decoder interface,
oracle-L1 treatment, layer-2 posterior, block length, iteration schedule, block
count, and mechanical success predicate remain fixed.

Existing V32 B1 is not rerun. Its archived records provide provenance only;
V34 is interpreted as a corrected control, not as a paired statistical trial.
Fresh seeds are nuisance randomizations rather than a second scientific
intervention.

## 2. Channel and posterior construction

For source `s`, load the frozen train count matrix `N_s[a,b]`. Before the first
block, require shape `(1024,1024)`, all values finite and nonnegative, a finite
strictly positive total, and a finite normalized probability vector satisfying
`np.isclose(p.sum(), 1.0, rtol=1e-12, atol=1e-12)`. Any failure is fatal
INCONCLUSIVE.

The sampling operation is frozen literally as:

```python
rng = np.random.Generator(np.random.PCG64(seed))
p = N.reshape(-1, order="C") / N.sum()
idx = rng.choice(1024 * 1024, size=1024, replace=True, p=p)
A = idx // 1024
B = idx % 1024
```

Each block initializes exactly one PCG64 and makes exactly this one random
`choice` call. No preceding/following random draw, without-replacement draw,
alternative sampler, source pooling, or hidden resampling is permitted.
The accepted implementation and official execution environment SHALL use
NumPy `2.4.0`. The manifest records `numpy.__version__`; prepare and execute
must stop INCONCLUSIVE before any decoder call if it differs.

The exact sampler reference `V34-PCG64-REF1` is frozen as follows:

```text
N = np.arange(1, 17, dtype=np.float64).reshape((4, 4), order="C")
seed = 340101
size = 12
idx = [8, 9, 14, 9, 15, 13, 10, 14, 10, 4, 11, 15]
A   = [2, 2, 3, 2, 3, 3, 2, 3, 2, 1, 2, 3]
B   = [0, 1, 2, 1, 3, 1, 2, 2, 2, 0, 3, 3]
```

IR1 and official prepare SHALL construct `p=N.reshape(-1, order="C")/N.sum()`,
make one `rng.choice(16, size=12, replace=True, p=p)` call, and require exact
integer-array equality for all three outputs. A mismatch is a fatal environment
binding failure before any decoder call. This small vector binds the NumPy API
implementation; production blocks still use the frozen `(1024,1024)` tables.

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
- Decoder constants are `max_iter=30`, `streak=20`, matching V32 B1.
  No decoder parameter may be tuned after any block outcome is observed.
- `max_iter=30` is a V32-comparability binding, not evidence that the decoder is
  iteration-saturated or adequate. A 200-iteration check would change the
  intervention and requires a separate successor OpenSpec and authorization.
- The H2 matrices are exclusively the V31 packet's source-specific
  `m2=184/190/192` matrices. Reusing the V28R decoder function SHALL NOT load
  V28R's own `m2=194/200/202` matrices.

## 4. Frozen-matrix target

Order is source `1M`, `1p5M`, `2M`, then increasing seed. Each source has 20
blocks:

| source | frozen seeds | n | m2 |
|---|---:|---:|---:|
| 1M | 340101..340120 | 1024 | 184 |
| 1p5M | 340201..340220 | 1024 | 190 |
| 2M | 340301..340320 | 1024 | 192 |

Block success is `exact_l2 && syndrome_ok && tag_ok && !false_accept`.
Source PASS is `successes >= 19/20`; overall PASS requires every
source PASS. Any ordinary block failure is recorded and execution continues.
Any evidence-integrity or binding defect makes overall INCONCLUSIVE. Otherwise
an unmet source threshold makes overall FAIL.
The `>=19/20` rule is a carried-forward mechanical discriminator only. It is
not a confidence threshold, FER estimate, or qualification criterion.

The 20 draws per source are iid conditional on the frozen empirical table,
packet and decoder configuration. They support only whether this bounded
control meets its predeclared discriminator; they do not estimate general
finite-block performance. In particular, 19/20 must not be translated into a
point or interval claim about operational FER.

An ordinary block failure means the decoder returned the complete expected
schema with finite legal values, but exact recovery or syndrome/tag validation
failed. Fatal failures are input/binding drift, invalid probabilities,
decoder/code identity drift, interface exception, missing/malformed/non-finite
return fields, output collision, or process/resource interruption. Fatal means
stop immediately, retain the root as INCONCLUSIVE, and never resume, retry,
replace a seed, or create `run_02`.

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

Each block record SHALL include source/source_id, ordinal, seed, packet and
posterior identities, oracle markers, sampled SER and delta histogram,
empirical-support violations, L2 status/iterations/runtime, initial/final L2
errors, exact/tag/syndrome/false-accept flags, and posterior NLL/entropy and
true-symbol-rank summaries. Each source summary SHALL reconstruct attempted,
completed, missing and duplicate counts, success components, false accepts,
decoder terminal counts, denominator 20, iteration/runtime distributions,
`m1/m2`, syndrome leakage and 64-bit verification leakage.

Protected read-only roots are V25 run_04, V26 run_02, V28R run_02_v28r, V31
run_01, V31 closeout-audit-v2 run_01 and run_02, V32 finite-DE run_01, V32
operating-point-audit run_01, V32 operating-point-audit-v2 run_01, and V33
run_01. Any V26/V28R/V32 file used for posterior, decoder, or manifest identity
is a read-only binding and must be included in the pre/post protected-root
comparison.

## 6. Canonical binding registry

| ID | Frozen input and role |
|---|---|
| B1 | V25 `nbldpc_v25_20260818/run_04/channel_counts.npz`, SHA `e0360203b8003c821d3ee543bdaf712bd853b0ea712055b936ca37f478ddd5b2`; train counts only |
| B2 | 1M source `type2_1M_20260121_184040`, NPZ key `type2_1M_20260121_184040_N_ab_train_N_ab_train`, m2=184 |
| B3 | 1p5M source `type2_1p5M_20260121_183806`, NPZ key `type2_1p5M_20260121_183806_N_ab_train_N_ab_train`, m2=190 |
| B4 | 2M source `type2_2M_20260121_183657`, NPZ key `type2_2M_20260121_183657_N_ab_train_N_ab_train`, m2=192 |
| B5 | V31 `run_01/matrix_payloads.json`, packet `m1_16_n1024_n1024\|QC-cyclic-projective`, SHA `3d0e8773a436eed59b515f32c1bde9525814f0ecaf0d8af5cd9d2bcd12ce9242` |
| B6 | GF(32), polynomial 37 (`0b100101`), field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, F03/A02 |
| B7 | V32 `run_nonbinary_v32_finite_de_bridge.ProductionRunner` oracle branch and V32 `RUN_MANIFEST.json`: `max_iter=30`, `streak=20`, `>=19/20` |
| B8 | V28R `decode_error_domain_posterior` function identity only; V28R matrices and allocations forbidden |
| B9 | Runtime NumPy exactly `2.4.0`; literal `V34-PCG64-REF1` binds the categorical draw implementation by exact array equality |

## 7. Simplicity boundary

This is one research CLI plus focused tests. Reuse existing field, posterior,
packet, decoder, tag, and syndrome helpers where their semantics match. Do not
add a framework, cache, retry layer, lock, backup, checksum manifest, general
sampler abstraction, or compatibility layer. Recorded source hashes are
scientific input identities, not a new integrity subsystem.

## 8. FR1 revision checklist

Independent FR1 re-review must accept all of the following before freeze:

1. direct 1024-iid draw semantics and exact PCG64 draw order;
2. fresh seed ranges and source/block enumeration order;
3. decoder identity plus `max_iter=30`, `streak=20`;
4. oracle-L1 markers and exact L2 success predicate;
5. source threshold fixed at V32's development `>=19/20`, never `20/20`;
6. fatal versus ordinary-failure classification and no-resume behavior;
7. terminal labels, evidence fields, protected roots, and unique output root;
8. claim boundary and the prohibition on automatic successors.
9. NumPy 2.4.0 environment identity and exact `V34-PCG64-REF1` equality.
