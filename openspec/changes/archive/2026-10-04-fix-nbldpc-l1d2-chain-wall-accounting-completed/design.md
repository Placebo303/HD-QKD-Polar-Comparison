# Design: per-chain wall measurement

Track: DECIDE. This is a narrow correction to the already completed Stage-2
runner, not a scientific rerun.

1. Time each `run_pair` arm around its own complete synchronous layered chain
   (L1 and, when invoked, L2, plus the existing transfer/verification work).
   Future frame `wall_s` is that arm's elapsed wall time. Preserve the existing
   24-column CSV order, paired inputs, decoder configuration, syndrome and
   leakage calculations, and existing callers of `run_pair`.
   Future manifests may add `pair_timings` for each started pair's elapsed
   time and actually attempted arms. That diagnostic does not determine the
   single-chain cap or alter any frame row.
2. Keep pair and batch elapsed times separate. The 120 s cap is compared to
   each attempted chain's measured time. The 7200 s cap retains its existing
   batch timing boundary, from `execute_pairs`' current `t_batch` start through
   the decode loop; model/prior/graph setup and STOP-result persistence remain
   outside that clock. A synchronous layered chain can only be classified after it
   returns; this is not a preemptive timer.
3. If the first chain returns over its cap, record its attempted disclosure and
   `resource_abort`, set an explicit stop reason, and do not start the second
   arm or another pair. Do not create a frame row for an unattempted chain.
   If the second chain breaches, retain both attempted rows and stop. The
   stopped run is incomplete; it cannot supply a zero-failure denominator or
   trigger a next arm.
4. A cap breach is a resource violation under the existing COND-3 rule. Keep
   all existing non-resource success, `accepted_wrong`, syndrome, transfer,
   and per-source semantics unchanged.
5. Preserve the old n128 root and acceptance. Its `wall_s` is historically
   **pair** elapsed time in both rows, so its maximum 3.55 s is a maximum pair
   time. Since that pair time is below 120 s, both chains were within the
   single-chain cap, but their separate times cannot be reconstructed.

Implementation may use an optional timing/cap argument or a small timed entry
point so existing `run_pair` callers retain their return shape. No general
timing framework or artifact-versioning system is needed.
