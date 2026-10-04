# Result: GF(32) shape-proxy label fine-grid EXPLORE

**Date:** 2026-09-30  
**Track:** EXPLORE  
**Batch UUID:** `d2d185a6-1b3f-4c8f-89f8-f7ac98d04a22`  
**Machine root:** `workspace/gf32_shape_fine_d2d185a6/`  
**Terminal:** `NO_SUFFICIENT_SIGNAL`  
**Disposition:** batch closed and accepted within the frozen claim ceiling.

## Frozen question and scope

This one-shot synthetic batch tested the fixed-graph GF(32) edge-label
allocation hypothesis using the accepted historical marginal-shape proxy as an
iid error source with Bob fixed to zero. It changed only the CONTROL p0
selection grid to `[0.625, 0.600, 0.575, 0.550, 0.525, 0.500, 0.475]`; the
graph profile, prior construction, decoder and candidate rule remained fixed.
The six graphs use seeds `2026093801`–`2026093806`, n=128, m=52 and E=256.
This is a marginal-shape stress test, not a reconstruction of the historical
conditional channel or temporal structure.

## Pilot and paired holdout

CONTROL exact-and-syndrome counts were 22/24, 21/24, 21/24 and 16/24 at the
first four grid points. Index 3 (p0=0.55) was the first point inside the frozen
5–19 selector interval; later grid points were not run. The gated candidate
arm and holdout then completed all 192 independent pairs
(384 holdout decoder calls).

| Graph seed | CONTROL | Candidate | Difference |
|---|---:|---:|---:|
| 2026093801 | 20 | 22 | +2 |
| 2026093802 | 22 | 23 | +1 |
| 2026093803 | 26 | 27 | +1 |
| 2026093804 | 22 | 23 | +1 |
| 2026093805 | 22 | 27 | +5 |
| 2026093806 | 18 | 18 | 0 |
| **Total** | **130** | **140** | **+10** |

The paired states were both-success 122, CONTROL-only 8, candidate-only 18,
and neither 44. Five of six graph differences were positive. Candidate J-gain
diagnostics in seed order were 3.837213, 4.169297, 4.474067, 5.031747,
3.806862 and 3.880288 bits. All six graphs passed the frozen profile,
connectivity, duplicate-edge, structural-rank and GF(32)-rank checks; each
candidate passed the frozen nontriviality, support, gauge and rank gates.

## Accounting, gates and resources

There were 480 decoder calls and rows: 96 CONTROL pilot calls, 192 holdout
CONTROL calls and 192 holdout candidate calls. Each disclosed 260 syndrome
bits, for 124,800 total (24,960 pilot bits and 49,920 per holdout arm). One
syndrome-consistent wrong result occurred in pilot CONTROL; holdout had zero.
This is not a physical undetected-error measurement: tag bits were zero,
verification was `NOT_IMPLEMENTED`, and undetected errors were
`NOT_MEASURED`.

The selector, all-pairs completion, holdout CONTROL range (130 within 39–153),
and positive-graph screen (5/6) passed. The frozen total-difference threshold
was the only signal gate missed: +10 did not reach +12. The mechanical
classification is therefore `NO_SUFFICIENT_SIGNAL`; the small positive
observation is not a statistical or established mechanism-success claim.

Wall time was 98.146604 s, maximum decoder-call wall time 0.588502 s, and peak
RSS 101,556,224 bytes. Integrity, resource and authorization violations were
all zero. The implementation review recorded 11 fake-focused tests passing
and T0 8/8; these are engineering checks, not additional scientific runs.

## Independent review, acceptance and limits

Independent reviewer `faithful_scope` reported batch-end P1–P7 PASS. The main
thread accepted this frozen synthetic iid marginal-shape label observation and
its mechanical `NO_SUFFICIENT_SIGNAL` classification. The user grant for this
one-shot batch is consumed. No additional frames, restart, n=256 run, or new
scientific batch is authorized by this acceptance.

Do not pool or rank this result across batches. It establishes no historical
conditional-channel or source-faithful result, FER, f_eff, SKR, qualification,
Model-F transfer, publication conclusion, route decision, or rejection of the
NB-LDPC family. Candidate and CONTROL counts here apply only to this frozen
synthetic batch and its six-graph profile.
