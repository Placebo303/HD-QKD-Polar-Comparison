# S2 Campaign Executor Review — 2026-09-20 (EXPLORE review-only)
- Track: EXPLORE review-only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). Static read only; suite NOT rerun, campaign NOT run.
- Scope: `formal_ir/v80_s2_fer_campaign.py` (496 lines) + `tests/test_v80_s2_campaign.py` (253 lines, 8 tests). Both tracked in `bc927b9b`; `git diff` empty on scoped files — no existing-file edits. Other worktree untracked dirt out-of-scope, untouched.
- Verdict: **PASS_WITH_FINDINGS** (no blocking findings; safe for Pre-EXECUTE adjudication, NOT execution).
## Per-item results
1. Dual-flag gate + refusal matrix: PASS. `main` refuses rc=2 unless both flags present, pre-anything (:481-484); root absent→fresh-run, present→refuse (:337-338), absent-partial→refuse (:324-325), root/resume mismatch→refuse (:322-323,:487-488). T1/T2 cover the matrix.
2. four_cycles gate + V2 both directions: PASS. V1 `!=1158`→STOP-BLOCKED, V2 `>=1158`→refuse (:444-450); seeds/trials pinned per variant (:431-432). T7 covers bad-V1, good-V2, bad-V2.
3. Seeds literal + absence proof: PASS. `2026096001+idx`/`2026096301+idx`, idx=4g+f (:64-65,:102-105) match packet §2; rg-absence note in docstring (:12-14) + manifest `seeds.absence` (:179-180). T6 pins endpoints 6001/6001+239/6301/6301+239.
4. Group rule / 60×4 / early-stop / FER: PASS. Any-fail⇒fail via `evaluate_superframe` (peg :233-257, exactly-4 enforced); 60×4=240 (:67-69); 4th-fail→FAIL-early-stop (:416-418, T5); FER=fails/groups (:162, T3). Rule-of-three NOT implemented — not required by packet §3; no finding.
5. Checkpoint/caps/writer: PASS_WITH_FINDINGS. Per-group flush (T3: 61 writes), append-only `wall_windows` 1→2 (:333-334, T4), 300 s/decode (:384-387), RSS≥4GiB→FAIL(budget) (:367-371), single-writer overwrite-in-place (:130-136). See SCE-02.
6. Resume deviation: PASS_WITH_FINDINGS. Executor implements §7 (exactly ONE `--resume-from`; second refuses via windows-len≠1, :267-268; overrun/RSS FAIL(budget) terminal, :248). See SCE-01.
7. D_blind / no-real-data / confinement: PASS. `D_BLIND=0.0` MEASURED + NEVER-ASSUME-ZERO label + sensitivity (:73-75,:108-122, T6); only `v80_s2_peg` smoke imports, no Jan-21/real paths; `results`/`outputs_comparison` refused (:86,:147-152, T8); tests touch only `/tmp/opencode` + `tmp_path` (see SCE-04).
8. Scope: PASS (see header; §5 CSV/md gap is SCE-03, not an edit).
## Findings (all non-blocking)
- SCE-01 §3/§4-vs-§7 residual wording contradiction: §3 "no resume"/§4 "never resumed" text frozen unchanged while §7 freezes ONE continuation. Ruling: §7 resolution governs (read old text as "no auto-relaunch/no resume-loop"); executor+manifest flag adjudication (:16-23,:211-215). Pre-EXECUTE must state the governing rule explicitly.
- SCE-02 Untested refusal paths: second-continuation refusal, per-decode-overrun halt, RSS halt, and FAIL(budget)-partial resume refusal are implemented but have no test. Recommend 2-3 fake-clock/rss tests before the real run; not blocking (paths fail closed).
- SCE-03 Packet §5 deliverable gap: executor emits `manifest.json`+`rows.json` only — no `group_accounting.csv` / `S2_FER_RESULT_*.md`. Operator post-processing must be defined at Pre-EXECUTE.
- SCE-04 Test-docstring inaccuracy: "zero disk writes" but T4 uses a real-disk shim under `/tmp/opencode` (outside forbidden roots, cleaned up). Docs-only fix, lowest priority.
## G-S2FER entry-evidence (§6 a–g) status
- Satisfied before this review: (c) accounting map; (f) constructor reviewer PASS (non-blocking findings only).
- NOT satisfied here (review-only, no execution): (a)(b) BER/G-REPRO records — confirm currency; (d) provenance re-attach + hash re-check; (e) constructor 7-passed suite rerun; (g) live 1158 assert. T7 verifies gate mechanics statically only.
- Remaining for Pre-EXECUTE: Q0–Q6 + exact command/budget/output-absence/authorization, rg-absence re-check (§2), SCE-01 governing-rule statement, SCE-02/SCE-03 disposition. Authorizes NOTHING.
