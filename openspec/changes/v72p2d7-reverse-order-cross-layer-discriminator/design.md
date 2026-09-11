# D7-F reverse-order cross-layer discriminator — design

> Freeze only (Phase B). No code, no decoder call, no Model-F content
> read, no root, no execution. All authorizations false.

## Frozen semantics

### Identities and decoder contract (B01)

- `f` order `[1.0, 1.2]`.
- Seeds `2026091300..2026091315`, ascending, exactly 16 per f.
- Same generated blocks, graph seeds, frozen rows/mothers and corrected
  per-Bob-column concentration Model-F semantics as accepted D7-C/D7-E:
  n=64; L1 rows 49 (f=1.0) / 59 (f=1.2); L2 rows 43 (f=1.0) / 52 (f=1.2);
  D5-native mothers `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start (`warm_beliefs=None`),
  `max_iter=90`, damping `1.0` (`v35.decode_row_layered_fftqspa` shape via
  the accepted `d5.bind_historical_decoder` adapter).
- No oracle, no flooding, no CAL/VAL, no real/raw, no graph/mother
  changes.

### Paired arms and eligibility gate (B02)

For every `(f, seed)` execute arms in this exact order:

```text
FORWARD_L1_TO_L2:  decode L1 marginal
                   -> gate -> transient P(U2|B,s1) -> cold decode L2
REVERSE_L2_TO_L1:  decode L2 marginal
                   -> gate -> transient P(U1|B,s2) -> cold decode L1
```

The gate requires source status finite/non-crash, belief shape valid, and
provenance exactly `CHECK_UPDATED` (via the accepted
`require_check_updated_provenance` helper; `PRIOR_ONLY`,
missing/`None`/unknown, `WARM_START_UNSPECIFIED` block before any
mixer/target decoder). Source exact is NOT an eligibility gate: a source
decode that is inexact but finite/non-crash with valid shape and
`CHECK_UPDATED` still transfers.

An ineligible second stage is a blocked non-call: recorded, never
replaced, never retried, never fabricated. There is no transfer back to
the source layer within either arm.

Maximum slots: `32 identities × 4 stages = 128` decoder calls (64
mandatory source marginals + up to 64 gated target transfers).

### Transfer formulas and estimator identity (B01/B04)

Let the accepted corrected joint model be `P(U1,U2|B=b)` and the source BP
APP approximation be normalized `q` from a `CHECK_UPDATED` log belief.

- Forward: `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`.
- Reverse: `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`.

Estimator identity is a hard pre-execution contract, not an implementation
choice. D7-F must obtain the joint only through
`prepare_model_f_prior_candidate` / `build_f_model_concentration`, whose
per-Bob-column smoothing is
`(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`. The historical
`build_f_model` rule `counts + lambda` per cell is forbidden. Static and
behavioral tests must fail if D7-F references that legacy builder, and a
tiny asymmetric table must distinguish the two formulas numerically.

Floor/renormalize exactly as the accepted D5 helper contract
(`_floor_renorm` with `DECODER_FLOOR = 1e-15`, applied once at the decoder
boundary). The source q is transient and never persisted. No source truth
enters either formula (truth selects nothing; only the source belief and
the accepted joint do).

### Outcome accounting (B03)

For each arm persist scalar-only:

- first/second stage eligibility and provenance;
- L1 exact/syndrome and L2 exact/syndrome separately;
- `both_layers_exact = L1_exact AND L2_exact` only;
- calls, blocked, crash/nonfinite, iterations/work, wall, RSS.

Never merge syndrome success into exact success: syndrome-satisfied rows
stay in their own columns and never set any `*_exact` field.

### Evidence-use contract (B04)

Each target starts cold from the transfer prior and consumes its own
syndrome once. No target posterior is fed back, blended, multiplied, or
reused — within an arm or across arms. Tests must prove the first-stage
syndrome is consumed only by its source decoder and the second-stage
syndrome only by its target decoder (e.g. syndrome-identity pins on each
call record plus a negative test showing a swapped/replayed syndrome
cannot verify).

Explicitly documented: >2-stage alternating stays blocked pending a
cavity/extrinsic-message contract capable of excluding returned syndrome
evidence. D7-F encodes no such contract and no automatic successor.

### Paired labels per f (B05)

Across the same 16 seeds compare reverse candidate C
(`REVERSE_L2_TO_L1` both-exact) with forward reference R
(`FORWARD_L1_TO_L2` both-exact). Per seed:

- `candidate_only`: C both-exact and R not;
- `reference_only`: R both-exact and C not;
- `both`, `neither`.

First-match label per f:

1. `COVERAGE_BLOCKED` if either arm has fewer than 12/16 complete
   eligible paired outcomes;
2. `REVERSE_REGRESSION` if `reference_only >= 2` and
   `candidate_only == 0`;
3. `STRONG_REVERSE_LIFT` if `candidate_only >= 4` and
   `reference_only == 0`;
4. `WEAK_REVERSE_LIFT` if `candidate_only > reference_only` but strong is
   not met;
5. `NO_REVERSE_LIFT` otherwise.

These are synthetic diagnostic labels, not FER thresholds. The `4/16`
threshold deliberately reuses D7-C's frozen useful-lift routing threshold
as a mechanism gate.

### Run terminal priority (B06, first applicable, verbatim)

1. `D7_F_PRE_EXECUTION_BLOCKED`
2. `D7_F_WATCHDOG_TIMEOUT_VOID`
3. `D7_F_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_F_RESOURCE_OVERRUN`
5. `D7_F_INCOMPLETE_MATRIX_BLOCKED`
6. `D7_F_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_F_REVERSE_ORDER_STRONG_LIFT` — either f is strong and the other
   does not regress
8. `D7_F_REVERSE_ORDER_WEAK_LIFT` — either f is weak and neither regresses
9. `D7_F_REVERSE_ORDER_REGRESSION`
10. `D7_F_NO_USEFUL_REVERSE_ORDER_LIFT`

No automatic successor is encoded. All paired outcomes and blocked counts
persist under a higher-priority terminal.

### Budgets (B07)

- Hard cap 128 decoder calls; no concurrency/retry/rerun/resume.
- Per-call watchdog 120 s.
- Stored scientific wall <=1500 s.
- Outer GNU timeout `1800` plus `-k 30`.
- On Linux/WSL, current-process peak RSS from `/proc/self/status` field
  `VmHWM` (unit exactly `kB`, `bytes = value * 1024`), strict `< 2 GiB`,
  fail-closed: missing/unparseable measurement blocks before the first
  scientific call and at the first affected call mid-run; no
  psutil/subprocess substitution.
- Sequential execution only.
- Target fresh direct child
  `workspace/d7_f_reverse_order_discriminator_<uuid>/`, no
  overwrite/subdirs.
- Exactly seven scalar text files (`manifest.json`,
  `decoder_records.csv`, `arm_pairs.csv`, `stratum_summary.csv`,
  `summary.json`, `report.md`, `command_log.txt`) plus an independent
  read-only verifier that never calls a decoder and never loads Model-F.

### Reuse points (narrow; read-only, no execution here)

- D7-E module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`:
  frozen identities, joint builder, mother builder, input preparation,
  transfer conditioners, decoder-prior adapter, single-call evaluator —
  identity/model helpers only, via narrow import; the D7-E module stays
  unmodified. No predecessor-module copies.
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
- VmHWM RSS parser convention from the accepted D7-E A2 delta
  (`parse_vmhwm_rss_bytes` semantics: exactly one ASCII
  `VmHWM: <positive integer> kB` line, at most 18 digits, else `None` and
  block); scalar seven-file writer and read-only verifier conventions from
  D7-E, adapted to the `arm_pairs.csv` schema.

### Planned code paths (for the implementer, frozen names)

- Module:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py`
- Tests:
  `comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py`
- Script: `scripts/v72p2d7_gf32_reverse_order_discriminator.py`

Lazy binding + DI required: import/`--help`/`--dry-run`/unauthorized/
verifier/tests must not read real Model-F, call/bind a real decoder, or
create a scientific root.

## Alternatives considered

- **Feedback cycle / alternating BP:** rejected — existing provenance does
  not expose cavity/extrinsic messages; >2-stage alternating stays
  blocked pending that contract.
- **Flooding arm:** rejected — D7-D froze no flooding advantage; D7-F
  holds schedule fixed at row-layered.
- **Oracle-prior arm:** rejected — D7-C already supplies the ceiling;
  D7-F decodes marginals and gated transfers only.
- **Source-exact gating:** rejected — exactness does not gate eligibility;
  only finite/non-crash + valid shape + `CHECK_UPDATED` does.
- **Coverage substitution (replacement seeds/denominators):** rejected — a
  thin arm reports `COVERAGE_BLOCKED`, never a relabeled or resampled
  stratum.
- **Joint factor graph / generalized turbo:** rejected — not a paired
  order discriminator; needs its own packet.
