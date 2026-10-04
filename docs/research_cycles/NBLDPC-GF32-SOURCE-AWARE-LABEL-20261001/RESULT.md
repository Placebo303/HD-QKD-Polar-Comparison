# Retained failed attempt — source-aware GF32 edge labels

Batch UUID: `f6fbf8cf-8773-4099-af68-54136326b60d`  
Disposition: **CLOSED / RETAINED FAILURE / INCOMPLETE**.

The dispatched attempt stopped at predecessor loading with
`PREDECESSOR_STOP`: `comparison_bench.cli.nbldpc_gf32_cycle_census` has no
`load_predecessor` attribute. The six fixed control graphs had already been
constructed and admitted at GF(32) rank 52, so this was not a zero-graph
attempt. The failure occurred before any cycle inventory was loaded and before
the source-label search began.

Label trials, affected-cycle evaluations, full-reference evaluations,
decoder calls, frame rows, and actual syndrome disclosure were all zero.
Control/candidate successes, delta, per-graph performance and paired states
are unknown (`null`); no performance or objective result was measured. The
terminal `INCOMPLETE` classification records a failed prerequisite, not zero
performance or a negative scientific result.

Wall time was 49.0868816 s. Maximum sampled RSS was 101711872 B across 27
samples. Maximum decoder-call time is null because no call occurred. Integrity,
resource and authorization violations were zero. The existing four machine
artifacts under `workspace/gf32_source_label_f6fbf8cf/` remain retained; this
closeout does not rewrite them.

Independent `faithful_scope` failure review found the previous implementation
record overstated P1 loader coverage: tests did not exercise the accepted
predecessor loader binding. That P1 loader-coverage PASS is withdrawn. Main
accepts this batch only as a retained failure record. No source-label gain or
no-gain result, mechanism rejection, route decision, qualification, FER,
`f_eff`, or SKR conclusion follows. No rerun, repair, promotion, commit, push,
merge, or archive is performed by this closeout.
