# Independent batch-end acceptance

Batch UUID: `a9352bc1-ae56-443b-ae93-9dcfa85d4229`  
Track: `EXPLORE`  
Independent reviewer: `iter_contract`

**A5 verdict: PASS**, limited to the frozen admitted-matrix synthetic batch and
its mechanical classification. The review did not rerun the decoder.

The independent review checked the actual selected-source matrix equality and
profile/deep-matrix lineage; six-graph, 192-pair, 384-call seed and artifact
maps; and the 384 saved raw-vector outcomes using GF(32) with polynomial 37
and each arm's own matrix syndrome. The recomputed exact, syndrome-valid-wrong,
and raw-syndrome-fail classes agree with the saved CSV/summary: control/candidate
exact=144/1, valid-wrong=0, raw failures=48/191. All 239 failures reached the
90-iteration cap. The review also checked syndrome disclosure, the nominal
edge-update proxy, sampled resource accounting and the frozen result gate.
The rank/connectedness provenance for the admitted source bundle is the
independent C4 review of that source canary; this batch did not rebuild graphs
or perform a new constructor run.

The batch completed 192 pairs / 384 BP calls with `Delta=-143`, positive
graphs 0/6, and paired both/control-only/candidate-only/neither counts
1/143/0/48. The 48 control raw failures yielded 0 candidate exact, 0
syndrome-valid wrong, and 48 still-failed outcomes. Since control=144 was
within [39,153], while `Delta >= 12` and positive graphs >=4/6 were not met,
`NO_SUFFICIENT_SIGNAL` is the frozen classification. Iterations were
5274/17199; decoder-wall sums were 32.031156971/149.823367981 s; the nominal
`E × sum(iterations)` proxy was 1350144/6604416 (7954560 total, cap 11059200).
Batch wall time was 390.257774451 s; sampled max RSS was 106266624 B over 1394
samples. Disclosure was 99840 syndrome bits; tag=0, verification=
`NOT_IMPLEMENTED`, undetected=`NOT_MEASURED`; integrity/resource/authorization
violations were 0.

The main thread accepts only this frozen common-admission profile-bundle
observation and its screen classification. It is not a degree-only causal
result, an NB-LDPC family or route rejection, nor FER/`f_eff`/SKR,
throughput/security, real-channel, qualification, publication, or cross-batch
ranking evidence. The zero syndrome-valid-wrong count is not a verification or
undetected-error bound. Authorization is consumed; no rerun or extension is
authorized.
