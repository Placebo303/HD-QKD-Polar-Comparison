# D0 — Full failure signature (read-only)

- records_total: 247; arm counts: {'B5': 1, 'B0': 6, 'B1': 60, 'B2': 60, 'B3': 60, 'B4': 60}
- B5 import control: imported=300, integrity_ok=True
- signature_mismatch: False
- P-i_B1_active_divergence: passed=True violations=0
- P-ii_B2_sentinel_not_run: passed=True violations=0
- P-iii_B3B4_improve_no_syndrome: passed=True violations=0

## arm×source means (L2 initial→final, NLL bits/symbol)

| arm|source | n | l2_init_mean | l2_final_mean | nll_bpsym_mean |
|---|---|---|---|---|
| B0|1M | 2 | 0.0 | 0.0 | 1.6e-05 |
| B0|1p5M | 2 | 0.0 | 0.0 | 1.5e-05 |
| B0|2M | 2 | 0.0 | 0.0 | 1.4e-05 |
| B1|1M | 20 | 234.95 | 457.8 | 0.223851 |
| B1|1p5M | 20 | 251.15 | 480.15 | 0.239375 |
| B1|2M | 20 | 251.55 | 478.0 | 0.238665 |
| B2|1M | 20 | 234.95 | 1024.0 | 0.223356 |
| B2|1p5M | 20 | 251.15 | 1024.0 | 0.238993 |
| B2|2M | 20 | 251.55 | 1024.0 | 0.238232 |
| B3|1M | 20 | 250.65 | 179.15 | 0.000846 |
| B3|1p5M | 20 | 261.8 | 180.95 | 0.000925 |
| B3|2M | 20 | 261.65 | 178.75 | 0.000832 |
| B4|1M | 20 | 250.65 | 175.75 | 0.000822 |
| B4|1p5M | 20 | 261.8 | 181.3 | 0.000806 |
| B4|2M | 20 | 261.65 | 178.75 | 0.000713 |
