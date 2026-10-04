# GF(32) fixed within-degree row-order EXPLORE result

Batch UUID: `44c394bc-e3dd-4e6b-9d4a-8a5b0dd5cdfc`  
Track: `EXPLORE`  
Machine root: `workspace/gf32_roworder_44c394bc/`

One authorized attempt completed 192 paired frames / 384 BP calls on six admitted GF(32), polynomial-37 deep-H0D graphs. Both arms used the same admitted deep-H0D coefficient matrix and sampled truth/prior: control decoded that matrix in natural row order, while candidate decoded that matrix in the frozen within-check-degree permutation `H[pi]` and applied the same `pi` to the syndrome. Each call used `max_iter=90`, `damping_alpha=1`, `warm_beliefs=None`, and `field=None`. No OSD/MRB rescue or real input was used.

The batch is `COMPLETE` and classified `NO_SUFFICIENT_SIGNAL`. Control/candidate exact-and-syndrome successes were 152/148 (`Delta=-4`), with positive graphs 0/6. Per-graph counts for seeds 2026093901–2026093906 were 22/22, 27/27, 26/25, 25/24, 27/27, and 25/23. Paired both/control-only/candidate-only/neither counts were 148/4/0/40. Raw syndrome failures were 40/44 and syndrome-valid wrong outcomes were 0. Among the 40 control failures, candidate exact/wrong/still-failed outcomes were 0/0/40. The control count met the frozen range [39,153]; `Delta>=12` and positive graphs >=4/6 were not met.

Total iterations were 4934/5001. Per-arm decoder-wall sums were 29.421401827/29.809025610 s; full batch wall time was 110.419199688 s. Sampled process RSS peaked at 103575552 B over 1370 samples (not a continuous peak). The diagnostics NPZ is 47321 B with 240624 B uncompressed payload. The run disclosed 99840 syndrome bits with tag=0; verification is `NOT_IMPLEMENTED` and undetected errors are `NOT_MEASURED`.

The five retained artifacts are `manifest.json`, `frame_records.csv` (384 call rows), `summary.json`, `diagnostics.npz`, and `EXPLORATION_LOG.md` under the machine root. There were 384 BP calls, 0 OSD calls, and 0 integrity/resource/authorization violations; no STOP occurred.

This is a bounded finite synthetic iid marginal-shape screen only. It does not establish a route, significance, causal effect, cross-batch ranking, real-channel performance, FER, `f_eff`, SKR, throughput, security, qualification, or publication result. Zero syndrome-valid wrong rows are not a verification or undetected-error bound. The one-shot grant is consumed; no rerun, resume, or additional permutation is authorized.
