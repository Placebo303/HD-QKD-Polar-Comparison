# V29 archive note

Archived locally on 2026-08-20 after the main-thread closeout review.

- Canonical `run_02` stopped by explicit user authorization after 9 persisted
  1M blocks: exact=1, tag_verified=1, remaining=91, maximum possible=92<95.
- Terminal: `v29_finite_gate_fail` with `early_fail_proof` and
  `user_authorized_stop=true`.
- `readonly_verify.json`: `ok=true`, `decoder_rerun=false`.
- Prefix FER is `observed_prefix_only`, not a full-300 FER.
- `run_01` is retained as superseded 0-call `implementation_blocked` evidence;
  neither run is a qualification or promotion result.
- The next route is the independent V30 projective-safe finite-graph gate;
  V30 remains `DRAFT_PENDING_FREEZE_REVIEW` and has not executed.
