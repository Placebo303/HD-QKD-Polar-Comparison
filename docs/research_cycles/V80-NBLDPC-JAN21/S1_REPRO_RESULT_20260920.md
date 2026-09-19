# V80 S1 G-REPRO Result (2026-09-20, EXPLORE) — RAW numbers only

- Track: **EXPLORE**. Packet `S1_REPRO_GATE_PACKET_20260920.md`;
  Pre-EXECUTE `S1_REPRO_PREEXEC_20260920.md` (PASS Q0–Q6).
  No interpretation, no S2 entry, no claim beyond the frozen bar arithmetic.
- Branch: `formal-ir-v72p1-addendum-clean` (no switch/commit/push; none done).

## Execution ledger (raw)

- Command: `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_s1_mcde_runner --repro-gate --execute-real --execution-authorized --root workspace/s1_repro_26483764`
- Exit status: 0. Wall: 6:06.89 (366.9 s, inside the single 3600 s window;
  under the ≈540–930 s estimate). Max RSS: 256864 kB (≈251 MB ≤ 4 GiB).
- Root: `workspace/s1_repro_26483764` (fresh; `manifest.json` + `rows.json`;
  checkpoint-per-eval; old roots untouched).
- Ledger: PRIMARY 30 / SECONDARY 0 / SETUP 0 / TOTAL 30 =
  scientific_de_calls 30/30. Terminals: `{"REPRO": "COMPLETE"}`,
  partial false.
- `config_hash` = `recorded_hash` =
  `60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe04fb0da`;
  `verify.ok` = true (hash_ok true, gate_match true).

## Per-cell raw table (BOTH units)

f_layer = layer-unit f_row (gate basis); f_superframe = frozen
whole-frame-with-tag superframe-n=1024 f
((4×5×(m₂+2)+64)/(1024×0.83256272)).

| m | base_seed | restart | seed_eff | converged | f_layer | f_superframe |
|---|---|---|---|---|---|---|
| 46 | 2026094951 | 0 | 2026094951 | True | 1.113537 | 1.201111 |
| 46 | 2026094951 | 1 | 2026102870 | False | 1.113437 | 1.201111 |
| 46 | 2026094951 | 2 | 2026110789 | False | 1.113392 | 1.201111 |
| 46 | 2026094951 | 3 | 2026118708 | True | 1.113171 | 1.201111 |
| 46 | 2026094951 | 4 | 2026126627 | True | 1.113141 | 1.201111 |
| 46 | 2026094952 | 0 | 2026094952 | False | 1.113353 | 1.201111 |
| 46 | 2026094952 | 1 | 2026102871 | True | 1.113442 | 1.201111 |
| 46 | 2026094952 | 2 | 2026110790 | True | 1.113513 | 1.201111 |
| 46 | 2026094952 | 3 | 2026118709 | True | 1.113351 | 1.201111 |
| 46 | 2026094952 | 4 | 2026126628 | True | 1.113290 | 1.201111 |
| 47 | 2026094951 | 0 | 2026094951 | True | 1.137523 | 1.224570 |
| 47 | 2026094951 | 1 | 2026102870 | True | 1.137394 | 1.224570 |
| 47 | 2026094951 | 2 | 2026110789 | True | 1.137876 | 1.224570 |
| 47 | 2026094951 | 3 | 2026118708 | True | 1.137528 | 1.224570 |
| 47 | 2026094951 | 4 | 2026126627 | True | 1.137738 | 1.224570 |
| 47 | 2026094952 | 0 | 2026094952 | True | 1.137697 | 1.224570 |
| 47 | 2026094952 | 1 | 2026102871 | True | 1.137778 | 1.224570 |
| 47 | 2026094952 | 2 | 2026110790 | True | 1.137701 | 1.224570 |
| 47 | 2026094952 | 3 | 2026118709 | True | 1.137721 | 1.224570 |
| 47 | 2026094952 | 4 | 2026126628 | True | 1.137317 | 1.224570 |
| 48 | 2026094951 | 0 | 2026094951 | True | 1.161899 | 1.248029 |
| 48 | 2026094951 | 1 | 2026102870 | True | 1.161527 | 1.248029 |
| 48 | 2026094951 | 2 | 2026110789 | True | 1.162145 | 1.248029 |
| 48 | 2026094951 | 3 | 2026118708 | True | 1.161829 | 1.248029 |
| 48 | 2026094951 | 4 | 2026126627 | True | 1.162022 | 1.248029 |
| 48 | 2026094952 | 0 | 2026094952 | True | 1.161950 | 1.248029 |
| 48 | 2026094952 | 1 | 2026102871 | True | 1.161881 | 1.248029 |
| 48 | 2026094952 | 2 | 2026110790 | True | 1.161847 | 1.248029 |
| 48 | 2026094952 | 3 | 2026118709 | True | 1.161868 | 1.248029 |
| 48 | 2026094952 | 4 | 2026126628 | True | 1.161392 | 1.248029 |

Per-(m, seed) f_layer min/max/range (raw, all rows incl. unconverged):

- m46 seed 2026094951: n=5 min 1.113141 max 1.113537 range 0.000396
- m46 seed 2026094952: n=5 min 1.113290 max 1.113513 range 0.000223
- m47 seed 2026094951: n=5 min 1.137394 max 1.137876 range 0.000482
- m47 seed 2026094952: n=5 min 1.137317 max 1.137778 range 0.000461
- m48 seed 2026094951: n=5 min 1.161527 max 1.162145 range 0.000619
- m48 seed 2026094952: n=5 min 1.161392 max 1.161950 range 0.000558

## G-REPRO verdict (COMPUTED by the frozen packet bar, not interpreted)

- m47 per-seed passes (converged ∧ 1.0≤f≤1.15): 5/5 on 2026094951,
  5/5 on 2026094952 (bar: ≥3/5 each).
- m47 converged n=10; pooled f range 0.000559 (bar: ≤0.04).
- **G-REPRO: PASS** (runner-computed `repro_gate.pass` = true).
- Per packet: PASS clears BER-2 only. BER-1 fix + re-verify still required
  pre-S2. No S2 entry in this record.
