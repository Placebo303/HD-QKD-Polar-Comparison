# S2c Executor Review (2026-09-20) — EXPLORE focused

Track: EXPLORE synthetic only; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). No run performed; focused test rerun only.
Verdict: PASS_WITH_FINDINGS (no blocking issues; 24 passed rerun 3.67s).
Scope: only `v80_s2c_campaign.py` (872L) + `test_v80_s2c_campaign.py` (573L) + `S2C_PREEXEC_20260920.md` vs frozen `S2C_EXPERIMENT_PACKET_20260920.md` E1-E7. Tracked diff empty; no `workspace/s2c_*` roots.
E1 PASS: ARMS L-A 0 / L-B 0 / L-C 2 pinned + STOP-BLOCKED + construct-twice + unknown-arm refuse; frozen `v80_s2_fer_campaign`/`v80_s2_peg`/`v10_peg`/kernel/`v26_channel` untouched (read-only imports, no `construct_l2`).
E2 PASS: triple order b~p_b -> u1~g1 -> u2~g2 matches S1 L507-526 + delta-at-0; sidecar `2M_p_b` sum=1+/-1e-9 gate, no uniform fallback; QSC p* path deleted.
E3 PASS: y=b&31 (v29 L269-273); rows via `posterior_rows` v26 L239-244 semantics; pi via XOR-centering (`_center_rows` v28 L189-197); calls `decode_error_domain_posterior` v28 L155-186 only (T8 bare-call scan empty); GENIE true-u1 + ceiling labelled.
E4 PASS: constructor 2026092001; frames literal 2026097201+idx (idx=4g+f, paired); stream `s2c_emp:{seed}` != `s2_smoke:`; 2026097201 clean outside S2c carriers; 20260973/74 zero hits.
E5-E7 PASS: single-arm + dual-flag refuse rc=2; gates FER<=3/60 AND f_super<=1.3 (f_L2 informational, f_super budget-mapping, D_blind=0 + sensitivity); caps wall 3600/per-decode 300/RSS 4GiB; checkpoint-per-group + one wall-partial `--resume-from`, terminal states nonresumable.
Q0-Q6 COMPLETE + D1 ceiling stated (Pre-EXEC L16); Q6 single-window commands + budgets present.
Findings (non-blocking):
- SC1: Q1 "only additive untracked: module+tests+record" understates worktree — many parallel untracked workstreams exist; tracked tree clean holds, S2c scope itself additive-only. Correct wording at run time.
- SC2: rg "no other hits" ambiguous — 2026098001 legitimately hits pre-existing R23/v22b carriers (expected rejection evidence), not S2c contamination. No action.
- SC3 (info): constructor-seed 2026092001 reuse from S2b intentional (same FIXED peg); frame-stream domain separation preserves pairing. Posterior `tot`/nonfinite extra gate is stricter fail-closed vs quoted norm-only. No action.
Explicit statement: three-arm run may proceed only under fresh user pre-authorization; this review authorizes nothing itself (G-S2C still frozen-only until grant).
Evidence: `.venv/bin/python -m pytest comparison_bench/tests/test_v80_s2c_campaign.py -p no:cacheprovider -q` -> 24 passed; `git diff --stat` empty; `workspace/s2c_*` absent.
