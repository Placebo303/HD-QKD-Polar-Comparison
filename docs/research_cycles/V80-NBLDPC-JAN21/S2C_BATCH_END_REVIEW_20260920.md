# S2c Batch-End Review (2026-09-20) — EXPLORE independent, ONE record

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` kept (verified, no switch/commit/push). Scope: S2c three-arm empirical-channel campaign only.
- Verdict: **PASS** (no blocking issues; one non-blocking finding SBR-1).

## 1. Authorization boundary — PASS
- Standing user pre-auth 2026-09-20 (PREEXEC Q3); packet G-S2C frozen-only, grant via pre-auth + PREEXEC Q0–Q6 + executor review.
- Wiring fix (`construct_fn(arm,seed,trials)`) reviewed PASS **before** re-launch; zero science-input change, re-launch under standing pre-auth recorded in PREEXEC delta.
- Zero-execution blocked attempt retained as record (wiring-fix SWF-4: zero roots/zero decodes; PREEXEC delta: refused roots never created).

## 2. Machine gates — PASS
- Pins honored per manifests: L-A fc0/g6, L-B fc0/g6, L-C fc2/g4 (pinned, not zero) — all match packet §1 + construct-twice gate.
- Gates per frozen rule (FER≤3/60 AND f_super≤1.3): all arms group FER 4/4 → gate (a) FAIL; f_super 1.2246≤1.3 → gate (b) pass (budget mapping). Verdicts FAIL-early-stop correct.
- Early-stop at 4th group, 0 continuations, terminal FAIL not resumed — matches packet §6. Budgets: wall 40/45/11 s ≪3600; max per-frame wall 25.1 s <300 s; caps (RSS 4 GiB) in manifests.

## 3. Evidence consistency — PASS
- Spot-check rows.json + group_accounting.csv vs result doc: L-A n_ok 1/3/3/2 + iters exact; L-B 0/1/2/0 + iters exact; L-C all 0/4 + iters exact. Frame FER 7/16, 13/16, 16/16 ✓. Ledger decodes=16/groups=4/failures=4/fer=1.0 ✓. f_L2 1.1376, f_super 1.2246, D_blind 0.0 + sensitivity ✓.

## 4. Retained failures — PASS
- V1 (S2_V1_DIAGNOSTIC), V2 (S2_FER_V2_RESULT), S2b raw (S2B_RESULT + FAILURE_TRIAGE) + blocked-attempt record + S2c raw (3 fresh roots) all retained; fresh UUID roots, no `results/`/`outputs_comparison/` writes, nothing overwritten.

## 5. Claim ceiling — PASS
- SUPPORTS: finite-length n=256/m₂=47/genie-u1/empirical-channel does not meet the group FER bar for any of the three λ arms (0/3 pass).
- DOES NOT: no L1 claim, no two-layer claim (genie ceiling only), no dv causal claim, no S3/real-data claim, no qualification/publication numbers, no route decision.
- S3 entry authorized? **No.** No S3 entry doc exists; packet states S3 DECIDE separate.

## 6. Per-frame vs group-rule nuance — PASS (reasoned)
- Bar needs P(group pass)=(1−p)⁴≥0.95 → p≤1.27%. Observed p: 43.75%/81.25%/100% — bar unattainable; 4/60 fails already exceed 3/60 even if all remaining groups passed. Early-stop conclusion sound, not premature.

## Findings
- SBR-1 (non-blocking): result-doc RSS 156/157 MB + exit 0 not present in machine artifacts (manifests carry only the 4 GiB cap). Wall/per-decode verified from artifacts; RSS claim unverifiable from roots. No action required for EXPLORE raw record.

**This review authorizes nothing.** No S3 entry, no qualification, no promotion, no further execution.
