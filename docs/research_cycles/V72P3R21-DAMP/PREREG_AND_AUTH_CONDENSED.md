# R21 PREREG_AND_AUTH (CONDENSED) — Damping sweep, S0-only m100

Track: DECIDE. Solidification only; no execution/data/commit under this task.

## Frozen scope (both arms)

- S0-only m100 per arm; ONLY varying parameter: `damping_alpha` ∈ {0.5, 0.8}.
- All else frozen: cold init, shift eps=1e-4, graphs 4720/4721, T=64/564.
- Paired R9 128 blocks 1p5M-2123..2186.
- Baselines read-only: S1-shift 2/128 + R9 + R20. No recomputation, no retune.

## Per-arm gates (frozen)

- ≥6 accepts → DAMP-HELPS; 4–5 → MARGINAL; ≤3 → NO-DAMP-GAIN; any undetected → STOP.

## Budgets

- sci ≤ 256 total (128/arm), setup ≤ 8 total (4/arm).

## Fresh roots

- 0.5: `workspace/g6r21_damp_9f43bc04-0b0b-44a0-a0f9-3b66329c272f`
- 0.8: `workspace/g6r21_damp_8dbeced5-7d77-478f-9dc6-0b992500bbcd`

## Grant lineage

- Mandate + pre-approvals consumed once for both arms (single-consumption per arm recorded in RESULT acceptance block).
