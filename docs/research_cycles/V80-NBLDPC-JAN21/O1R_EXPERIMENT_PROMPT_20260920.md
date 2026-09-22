# O1R Operator Prompt (2026-09-20) — needs fresh grant + Pre-EXECUTE; authorizes NOTHING

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). Packet `O1R_EXPERIMENT_PACKET_20260920.md` (G-O1R, frozen). One arm per invocation, sequential R1→R2.
- Pre-EXECUTE Q0–Q6 first: branch; scope cleanliness; frozen contract; rg-absence proofs (`2026095601–5840`, `2026092011`, `o1r_`); fresh `workspace/o1r_<uuid8>` absence per arm; focused tests green (incl. R2 pin dry-construction fc0/g8/rank-full + construct-twice; mismatch → STOP).
- R1: `--arm A208 --root workspace/o1r_<uuid8> --block-base 2026095601 --n-blocks 240 --construct-seed 2026092001 --de-label covered` (+ dual execute flags).
- R2: same with a fresh root + `--construct-seed 2026092011`.
- Gates/arm: fails/240 ≤ 12 AND f_super 1.294947 ≤ 1.3; report per-60 tally (quarters ≤3 fails, informational); early-stop at 13th fail (retain partials); no rerun/no tuning.
- Budgets: wall ≤3600 s/window/arm (≈600 s est, ≤900 s budget); per-decode 300 s; RSS <4 GiB; ≤1 wall-partial `--resume-from` per arm; FAIL never resumes.
- Genie-u1 D1 ceiling; D_blind measured-0 + sensitivity; f_L2 informational; blind-risk line carried.
- Deliver per arm: manifest/`rows.json`/`block_accounting.csv` + `O1R_RESULT_20260920.md`; ceiling §8 (no L1/S3/real-data/route claim).
- Return: arm verdicts, pooled FERs, tallies, budgets, concrete blocker (if any) + single decision needed. Deltas only.
