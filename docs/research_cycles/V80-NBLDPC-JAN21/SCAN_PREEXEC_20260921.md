# SCAN trade-scan PRE-EXECUTE record (2026-09-21) — EXPLORE, NOT granted

- Track EXPLORE. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Parent: rework memo v2 §2 (trade scan); P0 packet §§1–7; L1B packet §§1–7 + Amendment 2026-09-21.
- Q0 branch clean (implementation-only; no execution here). Q1 scope: `formal_ir/v80_o1_campaign.py`,
  `formal_ir/v80_l1b_campaign.py` + their two test files only; frozen modules untouched.
- Q2 frozen contract: paired blocks `2026095601+idx` (idx=0..239, NO independence claim);
  seed 2026092001/trials 20; bar fails/240≤12; f_super≤1.3; no rerun/no tuning.
- Q3 authorization: NOT granted — each arm needs a fresh explicit grant + Pre-EXECUTE rg-absence re-check.
- Q4 roots must be ABSENT pre-run: `workspace/p0_<uuid8>` (L2 arms), `workspace/l1b_<uuid8>` (L1 arms).

## Q5 dry-construct pins (measured 2026-09-21, seed 2026092001/trials 20, n=1024, in-memory)

- A192 (m=192): fc=0/girth=8/rank=192, twice-identical, sockets 2048/parity 0 — gate-clean.
- A196 (m=196): fc=0/girth=6/rank=196, twice-identical — girth RECORDED-not-gated (P0 rule).
- C12A m1=12: fc=7767/girth=4/rank=12, twice-identical — fc/girth recorded (Amendment).
- C16A m1=16: fc=4177/girth=4/rank=16, twice-identical — fc/girth recorded (Amendment).
- Focused tests: 111 passed (both campaign files, incl. real-gate dry pins + refusal matrix).

## Q6 commands (one arm/invocation; `--de-label exploratory`; ≤1 wall-partial resume; early-stop 13th fail)

- L2: `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_o1_campaign
  --execute-real --execution-authorized --arm A192|A196 --root workspace/p0_<uuid8>
  --block-base 2026095601 --n-blocks 240 --construct-seed 2026092001 --de-label exploratory`
- L1: `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_l1b_campaign
  --execute-real --execution-authorized --stage A --config C12A|C16A --root workspace/l1b_<uuid8>`
  (Stage B refused for C12A/C16A; C6/C8 behavior unchanged.)

## Budgets/stop (per arm)

- L2 ≈765–937 s/arm, 1 window ≤3600 s. L1: C8-type per-decode overrun risk (>300 s ⇒ terminal
  FAIL(budget), never resumes); RSS <4 GiB. Gates per arm (AND): fails/240≤12 + f_super-mapping≤1.3.
- Combined Stage B ONLY at a split where BOTH legs passed — needs its own frozen packet + grant.
