# OpenSpec Design: formal-ir-v36-empirical-p-irregular-source-native-graph

## 1. Pipeline Architecture

```
                  +-------------------------------------------------------+
                  | Stage A0: Decoder Iteration Diagnostic (30 vs 60 iters)|
                  | 9 Blocks (3 sources x 3 seeds), Baseline V31 graph    |
                  +---------------------------+---------------------------+
                                              | Unified max_iter chosen
                                              v
                  +-------------------------------------------------------+
                  | Stage A1: GF(32) Empirical-P Irregular Ensemble DE   |
                  | - Candidate grid: lambda_d in {2,3,4,5}, dbar in [2.15, 2.55] |
                  | - Coarse screen (1000 samples, 30 iters, 1 seed)      |
                  | - Confirmation (4000 samples, 60 iters, 3 seeds)      |
                  | - Shortlist selection (top <= 2 candidates)           |
                  +---------------------------+---------------------------+
                                              | DE_SHORTLIST_READY?
                                              v
                  +-------------------------------------------------------+
                  | Stage A2: Source-Native Finite PEG Graph Construction  |
                  | - Native 184x1024 (1M), 190x1024 (1.5M), 192x1024 (2M)|
                  | - Fixed graph & coefficient seeds, full GF(32) rank   |
                  | - Girth, degree-2 cycles, degree histograms audit    |
                  +---------------------------+---------------------------+
                                              |
                                              v
                  +-------------------------------------------------------+
                  | Stage A3: Finite Paired Development Screen            |
                  | - 15 Blocks (3 sources x 5 seeds 360xxx)              |
                  | - V31 Baseline vs C1 (and C2)                         |
                  | - Advance: Exact (>=1/5 all src) or Residual (-15% med)|
                  +---------------------------+---------------------------+
                                              | FINITE_GRAPH_ADVANCE?
                                              v
                  +-------------------------------------------------------+
                  | Stage A4: Moderate-Degree Incremental Syndrome        |
                  | - S0 (+0), S1 (+8), S2 (+16), S3 (+32) checks (deg<=16)|
                  | - Clean Cold-Start, per-stage logging                 |
                  | - Ready gate: >=3/5 exact per source, 0 false accept  |
                  +-------------------------------------------------------+
```

## 2. Stage Details

### A0: Decoder Iteration Diagnostic
- Evaluate true V31 baseline with row-layered schedule ($\alpha=1.0$) at `max_iter=30` and `max_iter=60` on 9 blocks (seeds `360101..360103`, `360201..360203`, `360301..360303`).
- If 60 iterations improves paired median residual by $\ge 5\%$ across all three sources, select 60; otherwise 30.
- Unified budget applies to all subsequent stages.

### A1: Empirical-P DE Candidate Screening
- Edge-perspective degree distribution $\lambda(x) = \sum_{d=2}^5 \lambda_d x^{d-1}$ on $0.05$ grid.
- Average degree $\bar{d}_v = 1 / \sum (\lambda_d / d) \in [2.15, 2.55]$.
- For each source, exact code rate $R$ determines concentrated check distribution $\rho$ via $\sum_j \rho_j / j = (1 - R) \sum_d \lambda_d / d$.
- Coarse screening ($N_{\text{samples}}=1000, \text{max\_iter}=30$): filter top 12 candidates that do not degrade relative to $d_v=2$ regular baseline.
- Confirmation screening ($N_{\text{samples}}=4000, \text{max\_iter}=60$): select top $\le 3$ candidates by:
  1. Convergence criterion on all sources;
  2. Final belief entropy on worst source;
  3. Symbol-error proxy on worst source;
  4. Seed stability;
  5. Lower max check degree;
  6. Canonical dictionary order tie-break.

### A2: Source-Native Finite Graph Construction
- For each shortlist candidate and each source, construct native parity check matrix $H \in \text{GF}(32)^{m_2 \times 1024}$ using PEG (`peg_construct`).
- No truncation from a master matrix.
- Ensure full row rank ($m_2$). If first coefficient seed is rank-deficient, try pre-frozen second seed.
- Verify 0 degree-2 cycles, Tanner girth $\ge 6$ (0 4-cycles), no isolated nodes, realized rate exact.

### A3: Finite Paired Development Screen
- 15 empirical blocks from V25 joint counts with seeds `360101..360105` (1M), `360201..360205` (1.5M), `360301..360305` (2M).
- Compare V31 baseline against Candidate C1 (and C2).
- Advance gate:
  - Exact path: $\ge 1/5$ exact recovery on all 3 sources; OR
  - Residual path: paired median residual $\ge 15\%$ lower than baseline on all 3 sources, $\ge 12/15$ blocks improved, no block $>10$ errors worse, 0 false accept.

### A4: Moderate-Degree Incremental Syndrome
- S0 (+0), S1 (+8), S2 (+16), S3 (+32) check rows added via PEG extension with check degree $10\text{--}14$ (max 16).
- Independent cold-start decoding per stage.
