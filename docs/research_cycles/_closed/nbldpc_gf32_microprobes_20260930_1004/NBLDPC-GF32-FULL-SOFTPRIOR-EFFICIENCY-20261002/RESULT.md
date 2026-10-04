# EXPLORE result — accepted complete-source implementation match

Main accepts `FULL_SOFTPRIOR_IMPLEMENTATION_MATCH` on2026-10-02 after independent `mechanism_freeze_review` PASS. Batch UUID `dcaa868f-b094-4551-8458-0511003a4405`, machine root `workspace/gf32_full_eff_dcaa868f/`; accepted source replica UUID `cbe151fe-25f7-4990-8895-858091467e2b`, graph/source lineage `a9352bc1-ae56-443b-ae93-9dcfa85d4229`. Exactly one frozen execution, session4843/WSL PID49250, exit0; no sampling, rerun or default promotion. The packet's reviewer name census_review was administratively replaced by independent mechanism_freeze_review; the operator kernel_accel_design did not review/accept its result.

Both paths replayed all492 source calls (192 baselines+300 branches),984 actual calls total,62,786 iterations (31,393/path). All984 vectors/statuses/iterations/own-syndrome source checks and492 paired checks match. Each path reproduced all192 selected call pointers using ORIGINAL effective-prior scoring. Control142/candidate156 exact-and-own-syndrome, selected and raw-branch syndrome-valid-wrong0; paired both/candidate-only/control-only/neither142/14/0/36, per-graph increments +3,+3,+2,+3,+1,+2. These reproduce the same source result; they are not a new recovery sample or mechanism replication.

| Actual outer-call wall, seconds | Reference | Batched FWHT |
|---|---:|---:|
| Baseline192 calls | 33.007575 | 22.866655 |
| Full six-branch pipeline492 calls | 189.765893 | 131.343432 |
| Full / own baseline | 5.749162 | 5.743885 |

Paired full-path batched/reference ratio `131.343432/189.765893=0.692134`, approximately30.79% lower observed call wall on this saved192-frame replay. Decoder-runtime totals189.752449/131.329774s. The six-branch algorithm still costs about5.74 times its own baseline; this is implementation acceleration, not reduced branch overhead. Raw summary field `candidate_pipeline_to_control_wall_ratio=3.979191` compares batched FULL against REFERENCE baseline; it must not be substituted for either within-path overhead or paired full-path acceleration. Single-pass order/cache effects remain; no steady-state or pipeline-throughput claim.

Resource checkpoint321.634s, high-water RSS106,561,536B, first-pass artifacts275,904B; terminal275,906B before subsequent review/closeout log appends. No STOP/cap events. Original method accounting260syndrome bits/frame once,49,920bits per method/192frames, branch incremental disclosure0/tag0; local replay new disclosure0. Verification NOT_IMPLEMENTED/undetected NOT_MEASURED, not security certification.

Independent review directly reconstructed returned NPZ vectors, own GF32/poly37 syndrome/truth, original-prior valid-branch scores and choices/costs. Final-belief arrays were not persisted: their match relies on saved runtime predicates/maxdiff and inspected CLI; maximum recorded pair/source failed-baseline belief difference0. Fourteen explicit-fake tests passed, plus compile/T0/dry/branch/scoped-root checks; no broad regression or new scientific run was inferred.

This acceptance is limited to full saved-source implementation fidelity and bounded timing. No default replacement, real-data/n256/N2048, general FER/f_eff/SKR, significance, qualification, promotion, route decision or publication claim. Two fresh independent correction mechanisms (rank2 fallback and lambda=.5 mixed bias) have separate frozen EXPLORE packets and remain subject to their own test/dispatch/review gates. No commit/push/merge/archive.
