# V27R Freeze-Review Packet — verified reference data & audit

> Purpose: pre-verified reference for the independent Luna freeze review of the
> V27R OpenSpec (source-adaptive finite-leakage-margin gate). All numbers below
> were recomputed by the main thread from the frozen V25 `channel_counts.npz`
> (run_04) using the committed V26 channel adapter. This packet is for the
> reviewer; it does NOT substitute for the independent review.

## P001 — V26 archived-reference evidence (closed)
- V26 archive: comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/
- run_01 `gate.json`: status `pass_target_f13`; `passed.A02=[1.3]`, `best_passing_f.A02=1.3`.
- run_01 `readonly_verify.json`: ok=true, screen_n_calls=72 (0 mismatch),
  confirm_n_calls=60 (0 mismatch), a02_f13_confirmed=30/30,
  gate_recomputed=pass_target_f13.
- Conclusion: V26 is a valid archived reference (asymptotic A02 f=1.3 30/30).
- V26 DE must NOT be rerun (V27R docs forbid it).

## P002 — frozen per-source full-precision entropies (from channel_counts.npz, F03=A02)
| source | H1 (bits/sym) | H2 (bits/sym) | H_total |
|--------|--------------:|--------------:|--------:|
| 1M     | 0.024280547   | 0.776757278   | 0.801037825 |
| 1p5M   | 0.025199497   | 0.800366555   | 0.825566052 |
| 2M     | 0.025662049   | 0.806900673   | 0.832562722 |

(command: load_channel_counts -> build_adapter(F03) -> adapter_entropy_bits; verified 2026-08-19/20)

## Frozen source-adaptive m_total table — verified
`m_total = floor((1.3*block_len*H_source - 64)/5)`

| source | n=1024 | 2048 | 4096 | 8192 |
|--------|-------:|-----:|-----:|-----:|
| 1M     | 200    | 413  | 840  | 1693 |
| 1p5M   | 206    | 426  | 866  | 1745 |
| 2M     | 208    | 430  | 873  | 1760 |

## m1_ep (round(m_total*H1/H_total), Python round) — verified
| source | n=1024 | 2048 | 4096 | 8192 |
|--------|-------:|-----:|-----:|-----:|
| 1M     | 6      | 13   | 25   | 51   |
| 1p5M   | 6      | 13   | 26   | 53   |
| 2M     | 6      | 13   | 27   | 54   |

Candidates per cell: m1 in {m1_ep-2,...,m1_ep+2}, m2 = m_total - m1. All cells legal
(m1 in [4..56], m2 in [194..1720], both < n => R1,R2 in (0,1)).

## Realized total f = (5*m_total + 64)/n/H_total — verified < 1.3 (all 12 cells)
1M: 1.29715 / 1.29775 / 1.29958 / 1.29974 (n=1024/2048/4096/8192)
1p5M: 1.29409 / 1.29764 / 1.29942 / 1.29956
2M: 1.29495 / 1.29847 / 1.29876 / 1.29964
=> all < 1.3, positive but small finite headroom.

## Required spec items vs docs (main-thread self-check, for reviewer confirmation)
1 source-adaptive: proposal What-1, design §2; 2 frozen table: design §2.2, spec R2;
3 m1_ep+±2: design §2.3, spec R2 (all five eligible); 4 asymptotic
true-predecessor DE + tag only in total leakage: design §1, spec R1; 5 source/delay
selector no repeated billing: design §1, spec R1; 6 block_len vs mc_samples distinct:
design §4, spec R3/R4; 7 ordering keys: design §4, spec R4; 8 screen-then-
ranked-confirmation: design §4/§5, spec R4; 9 same block_len 3-source pass + min:
design §5, spec R4/R5; 10 terminal states only 4 (no fixed_ensemble_margin_fail):
design §6, spec R5; 11 24h completed-call gate + checkpoint bound to frozen config:
design §7, spec R6; 12 V26 archived only no rerun: design §8, spec R6; 13 independent
freeze review (this): tasks Phase A; 14 P102 by main thread after P0/P1: proposal
Status, tasks Phase A.

## Verdict placeholder
[To be filled ONLY by the independent freeze review.]
