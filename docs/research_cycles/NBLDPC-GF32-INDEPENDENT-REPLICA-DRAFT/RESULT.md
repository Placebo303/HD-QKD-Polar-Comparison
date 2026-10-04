# Result: independent new-graph GF(32) label replica EXPLORE

**Date:** 2026-09-30  
**Track:** EXPLORE  
**Batch UUID:** `7d6e57f0-b78c-45ea-b18d-dc2c2adec353`  
**Machine root:** `workspace/gf32_label_replica_7d6e57f0/`  
**Terminal:** `NO_SUFFICIENT_SIGNAL`  
**Disposition:** batch closed and accepted within the frozen claim ceiling.

## Frozen question and scope

This one-shot synthetic test evaluated the fixed-p0 label-allocation
observation on six new n=128, m=52, E=256 graphs, using the accepted
historical marginal-shape proxy as an iid error source with Bob fixed to zero.
The fixed PMF used p0=0.550; there was no pilot or grid selection. Each graph
contributed 32 pairs from two streams of 16 frames. Only the label assignment
within each pair differed; the profile, PMF/prior, decoder and H0D candidate
rule remained fixed. This does not reconstruct the historical conditional
channel or temporal structure.

## Paired holdout results

All 192 pairs (384 decoder calls) completed. CONTROL had 139 exact-and-syndrome
successes and candidate had 147, for a difference of +8.

| Graph seed | CONTROL | Candidate | Difference |
|---|---:|---:|---:|
| 2026093901 | 19 | 21 | +2 |
| 2026093902 | 24 | 26 | +2 |
| 2026093903 | 22 | 22 | 0 |
| 2026093904 | 22 | 29 | +7 |
| 2026093905 | 29 | 27 | −2 |
| 2026093906 | 23 | 22 | −1 |
| **Total** | **139** | **147** | **+8** |

Paired states were both-success 128, candidate-only 19, CONTROL-only 11, and
neither 34. Three of six per-graph differences were positive.

## Gates, accounting and resources

All six graph constructions passed the frozen profile, connectivity,
duplicate-edge and rank gates. All six candidates passed the frozen support,
gauge, rank and nontriviality gates.
The CONTROL count of 139 was within the frozen 39–153 interval. The +12 total
difference gate and the requirement for positive differences on at least 4/6
graphs both failed (observed +8 and 3/6). The frozen mechanical classification
is `NO_SUFFICIENT_SIGNAL`; these finite observations are not a significance or
route test.

There were 384 attempted calls, each disclosing 260 syndrome bits, for 99,840
bits total: 49,920 per arm. Syndrome-consistent wrong rows were zero. Physical
verification was `NOT_IMPLEMENTED` and undetected errors were
`NOT_MEASURED`; zero wrong rows must not be read as zero physical undetected
errors. Integrity, resource and authorization violations were all zero.

Wall time was 79.960884 s, maximum decoder-call wall time 0.577542 s, and peak
RSS 101,896,192 bytes. The independent review checked paired seed/key identity,
alternating arm order and separation of the new seed namespace from prior
batches. The four machine artifacts do not store the truth/prior arrays, so
those shared arrays cannot be reconstructed value by value from the artifacts;
pairing is supported by the frozen runner and fake-test contract.

## Independent review, acceptance and limits

Independent reviewer `faithful_scope` (not operator `faithful_contract`)
reported batch-end P1–P7 PASS. The main thread accepted this result only as a
fixed-p0 synthetic iid marginal-shape observation on these six new graphs.
The one-shot grant is consumed; no additional frames, restart, n=256 run or
new scientific batch is authorized.

Do not pool or rank this batch with earlier batches. It establishes no
conditional-channel or source-faithful result, FER, f_eff, SKR, throughput,
qualification, Model-F transfer, publication or route conclusion, and does
not reject the NB-LDPC family.
