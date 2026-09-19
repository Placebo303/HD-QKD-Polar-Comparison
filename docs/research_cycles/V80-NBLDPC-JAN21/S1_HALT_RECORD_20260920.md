# V80 S1 RERUN — CONTROLLED HALT RECORD (2026-09-19T17:17Z UTC = 20260920 local)

Track: EXPLORE controlled halt (orchestrator decision; user informed; reversible pause).
Branch: formal-ir-v72p1-addendum-clean (no switch/commit/push; none done).

## H1 — positively identified before kill
- 51395 (PPID 517) `/bin/bash -c bash /tmp/opencode/s1_resume_loop.sh`, etime 01:08:14
- 51396 (PPID 51395) `bash /tmp/opencode/s1_resume_loop.sh`, etime 01:08:14
- 62601 (PPID 51396) `/usr/bin/time -v .venv/bin/python -m ...v80_s1_mcde_runner --execute-real --execution-authorized --resume-from workspace/s1_mcde_1b079a49-7a2a-4e3f-8a20-00cb69f3c210`
- 62602 (PPID 62601) python runner proper (CPU 00:04:10). PID 517 = opencode serve, NOT touched.

## H2 — kill order followed, SIGTERM only (no SIGKILL needed)
- SIGTERM loop 51396 + wrapper 51395 FIRST → both dead on recheck.
- Runner orphaned to PPID 510; SIGTERM 62602 → gone ≤5 s; time-wrapper exited on its own.

## H3 — TWO external respawns; watch STOPPED per protocol
- R1 (~17:14Z): chain 64107/64108/64112/64113, PPID 517 (relaunch via tool bridge, NOT self-respawn — loop script has no respawn logic). Killed same order, all dead ≤5 s.
- R2 (~17:16Z): chain 64431/64432/64436/64437, PPID 517 again. Killed same order, dead ≤5 s; final grep clean (exit 1) at 17:16:44Z.
- STOP: relauncher (parent = opencode serve session) is still active/polling — orchestrator MUST stop it or chain #3+ will appear. No further watch cycles run.

## H4 — rerun-root snapshot (read-only; in-flight call lost, not in rows)
- ledger {PRIMARY 420, SECONDARY 118, SETUP 12, TOTAL 538}; wall_windows 10; n_rows 1; partial True; terminals {PRIMARY SELECT, SECONDARY resource_blocked}; config_hash 60ab1e44…fb0da.

## Rationale / retention
- Stopped-early by orchestrator (cost/value: SECONDARY m24 0/30 combined; ~64 confirm slots ≈ 5 h unrecovered).
- Rerun root + old root untouched; RESUMABLE via --resume-from ONLY while config-hash stays 60ab1e44…0da (any runner edit rotating the hash ⇒ this partial is hash-foreign, like the old root). No commit/push; nothing deleted/edited.

## H5 — post-stand-down addendum (2026-09-20, docs-only)
- Final tally: ledger PRIMARY 420 / SECONDARY 119 / SETUP 12 / TOTAL 539; wall_windows 11; n_rows 539; partial true; terminals PRIMARY SELECT / SECONDARY resource_blocked; config_hash 60ab1e44…0da unchanged; old root 07723233 untouched; 61 SECONDARY confirm slots formally abandoned.
- Mechanism: bounded resume script /tmp/opencode/s1_resume_loop.sh (80-turn cap, manual relaunch per completion, no daemon/cron); loop killed first, then runner; 2 external (tool-bridge) respawn waves killed; stand-down confirmed; inert now.
- Quiescence verified 6×60s empty; no scheduler.
- Resume constraint: partial resumable ONLY while config-hash stays 60ab1e44…0da; any hash-rotating runner edit makes it hash-foreign — resume-before-edit decision if ever needed.
