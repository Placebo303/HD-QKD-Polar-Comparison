# S2 Fallback Options Memo (2026-09-20) — EXPLORE planning-only

- Track EXPLORE planning-only. Branch `formal-ir-v72p1-addendum-clean`. NO code, NO execution, NO authorization, NO S3 entry.
- Gate unattained under frozen mechanics (n=256, m2=47, fixed constructor, v10 decoder, empirical channel, genie-u1): L-A 7/16, L-B 13/16, L-C 16/16 frame FER; group 4/4 each; f_super 1.2246 budget-pass (S2C_RESULT_20260920.md).
- Gate = group FER<=5% (<=3/60) AND f_super<=1.3 (S2C_EXPERIMENT_PACKET §5; PROGRAM_PLAN §S2; S2_ACCOUNTING_MAP). Anchors: H_full=0.83256272, content_1024=852.544, budget=1108.31, headroom 64.31 bits.
- Stopping rule is not the cause (triage A2: 15/16 never syndrome-valid to 300 iters even streak=inf; S2C L-C fast-fail 3-7 iters). QSC cliffs 0.05 L-A / 0.06 L-B/L-C on 4 seeds (S2B_FAILURE_TRIAGE; S2B_DV_STUDY).

## O1. n=1024 single code (superframe-as-code)
- Spec-gap: changes code length 256->1024; S1 ensemble is rate-defined so MC-DE must be re-run at new length/rate (new arm); constructor n=1024 support UNCHECKED (v10_peg range not verified this turn — uncertainty).
- Cost: new DE + new construction + longer decodes (~4x frame work; S2C arms ran 16-48 s/16 decodes, so still small vs 3600 s window).
- Budget math (derived): leak=m*5+64<=1108.31 -> m<=208 rows, rate 1-208/1024=0.797. Scaled m=4*47=188 -> leak 188*5+64=1004 -> f=1004/852.544=1.178 (in budget, headroom ~104 bits). Finite-length gain expected at 4x length but unquantified — no FER promise.
- Risk: largest science change; invalidates S1->S2 chain continuity; needs fresh packet.

## O2. Keep 4x256, bump m2 within budget
- Spec-gap: none on machinery; only m_total 49-><=52. Derived: m_total=52 -> leak 4*52*5+64=1104 -> f=1104/852.544=1.2950<=1.3 (headroom ~4 bits; D_blind sensitivity 16 bits=+0.019 eats headroom — tight).
- Cost: cheapest (same constructor/decoder, +3 rows/frame = +6% redundancy, one re-DE point or reuse + new construction arm).
- Expected impact LIMITED: QSC cliff needs >>6% redundancy (failures are wrong-lock/cns, not near-miss; defect review: proxy f in own terms was 1.719, not marginal). Justify: do not promise gate from +6%.
- Risk: burns nearly all f headroom; any blind-round disclosure pushes over budget.

## O3. Decoder-side (iters / variants)
- Spec-gap: none on code; iter cap or variant swap only.
- Cost: cheapest compute-wise. Expected gain SMALL: triage shows 15/16 failures never reach valid syndrome by 300 (A2 max_iter, never valid); S2C medians 22/14/5 iters with 2 total 300s — iters not binding. Streak 3->10 recovered only 1 frame class (...016).
- Risk: variant-hopping without hypothesis; keep only as piggyback arm, never standalone route.

## O4. lambda re-selection on EMPIRICAL channel, larger N
- Spec-gap: current 16-frame ranking is noise: QSC dv-study ranks L-C best (4/4/2/0 vs L-A 2/2/1/0 at p<=0.06), empirical genie-u1 ranks L-A best (7/16 vs 13/16 vs 16/16) — REVERSAL across channels (S2B_DV_STUDY vs S2C_RESULT).
- Cost LOW: 32-64 frames/arm controlled scan before any lambda conclusion; same machinery, no DE rebuild.
- Expected impact: de-noises ranking; does not itself lower FER. Required before O2/O1 lambda choice.
- Risk: none scientific; only small window cost. Uncertainty: empirical sampler seed block must stay paired/fresh.

## O5. PA-aware accounting (Tauz ITW2024)
- Spec-gap: redefines success as subset-decode at fixed leak (Thm1: full-rank complement + cond-independence); S2 gate becomes subset-FER; S3 yield bookkeeping changes (LITERATURE_PA_AWARE.md; PROGRAM_PLAN §2.4 deferred-S3 tag).
- Cost: framework adoption + construction constraint (Block-MDS) + re-proof under our tag/leak books — NOT an S2 construction fix.
- Expected impact: relaxes f<=1.3 pressure at S3 level; zero effect on current 4/4 group FER under full-decode gate.
- Risk: misfits (demo rate 0.2-0.4 vs ours 0.89-0.91; n~2000 vs 256; cond-independence untested on Jan-21). Keep as S3-level reframing, not blocking S2.

## O6. Pause / close NB route
- Spec-gap: none. Cost zero. Impact: preserves negative result (genie-u1 ceiling fails at 4/4 groups) as route evidence; frees effort.
- Risk: premature if O4+O2/O1 cheap arms unrun — close only after those report.

## Ranked recommendation (no execution; user decides)
1. O4 first (cheap, de-noises lambda; gates O1/O2 choice). 2. O2 piggybacked on O4 (same machinery, tests redundancy slope within budget). 3. O1 next only if O4+O2 still far from gate (needs new DE arm + n=1024 constructor check). O3 piggyback only. O5 as S3-level reframing in parallel docs, never blocking S2. O6 if O4+O2 and O1 scoping both fail.
- No authorization requested or granted; no S3 entry; next step needs a frozen packet + explicit grant.
