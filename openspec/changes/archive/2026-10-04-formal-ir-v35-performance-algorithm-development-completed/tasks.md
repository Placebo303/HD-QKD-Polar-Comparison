# OpenSpec Tasks: formal-ir-v35-performance-algorithm-development (V35R1 Corrected)

## Phase Breakdown

- [x] **P0: Architecture & OpenSpec Specification Freeze**
  - Create proposal, design, tasks, and delta spec.
  - V35R1 correction: enforce baseline $d_v=2$ matrix loading, hand-designed mixed-degree protograph isolation, and cold-start incremental hierarchy.

- [x] **P1: Core Algorithm Module Implementation**
  - Update `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`.
  - Include `load_v31_qc_baseline_matrices` for true V31 $d_v=2$ matrix extraction.
  - Include `build_hand_designed_mixed_degree_protograph` with zero degree-2 cycles.
  - Include `check_protograph_degree2_cycles` verification function.
  - Include deterministic lifting ensuring girth $\ge 6$ and full GF(32) row rank (192 and 224).
  - Include `decode_v35_incremental_stage_a3` with clean cold-start decoding across S0..S3.

- [x] **P2: CLI Runner Implementation**
  - Update `comparison_bench/src/comparison_bench/cli/run_v35_algorithm_development.py`.
  - Support automatic progression (A1 -> A2 -> A3) on true baseline and isolated protograph.
  - Output exact 17-column CSV, JSON summary, and run manifest.
  - Automatically generate synthesis report directly from CSV execution dataset.

- [x] **P3: Test Suite T1–T5 Implementation**
  - Update `comparison_bench/tests/test_v35_algorithm_development.py`.
  - Cover T1 (Matrix identity isolation & numerical correctness), T2 (0 degree-2 cycles, girth $\ge 6$, full rank), T3 (Nested hierarchy & cold-start), T4 (MLC chain rule), T5 (Seed disjointness & non-destructive boundary).
  - Passed 25/25 unit & integration tests.

- [x] **P4: Test Suite Verification & A1--A3 Development Execution**
  - Run compilation check: `python -B -m py_compile ...` (PASSED).
  - Run test suite: `python -B -m pytest -q -p no:cacheprovider ...` (25/25 PASSED).
  - Run CLI on 15 development blocks to `run_02`.
  - Post-run review found that A4 was required after A3 failed but was not executed; retain `run_02` as partial development evidence only.

- [x] **P5: Corrected Scientific Synthesis & Terminal Attribution**
  - Recompute the A1--A3 results from the retained CSV and document the missing A4 stage.
  - Record `V35R1_A1_A3_RUN_COMPLETE`, `PROTOCOL_PARTIAL_A4_NOT_EXECUTED`, `NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION`, and `SCIENTIFIC_PROMOTION_NOT_GRANTED` in `docs/v35-algorithm-development-report.md`.
  - Do not use the broader `NO_CANDIDATE_SUCCESS` claim for this partial protocol.
