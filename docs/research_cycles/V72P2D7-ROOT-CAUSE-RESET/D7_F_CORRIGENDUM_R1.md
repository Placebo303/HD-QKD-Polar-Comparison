# D7-F corrigendum R1 — terminal label interpretation

> Authority: D7 root-cause and route-reset R1 packet §7 A04 and §4.
> This file is additive. It rewrites no historical artifact and changes no
> historical terminal string.

## Correction

`D7_F_REVERSE_ORDER_REGRESSION` remains the historical machine label of the
accepted D7-F result. It is **not** an immutable general mechanism fact.

The accepted interpretation is narrow and single-graph:

- one graph pair (L1 `2026090501`, L2 `2026090502`);
- n = 16 paired blocks (`2026091300..2026091315`);
- f = 1.2 paired table: candidate-only 0, reference-only 2, both 0,
  neither 14;
- exact two-sided McNemar/binomial test on the 2 discordant pairs with
  `p = 0.5` under `p=0.5` (minimum tail `P(X <= 0) = 0.25`, doubled and
  capped at 1).

The terminal name is a pre-registered classification for that graph and
sample; it is not statistical confirmation of a general reverse-order
mechanism, and it does not license claims about other graphs, block lengths,
decoders, or route outcomes.

## Consequences

- Historical G1/D7 artifacts, manifests, summaries, tables, reports, and
  authorization records are retained byte-identical.
- Future citations of D7-F must carry the single-graph, n=16 paired scope
  and the weak evidential status of the 2 discordant pairs: reference-only
  2 / candidate-only 0.
- The multi-graph diagnostic in this change exists precisely because that
  single-graph terminal wording does not generalize by itself.
