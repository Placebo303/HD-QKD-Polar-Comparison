# V80-P1 Rate-Adaptive Rescue — Design

Sources: `docs/research_cycles/V80-NBLDPC-JAN21/P1_PACKET.md` (+ parents listed there),
`docs/ROADMAP-20260921.md` §2–§4 + §8. Condensation only; no new numbers.

## Frozen accounting (quoted)

- n = 1024 GF(32) symbols, n_bits = 5120, H_full = 0.83256272, content = 852.544 b; f_super = (5·(m1+m2)+64)/852.544 ≤ 1.3 ⇒ leak ≤ 1108.31 b ⇒ m1+m2 ≤ 208.
- m_base = 200: leak 1064, f = 1.24803. Rescue total 208: leak 1104, f = 1.294947. Increment: 8 rows = 40 b. E[leak] = 1064 + 40·r; f_exp = E[leak]/852.544; f_eff = f_exp + 4.785675·FER (own blended basis).
- Deleted out-of-box arms: 202+8 = 210 rows (f = 1.30668); 200 two-segment = 216 rows (f = 1.34185).

## Frozen construction (nested, cold only)

- One matrix per instance (frozen A208 instance, pins carried). Base = rows [0,200); rescue transmission = rows [200,208); rescue decode = cold full-208 re-decode. Base ≠ P0's A200 (separate lineage; anchors are context).
- Prior/decoder: b2f verbatim (einsum marginal + row guard + XOR centering; v28 max_iter 300/streak 3; exact_match). No genie/argmax/L1. Warm-start forbidden.
- Blocks: 240 paired, seeds 2026095601+idx, stream `o1_blk:{seed}`. Rescue set = Stage-1 non-success exactly; `undetected`-class logged separately, never success.

## Gates / budgets / forbidden (freeze)

- (a) final 0/240 HARD (zero-failure-only certifiability scope); (b) f ≤ 1.3 own basis; (c) headroom ≥ 21.5 b (⇔ r ≤ 57.0%, required N ≤ 570). Stage-1 k/240 vs bar 12 = context only.
- Wall ≤ 3600 s/arm single window; per-call ≤ 300 s terminal; RSS < 2 GiB; fresh `workspace/p1_<uuid8>` roots; no resume/adaptive search; ≤1 engineering repair+rerun (infrastructure only, inputs unchanged).
- Forbidden: evidence-root touches; real data; constant/gate changes; cross-instance pooling; undetected-merging; f_exp-as-f_eff; warm-start; second matrix; two segments.

## Auth boundary

- Freeze consumes nothing. Execution needs Pre-EXECUTE Q0–Q6 + fresh explicit user grant per arm. One append-only EXPLORATION_LOG.md + one batch-end independent review. PASS ⇒ P3→P5 path; FAIL ⇒ P4-mandatory path (roadmap §4 tree). Neither path is authorized here.
