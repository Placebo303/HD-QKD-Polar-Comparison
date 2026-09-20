# V80 S2 FER Campaign — Operator Prompt (2026-09-20, EXPLORE, NOT AUTHORIZED)

- Execute ONLY after fresh explicit grant + Pre-EXECUTE Q0–Q6 PASS. This prompt alone authorizes nothing.
- Branch: `formal-ir-v72p1-addendum-clean`. Root: `workspace/s2_fer_<uuid8>` (fresh, absence-proven). Single shot per arm; no resume.

## Pre-flight asserts (STOP on any mismatch)
- `construct_l2(2026092001)["four_cycles"]==1158`; suite 7 passed; manifest hashes match; `rg` absence of `20260960xx/61xx/63xx` seeds.

## Run V1 (60 groups × 4 frames)
- For g in 0..59, f in 0..3: `smoke_decode_frame(V1, seed=2026096001+4g+f, max_iter=300)` on `qsc_pair_sampler` (p=0.05).
- Frame-ok := exact_match; group accept := all-4-ok (`evaluate_superframe`, D_blind=0).
- Halt at 4th group failure → FAIL (retain partials). Caps: wall ≤3600 s, RSS ≤4 GiB, 1 CPU.

## Verdict + records
- PASS iff fails/60≤5% AND (1044+D_blind)/852.544≤1.3. Write result doc + rows.json + group_accounting.csv under run root only.
- V2 (`construct_l2(2026096101, max_trials=100)`, seeds 2026096301+idx) runs IFF V1 verdict=FAIL and four_cycles<1158; else STOP.
- No retry/tuning/reseed/arm-hop. Report deltas + IDs only. D_blind sensitivity line (16 bits≈+0.019) mandatory in result.
