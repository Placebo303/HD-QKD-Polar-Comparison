# NB-LDPC GF32 local cycle/source-overlap diagnostic — RESULT

Batch `202e39a1-bf55-436a-ad3f-cad2d539e683` is closed and main-accepted with comments as a decoder-free inventory on the six fixed graphs, seeds 2026093901–2026093906, and simple cycles with `ell=2..6`. The terminal status is `OVERLAP_COMPLETE`; all 3026 input rows were processed. The accepted census matrices were read as frozen inputs; this batch reconstructed no graphs and called no decoder.

For each unit-cycle orbit, the frozen diagnostic sums the 31 scalar shifted-source Bhattacharyya products, `W(c)=sum_{lambda=1..31} product_v B(GFmul(lambda,c[v]))`, with `B(z)=sum_e sqrt(p(e)p(e XOR z))`. The GF(32) PMF and orbit convention are frozen in `PREREG_AND_AUTH.md`. This is a dimensionless local source-overlap diagnostic, not an error probability, FER, decoder result, global-code bound, or route claim.

| Matrix | Unique unit-cycle orbits | Positive-overlap orbits | Zero-overlap orbits | Nonunit cycle rows (`W=null`) | Sum of `W` over unique orbits |
|---|---:|---:|---:|---:|---:|
| Control | 105 | 36 | 69 | 2921 | 0.028521162905751574 |
| Accepted edge candidate | 121 | 76 | 45 | 2905 | 0.035753425835366386 |

A nonunit cycle has no unit codeword orbit and is represented by null `W`, not a measured zero. Unit orbits with zero source overlap are counted separately. The machine summary and CSV retain the per-graph/per-`ell` records; the totals above are descriptive for this frozen inventory and are not a cross-batch ranking.

The independent `faithful_scope` batch-end review passed P1–P7; the reviewer was not the operator. It checked all 3026 rows, the 226 arm-specific unit witnesses and the stored GF(32) overlap calculations. Maximum absolute recomputation differences were `1.73e-18` for `W` and `5.55e-17` for `B(z)`; normalized unit-orbit keys had no duplicates. The main acceptance is limited to this finite synthetic iid marginal-proxy diagnostic.

The batch made zero decoder calls, zero graph constructions and used zero sampled frames. Recorded wall time was `0.412950788 s`. The maximum RSS observation was `101978112 B` across five process high-water-RSS checkpoints; this is sampled checkpoint RSS, not an unobserved absolute peak. The run completed without a resource STOP. The batch grant is consumed; this record authorizes no rerun, range extension, additional graph, decoder run or route decision.

Do not pool or rank batches, or infer conditional-channel performance, causal mediation, FER, `f_eff`, SKR, throughput, qualification, publication or route closure. The machine artifacts are `workspace/gf32_cycle_overlap_202e39a1/{manifest.json,source_overlap.csv,summary.json,EXPLORATION_LOG.md}`. No commit, push, merge or archive was performed.
