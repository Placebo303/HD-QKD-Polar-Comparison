# Tasks

Track: DECIDE. Implementation and fake tests only; no batch execution.

- [x] W-1 Preserve the current `run_pair` caller contract while exposing each
      attempted arm's wall time and stopping before an unattempted second arm
      when the first breaches its cap.
- [x] W-2 Make future `frame_records.csv.wall_s` a measured per-chain value;
      enforce single-chain ≤120 s per attempt and total wall ≤7200 s per run.
      Keep the existing schema and all scientific inputs/decoder behavior.
- [x] W-3 Add focused fake-clock/fake-decoder checks for distinct arm times,
      first-arm stop with no fabricated second row, second-arm stop, aggregate
      budget, and unchanged ordinary pair results. No production decoder path
      may be entered by tests.
- [x] W-4 Independently review the scoped diff, relevant tests, old-root
      immutability and n256 output absence; then merge this delta into the live
      spec and replace the live file's stale "Spec delta" heading. Leave the
      archived frozen delta unchanged. No commit/push.

Independent review: W-1..W-3 PASS after correcting the exact-7200s
pre-chain boundary; W-4 live-spec merge and heading correction completed.
This is implementation acceptance only, not scientific execution authority.
