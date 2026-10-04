# NB-LDPC GF32 admitted-matrix degree-profile EXPLORE result

Batch UUID: `a9352bc1-ae56-443b-ae93-9dcfa85d4229`  
Track: `EXPLORE`  
Machine root: `workspace/gf32_degree_admitted_a9352bc1/`

The one authorized attempt completed 192 paired samples / 384 BP calls using
the six common-admitted graph groups from the accepted construction canary.
No constructor ran in this batch: all 12 matrices were loaded from the fixed
source by selected `matrix_index`, with `graphs_built=0` and six matrices
loaded per profile. The source canary's construction cost is separate.

The batch is `COMPLETE` and classified `NO_SUFFICIENT_SIGNAL` under the frozen
screen. Control/candidate exact-and-own-syndrome successes were 144/1
(`Delta=-143`), with positive graphs 0/6. Per-graph control/candidate exact
counts for graph IDs 2026093901–2026093906 were 27/0, 25/0, 19/0, 23/0,
25/0, and 25/1. Paired both/control-only/candidate-only/neither counts were
1/143/0/48. Raw syndrome failures were 48/191; all 239 reached 90 iterations.
Syndrome-valid wrong outcomes were 0. Among the 48 control raw failures,
candidate exact/wrong/still-failed outcomes were 0/0/48. The control count was
within the frozen [39,153] range; the `Delta >= 12` and positive-graph >=4/6
gates were not met.

Iterations summed to 5274/17199. Per-arm decoder-wall sums were
32.031156971/149.823367981 s; label-search sums were 53.408911051/152.915036230
s. Full batch wall time was 390.257774451 s. Sampled process RSS peaked at
106266624 B over 1394 samples (not a continuous peak); maximum single-call
wall times were 0.561814928/0.823502782 s. The nominal `E × sum(iterations)`
proxy was 1350144/6604416, total 7954560 against the frozen cap 11059200; this
is an iteration proxy, not measured operations. The run disclosed 99840
syndrome bits with tag=0; verification is `NOT_IMPLEMENTED` and undetected
errors are `NOT_MEASURED`.

The five retained artifacts are `manifest.json`, `frame_records.csv` (384
call rows), `summary.json`, `diagnostics.npz`, and `EXPLORATION_LOG.md` under
the machine root. NPZ size/payload were 68390/1428840 B. There were 384 BP
calls, 0 OSD calls, and 0 integrity/resource/authorization violations; no
STOP occurred.

Independent A5 review and main acceptance are recorded in
`INDEPENDENT_ACCEPTANCE.md`. The accepted scope is only this frozen common-
admission degree-profile bundle and sample. It does not isolate a degree-only
causal effect or establish random-graph population performance, NB-LDPC route
rejection, FER, `f_eff`, SKR, throughput, security, qualification, publication,
real-channel behavior, or cross-batch ranking. The one-shot grant is consumed;
no rerun, resume, replacement graph, or extension is authorized.
