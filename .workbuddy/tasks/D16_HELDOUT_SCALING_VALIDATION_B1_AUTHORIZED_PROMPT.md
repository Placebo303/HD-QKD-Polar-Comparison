# D16 Held-Out Scaling Validation — Batch B1 Authorized Prompt

I accept
`D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`
within its independently reviewed scope and explicitly authorize
`D16_HELDOUT_SCALING_VALIDATION_B1` once on branch
`formal-ir-v72p1-addendum-clean`, under:

`.workbuddy/tasks/D16_HELDOUT_SCALING_VALIDATION_B1_TASK_PACKET.md`

Treat D16 only as a held-out falsification test. Verify the three frozen
prediction files under
`workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`
and prove all outcomes remain `BLANK`. Never edit or refit them.

Only if every pre-dispatch check passes, execute exactly once:

```bash
.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a
```

This grant covers exactly 96 decoder calls and 22 setup units, with 900s wall,
120s/call, RSS <2GiB, one CPU process. It is consumed at command start. No
retry/resume/repair/search/tuning/replacement/prediction revision/model refit.

Obtain one independent batch-end review, compare pooled exact fractions to the
three frozen bands, and return
`D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`.

This grant does not authorize another D16 run, D17 model changes, D7-H, real
data, commit/push, route closure, or FER/leakage/SKR/qualification/optimality/
publication claims.
