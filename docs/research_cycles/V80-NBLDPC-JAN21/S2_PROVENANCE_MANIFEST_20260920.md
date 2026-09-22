# V80 S2 Provenance Manifest (2026-09-20) — EXPLORE readiness record only

- Track: EXPLORE. Branch `formal-ir-v72p1-addendum-clean`. Read-only record; authorizes nothing.
- Closes BER-4 (§4(d) alternative: explicit provenance manifest in lieu of version control).
- config_hash `60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe04fb0da` (suite-pinned, test:27; both roots match).

## Code identity (sha256, read-only `hashlib`; sizes/mtimes)
- `comparison_bench/src/comparison_bench/formal_ir/v80_s1_mcde_runner.py`: sha256 `e1b88a69…e20e8a7e3` (full: e1b88a69a85dc5a7186aac93ef49124a12142d82517692bdf836685e20e8a7e3), 88945 B, 2026-09-19T18:46:04Z.
- `comparison_bench/tests/test_v80_s1_readiness.py`: sha256 `0f9473a5…3484112c8` (full: 0f9473a527e4e792ac4ece2df2c6b4030f482f9ef84fa5121ace4183484112c8), 76145 B, 2026-09-19T18:46:17Z.
- `git status --short` both paths: `??` (untracked). Suite 2026-09-20: 54 passed + 6 subtests, 112.86 s.

## Evidence roots (manifest top-level keys only; no payload dump)
- `workspace/s1_mcde_1b079a49-7a2a-4e3f-8a20-00cb69f3c210` (partial): config_hash 60ab1e44…0da; ledger PRIMARY 420 / SECONDARY 119 / SETUP 12 / TOTAL 539; terminals PRIMARY SELECT / SECONDARY resource_blocked; n_rows 539.
- `workspace/s1_repro_26483764` (COMPLETE): config_hash 60ab1e44…0da; ledger PRIMARY 30 / SECONDARY 0 / SETUP 0 / TOTAL 30; terminals REPRO COMPLETE; n_rows 30; repro_gate.pass true (m47 5/5+5/5, range 0.000559).

## Provenance chain statement
- Both files are untracked-by-policy (BER-4); this manifest is the provenance chain (hash + size + mtime + suite re-verification). S2 readiness requires EITHER committing these files under version control OR re-attaching this manifest at Pre-EXECUTE with hash re-check.
