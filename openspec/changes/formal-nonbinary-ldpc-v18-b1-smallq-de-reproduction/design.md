# Design: formal-nonbinary-ldpc-v18-b1-smallq-de-reproduction

## 0. Status
PLANNING — M0 engineering.

## 1. Reuse contract
- `nonbinary_v10_de.run_de_search` for DE/rand/1/bin search.
- `nonbinary_v8_mcde` for independent MC-DE oracle constants.
- q=4 anchor from V8 REPRODUCTION_* constants.
- New change uses new seeds and new evidence identities.

## 2. Smoke budget
- pop_size=8, max_gen=2, F=0.85, CR=0.7
- n_samples=2000, max_iter=30
- q=4, rate=0.75, p_gate=0.069
- deterministic seed from new change

## 3. PASS/FAIL for production (future)
- Each reproduced row |ΔDET| <= 0.012 vs published.
- execute-once + strict replay.
- M0 does not gate anything.
