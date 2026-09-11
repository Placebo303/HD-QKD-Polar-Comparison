# D7-E provenance-safe cross-layer discriminator — design

> Freeze only (Track B R14). No code, no decoder call, no Model-F content
> read, no root, no execution. All authorizations false.

## Frozen semantics

### Identities and decoder contract (R08)

- `f` order `[1.0, 1.2]`.
- Seeds `2026091300..2026091315`, ascending, exactly 16 per f.
- Same generated blocks, graph seeds, frozen rows/mothers and corrected
  concentration Model-F semantics as accepted D7-C/D7-D:
  n=64; L1 rows 49 (f=1.0) / 59 (f=1.2); L2 rows 43 (f=1.0) / 52 (f=1.2);
  D5-native mothers `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start (`warm_beliefs=None`),
  `max_iter=90`, damping `1.0` (`v35.decode_row_layered_fftqspa` shape via
  the accepted `d5.bind_historical_decoder` adapter).
- Directions in order `[L1_TO_L2, L2_TO_L1]`.
- No flooding: D7-D established no preregistered flooding advantage.
- No oracle decoder calls: accepted D7-C tables are a contextual ceiling
  only; no `L1_ORACLE_U2` / `L2_ORACLE_U1` prior is constructed or decoded.

Per `(f, seed)` exact slot order:

```text
L1_TO_L2_SOURCE_L1_MARGINAL
L1_TO_L2_TARGET_L2_CONTROL_MARGINAL
L1_TO_L2_TARGET_L2_TRANSFER       # invoked only if source CHECK_UPDATED
L2_TO_L1_SOURCE_L2_MARGINAL
L2_TO_L1_TARGET_L1_CONTROL_MARGINAL
L2_TO_L1_TARGET_L1_TRANSFER       # invoked only if source CHECK_UPDATED
```

192 scheduled slots: 128 mandatory source/control decoder calls plus up to
64 provenance-eligible transfer calls. A blocked transfer slot is a recorded
non-invocation, never replacement, retry or fake decoder result.

### Transfer formulas and estimator identity (R09)

Let the accepted corrected joint model be `P(U1,U2|B=b)` and the source BP
APP approximation be normalized `q` from a `CHECK_UPDATED` log belief.

- L1 to L2: `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`.
- L2 to L1: `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`.

Estimator identity is a hard pre-execution contract, not an implementation
choice. D7-E must obtain the joint only through
`prepare_model_f_prior_candidate` / `build_f_model_concentration`, whose
per-Bob-column smoothing is
`(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`. The historical
`build_f_model` rule `counts + lambda` per cell is forbidden. Static and
behavioral tests must fail if D7-E references that legacy builder, and a
tiny asymmetric table must distinguish the two formulas numerically.

Floor/renormalize exactly as the accepted D5 helper contract
(`_floor_renorm` with `DECODER_FLOOR = 1e-15`, applied once at the decoder
boundary). The source q is transient and never persisted. No source truth
enters either formula (truth selects nothing; only the source belief and
the accepted joint do).

### Pair and eligibility semantics (R10)

For each direction, the target control and transfer share f/seed/block/
target H/syndrome/decoder configuration; only the target prior differs.
Source exactness does not gate eligibility. Eligibility requires source
status finite/non-crash, belief shape valid and provenance exactly
`CHECK_UPDATED` (via the accepted `require_check_updated_provenance`
helper; `PRIOR_ONLY`, missing/`None`/unknown, `WARM_START_UNSPECIFIED`
block before any mixer/target decoder).

Per `(f,direction)` stratum, at least 12/16 transfer slots must be eligible
for a mechanism label. Fewer gives `PROVENANCE_COVERAGE_BLOCKED`; no
denominator substitution or replacement seed.

### Stratum labels (R11, first match)

On eligible control/transfer pairs:

1. `STRONG_TRANSFER_LIFT`: eligible >=12, transfer-only >=4,
   control-only <=1, transfer exact >=4, zero crash/nonfinite.
2. `TRANSFER_REGRESSION`: eligible >=12, control-only >=4,
   transfer-only <=1.
3. `NO_TRANSFER_RECOVERY`: eligible >=12, transfer exact <=1 and control
   exact <=1.
4. `CONTROL_ALREADY_RECOVERS`: eligible >=12 and control exact >=12.
5. `AMBIGUOUS_TRANSFER_EFFECT`: every other complete finite eligible case.
6. Empty label when eligible <12; coverage status records the reason.

The threshold `4/16` deliberately reuses D7-C's frozen useful-lift routing
threshold. It is a mechanism gate, not a probability estimate.

### Run terminal priority (R12, first applicable)

1. `D7_E_PRE_EXECUTION_BLOCKED`
2. `D7_E_WATCHDOG_TIMEOUT_VOID`
3. `D7_E_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_E_RESOURCE_OVERRUN`
5. `D7_E_INCOMPLETE_CORE_CALL_MATRIX`
6. `D7_E_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_E_BIDIRECTIONAL_TRANSFER_LIFT` — same f has strong lift both
   directions
8. `D7_E_L1_TO_L2_TRANSFER_LIFT` — strong only L1 to L2
9. `D7_E_L2_TO_L1_TRANSFER_LIFT` — strong only L2 to L1
10. `D7_E_TRANSFER_REGRESSION` — any regression, no strong lift
11. `D7_E_NO_USEFUL_TRANSFER_RECOVERY` — all four strata no recovery
12. `D7_E_MIXED_TRANSFER_DIAGNOSTIC`

All four strata and blocked-slot counts persist under higher-priority
terminal.

### Budgets (R13)

- Hard cap 192 decoder calls; no concurrency/retry/rerun/resume.
- Per-call watchdog 120 s.
- Stored scientific wall <=1500 s.
- Outer GNU timeout `1800` plus `-k 30`.
- WSL stdlib `resource` RSS finite positive and `<2GiB` before the first
  call and recorded maximum during run; no psutil.
- Target fresh direct child
  `workspace/d7_e_cross_layer_discriminator_<uuid>/`, no overwrite/subdirs.

### Reuse points (narrow; read-only, no execution here)

- D7-C module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_bidirectional_oracle.py`:
  `frozen_identities`, `build_joint`, `build_mother`, `prepare_inputs`,
  `condition_prior_qn`, `decoder_prior`, `evaluate_call` — identity/model
  helpers only, via narrow import or exact contract copy with equality
  tests; the D7-C module stays unmodified.
- D5 helpers
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`:
  `prepare_model_f_prior_candidate`, `build_f_model_concentration`
  (`LAMBDA_STAR`), `sample_matched_block`, `build_dv3_nested_support`,
  `assign_gf32_coefficients`, `symbols_to_layers` / `layers_to_symbols`,
  `marginalize_f_to_p1` / `conditionalize_f_to_p2` (marginal-control shape
  reference), `_floor_renorm` (`DECODER_FLOOR`), `_decode_block` result
  semantics, `require_check_updated_provenance` path (via
  `_require_check_updated_provenance`).
- V35 contract
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`:
  `decode_row_layered_fftqspa`, `BELIEF_PROVENANCE_*`,
  `require_check_updated_provenance`, current-belief labels
  (`PRIOR_ONLY_CURRENT_BELIEF` / `CHECK_UPDATED_CURRENT_BELIEF`); consumer
  only, no V35 edit.

## Alternatives considered

- **Alternating/joint BP or feedback loop:** rejected — not a
  discriminator; needs its own packet and provenance design.
- **Flooding arm:** rejected — D7-D froze no flooding advantage; D7-E holds
  schedule fixed at row-layered.
- **Oracle-prior arm:** rejected — D7-C already supplies the ceiling; D7-E
  decodes marginal/control/transfer only.
- **Source-exact gating:** rejected — exactness does not gate eligibility;
  only finite/non-crash + valid shape + `CHECK_UPDATED` does.
- **Coverage substitution (replacement seeds/denominators):** rejected — a
  thin stratum reports `PROVENANCE_COVERAGE_BLOCKED`, never a relabeled or
  resampled stratum.
