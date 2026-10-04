# Independent acceptance — MRB additive reaggregation

**Reaggregation:** `e1d549f7-695d-4166-8c4c-e6eaa803a735`  
**Scientific batch retained:** `ebbbe5c2-f53f-4b92-a2ff-3eca358002de`  
**Independent reviewer:** `faithful_contract`  
**Disposition:** P6 PASS; main accepted the additive aggregate within the frozen EXPLORE ceiling.

The independent reviewer rechecked the frozen source identity and reaggregation roles, all 384 rows, 192 pair seeds and alternating arm order, exact-and-syndrome success rule, per-graph and paired-state counts, wrong-output separation, rescue/candidate counts, 260-bit-per-attempt disclosure, resource fields, source costs, output set, and no-source-write/no-science boundary. Results were control/candidate=149/149, Δ=0, all six Δg=0, paired states 149/0/0/43, and wrong outputs control/candidate=0/43. The 43 candidate rescues examined 11,008 candidate vectors; all selected syndrome-valid outputs were wrong and remained failures. The screen is `NO_SUFFICIENT_SIGNAL`.

The reviewer confirmed that source batch wall=116.326794 s covers the 66.473994 s sum of retained per-call wall times; max call=0.707384 s and sampled RSS=111,742,976 B over 1,499 samples agree with the source manifest/rows. Reaggregation cost was 0.011516 s with 100,306,944 B maximum sampled RSS over four samples; the stated scope excludes writing the three derived outputs. Exactly the three frozen reaggregation artifacts were produced; no new graph, decoder, OSD, or sample call occurred. The old source `summary.json` identity was recognized as deficient and was not used or changed.

The independent review cannot replay sample vectors because the source arrays were not saved. Acceptance is limited to the mechanical stored-row aggregate and the frozen screen. Verification=`NOT_IMPLEMENTED`, undetected=`NOT_MEASURED`, tag=0; no FER, `f_eff`, SKR, throughput, qualification, publication, route, conditional-channel, causal, or cross-batch ranking claim is accepted. The original scientific batch is still `ebbbe5c2`; the new UUID identifies only its additive reaggregation. Main acceptance does not repair or rewrite the original summary.
