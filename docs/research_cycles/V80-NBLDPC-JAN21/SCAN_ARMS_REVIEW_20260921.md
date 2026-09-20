# SCAN arms review 20260921 (EXPLORE, pre-execution, no run)
Branch formal-ir-v72p1-addendum-clean; scope: v80_o1_campaign.py, v80_l1b_campaign.py, 2 test files, SCAN_PREEXEC + memo v2.
Verdict: PASS WITH COMMENTS — L2@192, L2@196, L1@16, L1@12 may proceed under standing pre-authorization after Q3 fresh grant + rg-absence re-check.
SAR-01 accounting: A192 1024b/1.201124, A196 1044b/1.224585 (preexec truncations within test tol 1e-4); C12A/C16A carry 1104b/1.294947 + m2-deferred note.
SAR-02 pins: A192 fc0/g8 gated-clean; A196 fc0/g6 recorded-not-gated (P0 rule); C12A fc7767/g4, C16A fc4177/g4 recorded covariates; rank-full + twice-identical gated all legs.
SAR-03 refusals: closed-world lists updated (A192|A196, C12A|C16A); Stage B for C12A/C16A refuses rc=2 pre-decode, zero decodes (test calls==[]).
SAR-04 mechanics: frozen triple sampler / L1-only rows / XOR-centered prior / posterior-only entrypoint / max_iter 300 reused; bar 12, early-stop 13th fail; caps 3600s/300s/4GiB; C8-type overrun risk flagged.
SAR-05 scope: diff = 2 campaign + 2 test files only; frozen modules read-only; paired base 2026095601, no-independence note kept.
SAR-06 (non-blocking): ARMS table min_girth=8 for A196 vs dry 6 — harmless (ungated) but annotate measured-vs-spec; 'P0' campaign label reused for SCAN — identity via arm id + preexec only.
Statement: per memo v2 S4 interpretation rule acknowledged — no auto-proceed; Stage B ONLY at a split where BOTH legs pass, needs its own frozen packet + grant; report to main thread.
