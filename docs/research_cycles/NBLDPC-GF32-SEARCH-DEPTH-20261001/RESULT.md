# Result — fixed-graph label-search depth probe

**Track:** EXPLORE. **Batch UUID:** `21cc2d44-6aa6-4619-b8e2-7f95615bebe2`.
**Machine root:** `workspace/gf32_search_depth_21cc2d44/`.
**Terminal:** `NO_SUFFICIENT_SIGNAL` under the frozen practical screen.

This batch compared the accepted one-pass labels (`onepass`) with deeper
deterministic coordinate sweeps (`deep`) on six fixed synthetic GF(32)
graphs. It used p0=0.55, the frozen historical nonzero marginal shape as an
iid Bob-zero proxy, and no pilot. This is a finite synthetic observation for
the frozen setup, not a route verdict or a family-level result.

## Search and graph checks

All six graph and candidate admissions passed, including the frozen degree
profile, support and degree preservation, GF(32) rank 52, and column-gauge
checks. The deep search ended by `NO_CHANGE` on every graph after respectively
4, 5, 6, 5, 4, and 4 total sweeps; each final sweep changed zero labels. The
deep-minus-onepass objective increments J were 0.257821753652, 0.359428366612,
0.412678706360, 0.461394163165, 0.318499858253, and 0.287716897104 bits for
graph seeds 2026093901–2026093906. Maximum recorded adjacent/reference J
drift was at most 5.7e-14 bits. No rollback was applied.

## Paired execution and frozen screen

The complete holdout contained 192 pairs and 384 decoder calls. Onepass had
146 exact-and-syndrome successes and deep had 149, for Δ=+3. Paired states
both / candidate-only / control-only / neither were 136 / 13 / 10 / 33.
Per-graph onepass→deep counts for seeds 2026093901–2026093906 were
27→28 (+1), 23→21 (−2), 19→20 (+1), 27→28 (+1), 25→26 (+1), and 25→26 (+1),
so 5/6 graph differences were positive.

The control count 146 was within the frozen 39–153 interval, and the 5/6
positive-graph gate passed. The frozen Δ≥12 gate failed at +3, giving the
mechanical terminal `NO_SUFFICIENT_SIGNAL`. The small positive total and
mixed per-graph counts do not establish a search-depth mechanism benefit or
causal mediation, and do not negate the NB-LDPC route.

There were 384 calls, 260 disclosed syndrome bits per call (99,840 total),
tag bits=0, wall time 115.787441 s, maximum call time 0.572914 s, and peak
RSS 102256640 bytes. Integrity, resource, and authorization violations were
all zero. Syndrome-consistent wrong rows=0; verification is
`NOT_IMPLEMENTED` and undetected errors are `NOT_MEASURED`, so this is not a
physical-undetected-error result.

## Independent review and claim limits

Independent reviewer `faithful_scope` (not operator `faithful_contract`)
passed batch-end items P1–P7. Main-thread acceptance is limited to this
frozen synthetic iid marginal-shape observation and its mechanical
`NO_SUFFICIENT_SIGNAL` classification. The four machine artifacts do not
store sampled truth/prior arrays: review checked paired keys, shared-seed
roles, formula, and arm order, but cannot reproduce those vectors
value-by-value from the artifacts.

Do not pool or rank this batch against earlier batches. It does not establish
a conditional-channel or source-faithful result, FER, `f_eff`, SKR,
throughput, qualification, publication, route conclusion, or causal
mediation. The one-shot user grant is consumed; no extra frames, rerun,
repair, restart, or successor batch is authorized. No commit, push, merge, or
archive was performed.
