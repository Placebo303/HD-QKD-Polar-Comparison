# OpenSpec Tasks: formal-ir-v36-empirical-p-irregular-source-native-graph

## Phase Breakdown

- [x] **P0: Architecture & OpenSpec Specification Freeze**
  - Create proposal, design, tasks, and delta spec for V36.
  - Establish exact development seeds and stage progression gates.

- [x] **P1: Core Algorithm Module Implementation**
  - Implement `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v36_empirical_graph.py`.
  - Implement Stage A0 iteration budget diagnostic.
  - Implement candidate degree distribution grid generator ($\bar{d}_v \in [2.15, 2.55]$).
  - Implement empirical-P MC-DE adapter with coarse (1000) and confirmation (4000) screening.
  - Implement source-native PEG graph construction ($184\times 1024, 190\times 1024, 192\times 1024$).
  - Implement graph topology audits (rank, 0 deg-2 cycles, 4-cycles, degree histograms).
  - Implement moderate-degree incremental parity check extension.

- [x] **P2: CLI Runner Implementation**
  - Implement `comparison_bench/src/comparison_bench/cli/run_nonbinary_v36_empirical_graph.py`.
  - Orchestrate A0 -> A1 -> A2 -> A3 [-> A4 conditional].
  - Emit all required CSV/JSON structured artifacts and generate `docs/nbldpc-v36-empirical-graph-development.md`.

- [x] **P3: Test Suite Implementation (T0–T9)**
  - Implement `comparison_bench/tests/test_nonbinary_v36_empirical_graph.py`.
  - Cover T0 (empirical channel), T1 (degree algebra), T2 (DE golden case), T3 (source-native graph), T4 (actual-H structure), T5 (decoder), T6 (noisy real path), T7 (incremental), T8 (output identity), T9 (report regeneration).
  - 11/11 tests passed cleanly.

- [x] **P4: Test Suite Verification & Exploratory Execution**
  - Verified compilation: `python -B -m py_compile ...` (PASSED).
  - Verified unit tests: `python -B -m pytest -q -p no:cacheprovider ...` (11/11 PASSED).
  - Executed the V36 pipeline on development blocks and retained its outputs.
  - Post-run review found that A1 did not satisfy the frozen same-setting/per-source DE comparison and A2 violated the zero degree-2-cycle and zero 4-cycle requirements. A3 data are retained as exploratory evidence, not as a gate-compliant downstream run.

- [x] **P5: Scientific Synthesis & Terminal Attribution**
  - Recomputed the paired finite-block statistics and corrected the generated report in `docs/nbldpc-v36-empirical-graph-development.md`.
  - Record the bounded positive signal (`174.80` to `157.07` mean residual symbols; 10/15 paired improvements) separately from acceptance.
  - Confirm terminal state `NO_FINITE_GRAPH_ADVANCE`; do not claim an accepted DE shortlist, structural pass, MET necessity, or general FER result.
