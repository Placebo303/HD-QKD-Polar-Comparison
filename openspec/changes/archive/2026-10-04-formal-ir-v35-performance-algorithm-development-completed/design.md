# OpenSpec Design: formal-ir-v35-performance-algorithm-development

## 1. System Architecture & Progression Flow

```
              +----------------------------------------------------+
              |          Input Data: V25 Empirical Channel         |
              |   15 Paired Blocks (3 Sources x 5 Seeds 350xxx)    |
              +-------------------------+--------------------------+
                                        |
                                        v
              +----------------------------------------------------+
              | Stage A1: Decoder Schedules on Baseline GF(32) H   |
              | (Flooding, Row-Layered, Damped Row-Layered a=0.5)  |
              +-------------------------+--------------------------+
                                        |
                                        v
              +----------------------------------------------------+
              | Stage A2: Empirical-P Protograph & Quasi-Cyclic    |
              | (Variable deg 2-5, Avg deg 2.2-3.2, Girth >= 6)    |
              +-------------------------+--------------------------+
                                        |
                                        v
              +----------------------------------------------------+
              | Stage A3: Rate-Adaptive Incremental Syndrome       |
              | (S0: +0b, S1: +40b, S2: +80b, S3: +160b)           |
              | (Warm-started state transfer & early stop)         |
              +-------------------------+--------------------------+
                                        |
                         A3 >= 3/5 exact on all 3 sources?
                               /                  \
                             YES                   NO
                             /                       \
                            v                         v
        +----------------------------+     +-------------------------------+
        | Terminal Status:           |     | Stage A4: Binary MLC Fallback |
        | NB_CANDIDATE_DEVELOPMENT_  |     | (10-bit Gray MSD + ldpc BP)   |
        | READY                      |     +---------------+---------------+
        +----------------------------+                     |
                                            A4 >= 3/5 exact on all 3 sources?
                                                  /                 \
                                                YES                  NO
                                                /                      \
                                               v                        v
                           +----------------------------+     +-------------------+
                           | Terminal Status:           |     | Terminal Status:  |
                           | BINARY_MLC_CANDIDATE_      |     | NO_CANDIDATE_     |
                           | DEVELOPMENT_READY          |     | SUCCESS           |
                           +----------------------------+     +-------------------+
```

---

## 2. Stage A1: Decoder Schedule Exploration

1. **Flooding FFT-QSPA**: Synchronous two-phase message passing. In each iteration, all variable-to-check messages are computed in parallel, followed by all check-to-variable updates via 32-point FWHT.
2. **Row-Layered FFT-QSPA**: Sequential check row processing. Check nodes $i \in \{0, \dots, M-1\}$ are updated sequentially. Each check reads current extrinsic messages from variable total beliefs, computes updated check-to-variable messages, and immediately updates global variable beliefs $\Gamma_j \leftarrow \Gamma_j - u_{i \to j}^{\text{old}} + u_{i \to j}^{\text{new}}$.
3. **Damped Row-Layered FFT-QSPA ($\alpha = 0.5$)**: Check-to-variable messages are smoothed with prior messages in probability domain:
   $$P_{i \to j}^{\text{damped}} = (1 - \alpha) P_{i \to j}^{\text{old}} + \alpha P_{i \to j}^{\text{new}}$$
   converted back to log-domain with minimum floor $\log(10^{-15})$. Ensures strictly non-negative, finite, normalized messages and prevents destructive oscillations on short cycles.

---

## 3. Stage A2: Empirical-P Protograph & Deterministic Lifting

1. **Protograph Base Matrix ($B \in \mathbb{Z}_{\ge 0}^{M_p \times N_p}$)**:
   - Size: $M_p = 6, N_p = 32 \implies R_{\text{design}} = 1 - 6/32 = 0.8125$.
   - Variable node degree distribution: $d_v \in \{2, 3, 4, 5\}$ with average degree $\bar{d}_v \in [2.2, 3.2]$.
   - Max degree-2 edge fraction $\lambda_2 \le 0.35$; zero degree-1 variable nodes ($\lambda_1 = 0$).
   - Degree-2 variable nodes form no cycles within the protograph (constrained chains of length $\le 2$).
2. **Quasi-Cyclic Deterministic Lifting ($Z = 32 \implies N = 1024, M = 192$)**:
   - Shift matrix $S \in [0, 32)^{M_p \times N_p}$ assigned deterministically to cancel 4-cycles.
   - For every edge $(i, j)$ where $B_{ij} > 0$, the circulant permutation block has shift $S_{ij}$.
   - Resulting Tanner graph achieves girth $\ge 6$ (zero 4-cycles and zero parallel edges).
3. **GF(32) Projective Edge Labeling**:
   - Non-zero field coefficients $c_{ij, k} \in \text{GF}(32)^*$ assigned to ensure full GF(32) rank ($M = 192$) and prevent algebraic cycle degeneracies.

---

## 4. Stage A3: Rate-Adaptive Incremental Parity-Check Hierarchy

1. **Nested Matrix Hierarchy**:
   - Mother matrix $H_{\text{mother}} \in \text{GF}(32)^{(192 + 32) \times 1024}$ partitioned into nested submatrices:
     - $S0$: Base $M = 192$ rows ($+0$ extra checks / $+0$ bits).
     - $S1$: $+8$ extra checks ($M = 200$, $+40$ syndrome bits).
     - $S2$: $+16$ extra checks ($M = 208$, $+80$ syndrome bits).
     - $S3$: $+32$ extra checks ($M = 224$, $+160$ syndrome bits).
2. **Warm-Started Decoder State**:
   - When transitioning from $S_k \to S_{k+1}$, the converged variable belief vector $\Gamma_j$ from $S_k$ is transferred directly as the initial prior for $S_{k+1}$.
   - Checks $1 \dots M_k$ retain their active message state; new check rows $M_k + 1 \dots M_{k+1}$ are initialized with zero check-to-variable messages.
3. **Early Stop Rule**:
   - Decoding terminates immediately at stage $S_k$ if `exact_l2 == True` and `syndrome_ok == True` and `tag_ok == True`.

---

## 5. Stage A4: Binary Multilevel Coding (MLC) Fallback

1. **10-Bit Plane Gray Decomposition**:
   - Each 1024-bin symbol $A \in [0, 1024)$ is mapped to a 10-bit vector $(b_0, \dots, b_9)$ using MSB-first Gray code:
     $$g = A \oplus (A \gg 1), \quad b_i = (g \gg (9 - i)) \& 1$$
2. **Empirical Conditional LLR Evaluation**:
   - For plane $i \in \{0, \dots, 9\}$, given Bob's symbol $Y$ and decoded prefix bits $(\hat{b}_0, \dots, \hat{b}_{i-1})$:
     $$LLR_{i, k} = \ln \left( \frac{\sum_{a \in \mathcal{A}(\hat{u}_{<i}), b_i(a)=0} P(A=a \mid B=y_k)}{\sum_{a \in \mathcal{A}(\hat{u}_{<i}), b_i(a)=1} P(A=a \mid B=y_k)} \right)$$
3. **Sequential Multistage Decoding (MSD)**:
   - Planes $i = 0 \to 9$ decoded sequentially using `ldpc.BpOsdDecoder` with error channel probabilities derived from empirical conditional LLRs.
   - Parity-check row allocations $m_0..m_9$ matched to conditional entropies $H(b_i \mid Y, b_{<i})$.
   - Explicit tracking of error propagation across decoding stages.

---

## 6. Output Schemas & Attribution

- **Per-Block CSV Record** (`v35_algorithm_development_blocks.csv`, 17 columns):
  `source,seed,method,graph_id,decoder_schedule,redundancy_stage,exact_l2,syndrome_ok,tag_ok,false_accept,errors_initial,errors_final,iterations,runtime_s,syndrome_leakage_bits,cumulative_leakage_bits,status`
- **JSON Summary** (`v35_algorithm_development_summary.json`): Contains overall terminal status, per-stage success breakdown, false accept count, and wallclock runtimes.
- **Scientific Synthesis Report** (`docs/v35-algorithm-development-report.md`): Full comparative analysis of performance drivers.
