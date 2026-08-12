# Design: final-ir-method-selection

## Decision Boundary

The decision selects the best executable comparison candidate only. The sole
ranked candidates are `cascade_lite` and `layered_ldpc_lite`.
`qldpc_reference` is reported as `reference_only` and excluded from ranking.
`polar_existing` is historical context only, never a same-frame comparator or
winner candidate.

## Locked Comparison Unit

For every confirmation stratum, both candidates must receive the exact same
frame IDs, source bytes/hashes, preprocessing version and parameters, mapping,
success classifier, and independent verification procedure. The record must
include attempted frame IDs, including decode and verification failures; rates
use all attempted frames as denominators. A missing or incompatible input makes
the stratum ineligible rather than silently dropping it.

The protocol must declare its supported domain before data lock: dimensions,
raw-SER strata, and frame-length range. Claims are limited to completed strata
inside that domain.

## Tuning and Confirmation

Freeze a disjoint tuning/confirmation split before tuning. The data-lock
manifest stores exact frame IDs, source hashes, preprocessing/config hashes,
seeds, git commit, dependency versions, and environment metadata.

Tune only on the tuning partition. Select one fixed global configuration per
candidate before confirmation; no per-point oracle selection is permitted.
Confirmation runs use those frozen configurations unchanged. The protocol must
set bounded frame/time/compute stopping rules in advance and record any stop
reason. It may not extend a stratum adaptively to reverse an observed result.

## Metrics and Decision Rule

The common primary outcome is independently verified success fraction over all
attempted frames. Secondary common metrics may be ranked only when their
definitions match. Leakage decompositions that are not compatible are shown in
separate labeled tables and are not used for cross-method ranking;
`beta_eff_empirical` remains derived from leakage and error inputs.

Before execution, define the minimum attempted-frame count per declared
stratum and the confidence-interval method/level for paired comparison. A
candidate may be selected only when each required stratum meets that sample
rule, bounded runs complete, and the pre-registered confidence rule supports
the stated direction. Otherwise the result is `insufficient_evidence` or
`no_decision`, with no overclaim.

## Polar and Route A Boundaries

The current `polar_existing` bridge uses aggregate dimension/bin-width
matching, has no frame-ID/replay binding, contains only a one-row tracked
fixture, and points to legacy unavailable sources. Its rows can be retained as
historical context but cannot validate this decision.

Route A requires a required-field compatibility gate: inspect the confirmation
artifact schema, verification-accounting fields, and manifest provenance
against the Route A interface and record pass/fail/missing fields. This is a
non-numerical gate only; it must not invoke a Route A rerun.

## Outputs

All new artifacts use an additive run directory under
`comparison_bench/outputs_comparison/final_ir_method_selection/<run_id>/`.
It contains immutable config snapshots, data-lock and run manifests,
frame-level attempted-outcome records, aggregate summaries, compatibility-gate
report, and a decision report. Existing outputs are never overwritten.

