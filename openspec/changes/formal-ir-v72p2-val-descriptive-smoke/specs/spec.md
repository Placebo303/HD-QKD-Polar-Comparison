# V72P2 delta specification

## ADDED Requirements

### Requirement: fixed non-fresh smoke
The runner SHALL select only CAL702..1725 and the preassigned VAL1726..1761 of 20260123_1M_600k_0dB under the design's256-pair/4-frame mapping. Prior fitting and CV SHALL use CAL only. All claims SHALL be descriptive/non-fresh.

#### Scenario: missing seventh frame
Given a missing or invalid assigned smoke frame, its block SHALL be INVALID_INPUT without replacement by a later frame. Nine assigned slots remain visible.

### Requirement: actual incremental budget
The runner SHALL check budget before communication, slice the frozen CSR, warm-start only within a block, and count actual completed iterations from residuals.

#### Scenario: remaining two iterations
Given718 used iterations, the call SHALL receive max_iter2; a valid candidate at720 SHALL still be checked. A subsequent zero-budget checkpoint SHALL send/call nothing.

### Requirement: current readout
The adapter SHALL return APP/hard/syndrome from final c2v and self-excluded local factors; first warm residual SHALL be the true message delta. No new check-update iteration is charged for readout.

#### Scenario: nonzero incoming c2v
Given warm messages w, the first residual SHALL equal max(abs(returned_c2v-w)) for one iteration, not max(abs(returned_c2v)).

### Requirement: protocol versus oracle
Only the current finite syndrome-and-tag candidate SHALL stop. Offline Alice equality SHALL not affect the prior or stopping; accepted-wrong SHALL be isolated from exact-success counts. Tag uses the predecessor64-bit protocol; no information-theoretic security bound is claimed.

### Requirement: monotonic public accounting
First publication SHALL charge160 syndrome+64tag; subsequent checks SHALL charge one CONTINUE and only new syndrome rows. Failures SHALL preserve counters. leak_IR and public-control counts SHALL remain separate. All model-relative ratios SHALL use selected CAL-CV CE fixed before smoke; posthoc smoke CE SHALL not replace it.

### Requirement: bounded additive execution
Only the exact reviewed implementation SHALL run once after Pre-EXECUTE, in the frozen new directory. All9 assigned outcomes and partial failures SHALL be retained; no real rerun, other source, overwrite, confirmation or promotion is authorized. Pre-RESULT SHALL precede result commit.
