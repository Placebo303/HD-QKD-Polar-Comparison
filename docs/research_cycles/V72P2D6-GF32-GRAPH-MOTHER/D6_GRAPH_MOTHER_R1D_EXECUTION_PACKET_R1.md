# D6 graph/mother R1d execution packet R1 (Pre-EXECUTE freeze, NOT authorized)

Status: `R1D_PRE_EXECUTE_FROZEN_NOT_AUTHORIZED`. This packet authorizes nothing:
no R1d execution, rerun, resume, `--phase`, G1/G2, VAL, or real/raw data.
No R1d root was created (and none may be created under this packet).
All authorization keys remain false; `evidence_root`/`terminal` remain null.
`next_gate`: `D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.

## 1. Exact future command (frozen; DO NOT RUN without explicit authorization)

```text
python scripts/v72p2d6_graph_mother_development.py --r1d \
  --model-f-root <CAL-ONLY-Model-F-artifact-root> \
  --out-root workspace/d6_graph_mother_r1d_<uuid>/ \
  [--workers 18]
```

- `--model-f-root`: explicit, no default (accepted CAL-only Model-F artifact).
- `--out-root`: one fresh UUID root; refuses overwrite; named A2/VOID roots
  refused. No R1d root currently exists (verified §7).
- `--workers`: requested 18 with reviewed RSS-only downgrade 18→14→12→8
  (frozen R1c-A1 pilot sizing; unknown→`D6_RSS_UNKNOWN_BLOCKED`,
  over-limit→`D6_RSS_LIMIT_BLOCKED`).
- No `--phase` flag exists. No G1/G2/VAL/real/raw contact.

## 2. Dispatch set (26 structure cells, §4 proof table in the acceptance doc)

- Canary (mandatory): `{B0,B1,T1}` × n64 × 4 canary seeds × {f1.2 (59,52),
  square (64,64)} × {L1 + APP-L2 + oracle-L2 diagnostic} = 72 invocations.
- Confirmation (iff T1 advances, f1.2 APP exact ≥1/4): T1 × n64 × 16 seeds ×
  {f1.0, f1.2, square} = 144 invocations; strong ≥12/16, partial 1..11/16,
  both requiring f1.0 ≤ f1.2 ≤ square, zero crash/nonfinite, zero APP
  exact/syndrome disagreement, known RSS <2 GiB.
- Scaling (iff no new arm reaches 1/4 at n64 f1.2): T1 ONLY × 4 scaling seeds
  × {f1.2, square} at n128 (24), then n256 (24) if silent; stop at first
  signaling width; ≤1-arm confirmation by the same rules (144 each).
- Worst case 552 scientific + small setup ≤ 2500 total. Every dispatched
  `(arm,n,layer,prefix)` is asserted in `R1D_VALID_SUBSET` with live I1
  recheck before any decoder binding; anything else is a hard failure.

## 3. Frozen science (unchanged from prereg R1)

Decomposition `A = 32*U1 + U2`; E2 total-concentration/backoff prior
(`LAMBDA_STAR = 137.3823795883264`, floors 1e-300/1e-15, probability-domain
transfer); GF32 poly 37; historical row-layered FFT-QSPA (cold start,
max_iter=90, damping 1.0, warm_beliefs None); L1→APP-L2 schedule, oracle
diagnostic-only; exact = full Alice equality, syndrome separate, disagreements
isolated never merged; one sample per `(n, block_seed)` reused byte-identically;
coefficient stream `(n,layer,column,edge_index)` seeds L1 `202609120100+n` /
L2 `202609120200+n`; advancement/terminal rules per §8; no-retry.

## 4. Budgets, watchdog, stop rules

≤2500 total setup+scientific calls; ≤12 h wall (`deadline=t0+12h`,
`poll=min(120s,remaining)`); 120 s per-invocation watchdog (dedicated
respawnable worker, pids logged); aggregate RSS <2 GiB (strict, no-zero);
chunk ≥5400 s blocks dispatch (`D6_GRAPH_CHUNK_WALL_BLOCKED`); no retry;
only task-owned processes terminated.

## 5. Evidence (fresh root, schema r1d-v2, scalar-only)

`manifest.json` (+ `structure_schema=r1d-v2`, `eligible_semantics=frozen-AND-I1`),
`structure_records.csv` (frozen columns + `row_degree_min,rows_below_degree_2`),
`selected_arms.json`, `decoder_records.csv`, `summary.json`, `command_log.txt`.
`--verify` recomputes every group (zero skip), requires v2 columns + stored-vs-
recomputed I1 agreement, and reports stored-vs-recomputed terminal agreement
(recomputed governs).

## 6. No-reuse rule

The 184 R1c-A2 calls and the A2 six-file root
(`workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`) are immutable
history. No R1d claim, selection, advancement, terminal, or benchmark may cite,
import, or recompute-from them as science input; `--verify` read-only
recomputation is the only permitted contact. Protected-root metadata matches
the snapshot (6 files, lengths/mtimes; path git-clean).

## 7. Pre-EXECUTE checklist (all must hold; else no execution)

1. Fresh UUID output root absent; `assert_no_formal_write` passes.
2. Every authorization key false except an explicit main-thread grant naming
   this packet, branch, widths, arms, and budget; G2 absent.
3. Protected-root metadata matches snapshot; historical files byte-identical.
4. Focused D6 + seven-file non-perf suites green on the frozen HEAD.
5. Dispatched set ⊆ §4 valid subset (26/26 proven; guard landed + tested).
6. Exact command frozen (§1) with stop rules (§4); workers/budgets per §1/§4.
7. T2 excluded (rank-bound record only); no Track B dependency for R1d
   (T1/B0/B1 structure builds ≤0.34 s at every width).

## 8. Lifecycle gates

Implementation review PASS → Pre-EXECUTE review
`D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (grants no
authorization) → explicit main-thread execution authorization (NOT granted
here) → calls under code freeze → independent Pre-RESULT review PASS →
result solidification. Any code/graph/seed/row/decoder change after calls
start needs a new revision with no call reuse.
