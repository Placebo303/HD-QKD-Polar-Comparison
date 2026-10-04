# JOINT-PRICING-R2 — Frozen Executable Packet (corrected single-block total-form re-evaluation)

- **Status**: FROZEN — awaits Pre-EXECUTE + new grant (§14). This packet authorizes nothing by itself.
- **Track**: **EXPLORE** (analytic; zero data contact — see §0.1).
- **Proposal authority**: this packet is the re-evaluation required by `docs/research_cycles/JOINT-PRICING/PREREG_AND_AUTH.md` §17.3 (executed KILL withdrawn as a decision; corrected numbers sit in the §5.3(a) MARGINAL band; formal re-evaluation required, not decided by that section). It changes no scientific input, no `f` grid, no backoff, no threshold, no data role — only the total-form label correction (M is the tag-inclusive total) plus the STAGE0 §16.3 machine-check wiring that would have caught the miscount pre-execution.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.
- **Frozen antecedents (read, never re-verified here)**: STAGE0 `STAGE0_PACKET.md` §16.1 identities (I-TOTAL/I-LEAK/I-BUDGET/I-GATE/I-SHAPE) adopted by reference (§3); JOINT-PRICING §§1–16 preserved as the executed-but-miscounted record; JOINT-PRICING §17.3 carried verbatim in §17 below.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Re-price, under the **corrected single-block total form** (`M(f) = ceil(1024·f·H)` **is** the tag-inclusive total; leak is `M − 64`), the exact joint question JOINT-PRICING asked — six already-persisted JSON files (§2), frozen `f` grid plus backoff-inside-ceil columns (§4), two entropy scopes (primary ten-plane Scope A, sensitivity five-plane Scope B), disclosure totals under both D-1 tag accountings with no headline designated, per-capture budget comparisons, transcription-fidelity check — closed by one mechanical decision word: PASS, MARGINAL, or KILL (§5). The anticipated outcome on the frozen numbers is **MARGINAL per §5.3(a)** (nominal Scope-A total 1100 fits by 4; `+20%` backoff total 1319, excess 215), with the §5.4 thin-margin concern acute (4-bit nominal margin < 64-bit tag) for any continuation.

### Non-Goals

- No decoder call, no construction call, no `.ttbin` open, no channel-bundle open, no `(a, b)` array open, no raw-data contact of any kind (§2.3).
- No FER, efficiency, leakage, `f`, SKR, or key figure; no method comparison or ranking; no claim that any method corrects; no claim that a joint design exists, is constructible, decodes, or works (§11).
- No designation of a headline tag ratio (D-1 deferred; §3.6).
- No route closure, qualification, publication number, or acceptance of any method. A MARGINAL here licenses no joint-design work; a PASS with THIN-MARGIN licenses no downstream design packet until the user explicitly addresses the margin on record (§5.4).
- No modification of any frozen packet (`JOINT-PRICING/PREREG_AND_AUTH.md` §§1–17, `STAGE0_PACKET.md`), any existing workspace root (including `workspace/jp_*/`, `workspace/s0_1bbe38ac/`, `workspace/cq_*/`), `results/`, `comparison_bench/outputs_comparison/`, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push. No re-decision of Stage 0 (executed KILL 1875 / excess 771 stands; §13).

### Impact Scope

- **Written by this stage**: no new repo code beyond freezing the §10 P-2 scoped manifest (the corrected `joint_pricing.py` total-form + its corrected fake test + the shared `accounting_identities.py` helper + its fake test — all four already present in the working tree as untracked files, frozen at Pre-EXECUTE, not rewritten here), plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/jp_<uuid8>` (§6).
- **Read-only inputs**: the five CQ JSONs plus `S0_RESULT.json` of §2. Nothing else is read for content.
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root, the two frozen packets, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2

EXPLORE (not `EXPLORE_HEAVY`: millisecond-scale arithmetic), on the identical argument JOINT-PRICING §0.1 made and the audit confirmed: arithmetic over six already-persisted non-sensitive channel statistics (§2), bounded and reversible (one process, ≤300 s, ≤1 GiB, fresh additive root), no claim beyond a budget-fit table plus a decision word under the §11 ceiling, no real-data contact, no route closure, no publication claim, no destructive output, no scientific-input change (the total-form fix is a label/category correction to the *same* frozen numbers, not a new hypothesis). Uncertainty defaults do not apply; failure modes are met by JP-equivalent gates plus C-1/C-2/F-1…F-4 (§10), not escalation.

---

## §1 Frozen question (answerable in one shot)

For each of the five measured captures, price a **joint** code at the same efficiency target (`f` grid of §4, identical to Stage 0's) and the same block length Stage 0 used (**n = 1024 symbols per superframe**; one joint block = one 1024-symbol superframe), and determine whether the joint rate allocation fits the frozen disclosure budget **in the corrected total form and with the §11 ceiling applied**.

### §1.1 Joint cost basis: which entropy, primary vs priced

Carried unchanged from JOINT-PRICING §1.1 (verbatim scope definitions):

- **Scope A — PRIMARY: `H(A|B)` over all ten planes.** Primary because (a) commensurate with Stage 0's ten-plane scope; (b) the audit's unsupported figure was computed on this basis; (c) by `H(A|B) = H(U1|B) + H(U2|U1,B)` the conservative (larger) joint cost basis. The §5 decision rule operates on Scope A only.
- **Scope B — SENSITIVITY, priced not assumed: `H(U2|U1,B)` over the five planes the reconciliation alphabet actually codes.** Reported with the explicit caveat (§12) that this stage does not resolve which scope a joint construction would code, nor the budget's applicability to Scope B beyond the arithmetic shown.

---

## §2 Frozen input list (read-only)

Identical to JOINT-PRICING §2 (survives unchanged per §17.3). Exactly these six files; no other file is opened for content:

| # | Path | Bytes | UTC mtime (measured 2026-09-28) | Role |
|---|---|---|---|---|
| I-1 | `workspace/cq_15d6f160/CQ-20a.json` | 8632 | 2026-09-27 09:48:32 UTC | Arm A OK group (500K) |
| I-2 | `workspace/cq_15d6f160/CQ-20b.json` | 8628 | 2026-09-27 09:50:34 UTC | Arm A OK group (1M) |
| I-3 | `workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json` | 4221 | 2026-09-27 09:21:12 UTC | Arm B source 1M |
| I-4 | `workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json` | 4235 | 2026-09-27 09:24:52 UTC | Arm B source 1p5M |
| I-5 | `workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json` | 4211 | 2026-09-27 09:28:26 UTC | Arm B source **2M** (M0 baseline; drives §5) |
| I-6 | `workspace/s0_1bbe38ac/S0_RESULT.json` | 19701 | 2026-09-27 11:59:00 UTC | transcription-fidelity reference |

Fields consumed per I-1…I-5: `status` (must be `OK`), `channel.ser`, `channel.plane_rates_lsb_first` (provenance only), `channel.H_U1_given_B`, `channel.H_U2_given_U1B`, `channel.H_A_given_B`. From I-6: per-source recorded `H` values for the fidelity check (§3.7).

### §2.1 Transcribed `H` values (carried from JOINT-PRICING §2.1; files govern; mismatch = STOP)

| source | `H(A|B)` (Scope A) | `H(U2\|U1,B)` (Scope B) | `H(U1\|B)` (chain check) |
|---|---|---|---|
| CQ-20a | 0.79089947 | 0.76687736 | 0.02402211 |
| CQ-20b | 0.81957888 | 0.79518146 | 0.02439743 |
| CQ-J21a | 0.79837921 | 0.77422846 | 0.02415075 |
| CQ-J21b | 0.82351165 | 0.79928241 | 0.02422924 |
| CQ-J21c | 0.82567853 | 0.80076697 | 0.02491156 |

### §2.2 `p_k` provenance (carried, not consumed)

Per JOINT-PRICING §2.2: ten-plane `p_k` vectors are those of `STAGE0_PACKET.md` §2.1; consumed nowhere here; cited only for the scope fact.

### §2.3 Zero-decode / no-data-contact statement

Carried verbatim in force from JOINT-PRICING §2.3: the execution SHALL NOT open any `.ttbin`, any channel bundle, any `pairs.parquet`, any `(a, b)` array, or any raw data. The script's allowed-input gate admits exactly the six frozen paths and refuses any path outside them and any path ending in `.ttbin`, `.npz`, `.parquet`.

### §2.4 Standing citation discipline (required verbatim wherever invoked)

Carried verbatim from JOINT-PRICING §2.4: the two fenced forms of `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B.1 (plane structure: 「零观测到的跨面共错；单面翻转结构」 with the 1e-6 detection-limit qualifier; the negative only as fence, never本体), the `0.098260` prohibition, the 1104-nominal-convention rule, and the claim-10 ratio prohibition.

---

## §3 Frozen formulas — CORRECTED total form (single-block shape; STAGE0 §16.1 adopted)

Authoritative basis (adopted by reference, not restated at length): `STAGE0_PACKET.md` §16.1 identities — **I-TOTAL** (`TOTAL(f,H) = ceil(f·1024·H)`, tag-inclusive), **I-LEAK** (`LEAK = TOTAL − 64`, tag-exclusive), **I-BUDGET** (`B_T = 1104`, `B_L = 1040`), **I-GATE** (`T_int ≤ 1104 ⟺ T_int − 64 ≤ 1040`, tag added exactly once), **I-SHAPE single-block arm** (one syndrome + one tag: the f-derived ceil **is** the total; forming `ceil + 64` double-counts and overstates every excess by exactly 64). The joint code is the single-block shape.

Block length **n = 1024 symbols** per superframe. Per-symbol entropies from each capture's **own-source** file (never cross-source average, never V17 ladder).

1. **Joint total (Scope A, primary)**: `M_A(f) = ceil(1024·f·H(A|B))` bits per superframe — **the tag-inclusive TOTAL**. Budget-compared directly: fit ⟺ `M ≤ 1104`, excess `E = M − 1104`.
2. **Joint total (Scope B, sensitivity)**: `M_B(f) = ceil(1024·f·H(U2|U1,B))` — likewise the tag-inclusive total in its scope.
3. **Ceiling**: `ceil` applies to the redundancy product **after** the backoff multiplier (§4), exactly mirroring Stage 0's backoff semantics. No floor, no rounding, no post-ceil adjustment.
4. **Leak form (derived only where a leak figure is genuinely needed)**: `L(f) = M(f) − 64` vs leak budget **1040** (`1104 − 64`, I-BUDGET). The leak gate is verdict-equivalent to the total gate by I-GATE; it never replaces the budget-compared total.
5. **Per-capture disclosure totals under both D-1 accountings** (§3.6): Comparison A `T_single(f) = M(f)` vs `1104`; Comparison B `T_recorded(f) = (M(f) − 64) + 1024 = M(f) + 960` vs `2064`. **The executed forms (`M + 64` vs 1104; `M + 1024` vs 2064) are withdrawn and SHALL NOT appear.**
6. **Budget**: **1104 bits** per 1024-symbol superframe (single-tag nominal); **2064 bits** (`1104 + 960`) recorded-tag consistent. Derivation chain carried from `STAGE0_PACKET.md` §3 item 5 via JOINT-PRICING §3 item 5 (displayed-nominal `(5m+64)/(1024·H_corr)`; M0 m=208 point `5·208 + 64 = 1104`). Frozen convention, not measured headroom.
7. **Joint feasibility**: feasible iff `0 < M(f) ≤ 10240`. Otherwise recorded **infeasible with reason**, never clamped.
8. **Transcription-fidelity check**: per source, `H(A|B)` and `H(U2|U1,B)` from I-1…I-5 must equal I-6 counterparts **exactly** (float equality), chain `H(U1|B) + H(U2|U1,B) = H(A|B)` within `1e-9`. Else STOP (§9). Stage-0 `Σh2 − H(A|B)` gaps carried as reference context, not recomputed.
9. **Margin report**: per source, `M_A` at `f = 1.3` nominal and at `+20%` backoff, headrooms `1104 − T_single` and `2064 − T_recorded` (equal by the §3.6 invariance).

### §3.6 Tag accounting under D-1 (both totals carried distinctly; no headline designated)

Decision D-1 DEFERRED (same standing as JOINT-PRICING §3.6). This packet therefore:

- carries **Comparison A (single-tag nominal, Stage-0 basis)**: `T_single = M` vs `B_single = 1104`;
- carries **Comparison B (recorded 16-tag consistent)**: `T_recorded = (M − 64) + 1024 = M + 960` vs `B_recorded = 2064`;
- **designates neither as headline**;
- demonstrates the invariance in the table rather than asserting it: cost and budget shift by the same 960 bits, so the excess `E = M − 1104 = ((M − 64) + 1024) − 2064` is **identical under both comparisons** — the verdict stays tag-accounting-invariant as §3.6 requires. The script computes both excess columns; the reviewer verifies the identity on ≥1 capture by hand (JR-02). The executed excess reading `M − 1040` (a total against the leak budget — category error) is withdrawn.

### §3.8 What changed vs the executed packet (labels only; grid/inputs/rule survive)

`M` relabelled from "leak" to **tag-inclusive total**; Comparison A `M + 64 → M`; Comparison B `M + 1024 → (M − 64) + 1024`; excess `M − 1040 → M − 1104` on both comparisons. Uniform-shift rule (exact): every joint cell's corrected excess is its executed excess minus 64. §2 inputs, §4 grid and backoff-inside-ceil semantics, §5.1/§5.3/§5.4 rule text, §5.5, §§6–16 machinery survive per §17.3 (§17 below).

---

## §4 Frozen `f` grid and backoff columns (carried原文 — multipliers unchanged; `M` now denotes the tag-inclusive total)

Five `M` columns per scope per source (5 sources × 2 scopes × 5 columns = 50 `M` cells, plus 5×2 disclosure-total pairs, 5 fidelity rows, 5 margin rows), matching Stage 0's grid for comparability:

| Column | Formula | Purpose |
|---|---|---|
| `M(1.2)` | `ceil(1024·1.2·H)` | Optimistic sensitivity: one efficiency step below the frozen gate |
| `M(1.3)` | `ceil(1024·1.3·H)` | **Primary nominal**: matches the frozen `f = 1.3` reference (`nonbinary_v25_gate.py:29` `R_TARGET = 1.3`); feeds the §5 rule |
| `M(1.4)` | `ceil(1024·1.4·H)` | Pessimistic sensitivity: one step above the gate, no tuning |
| `M(1.3,+10%)` | `ceil(1024·1.3·1.10·H)` | Moderate finite-length backoff (effective `f = 1.43` pre-ceil); margin observation only |
| `M(1.3,+20%)` | `ceil(1024·1.3·1.20·H)` | **Decision-driving finite-length backoff** (effective `f = 1.56` pre-ceil); feeds the §5 rule |

Backoff semantics frozen: the backoff factor multiplies the redundancy product *inside* the ceil (not added to `M` after). The backoff factors are carried over from Stage 0 **for comparability only** — this stage does not establish that they are adequate for a joint construction (§12). No other `f`, no other backoff, no interpolation, no refit. The `f` grid is reported, never tuned — sensitivity columns cannot move the decision word. **The decision-driving column is `M(1.3,+20%)`; all other columns are sensitivity.**

---

## §5 Frozen decision rule (PASS / MARGINAL / KILL)

Applied **mechanically** to the frozen table on the **2M source** (CQ-J21c — the M0 baseline source) in **Scope A**. The `M` table is frozen before comparison with the budget (outcome-independent). `M` throughout is the corrected tag-inclusive total (§3); `T_single = M`, `T_recorded = M + 960`.

> **§5.1 PASS.** Iff, on CQ-J21c in Scope A, at `f = 1.3` with `+20%` backoff, the allocation is **feasible** (`0 < M ≤ 10240`) **and** fits under **both** tag comparisons (`T_single ≤ 1104` and `T_recorded ≤ 2064` — equivalent by the §3.6 invariance, both shown): the word is **PASS**.

> **§5.2 KILL — executed firing WITHDRAWN (no re-decision of the clause text here).** The executed KILL is withdrawn as a decision and retained as evidence of an executed-but-miscounted stage: the §5.2 clause did **not** fire under corrected arithmetic (nominal Scope-A total 1100 ≤ 1104). The audit-estimate parenthetical inside the frozen §5.2 — `≈1319` bits, over by `≈215` — was computed in the correct form and survives verbatim; it now reads as the backoff outcome, not a nominal outcome.

> **§5.3 MARGINAL (the middle band — frozen, not left undefined).** Every outcome between §5.1 and §5.2 — in particular (a) fit at `f = 1.3` nominal on 2M but FAIL with `+20%` backoff (the audit's anticipated case: the hypothesis fits ideal arithmetic but not finite-length margin — a ~5-bit nominal margin is not a pass), or (b) the full §5.1 condition met on 2M but failed on one or more of the other four sources: the word is **MARGINAL**. Consequence: **no joint-design work is licensed**; the operator returns to the main thread with the frozen table; any continuation requires a **new proposal + new packet + new grant** — never a relaxed re-reading of this packet. MARGINAL is terminal for this packet, exactly as KILL is.

> **§5.4 What PASS does and does not license.** A PASS prices a budget fit under backoff; it licenses **only** the drafting of a joint-design packet. It licenses no decoder run, no construction run, no performance claim of any kind, no FER/efficiency/leakage/`f`/SKR/key figure, no method comparison, and no execution. **Thin-margin flag**: a PASS whose nominal single-tag margin (`1104 − T_single` at `f = 1.3`) is fewer than 64 bits carries a `THIN-MARGIN` flag, and no downstream design packet may be drafted until the user explicitly addresses the margin on record (audit §5 remedy). Bare fit under the decision-driving backoff column is sufficient for PASS — no further margin is required — but a thin nominal margin may not be spent silently.

> **§5.5 Scope B never decides.** The Scope-B (`H(U2|U1,B)`) columns are reported and budget-compared arithmetically, but no Scope-B outcome can move the decision word in either direction.

Anticipated application (not a decision by this packet — the operator applies §5 mechanically at execution): corrected CQ-J21c Scope A gives nominal `M = 1100` (fits by 4) and backoff `M = 1319` (excess 215), i.e. the **§5.3(a) MARGINAL band**. The 4-bit nominal margin is below one tag: had the word been PASS, the THIN-MARGIN flag would in any case have blocked downstream design until the user addresses the margin on record; as MARGINAL, no design work is licensed at all.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/jp_<uuid8>/` (uuid8 recorded in §14 P-6; new uuid8 distinct from the executed `workspace/jp_<uuid8>/` root's uuid, which is retained as-is — R2 reuses the frozen script's `jp_` prefix and `JP_*` filenames per §10 P-2/P-6, distinguished by uuid only). **No existing root may be written.**

| # | File | Content |
|---|---|---|
| D-1 | `workspace/jp_<uuid8>/JP_RESULT.json` | One JSON result. Frozen schema: `inputs` (6 paths + sizes + mtimes + `status` echoes), `formulas` (the §3 strings as executed, corrected total-form), per-source per-scope `M` table (2 × [`H`, 5 `M` columns, feasibility flags]), per-source per-scope `totals` (`T_single = M` vs 1104 and `T_recorded = M + 960` vs 2064 per column, both excess columns `M − 1104`), `leak` (derived `M − 64` vs 1040 where shown), `fidelity`, `margin`, `decision` (PASS/MARGINAL/KILL + fired §5 clause + evidence pointers + `THIN-MARGIN` flag state), `resources` |
| D-2 | `workspace/jp_<uuid8>/JP_SUMMARY.md` | Short Markdown summary: tables only, the decision word, the §11 ceiling restated verbatim. No ranking sentence beyond sorting sources by disclosure total with the ceiling restated |
| D-3 | `workspace/jp_<uuid8>/JOINT_PRICING_LOG.md` | Single append-only log (EXPLORE contract): attempts, machine-gate results, the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/jp_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against JR-01…JR-08. FAIL blocks promotion of every number; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| JR-01 | Input fidelity: exactly the six §2 paths opened, sizes + mtimes match, all five CQ `status == OK`, both `H` fields present; §2.1 transcription exact; no `.ttbin`/`.npz`/`.parquet`/raw/`(a,b)` opened | `JP_RESULT.json` `inputs` + log + script source |
| JR-02 | Formula fidelity (corrected): `M = ceil` is the budget-compared total (`T_single = M ≤ 1104`); leak derived as `M − 64` vs 1040 only where needed; `T_recorded = M + 960 ≤ 2064`; backoff inside ceil; both excess columns equal `M − 1104` (reviewer hand-recomputes ≥1 capture under both comparisons); no `M + 64` vs 1104 and no `M − 1040` excess anywhere outside the quoted withdrawal note | fake tests (C-1/C-2) + reviewer hand recomputation |
| JR-03 | Column completeness: five §4 columns × 2 scopes × 5 sources (50 `M` cells), 10 disclosure-total pairs, 5 fidelity rows, 5 margin rows; no extra column, no tuned `f` | `JP_RESULT.json` |
| JR-04 | Decision mechanics: exactly one of PASS/MARGINAL/KILL with the fired §5 clause cited, Scope A 2M only, table frozen before comparison; `THIN-MARGIN` flag state recorded (anticipated: MARGINAL §5.3(a); any PASS with nominal margin < 64 carries THIN-MARGIN) | `JP_RESULT.json` `decision` + summary |
| JR-05 | Budget: wall ≤ 300 s, peak RSS ≤ 1 GiB, 1 CPU, threads pinned, one process, sequential; breach ⇒ INCOMPLETE, retained, never continued | log + `resources` |
| JR-06 | No-overwrite: fresh `workspace/jp_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; frozen packets byte-untouched; new repo files = exactly the §10 P-2 manifest | filesystem + git state |
| JR-07 | Deliverables + review: D-1…D-4 complete in the fresh root; §11 ceiling respected verbatim; independent batch-end review PASS | review document |
| JR-08 | Claim-ceiling machine check: `0.098260`/`0.09826` zero hits, `f_eff` zero hits, tokens `366`, `1.6×`/`1.6x` zero hits in the fresh root (only inside the quoted §11 ceiling); no numeric FER/efficiency/leakage/`f`/SKR/key claim, no ranking sentence, no design-existence claim, no headline-tag designation | `rg` over `workspace/jp_<uuid8>` + reviewer read |

---

## §8 Budget (frozen ceiling)

One process, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`; numpy-only arithmetic), sequential, **no retry, no resume** except the single preregistered infra repair below. Wall **≤ 300 s**, peak RSS **≤ 1 GiB**. Breach ⇒ INCOMPLETE, retained, never continued. (Ceiling generous by ~3 orders on wall and ~2 on memory; it must never be the thing under test.)

**Preregistered repair (single, infra-only)**: at most one repair+rerun, only for infrastructure failure (crash, OOM-kill, tool-side timeout, lost transcript) with **unchanged** scientific inputs, `f` grid, backoff factors, budget reading, tag accountings, thresholds, data roles, tested question; failed attempt retained in the R2 log in the same root. Any scientific-input/threshold/§5-rule change is a new packet, not a repair.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the six §2 files absent, unreadable, size/mtime drifted, CQ `status != OK`, or an `H` field missing/non-scalar.
2. Transcription-fidelity violation (CQ `H` ≠ `S0_RESULT.json` counterpart exactly, or chain residual > `1e-9`).
3. A formula ambiguous as written here (do not interpolate — stop).
4. Any attempt, successful or attempted, to open a `.ttbin`, channel bundle, `pairs.parquet`, `(a, b)` array, or any raw data.
5. Any invented `H` value, cross-source averaging, or V17-ladder input.
6. Any total-form regression: a budget-compared `M + 64` vs 1104, a recorded `M + 1024` vs 2064, an excess `M − 1040`, or a bare joint ceil labelled `leak`/`parity` reaching the comparison (F-1…F-4 tripwire, §10 P-8).
7. Budget breach (§8).
8. Output collision (`workspace/jp_<uuid8>` exists) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
9. Any evidence-label error (wrong source/file/line, relabelled status, altered §2.4 fence, tag total presented as headline).

On stop: retain evidence in place, **do not adjust inputs to fit**, return to main with the failing check, exact command, exact error. No rerun except the §8 repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before granting)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped manifest (frozen here) | New repo files = exactly four: `comparison_bench/src/comparison_bench/cli/joint_pricing.py` (corrected total-form) + `comparison_bench/tests/test_joint_pricing_fake.py` (corrected fake test) + `comparison_bench/src/comparison_bench/cli/accounting_identities.py` (shared C-1/C-2/C-3 helper, stdlib+math only) + `comparison_bench/tests/test_accounting_identities_fake.py` (helper fake test). All four already present untracked in the working tree; Pre-EXECUTE freezes them (hashes recorded). Frozen packets, `perplane_stage0.py`, `S0_RESULT.json`, every `workspace/` root: byte-untouched. `git diff --stat -- src/ experiments/ tools/` empty apart from the four additive paths |
| P-3 | Focused tests T0 — REQUIRED all-pass | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_joint_pricing_fake.py comparison_bench/tests/test_accounting_identities_fake.py -p no:cacheprovider` — must be **all-pass** on fresh additive `workspace/jp__pytest_<uuid8>` roots. **What the fakes assert** (hand constants `f = 1.3, N = 1024, H = 0.5, TAG = 64, B = 1104`; zero data contact): C-1 (`ceil(1024·1.3·0.5) = 666`; `LEAK = 602`; margins `438 = 438`); backoff inside ceil (`ceil(1024·1.3·1.2·0.5) = 799`); boundary (`ceil(1024·1.3·1.0) = 1332`); gate both sides under **both** comparisons (hand `1104` within / `1105` over on `T_single` and `T_recorded`); C-2 trap (hand `Q = 666 + 64 = 730` FAILS); real-function shape identity on hand inputs (no `M + 64` reaching the gate); fidelity comparator both sides; path-gate refusal of planted `.ttbin`/`.npz`/`.parquet`. Plus `python -m py_compile` on both cli modules |
| P-4 | Input size/mtime check | `stat` the six §2 paths: sizes + UTC mtimes match §2 exactly; CQ `status` values read as `OK` (drift check only) |
| P-5 | Output absence | `workspace/jp_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded |
| P-6 | Exact command frozen | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.joint_pricing --inputs <six frozen paths> --root workspace/jp_<uuid8> --execute --execution-authorized` (refuse without both flags). Root uuid8 fixed here at Pre-EXECUTE |
| P-7 | Budgets + stops read back | §8 ceilings and §9 stop rules read back verbatim |
| P-8 | Forbidden-pattern + shape-identity gate (STAGE0 §16.3 F-1…F-4, run over the R2 script, its test, and this packet; reviewer dispositions each hit in writing against the declared single-block shape) | F-1: `rg -n -U 'ceil\(.*1024.*\)[\s\S]{0,400}\+\s*(64\|TAG_SINGLE)\b'` — single-block hits guilty until proven otherwise (the honest R2 hits are `leak = total − 64` derivations and `(M − 64) + 1024` recorded-companion construction, each dispositioned). F-2: `rg -ni '(leak\|parity)[^:\n]{0,60}=\s*ceil\(1024'` + `M(f) = ceil` co-occurring with `leak` within 3 lines — a bare joint ceil may be named `total`/`M_total`/`joint_bits`, never `leak`/`parity` (leak appears only as `M − 64`). F-3: `rg -n 'totals_single\(1040\) == 1104\|== m - 1040\|M \+ 64 = 1104'` — must be zero live hits (old-gate fixtures survive only inside explicitly marked CORRECTED/superseded comment blocks). F-4: any test asserting `(M+64)−1104 == (M+1024)−2064` as correctness evidence without C-1/C-2 first — must be absent (the R2 test asserts C-1/C-2 on the real function first; the invariance asserted is `M − 1104` on both comparisons) |
| P-9 | Protected roots + forbidden reads | Prove the six input files' parent roots otherwise untouched; `rg` the script for `ttbin\|npz\|parquet\|decode\|ldpc\|construct\|bundle` open/decode-shaped tokens returns only refusal-gate lines (zero read paths) |

### §10.1 Focused-test decision (justification)

No new script and no new test file: the corrected `joint_pricing.py` (total-form, `totals_single(m) = m`, `totals_recorded(m) = m − 64 + 1024`, excess `m − 1104`) plus its corrected fake test (C-1 on the real function, C-2 double-count trap, both-sides both-comparisons gate, superseded-gate comment blocks) plus the shared `accounting_identities.py` helper (C-1/C-2/C-3 on hand constants, stdlib+math only) plus its fake test already exist in the working tree and are frozen by P-2. Extending `perplane_stage0.py` is rejected (accepted Stage-0 evidence; distinct single-block vs ten-block shapes). Per `AGENTS.md` §5.7 the smallest sufficient unit is freezing these four additive files, not generalizing them.

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation)

> Joint pricing is budget-fit arithmetic about one joint cost basis, nothing more. This stage establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement; NO key figure; NO method comparison or ranking; NO claim that any method corrects any frame; and NO claim that a joint design exists, is constructible, decodes, or works anywhere. No headline tag ratio is designated: all tag totals are carried distinctly and none is selected. The legacy value 0.098260 is not cited as a measurement in any deliverable in any form. The void HDC and void Layered-Binary figures are not used as a baseline in any form. The symbol f_eff does not appear in any deliverable in any form. A PASS prices a budget fit under backoff; it licenses only the drafting of a design packet, and no performance claim, no decoder claim, and no execution.

---

## §12 What this stage cannot decide (with the cheapest test that would)

Carried from JOINT-PRICING §12 (total-form correction changes none of it): (1) no correction evidence — cheapest test a future joint-design packet with construction + decoding on measured-rate synthetic draws (not licensed beyond drafting, and not licensed at all on MARGINAL); (2) no constructibility/decodability at the priced allocation; (3) no realisable-rate gap beyond ideal `f`-scaled entropy with ceil; (4) backoff adequacy for a joint construction unvalidated (comparability convention only); (5) ten- vs five-plane scope and `bin_width_ps = 200` convention unresolved — science-input changes needing their own packets.

---

## §13 Carried notes (binding on this packet)

- **Stage 0 stands.** `STAGE0_PACKET.md` §16.2 verdict adopted: ten-block shape honest (`Σm + 64` vs 1104, tag counted once); executed KILL (nominal total 1875, excess 771; backoff total 2233, excess 1129) unchanged; Stage-0-side numerical quotations need no correction.
- **Shape rule.** Single-block stages compare the bare ceil against 1104 (I-TOTAL/I-GATE); ten-block stages add one shared tag (I-SHAPE). A blanket "`M + 64` forbidden" rule false-positives on honest ten-block totals — every §10 P-8 hit is dispositioned against the declared shape.
- **D-1.** Both tag comparisons carried distinctly per §3.6; no headline designated here or in any deliverable.

---

## §14 Grant block (EMPTY — new grant required)

- Grant verbatim: *(none yet — this packet authorizes nothing by itself)*.
- Date / granter: *(to be filled at grant)*.
- Scope when granted: freezing this packet's manifest + executing the single §10 P-6 command within the §8 ceilings only. All other lines (Stages 1–3 of the per-plane line, proxy line, u1 line, real-frame route) remain as they stand.

---

## §15 What this packet is for

This packet exists to **formally re-evaluate, under a new grant, the joint-pricing question with the tag counted once**: corrected nominal Scope-A total 1100 fits by 4, `+20%` backoff total 1319 exceeds by 215 — the §5.3(a) MARGINAL band with a nominal margin smaller than the tag itself. The re-evaluation is mechanical, zero-design-cost, and terminal for this packet: MARGINAL licenses no joint-design work (any continuation needs a new proposal + packet + grant), and even a PASS-shaped outcome would carry THIN-MARGIN and be blocked from downstream design until the user addresses the margin on record. The executed KILL stays on record as executed-but-miscounted evidence; it is not deleted, not edited, not re-argued here.

---

## §16 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-JR01** — Freeze verification of the P-2 manifest (read-only): confirm `joint_pricing.py` implements the §3 corrected total-form (`joint_bits = ceil`, `totals_single(m) = m` vs 1104, `totals_recorded(m) = m − 64 + 1024` vs 2064, excess `m − 1104` both comparisons, leak derived as `m − 64`), `accounting_identities.py` exposes C-1/C-2/C-3 on hand constants, both fake tests assert per §10 P-3; record hashes. No edits to frozen packets or workspace roots.
2. **T-JR02** — Run the §10 P-3 T0 command (exact): `.venv/bin/python -m pytest comparison_bench/tests/test_joint_pricing_fake.py comparison_bench/tests/test_accounting_identities_fake.py -p no:cacheprovider` plus `py_compile` on both cli modules. All-pass required; failures return to main (no repair-by-rewrite inside Pre-EXECUTE).
3. **T-JR03** — Pre-EXECUTE measurement (§10 P-1…P-9) by main; fill the `workspace/jp_<uuid8>` uuid8 only on PASS, including the F-1…F-4 grep record with per-hit dispositions.
4. **T-JR04** — Execute the single frozen §10 P-6 command; operator writes D-1…D-3. Any STOP (§9) retains evidence and returns to main; only the §8 infra repair is permitted.
5. **T-JR05** — Independent batch-end review → D-4 against JR-01…JR-08; FAIL ⇒ rework + re-review, never publish-then-patch.

**Size note for orchestrator**: small enough to implement directly — no new code to write (four additive files frozen as-is), one pytest command, one frozen execution command, one review. No full pipeline. No `/opsx-explore`: every primitive (H values, corrected formulas, budget chain, tag accountings, grid, rule) is frozen above.

---

## §17 Appendix — JOINT-PRICING §17.3 carried verbatim (the authority for this re-evaluation; no re-decision here)

### §17.3 Decision status and clause survival (no re-decision here)

- The executed **KILL is withdrawn as a decision** and retained as evidence of an executed-but-miscounted stage. The §5.2 KILL clause did **not** fire under corrected arithmetic (nominal Scope-A total 1100 ≤ 1104).
- The corrected numbers sit in the **§5.3(a) MARGINAL band** (nominal fit, `+20%` backoff fail) with a 4-bit nominal margin — the thin-margin concern of §5.4 is acute for any continuation, since any future design packet must confront a margin smaller than the tag itself. **Formal re-evaluation (MARGINAL per §5.3(a)) is required; it is not decided by this section.**
- Survive unchanged: §2 inputs, §4 grid and backoff-inside-ceil semantics, §5.1/§5.3/§5.4 rule text, §5.5 (Scope B never decides), §§6–16 machinery.
- Do not survive: the §3 items 1–2 "**leak**" labels (M is the total; leak is `M − 64`); Comparison A as executed (`M + 64` vs 1104 → corrected: **`M` vs 1104**); Comparison B as executed (`M + 1024` vs 2064 → corrected: **`(M − 64) + 1024 = M + 960` vs 2064**); the §3.6 excess reading (the identity `E = (M+64) − 1104 = (M+1024) − 2064 = M − 1040` survives as *arithmetic* but `M − 1040` is not an excess against any budget under correction — the excess is `M − 1104` identically on both comparisons, so the verdict stays tag-accounting-invariant as §3.6 requires); §5.2's executed firing (the audit-estimate parenthetical inside §5.2 — `≈1319` bits, over by `≈215` — was computed in the correct form and survives verbatim).
- The machine-check specification that would have caught this pre-execution is STAGE0 §16.3 (invariants C-1/C-2, patterns F-1…F-4, three-item wiring, and the stated prohibitions) — adopted by reference, not repeated.
