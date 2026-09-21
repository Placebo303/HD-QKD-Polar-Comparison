# V80-X1 Cross-Source Cliff & Generality Baseline — Proposal

- Charter: user strategic directive 2026-09-21 (anti-cherry-picking: test the WORST source, not the best) + F-1 closure `workspace/p3_census_3954637c/DESIGN_POINT_ARITHMETIC.md` (corrected H/m_max verdicts).
- Packets: `docs/research_cycles/V80-NBLDPC-JAN21/X1_CROSS_SOURCE_PACKET.md` (Acceptance ID G-X1, frozen NOT granted) + `X1_CROSS_SOURCE_PROMPT.md`; consumes into `P1_PACKET.md` §9 (amendment A-X1-20260921).
- Track: EXPLORE synthetic (EXPLORE_HEAVY cost annotation: 15 arms). Per-source channels derive from already-measured A1-census histograms — NO new real-data read, no `.ttbin` access authorized. This change itself authorizes no execution and consumes no budget; arm execution needs X1 evidence + Pre-EXECUTE + fresh explicit grant; batch-end review closes the batch.
- Scope anchor: all existing cliff data (A188–A208 genie + soft-marginal) is on the 2M frozen channel only; m_min is UNMEASURED for every source. X1 measures the soft-marginal FER-vs-m cliff per source so P1's per-source base rates come from evidence.

## Why (what changed)

- Corrected H_full (MM): 1M 0.80361 / 1.5M 0.82896 / 2M 0.83458 ⇒ corrected m_max 201 / 207 / 209→cap 208. 1M is OUT@208 (genuine, ~9σ) but IN@200/199; 1.5M INDETERMINATE@208 (inside CI) but IN@200/199; 2M IN@208. The frozen A208 design point does not transfer across sources — each source needs its own measured cliff.
- Generality framing: the algorithm claim is generality across sources; the evidence anchor is the WORST source (1M). A 2M-only headline is cherry-picking and forbidden.

## Scope (frozen)

- 15 arms: 1M {185,189,193,197,201}; 1.5M {191,195,199,203,207}; 2M {192,196,200,204,208} (top = own corrected m_max, cap-bound for 2M); 240 paired blocks each, frozen seeds `2026095601+idx`, single instance 2026092001, standalone per-m constructs, per-source channel bundles, b2f prior/decoder.
- Gates: (a) fails/240 ≤ 12 route gate; (b) f_super ≤ 1.3 own corrected H; (c) N ≥ ceil(3·4.785675/(1.3−f_super)) — expected to FAIL essentially everywhere; no single-source f_eff is certifiable.
- Budgets: wall ≤ 1800 s/arm, per-call ≤ 300 s, RSS < 4 GiB, no resume/adaptive search. Total ceiling 27000 s.
- Claim ceiling: synthetic per-source FER curves only; establishes no generality claim by itself.

## Non-goals

- No FER/SKR/route/qualification/publication/real-data claim in this change.
- No P1 rescue execution, no P2 curve re-measurement (overlap scheduled once, consumed by reference), no nested-code-optimality work.
- No prediction of any arm's FER (all measured outcomes, [TO BE MEASURED]); 1M/1.5M bundle materialization is entry work, not a scientific result.

## Affected specs

- `specs/v80-x1-cross-source-cliff/spec.md` (delta: per-source cliff procedure, grids, gates, budgets, forbidden list).
