# L1B Stage A Result (2026-09-21) — EXPLORE synthetic, RAW only

- Track EXPLORE_HEAVY synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). Stage A only; Stage B NOT in scope.
- Frozen recap: m1 legs rank-full + twice-identical GATED, fc/girth RECORDED-not-gated (C6 m1=6: fc34608/g4; C8 m1=8: fc18368/g4; dense-check regime); m2 legs fc==0 + rank-full + twice GATED. Blocks `2026095601+idx` (paired reuse O1R/P0, no independence claim); construct seed 2026092001/trials 20. Gates/arm: fails/240≤12 AND f_super-mapping 1.294947≤1.3 carried. GENIE not involved in Stage A (L1-only exact û1==u1).
- | cfg | root | blocks | fails | FER | Q0-59 | Q60-119 | sucIter med | failIter med | verdict |
- | C6 | `workspace/l1b_5457229a` | 27 | 13 | 0.481 | 27/13 | — | 6 (2–9) | 7 (5–14) | FAIL-early-stop |
- | C8 | `workspace/l1b_7c2db924` | 85 | 6 | 0.071 | 60/4 | 25/2 | 4 (2–12) | 10 (7–12) | FAIL(budget) |
- Machine verdicts (frozen gates ONLY): C6 FAIL — 13th fail at block 26, gate (a) unpassable; C8 FAIL(budget) — block 84 per-decode overrun 1120.7 s > 300 s cap (terminal, non-resumable per frozen code + packet §6). Gate (b) mapping 1.294947≤1.3 carried both (budget mapping, not measured efficiency). Neither config PASSED; no A PASS record exists.
- Budget/ledger/windows: C6 wall 15:21 (manifest 909.1 s) vs ≤900 s est, window ≤3600 ok; RSS max 165444 kB. C8 wall 42:14 (manifest 2521.8 s) OVER ≤900 s est, window ≤3600 ok; RSS max 165692 kB (<4 GiB). Ledger C6 27/27 ok; C8 decodes 84 vs blocks 85 (overrun row, ledger_ok False). 1 window each; continuations used 0/1 (no resume: FAIL states never resume).
- Provenance: executor `formal_ir/v80_l1b_campaign.py` (frozen); Q6 canonical commands; C6 PID 290738 start 2026-09-20T08:55:25Z; C8 PID 291892 start 2026-09-20T09:12:31Z; logs `/tmp/opencode/l1b_A_C6.log`, `/tmp/opencode/l1b_A_C8.log`. Per-root: manifest.json + rows.json + block_accounting.csv + group_accounting.csv (group = single-code block projection, O1R column format).
- Cross-refs: packet `L1B_EXPERIMENT_PACKET_20260920.md` (+Amendment); amendment review `L1B_AMENDMENT_REVIEW_20260921.md`; rework memo `L1_REWORK_MEMO_20260921.md`; preexec `L1B_PREEXEC_20260920.md`.
- Does NOT establish: no Stage B / combined-chain claim; no threshold claim (C8 0.071 is a partial raw rate, not a gate pass); synthetic only, no real/Jan-21 data; single-code block ≠ S2c-group; no S3/qualification/publication/route decision.
- NO decision on Stage B here (packet Q3: B gated on A PASS + separate grant by main thread). Returned to main thread.
