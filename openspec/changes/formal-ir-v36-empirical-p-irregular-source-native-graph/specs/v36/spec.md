# OpenSpec Delta Specification: formal-ir-v36-empirical-p-irregular-source-native-graph

## 1. Specification Requirements

### REQ-V36-01: Decoder Iteration Diagnostic (Stage A0)
- SHALL evaluate the true V31 baseline on 9 development blocks (1M: `360101..360103`, 1p5M: `360201..360203`, 2M: `360301..360303`).
- SHALL test `max_iter=30` versus `max_iter=60` with row-layered FFT-QSPA ($\alpha=1.0$).
- SHALL select 60 iterations if paired median residual improves by $\ge 5\%$ across all three sources; otherwise 30.
- SHALL apply the selected budget uniformly across all subsequent finite-graph decoding evaluations.

### REQ-V36-02: Empirical-P DE Candidate Screening (Stage A1)
- SHALL generate edge-perspective candidate distributions $\lambda(x) = \sum_{d=2}^5 \lambda_d x^{d-1}$ on a 0.05 step grid satisfying $\lambda_1 = 0$, $\sum \lambda_d = 1$, and $\bar{d}_v \in [2.15, 2.55]$.
- SHALL compute exact concentrated check distribution $\rho$ for each source from exact code rate ($1M: 0.8203125, 1p5M: 0.814453125, 2M: 0.8125$).
- SHALL enforce check degrees $\le 16$.
- SHALL execute coarse screening ($N=1000, \text{iter}=30$) retaining up to 12 candidates that do not degrade relative to $d_v=2$ regular baseline.
- SHALL execute confirmation screening ($N=4000, \text{iter}=60$) selecting top $\le 2$ shortlist candidates.
- SHALL declare `DE_SHORTLIST_READY` only if at least one candidate improves by $\ge 10\%$ over baseline on all sources; otherwise declare `NO_DE_ADVANCE`.

### REQ-V36-03: Source-Native Finite Graph Construction (Stage A2)
- SHALL independently construct $H_{1M} (184 \times 1024)$, $H_{1p5M} (190 \times 1024)$, $H_{2M} (192 \times 1024)$ via PEG. Submatrix slicing or truncation is strictly prohibited.
- SHALL verify full $\text{GF}(32)$ row rank equal to $m_2$ for each source.
- SHALL verify zero degree-2 cycles, zero 4-cycles (girth $\ge 6$), zero isolated nodes, and max check degree $\le 16$.

### REQ-V36-04: Finite Paired Development Screen (Stage A3)
- SHALL evaluate 15 paired blocks (seeds `360101..360105`, `360201..360205`, `360301..360305`) comparing V31 baseline against shortlisted candidates under identical blocks, posteriors, and decoder parameters.
- SHALL declare `FINITE_GRAPH_ADVANCE` if either:
  - Exact Path: $\ge 1/5$ exact recovery per source; OR
  - Residual Path: paired median residual drop $\ge 15\%$ on all three sources, $\ge 12/15$ blocks improved, no block $>10$ errors worse, and 0 false accepts.
- Otherwise SHALL declare `NO_FINITE_GRAPH_ADVANCE` and stop.

### REQ-V36-05: Moderate-Degree Incremental Syndrome (Stage A4)
- SHALL execute only if Stage A3 achieves `FINITE_GRAPH_ADVANCE`.
- SHALL construct nested check rows: S0 (+0), S1 (+8), S2 (+16), S3 (+32) with check degree $10\text{--}14$ (max 16).
- SHALL decode using independent cold-starts and log all 4 stages per block.
- SHALL declare `NB_DEVELOPMENT_CANDIDATE_FOUND` if $\ge 3/5$ exact recovery per source with 0 false accepts.
