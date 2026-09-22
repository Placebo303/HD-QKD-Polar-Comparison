# S2 FER Pre-EXECUTE Record — 2026-09-20 (EXPLORE prep only; campaign NOT run)

- Track: EXPLORE synthetic only. This record authorizes NOTHING; execution needs a fresh explicit grant.
- Q0 branch: `formal-ir-v72p1-addendum-clean` (verified `git branch --show-current`; no switch/commit/push by this task).
- Q1 scoped cleanliness: only tracked change is `comparison_bench/tests/test_v80_s2_campaign.py` (+161, additive T9–T11) plus this new record; other untracked dirt is pre-existing/out-of-scope, untouched.
- Q2 frozen contract (packet `S2_FER_CAMPAIGN_PACKET_20260920.md` G-S2FER): V1 `construct_l2(seed=2026092001, max_trials=20)` with `four_cycles==1158` assert-or-STOP; 60 groups x 4 frames = 240 decodes; literal seeds V1 `2026096001+idx` / V2 `2026096301+idx` (idx=0..239, g/f -> 4g+f); group rule any-frame-fail => group-fail; early-stop at 4th group failure; D_blind=0 MEASURED placeholder (NEVER-ASSUME-ZERO + sensitivity line mandatory); gates PASS iff superframe FER<=5% (<=3 fails/60) AND f_super<=1.3.
- Q3 authorization: 用户预授权 2026-09-20——继续自主推进；所需授权均已预授权；抉择取 recommend 项.
- Q4 fresh root: `workspace/s2_fer_<uuid8>` MUST be absent at run start; operator verifies absence (e.g. `test ! -e`) immediately before launch; old roots untouched; `results/` and `outputs_comparison/` forbidden.
- Q5 tests green: `.venv/bin/python -m pytest comparison_bench/tests/test_v80_s2_campaign.py comparison_bench/tests/test_v80_s2_construction.py -p no:cacheprovider -q` -> 18 passed (11 campaign incl. new T9–T11 + 7 construction), wall 23.09 s.
- Q6 command template (module has NO `__main__` guard — call `main()` explicitly; single argv, V1 first):
  `.venv/bin/python -c "from comparison_bench.src.comparison_bench.formal_ir.v80_s2_fer_campaign import main; raise SystemExit(main(['--execute-real','--execution-authorized','--root','workspace/s2_fer_<uuid8>']))"`
  Budget: at most 2 windows x 3600 s wall (fresh window per invocation); per-decode cap 300 s; RSS < 4 GiB; 1 CPU; ledger-style call count in result.
- SCE-01 governing rule: packet §7 governs — exactly ONE explicit `--resume-from` continuation allowed (fresh window appended to `wall_windows`, scientific ledger continues, completed groups never recomputed); §3/§4 one-shot wording is superseded (read as no auto-relaunch / no resume-loop); NO auto-relaunch; second resume refuses rc=2 (tested T9).
- SCE-03 operator definitions (executor emits manifest+rows only; operator post-processes): `group_accounting.csv` columns: `group_idx, seed, frame0..3 converged/iterations, group_pass, cumulative_fail_groups, fer_running, wall_s`. RESULT doc required fields: per-group table, FER point estimate + rule-of-three upper bound if implemented else point only, f_super incl. D_blind line + sensitivity line, machine verdict per frozen gate, budget state, ledger, provenance/root path.
- Artifacts under the fresh root: `manifest.json` + `rows.json` (executor) + `group_accounting.csv` (operator); result doc `S2_FER_RESULT_*.md`; NO overwrite of any existing root.
- Entry evidence still owed at grant time (§6 a–g): BER/G-REPRO currency, provenance re-attach + hash re-check, constructor 7-passed suite rerun, reviewer PASS, live 1158 assert, rg-absence re-check.
- 2026-09-20 micro-fix: `__main__` guard added to `v80_s2_fer_campaign.py` (`sys` already imported; no other change); now-canonical Q6 command: `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_s2_fer_campaign --execute-real --execution-authorized --root workspace/s2_fer_<uuid>` (Q6 otherwise unchanged).

## V2 addendum (2026-09-20)
- V1 verdict FAIL (S2_FER_RESULT_20260920.md, FAIL-early-stop 4/4) + diagnostic PLUMBING-SANE (S2_V1_DIAGNOSTIC_20260920.md) → V2 trigger per packet §3 (single shot; no re-seed).
- Frozen inputs: construct_l2(seed=2026096101, max_trials=100), valid IFF four_cycles<1158; frame seeds 2026096301+idx (idx=0..239); decoder log-FFT-SPA max_iter=300 qber=0.05; channel qsc_pair_sampler QSC p=0.05; D_blind=0.
- Fresh root: `workspace/s2_fer_c5a176ee` (absence-verified pre-launch); V1 root `workspace/s2_fer_2752f403` untouched; results/outputs_comparison forbidden.
- Command: `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_s2_fer_campaign --execute-real --execution-authorized --variant V2 --root workspace/s2_fer_c5a176ee` (timed, detached).
- Budget: ≤70 min window here (+ at most ONE --resume-from continuation per §7; second forbidden); wall ≤3600 s/invocation, RSS ≤4 GiB, 1 CPU.
- Authorization: user pre-authorization 2026-09-20 (covers this V2 single shot; no commit/push).
- V2 terminal 2026-09-20: executor `FAIL-early-stop` (4/4 groups FAIL; 1/16 exact_match); elapsed 157.59 s, 1 window, `continuations_used: 0`.
- Result: `S2_FER_V2_RESULT_20260920.md`; accounting: `workspace/s2_fer_c5a176ee/group_accounting.csv`. Per packet §3, V2 FAIL ⇒ no S3 + fallback review required; this note authorizes nothing.
