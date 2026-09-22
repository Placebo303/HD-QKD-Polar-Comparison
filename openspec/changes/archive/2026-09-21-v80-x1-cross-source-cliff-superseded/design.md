# V80-X1 Cross-Source Cliff — Design

Sources: `docs/research_cycles/V80-NBLDPC-JAN21/X1_CROSS_SOURCE_PACKET.md` (§§1–8),
`P3_A1_REVIEW.md` (§5/§7, findings F-1/F-4/F-5), `P1_PACKET.md` (§§3/5 gates, §9 consumer),
`P2_PACKET.md` (§3 single-instance precedent), `B2F_RESULT_20260921.md` (lineage + cost bracket).
Condensation only; no new numbers.

## Frozen accounting (quoted)

- n = 1024 GF(32) symbols, tag 64 b; corrected H: 1M 0.80361 / 1.5M 0.82896 / 2M 0.83458; content = 1024·H = 822.897 / 848.855 / 854.610.
- f_super(m) = (5m+64)/content on the arm's OWN source H; m_max(H) = floor((1.3·1024·H−64)/5) = 201 / 207 / 209→cap 208.
- f_eff = f_super + 4.785675·FER (own basis, never quoted as f_super when FER > 0). N_req = ceil(3·4.785675/(1.3−f)) ≈ 15438 / 2708 / 1754 at own m_max — all ≫ 911.

## Frozen measurement design (standalone, cold only)

- One standalone construct per (source, m) @instance 2026092001 (NOT P1 nested submatrices; X1-*-S<m>-standalone labels). Base grid §3 of packet; 240 blocks `2026095601+idx`, stream `o1_blk:{seed}` (integers reused; draws differ per channel; no cross-source frame identity).
- Prior/decoder: b2f verbatim (einsum marginal + row guard + XOR centering; v28 max_iter 300/streak 3; exact_match). No genie/argmax/L1. Per-source bundles: 2M frozen `gamma_f03.npz`+pb read-only; 1M/1.5M [BLOCKING] derived from A1 histograms, no `.ttbin`.
- Overlap rule: b2f F202/F208 = cross-batch consistency checks (never pooled); X1-2M m=200 standalone ≠ P1 Stage-1 nested-200 (both labeled, never equated); X1-2M {192,196,204} vs P2 arm (ii) scheduled ONCE.

## Gates / budgets / forbidden (freeze)

- (a) fails/240 ≤ 12 (route gate, not certifiability); (b) f_super ≤ 1.3 own corrected H; (c) N-rule (fails essentially everywhere; no certifiable single-source f_eff).
- Wall ≤ 1800 s/arm single window (total ≤ 27000 s); per-call ≤ 300 s terminal; RSS < 4 GiB; fresh `workspace/x1_<uuid8>` roots; no resume/adaptive search; ≤1 engineering repair+rerun (infrastructure only, inputs unchanged).
- Forbidden: any `.ttbin` read / both-member open; cross-source channel reuse; pooling across sources/m/instances; undetected-merging; f_super-as-f_eff; `src/` touches; P2/P3/Stage-0.5 packet edits.

## Auth boundary

- Freeze consumes nothing. 1M/1.5M bundles unblock entry; execution needs Pre-EXECUTE Q0–Q6 + fresh explicit user grant per arm. One append-only EXPLORATION_LOG.md + one batch-end independent review. X1 establishes NO generality claim alone; P1 §9 rescue on 1M is the generality evidence.
