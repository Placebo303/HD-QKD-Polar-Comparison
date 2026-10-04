Merged from openspec/changes/add-nbldpc-l1d2-synth-batch-runner (archived 2026-09-30, disposition: completed).

# NB-LDPC L1-degree2 Stage-2 synthetic batch runner

Track DECIDE. This change freezes the batch contract and authorizes NO
execution (DEC-1 still required). Any conflict with a frozen item below
resolves to STOP with an explicit reason. Named IDs only: GAP-6b / COND-3 /
DEC-1 (no bare `G6b / C3 / D1`).

## SHALL (frozen Stage-2 batch contract)

- The change SHALL add exactly the files in `proposal.md` §Impact scope and
  SHALL modify no existing file (in particular nothing under
  `openspec/changes/add-nbldpc-l1-degree2-layout/`, no `AGENTS.md` / memory /
  decision-log change).
- GAP-6b seeds SHALL be exactly: graphs n128 `2026093701-3706`, n256
  `2026093711-3716`; data n128 `2026093201,2026093202`, n256
  `2026093301,2026093302`; `frame_idx=0..7`; integers only are reused, no
  D12 output root is read, same integer ≠ same frame.
- The L2 map SHALL be the 12-row 1-to-1 rotation n128 `3701→2801 … 3706→2806`,
  n256 `3711→2901 … 3716→2906`; the frame stream SHALL be
  `call_seed = v10_seed("nbldpc-l1d2-s2c:{width}:{block_seed}:{frame_idx}")`.
- The prior chain SHALL be strict (A) D10 only
  (`prepare_model_f_prior_candidate → sample_matched_block → p1
  floor_renorm(DECODER_FLOOR)`, `DECODER_FLOOR=1e-15`,
  `AUDIT_FLOOR=1e-300`, column-sum tolerance `1e-8`, zero-mass fallback
  uniform `1/32`, LAMBDA_STAR=137.3823795883264); the (B) V80-S2C U2 GENIE
  chain SHALL be excluded.
- The decoder档 SHALL be `row-layered / max_iter=90 / damping=1.0 /
  warm=None / CHECK_UPDATED / oracle=False` on both arms; the exact command
  SHALL lock `--max-iter 90 --damping 1.0`; the D13 three-arm variant SHALL
  be excluded.
- Counting SHALL be `status ∈ {ok, nonconverged, resource_abort}` plus
  build-level `construction_failed`; `is_success = pair_exact ∧
  verify_accept ∧ ¬accepted_wrong` with `verify_accept = syn_l1 ∧ syn_l2`;
  `accepted_wrong` SHALL never merge into success; `resource_abort` SHALL
  count neither as success nor as zero-failure; syndrome agreement SHALL
  never substitute for exact; failed frames SHALL keep full attempted
  disclosure; blocked transfer (`transfer_invoked=False`) SHALL record a
  non-success, never a silent skip.
- Outputs SHALL use the 17-column fixed order (u1_exact, u2_exact,
  pair_exact, syn_l1, syn_l2, syn_joint, verify_accept, accepted_wrong,
  status, l1_syn_bits, l2_syn_bits, extra_parity_bits, verify_tag_bits,
  other_public_bits, rounds, wall_s, rss_b) keyed by (width, arm,
  graph_seed, block_seed, frame_idx, call_seed, transfer_invoked).
- Scale SHALL be dual-row: per-width `96` paired samples / `192` chains /
  `384` layered decode calls; both-widths total `192` / `384` / `768`. A
  bare "384" SHALL carry its row label.
- Budget SHALL be `wall≤7200s / RSS≤4GiB / single-chain≤120s`, single
  process, no retry/resume/sample-reduction/seed-change, canary inside the
  budget, over-cap STOP with results retained.
- `--canary` SHALL select the **minimum** graph seed × **minimum** data seed
  (sort-then-first, CLI-order-independent) × full frame list, both arms; its
  projection SHALL be advisory only.
- COND-3 SHALL gate n256 entry on `Δ≥6 and ≥4/6 graphs Δ_g>0` with zero
  accounting/undetected/authorization/resource violations; otherwise the
  record SHALL read "此冻结试验未给出足够机制信号", and zero-success /
  near-full-control SHALL read "区分能力不足/天花板受限".
- Out-roots SHALL be single fresh roots per width; existing roots SHALL
  refuse; `results/`, `comparison_bench/outputs_comparison/`, and existing
  workspace result roots SHALL refuse writes; `model-f-root` SHALL stay
  read-only.

## SHALL NOT

- This change SHALL NOT grant execution (no DEC-1); no `--execute` without
  a dated/signed DEC-1 authorization.
- No FER/SKR/qualification/promotion/publication conclusion from this batch.
- No bare `G6b / C3 / D1` identifiers.

## Future runner correction: per-chain wall time (2026-09-30)

This correction applies to future executions only. The completed n128 machine
artifacts and COND-3 decision are unchanged. It grants no new execution.

- The 24-column frame schema and order SHALL remain unchanged. `wall_s` SHALL
  measure each attempted complete layered chain (L1, any invoked L2, transfer
  and verification), rather than copying the pair elapsed time into both rows.
- The manifest MAY include `pair_timings` for the total elapsed time and
  actually attempted arms of each started pair. This diagnostic SHALL NOT
  replace frame `wall_s` or govern the single-chain cap.
- The 120 s cap SHALL apply to each attempted chain. An over-cap chain SHALL
  be recorded as `resource_abort`, retain its attempted disclosure, and STOP
  after the synchronous chain returns. If the first chain breaches the cap,
  the second SHALL NOT start or receive a fabricated frame row.
- The 7200 s cap SHALL retain the existing `execute_pairs` timing boundary
  from `t_batch` through the decode loop; setup and STOP-result persistence
  remain outside that clock. At or above 7200 s, the runner SHALL STOP before
  starting another chain. An unattempted chain SHALL have no frame row and
  SHALL NOT contribute success, failure, or disclosure counts.
- All frozen scientific inputs, decoder behavior, counting, output-root, and
  authorization rules above SHALL remain in force. A stopped batch remains
  incomplete and cannot enable conditional n256 entry.
