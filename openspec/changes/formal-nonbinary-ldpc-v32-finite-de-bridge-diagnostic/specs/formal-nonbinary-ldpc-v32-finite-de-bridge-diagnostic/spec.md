# Spec: formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic

## Scope

This delta spec freezes the **V32 diagnostic bridge**: a paired, pre-registered B0–B5 arm execution that attributes the V31 n=1024 `finite_graph_fail` (300/300, 0 exact/tag/syndrome; n=2048 only a 14-block 1M prefix) to one of four mutually exclusive root causes. V32 is not a qualification, not a promotion, not a new reconciler, and not a V31 completion.

In scope:
- One harness executing arms B0–B5 against frozen V31/V25/V26/V28R bindings, with per-block evidence persistence, exact resume, a 12h cumulative resource budget, and terminal reconstruction via a frozen truth table.
- Candidate-only handoff artifacts after the run; no acceptance, qualification, or promotion semantics.

Out of scope:
- Any modification of the V31 fixed n=1024 QC packet, V26 allocation, V25/V26 empirical posterior, or V28R decoder.
- V31 rerun or completion; anything `n=2048`; new matrices/allocation/decoders; posterior retuning; seed search; result-based block selection; raw `.ttbin` access.
- Qualification/promotion statements in any V32 artifact.

## Definitions

- **Frozen bindings**: the 9 input bindings of `proposal.md §Frozen Input Bindings` (V31 n=1024 QC packet / validation blocks+frames / per-block baseline at `nbldpc_v31_20260820/run_01/`; V25 run_04 empirical channel; V26 run_02 F03/A02 allocation; V28R decoder interface; GF(32) field identity with `field_id=c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`; `m1=16`; source IDs `type2_1M_20260121_184040`, `type2_1p5M_20260121_183806`, `type2_2M_20260121_183657`).
- **block success** = `exact && tag && syndrome && !false_accept`.
- **arm pass** = every source ≥19/20 block successes (B0: 6/6 exact/tag/syndrome, 0 false accept). Development discriminator only — never a qualification threshold.
- **Run root** = `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/`.
- **Terminal set** = exactly: `bridge_binding_fail`, `finite_graph_decoder_mismatch`, `l1_sequential_propagation_limit`, `real_error_structure_mismatch`, `empirical_channel_model_mismatch`, `bridge_pass_ready_for_successor`, `bridge_inconclusive`, `resource_blocked`, `implementation_blocked`.

## Requirements (SHALL)

### Arms & Seeds

- **SHALL-A1** — The system SHALL execute exactly six arms with frozen sizes: B0 noiseless control 2 blocks/source × 3 sources = 6 total; B1 iid synthetic + oracle L1 20/source × 3 = 60; B2 Bob-only sequential on the identical B1 blocks = 60; B3 deterministic shuffled real-error surrogate 20/source × 3 = 60; B4 real retrospective oracle-L1 blocks 0–19/source × 3 = 60; B5 read-only import of the V31 n=1024 300-block baseline.
- **SHALL-A2** — The system SHALL use frozen seeds for B1/B2: 1M `320101–320120`; 1.5M `320201–320220`; 2M `320301–320320`. Seeds and block IDs SHALL NOT change during the change.
- **SHALL-A3** — B2 SHALL differ from B1 in exactly one respect: oracle L1 replaced by Bob-only sequential L1; block/seed/truth/channel sample/graph/posterior SHALL be identical to B1.
- **SHALL-A4** — B3 SHALL preserve each source block's error count/marginals under a deterministic permutation of EXACTLY the B4 block set (blocks 0–19 per source); the permutation rule and seed SHALL be fixed and recorded in `RUN_MANIFEST.json` BEFORE execution; permutation SHALL never be selected by results; truth MAY construct the fixture but SHALL NEVER be a decoder input.
- **SHALL-A5** — Every B1/B2/B4 block SHALL be marked `truth_used=true, truth_role=oracle_l1, operational=false, qualification=false`; B0 requires 6/6 exact, 6/6 tag, 6/6 syndrome, 0 false accept, and any B0 failure SHALL stop the run before scientific attribution.
- **SHALL-A6** — B5 SHALL import the V31 baseline strictly read-only: it SHALL NOT invoke the V31 decoder and SHALL NOT regenerate any result; import integrity (300 records, identity match vs canonical) SHALL be verified.

### Discriminator & Terminals

- **SHALL-D1** — The system SHALL apply the frozen development discriminator: arm pass = ≥19/20 block successes per source; block success = `exact && tag && syndrome && !false_accept`. It SHALL NOT represent this discriminator as a qualification threshold anywhere.
- **SHALL-D2** — The system SHALL classify exactly one terminal from the frozen 9-state set using the minimum decision logic (B0 fail → binding/blocked; B0✓+B1✗ → `finite_graph_decoder_mismatch`; B1✓+B2 sig. below → `l1_sequential_propagation_limit`; B1✓+B3✓+B4✗ → `real_error_structure_mismatch`; B1✓+B3✗+posterior anomaly → `empirical_channel_model_mismatch`; conflicts/insufficient evidence → `bridge_inconclusive`) extended by the complete truth table in `design.md §5`.
- **SHALL-D3** — Combinations not covered by the truth table SHALL map uniformly to `bridge_inconclusive`; no terminal SHALL be invented, renamed, or re-mapped after results are observed.

### Output Root & Collision

- **SHALL-O1** — All run evidence SHALL be written only under the unique run root (`.../nbldpc_v32_finite_de_bridge/run_01/`). If that path already exists, the system SHALL STOP with implementation/output collision; it SHALL NOT overwrite and SHALL NOT automatically create `run_02`.

### Resource Budget

- **SHALL-R1** — The system SHALL enforce a 12-hour cumulative wall-clock budget; cumulative elapsed time SHALL be persisted in `resource_ledger.json` and SHALL NOT be reset by resume.
- **SHALL-R2** — The system SHALL persist `resource_ledger.json`, `progress.json`, and `per_block.jsonl` under the run root and SHALL persist each completed block immediately upon completion.
- **SHALL-R3** — Budget exhaustion SHALL stop the run with terminal `resource_blocked`.

### Exact Resume

- **SHALL-X1** — Resume SHALL restore only the same `run_01`; completed blocks SHALL NOT be repeated; block identity SHALL be unique across the run.
- **SHALL-X2** — Resume SHALL require seed/input/code/config consistency with the interrupted run; cumulative wall-clock SHALL continue across resume; the resume reason SHALL be recorded in `resource_ledger.json`.
- **SHALL-X3** — Resume from a scientific failure terminal SHALL be forbidden; resume SHALL NOT modify arms, blocks, thresholds, or any frozen quantity; a duplicated block in `per_block.jsonl` SHALL be treated as evidence inconsistency and stop the run.

### Execution Order & Early Stop

- **SHALL-E1** — Execution SHALL follow the fixed order: binding verification → B5 read-only import → B0 → B1 → B2 → B3 → B4 → terminal reconstruction.
- **SHALL-E2** — Early stop SHALL be permitted ONLY for: binding failure; B0 failure; implementation exception; output collision; cumulative 12h exhaustion; canonical/input drift; truth-use violation. Skipping B2/B3/B4 because of bad B1 results, single-source early failure, intermediate trends, or time saving SHALL be forbidden.

### Truth-Use Marking

- **SHALL-T1** — Per-block records SHALL carry explicit truth-use flags (`truth_used`, `truth_role`, `operational`, `qualification`) as defined in SHALL-A5; a truth-use violation (truth leaking into B2/B3 decoder inputs) SHALL stop the run.

### Per-Block Metrics

- **SHALL-M1** — Every decoded block SHALL persist one JSONL line containing at least: `arm`; `source`; seed/block ID; graph/packet identity; posterior identity; truth-use flags; initial/final L1 errors; initial/final L2 errors; `exact`; `tag`; false accept; syndrome; unsatisfied checks; iterations; terminal decoder status; runtime; posterior NLL; entropy; truth-symbol rank; calibration bucket; residual syndrome/check statistics.
- **SHALL-M2** — Summaries SHALL stratify by arm and truth-role; synthetic (B1/B2), oracle-L1 diagnostic (B3/B4), and imported operational baseline (B5) SHALL NOT be blended into a single FER. Decoder failure statuses SHALL NOT be silently converted into success.

### Test Tiers

- **SHALL-V1** — Verification SHALL follow the frozen tiers: T0 structural (compile/import; GF(32)/field binding; QC packet identity; tiny noiseless B0; B1/B2 same-block identity; B3 deterministic permutation; B5 no decoder invocation; output collision refusal; no production execution from tests); T1 tamper (at minimum: seed drift; block ID drift; graph packet drift; posterior binding drift; B1/B2 block mismatch; truth leakage into B2/B3; duplicate block; resource meter reset; illegal resume; terminal tamper; source label tamper; partial JSONL; B5 re-executing decoder; output overwrite); T2 full fake B0–B5 with ≥1 fixture per major terminal, truth-use audit, exact resume, 12h resource simulation, independent terminal reconstruction; T3 read-only regression (V25 binding; V26 allocation; V28R decoder interface; V31 QC packet; V31 B5 import; canonical/frozen directories unmodified).
- **SHALL-V2** — All tests SHALL run in a fresh `workspace/<v32>/<uuid>/` root with `pytest -p no:cacheprovider --basetemp <root>`; legacy ACL temp directories SHALL NOT be touched; tests SHALL NEVER implicitly invoke production decoders/pipelines (fake runners passed explicitly).

### Autonomy Boundary

- **SHALL-B1** — Implementation agents MAY decide internal structure, fixtures, CLI details, JSON field layout (within SHALL-M1), progress display, exact-resume implementation, Windows writable basetemp, in-scope bug fixes, test split, and internal division of labor. They SHALL STOP and escalate before: modifying B0–B5; changing seeds/block IDs; changing the 19/20 discriminator; expanding samples; adding n=2048; extending 12h; new matrix/decoder; re-estimating posterior; automatic `run_02`; rerunning failed blocks; changing terminals from results; starting V33/NB-Polar; writing qualification/promotion; push; reading raw `.ttbin`; overwriting existing evidence.

### Candidate-Only Handoff

- **SHALL-H1** — At long-run end the operator SHALL produce candidate-only handoff artifacts (`workspace/nbldpc_v32_finite_de_bridge/OPERATOR_HANDOFF.md` and/or `operator_handoff.json`, `candidate_recount.json`, `candidate_terminal.json` under the evidence root), each marked `candidate_only=true, main_acceptance_pending=true, qualification=false, promotion=false`.
- **SHALL-H2** — After spec freeze, the implementation phase SHALL update only V32 `tasks.md`, test evidence, and candidate manifest; the formal run phase SHALL write only run-root evidence and operator logs; edits to `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`, final reports, archive, or promotion documents SHALL be forbidden during the run phase.

## Acceptance Mapping

| Area | Requirements | Verified by |
|---|---|---|
| Arms/seeds/truth markers | SHALL-A1..A6 | T0/T1/T2 fixtures + RUN_MANIFEST inspection |
| Discriminator/terminals | SHALL-D1..D3 | T2 terminal fixtures + independent reconstruction |
| Root/collision/resources/resume | SHALL-O1, R1..R3, X1..X3 | T1 tamper items + T2 resume/resource simulation |
| Order/early-stop | SHALL-E1..E2 | T2 fake run order assertions |
| Metrics/aggregation | SHALL-M1..M2 | T0 schema check + T2 summary stratification |
| Tests | SHALL-V1..V2 | pytest logs under workspace root |
| Autonomy/handoff/docs timing | SHALL-B1, H1..H2 | reviewer report + handoff artifact inspection |
