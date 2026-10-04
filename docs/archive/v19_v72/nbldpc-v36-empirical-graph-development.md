# V36 empirical-P irregular LDPC/source-native graph development report

**Date**: 2026-08-24  
**Output**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v36_empirical_graph_development/run_01/`

Corrected post-run status:

- **`POSITIVE_EXPLORATORY_RESIDUAL_SIGNAL`**
- **`A1_DE_SELECTION_NOT_ACCEPTED`**
- **`A2_STRUCTURAL_GATE_FAILED`**
- **`NO_FINITE_GRAPH_ADVANCE`**

The code and compact run artifacts are retained as research evidence. This run
is not an accepted V36 candidate and does not authorize a successor or formal
execution.

## A0: iteration-budget diagnostic

The true V31 baseline was evaluated at 30 and 60 iterations on nine
development blocks. Final residuals were identical on all nine and runtime
approximately doubled, so the pipeline selected 30 iterations. This supports
only the bounded statement that 60 iterations did not improve these blocks; it
does not prove universal decoder steady state.

## A1: empirical-P DE screening

- Candidate grid: 195 edge-perspective degree distributions with
  $\bar{d}_v\in[2.15,2.55]$ and maximum check degree at most 16.
- Persisted selection:
  `lam_d2_0.85_d3_0.00_d4_0.15_d5_0.00`.
- The empirical-P sampler and MC-DE calls are real, not a facade.

The persisted `DE_SHORTLIST_READY` status is nevertheless **not accepted**:

1. The frozen OpenSpec required at least 10% improvement on every source.
   Implementation compared one aggregate candidate worst entropy against an
   aggregate coarse-baseline worst entropy and did not enforce that condition.
2. Candidate confirmation used `N=4000`, 60 iterations and three seeds, while
   the baseline was not rerun under the same confirmation settings.
3. Final entropy saturated near zero (`~3e-296` for two baseline sources and
   the selected candidate), so final entropy was not a useful discriminator.

The artifacts therefore support only: “the current DE program selected this
distribution.” They do not support empirical-P DE superiority.

## A2: source-native PEG graph construction

Separate $184\times1024$, $190\times1024$, and $192\times1024$ matrices were
constructed without prefix truncation. All were full GF(32) row rank and had
maximum check degree 12--13. They failed the frozen structural gate:

| Source | 4-cycles | Degree-2 cycle rank |
|---|---:|---:|
| 1M | 3002 | 801 |
| 1p5M | 2721 | 785 |
| 2M | 2288 | 779 |

The implementation logged these counts but did not use them as elimination
conditions, and the focused tests checked their types rather than the required
zero values. Under the frozen OpenSpec, A2 should have stopped before A3.

The selected edge distribution has $\lambda_2=0.85,\lambda_4=0.15$, which is
about 91.9% degree-2 variables in node view (roughly 941 of 1024). A degree-2
subgraph with that many edges over only 184--192 check nodes cannot be a
forest. Retaining this distribution while requiring zero degree-2 cycles is
therefore a design contradiction, not something ordinary PEG or MET can simply
remove.

## A3: paired finite development screen

Fifteen oracle-L1 development blocks compared V31 baseline with the selected
source-native graph:

| Source | Baseline mean/median | Candidate mean/median | Improved/worse | Mean paired delta |
|---|---:|---:|---:|---:|
| 1M | 170.8 / 171 | 164.8 / 166 | 2 / 3 | -6.0 |
| 1p5M | 175.8 / 178 | 159.2 / 166 | 4 / 1 | -16.6 |
| 2M | 177.8 / 183 | 147.2 / 159 | 4 / 1 | -30.6 |
| Overall | 174.80 / 177 | 157.07 / 166 | 10 / 5 | -17.73 |

Exact recovery was 0/15 for both methods. Per-source marginal-median drops
were 2.92%, 6.74%, and 13.11%, all below 15%; only 10/15 blocks improved and
two blocks worsened by more than 10 errors. Thus `NO_FINITE_GRAPH_ADVANCE` is
consistent with the recorded A3 data.

The aggregate residual decrease is not created by one block, but it is
heterogeneous: 1M is unstable while 1p5M/2M provide the stronger signal. Since
A2 failed, A3 is retained only as a useful exploratory observation.

## Verification-tag and end-to-end boundary

The records contain `false_accept == 0`, but V36 sets `tag_ok=False` whenever
the estimate is not exact. This is not an independent false-accept experiment
and must not be presented as cryptographic-integrity evidence.

The finite screen conditions the L2 posterior on the true Alice `x1`. It is an
oracle-L1 L2 graph diagnostic, not Bob-only end-to-end reconciliation.

## Claim ledger

| Claim | Evidence | Permitted wording |
|---|---|---|
| DE program selected the distribution | DE code and CSV/JSON | Allowed, with gate limitation |
| Residual change on 15 development blocks | `finite_block_results.csv` | Allowed with per-source spread and 0 exact |
| Full-rank source-native graphs | `finite_graph_metrics.csv` and construction code | Allowed |
| Graph passed frozen structure gate | Contradicted by cycle counts | Forbidden |
| Empirical-P DE superiority | Confirmation/gate invalid | Forbidden |
| Trapping-set causality or waterfall threshold | No causal ablation | Forbidden |
| General FER or end-to-end improvement | Development-only oracle-L1 screen | Forbidden |
| MET is necessary or sufficient | MET not tested | Forbidden |

## Next scientific decision

Run a small corrected DE/finite-graph A/B before considering a full MET route:

1. rerun baseline and candidates under identical per-source confirmation
   settings and retain iteration trajectories;
2. rank with a non-saturated metric such as early-iteration entropy,
   trajectory area, or iterations to threshold;
3. either constrain node-view degree-2 mass to a cycle-feasible range or
   replace the impossible zero-cycle requirement with a justified finite-aware
   penalty;
4. compare only a baseline, the current exploratory positive control, and one
   corrected structurally admissible candidate on development data.

