# Code-factor extrinsic contract — design (freeze only, Phase B)

> Status: design freeze. No code, no decoder call, no root, no execution.
> All authorizations false. Predecessor D7-F acceptance:
> `D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`. Conventions
> mirror the BP provenance change
> (`openspec/changes/v72p2d7-layer-interface-belief-provenance/`) and D7-A
> certification (`v72p2d7-gf32-decoder-certification`).

## Frozen formula and normalization

For a cold decoder with normalized positive input prior `p_in(x)` (the exact
normalized prior used internally: floor 1e-15 + renormalize, the v35
`priors_clean` rule) and final log belief `L_post(x)`:

```text
L_code_ext(x) = L_post(x) - log(p_in(x))
```

- Defined only up to a per-symbol-variable additive constant: adding a
  row-constant `c_i` to any row changes no transported distribution.
- Transport normalization: stable softmax of `L_code_ext` rows.
- Stored-field normalization (frozen): subtract the row log-sum-exp, i.e.
  store `L_code_ext - logsumexp(L_code_ext, axis=1, keepdims)`.
- Why log-sum-exp, not max: subtracting the row maximum leaves rows with an
  arbitrary unnormalized scale (max 0 but unknown sum), so two stored fields
  from different sweeps/priors are not directly comparable and a downstream
  `log(p_in)+L_code_ext` reconstruction inherits the unknown offset; the
  log-sum-exp normalization makes every stored row exactly log-normalized
  (`softmax` of the stored row equals the transported distribution), so
  reconstruction `softmax(log(p_in)+L_code_ext)` is exact without
  re-deriving a hidden constant. Max-subtraction remains valid only as an
  internal numerical stabilizer inside softmax, never as the stored form.

## Frozen tokens and fields

### Extrinsic-provenance tokens (exact, own namespace)

- `NO_CHECK_EVIDENCE`
- `CHECK_EXTRINSIC`
- `WARM_START_UNSPECIFIED`

This namespace is distinct from `belief_provenance`
(`PRIOR_ONLY`/`CHECK_UPDATED`/`WARM_START_UNSPECIFIED`). The two
`WARM_START_UNSPECIFIED` tokens share a spelling but live in different
fields with different meanings (belief provenance vs extrinsic usability);
consumers must check the `extrinsic_provenance` field, never infer from
`belief_provenance` or `iterations`.

### Optional result fields (fixed names)

- `extrinsic_log_beliefs`: log-domain extrinsic message array, shape
  `(n, 32)`, row-normalized by log-sum-exp as above; `None`/absent when
  ineligible (iteration 0, warm, failure paths).
- `extrinsic_provenance`: one of the three tokens above, or `None`/absent
  (unspecified/legacy). `None` is never upgraded to `CHECK_EXTRINSIC`.

Both fields are additive and defaulted (`None`) so existing positional
construction and all current test fakes keep working.

## Frozen behavior mapping

- **Cold start** (decoder called with `warm_beliefs=None`): after ≥1
  completed check sweep with finite shape-correct beliefs, populate
  `extrinsic_log_beliefs` and `extrinsic_provenance=CHECK_EXTRINSIC`.
- **Iteration 0** (return at the initial-syndrome check before any check-row
  update, `iterations == 0`): neutral zero matrix + `NO_CHECK_EVIDENCE`;
  ineligible for cross-layer transfer.
- **Warm start** (any non-`None` `warm_beliefs` seed without
  caller-supplied provenance): no usable extrinsic,
  `extrinsic_provenance=WARM_START_UNSPECIFIED`, fail-closed. Provenance is
  never inferred from `iterations`.
- **Nonfinite/shape mismatch**: fail-loud or ineligible, never silently
  repaired (no re-flooring, no renormalization rescue, no fallback fill).
- **No-persistence rule**: no beliefs/messages persisted by any writer —
  extrinsic arrays are transient decoder-result fields only; scalar-only
  evidence roots (as in D7-E/F) must not gain belief/prior/message payloads.

## Narrow consumer helper (frozen contract, implementation later)

- Accepts only explicit `CHECK_EXTRINSIC` with a finite shape-correct
  array; stably softmaxes it for transport.
- Rejects `NO_CHECK_EVIDENCE`, `WARM_START_UNSPECIFIED`, missing/`None`/
  unknown provenance, missing arrays, wrong shapes, nonfinite values —
  fail-closed before any cross-layer prior is computed.
- Not wired into D5/D6/D7 production execution yet; existing
  posterior-based one-pass D7-E/F behavior stays immutable.

## Certification matrices (frozen fixture families)

Conventions: GF(32), poly 37, `q=32`; max-abs asserts at `1e-10`;
exact-enumeration oracles; fixed seeds below (no tuning, no reseed on
failure). Prior regimes: ordinary (near-uniform cyclic), skewed/peaked
(asymmetric mass 0.9 at a fixed label), and per-row asymmetric variants.

- **EXT-T (tree-exact):** single degree-2 and degree-3 checks; shapes
  `(1,2)`, `(1,3)`; coefficient sets covering `(1,1)`, `(1,2,3)`,
  `(2,7,13)`, `(1,13,29)` with the full multiplier sweep convention for
  degree 2 (all 31 nonzero second coefficients); syndromes `(0,5,17,31)`
  with at least two nonzero per family; asymmetric priors (skewed peak ≠
  syndrome-consistent label); negative direction/label controls (swapped
  edge direction and negated-label variants must mismatch deterministically,
  proving the oracle is not vacuous). Compare normalized outgoing
  code-factor message per variable against exact
  `P(syndrome constraints | x_i)` marginalized over other variables and
  their priors. Compare distributions (max-abs ≤1e-10), not only MAP.
  Seeds: `2026091401` (check priors), `2026091402` (tree priors).
- **EXT-L (loopy recurrence):** tiny loopy graph (2 checks × 3 variables,
  each variable degree 2); sweeps 1–3 of the cold row-layered schedule
  (damping 1.0); emitted extrinsic after each completed sweep vs an
  independently coded recurrence's accumulated check-to-variable message
  sum (max-abs ≤1e-10). Never vs MAP. Seed: `2026091403`.
- **EXT-N (no-returned-evidence two-layer tree):** channel factor
  `P(U1,U2|B)` (tiny: 2+2 variables, q=32 rows from seed `2026091404`) +
  one syndrome factor per layer (degree-2, nonzero syndromes). Demonstrate:
  1. posterior-based back-transfer double-counts the originating syndrome
     in a constructed counterexample (deterministic numerical gap);
  2. explicit code-extrinsic transfer matches independent forward and
     backward sum-product factor messages within `1e-10`;
  3. iteration-0 neutral extrinsic cannot create a false lift;
  4. warm/unknown provenance is rejected.
  Decisive certification (packet §7 D04): if no deterministic
  counterexample or exact match can be produced, STOP with mathematical
  ambiguity — do not weaken tolerances or rename posterior as extrinsic.

## Tolerances (frozen)

- `1e-10` max-abs for tree-exact distribution match.
- `1e-10` max-abs for independent-recurrence match.
- D7-A/BP precedent; no loosening without a pre-results justification
  recorded here — none recorded.

## Compatibility matrix

| # | Consumer / site | Under this contract |
|---|---|---|
| 1 | v35 `DecoderResult` + row-layered returns | Additive optional fields only; `x_hat`/`syndrome_ok`/`iterations`/`status`/`final_beliefs`/`belief_provenance` byte-identical |
| 2 | v35 flooding returns | Same additive fields ONLY if needed for `DecoderResult` coherence; default DEFERRED (record decision; do not broaden into a schedule project) |
| 3 | Narrow consumer helper (new) | Accepts only explicit `CHECK_EXTRINSIC`; fail-closed otherwise; not wired into production |
| 4 | D5/D6/D7 + historical v45–v55 + shell adapter + v72p2d3/V64 paths | Unchanged; NO auto-switch to the new field |
| 5 | Static inventory test | Must fail if any production cross-layer consumer uses explicit extrinsic without its own future OpenSpec |

## Alternatives (decision frozen)

| Alt | Verdict |
|---|---|
| Store row-normalized by subtracting max | Rejected: leaves unknown scale; breaks direct comparability and exact reconstruction (see rationale above) |
| Reconstruct prior by re-cleaning caller-side priors | Rejected: duplicates numerical cleaning rules; consumers must use the decoder-carried explicit field |
| Persist extrinsic arrays in evidence roots | Rejected: no-persistence rule |
| Certify loopy extrinsic against exact MAP | Forbidden: loopy BP is not exact; recurrence comparison only |

## Frozen implementation file map (names fixed here for the later implementer)

- Independent oracle:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_extrinsic_oracle.py`
  — must not import the production check-update/extrinsic helper; numpy-only
  (may import field/alphabet-size constants only after independently
  checking declared values, D7-A convention).
- Tests: `comparison_bench/tests/test_v72p2d7_gf32_extrinsic_contract.py`
  — tiny GF32 checks, exact-enumeration oracles, `1e-10` asserts, mirroring
  D7-A/BP fixture and test conventions.
- Producer/helper edits confined to:
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
  — additive optional fields + one narrow consumer helper only.
- Flooding receives the same additive fields ONLY if needed for
  `DecoderResult` coherence; decision rule: populate flooding iff a
  `DecoderResult` coherence test (all return sites carry the same field
  set) requires it, else record `FLOODING_EXTRINSIC_DEFERRED`. Default:
  DEFERRED.

## Implementation outline (not started here)

Ordered tasks live in `tasks.md`. This design fixes semantics, fixtures,
tolerances, and file paths only; guard error types, storage details beyond
the frozen normalization, and review mechanics are implementation decisions
inside this frozen contract.
