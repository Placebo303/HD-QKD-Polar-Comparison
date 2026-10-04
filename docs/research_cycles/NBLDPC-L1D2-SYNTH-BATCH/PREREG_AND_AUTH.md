# PREREG_AND_AUTH — NB-LDPC L1D2 Stage-2 synthetic batch (DECIDE, frozen)

- Cycle: `NBLDPC-L1D2-SYNTH-BATCH` (Stage-2 only; R2 of
  `NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT`).
- Track: **DECIDE** (Model-F bundle derived from the real-session CAL fit
  session=20260123_1M_600k_0dB, CAL 702-1725). Three-document form
  `PREREG_AND_AUTH.md` / `RESULT.md` / `INDEPENDENT_ACCEPTANCE.md` +
  Pre-EXECUTE + independent Pre-RESULT + main-thread acceptance.
- Status: PREREGISTERED & FROZEN; DEC-1 GRANTED 2026-09-30 for n128 ONLY (out-root b07b0f91); n256 NOT GRANTED (requires COND-3 + separate authorization); no execution has occurred yet.
- **This packet approval ≠ execution authorization.** P4: the new L055 is
  outside the `P4_FEAS_PACKET.md` F2(n=2048)/F3/F4 scope but is bound by the
  §4 procedural gate of
  `NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/PROPOSAL.md` → execution
  requires a new authorization covering the concrete scope (DEC-1, §9).
- Named IDs only: **GAP-6b / COND-3 / DEC-1** (no bare `G6b / C3 / D1`).
- Branch: `formal-ir-v72p1-addendum-clean`.

## §1 Science-input freeze table (GAP-6b)

| Item | Frozen value |
|---|---|
| Graph seeds n128 | `2026093701,2026093702,2026093703,2026093704,2026093705,2026093706` (40xx/41xx abandoned: collision with D16 `4001-4012/4101-4108`) |
| Graph seeds n256 | `2026093711,2026093712,2026093713,2026093714,2026093715,2026093716` |
| `_PRIOR` integer domain | D14N/D15/D16/D17/D18/D19/R23+weak/G6-R7/S1/CLI literals/V80 large intervals (2001,2011,5501-5560,5601-5840,6401-6640,6801,6811,7001-7440,7501-7564) |
| Data seeds n128 | `2026093201,2026093202`, `frame_idx=0..7` |
| Data seeds n256 | `2026093301,2026093302`, `frame_idx=0..7` |
| Integer reuse | 仅重用整数，不读 D12 输出根；同整数≠同帧 |
| L2 map (12-row 1-1 rotation) | n128 `3701→2801 … 3706→2806`; n256 `3711→2901 … 3716→2906` |
| Frame stream | `call_seed = v10_seed("nbldpc-l1d2-s2c:{width}:{block_seed}:{frame_idx}")` |
| Prior chain (strict (A) D10; (B) excluded) | `prepare_model_f_prior_candidate → sample_matched_block → p1 floor_renorm(DECODER_FLOOR)`; `DECODER_FLOOR=1e-15`, `AUDIT_FLOOR=1e-300`, column-sum tolerance `1e-8`, zero-mass fallback uniform `1/32`; LAMBDA_STAR=137.3823795883264; (B) V80-S2C U2 GENIE chain excluded |
| Decoder档 (dual-arm) | `row-layered / max_iter=90 / damping=1.0 / warm=None / CHECK_UPDATED / oracle=False` both arms; D13 three-arm (RL360 / damping 0.7 / FLOODING360) excluded |
| Counting | `status ∈ {ok, nonconverged, resource_abort}` + build-level `construction_failed`; `is_success = pair_exact ∧ verify_accept ∧ ¬accepted_wrong`; `verify_accept = syn_l1 ∧ syn_l2`; `accepted_wrong` isolated, never merged into success; `resource_abort` neither success nor zero-failure; syndrome agreement ≠ exact; failed frames full attempted disclosure, no refund; blocked transfer (`transfer_invoked=False`) non-success, never silently skipped |
| Model-F root (read-only) | `workspace/v72p2d5_model_f_input/20260907_r1` |

## §2 Exact commands (out-root UUID frozen at T5 Pre-EXECUTE, §10 S1)

n128 UUID = `b07b0f91` → out-root `workspace/nbldpc-l1d2-s2c-n128-b07b0f91`.
n256 UUID = `5b2240a0` → out-root `workspace/nbldpc-l1d2-s2c-n256-5b2240a0`
(frozen now; n256 runs only if COND-3 permits + separate authorization).

n128:

```
PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_l1d2_synth_batch_prod --width 128 --graph-seed 2026093701,2026093702,2026093703,2026093704,2026093705,2026093706 --data-seed 2026093201,2026093202 --frames 0-7 --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/nbldpc-l1d2-s2c-n128-b07b0f91 --max-iter 90 --damping 1.0 --wall-cap-s 7200 --rss-cap-bytes 4294967296 --chain-wall-cap-s 120 --execute
```

n256 (runs only if COND-3 permits, §7):

```
PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_l1d2_synth_batch_prod --width 256 --graph-seed 2026093711,2026093712,2026093713,2026093714,2026093715,2026093716 --data-seed 2026093301,2026093302 --frames 0-7 --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/nbldpc-l1d2-s2c-n256-5b2240a0 --max-iter 90 --damping 1.0 --wall-cap-s 7200 --rss-cap-bytes 4294967296 --chain-wall-cap-s 120 --execute
```

`--max-iter 90 --damping 1.0` is locked (the flags are CLI-overridable, so
any deviation voids this preregistration).

Real execution goes through the thin CLI `nbldpc_l1d2_synth_batch_prod`,
which assembles the production decode adapter `production_decode_fn`
(v35.decode_row_layered_fftqspa, fixed 90/1.0/warm=None/field=None,
ignoring layer); the runner body and frozen flags are unchanged; the
fake-only path remains with the original runner.

## §3 Single out-root + absence precheck

One fresh out-root per width (`workspace/nbldpc-l1d2-s2c-n128-b07b0f91`,
`workspace/nbldpc-l1d2-s2c-n256-5b2240a0`, frozen at T5, §10 S1). Pre-EXECUTE verifies each root
does not exist (e.g. `test ! -e <out-root>`); an existing root errors out
with no overwrite and no merge. `model-f-root` is read-only input.

## §4 Output schema (frozen order)

Per frame record, 7 key columns + 17 schema columns: width, arm,
graph_seed, block_seed, frame_idx, call_seed, transfer_invoked, then
u1_exact, u2_exact, pair_exact, syn_l1, syn_l2, syn_joint, verify_accept,
accepted_wrong, status, l1_syn_bits, l2_syn_bits, extra_parity_bits,
verify_tag_bits, other_public_bits, rounds, wall_s, rss_b.

## §5 Scale (dual-row arithmetic)

- Per-width row: 6 graphs × 2 data seeds × 8 frames = **96 paired samples**
  = **192 chains** (dual-arm) = **384 layered decode calls** (≤1×L1 + 1×L2
  per chain).
- Both-widths total row: **192 paired samples** / **384 chains** /
  **768 layered decode calls**.
- A bare "384" must carry its row label (per-width calls vs total chains).

## §6 Budget caps + canary

Caps: `wall≤7200s / RSS≤4GiB / single-chain≤120s`; single process; no
retry/resume/sample-reduction/seed-change; the canary counts against the
budget; over-cap STOP with results retained.

Canary: per width, the **minimum** graph seed × **minimum** data seed
(sort-then-first, CLI-order-independent) × frames 0-7, both arms (n128
`3701×3201`; n256 `3711×3301`). The projection is advisory only; promotion
is decided by the main thread.

## §7 Machine gate COND-3 (itemized decision procedure)

1. Compute per-graph `Δ_g` = candidate pair-exact − control pair-exact
   (6 graphs, n128), and total `Δ` = ΣΔ_g over 96 paired samples.
2. Check `Δ≥6` AND `≥4/6` graphs with `Δ_g>0`.
3. Check zero accounting/undetected/authorization/resource violations.
4. If all pass → run the frozen n256 arm only (no new rate/degree/seed
   scan). Else → STOP the conditional arm and record
   "此冻结试验未给出足够机制信号", never "NB-LDPC 不行".
5. Degenerate cases: both arms zero success, or control near-full success →
   record "区分能力不足/天花板受限"; no model change.

## §8 No-overwrite + forbidden zones

No writes to `results/`, `comparison_bench/outputs_comparison/`, or any
existing workspace result root. No modification of any existing file. No
`.ttbin`/real-input contact beyond the frozen read-only Model-F root. No
production decoder binding beyond the frozen packet (execution without
DEC-1 refuses).

## §9 P4/DEC-1 authorization statement (filled at T5 Pre-EXECUTE, 2026-09-30)

> I authorize the single frozen execution in §2 (n128; n256 only if COND-3
> permits) under caps in §6, with no scope change. This authorization
> (DEC-1) covers the concrete new-L055 Stage-2 range per
> `NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/PROPOSAL.md` §4 and does not
> revoke any standing P3/P4/D7-H/Joint-MARGINAL verdict.
>
> Date: 2026-09-30
>
> Authorization basis: User explicitly delegated decision authority to the
> orchestrator + independent reviewer for this DECIDE cycle
> (NBLDPC-L1D2-SYNTH-BATCH n128); user retains final self-check before
> acceptance.
>
> Scope (frozen, no expansion): branch `formal-ir-v72p1-addendum-clean`;
> new L055 second-degree directed layout; graph seeds n128
> 2026093701-3706; L2 2801-2806; data seeds 2026093201,2026093202 ×
> frame 0-7; prior chain (A) D10; decoder档
> row-layered/90/1.0/warm=None/CHECK_UPDATED/oracle=False; output root
> limited to the S1-filled n128 out-root
> `workspace/nbldpc-l1d2-s2c-n128-b07b0f91`; budget wall≤7200s /
> RSS≤4GiB / single-chain≤120s.
>
> Explicit exclusions: this authorization does NOT cover n256 (n256 needs
> COND-3 pass plus a separate authorization); does NOT cover other
> graphs/seeds/real data; does NOT lift the historical P4 FROZEN NOT
> GRANTED; does NOT constitute route acceptance.
>
> Signature: Recorded per explicit user delegation (see authorization basis
> above); countersigned by independent reviewer — see INDEPENDENT_ACCEPTANCE
> at T9.

## §10 Sign-off list S1-S8

| ID | Item | State |
|---|---|---|
| S1 | OUT_ROOT UUID (frozen at T5) | ☑ FILLED 2026-09-30 — n128 `workspace/nbldpc-l1d2-s2c-n128-b07b0f91`, n256 `workspace/nbldpc-l1d2-s2c-n256-5b2240a0` (§2) |
| S2 | Exact command path/module | ☐ pending sign-off: ______ |
| S3 | Prior-chain numerics (§1) | ☑ CONFIRMED by user — signature retained: ______ |
| S4 | Stream naming (`call_seed` formula) | ☐ pending sign-off: ______ |
| S5 | V80 integer domain (decided = included) | ☑ CONFIRMED by user — signature retained: ______ |
| S6 | Seeds / L2 / decoder / gate / budget confirmation | ☐ pending sign-off: ______ |
| S7 | P4/DEC-1 date + signature (§9) | ☑ FILLED 2026-09-30 — recorded per explicit user delegation (n128 only; n256 excluded pending COND-3 + separate auth); reviewer countersignature at T9 INDEPENDENT_ACCEPTANCE |
| S8 | Preregistration acceptance (main thread) | ☑ ACCEPTED 2026-09-30, by orchestrator per user delegation |

T5 BLOCKER-7 status: RESOLVED 2026-09-30 (production decode adapter + thin prod CLI added; 33 frozen tests unchanged).

## §11 Claim ceiling

No FER/SKR/qualification/promotion/publication conclusion. The batch
supports only "whether a next packet is worth drafting".
