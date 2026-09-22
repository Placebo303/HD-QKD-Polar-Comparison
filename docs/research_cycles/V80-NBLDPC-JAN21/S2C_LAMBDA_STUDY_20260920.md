# S2c Lambda Study (2026-09-20) — EXPLORE diagnostic, OBSERVATIONS ONLY

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean`. O4+O2 probe per S2_FALLBACK_OPTIONS (O4 de-noise + O2 m2=50 slope). NO gate, NO early-stop, NO verdict.
- Design: 64 frames/arm PAIRED (seeds 2026097501+idx, idx 0..63; rg-absence clean 2026-09-20 over src/tests/docs/openspec/.workbuddy/.codebuddy/scripts; 2026098xxx/90xx/6xxx avoided). Frozen S2c semantics read-only (2M γ/p_b triple, genie-u1, y=b&31, `decode_error_domain_posterior`, max_iter=300/streak=3). A50 (λ{2:1}, m2=50) built study-local via same primitives (peg+make_rho+reconcile); f_super=1104/852.544=1.2950 info only. Executor: `formal_ir/v80_s2c_lambda_study.py` (176 lines); raw `/tmp/opencode/s2c_lambda_study.json`.
- Construction (seed 2026092001 ×20): A47 fc=0 g=6 r=47; B47 fc=0 g=6 r=47; C47 fc=2 g=4 r=47 (all match S2c pins); A50 fc=0 g=6 r=50, ρ{10:0.74,11:0.26}.

| arm | frame ok (N=64) | Wilson 95% CI | grp-of-4 (ref) | iters min/med/max | n300 |
|---|---|---|---|---|---|
| A47 λ{2:1} m47 | 33/64 | [0.396, 0.634] | 1/16 | 7/22/300 | 8 |
| B47 λ{2:0.5,3:0.5} m47 | 10/64 | [0.087, 0.264] | 0/16 | 8/16/300 | 2 |
| C47 λ{3:1} m47 | 0/64 | [0.000, 0.057] | 0/16 | 3/6/10 | 0 |
| A50 λ{2:1} m50 | 56/64 | [0.772, 0.935] | 9/16 | 5/9/300 | 8 |

- Paired differentials: A50⊇A47 successes (A47-only 0, A50-only 23); A47⊇B47 nearly (24 vs 1); C47 ok on nothing (all C47-vs-* second_only 0/0/0 vs 33/10/56). CIs pairwise non-overlapping; frame ordering A50>A47>B47>C47 at N=64.
- Cross-refs: S2c FAIL stands (4/4 group FER all arms, gate ≤3/60). Empirical ordering (A>B>C) REVERSES the QSC dv-study ranking (C best, S2B_DV_STUDY) — channel dependence confirmed as observation, mechanism unexplained. C47 fast-fail signature repeats (3–10 iters, 0 n300).
- NO causal claim (no λ-optimality, no gate-pass, no route decision); group counts reference only; f_super values budget-mapping. Wall 648 s. Pending user route review (O1/O2/O6 per fallback memo).
