# GF32 BP iteration-cap EXPLORE result

Batch UUID: `eb0eb231-b295-4c1c-9ddd-4d775bc74352`  
Track: `EXPLORE`  
Machine root: `workspace/gf32_itercap_eb0eb231/`

The one authorized attempt completed all 192 paired frames / 384 BP calls on the six frozen deep H0D GF(32)/polynomial-37 graphs. The only arm difference was `max_iter=90` versus `max_iter=250`; no OSD/MRB rescue or real input was used. Terminal status was `COMPLETE`, with the frozen screen classification `NO_SUFFICIENT_SIGNAL`.

Control and candidate each produced 146 exact-and-syndrome-valid outputs, for `Delta=0` and 0/6 positive graphs. Per-graph exact counts in seed order 2026093901–2026093906 were 25, 23, 24, 26, 23, 25 in both arms. Paired outcomes were both/control-only/candidate-only/neither = 146/0/0/46. Each arm had 46 raw syndrome failures and zero syndrome-valid-wrong outputs. Of the control failures, candidate transitions were exact/wrong/still-fail = 0/0/46; all 146 control syndrome-passes were prefix-consistent. Thus the control exact count was within the frozen [39,153] screen range, while the required Delta>=12 and positive-graphs>=4/6 conditions were not met.

Iteration totals were 5127 for control and 12487 for candidate, a difference of 7360 (46×160). Decoder-wall sums were 30.894529954 s and 74.938742763 s; maximum arm wall times were 0.623469105 s and 1.553238648 s. Batch wall was 156.382415121 s, including graph/deep-candidate construction, source generation, BP, and `diagnostics.npz`, while excluding compact summary/manifest/log writes. Sampled process RSS maximum was 103010304 B across 1371 samples; it is not a continuous peak. The diagnostics payload was 189744 B and compressed NPZ was 36456 B. Disclosure was 99840 syndrome bits; tag bits were zero. Verification remains `NOT_IMPLEMENTED` and undetected errors `NOT_MEASURED`.

The machine root contains exactly five artifacts: `manifest.json`, `frame_records.csv` (384 rows), `summary.json`, `EXPLORATION_LOG.md`, and `diagnostics.npz`. The NPZ contains the six deep H matrices, 192 sampled truth/syndrome pairs, all 384 returned raw vectors, and explicit pair/call/vector lineage. Integrity, resource, and authorization violations were zero; no STOP marker or reason was recorded. The exact authorized command is preserved in the packet and manifest.

This is only the frozen finite synthetic iid marginal-shape screen. It is not a significance, causal, route, cross-batch ranking, real-channel, FER, `f_eff`, SKR, throughput, security, qualification, or publication result. Zero syndrome-valid-wrong rows are not a verification or undetected-error bound. The one-shot batch authority is consumed; no rerun, resume, or extra samples follow.
