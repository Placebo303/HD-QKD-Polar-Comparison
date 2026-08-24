# V36 Empirical-P Irregular LDPC & Source-Native Graph Development Report

**Date**: 2026-08-24  
**Milestone**: V36 Empirical-P Irregular LDPC Development  
**Domain**: Formal Information Reconciliation (IR) / Nonbinary LDPC  
**Output Root**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v36_empirical_graph_development/run_01/`  
**Terminal Scientific Status**: **`NO_FINITE_GRAPH_ADVANCE`**  

---

## 1. Executive Summary & Progression Results

### Stage A0 (Decoder Iteration Diagnostic)
- **Evaluated**: True V31 baseline at `max_iter=30` vs `max_iter=60` across 9 development blocks (seeds `360101..360303`).
- **Selected Budget**: `max_iter = 30`.
- **Median Relative Improvements**: {'1M': 0.0, '1p5M': 0.0, '2M': 0.0}.

### Stage A1 (GF(32) Empirical-P Irregular Ensemble DE Screening)
- **Candidate Grid**: 195 variable degree distributions ($ar{d}_v \in [2.15, 2.55]$, $d_c \le 16$).
- **Coarse Passed**: 1 non-degraded candidates.
- **Top Shortlisted Candidate**: `lam_d2_0.85_d3_0.00_d4_0.15_d5_0.00`.
- **Persisted runner status**: `DE_SHORTLIST_READY`.
- **Post-run acceptance**: `A1_DE_SELECTION_NOT_ACCEPTED`. The confirmation did not implement the frozen same-setting, per-source improvement comparison; near-zero saturated entropy is not evidence of a meaningful 10% advantage.

### Stage A2 (Source-Native Finite Graph Construction)
- **Native Construction**: Separate PEG parity-check matrices generated for 1M ($184\times 1024$), 1.5M ($190\times 1024$), 2M ($192\times 1024$).
- **Submatrix Truncation**: Strictly zero truncation used.
- **Matrix Audits**: Full GF(32) row rank was realized, but the three graphs contained 3002/2721/2288 4-cycles and degree-2 cycle ranks 801/785/779.
- **Post-run acceptance**: `A2_STRUCTURAL_GATE_FAILED`; the frozen zero-cycle requirements were not met. A3 is retained as exploratory downstream data.

### Stage A3 (Finite Paired Development Screen)
- **Evaluated**: 15 paired empirical blocks comparing V31 baseline vs DE shortlist candidate.
- **V31 Baseline Residual Errors**: Mean = $174.80 \pm 12.38$, Median = $177.0$, Exact = 0/15.
- **Candidate Residual Errors**: Mean = $157.07 \pm 25.05$, Median = $166.0$, Exact = 0/15.
- **Stage A3 Terminal**: `NO_FINITE_GRAPH_ADVANCE`.

### Stage A4 (Moderate-Degree Incremental Syndrome)
- **Executed**: False.
- **Stage A4 Terminal**: `SKIPPED`.

---

## 2. Verification bookkeeping boundary

- Across all evaluated records (30 total records), recorded `false_accept` is **0**. This oracle-L1 development diagnostic is not an independent cryptographic-integrity or end-to-end security result.

---

## 3. Pre-Registered Claim Ledger

| Claim | Evidence Type | Direct Artifact / Field | Permitted Wording |
|---|---|---|---|
| **Candidate DE Comparison** | Protocol-incomplete computation | `de_coarse_results.csv`, `de_confirmation_results.csv` | “候选由实现筛出，但未通过冻结的 A1 接受语义” |
| **Finite Graph Performance** | Exploratory paired finite data | `finite_block_results.csv` | “15 块中均值残差 174.80 降至 157.07，10/15 改善，exact 0/15；未晋级” |
| **Trapping Set Causality** | None | — | **禁止作为定论** |
| **Waterfall Threshold Claim** | None | — | **禁止作为定论** |
| **General FER Claim** | None | — | **禁止作为定论** |

---

## 4. Official Terminal Scientific Status

`POSITIVE_EXPLORATORY_RESIDUAL_SIGNAL / A1_DE_SELECTION_NOT_ACCEPTED /
A2_STRUCTURAL_GATE_FAILED / NO_FINITE_GRAPH_ADVANCE`
