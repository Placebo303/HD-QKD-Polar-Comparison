# Tasks

- [x] Inspect current lifecycle and existing V64 stop semantics.
- [x] Freeze A1-A6 before implementation.
- [x] Implement A1-A5 in the one allowed analysis script.
- [x] Run self-check and retrospective analysis (zero decoder calls).
- [x] Independent A6 numerical/scientific review and read-only memory triage.
- [x] Report results and prioritize one-factor follow-up experiments.

Validation: `python scripts/analyze_v64_stage_ablation.py --self-check` and default execution PASS. Independent luna reviewer `stage_ablation_check` rechecked final code and outputs after correcting L2 undetected semantics and exclusive outcome partitioning. Luna `ablation_options` completed read-only memory triage; no long-term memory written. Acceptance is limited to this retrospective analysis, not source-run qualification or new decoder execution.

No formal decoder run, qualification, or promotion is included.
