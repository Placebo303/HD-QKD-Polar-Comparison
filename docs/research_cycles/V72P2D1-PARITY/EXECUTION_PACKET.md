# V72P2D1-PARITY frozen execution packet (P5前半)

Cycle: V72P2D1-PARITY. Base: ba0df2d3bea4147574e0b8224480f45c93505178.
Branch: formal-ir-v72p1-addendum-clean. Status: FROZEN / EXECUTE_NOT_AUTHORIZED until Pre-EXECUTE PASS.
Scope: OpenSpec openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/ + scripts/v72p2d1_parity_layout_diagnostic.py + scripts/test_v72p2d1_parity_layout_diagnostic.py + this cycle docs only. No src/experiments/tools/results change. No overwrite of any existing output.

## Frozen CLI (single invocation only)

```
python scripts/v72p2d1_parity_layout_diagnostic.py \
  --registry v71_data_registry.json --session 20260123_1M_600k_0dB \
  --out comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab \
  --arm-budget-s 600 --global-budget-s 1800
```

No other flags change semantics. No tuning / budget-override / rerun flags.

## Budget (frozen)

- Per-arm soft deadline: 600s (checked before each checkpoint publication; one checkpoint may overrun).
- Whole-command budget: 1800s (includes CAL fit + A + B + diagnostics + terminal write).
- Ladder: 72 checkpoints, max 10/ckpt, max 720/arm. No posthoc revision.

## Output (frozen)

- Output root: comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/ (must be absent before invocation; exists => refuse with zero files, no delete).
- Terminal state always exactly four files: manifest.json + results.json + table.csv + report.md (success / A-gate-B / CAL_FAILED / M_FAILED / real-exception all same four; unrun arms not_attempted + D null).
- Running candidates only in workspace/v72p2d1_<uuid>/ temp, never counted; temp removed after terminal four land (kept only if terminal write fails). No run_01. No raw symbols / syndrome bytes / fitted matrix / per-bit arrays.

## Authorization (only this A/B single block, each once; 仅本次A/B单块各一次)

- Authorized scope when released: ONE invocation of the above CLI on the single non-fresh diagnostic block VAL1726-1729 (session 20260123_1M_600k_0dB, CAL702..1725 shared prior), arm A once then arm B once (A-then-B serial). No second block, no fresh data, no tuning.
- One-shot: same --out second call always refuses (no resume/fill of B; new out is a new run outside this freeze). No rerun within this authorization. Authorization consumed after one completed/failed invocation.
- P5前半 does NOT release formal execution; release requires separate Pre-EXECUTE PASS binding implementation SHA. Tests use fake runner only and never touch the production output root.

## Tests (frozen)

- T0: python -m py_compile scripts/v72p2d1_parity_layout_diagnostic.py scripts/test_v72p2d1_parity_layout_diagnostic.py
- T1: pytest -p no:cacheprovider scripts/test_v72p2d1_parity_layout_diagnostic.py (workspace独立temp, fake only, no real registry/parquet read, no production output touch; missing injected decoder_fn must raise, never fallback to real decoder).
