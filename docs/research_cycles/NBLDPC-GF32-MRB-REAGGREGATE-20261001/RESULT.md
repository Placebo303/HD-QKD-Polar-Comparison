# MRB additive reaggregation — EXPLORE result

**Reaggregation UUID:** `e1d549f7-695d-4166-8c4c-e6eaa803a735`  
**Scientific source batch:** `ebbbe5c2-f53f-4b92-a2ff-3eca358002de`  
**Machine root:** `workspace/gf32_mrb_reaggregate_e1d549f7/`  
**Terminal:** `REAGGREGATION_COMPLETE`; recomputed frozen screen: `NO_SUFFICIENT_SIGNAL`.

This action read the retained MRB manifest and 384-row frame CSV and made no new samples, graphs, decoder calls, or OSD calls. It wrote only `manifest.json`, `summary.json`, and `EXPLORATION_LOG.md` in the new root. The original scientific batch UUID, MRB contract, and `gf32-mrb-rescue-v1` namespace remain the summary's scientific identity. The reaggregation UUID/contract identify only this derived reader pass. The original source `summary.json` has inherited damping identity and was not used; no source artifact was modified or copied.

The complete 192-pair table gives control=149 and candidate=149 exact-and-syndrome successes, Δ=0. Per graph, both arms scored 22/32, 24/32, 28/32, 25/32, 24/32, and 26/32 for seeds 2026093901–2026093906, so Δg=0 on all six graphs. Paired states are both=149, candidate-only=0, control-only=0, neither=43. Control=149 is inside the frozen [39,153] range; Δ≥12 and positive Δ on at least 4/6 graphs are not met. The recomputed terminal is `NO_SUFFICIENT_SIGNAL`.

There were 43 raw syndrome failures in each arm. MRB was attempted and selected a candidate on all 43 candidate-arm failures, examining 11,008 candidates. Final syndrome acceptance was control=149 and candidate=192. The 43 candidate outputs accepted by syndrome were all wrong and were not counted as success; control had zero wrong outputs. Iteration sums were 5,017 per arm. Full arm wall sums were 30.339190 s control and 36.134804 s candidate; BP runtime sums were 30.259852 s and 30.202624 s; total rescue wall time was 5.835860 s. Attempted disclosure was 99,840 syndrome bits (260 per call), tag=0. Integrity/resource/authorization violations were all zero.

Inherited science cost, from the source manifest: batch wall=116.326794 s, max call=0.707384 s, sampled high-water RSS=111,742,976 B over 1,499 samples. The 66.473994 s sum of retained call wall times is below the batch wall. New reaggregation cost was 0.011516 s and 100,306,944 B maximum sampled RSS over four samples; the measurement scope covers manifest/CSV read and reduction and excludes writing the three new artifacts. The reader used 2 source artifact reads and 384 source rows, within its 600 s, 4 GiB, and 384-row caps.

This is a stored-row reaggregation of one completed synthetic iid marginal-shape trial, not a second scientific batch. Truth/prior/belief/estimate arrays were not saved, so no vector replay or redecoding was possible. Verification remains `NOT_IMPLEMENTED`, undetected remains `NOT_MEASURED`, and tag=0 is only the frozen accounting entry. No FER, `f_eff`, SKR, throughput, qualification, publication, route decision, conditional-channel inference, or cross-batch ranking follows.
