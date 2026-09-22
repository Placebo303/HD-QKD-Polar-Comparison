# L1B Stage A Batch-End Review (2026-09-21) — EXPLORE synthetic, independent

- Track EXPLORE_HEAVY synthetic; branch `formal-ir-v72p1-addendum-clean` (read-only review; no switch/commit/push). Stage A only; Stage B NOT run, correctly.
- Verdict: **PASS_WITH_FINDINGS** (terminals correct, evidence consistent, ceiling held; findings non-blocking, no gate impact).
- L1AR-1 C6 early-stop correct: 13th fail at block idx 26 (seed 2026095627), bar 12 ⇒ FAIL-early-stop; manifest 27/27 decodes, ledger_ok True; recomputed 13 fails from rows.json.
- L1AR-2 C8 budget terminal correct: block 84 `status=overrun`, decode_s 1120.7 s > 300 s per-decode cap; verdict FAIL(budget); ledger decodes 84 vs blocks 85, ledger_ok False as designed; terminal non-resumable.
- L1AR-3 Windows/resumes: one 3600 s window each (C6 909.1 s, C8 2521.8 s, both ≤3600); continuations 0/1 each; no resumes of FAIL states. C6 wall slightly over ≤900 s est — estimate only, window holds.
- L1AR-4 Evidence consistency: result doc == manifests == rows == CSVs (spot-checked). C6 27/13 FER 0.481; C8 6 fails, FER 0.071 RAW-only; quarters (C6 27/13; C8 60/4 + 25/2); suc/fail iter medians (C6 6/7; C8 4/10) all match.
- L1AR-5 (note) C8 denominator: result doc "85 blocks" counts the overrun row (84 decoded + 1 overrun); brief "84 blocks" counts decodes. Both round to FER 0.071; RAW-only either way — use "6/84 decoded (+1 overrun row)" henceforth.
- L1AR-6 Retained failures: C6 27 rows + C8 85 rows retained incl. overrun row; CSVs carry fails + overrun line; no overwrite (only 2 fresh `workspace/l1b_*` roots; `results/`, `outputs_comparison/` untouched; no Stage B roots).
- L1AR-7 Instability finding recorded: per-decode stall 1120.7 s on a dense-check (m1=8, avg check deg ~256) block is in manifest + rows + CSV + result doc — confirms rework-memo §1 risk (dense SPA can stall, not just fail). Relevant to (b1/b2) fallback deliberation.
- L1AR-8 Authorization: amendment recorded pre-run (packet Amendment + review PASS + preexec RESOLVED); Stage A ran under standing pre-auth; Stage B correctly NOT run (packet Q3: B gated on A PASS + separate grant; no A PASS exists).
- Claim ceiling (held): dense-check L1 (n=1024, m1=6/8, λ={2:1}, γ1 channel) does NOT meet Stage A at either config — m1=6 FER 48%; m1=8 partial 7.1% RAW with per-decode instability. NOT beyond: no Stage B eligibility, no L1 finality, no S3, synthetic only, C8 7.1% is not a pass and the run is incomplete.
- This review **authorizes nothing / no Stage B**. Returned to main thread.
