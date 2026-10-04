# Independent batch-end acceptance

Batch UUID: `44c394bc-e3dd-4e6b-9d4a-8a5b0dd5cdfc`  
Track: `EXPLORE`  
Independent reviewer: `iter_contract`

**R6 verdict: PASS**, limited to the frozen synthetic batch and its mechanical classification. The independent review checked the actual GF(32) outcomes, CSV/NPZ row and graph mappings, the fixed row permutation and corresponding syndrome mapping, seed plan, disclosure/resource accounting, and frozen call/resource caps. All checked items passed; the review did not rerun the decoder.

The reviewed batch completed 192 pairs / 384 BP calls with control/candidate exact-and-syndrome successes 152/148 (`Delta=-4`), positive graphs 0/6, and paired both/control-only/candidate-only/neither outcomes 148/4/0/40. The 40 control failures produced 0 candidate exact, 0 syndrome-valid wrong, and 40 still-failed outcomes. Classification is `NO_SUFFICIENT_SIGNAL` under the frozen gates. Iterations were 4934/5001; arm decoder-wall sums were 29.421401827/29.809025610 s; batch wall time was 110.419199688 s; sampled maximum RSS was 103575552 B over 1370 samples. NPZ size/payload were 47321/240624 B. Disclosure was 99840 syndrome bits, tag=0, verification=`NOT_IMPLEMENTED`, undetected=`NOT_MEASURED`.

The main thread accepts only this bounded finite synthetic observation and its frozen classification. It is not route rejection or promotion, nor FER/`f_eff`/SKR, throughput/security, causal, real-channel, qualification, publication, or cross-batch ranking evidence. The zero syndrome-valid wrong count is not a verification or undetected-error bound. The authorization is consumed; no rerun or extension is authorized.
