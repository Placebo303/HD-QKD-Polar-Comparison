# V26 channel-informed multilevel DE gate — run evidence

Terminal state: **pass_target_f13** (A02 F03 GF32+GF32 f=1.3 全收敛; A01 f=1.6 slack).

## Run roles

| run | role | description |
|-----|------|-------------|
| `run_02/` | **canonical** | authoritative evidence root; `RUN_MANIFEST.json` role=canonical |
| `run_01/` | **deterministic_repeat** | independent re-run; scientific fields identical to canonical (72 screen + 60 confirmation 0 mismatch) |

Each run root contains:

- `m0_report.json` — M0 adapter semantic gate (incl. explicit source↔delay metadata)
- `m1_report.json` — M1 mechanism reference tests (incl. corrected iteration-0 and
  centered GF2 BSC reference)
- `screen_results.json` / `confirmation_results.json` — persisted DE calls
  (NOT re-run during closeout; verifier recomputes read-only for comparison)
- `screen_checkpoint.json` / `confirm_checkpoint.json` — completion checkpoints
- `calls_summary.json` / `gate.json` — per-call summary + terminal state
- `readonly_verify.json` — independent read-only verifier result (`ok=true`, recomputes
  72 screen + 60 confirmation + A02@f=1.3 30/30 + rate/rho/seed/entropy/terminal)
- `RUN_MANIFEST.json` — role, source↔delay metadata, resource-gate verdict, design constants

## Resource gate

`RESOURCE_LIMIT_SECONDS = 24*3600` per completed-call accumulated wall-clock; not
triggered (screen≈44s + confirm≈112s).
