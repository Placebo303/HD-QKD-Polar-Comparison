# Design — NB-LDPC L1-degree2 Stage-2 synthetic batch runner

Change `add-nbldpc-l1d2-synth-batch-runner`. Track DECIDE. Approval is not
execution authorization (DEC-1 still required per `proposal.md`). Claim
ceiling: no FER/SKR/qualification/promotion/publication conclusion; the batch
supports only "whether a next packet is worth drafting".

## §1 Frozen seeds and L2 map (GAP-6b)

- Graph seeds: n128 `2026093701-3706`; n256 `2026093711-3716` (the 40xx/41xx
  range is abandoned: collision with D16 `4001-4012/4101-4108`).
- `_PRIOR` integer-domain full set includes D14N/D15/D16/D17/D18/D19/R23+weak/
  G6-R7/S1/CLI literals/V80 large intervals (2001,2011,5501-5560,5601-5840,
  6401-6640,6801,6811,7001-7440,7501-7564).
- Data seeds: n128 `2026093201,2026093202`; n256 `2026093301,2026093302`;
  `frame_idx=0..7`. Recorded declaration: "仅重用整数，不读 D12 输出根；
  同整数≠同帧" (integers only are reused; no D12 output root is read;
  same integer ≠ same frame).
- L2 map, 12 rows of 1-to-1 rotation: n128 `3701→2801 … 3706→2806`;
  n256 `3711→2901 … 3716→2906` (one shared DV3 L2 per L1 pair).
- Frame stream naming:
  `call_seed = v10_seed("nbldpc-l1d2-s2c:{width}:{block_seed}:{frame_idx}")`.

## §2 Prior chain (strict (A) D10; (B) excluded)

Strict (A) D10 chain only:
`prepare_model_f_prior_candidate → sample_matched_block → p1
floor_renorm(DECODER_FLOOR)` with `DECODER_FLOOR=1e-15`,
`AUDIT_FLOOR=1e-300`, column-sum tolerance `1e-8`, zero-mass columns fall
back to uniform `1/32`; LAMBDA_STAR=137.3823795883264.
The (B) V80-S2C U2 GENIE chain is excluded.

## §3 Decoder档 (dual-arm, locked)

`row-layered / max_iter=90 / damping=1.0 / warm=None / CHECK_UPDATED /
oracle=False` on both arms. The D13 three-arm variant (RL360 / damping 0.7 /
FLOODING360) is excluded. The exact command must lock
`--max-iter 90 --damping 1.0`.

## §4 Counting (four-state, F-4)

`status ∈ {ok, nonconverged, resource_abort}` plus build-level
`construction_failed`. `is_success = pair_exact ∧ verify_accept ∧
¬accepted_wrong`; **verify_accept = syn_l1 ∧ syn_l2**. `accepted_wrong`
(undetected) has its own column and is never merged into success.
`resource_abort` counts neither as success nor as zero-failure. Syndrome
agreement never substitutes for exact. Failed frames keep full attempted
disclosure with no refund. A blocked transfer (`transfer_invoked=False`)
runs no L2 and is recorded as a non-success, never silently skipped.

## §5 Output schema (frozen order)

Frame-record schema, 17 columns in fixed order: u1_exact, u2_exact,
pair_exact, syn_l1, syn_l2, syn_joint, verify_accept, accepted_wrong,
status, l1_syn_bits, l2_syn_bits, extra_parity_bits, verify_tag_bits,
other_public_bits, rounds, wall_s, rss_b. Each frame record is additionally
keyed by 7 leading columns: width, arm, graph_seed, block_seed, frame_idx,
call_seed, transfer_invoked.

## §6 Scale (dual-row; bare "384" must carry a row label)

- Per-width row: `96` paired samples / `192` chains / `384` layered decode
  calls.
- Both-widths total row: `192` paired samples / `384` chains / `768` layered
  decode calls.

## §7 Budget and canary

- Budget: `wall≤7200s / RSS≤4GiB / single-chain≤120s`; single process; no
  retry/resume/sample-reduction/seed-change; the canary counts against the
  budget; on cap breach STOP with results retained.
- Canary: per width, the **minimum** graph seed × **minimum** data seed ×
  frames 0-7, both arms (n128 `3701×3201`; n256 `3711×3301`),
  sort-then-first, independent of CLI argument order. The `--canary` help
  text reads "minimum graph seed x minimum data seed". The projection is
  advisory only; promotion is decided by the main thread.

## §8 Gate COND-3

COND-3: `Δ≥6 and ≥4/6 graphs Δ_g>0`, and no accounting/undetected/
authorization/resource violation, before entering n256. Otherwise record
"此冻结试验未给出足够机制信号" (this frozen trial gives insufficient
mechanism signal), never phrased as "NB-LDPC 不行" (NB-LDPC fails). Zero
success on both arms / near-full control records "区分能力不足/天花板受限"
(insufficient discrimination / ceiling-limited).

## §9 Out-root protection

An existing out-root errors out without overwrite. Refuse writes to
`results/`, `comparison_bench/outputs_comparison/`, and any existing
workspace result root; `model-f-root` is read-only.

## §10 Deferred items (carried, not decided here)

DFR-* are engineering deferred-item numbers and are unrelated to the S1–S8
sign-off list in PREREG_AND_AUTH.md.

- DFR-2: DFR-2 single-chain wall is the conservative dual-arm shared total;
  per-arm timing may replace it before DECIDE.
- DFR-4: `--max-iter/--damping` are CLI-overridable, hence the exact command
  must lock them (`--max-iter 90 --damping 1.0`).
- DFR-5: `AUDIT_FLOOR` reuses the d5 constant without a local alias.
- DFR-6: worktree-concurrent untracked files require manual Pre-EXECUTE
  confirmation of the batch boundary against the file manifest.
