# V80-P1 Rate-Adaptive Incremental-Syndrome Rescue — Proposal

- Charter: `docs/ROADMAP-20260921.md` §3 P1 + §4 decision tree (main-thread DECISION-1/2, 2026-09-21).
- Packet: `docs/research_cycles/V80-NBLDPC-JAN21/P1_PACKET.md` (Acceptance ID G-P1, frozen NOT granted) + `P1_PROMPT.md`.
- Track: EXPLORE synthetic (EXPLORE_HEAVY cost annotation). This change itself authorizes no execution and consumes no budget; arm execution needs a fresh explicit grant + Pre-EXECUTE; batch-end review closes the batch.
- Scope anchor: main route per DECISION-2 = rate-adaptive (incremental syndrome) NB-LDPC; P1 is its highest-priority step. Joint A2 is demoted to a P4 construction sub-arm and is explicitly NOT in this change.

## Why (what changed)

- Decodability at m = 208 is settled synthetic (soft-marginal F208 0/240 on BOTH construction instances 2026092001/2011); the binding constraint is budget headroom (A208 headroom 4.31 b < one 5 b row) and certifiability (A208 needs N ≥ 2842 zero-fail blocks; pool total only 2103).
- The L2 cliff (genie: 8 rows move FER 10.5% → 0.83% between m2 = 192 and 200) plus enacted cold-decode rescue evidence (all soft-marginal F202 failures lie in frame sets the m = 208 code decodes at 0/240) make "m_base = 200 + single Δm = 8 rescue" the only in-box rate-adaptive arm (m1+m2 ≤ 208 hard cap deletes m_base = 202 and two-segment variants).

## Scope (frozen)

- Two arms P1-R1/P1-R2 (instances 2026092001/2011, reported separately, NO pooling); each = Stage 1 baseline-only (leading-200 submatrix, cold) + Stage 2 rescue (rows [200,208), cold full-208 re-decode of Stage-1 failures only).
- Gates: (a) final fails/240 = 0 HARD; (b) f ≤ 1.3 own basis; (c) headroom 1108.31 − E[leak] ≥ 21.5 b. Budgets: wall ≤ 3600 s/arm, per-call ≤ 300 s, RSS < 2 GiB, no resume/adaptive search.
- Claim ceiling: synthetic paired frames; rate-adaptation efficiency only.

## Non-goals

- No FER/SKR/qualification/publication/real-data claim in this change.
- No joint-A2, frame-length (P4), memory-audit (P3), throughput (P6), or nested-code-optimality work.
- No prediction of the m = 200 baseline FER (measured outcome, [TO BE MEASURED]).

## Affected specs

- `specs/v80-p1-rate-adaptive-rescue/spec.md` (delta: rescue procedure, gates, budgets, forbidden list).

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved to the consolidated baseline; retained for history. No new OpenSpec change created (consolidation is documentation-only).
