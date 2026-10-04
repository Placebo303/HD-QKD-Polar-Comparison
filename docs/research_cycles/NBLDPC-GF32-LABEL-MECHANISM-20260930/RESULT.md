# GF32 label alignment EXPLORE result

Date: 2026-09-30. Batch UUID: `a74e912c-4bac-4d7d-9fe9-2358bd8a85d1`.
Track: **EXPLORE**. Terminal: **NO_SUFFICIENT_SIGNAL**.
Preregistration: [PREREG_AND_AUTH.md](PREREG_AND_AUTH.md).
Machine root: `workspace/gf32_label_a74e912c/`.

## Frozen scope

This batch tested one synthetic L1 mechanism at n=128 over GF(32),
polynomial 37. It held the six L055 graph supports, prior, sampled errors,
decoder, iteration settings, and syndrome length fixed; the candidate changed
only nonzero edge labels using the preregistered column-scaling rule. The
source PMF was constructed for this experiment and is not a measured HD-QKD
error law. Each arm computed its own syndrome from its own parity-check
matrix. This result covers L1 exact recovery on this synthetic model only.

## Execution and result

The T0 checks passed 6/6. All six baseline graphs passed preflight at rank
118 with 301 edges. Pilot PMF 0 gave 2/24 control exact; PMF 1 gave 8/24 and
was selected by the frozen rule. The 432 decoder calls comprise 48 pilot
calls and 384 holdout calls over 192 complete paired frames. No pilot
candidate calls were made. All six candidates were admitted with rank 118,
equal support, and the frozen column-gauge identity; each was nontrivial and
had a higher analytic sum-check-entropy score than its baseline. This score
is a construction proxy, not a decoder-performance measure.

| Holdout outcome | Count |
|---|---:|
| Control exact | 58/192 |
| Candidate exact | 57/192 |
| Both exact | 52 |
| Control only | 6 |
| Candidate only | 5 |
| Neither | 129 |
| Δ = candidate − control | −1 |

Per-graph exact counts and differences were:

| Graph seed | Control | Candidate | Δ_g |
|---|---:|---:|---:|
| 2026093701 | 14 | 15 | +1 |
| 2026093702 | 9 | 9 | 0 |
| 2026093703 | 10 | 10 | 0 |
| 2026093704 | 9 | 8 | −1 |
| 2026093705 | 11 | 11 | 0 |
| 2026093706 | 5 | 4 | −1 |

The frozen `MECHANISM_SIGNAL` gate required Δ≥12 and positive Δ_g on at least
4/6 graphs, alongside a control total of 39–153, 192 completed pairs, and no
integrity, authorization, or resource violations. The control-range and
completion conditions passed; the effect thresholds did not (Δ=−1 and
positive Δ_g on 1/6 graphs). Therefore the preregistered classification is
`NO_SUFFICIENT_SIGNAL`. It is a result for this frozen screening experiment;
it does not reject NB-LDPC or settle the label mechanism beyond this scope.

## Accounting and claim ceiling

Wall time was 247.648 s, maximum synchronous call time 0.838521 s, and peak
RSS 102,903,808 bytes. There were zero resource, authorization, integrity,
or syndrome-consistent-wrong violations. Each attempted call accounted for
590 syndrome bits; `tag_bits=0`, `verification_status=NOT_IMPLEMENTED`, and
`undetected_status=NOT_MEASURED`. The batch has no physical verifier.

The claim ceiling is **synthetic L1 mechanism screening only**. This result
does not establish full-pair recovery, real-data performance, FER, `f_eff`,
SKR, throughput qualification, or route closure. In particular, the result
does not authorize n256 or an automatic successor experiment.

## Review and acceptance

The independent Luna reviewer `label_plan_review` recorded batch-end
**PASS**, independently recomputing the paired counts, budget accounting,
rank/support/gauge checks, and authorization boundary against the artifacts.
Main-thread acceptance is limited to the faithful execution record and the
frozen `NO_SUFFICIENT_SIGNAL` classification. The main thread makes no
family-level negative conclusion and grants no successor authorization.

The append-only process record is
[`workspace/gf32_label_a74e912c/EXPLORATION_LOG.md`](../../../workspace/gf32_label_a74e912c/EXPLORATION_LOG.md);
machine evidence is in `manifest.json`, `summary.json`, and
`frame_records.csv` under that root.
