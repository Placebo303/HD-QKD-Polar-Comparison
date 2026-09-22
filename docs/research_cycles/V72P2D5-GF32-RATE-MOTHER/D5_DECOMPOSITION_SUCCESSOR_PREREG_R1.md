# D5 decomposition successor preregistration R1 (decoder-blind, development-only)

- status: `PREREGISTRATION / FROZEN / DEVELOPMENT_ONLY / NO_FORMAL_EXECUTION_AUTHORIZATION`
- repo: `D:\Code\HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`
- packet: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_AND_DECOMPOSITION_SUCCESSOR_R1_TASK_PACKET.md` (FROZEN_TASK_PACKET, §§4.1–4.7 frozen verbatim in substance below)
- premise: `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED` (`D5_ROUTE_STOP_REVIEW_PASS` accepted)
- rule: this commit MUST predate every new candidate score and every decoder call in this packet (prove with commit time + command log)

## 4.1 Candidate family

Interpret each Alice symbol `A in [0,1023]` as ten little-endian bits `b0..b9`.

For every ordered first-layer subset `S1`, where `S1` is one of all `C(10,5)=252` sorted five-bit subsets:

- `S2` is the sorted complement.
- `U1` packs bits in `S1` in ascending source-bit order.
- `U2` packs bits in `S2` in ascending source-bit order.
- reconstruction places those bits back into their original positions.

This is a complete, finite family of 252 reversible bit permutations. The existing mapping is control `S1=(5,6,7,8,9)`; the swapped mapping is control `S1=(0,1,2,3,4)`.

No XOR mixing or general linear transform is in scope.

## 4.2 CAL-only model and folds

- Use only canonical CAL-TRAIN 702..1725 and the accepted R2 total-concentration/backoff contract.
- Use the existing four frozen outer folds and the already accepted concentration-selection semantics. Do not read VAL.
- For each partition derive held-out `CE_L1 = CE(U1|B)` and oracle-conditional `CE_L2 = CE(U2|U1,B)` from the transformed symbols/counts.
- Independently verify reversibility over all 1024 symbols, normalization, finite values, fold accounting, and the chain identity against joint held-out NLL within numerical tolerance.

## 4.3 Selection rule (decoder-blind)

For each partition compute four-fold mean `CE_L1`, `CE_L2`, and `CE_joint` plus fold dispersion. Compute development row indications at `n=64`, `f=1.2`:

```text
m1 = ceil(64 * CE_L1 * 1.2 / 5)
m2 = ceil(64 * CE_L2 * 1.2 / 5)
```

Rank all 252 partitions lexicographically by:

1. `max(CE_L1, CE_L2)` ascending;
2. `CE_joint` ascending;
3. `CE_L1` ascending;
4. `S1` lexicographically ascending.

Freeze the first three ranked partitions before decoder calls. Always include the two controls even if they are not top three. Deduplicate identical partitions. Decoder results may not alter this list or any row count.

## 4.4 Development decoder matrix

Use explicit function injection only. Use accepted R2 candidate priors transformed under each partition. Use fixed paired seeds `2026090600..2026090607` for all candidates and controls.

For each frozen candidate/control:

- rate point: use its preregistered `(m1,m2)` only if both are `<64`; otherwise label `NONZERO_RATE_INELIGIBLE` and do not silently cap it;
- square diagnostic: `(64,64)`;
- decode L1 then APP-propagated L2; oracle-L2 may be recorded only as a diagnostic;
- use the existing deterministic square/nested-mother construction and historical GF32 decoder, cold start, `max_iter=90`, `damping=1.0`;
- record exact and syndrome flags separately, iterations, nonfinite/crash, per-call wall, RSS, partition, seed, rows, and whether the call is APP or oracle.

Do not use a decoder result to tune anything. A deterministic implementation bug may be fixed within the allowlist with a test; a scientific ambiguity is a STOP.

## 4.5 Development classifications

Classify only the decoder-blind rank-1 partition at its non-square point:

- `DECOMPOSITION_STRONG_N64_RECOVERY`: both rows `<64`, end-to-end APP exact at least `6/8`, zero nonfinite/crash, zero syndrome/exact disagreement, and square exact count is not lower than non-square.
- `DECOMPOSITION_WEAK_N64_SIGNAL`: both rows `<64`, APP exact `1..5/8`, with zero nonfinite/crash and zero syndrome/exact disagreement.
- `DECOMPOSITION_NO_N64_RECOVERY`: both rows `<64`, APP exact `0/8`.
- `DECOMPOSITION_NO_NONZERO_RATE_CANDIDATE`: rank-1 has `m1>=64` or `m2>=64`.
- `DECOMPOSITION_MODEL_OR_IMPLEMENTATION_BLOCKED`: required invariants cannot be established.

These are development routing labels, not formal results. Do not relabel syndrome-only success as exact recovery.

## 4.6 Autonomous implementation branch

Only `DECOMPOSITION_STRONG_N64_RECOVERY` authorizes implementation of an additive, nonformal candidate in this packet.

If strong:

1. Create an OpenSpec change first, named `v72p2d5-decomposition-successor-r1`.
2. Implement only the minimum reversible mapping/prior/development-runner functions needed to reproduce the selected partition.
3. Keep the existing formal mapping, production wiring, roots, constants, CLI phases, and accepted artifacts unchanged.
4. Add focused tests for all-1024 round trip, controls, probability axes/normalization, decoder isolation, no formal-root writes, exact/syndrome separation, and deterministic replay.

If weak, none, or ineligible: do not add production code or an OpenSpec implementation change. Return the evidence and route terminal for main-thread choice. In particular, do not auto-fallback to graph or scheduling work.

## 4.7 Budgets

- Maximum decoder calls: 600.
- Maximum wall for all development decoder calls: 6 hours.
- Per-call watchdog: 120 seconds.
- RSS ceiling: 2 GiB; unknown RSS blocks a strong classification.
- At most one execution per frozen partition/seed/row/mode cell; no retries.
- CAL-only selection calculations do not count as decoder calls but must be timed and recorded.

(End of preregistration — family, ordering, thresholds, budgets frozen; no scores computed, no decoder invoked at commit time.)
