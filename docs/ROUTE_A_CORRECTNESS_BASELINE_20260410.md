# Route A Correctness Baseline (2026-04-10)

Current authoritative result roots remain:
- `results/_tmp_longrun_fresh_rerun`
- `results/_tmp_minrerun_stageC_security_20dB`
- `results/_tmp_minrerun_stageD_cross_loss`

Current correctness state before formal universal-hash verification:
- `verification_bits_used_actual` is still mainly sourced from configured CRC budget on SCL rows
- `verification_source_tag` is therefore mostly `configured_budget`
- `leak_EC` already includes actual replay syndrome leakage and current verification budgeting
- current `epsilon_EC` is only a replay-audit empirical fail-rate style quantity
- current correctness wiring is useful for audit and compare, but is not a strict Zhong 2015 or Niu 2016 instantiation

Safe wording for the pre-formal baseline:
- `actual replay leak + actual sidecar frame-level accounting + finite-key calibrated Zhong-like security`
