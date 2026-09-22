# S2b Failure Triage (2026-09-20) — EXPLORE observations only

- Track: EXPLORE synthetic. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Authorization: user pre-authorization 2026-09-20; mandate: stopping rule and dv distribution evaluated SEPARATELY; no causal attribution, no route decision.
- Fixed basis: `construct_l2(seed=2026092001)` → four_cycles=0/min_girth=6/rank=47 (rebuilt here, 0.08 s); S2b channel QSC p*=0.081 sampler+prior, max_iter=300; probe `/tmp/opencode/s2b_triage_probe.py` (numpy 2.5.3); rows `/tmp/opencode/s2b_triage_{a2,a3}.json`. No repo code touched; no roots/results/outputs writes.

## Study 0 — stopping criterion (code facts, exact)
- `decode_fftqspa(..., max_iter, *, streak=DEFAULT_STREAK, ...)`; `DEFAULT_STREAK = 3` (fftqspa L66/L307-308). Seam exists on kernel + `decode_error_domain`; `smoke_decode_frame` (s2_peg L297-300) forwards NO streak (call L322-323) — probes bypassed it via the kernel seam (same-sample: identical `s2_smoke:{seed}` stream).
- Per iteration: `syndrome_ok = syndrome_of(...) == syndrome` (L423, checked EVERY iter, transcripted). `if syndrome_ok: status=STATUS_SUCCESS; break` (L434-436). Else `stability_streak>=streak → STATUS_CONVERGED_NO_SYNDROME; break` (L437-439; streak = e_hat-stability, NOT soft convergence).
- `success` ⟺ error-domain syndrome `H*e_hat==s_e` at break iter. Wrapper adds `reconstruction_ok=(H*x_hat==s_x)` (L527) separately; docstring "Success requires the syndrome identity AND the reconstruction identity" (L496-497). Campaign gate uses `exact_match=(x_hat==alice)`.

## Study A — stopping rule (same 16 samples; A1 iters reproduce S2b exactly)
| seed | A1 streak=3 | A2 streak=∞ (to 300) | A3 streak=10 |
|---|---|---|---|
| …001 | cns 11 | max_iter, never valid | cns 18 |
| …002 | cns 5 | max_iter, never valid | cns 12 |
| …003 | cns 9 | max_iter, never valid | cns 16 |
| …004 | cns 6 | max_iter, never valid | cns 13 |
| …005–008 | cns 9,9,9,9 | all max_iter, never valid | cns 21,16,16,16 |
| …009–012 | cns 8,12,12,7 | all max_iter, never valid | cns 15,19,19,14 |
| …013–015 | cns 5,12,14 | all max_iter, never valid | cns 12,19,21 |
| …016 | cns 17 | **success @19, exact=True** | **success @19, exact=True** |
- Counts: A1 16/16 cns, 0 exact. A2: 15/16 max_iter_reached (syndrome NEVER valid in 300 iters), 1/16 late recovery (…016 @19). A3: 15/16 cns (12–21), same 1 recovery. (cns=`converged_no_syndrome`.)
- Observation: loosening/disabling the stop recovers exactly one frame (…016, exact); the other 15 never reach a valid syndrome within budget. No causal claim.

## Study B — p-ladder, production stopping (seeds …001–004; status/iter/exact; diff-weight = ‖x̂−x‖ symbol-Hamming when syndrome-valid-but-wrong)
| p | …001 | …002 | …003 | …004 |
|---|---|---|---|---|
| 0.01 | succ 4 E | succ 3 E | succ 2 E | succ 2 E |
| 0.02 | succ 4 E | succ 6 E | succ 2 E | succ 4 E |
| 0.04 | cns 15 | succ 11 E | succ 8 E | succ 10 ¬E, **w=14** |
| 0.06 | cns 12 | cns 17 | cns 23 | cns 11 |
| 0.081 | cns 11 | cns 5 | cns 9 | cns 6 |
- (E=exact, ¬E=non-exact, succ=`success`, cns=`converged_no_syndrome`.) Miscorrection weight now measured: p=0.04/…004 wrong solution differs in 14/256 symbols. Transition between 0.04 (3/4 success) and 0.06 (0/4) on these 4 frames; observations only.

## Study C — dv feasibility (read-only)
- `construct_l2` hardcodes `lam` from frozen `L2_LAMBDA={2:1.0}` (s2_peg L82/L172-173); NO lambda parameter — an alternative mix CANNOT be built through it without touching frozen S2b code.
- Lower layer accepts it: `peg_construct(n,m,lambda_edge,rho_edge,seed,...)` (v10_peg L291-294) takes arbitrary `lambda_edge`; `make_rho(rate,lambda_edge)` (v26_mcde L236) matches. So `{2:0.5,3:0.5}` / `{3:1}` need at most an additive optional `lambda_edge=None→L2_LAMBDA` on `construct_l2` (defaults pinned) — or a fresh probe calling the peg layer directly with zero frozen-code contact. NOT implemented this round.

**Attribution still paused — observations only.** No stopping-rule vs distribution causal claim; no route decision; no science-input change; no campaign rerun.
