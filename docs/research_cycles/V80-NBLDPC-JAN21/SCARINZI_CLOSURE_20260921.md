# Scarinzi 2025 Route Closure (2026-09-21) — zero-execution trigger evaluation at the frozen V80 design point

- Track: documentation-only (AGENTS.md §1.2 matrix; no track gate). Zero execution: no new run, no decode, no real-data read — the triage §5.3 trigger condition is evaluated with EXISTING b2f report-only measurements only. Branch `formal-ir-v72p1-addendum-clean`; this note authorizes nothing and changes no frozen quantity.

## 1. Trigger condition (from triage §5.3)

Before any per-block-vs-pooled packet, the triage set a ZERO-DECODE probe: does the per-block vs pooled entropy spread rewrite the m budget? (`LITERATURE_RECOMMENDATION_TRIAGE_20260921.md` §5.3 item 1; decision-log 2026-09-21 §5 entry). The probe data already exists in b2f's report-only `prior_entropy_bits` column; this note reuses it — no new measurement was performed.

## 2. Evidence (b2f report-only, 240 paired blocks, seeds 2026095601+idx)

- Per-block marginal-prior entropy: mean 852.5332 / p50 852.5606 / p90 853.8280 / p99 855.0620 / max 855.6549 b vs pooled H_full·n = 852.544 b; identical in F202 (paired frames, same (b,u1) marginal; column never gated).
- Spread arithmetic: p99−p50 ≈ 2.5 b; max−mean ≈ 3.1 b per 1024-symbol block (≈0.35% of Ĥ).
- A Scarinzi-style per-block rate allocation (m_block ∝ H_block) could shift at most ~±0.7 of 208 rows per block, i.e. ≤~0.4% of the 1104-b leak (f_super 1.294947 → ≈1.2904 at best) — no usable headroom against the frozen 1.3 gate or the ~278-b leak−content margin.
- No block-cluster structure an allocator could exploit: u1_mismatches mean 8.083 (max 17); F202's 6/240 fails (seeds 2026095630/5638/5686/5698/5803/5834) spread across quarters 2/2/2/0.

## 3. Other closure arguments (from triage §5.2, cited)

1. Mechanism isomorphism: Scarinzi's predefined decreasing-rate sequence with progressive lowering on decode failure is the same mechanism as our v52/v54/v55 conditional HARQ (base → stage1 Δm=8 → stage2 Δm=8) — no mechanism gap to close.
2. Scale + denominator: their λ_IR advantage "emerges only for very large block sizes" (N_bl=460800 bits vs our 5120-bit superframe, ~90×) and their f uses a binary-entropy denominator without tag → not comparable to our frozen f_super (same situation as IEEE 11440984).

## 4. Conclusion (machine-style, bounded)

Trigger condition NOT met at the frozen design point (n=1024 GF(32), superframe accounting, empirical γ from the 2M bundle): the per-block entropy spread (≈3 b/block, ≈0.35%) cannot rewrite the m budget, and Scarinzi-style per-block rate adaptation offers no usable efficiency or reliability headroom. Route remains CLOSED for this design point; this evidence warrants no per-block-vs-pooled packet.

**Does-not-establish**: other block sizes / channel regimes / binary BSC settings not covered; no new measurement performed (reuses b2f report-only columns, never gates); the borrowing remains valid — IR side instantaneous reliability / security side average QBER mirrors our gate/claim layering, and code selection by mean channel capacity ≈ per-block Ĥ (not mean QBER); this note authorizes nothing and changes no frozen quantity.
