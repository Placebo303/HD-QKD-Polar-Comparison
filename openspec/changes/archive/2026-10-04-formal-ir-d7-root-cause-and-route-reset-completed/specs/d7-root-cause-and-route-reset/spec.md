## ADDED Requirements

### Requirement: Same-input G1/D7 transfer equivalence is established by test

The repository SHALL expose one canonical implementation of the source
posterior-to-probability conversion `q` and of the transfer prior
`P(U2|B) = sum_u1 q(u1) P2(u1,b,u2)` inside the accepted D5 module, and the
legacy G1 layered path SHALL form those quantities through that canonical
implementation. A deterministic fixture SHALL compare, on the same in-memory
graph, block, priors, and injected decoder results, the L1 input prior, `q`,
the L2 transfer prior, both target syndromes, the decoded target, and the
per-layer counters between the legacy-G1-compatible path and the D7 path.

#### Scenario: Frozen exact/numerical comparison contract

- **WHEN** the two paths are compared on identical inputs
- **THEN** `q`, the target syndromes, the decoded target, and the per-layer
  counters SHALL be exactly equal
- **AND** the L1 input prior and the L2 transfer prior SHALL be equal within
  `atol=1e-12` (`rtol=0`), with the maximum absolute difference recorded
- **AND** a failure of either criterion SHALL localize the first unequal
  tensor and flat index and stop without compensation or tuning.

#### Scenario: Decoder is not rewritten

- **WHEN** the canonical helpers are introduced
- **THEN** no decoder implementation is rewritten and no historical
  artifact changes.

### Requirement: Non-CHECK_UPDATED cross-layer consumption fails closed

Both the legacy G1 layered path and the D7 transfer path SHALL refuse to
consume L1 beliefs whose provenance is not exactly `CHECK_UPDATED`, before
constructing the L2 transfer prior or invoking the L2 decoder.

#### Scenario: Provenance boundary matrix

- **WHEN** the source return carries exact `CHECK_UPDATED`
- **THEN** the gated transfer proceeds
- **WHEN** the source return has a missing provenance key, explicit `None`,
  `PRIOR_ONLY`, an unknown token, or a valid zero-iteration prior-only
  return
- **THEN** the transfer is refused with no mixer call and no L2 decoder call
  on both paths.

### Requirement: Future G1 evidence is per-layer and provenance-observable

The G1 evidence schema SHALL be extended additively with per-layer exact
counts, per-layer syndrome-valid counts, per-layer iteration totals, the
CHECK_UPDATED provenance count, and transfer-invoked/blocked counts.

#### Scenario: Additive schema

- **WHEN** G1 evidence is written after this change
- **THEN** all previously existing keys, file names, and existing table
  columns are preserved and the new fields are appended
- **AND** a blocked transfer is recorded as a non-invocation, never
  replaced, and no L2 prior or L2 decode is produced from it.

### Requirement: No-write historical decoder probe

A pure callable SHALL resolve the historical decoder (only when no decoder
is injected) and report whether one result carries accepted provenance,
without starting a phase run, creating an output root, or writing any file.

#### Scenario: Injected fake path

- **WHEN** the probe is called with an injected fake decoder
- **THEN** no historical decoder import or production call occurs and the
  report contains the provenance token, acceptance flag, iterations, and
  shape validity.

### Requirement: Frozen multi-graph exploratory diagnostic

One small runner SHALL implement the packet-frozen multi-graph diagnostic:
graph pairs `(2026090501,2026090502)`, `(2026091401,2026091402)`,
`(2026091501,2026091502)`; block seeds `2026091300..2026091315`; n=64 with
f=1.2 primary (rows L1=59/L2=52) and f=1.0 sanity (rows L1=49/L2=43); arms
marginal L1, L1-to-L2 transfer, marginal L2, L2-to-L1 transfer, and
forward/reverse joint outcomes; accepted Model-F input, `max_iter=90`,
`damping_alpha=1.0`.

#### Scenario: Fresh output and no overwrite

- **WHEN** the runner executes
- **THEN** it writes `manifest.json`, `call_records.csv`, `block_pairs.csv`,
  `graph_summary.csv`, `across_graph_summary.json`, `report.md`, and
  `command_log.txt` into one fresh user-specified `workspace/` root
- **AND** it refuses an existing root.

#### Scenario: Descriptive statistics only

- **WHEN** paired outcomes are summarized
- **THEN** raw discordant counts are reported per graph and per f with exact
  two-sided McNemar/binomial p-values and confidence intervals
- **AND** no pass/fail decision uses only a p-value and no pooled claim hides
  graph or f heterogeneity.

#### Scenario: Terminal vocabulary

- **WHEN** the runner completes
- **THEN** exactly one of `GRAPH_SENSITIVITY_OBSERVED`,
  `NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE`, `INCONCLUSIVE`, or the
  engineering/resource blocker is recorded, each carrying
  `EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`.

### Requirement: Bounded strong-reference ladder

A dormant reference ladder SHALL provide the current decoder at 90
iterations, the same decoder at the frozen 360 ceiling, and the existing
flooding schedule at 90 iterations, recording exact, syndrome-valid,
residual syndrome weight, computable exact posterior scores, and whether a
higher arm changes the outcome.

#### Scenario: Tiny exact-enumeration correctness

- **WHEN** posterior scores are computed for a tiny enumeration-capable
  fixture
- **THEN** the enumeration, normalization, and ranking are cross-checked
  against an independent brute-force computation
- **AND** n=64 outputs are labeled `STRONG_REFERENCE_DIAGNOSTIC` and never
  presented as ML proof or information-theoretic feasibility.

#### Scenario: Ladder scope

- **WHEN** the ladder is applied
- **THEN** it applies only to frozen multi-graph f=1.2 blocks that fail, with
  no adaptive seed replacement.

### Requirement: G2 readiness is reconciled and runtime status is explicit

The G2 implementation SHALL match the accepted D5 plan matrix and SHALL
preserve the four-state grading vocabulary. Its runtime status SHALL be
`G2_RUNTIME_UNVERIFIED` until measured/scaled probes are explicitly
authorized.

#### Scenario: Reconciled matrix

- **WHEN** the G2 matrix is inspected
- **THEN** n=256, f=`(1.0,1.1,1.2)`, rows L1 `(196,215,235)`, rows L2
  `(172,189,206)`, block seeds `2026091000..2026091199`, graph seeds
  `2026090501`/`2026090502`, and APP 200 + oracle 40 per f are present
- **AND** fake-runner tests confirm the exact call count, budget accounting,
  additive output, per-layer metrics, and zero accidental decoder calls.

#### Scenario: Four states preserved

- **WHEN** G2 grading is evaluated
- **THEN** the only outcomes are `G2_SYNTHETIC_QUALIFIED`,
  `G2_INCONCLUSIVE`, `G2_CURRENT_CONFIGURATION_FAILED`, or
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`
- **AND** no unconditional `ROUTE_DEAD` wording is revived.

### Requirement: Historical evidence and D7-F corrigendum

All historical evidence SHALL be retained byte-identical; corrections SHALL
be additive or superseding.

#### Scenario: D7-F label interpretation

- **WHEN** the D7-F result is cited
- **THEN** `D7_F_REVERSE_ORDER_REGRESSION` is a historical machine label for
  single-graph n=16 paired evidence (candidate-only 0, reference-only 2, both
  0, neither 14 at f=1.2) and is not treated as an immutable general
  mechanism fact.

#### Scenario: G2 pending status

- **WHEN** the G2 experiment is referenced
- **THEN** it is recorded as pending (not failed, skipped, or superseded) and
  remains the accepted-plan n=256 length discriminator.

### Requirement: No execution is authorized by this change

The change SHALL NOT execute a production decoder, CAL/VAL loader, G1 run,
multi-graph run, reference ladder run, G2 run, or D7-H run.

#### Scenario: Dormant phases

- **WHEN** any runner is entered without its explicit authorization key and
  `authorized=True`
- **THEN** it refuses before decoder bind, Model-F read, or root creation.

#### Scenario: Lifecycle terminal

- **WHEN** Phases A–F complete
- **THEN** the lifecycle terminal is
  `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`
- **AND** X1–X4 and D7-H remain dormant until the main thread records exact
  command, fresh root, budget, stop rules, and explicit authorization, with
  Pre-EXECUTE authorization and independent Pre-RESULT review.
