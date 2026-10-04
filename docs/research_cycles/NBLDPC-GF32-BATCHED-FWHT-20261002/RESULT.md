# EXPLORE — accepted batched FWHT fixed-case comparison

Main accepts independent F5 PASS_WITH_FINDING for UUID `7d45396d-a8ca-4a21-adef-74adacc5e9ec`, root `workspace/gf32_batchedfwht_7d45396d/`. Status **BATCHED_FWHT_FIXED_CASES_MATCH**, operator kernel_accel_design session74819 exit0, one attempt, no retry/post-execution code edits.

Only outgoing FWHT is batched. The old helper remains unchanged; keyword-only check_update_fn=None preserves the original default path. Candidate explicitly injects the new helper. Prior/graphs/labels/cold BP90/alpha1/edge order/clipping/normalization are fixed; no JIT/parallel/adaptive or default promotion.

Same18 convenience source-call cases as accepted hotspot443938ee, from replica UUIDcbe151fe-25f7-4990-8895-858091467e2b only. Round1 reference→batched per case, round2 reverse. Total72 calls/2628 iterations (657 per path per round), max90; all72 source and36 paired checks passed. x_hat/status/iterations/syndrome agree, final-belief max absolute difference0.0 (atol1e-12/rtol0). Each path/round12 exact/18 call cases,0 valid-wrong, repeating the same cases rather than new frames/efficacy observations.

| Round | Reference outer call wall (s) | Batched (s) | Batched/reference |
| --- | ---: | ---: | ---: |
| 1 | 4.011259 | 2.736013 | 0.682083 |
| 2 | 3.969121 | 2.754680 | 0.694028 |
| Both timing rounds | 7.980380 | 5.490693 | 0.688024 |

Internal runtime sums7.979332/5.489601s. About31.2% lower outer call wall (inverse-time ratio1.45×) applies only to this frozen outcome-conditioned sample. No pipeline throughput, fresh holdout, universal speedup or full-six-branch effectiveness/cost certification. Next useful validation would cover all saved baseline/restart calls and final choices in a separately frozen synthetic packet.

Reviewer independently recomputed cases/maps/order/source-vector syndrome/truth flags, iteration/status/report fields, paired sums/ratios and resources. Returned vectors/beliefs were not persisted: actual equality/allclose comparisons ran in the CLI and their flags/max differences were saved; reviewer checked that code/records rather than directly observing replay-returned arrays. No BP/test rerun.

Checkpoint13.555496s after production binding/import through first-pass outputs; RSS103882752B (Linux KiB×1024), no STOP/resource events. Source reads1, sampler/search/build0. First-pass23723B; execution-terminal four files23855B independently measured before review/closeout append, below5MiB. These are not recursive finalization/full-process measurements.

Non-blocking finding: machine manifest/summary/log omitted explicit disclosure/tag/verification/undetected fields. Frozen local-replay semantics are no additional public disclosure/tag action (0/0), verification NOT_IMPLEMENTED and undetected NOT_MEASURED; these are contract semantics, not serialized security measurements. Raw artifacts retained, no patch/rerun. No FER/f_eff/SKR, pooling/ranking, real-data/n256/N2048, qualification/promotion/publication/security or route claim.

Focused21 tests passed3.27s (helper tiny-math, explicit1×2/maxiter1 seam, fake paired runner; no accepted arrays/production source binding); compile/help/T0dry/scoped branch/root absence PASS. Only assigned v35 seam/new helper/new CLI/new test changed, unrelated dirty work preserved. No commit/push/merge/add/archive. Project-memory triage and independent documentation milestone accompany closeout.
