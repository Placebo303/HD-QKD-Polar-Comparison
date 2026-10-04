# Result — NB-LDPC GF32 MRB top-6

Batch `df44e589-370d-4818-b652-2e2cc67de758` is closed and main-accepted as
`NO_SUFFICIENT_SIGNAL` within this frozen synthetic comparison. The one
authorized run completed 192 paired holdout frames (384 BP calls), with no
pilot calls, at fixed `p0=0.55` and seed namespace `gf32-mrb-top6-v1`. The
six fixed deep H0D graphs each contributed 32 pairs.

The comparator was the same order-1 GF32 BP+MRB pipeline with the existing
helper's `top_symbols=None` versus `top_symbols=6`. Control and candidate each
had 151 exact-and-syndrome successes; `Delta=0`. Per-graph control/candidate
successes were:

| Graph seed | Control | Candidate | Delta_g |
|---|---:|---:|---:|
| 2026093901 | 25 | 25 | 0 |
| 2026093902 | 23 | 23 | 0 |
| 2026093903 | 25 | 25 | 0 |
| 2026093904 | 25 | 25 | 0 |
| 2026093905 | 24 | 24 | 0 |
| 2026093906 | 29 | 29 | 0 |

Paired states were both-success 151, neither-success 41, candidate-only 0,
and control-only 0. Each arm had 41 syndrome-valid wrong outcomes: one raw BP
syndrome-valid-but-wrong passthrough and 40 wrong MRB-selected rescues. The
two arms together selected 80 rescues and examined 20,480 candidate vectors;
these wrong outputs remain failures. Final syndrome acceptance does not
substitute for exact success.

The frozen control-range gate `[39,153]` passed at 151. The `Delta >= 12` gate
and the positive-delta-on-at-least-4/6-graphs gate both failed (`0/6` positive
graphs). This yields `NO_SUFFICIENT_SIGNAL`; it is not a route rejection or a
causal claim.

Recorded syndrome disclosure was 99,840 bits and tag bits were 0. Verification
was `NOT_IMPLEMENTED`; undetected errors were `NOT_MEASURED`; `FER`, `f_eff`,
and `SKR` are null. Integrity, resource, and authorization violations were
all 0. Batch wall time was 119.521162 s, maximum call time 0.707369 s, and
recorded maximum RSS 113,131,520 B over 1,610 samples. The run used the fresh
root `workspace/gf32_mrb_top6_df44e589/` and produced four machine artifacts.

The claim ceiling is this paired order-1 GF32 MRB comparison, differing only
in the existing helper's `top_symbols` argument, on six fixed deep H0D graphs
under a synthetic iid marginal-shape proxy. It does not establish hard source
support, a conditional-channel result, cross-batch ranking, FER, `f_eff`,
SKR, throughput, qualification, publication, or route performance. Truth and
prior arrays were not saved, so the batch-end reviewer did not replay sampled
vectors value by value. No rerun or extension is authorized by this packet.
