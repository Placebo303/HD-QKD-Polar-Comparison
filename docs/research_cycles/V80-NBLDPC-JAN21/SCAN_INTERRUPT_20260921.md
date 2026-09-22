# SCAN trade-scan INTERRUPT record (2026-09-21) — EXPLORE, docs-only

- Track EXPLORE (interrupt record only: no execution, no resume, no rerun/tuning, no commit/push). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Interrupt: operator instruction "interrupt if too negative" after A192's decisive FAIL-early-stop; A196 was then terminated by SIGTERM. Process death verified: `/tmp/opencode/scan_a196.time` line 1 "Command terminated by signal 15" (wall 3:03.23, RSS max 166884 KB ≈ 163 MB).

## Per-arm final states (machine manifests, roots retained)

- **A192 — FAIL-early-stop** (root `workspace/p0_226c6dee`): 124/240 blocks, 13 fails (13th fail = block 123), block FER 0.1048; quarter tally 4/60 + 6/60 + 3/4 (2 quarters complete); manifest `verdict: FAIL-early-stop`, partial=true, next_block=124; wall 22:55.44 (`/tmp/opencode/scan_a192.time`, exit 0, RSS max 166308 KB); verify pins/ledger/rows ok.
- **A196 — INTERRUPTED** (root `workspace/p0_23ce5cb9`): 29/240 blocks, 1 fail (raw FER 1/29 = 3.4%, 0 complete quarters); partial=true, next_block=29; manifest verdict field `INCOMPLETE-wall` — NO gate verdict (PASS/FAIL); rows.json + block_accounting.csv retained; no resume launched.
- **C16A / C12A — NEVER LAUNCHED**: `workspace/l1b_*` holds only the Stage-A roots C6 (`l1b_5457229a`, FAIL-early-stop 13/27) and C8 (`l1b_7c2db924`, FAIL(budget) 6/85), both predating this scan; no new `l1b_*` root exists.

## Scientific read (observation level, not a claim)

- L2 cliff evidence: A188 (m=188) FAIL 4/14 = 28.6%; A192 (m=192) FAIL 13/124 = 10.5%; A196 (m=196) unresolved-but-trending-bad at 1/29; A200 (m=200) PASS 2/240 = 0.83%; A202 PASS 0/240 = 0%; A208 PASS 0/240 ×2 = 0%.
- Reading: inside the frozen box (m1+m2 ≤ 208, f_super ≤ 1.3) NO viable split exists under the dense-check-L1 + genie-u1-L2 family — the m1=12/16 funding legs (m2=196/192) are FAIL or unresolved, while the passing m2 (200/202/208) cannot fund m1≥6. The primary hypothesis (m2=192 funds m1=16) is decisively falsified by A192's FAIL-early-stop.

## Next-step pointer

- Live path: `L1_REWORK_MEMO_V3_20260921.md` (scan closure + option b2e) and `B2E_EXPERIMENT_PACKET_20260921.md` (cheap-u1-estimator probe). No auto-continue; no rerun/tuning; no Stage B.

## No authorization

- This record authorizes NOTHING: no arm execution, resume, or Stage B is granted; any new probe needs its own frozen packet, Pre-EXECUTE, and explicit grant. Docs-only; no commit/push.
