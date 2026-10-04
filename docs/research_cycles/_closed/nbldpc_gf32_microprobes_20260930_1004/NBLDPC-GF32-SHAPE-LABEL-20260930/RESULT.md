# Result — historical-shape GF32 label alignment

**Track:** EXPLORE  
**Batch UUID:** `fd01e03e-3832-4f01-bdb1-eecd744e4b40`  
**Status:** `CLOSED / ACCEPTED` for the frozen synthetic CONTROL-pilot STOP only.  
**Terminal classification:** `CONTROL_RANGE_UNINFORMATIVE` (`summary.json` classification `INCOMPLETE`).

## Frozen setup

This batch used a new synthetic n=128, m=52 graph profile over six seeds `2026093801..2026093806` (128 variable nodes of degree 2; 4 checks of degree 4 and 48 of degree 5; E=256). Every graph passed the frozen preflight: no duplicate edges, one connected support, structural rank 52, and GF(32) rank 52.

The iid error PMF used only the previously accepted historical 2M nonzero marginal-shape proxy counts `{1:2295, 3:1126, 7:557, 15:304, 31:146}` (total 4428), not a new empirical read or a reconstruction of the conditional channel. Bob was fixed to zero, so source dependence on Bob and temporal structure were absent. The normalized nonzero-shape entropy was 1.7976135070 bits. The frozen p0 grid and constructed PMF entropies were:

| Index | p0 | H(PMF), bits | Control exact-and-syndrome successes |
|---:|---:|---:|---:|
| 0 | 0.85 | 0.8794823308 | 24/24 |
| 1 | 0.65 | 1.5632327828 | 24/24 |
| 2 | 0.45 | 1.9814618828 | 3/24 |
| 3 | 0.25 | 2.1594882547 | 0/24 |

The p0=0.45 successes by graph seed were `[0,0,1,0,1,1]` in the frozen seed order. There were zero syndrome-consistent wrong outputs at every grid point. The preregistered CONTROL-only selector required 5–19 successes out of 24. Neither 24/24 point was in range, and both later points were below range; therefore no p0 was selected and the batch stopped after all four pilot points.

## Execution and accounting

The run made 96 CONTROL-only pilot calls and wrote the four frozen root files: `manifest.json`, `frame_records.csv`, `summary.json`, and the append-only `EXPLORATION_LOG.md`. Each call disclosed 260 syndrome bits, for 24,960 bits across the attempted calls. Wall time was 26.929810 s, maximum decoder-call time 0.574928 s, and peak RSS 100,954,112 bytes. Authorization, integrity, and resource violation counts were all zero. `tag_bits=0`; physical verification was `NOT_IMPLEMENTED` and undetected errors were `NOT_MEASURED`.

The selected PMF is null. No candidate label matrix was built or decoded, and no holdout calls or pairs were started. The machine summary has zero counts in all four paired-state categories because there were zero completed pairs; those raw counts describe no observation and are not a performance denominator. Control success, candidate success, delta, and per-graph deltas remain unknown (`null`), not zero. The `INCOMPLETE` label describes the unrun holdout after the preregistered selector stopped, not a failed candidate.

## Review, acceptance, and limits

Independent reviewer `faithful_scope` (not the operator) passed the batch-end review P1–P7, independently checking all 96 CSV calls and seeds, pilot order and counts, 260-bit accounting, graph profile/rank/connectivity, and resource and claim boundaries. The reviewer confirmed zero calls and rows for candidates and holdout. The main thread accepts only the frozen synthetic iid marginal-shape CONTROL pilot and its `CONTROL_RANGE_UNINFORMATIVE` STOP.

This result neither measures a label benefit nor a lack of label benefit. It does not establish a route decision, compare or rank this new graph profile against the earlier L055 batch, or reject NB-LDPC as a family. The iid Bob-zero marginal proxy is not the historical conditional channel, a qualified real channel, or evidence transferable to current Model-F. No FER, `f_eff`, SKR, throughput, qualification, or publication claim follows.

The authorization “可以继续” is consumed. A separate `NBLDPC-GF32-SHAPE-FINE-DRAFT` exists only as an ungranted planning pointer; it is not an accepted conclusion and authorizes no execution. Any successor requires a new frozen packet and explicit grant. No retry, fitting, new data read, archive, commit, push, or merge occurred.
