# S2c Operator Prompt (2026-09-20) — ONE arm per run; authorizes NOTHING without grant

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). G-S2C frozen ONLY — fresh explicit grant + Pre-EXECUTE Q0–Q6 (packet §7) required before any run.
- Run ONE arm: `--arm L-A|L-B|L-C` (λ {2:1}|{2:0.5,3:0.5}|{3:1}); 60 groups × 4 frames = 240 decodes max; seeds `2026097201+idx`, idx=4g+f; stream `s2c_emp:{seed}`; root `workspace/s2c_<uuid8>` (fresh, absence proven).
- Constructor asserts first (STOP on mismatch; seed 2026092001, fixed peg+reconcile, construct-twice-identical): L-A fc0/girth6/rank47; L-B fc0/girth6/rank47; L-C fc2/girth4/rank47.
- Channel (synthetic draws, no new data): 2M `gamma_f03.npz` + `gamma_f03_pb.npz` read-only (p_b normalized else refuse); per-symbol triple (b,u1,u2); Alice x=u2, Bob b; GENIE true-u1 conditioning (upper-bound only).
- Decode per frame: y=b&31; rows=γ_2(·|b,genie-u1); π(e)=rows[y⊕e]; `decode_error_domain_posterior` (NEVER scalar-p `decode_error_domain`); max_iter=300, streak default; exact_match=(x_hat==u2); group any-fail⇒fail.
- Early-stop at 4th group fail → FAIL (retain partials, never resumable). Budgets: wall ≤3600 s, per-decode 300 s, RSS <4 GiB; ≤1 `--resume-from` for WALL-PARTIAL only.
- Gates per arm (AND): (a) FER ≤3/60; (b) f_super=1.2246-mapping ≤1.3 (D_blind=0 + sensitivity 16 bits≈+0.019). f_L2=1.1376 INFORMATIONAL.
- STOP on any science-input change. Return: run root (`rows.json` + `group_accounting.csv`), per-group iters/accept, ledger, verdict; no route/S3/dv-causal claims.
