# Source-aware edge-label R2 — EXPLORE result

Batch UUID `358c49ba-4cab-4df2-b424-e17dad5bfe55`; parent retained-failure batch `f6fbf8cf-8773-4099-af68-54136326b60d`. Main closes and accepts this run only as the finite synthetic observation below, terminal `NO_SUFFICIENT_SIGNAL`.

The run used the frozen six GF(32)/polynomial-37 graphs (seeds 2026093901–2026093906), p0=0.550, the `gf32-source-label-v1` holdout namespace, 192 paired holdouts and 384 decoder calls; there was no pilot. All six graphs passed structural/GF(32) rank 52 admission. Each candidate kept support and degrees, changed cycle class, and was not row/column-gauge-equivalent to its control. Candidate rank was 52 for every graph.

| Graph seed | Control → candidate exact successes | Δg | Changed labels | F reduction | Unit / positive / zero source-overlap orbits, control → candidate |
|---|---:|---:|---:|---:|---|
| 2026093901 | 23 → 23 | 0 | 6 | 0.0016321725642 | 15/6/9 → 8/0/8 |
| 2026093902 | 24 → 24 | 0 | 5 | 0.0022268558004 | 15/5/10 → 10/0/10 |
| 2026093903 | 25 → 24 | −1 | 8 | 0.0143075536141 | 19/11/8 → 10/0/10 |
| 2026093904 | 29 → 29 | 0 | 4 | 0.0009043438462 | 25/4/21 → 23/0/23 |
| 2026093905 | 25 → 22 | −3 | 7 | 0.0093060267170 | 17/7/10 → 14/0/14 |
| 2026093906 | 25 → 25 | 0 | 3 | 0.0001442103639 | 14/3/11 → 10/0/10 |

The source-objective F decreased on all six candidates, reaching F=0 in each. Across the batch, control/candidate successes were 151/147 (Δ=−4), with 0/6 positive Δg. Paired states were both/candidate-only/control-only/neither = 146/1/5/40. Control was within the frozen range 39–153, but the required Δ≥12 gate failed. The candidate had 75 unit orbits (0 positive, 75 zero), versus control 105 (36 positive, 69 zero). Gauge diagnostics found cycle-class change on all six graphs.

There were 99840 disclosed syndrome bits (260 per call), tag bits=0, and zero syndrome-consistent wrong rows. Verification is `NOT_IMPLEMENTED`; undetected is `NOT_MEASURED`. FER, `f_eff`, and SKR are null. Search counters were 47616 label trials, 1075886 affected-cycle evaluations, and 22621 separate full-reference evaluations.

Measured batch wall time was 153.734255 s; maximum arm wall time was 0.557433 s; reported maximum RSS was 122302464 bytes over 4264 samples. Control/candidate decoder wall sums were 29.428333/30.508201 s, with 4866/5051 total decoder iterations. Integrity, resource, and authorization violations were all zero; `stop_reason` was empty.

Independent `faithful_scope` review passed P1–P7; reviewer and operator were different. The review checked the saved GF/W/label-all-31 replay, reference/counter consistency, and the 384-row CSV's seeds, order, leakage, accounting, and resource record. Sampled truth/prior arrays were not saved, so the vectors cannot be reconstructed value by value from the artifacts. This result is limited to the frozen six-graph synthetic iid marginal-shape proxy. It is not conditional-channel reconstruction, causal or significance evidence, a route decision, or a rejection of the NB-LDPC family; do not pool or rank it across batches or infer FER, `f_eff`, SKR, throughput, qualification, or publication claims. The earlier parent batch remains a separate retained failure. This batch's grant is consumed; there is no rerun, repair, or extra-frame authorization.

Machine artifacts: `workspace/gf32_source_label_r2_358c49ba/manifest.json`, `frame_records.csv`, `summary.json`, and `EXPLORATION_LOG.md`.
