# 48h Acceleration Plan — Design

Status: doc-only sequencing design. Freezes order, gates, and fences only; authorizes nothing.

## 0. Frozen facts this design rests on (adopted by reference, never re-verified here)

- Joint line: executed-but-miscounted KILL withdrawn as a decision; corrected numbers sit in §5.3(a) MARGINAL band (nominal Scope-A total 1100 vs 1104 fits by 4; `+20%` backoff total 1319 vs 1104 excess 215; uniform-shift rule executed-excess − 64). Formal re-evaluation needs JOINT-PRICING-R2 + new grant, never an edit. THIN-MARGIN (nominal margin 4 < 64) is acute for any continuation.
- Stage-0 line: ten-block shape honest (`Σm+64` vs 1104, tag once); CQ-J21c nominal 1875 vs 1104 excess 771, backoff 2233 excess 1129; KILL provisional pending S0-01…S0-08 review. Scope is ten independent per-plane allocations at the frozen `f` grid — joint or structured-layered designs not excluded.
- Proxy line: Packet A terminal INCOMPLETE (wall >3600 s, 240 unfinished, zero rows retained); R2 delta is infra-only segmented checkpointing (6×40, per-block SEG rewrite + manifest + 240/240 assembly gate), zero science change; execution grant PENDING.
- U1 line: header ceiling ≈24.6 bit/superframe (≈0.03 f) binds every outcome; option F closed as improvement route under §5.1–§5.4; batch-end review pending.
- Channel fence: five captures `ser` 0.23856707–0.25433839; structure only as "zero observed cross-plane co-error; single-plane-flip structure" (off-diagonals exactly 0.0, popcount only {0,1}, flips-per-error 1.0 both routes) with the ~1e-6 detection-floor qualifier whenever "independent" is used; negative only as "no measured easier point among the five captures; unmeasured groups supply no evidence of one on recorded grounds"; `0.098260` never a measurement; `f_eff`/`366`/`1.6x` never appear outside quoted ceilings.
- Dead routes: M3C STOP (R1 COMPLETE 372/383 u2-success but R2 INCOMPLETE-wall → no two-graph/FER decision); M3D single narrow mechanical sentence only (R1 point estimate missed the 10% gate; repeat/second-graph/real-frames unresolved; no M3C/throughput consequence); M2 WITHHELD (T2 12/12 stored arithmetic accepted, five blocks stand); HDC 0/28,000 + LB 36/28,000 both `void-no-correction`, never ranked; LB `void-stub-artifact` explicitly not applicable.

## 1. Ordering logic (why P-1…P-6 in this sequence)

1. **Cheapest terminal verdict first (P-1, seconds-scale EXPLORE).** Joint re-evaluation is pure ceil arithmetic over six persisted JSONs (≤300 s). It decides whether the joint line is MARGINAL-terminal (anticipated) and whether THIN-MARGIN blocks all downstream design. No design spend may precede it.
2. **Provisional→accepted before any Stage-1 thought (P-2, doc-only review).** Stage-0 KILL is the only thing standing between H1 and Stage-1 spend. Closing S0-01…S0-08 converts it from provisional to accepted at zero compute cost.
3. **Unblock the heavy line with code-only work (P-3, implementation-only).** The segmented driver + fake test is ~150 lines importing frozen helpers, verified by hand constants. It costs one pytest run and removes the sole implementation blocker for P-4 without spending decode budget.
4. **Single heavy spend last and alone (P-4, EXPLORE_HEAVY).** 240 Stage-1 m=200 decodes in 6 sequential segments (total ≤10800 s) is the only >1h item in 48h. It runs only after P-1/P-2 are closed and its own grant + Pre-EXECUTE pass. Partial completion yields INCOMPLETE with retained segments, never a word.
5. **Fence the dead ends while heavy compute runs (P-5, doc-only).** U1 review closure + dead-route consolidation costs zero execution and runs in parallel with P-4 waiting time; it prevents the most expensive failure mode (reopening M3C/M3D/M2/void-baseline/option-F on stale readings).
6. **Land the record (P-6, doc-only).** Decision-log/NOW maintenance + scoped manifest + memory triage makes the 48h window auditable and PR-ready without touching workspace or committing.

## 2. Track architecture (per AGENTS.md §1.2)

| P | Kind | Track | Reason |
|---|---|---|---|
| P-1 | packet (frozen JOINT-PRICING-R2) | **EXPLORE** | Analytic over six persisted non-sensitive statistics; bounded/reversible (1 proc, ≤300 s, ≤1 GiB, fresh additive root); no claim beyond fit-table + decision word; no raw-data contact; no route closure. Not HEAVY (millisecond arithmetic). |
| P-2 | doc-only review closure | — (no gate) | No execution; independent batch-end review of an executed EXPLORE batch per §10.3. |
| P-3 | implementation-only (2 additive files + fake test) | — (no gate) | No execution; T0 pytest on hand constants only. |
| P-4 | packet (frozen PROXY-RECAL-R2) | **EXPLORE, EXPLORE_HEAVY cost annotation** | Synthetic route-gate diagnostic arms (240 regenerated frames, one graph instance); bounded (6×40 sequential, ≤10800 s, ≤2 GiB); no claim beyond proxy-fidelity word + paired table; route-closing interpretation stays outside as future DECIDE. |
| P-5 | doc-only fence consolidation | — (no gate) | No execution; review proportionality only. |
| P-6 | doc-only record + triage | — (no gate) | No execution; memory triage per mandatory processes. |

Every execution P declares exactly one track before execution; `EXPLORE_HEAVY` is a cost annotation, not a third lifecycle. Uncertainty defaults to DECIDE only on a named concrete risk; calling a decoder alone does not force DECIDE — but P-4's decoder calls are inside the frozen EXPLORE_HEAVY packet boundary with its own grant + Pre-EXECUTE + batch-end review.

## 3. Cost architecture (ceilings are the thing that must never be under test)

- P-1: 1 proc, 1 CPU, threads pinned, sequential, wall ≤300 s, RSS ≤1 GiB; breach ⇒ INCOMPLETE retained never continued; single preregistered infra repair only (unchanged inputs/grid/rule).
- P-3: T0 pytest only on fresh `workspace/*__pytest_<uuid8>` roots; `py_compile` on both cli modules; zero science contact.
- P-4: sequential segments, 1 proc at a time, 1 CPU, threads pinned (incl. NUMBA), per-segment wall ≤1800 s, total ≤10800 s, RSS ≤2 GiB, per-block 300 s overrun ⇒ block failed + segment INCOMPLETE; breach in segment g ⇒ retain 0..g−1, never continue; single infra repair only (validation REFUSE / saturation-cost breach / science change = new packet, never repair).
- P-2/P-5/P-6: zero execution budget; doc writes only under `docs/` + `openspec/changes/accel-48h-plan/`; no workspace write.

## 4. Gate architecture (each execution P reuses its packet's frozen gates)

- P-1 reuses JOINT-PRICING-R2 §10 P-1…P-9 (branch/HEAD re-measured; P-2 four-file manifest frozen with hashes; T0 `pytest test_joint_pricing_fake + test_accounting_identities_fake` all-pass; six input size/mtime checks; output absence; exact P-6 command with dual flags; budgets/stops read-back; F-1…F-4 shape-identity grep with per-hit dispositions; protected-roots + forbidden-reads) and §9 stops (any one ⇒ retain + return, no input-fitting).
- P-4 reuses PROXY-RECAL-R2 §10 PR2 P-1…P-8 (two-file manifest; new fake-only seg test all-pass incl. partition-once/checkpoint-survives/refuse-short/refuse-overlap/word-helper-equality/path-gate; nine input size/mtime + I-5-vs-I-6 bitwise checks; output absence; six frozen segment commands + assemble command; budgets/stops read-back; protected-roots) and §9 stops (10 rules) plus §3.5 per-segment validation gate (REFUSE ⇒ zero decodes in that segment, no later segment).
- Reviews: P-1 D-4 against JR-01…JR-08; P-2 D-4 against S0-01…S0-08; P-4 D-4 against PR2-01…PR2-08. FAIL blocks promotion of every number in that batch; rework + re-review, never publish-then-patch.

## 5. Fence rules carried into every P

- THIN-MARGIN: any PASS with nominal single-tag margin <64 carries the flag; no downstream design packet may be drafted until the user explicitly addresses the margin on record. MARGINAL licenses no design work at all (new proposal + packet + grant required, never relaxed re-reading).
- Tag invariance: both comparisons carried distinctly (`T_single=M` vs 1104; `T_recorded=M+960` vs 2064); excess identically `M−1104`; reviewer hand-recomputes ≥1 capture under both.
- Shape-aware machine check (STAGE0 §16.3 C-1/C-2/C-3 + F-1…F-4): single-block bare ceil is the total (never `leak`/`parity`); ten-block `Σm+64` honest with exactly one tag; fixtures asserting `(M+64)−1104` correctness without C-1/C-2 are absent.
- Citation discipline (§0 fence): bare "plane independence / mutually independent", absolute "no easier point exists", "unused groups do not help", and "is an artifact of" forms are forbidden; only the fenced forms travel.
