# Correct L1D2 chain wall accounting

Track: DECIDE. Status: implementation proposal; no scientific execution authorization.

The completed n128 batch met its resource caps, but its runner measured one
control-plus-candidate pair and stored that elapsed time in both `wall_s` rows.
It also compared the pair time with a frozen **single-chain** 120 s cap. This
made the reported maximum a pair time and could abort a future pair even when
both chains were individually within the cap.

Change only future runner timing and cap enforcement. Preserve the completed
`workspace/nbldpc-l1d2-s2c-n128-b07b0f91/` machine artifacts and the archived
change verbatim. The completed batch's COND-3 NOT MET, authorization, seeds,
model, graph, decoder and claim ceiling do not change. This change does not
grant another batch, n256 or real-data execution.

Implementation scope: `comparison_bench/src/comparison_bench/cli/
nbldpc_l1_degree2_driver.py`, `nbldpc_l1d2_synth_batch.py` and focused fake
tests. The live `openspec/specs/synth-batch-runner/spec.md` receives the delta
after implementation and review and its merged-spec heading is made accurate;
the archived delta stays untouched. Cycle
RESULT/acceptance text correction is a separate docs-only closeout.

No code in the frozen Polar baseline, source model, graph construction, or
decoder kernel is changed. No output column name/order is changed.
