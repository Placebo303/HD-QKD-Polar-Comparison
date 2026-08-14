# Spec: Final Executable IR Method Selection

## Requirements

### R1: Eligible Candidates and Scope

The system SHALL rank only `cascade_lite` and `layered_ldpc_lite` as executable
comparison candidates. The resulting selection SHALL NOT be presented as a
production replacement for the frozen Polar workflow.

`qldpc_reference` SHALL retain `reference_only` status and SHALL be excluded
from winner ranking. `polar_existing` SHALL be labeled historical context only.

### R2: Frame-Identical Confirmation

For each confirmed stratum, both eligible candidates SHALL use identical frame
IDs, source content, preprocessing, mapping, success classifier, and
independent verification. The output SHALL preserve an attempted-frame record,
including decode and verification failures, and SHALL use all attempts in
success/failure denominators.

### R3: Pre-Registration and Provenance

Before tuning, the run SHALL freeze disjoint tuning and confirmation partitions
and record exact frame IDs, source hashes, preprocessing/config hashes, seeds,
commit, dependency versions, and environment metadata. It SHALL declare its
supported dimensions, raw-SER range/strata, and frame-length domain.

### R4: Fixed Candidate Configurations and Bounded Execution

Tuning SHALL use only the tuning partition. Before confirmation, one global
configuration per eligible candidate SHALL be frozen. Confirmation SHALL NOT
use per-point oracle selection. The protocol SHALL pre-register bounded
frame/time/compute stopping rules and record the actual stop reason.

### R5: Metrics and Evidence Threshold

Verified success fraction over all attempted frames SHALL be the common primary
outcome. Leakage fields with incompatible decomposition semantics SHALL be
reported separately and SHALL NOT determine cross-method rank. The
implementation SHALL preserve status values and derive, rather than hand-fill,
`beta_eff_empirical`.

The protocol SHALL define a per-stratum minimum attempted-frame count and a
confidence method/level before execution. If either criterion is unmet, the
decision report SHALL say `insufficient_evidence` or `no_decision` and SHALL
not claim a winner.

### R6: Polar Evidence Boundary

The protocol SHALL NOT use `polar_existing` as frame-identical confirmation.
It SHALL document that the current bridge performs aggregate dimension/bin-width
matching, lacks frame-ID/replay binding, has only a one-row tracked fixture,
and relies on legacy unavailable sources.

### R7: Additive Outputs and Route A Gate

Outputs SHALL be created only in an additive run directory under
`comparison_bench/outputs_comparison/final_ir_method_selection/` and include a
data-lock manifest, run manifest, immutable configuration snapshots,
frame-level outcomes, summaries, and decision report.

The change SHALL perform a required-field compatibility inspection against the
Route A interface without running a numerical Route A rerun. It SHALL record
pass/fail/missing fields and SHALL NOT reinterpret the gate as proof of Route A
numerical performance.

## Constraints

- No modifications to `src/`, `experiments/`, `tools/`, existing result
  outputs, or public schemas/interfaces are permitted in this change.
- Existing Polar artifacts remain read-only.
- Failure, unavailable, and reference statuses must remain visible.
