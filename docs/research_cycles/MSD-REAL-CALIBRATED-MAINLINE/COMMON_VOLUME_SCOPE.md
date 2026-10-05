# Common-volume short/long comparison scope (DRAFT, documentation only)

Status: **DRAFT** — frozen for review in the same change
(`openspec/changes/msd-real-calibrated-mainline`) and the single MSD log
(`EXPLORATION_LOG.md`). Not accepted, not a decoder packet, not an execution
authorization. Main thread owns route choice and acceptance; a read-only
subagent review precedes any acceptance.

This document asserts **no new number**: no power result, no FER, no f, no code
rate or degree, no decoder cost, no sample-availability count. Every quantity
below is either already accepted elsewhere in this change or is explicitly
marked `UNKNOWN`.

Authority inherited (already accepted, not repeated here): `design.md` (comparator
planning, native ledger aggregation, common-volume bound), the L1–L5 section of
`P2_IMPLEMENTATION_CONTRACT.md`, the closed M metadata inventory acceptance, and
the L5 read-only review. Frozen production roots and old packets are untouched.

## 1. Purpose

Freeze, before any decoder packet is written, the comparison semantics that
could otherwise produce a false efficiency gain:

1. equal complete-symbol volume and equal entropy denominators across arms;
2. per-native-block tag and partial-retention charging;
3. boundary-preserving grouping;
4. the separation between the existing used development/replay pool and any
   potentially fresh out-of-sample (OOS) subset;
5. the revised common-volume power/cost algebra, distinguishing fixed tag
   offsets from outcome-dependent disclosure.

## 2. Comparator and comparison unit

- Same natural LSB-first MSD construction family at native `N=1024` and
  `N=16384` (`design.md`).
- A **complete-volume pair** is one long native block versus `q=16` contiguous
  short native blocks: both arms cover the same contiguous span of Alice and
  Bob complete symbols, `16384` symbols per side per pair.
- The pair is the unit of comparison and of any later power calculation. No
  arm-level or dataset-level average is a primary quantity.

## 3. Native ledger (adopted, unchanged)

Per native block, using the accepted L2 ledger with caller-supplied per-symbol
`H_A`, `H_A_given_B` (both bits/symbol, with `0 <= H_A_given_B <= H_A`), actual
EC/disclosure bits `L`, actual tag bits `tag`, and one L1 classification:

```text
H_A_total = N * H_A                    # bits/block
kept      = H_A_total - L              # bits/block
F         = 0 only for verified_exact  # accepted_wrong has F = 1
Y         = kept - tag - kept * F      # bits/block
numerator = L + tag + kept * F         # bits/block
f         = numerator / (N * H_A_given_B)   # dimensionless
```

- `kept < 0` stays visible with `valid_yield=False`, `f=None`; zero denominator
  gives `f=None`. Such a ledger is retained and reported, never silently
  dropped; a pair containing any invalid-yield or zero-denominator ledger
  cannot provide a finite paired `f` difference.
- `accepted_wrong` is counted separately and earns no verified yield; it is
  never relabeled as success, and no success/FER field absorbs it.
- Tag/disclosure bits are the **actual** charged bits, not a nominal rate.

## 4. Aggregation and the equality requirements

- A pair aggregates by **summing native ledgers** over its 1 long and 16 short
  blocks. Multiplying an average kept-bit count by an average failure rate is
  forbidden; per-block weighted penalties must be summed.
- Both arms must expose equal aggregate Alice volume `A = sum H_i` and an equal
  conditional-entropy denominator `B = sum N * H_A_given_B`. The aggregate
  builder rejects incompatible volumes or denominators; a rejection is a scope
  failure to be reported, not a value to be averaged away.

**Gate G-ENV (blocking, unresolved).** The accepted common-volume bound is
stated for equal aggregate `A` and equal `B`. `A` matches by construction if the
same per-symbol `H_A` is supplied to both arms. `B` does **not** match
automatically: if each native block's `H_A_given_B` is conditioned only on Bob
symbols inside that same block, then conditioning context differs between
`N=1024` and `N=16384`, and the two aggregate denominators are not guaranteed
to be equal without a declared common conditioning rule. This document neither
assumes they coincide nor asserts that they must differ. Before any decoder
packet, main thread must freeze one of:

- **E1** supply per-symbol `H_A_given_B` for both native lengths under one
  declared common conditioning rule, and show the aggregate denominators are
  equal (or declare the residual difference explicitly);
- **E2** restate the primary comparison on a denominator-independent per-Alice-bit
  basis and re-derive the paired-gap algebra for that estimand;
- **E3** keep both denominators explicit and treat any denominator difference as
  a first-class term in the paired gap rather than cancelling it.

`G-ENV` is `UNKNOWN` and blocks the packet. Choosing E1 without evidence that
equal conditioning contexts exist would be an unfrozen assumption, not a
resolution.

## 5. Grouping rule (boundary-preserving)

- The 16 short blocks must partition the long block's contiguous span exactly:
  same start, no gap, no overlap, same order, same complete-symbol source.
- The whole pair must lie inside one contiguous acquisition/session run. No
  stitching across acquisition, session, or rollover boundaries, and no
  assembling a pair from frames belonging to different runs.
- The grouping key (acquisition/session identifier, symbol-span or frame-range
  identifier, and the long-to-short mapping) must be **frozen before any
  decoder packet** and be re-checkable without reading frame vectors. The span
  identifier's convention — its origin within a run, zero- or one-based
  indexing, and its offset relative to the run start — is part of that frozen
  key and must not be chosen ad hoc at execution time.
- Whether such a mapping exists in the current records, at what granularity, and
  for which sources is `UNKNOWN`. Historical acquisition-frame counts are not
  reconciliation block lengths and not group counts (M adjudication).

## 6. Data roles

- The existing R1 VAL/HOLD pool is treated as **previously used
  development/replay input**. Closed M0/M2 records document evaluation drawn
  from it; M3C documents further diagnostic exposure; M2's withheld acceptance
  does not restore unused status.
- The whole pool must not be called fresh OOS. The converse is equally
  unsupported: full exposure of every possible index must not be asserted.
- A subset may be called fresh OOS only if a specific untouched subset is
  demonstrated with an explicit evidence basis recorded before it is used.
- Model draws under the fixed calibrated TRAIN model are evidence about that
  model only; they are not additional independent OOS acquisition data
  (`design.md`).
- Exact exposed indices, remaining unused subsets, session boundaries, and the
  number of independent complete-volume pairs are `UNKNOWN`.

## 7. Power and cost framework (algebra only)

Adopted from `design.md` and not re-derived here: for a valid native ledger
`G_i = L_i + (H_i - L_i) F_i` lies in `[0, H_i]`; at equal `A > 0`, `B > 0`,
`D = f_long - f_control = (G_long - G_control + T_long - T_control) / B`.

- **Fixed tag totals:** with `c = (T_long - T_control)/B` and `R = A/B`,
  `D` lies in `[c - R, c + R]` and its variance is bounded by `R^2`.
- **Outcome-dependent tag totals:** with nonnegative totals bounded by
  `T_long_max` / `T_control_max`, `D` lies in
  `[(-A - T_control_max)/B, (A + T_long_max)/B]`, standard deviation bounded by
  half that width.
- Which branch applies is **not chosen here**: it depends on the actual tag
  protocol, which is `UNKNOWN`. Both branches must be carried until the protocol
  is frozen.
- **Cost structure:** one complete-volume pair has at most `K * (1 + q)` native
  stage attempts — one long block plus `q = 16` short blocks, `K` stages each.
  This is a structural upper bound on attempt structure, not measured runtime,
  not a chosen protocol, and not a wall-clock budget.
- **What the bound does not give.** Across-pair independence is a separate
  statistical assumption that the algebra does not supply. A worst-case
  variance bound yields a *sufficient* pair count, not a necessary one; it is
  not a variance estimate. A practical pair count therefore needs an explicitly
  declared variance source (conservative worst case, or a model-calibrated
  estimate labelled as model evidence). The historical `P2_POWER.json` counts
  assume equal native lengths and one shared tag and are **not** transferable to
  this comparator.

Interpretation guard: the short arm verifies and retains per short block while
the long arm verifies and retains its whole block. Any observed `D` therefore
confounds code performance with verification granularity and tag cadence. No
attribution of `D` to code quality alone is licensed by this scope.

## 8. Required derivations before any decoder packet

Each item needs its own frozen inputs, script, and independent recomputation.
None is authorized by this document.

1. Freeze `G-ENV` (Section 4) — equal denominators or an explicitly restated
   estimand.
2. Freeze the actual tag protocol well enough to classify it as fixed-offset or
   outcome-dependent, which selects the bound branch in Section 7.
3. Freeze the grouping key and demonstrate the boundary-preserving mapping
   without reading frame vectors.
4. Establish the current role/provenance of every candidate pair and count the
   independently available complete-volume pairs.
5. Derive the required pair count and achievable MDE under the selected branch,
   with the variance source declared; keep the planning parameters
   (`delta_f`, `alpha`, power) as planning targets only, never inflated to
   shrink a required sample size.
6. Re-derive whole-workload cost as a structure (`K*(1+q)` per pair, times the
   required pair count, with outcome-dependent tag cost if applicable), leaving
   actual runtime `UNKNOWN` until separately authorized timing exists.

Steps 3–4 and 6 need index/frame/raw reads or backend timing. They are out of
scope here and require a separately frozen, explicitly authorized packet.

## 9. UNKNOWN register

Actual tag protocol and serialization; per-stage practical rates/degrees;
independent complete-volume pair count; current data roles and provenance;
exact exposed index set and unused subsets; session/acquisition boundary
granularity; whether the two arms' conditional-entropy denominators coincide;
measured decoder cost and the real-frame wall-clock budget.

## 10. Stop conditions

Stop and do not write a decoder packet if any holds: `G-ENV` unresolved; tag
protocol not classified; independent pair count not demonstrable; required MDE
exceeds the target effect under a declared variance source; real-frame
wall-clock budget not approved. Small decoder pilots, GF32 micro-probes, random
walks and stochastic guesswork are excluded by construction.

## 11. Not authorized by this document

No decoder, DE, frame/raw/NPZ/index read, backend timing, card operation,
qualification, publication, push, deletion or history rewrite. No old grant —
including the completed four-file M metadata grant — extends to any of these.

## 12. Expected benefit and cost

Benefit: a comparison whose tag cadence, retention granularity, denominators
and sample roles are charged correctly, so a real difference cannot be
manufactured by unequal units, hidden tags or contaminated "fresh" labels.
A practical f improvement remains `UNKNOWN`.

Cost: text and algebra only, plus one independent read-only review and one
scoped local commit. No push.

## 13. Open decisions for main thread

- `G-ENV` resolution: E1, E2 or E3 (Section 4).
- Variance source for the pair-count derivation: conservative worst case or a
  model-calibrated estimate labelled as model evidence (Section 7).
- Whether to freeze the grouping-key specification as the next deliverable
  before any data read.