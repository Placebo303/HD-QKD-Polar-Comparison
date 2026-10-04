# Independent batch-end review and main acceptance

`faithful_scope`, independent of operator `shape_closeout`, completed P7 with
PASS. The review recounted 384 rows and 192 pairs; checked seed, pair order,
arm identity, per-graph counts, success and paired-state aggregates, resource
and accounting fields, and consistency across the four retained artifacts.
It confirmed control/candidate success `151/151`, `Delta=0`, per-graph
successes `25/25, 23/23, 25/25, 25/25, 24/24, 29/29`, positive graphs `0/6`,
and paired states `151/0/0/41` (both/candidate-only/control-only/neither).

The review also confirmed the wrong-result accounting: in each arm, 41
syndrome-valid wrong outcomes comprise one raw BP passthrough and 40
syndrome-valid wrong MRB rescues. It verified the recorded disclosure,
zero-valued integrity/resource/authorization violation counts, and frozen
screen outcome. Sampled truth/prior arrays were not persisted, so the reviewer
did not independently replay their values. Verification remains
`NOT_IMPLEMENTED`; undetected errors remain `NOT_MEASURED`.

Main accepts the batch only as `NO_SUFFICIENT_SIGNAL` within the frozen
synthetic iid marginal-shape comparison and its stated claim ceiling. This
does not reject the route or support causal, conditional-channel, FER,
`f_eff`, SKR, throughput, qualification, publication, or cross-batch ranking
claims. The batch grant is consumed; no rerun or extension follows from this
acceptance.
