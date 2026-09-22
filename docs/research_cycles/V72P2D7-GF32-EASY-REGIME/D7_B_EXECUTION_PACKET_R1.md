# D7-B execution packet R1 (frozen; NOT authorized)

## Command (exact, do not run in this task)

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>
```

`<uuid>` is a fresh UUID for the one authorized invocation. Target must be
absent before launch; implementation refuses overwrite and refuses subdirs.

## Authorization lifecycle

- State file `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/cycle_state.yaml`
  holds `d7b_execution_authorized: false`. Runner reads only this state file,
  refuses before any work/root/decoder-bind when false.
- A future verbatim user authorization flips the key for exactly one UUID and
  is consumed on the first historical-decoder attempt regardless of outcome.
  No retry, rerun, resume, reuse. Importing, `--help`, `--dry-run`, and
  unauthorized runs bind no decoder and create no root.

## Budgets / stop rules (frozen)

Caps [1,2,4,8,16,32,90] cold; 420-call global stop before each call
(`D7_B_CALL_BUDGET_EXHAUSTED`, no success verdict); 120 s/call watchdog;
1500 s stored run wall; 1800 s outer + 30 s grace; <2 GiB RSS (unknown blocks
PASS); finite required; 1e-10 posterior tol; 1e-12 determinism. Terminal
priority T1–T9 per prereg §4.

## Root contract

`workspace/d7_b_easy_regime_<uuid>/` fresh, no subdirs, exactly:
`manifest.json, decoder_records.csv, summary.json, report.md, command_log.txt`
(scalar-only; no priors/beliefs/truths/syndromes). Verify mode recomputes
schema/terminal/accounting independently.

## Boundaries

Zero Model-F/CAL/VAL/real/raw/formal/VOID content reads (metadata-only root
checks). Zero `--phase`/R1d/G1/G2. v35/D5 read-only. D7-A oracle reused.
Pre-RESULT review mandatory before any result root/return is committed. This
packet authorizes no execution and no result acceptance. Next gate after T6:
`D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.
