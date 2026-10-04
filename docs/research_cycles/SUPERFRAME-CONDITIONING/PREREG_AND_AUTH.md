# SUPERFRAME-CONDITIONING — Frozen Executable Packet (packet ②, superframe-level structure + adaptive-m counterfactual)

- **Status**: FROZEN — awaits Pre-EXECUTE measurement + execution under the grant below (§14). This freeze authorizes nothing by itself.
- **Track**: **EXPLORE** (arithmetic over already-persisted statistics; zero decode, zero new data contact — see §0.1).
- **Proposal authority**: `docs/research_cycles/M0-REALFRAME/RESULT.md` §3.1 (frozen route: "在信任 M3 的合成结果之前，先做信道条件化（逐超帧自适应先验 / 漂移处理），并用 F9(ii) 的逐超帧误差序列定位原因") and `docs/research_cycles/NEXT-STEP-OPTIONS/PROPOSAL.md` Correction 2026-09-28 (joint corrected figures: nominal `1100 vs 1104`, backoff `1319 vs 1104`). This packet freezes the F9(ii) follow-up as one mechanical question; it redesigns nothing. Any conflict between this packet and those records is a STOP (§9), not a patch license.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Using **already-persisted per-superframe error counts only** (the M0 `block_accounting.csv` `raw_symbol_errors` columns, deduplicated to one value per superframe: 205 / 287 / 383) plus the five frozen CQ JSONs (§2), decide with **one mechanical word, PASS or KILL** (§5) whether superframe-level conditioning can move the **joint 215-bit backoff gap** (corrected Scope-A backoff total `1319 vs 1104` on CQ-J21c; nominal margin `1100 vs 1104`, i.e. about 4 bits — both carried as frozen references from `JOINT-PRICING/PREREG_AND_AUTH.md` §17.2, never recomputed here). The work is three frozen test families over the count sequences (drift / autocorrelation / dispersion, §3) plus a generous oracle adaptive-m upper-bound arithmetic (§4), closed by the mechanical rule. If the answer is that conditioning cannot move the gap, the conditioning route is abandoned at zero design cost.

### Non-Goals

- No decoder call, no construction call, no `.ttbin` open, no channel-bundle open, no `(a, b)` array open, no raw-data contact of any kind (§2.3).
- No FER, efficiency, leakage, `f`, SKR, or key figure; no method comparison or ranking; no claim that any method corrects; no claim that any conditioning, adaptive-m, or joint design exists, is constructible, decodes, or works (§11).
- No design packet drafted; no headline tag ratio designated (both tag accountings are untouched — this stage prices counts, not tags; §4.3).
- No citation of the legacy value `0.098260` as a measurement; no use of the void HDC / void Layered-Binary figures as baselines in any form; the symbol `f_eff` does not appear in any deliverable.
- No route closure, qualification, publication number, or acceptance of any method.
- No modification of any runner, construction, decoder, config, existing workspace root, `M0_RESULT_*.md`, `rows.json`, CQ JSONs, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: exactly two new files — `comparison_bench/src/comparison_bench/cli/superframe_conditioning.py` (additive arithmetic script, T-2/T-3) and `comparison_bench/tests/test_superframe_conditioning_fake.py` (fake-only test, T-1) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/sf_<uuid8>` (§6).
- **Read-only inputs**: the three M0 `block_accounting.csv` files plus the five CQ JSONs of §2. Nothing else is read for content (code, docs, and configs cited elsewhere in this packet are frozen references carried from planning, not execution inputs).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/m0_359922a7_1M/`, `workspace/m0_642a8fe8_1p5M/`, `workspace/m0_b1a9142d_2M/`, `workspace/cq_15d6f160/`, `workspace/cq_4af91a87/`), `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2

This packet is **EXPLORE** (not `EXPLORE_HEAVY`: millisecond-scale arithmetic, no costly execution), confirmed against the §1.2 applicability matrix ("Synthetic diagnostics → EXPLORE" and "Parameter scans (synthetic) → EXPLORE"):

1. **Input character**: the inputs are already-persisted, closed-batch per-superframe counts and channel statistics from the closed M0 DECIDE batch and the closed CHAN-QUALITY-SURVEY batch. This stage opens no `.ttbin`, no channel bundle, no `(a, b)` array, no raw data of any kind (§2.3). Arithmetic over frozen persisted numbers is not data contact — the identical argument `JOINT-PRICING` §0.1 and `U1-CEILING-PROBE` §0.1 made.
2. **Bounded and reversible**: one process, one CPU, ≤600 s, ≤2 GiB (§8); one fresh additive root, append-only (§6).
3. **No claim**: the §11 ceiling forbids every claim-bearing figure (FER, efficiency, leakage, `f`, SKR, key, ranking, correction, design existence, headline tag). The only outputs are a structure table, an upper-bound arithmetic, and one decision word that kills or defers the conditioning route (§5.4).
4. **Uncertainty default**: no concrete risk named here defaults this to DECIDE. The foreseeable failure modes (misread input, cross-arm mismatch, formula drift, evidence-label error) are met by the input size/mtime/dedup gate (SF-01), the transcription-free derivation (§3.1), the fake-only test (§10 P-3), and the batch-end review (SF-07) — not by escalation.
5. **No escalation trigger**: this stage touches no real data, closes no route by itself (KILL is terminal for this packet only), makes no publication claim, performs no destructive output, incurs no material cost, and changes no scientific input or hypothesis.

---

## §1 Frozen question (answerable in one shot)

Do the persisted per-superframe error sequences carry **exploitable non-stationarity or burst structure** (drift across the acquisition, short-lag autocorrelation, overdispersion beyond IID counting noise), and — under a **generous oracle upper bound** that overstates what per-superframe adaptation could save — can that structure move the **215-bit joint backoff gap**, with the **4-bit nominal margin** carried as the secondary comparison? The answer is exactly one word, PASS or KILL, applied mechanically on the 2M source (the M0 baseline source, mirroring `JOINT-PRICING` §5).

Scope note (binding): only the three Jan-21 M0 eval-region sequences are priced. The Type0 groups' block accountings do not exist; nothing here speaks about conditioning on unmeasured data (§12.5).

---

## §2 Frozen input list (read-only)

Exactly these eight files. No other file is opened for content by the execution.

| # | Path | Bytes | UTC mtime (measured 2026-09-29) | Role |
|---|---|---|---|---|
| I-1 | `workspace/m0_359922a7_1M/block_accounting.csv` | 25696 | 2026-09-24 11:06:33 UTC | 1M per-arm rows: `m`, `superframe`, `exact_match`, `undetected`, `raw_symbol_errors` (410 rows = 205 sf × 2 arms, m = 197/201) |
| I-2 | `workspace/m0_642a8fe8_1p5M/block_accounting.csv` | 35747 | 2026-09-24 11:11:19 UTC | 1p5M rows (574 = 287 sf × 2 arms, m = 203/207) |
| I-3 | `workspace/m0_b1a9142d_2M/block_accounting.csv` | 47681 | 2026-09-24 11:27:35 UTC | 2M rows (766 = 383 sf × 2 arms, m = 204/208; **§5 decision source**) |
| I-4 | `workspace/cq_15d6f160/CQ-20a.json` | 8632 | 2026-09-27 09:48:32 UTC | Arm A group (500K): `status`, `channel.ser`, `channel.H_*` (context + provenance only) |
| I-5 | `workspace/cq_15d6f160/CQ-20b.json` | 8628 | 2026-09-27 09:50:34 UTC | Arm A group (1M): same fields |
| I-6 | `workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json` | 4221 | 2026-09-27 09:21:12 UTC | Arm B source 1M: same fields |
| I-7 | `workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json` | 4235 | 2026-09-27 09:24:52 UTC | Arm B source 1p5M: same fields |
| I-8 | `workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json` | 4211 | 2026-09-27 09:28:26 UTC | Arm B source **2M** (M0 baseline source; provenance anchor for the 4 / 215 references) |

Fields consumed from I-1…I-3 per row: `m`, `superframe`, `exact_match`, `undetected`, `raw_symbol_errors`. The `u2_symbol_errors` column is a cross-check only (must equal `raw_symbol_errors` on every row — §3.1 assertion; never consumed as input). Fields consumed from I-4…I-8 per file: `status` (must be `OK`), `channel.ser`, `channel.H_A_given_B`, `channel.H_U2_given_U1B`, `channel.H_U1_given_B` (provenance context only — they enter **no** arithmetic; the script asserts presence and echoes values). Every other key is provenance context only.

### §2.1 Frozen references carried from planning (not execution inputs — the script reads no additional file for them)

- **R-4**: joint nominal total `M = 1100 vs 1104` — fits by **about 4 bits** (Scope A, CQ-J21c, `f = 1.3`), per `JOINT-PRICING/PREREG_AND_AUTH.md` §17.2.
- **R-215**: joint backoff total `M = 1319 vs 1104` — excess **215 bits** (Scope A, CQ-J21c, effective `f = 1.56`), per ibid. §17.2.
- **R-m**: M0 single-tag disclosure proxy `T(m) = 5·m + 64` bits per superframe (at m = 208: `5·208 + 64 = 1104`, ibid. §3.6 item 5); all three sources test two arms with `Δm = 4`, so the tested-granularity oracle bound caps at `5·4 = 20` bits/superframe (§4.1).
- **R-planes**: ten Gray planes (`BITS = 10`, `nonbinary_v25_gate.py:28`, carried via `U1-CEILING-PROBE` §2) — the frozen per-error value-bit cap `c = 10` in §4.2.
- The script embeds R-4 / R-215 / R-m / R-planes as frozen constants. Pre-EXECUTE verifies them character-for-character against the cited sources (§10 P-4); any mismatch is a STOP, never an edit.

### §2.2 Deduplication predicate (verified read-only 2026-09-29 before freezing — not assumed)

On the frozen files: every superframe appears exactly twice (two `m` arms); `raw_symbol_errors` agrees across the two arms on **all** 205 + 287 + 383 superframes; `raw_symbol_errors == u2_symbol_errors` on **all** rows; per-arm means 244.29 (1M) / 260.44 (1p5M) / 259.85 (2M) reproduce `M0-REALFRAME/RESULT.md` §§2.1–2.3. The script re-asserts all of the above at startup (§3.1); any violation is K2-4 STOP.

### §2.3 Zero-decode / no-data-contact statement

The execution SHALL NOT open any `.ttbin` file, any channel bundle (`gamma_f03*.npz` — named here only to forbid), any `pairs.parquet`, any `(a, b)` array, any `rows.json`, or any raw data of any kind. The script's allowed-input gate (T-1) admits exactly the eight frozen paths above and refuses any path outside them and any path ending in `.ttbin`, `.npz`, `.parquet`, or `rows.json`. The `rows.json` files beside the M0 roots are not inputs and stay unopened.

### §2.4 Standing citation discipline (required verbatim wherever invoked)

Wherever the channel structure or the five-capture measurements are invoked, verbatim the standing fenced forms of `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B.1 (as carried in `JOINT-PRICING` §2.4):

> 已定事实是 **「零观测到的跨面共错；单面翻转结构」**. 约一百万对中零个双面错误只排除高于约 1e-6 的多面率，**低于探测限的罕见双翻未被排除**. 措辞「位面相互独立」**只在附带该探测限限定时**可用。引用证据时用三元组：零共错、popcount 限于 {0,1}、每次误差翻面数 1.0.

> 只能以围栏形式：「**五个已测采集中无已测得的更易工作点；未测组按在案理由不提供证据**」。**本体形式（「不存在更易数据」）绝不可单独引用。**

Additionally: the legacy value `0.098260` is never cited as a measurement (§11); the 1104 budget is carried as a frozen nominal convention, never as an empirical headroom discovery; and the derived ratios of the session audit §2 claim 10 (`2–4×`, `1.6×`, `≈366 sym/s`) appear nowhere in any deliverable.

---

## §3 Frozen derivation — sequence extraction + three test families (T-2)

### §3.1 Extraction (per source, identical)

1. Read the source's `block_accounting.csv`. Assert total rows `== 2·n` with `n = 205` (1M) / `287` (1p5M) / `383` (2M); assert exactly two distinct `m` values with `Δm == 4` (else K2-4 STOP — the T-3a bound in §4.1 is exact only at this granularity).
2. Assert `raw_symbol_errors == u2_symbol_errors` on every row (else K2-4 STOP).
3. Group by `superframe`; assert exactly 2 rows per superframe and equal `raw_symbol_errors` across the two arms (else K2-4 STOP).
4. Sequence `x` = the agreed `raw_symbol_errors` per superframe in ascending `superframe` order, length exactly `n`. No smoothing, no trimming, no outlier removal, no reordering.
5. `S_lo` bookkeeping for §4.1 is derived from the same rows (no second read): per superframe, lo-arm u2-success `r.exact_match == true AND r.undetected == false` (U1-packet predicate precedent; `undetected` never counts as success).

### §3.2 Family D — drift (non-stationarity across the acquisition)

Per source with `n1 = floor(n/2)` (first half), `n2 = n − n1` (second half), sample means `m1, m2` and sample variances `v1, v2` (`ddof = 1` throughout this packet):

- `SE = sqrt(v1/n1 + v2/n2)`; `z = (m2 − m1) / SE` (if `SE == 0`: STOP, never zero-filled).
- Linear trend slope `β` = least-squares slope of `x` on index `0…n−1` (reported, no flag).
- First-vs-last-quarter means (reported, no flag).
- **Flag `DRIFT`** iff `|z| > 3` (frozen descriptive gate — a 3σ split-half band, not a hypothesis test with a claimed level; no p-value is reported or cited).

### §3.3 Family C — short-lag autocorrelation (burst/clustering)

Per source: Pearson `r_k = corr(x[0:n−k], x[k:n])` for lags `k = 1…5` (if any lag window has zero variance: STOP, never zero-filled).

- **Flag `CORR`** iff `|r_1| > 3/sqrt(n)` (frozen descriptive gate — the classical white-noise 3σ band: 0.210 / 0.177 / 0.153 for n = 205 / 287 / 383; not a significance claim).

### §3.4 Family V — dispersion (overdispersion beyond IID counting noise)

Per source: sample variance `v` (`ddof = 1`), mean `m`, index `D = v / m`.

- **Flag `OVERDISP`** iff `D > 1 + 3·sqrt(2/(n−1))` (frozen descriptive gate — chi-square 3σ band around the Poisson-IID value 1: 1.297 / 1.251 / 1.217 for n = 205 / 287 / 383; underdispersion `D < 1` sets no flag).
- The band is descriptive, not a distributional claim: counts are not asserted Poisson; the band is only the frozen yardstick that keeps the flag outcome-independent.

### §3.5 Structure verdict (2M decides; all three reported)

`STRUCTURE_2M = DRIFT_2M OR CORR_2M OR OVERDISP_2M`. The 1M / 1p5M flags are context columns only and cannot move the §5 word. Absence of all three flags on 2M is the K2-1 condition (no exploitable structure at the frozen sensitivity).

---

## §4 Frozen counterfactual — oracle adaptive-m upper bounds (T-3)

Both bounds are **budget-fit proxy arithmetic under named generous assumptions, not leakage/efficiency measurements** (§11). Generosity direction is stated per bound: each overstates what real adaptation could save, so a KILL under either bound is conservative (the true saving is smaller).

### §4.1 T-3a — tested-granularity oracle (tight; decides the 4-bit nominal-margin question as context)

Per source with arms `(m_lo, m_hi)`, `Δm = 4`, `P_lo = |S_lo| / n` (S_lo from §3.1 item 5; both-failed and undetected superframes are charged `m_hi` — generous: the true rescue cost is ≥ `m_hi`, so this understates cost and overstates saving):

- Oracle mean parity `m_or = (P_lo·m_lo + (1 − P_lo)·m_hi)`.
- Saving vs flat-`m_hi` under R-m: `S_a = 5·(m_hi − m_or) = 20·P_lo` bits/superframe (exact at `Δm = 4`; reported to 6 dp).
- Comparison: `S_a` vs **R-4 (4 bits)**: covers the nominal margin iff `P_lo ≥ 0.2`. Reported per source as context; it does **not** move the §5 word (the frozen question is the 215-bit gap).

### §4.2 T-3b — spread oracle (loose; drives the 215-bit decision)

Per source with `μ = mean(x)`, `M = max(x)`:

- `S_spread = 10·(M − μ)` bits/superframe (integer-valued; `c = 10` is the R-planes value-bit cap: one symbol error flips at most ten plane bits).
- **Named generosity**: position/disclosure overhead, finite-length margin on the adaptive law itself, and estimation error of the per-superframe state are all excluded — every exclusion overstates the saving. `S_spread` is therefore a strict upper-bound illustration; the realisable conditioning saving is smaller (direction frozen, §12.3).
- Comparison: `S_spread` vs **R-215 (215 bits)** on 2M (decision-driving); reported for all three sources.

### §4.3 Tag-accounting note (no headline designated)

Both bounds are single-tag-nominal-basis proxy bits comparable to the R-4 / R-215 figures, which are themselves single-tag-nominal (`M` vs 1104). No tag total is formed here, no headline is designated, and the D-1 deferral is untouched.

---

## §5 Frozen decision rule (PASS / KILL) + kill conditions K2-1…K2-4

Applied **mechanically** to the frozen table on the **2M source** (I-3; the M0 baseline source). The structure table and both bounds are frozen before any comparison with R-4 / R-215 (outcome-independent).

> **§5.1 PASS.** Iff on 2M `STRUCTURE_2M` is true (§3.5) **and** `S_spread_2M ≥ 215` (§4.2): the word is **PASS**.
>
> **§5.2 KILL (K2-1 — no exploitable structure).** Iff on 2M `STRUCTURE_2M` is false: the word is **KILL**. The sequences are IID-consistent at the frozen sensitivity; conditioning has nothing to exploit. The bounds are still reported but cannot move the word.
>
> **§5.3 KILL (K2-2 — arithmetic ceiling).** Iff on 2M `STRUCTURE_2M` is true but `S_spread_2M < 215`: the word is **KILL**. Structure exists yet even the generous spread oracle cannot cover the backoff gap. The T-3a vs 4-bit comparison is recorded alongside (a `S_a ≥ 4` outcome means nominal-margin defense is arithmetically possible but the frozen 215-bit question is still unmoved — still KILL).
>
> **§5.4 What PASS does and does not license.** A PASS prices generous upper-bound headroom under structure; it licenses **only** the drafting of a conditioning-design packet. It licenses no decoder run, no construction run, no performance claim of any kind, no FER/efficiency/leakage/`f`/SKR/key figure, no method comparison, and no execution.
>
> **§5.5 Scope never decides beyond 2M.** No 1M / 1p5M outcome can move the decision word in either direction.

**Batch-killing stops (no word promoted):**

- **K2-3 — data-contact escalation.** Any attempt, successful or attempted, to open a `.ttbin`, channel bundle, `pairs.parquet`, `(a, b)` array, `rows.json`, or raw data; any decoder/construction call or import ⇒ STOP-BLOCKED, evidence retained, return to main. No decision word is emitted; a new packet is required for anything touching data.
- **K2-4 — input absence/drift.** Any of I-1…I-8 absent, unreadable, size/mtime drifted from §2, row-count/`Δm`/dedup/`raw==u2` assertion failure, CQ `status != OK`, or a missing `H`/presence field ⇒ STOP-BLOCKED, evidence retained, return to main. Summaries never override rows; rows never get "corrected" to match summaries.

K2-1/K2-2 kill the route with a KILL word; K2-3/K2-4 kill the batch with a retained STOP and no word. None licenses a rerun except the §8 preregistered infra repair.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/sf_<uuid8>/` (uuid8 recorded in §10 P-6). **No existing root may be written.**

| # | File | Content |
|---|---|---|
| D-1 | `workspace/sf_<uuid8>/SF_RESULT.json` | One JSON result. Frozen schema: `inputs` (8 paths + byte sizes + UTC mtimes + row-count/`Δm` echoes), `sequences` (per source: n, mean, min, max), `families` (per source: split-half means, z, β, quarter means, r_1…r_5, D + three flags), `counterfactual` (per source: P_lo, S_a vs 4; μ, M, S_spread vs 215), `decision` (`PASS`/`KILL` + fired §5 clause + evidence pointers), `resources` (wall_s, peak RSS, CPU, command, thread-pin env) |
| D-2 | `workspace/sf_<uuid8>/SF_SUMMARY.md` | Short Markdown summary: the three-source table, the decision word, the §11 ceiling restated verbatim. No ranking sentence beyond sorting sources by S_spread with the ceiling restated |
| D-3 | `workspace/sf_<uuid8>/SF_LOG.md` | Single append-only log (EXPLORE contract): attempts, machine-gate results, the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/sf_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against SF-01…SF-08 (§7). FAIL blocks promotion of every number in this batch; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| SF-01 | Input fidelity: exactly the eight §2 paths opened, byte sizes + UTC mtimes match the table; row counts 410/574/766 with `Δm == 4` per file; 2-rows-per-superframe, cross-arm agreement, and `raw==u2` assertions all pass; all five CQ `status == OK` with presence fields echoed; no `.ttbin`/`.npz`/`.parquet`/`rows.json`/raw path opened (script path-gate + log) | `SF_RESULT.json` `inputs` + `SF_LOG.md` + script source |
| SF-02 | Extraction fidelity: sequences lengths exactly 205/287/383 in ascending superframe order, no smoothing/trimming/reordering; reviewer hand-checks ≥1 source end-to-end from CSV to sequence | fake test (§10 P-3) + reviewer hand recomputation |
| SF-03 | Family completeness: all three families × three sources (z/β/quarters, r_1…r_5, D) with the frozen §3.2–§3.4 gates applied as written; no extra test, no tuned threshold, no p-value | `SF_RESULT.json` `families` |
| SF-04 | Counterfactual arithmetic: T-3a `S_a = 20·P_lo` exact with undetected-excluded predicates and vs-4 comparison; T-3b `S_spread = 10·(max − mean)` with vs-215 comparison; R-4/R-215/R-m/R-planes constants match §2.1 provenance | fake test (§10 P-3) + reviewer hand recomputation of the 2M cells |
| SF-05 | Decision mechanics: exactly one of PASS/KILL with the fired §5 clause cited, on 2M only, table frozen before comparison; K2-1 vs K2-2 reason recorded; K2-3/K2-4 stops carry no word | `SF_RESULT.json` `decision` + `SF_SUMMARY.md` |
| SF-06 | Budget: wall ≤ 600 s, peak RSS ≤ 2 GiB, 1 CPU, threads pinned, one process, sequential; breach ⇒ INCOMPLETE, retained, never continued | log + resource lines in `SF_RESULT.json` |
| SF-07 | No-overwrite: fresh `workspace/sf_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest | filesystem + git state |
| SF-08 | Deliverables + claim-ceiling machine check: D-1…D-4 complete; §11 respected verbatim; the strings `0.098260`/`0.09826` return **zero hits**, the symbol `f_eff` returns **zero hits**, void-baseline tokens return **zero hits** in the fresh root (outside the quoted §11 ceiling); no numeric FER/efficiency/leakage/`f`/SKR/key claim, no method sentence, no design-existence claim, no headline-tag designation; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | `rg` over `workspace/sf_<uuid8>` + review document |

---

## §8 Budget (frozen ceiling)

One process, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`; numpy-only arithmetic), sequential, **no retry, no resume** except the single preregistered infra repair below. Wall **≤ 600 s**, peak RSS **≤ 2 GiB**. Breach ⇒ INCOMPLETE, retained, never continued.

The ceiling is generous by roughly three orders of magnitude on wall (three CSVs ≈ 109 KiB total, five JSONs ≈ 30 KiB; the work is counting plus closed-form statistics — the same class as Stage-0 JSON arithmetic at measured 0.39 s outer) and by roughly two orders on memory. The generosity is deliberate: the ceiling must never be the thing under test.

**Preregistered repair (single, infra-only)**: at most one repair+rerun is permitted, and only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript) with **unchanged** scientific inputs, predicates, gates, bounds, thresholds, data roles, and decision rule; the failed attempt is retained in `SF_LOG.md` in the same root. Any change to a predicate, gate, bound, or the §5 rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the eight §2 files absent, unreadable, or size/mtime drifted from the table (K2-4).
2. Row-count / `Δm == 4` / dedup / `raw==u2` assertion failure; CQ `status != OK` or missing presence field (K2-4). Summaries never override rows.
3. `SE == 0` in §3.2 or zero-variance lag window in §3.3 (never zero-filled).
4. A formula ambiguous as written here (do not interpolate — stop).
5. Any attempt, successful or attempted, at raw-data contact or decoder/construction use (K2-3).
6. Any invented count, any cross-source pooling, any smoothed/trimmed/reordered sequence, any tuned gate.
7. Budget breach (§8).
8. Output collision (`workspace/sf_<uuid8>` already exists) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
9. Any evidence-label error (a number cited with the wrong source/file, a status relabelled, a §2.4 fenced sentence altered, a bound presented as a measurement).

On stop: retain all evidence in place, **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before execution)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/superframe_conditioning.py` + `comparison_bench/tests/test_superframe_conditioning_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_superframe_conditioning_fake.py -p no:cacheprovider` — must be **all-pass** on a fresh additive `workspace/sf__pytest_<uuid8>` root. **What the fake asserts** (hand-computable constants, zero data contact — reads no M0 CSV, no CQ JSON, nothing): dedup of a hand 3-superframe × 2-arm table with a planted cross-arm agreement (and refusal on a planted disagreement); split-half z on a hand sequence matched to 1e-9; lag-1 r on a hand AR(1)-shaped sequence (flag fires) vs a hand alternating sequence (flag silent); dispersion D on hand overdispersed vs Poisson-like sequences (flag fires/silent at the frozen band); T-3a `20·P_lo` on a hand success pattern with one undetected row excluded; T-3b `10·(max − mean)` on hand counts; the PASS/KILL gate on both sides of each frozen threshold; and the input path-gate refusal of planted `.ttbin`/`.npz`/`.parquet`/`rows.json` paths |
| P-4 | Input size/mtime + threshold provenance | `stat` the eight §2 paths: byte sizes + UTC mtimes match the table exactly; R-4 (`1100 vs 1104`, ~4 bits) and R-215 (`1319 vs 1104`, 215 bits) verified character-for-character against `JOINT-PRICING/PREREG_AND_AUTH.md` §17.2; R-m (`5·m + 64`, `Δm = 4` → 20-bit cap) against ibid. §3.6; R-planes (`BITS = 10`) against `nonbinary_v25_gate.py:28` |
| P-5 | Output absence | `workspace/sf_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-6 | Exact command frozen | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.superframe_conditioning --inputs <eight frozen paths> --root workspace/sf_<uuid8> --execute --execution-authorized` (refuse without both flags, M0/CQ/Stage-0 precedent). Root uuid8 fixed here at Pre-EXECUTE |
| P-7 | Budgets + stops read back | §8 ceilings and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove the eight input files' parent roots are otherwise untouched (no writes); `rg` the T-2/T-3 script for `ttbin\|npz\|parquet\|rows\.json\|decode\|ldpc\|construct\|bundle\|pair_nearest` open/decode-shaped tokens returns only the refusal-gate lines (zero read paths) |

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation; quoted verbatim in every artifact)

> Superframe conditioning is budget-fit arithmetic about persisted counts, nothing more. This stage establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement; NO key figure; NO method comparison or ranking; NO claim that any method corrects any frame; and NO claim that any conditioning, adaptive-m, or joint design exists, is constructible, decodes, or works anywhere. No headline tag ratio is designated. The legacy value 0.098260 is not cited as a measurement in any deliverable in any form. The void HDC and void Layered-Binary figures are not used as a baseline in any form. The symbol f_eff does not appear in any deliverable in any form. A PASS prices generous upper-bound headroom under structure; it licenses only the drafting of a design packet, and no performance claim, no decoder claim, and no execution.

---

## §12 What this stage cannot decide (with the cheapest test that would)

1. **It cannot show that any conditioning corrects anything.** No frame is decoded here. Cheapest test: a future conditioning-design packet with per-superframe priors/allocations decoded on measured-rate synthetic draws (EXPLORE) — which this stage does not license beyond drafting (§5.4).
2. **It cannot set the adaptive-m law.** T-3a prices only the tested `Δm = 4` granularity; T-3b is a spread illustration, not an allocation rule. Cheapest test: same future design packet — fit the law and measure at matched disclosure.
3. **It cannot validate the carried-over backoff for a conditioned construction.** R-215 is a joint-arithmetic convention, not a conditioned finite-length margin. Cheapest test: same future design packet — measure whether the conditioned allocation decodes.
4. **It cannot speak to conditioning on unmeasured groups.** Only the three Jan-21 eval-region sequences are priced; Type0 block accountings do not exist. Cheapest test: a new measurement packet on those groups' own sequences, if they are ever produced under their own grant.
5. **It cannot resolve the ten-plane versus five-plane scope question or the bin-width question** (all captures use the imposed `bin_width_ps = 200` convention). Both are science-input changes requiring their own packets.

---

## §13 Carried notes (binding on this packet)

- **§13.1 Ten planes, not nine.** Per `STAGE0_PACKET.md` §13.1 (`BITS = 10`). The `c = 10` cap in §4.2 is that plane count, not a fitted parameter.
- **§13.2 The 1104 budget is a nominal-equality convention, not an empirical headroom discovery.** Per the session audit §2 claim 9: M0's `5·208 + 64 = 1104` equals the budget by definition. R-4 / R-215 are carried as the frozen comparison basis; no fit margin is cited as a headroom "finding" beyond the §5 decision word.
- **§13.3 Fence-soundness.** The D-1 headline deferral is untouched: this stage forms no tag total and designates no headline (§4.3). The joint §3.6 invariance is not re-derived here because no tag comparison is made.

---

## §14 Grant block

- Grant verbatim: 「继续往下推进」+「按照建议直接来」
- Date / granter: 2026-09-29, user (via main thread; EXPLORE packet ② of the frozen order).
- Scope: this grant covers **freezing this packet and executing it within the §8 ceilings only**. Nothing else is authorized: any conditioning-design packet, any decoder/construction work, any DECIDE real-frame, qualification, or publication-claim work each needs its own packet + grant. Neither this packet nor any sibling packet authorizes anything beyond itself.

---

## §15 Tasks (ordered: T-1 input fidelity → T-2 extraction + three families → T-3 counterfactual → T-4 word + review)

1. **T-1 — Input fidelity + code gates (implementation-only code needs no track gate).** Implement `comparison_bench/src/comparison_bench/cli/superframe_conditioning.py` (new file only): stdlib + numpy pure arithmetic; argv takes exactly the eight §2 paths + `--root workspace/sf_<uuid8>` + dual `--execute --execution-authorized` flags (refuse without both); startup path-gate admits only the frozen eight and refuses any `.ttbin`/`.npz`/`.parquet`/`rows.json` path; startup input gate asserts sizes/shapes per §3.1 (row counts, `Δm == 4`, dedup agreement, `raw==u2`, CQ `status == OK`); appends gate results to `SF_LOG.md`. Implement `comparison_bench/tests/test_superframe_conditioning_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/sf__pytest_<uuid8>` roots; zero scientific/real-data contact — hand constants only, reads no input file). No `src/` touch. Per `AGENTS.md` §5.7: simplest implementation that is scientifically correct — no checksums, no atomic writes, no locking, no retry framework, no caching. **Size note for orchestrator**: small enough to implement directly — one additive arithmetic script (~150 lines: dedup, three closed-form families, two bounds, frozen-path gate) plus one fake-only test with hand-computable constants. No full pipeline needed. No `/opsx-explore` needed: every primitive (inputs, predicates, gates, bounds, rule) is frozen above.
2. **T-2 — Sequence extraction + IID/drift/burst families.** Execute §3 exactly: per-source dedup to 205/287/383 sequences; drift (z, β, quarters), autocorrelation (r_1…r_5), dispersion (D) with the frozen flags; write the `families` block of D-1. Any §3.1 assertion failure ⇒ K2-4 STOP; `SE == 0` / zero-variance lag ⇒ STOP per §9 items 2–3.
3. **T-3 — Adaptive-m counterfactual budget arithmetic.** Execute §4 exactly: T-3a `S_a = 20·P_lo` vs 4 bits per source; T-3b `S_spread = 10·(max − mean)` vs 215 bits per source; write the `counterfactual` block of D-1. No other bound, no fitted law, no interpolation.
4. **T-4 — Mechanical word + independent batch-end review.** Emit exactly one of PASS/KILL per §5 on 2M (K2-1/K2-2 with reason; K2-3/K2-4 stops carry no word); write D-2 + D-3; independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against SF-01…SF-08; FAIL ⇒ rework + re-review, never publish-then-patch. Before review PASS, zero promotion of any number in this batch.

---

## §16 Planner handoff (read-only verification behind this freeze; no execution)

- Dedup predicates verified read-only 2026-09-29 against the frozen files (planner opened no `.ttbin`, no bundle, no `(a,b)`, no `rows.json`): 410/574/766 rows = 205/287/383 sf × 2 arms; `Δm = 4` on all three sources; `raw == u2` on all rows; cross-arm agreement on all superframes; per-arm means 244.29/260.44/259.85 reproduce `M0-REALFRAME/RESULT.md` §§2.1–2.3.
- CQ presence fields verified: all five `status == OK`; `H_A_given_B` 0.79089947 / 0.81957888 / 0.79837921 / 0.82351165 / 0.82567853 reproduce `JOINT-PRICING` §2.1 transcriptions to 8 dp.
- R-4 / R-215 character-verified against `JOINT-PRICING` §17.2 (`M = 1100`, fits by 4; `M = 1319`, excess 215; Scope A, CQ-J21c).
- This packet writes exactly one new file (itself). No workspace root, frozen packet, or `AGENTS.md` touched. No commit.
