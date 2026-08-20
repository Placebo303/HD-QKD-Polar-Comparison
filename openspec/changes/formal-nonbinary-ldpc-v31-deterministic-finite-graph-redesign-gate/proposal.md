# V31 — deterministic finite-graph redesign gate (projective-capacity-aware PEG + QC-cyclic control)

Status: FROZEN_BY_USER_OBJECTIVE (new user-authorized change, 2026-08-20). The explicit V31 goal text is the authorization; implementation and one pre-registered execution are authorized, with no qualification/promotion.
This is a NEW change generated from the explicitly authorized V31 objective. It
does not expand or rerun the archived V30R packet. The V30R balanced-projective
packets and their PEG-projective-cycle-cancelled packets are frozen and must
not be re-executed.

## What

Create and execute a new deterministic finite-graph redesign gate that keeps the
successful V25 source/delay-conditioned empirical channel, the V26
channel-informed F03 GF(32)+GF(32) multilevel DE, and the frozen leakage/tag
accounting, but replaces the V30R graph families with a deterministic
projective-capacity-aware construction and a deterministic QC-cyclic control
family. The gate runs at both `n=1024` and `n=2048`.

The gate has the following phases:

- M0: read-only predecessor audit (V25/V26/V28R/V30R bindings and the frozen
  field/entropy/leakage authority). No modification of predecessor evidence.
- M1: pre-registered 30-call DE confirmation for the single fixed allocation
  `m1=16`, independently for each block length `n in {1024, 2048}`. Each
  block length must pass its own 30/30 confirmation (5 seeds × 3 sources ×
  2 layers) before any matrix construction for that length.
- M2: deterministic matrix construction for each passing block length with two
  families:
  1. `PEG-capacity-aware` — progressive-edge-growth support selection that is
     explicitly projective-capacity-aware: every support pair `(a,b)` is
     hard-limited to at most 31 columns (one per nonzero GF(32) ratio), and the
     support score includes current occupancy;
  2. `QC-cyclic-projective` — a deterministic quasi-cyclic control family built
     from cyclic shift supports, with the same frozen coefficient-label rule
     (projective uniqueness + bounded Tanner-6 cancellation).
  No random matrix-library search, no seed adjustment, and no rerun of any
  V30R balanced packet is permitted.
- M3: Bob-only validation gate on the V25 validation frames at both n, per
  family per n: full validation window (100 blocks/source for n=1024, 50
  blocks/source for n=2048), recording per-block syndrome convergence,
  exact/tag FER, waterfall (cumulative success curves), and failure positions.
  The gate closes with `finite_graph_pass` or `finite_graph_fail`, with
  pre-registered per-source thresholds.

## Why

V30R (`finite_graph_fail`, 2026-08-20) showed that the tested `n=1024` F03
balanced-projective and PEG-projective-cycle-cancelled families did not convert
the successful V26 DE into a finite-code validation pass. The V30R report
explicitly recorded the successor hypotheses: raise shared L1 toward `m1=16`,
make PEG support selection projective-capacity-aware, impose structured
QC/SC/protograph control, and test `n=2048`. This change is the user-authorized
implementation of exactly that successor hypothesis set, with strict
deterministic construction and no tuning.

The two family control arms are necessary to separate the effects of the PEG
capacity-aware support rule from the structured-control baseline: if the
capacity-aware PEG fails while the QC-cyclic control succeeds, the bottleneck is
in the PEG support/label interaction; if both fail, it is upstream (allocation,
decoder, channel conversion); if both pass, the earlier V30R failure is
attributable to the specific V30R families/allocation.

## Frozen input binding (V25/V26/V28R/V30R)

All source/evidence inputs resolve through the existing repository-relative
paths and identifiers:

| source_id | pairs path | delay_used_ps | label |
|---|---|---:|---|
| `type2_1M_20260121_184040` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet` | -50 | `1M` |
| `type2_1p5M_20260121_183806` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet` | +50 | `1p5M` |
| `type2_2M_20260121_183657` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet` | +50 | `2M` |

Authority files:

- V25 inventory:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
- V25 split manifest:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`
- V25 channel counts:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`
- V26 canonical: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
- V28R canonical: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
- V30R canonical (read-only predecessor): `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01/`

Field binding: `GF2mField.create(32)`, primitive polynomial `0b100101`, V28R
field_id
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, zero-based
`ratio_index` into the field's `nonzero_cycle`.

F03 layer entropies (float64 authority from V26 canonical M0
`detail["A02:<source_id>"].adapter_H`):

| source | H_L1 bits/symbol | H_L2 bits/symbol | H_total |
|---|---:|---:|---:|
| 1M | 0.0242805468186788 | 0.7767572780789986 | 0.8010378248976774 |
| 1p5M | 0.02519949687785432 | 0.8003665547438693 | 0.8255660516217236 |
| 2M | 0.02566204879687012 | 0.8069006731253252 | 0.8325627219221954 |

## Frozen allocation and leakage

Allocation is fixed: `m1 = 16` for all sources and block lengths.
`m2 = m_total - 16`.

| n | source | m_total | m2 = m_total-16 | leak_total = 5*m_total+64 | f_total |
|---|---:|---:|---:|---:|---:|
| 1024 | 1M | 200 | 184 | 1064 | 1.2971453628 |
| 1024 | 1p5M | 206 | 190 | 1094 | 1.2940931533 |
| 1024 | 2M | 208 | 192 | 1104 | 1.2949474816 |
| 2048 | 1M | 413 | 397 | 2129 | 1.29775 |
| 2048 | 1p5M | 426 | 410 | 2194 | 1.29764 |
| 2048 | 2M | 430 | 414 | 2214 | 1.29847 |

`m_total` for n=1024 comes from V30R; m_total for n=2048 comes from the V27
frozen budget table (1M=413, 1p5M=426, 2M=430). All `f_total < 1.3`.

Per-layer DE: `R_i = 1 - m_i/n`, `leak_i = 5*m_i` bits,
`f_i = leak_i/(n*H_i)`. The 64-bit tag is excluded from single-layer DE and is
included only in the block-level total.

## In scope

- GF(32), F03 natural MSB→LSB GF32+GF32, `lambda={2:1}`;
- V25 source/delay-conditioned channel posterior (V26 adapter, train-only);
- `m1=16` only; n ∈ {1024, 2048};
- two deterministic finite families:
  `PEG-capacity-aware` and `QC-cyclic-projective`;
- per-block syndrome convergence, exact/tag FER, waterfall, failure positions,
  and a pre-registered finite pass/fail;
- read-only verifier that rebuilds manifests/audits/registries/FER summaries
  without rerunning DE or the decoder.

## Out of scope

- rerunning, expanding, or tuning any V30R packet or its balanced/PEG families;
- random matrix-library search, seed libraries, random tie-breaks, or tuning;
- qualification, promotion, V29 holdout, raw `.ttbin`, or public residual
  claims;
- changing the V25 channel split, F03 factorization, GF(32) field, decoder, or
  leakage/tag accounting;
- MET, joint protograph search, or new decoder development.

## Terminal states

- `de_allocation_fail` — at least one block length fails its pre-registered
  30/30 DE confirmation;
- `finite_graph_fail` — DE passes but no family passes the finite validation
  thresholds at every required block length;
- `finite_graph_pass` — each block length has at least one family passing all
  per-source thresholds with zero false accepts;
- `resource_blocked` — 24h DE or decoder cumulative meter exhausted;
- `implementation_blocked` — unhandled implementation failure.

Only after the read-only verifier returns `ok=true` with no problems is the
terminal treated as final, and then only as a finite development-gate result
(pass/fail), never as qualification or promotion.
