# JOINT-PRICING — Frozen Executable Packet (joint-code budget-fit arithmetic, option-E pricing gate)

- **Status**: FROZEN — awaits Pre-EXECUTE + grant (§14). This packet authorizes nothing by itself.
- **Track**: **EXPLORE** (analytic; zero data contact — see §0.1).
- **Proposal authority**: this packet is a direct remedy for `docs/research_cycles/SESSION-AUDIT-20260928/SESSION_AUDIT.md` §5 (the single most consequential weakness: the unsupported jointly-coded "fits with ~5 bits to spare" narrative). It mirrors the frozen structure of `docs/research_cycles/PERPLANE-BINARY-LDPC/STAGE0_PACKET.md` (§§3–5 budget, stop-rule and claim-ceiling structure) and redesigns nothing. Any conflict between this packet and the audit's remedy text is a STOP (§9), not a patch license.
- **Grant**: §14 (verbatim user authorisation, 2026-09-28). Covers freezing this packet + executing joint pricing within the ceilings of §8. Nothing else.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Answer, with no decoding and no construction at all, whether a jointly-coded alternative at the same efficiency target and block length Stage 0 used fits inside the frozen disclosure budget **including the backoff columns and with the claim ceiling applied**. The work is pure pricing arithmetic over six already-persisted JSON files (§2): the joint leak `M(f) = ceil(1024·f·H)` on a frozen `f` grid plus finite-length backoff columns (§§3–4) in two entropy scopes (primary ten-plane, sensitivity five-plane), disclosure totals under both D-1 tag accountings with no headline designated, per-capture budget comparisons, a transcription-fidelity check of the measured `H` values against `S0_RESULT.json` — closed by one mechanical decision word: PASS, MARGINAL, or KILL (§5). If the answer is that the joint allocation does not fit under backoff, option E is abandoned at zero design cost (§15).

### Non-Goals

- No decoder call, no construction call, no `.ttbin` open, no channel-bundle open, no `(a, b)` array open, no raw-data contact of any kind (§2.3).
- No FER, efficiency, leakage, `f`, SKR, or key figure; no method comparison or ranking; no claim that any method corrects; no claim that a joint design exists, is constructible, decodes, or works (§11).
- No designation of a headline tag ratio (D-1 deferred; §3.6).
- No route closure, qualification, publication number, or acceptance of any method.
- No modification of any runner, construction, decoder, config, existing workspace root, `STAGE0_PACKET.md`, `S0_RESULT.json`, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: exactly two new files — `comparison_bench/src/comparison_bench/cli/joint_pricing.py` (additive arithmetic script, T-J01) and `comparison_bench/tests/test_joint_pricing_fake.py` (fake-only test, T-J02) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/jp_<uuid8>` (§6).
- **Read-only inputs**: the five CQ JSONs plus `S0_RESULT.json` of §2. Nothing else is read for content (code, docs, and configs cited elsewhere in this packet are frozen references carried from planning, not execution inputs).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (including `workspace/s0_1bbe38ac/` and `comparison_bench/src/comparison_bench/cli/perplane_stage0.py`), `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE — confirmed against `AGENTS.md` §1.2

This packet is **EXPLORE** (not `EXPLORE_HEAVY`: millisecond-scale arithmetic, no costly execution), confirmed against the §1.2 applicability matrix ("Synthetic diagnostics → EXPLORE" and "Parameter scans (synthetic) → EXPLORE"):

1. **Input character**: the six inputs are already-persisted, non-sensitive channel *statistics* (float scalars in JSON), produced by the closed CHAN-QUALITY-SURVEY batch and the executed Stage 0. This stage opens no `.ttbin`, no channel bundle, no `(a, b)` array, no raw data of any kind (§2.3). "Real data" in the matrix means contact with real/private/raw data; arithmetic over frozen numbers is not data contact — the identical argument Stage 0's §0.1 made, which the audit's §3 confirmed as correctly classified.
2. **Bounded and reversible**: one process, one CPU, ≤300 s, ≤1 GiB (§8); one fresh additive root, append-only (§6).
3. **No claim**: the §11 ceiling forbids every claim-bearing figure (FER, efficiency, leakage, `f`, SKR, key, ranking, correction, design existence, headline tag). The only output is a budget-fit arithmetic table plus a decision word that prices one cost basis (§5.4).
4. **Uncertainty default**: no concrete risk named here defaults this to DECIDE. The foreseeable failure modes (misread input, formula drift, evidence-label error) are met by the input size/mtime gate (JP-01), the transcription-fidelity check (§3.7), the fake-only test (§10 P-3), and the batch-end review (JP-07) — not by escalation.
5. **No escalation trigger**: this stage touches no real data, closes no route, makes no publication claim, performs no destructive output, incurs no material cost, and changes no scientific input or hypothesis — it prices the audit's frozen numbers under Stage 0's frozen grid.

---

## §1 Frozen question (answerable in one shot)

For each of the five measured captures, price a **joint** code at the same efficiency target (`f` grid of §4, identical to Stage 0's) and the same block length Stage 0 used (**n = 1024 symbols per superframe**; the joint block is one 1024-symbol superframe, mirroring Stage 0's `n_plane = 1024` bits per plane), and determine whether the joint rate allocation fits the frozen disclosure budget **including the backoff columns and with the §11 ceiling applied**.

### §1.1 Joint cost basis: which entropy, primary vs priced

The joint cost basis is the **joint conditional entropy, per symbol, in bits/symbol**. Two scopes are frozen; both are priced, exactly one decides:

- **Scope A — PRIMARY: `H(A|B)` over all ten planes** (the full-symbol conditional entropy). Primary because (a) it is commensurate with Stage 0's ten-plane scope — Stage 0's own arithmetic treated the ten-plane question (`Σ_k m_k` over ten planes vs the 1104 budget) and the comparison means something only on the same scope; (b) the audit's unsupported figure (`1.3 × 0.8257 × 1024 ≈ 1099`) was computed on this basis, so pricing it here answers the exact claim the audit found unsupported; (c) by the entropy chain `H(A|B) = H(U1|B) + H(U2|U1,B)` it is the conservative (larger) joint cost basis for the full symbol. The §5 decision rule operates on Scope A only.
- **Scope B — SENSITIVITY, priced not assumed: `H(U2|U1,B)` over the five planes the reconciliation alphabet actually codes.** Stage 0's arithmetic treated the ten-plane question; the five-plane question is a different scope and is **priced as its own column, not assumed, not decided**. It is reported with the explicit caveat (§12) that this stage does not resolve which scope a joint construction would code, nor the budget's applicability to Scope B beyond the arithmetic shown.

---

## §2 Frozen input list (read-only)

Exactly these six files. No other file is opened for content by the execution.

| # | Path | Bytes | UTC mtime (measured 2026-09-28) | Role |
|---|---|---|---|---|
| I-1 | `workspace/cq_15d6f160/CQ-20a.json` | 8632 | 2026-09-27 09:48:32 UTC | Arm A OK group (500K): `plane_rates_lsb_first`, `ser`, `H_U1_given_B`, `H_U2_given_U1B`, `H_A_given_B` |
| I-2 | `workspace/cq_15d6f160/CQ-20b.json` | 8628 | 2026-09-27 09:50:34 UTC | Arm A OK group (1M): same fields |
| I-3 | `workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json` | 4221 | 2026-09-27 09:21:12 UTC | Arm B source 1M: same fields |
| I-4 | `workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json` | 4235 | 2026-09-27 09:24:52 UTC | Arm B source 1p5M: same fields |
| I-5 | `workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json` | 4211 | 2026-09-27 09:28:26 UTC | Arm B source **2M** (the M0 baseline source; drives the §5 decision rule) |
| I-6 | `workspace/s0_1bbe38ac/S0_RESULT.json` | 19701 | 2026-09-27 11:59:00 UTC | Stage-0 result: transcription-fidelity reference for every `H` value below |

Fields consumed per I-1…I-5 file: `status` (must be `OK`), `channel.ser`, `channel.plane_rates_lsb_first` (carried for provenance only; enters no arithmetic), `channel.H_U1_given_B`, `channel.H_U2_given_U1B`, `channel.H_A_given_B`. Fields consumed from I-6: the per-source recorded `H(A|B)` and `H(U2|U1,B)` values used in the transcription-fidelity check (§3.7). Every other key is provenance context only.

The `p_k` and `H` values must be the same numbers Stage 0 used, or the comparison means nothing — enforced by JP-01 and §3.7, never by adjustment (§9).

### §2.1 Transcribed `H` values (Scope A primary, Scope B sensitivity, chain check)

(Full precision lives in the JSONs; the script reads the JSON values, never this transcription. Any mismatch between this transcription and the files is a STOP under §9 — the files govern.)

| source | `H(A|B)` (Scope A) | `H(U2\|U1,B)` (Scope B) | `H(U1\|B)` (chain check) |
|---|---|---|---|
| CQ-20a | 0.79089947 | 0.76687736 | 0.02402211 |
| CQ-20b | 0.81957888 | 0.79518146 | 0.02439743 |
| CQ-J21a | 0.79837921 | 0.77422846 | 0.02415075 |
| CQ-J21b | 0.82351165 | 0.79928241 | 0.02422924 |
| CQ-J21c | 0.82567853 | 0.80076697 | 0.02491156 |

(`H(A|B)` per `STAGE0_PACKET.md` §2.1; `H(U2|U1,B)` per ibid. §13.2; `H(U1|B)` per `CHAN-QUALITY-SURVEY/RESULT.md` §§2–3. Chain identity `H(U1|B) + H(U2|U1,B) = H(A|B)` holds per source, e.g. CQ-J21c `0.02491156 + 0.80076697 = 0.82567853`.)

### §2.2 `p_k` provenance (carried, not consumed)

The ten-plane `p_k` vectors are those of `STAGE0_PACKET.md` §2.1, reproduced in `S0_RESULT.json` and `S0_SUMMARY.md`. This stage consumes no `p_k` value; they are cited only to state the scope fact: Stage 0 priced ten planes, this stage prices the joint symbol.

### §2.3 Zero-decode / no-data-contact statement

The execution SHALL NOT open any `.ttbin` file, any channel bundle (`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`, `gamma_f03_pb.npz` — named here only to forbid them), any `pairs.parquet`, any `(a, b)` array, or any raw data of any kind. The script's allowed-input gate (§10, T-J01) admits exactly the six frozen paths above and refuses any path outside them and any path ending in `.ttbin`, `.npz`, `.parquet`.

### §2.4 Standing citation discipline (required verbatim wherever invoked)

Wherever the channel structure or the five-capture measurements are invoked, the packet requires verbatim the standing fenced forms of `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B.1:

(i) Plane structure:

> 已定事实是 **「零观测到的跨面共错；单面翻转结构」**. 约一百万对中零个双面错误只排除高于约 1e-6 的多面率，**低于探测限的罕见双翻未被排除**. 措辞「位面相互独立」**只在附带该探测限限定时**可用。引用证据时用三元组：零共错、popcount 限于 {0,1}、每次误差翻面数 1.0.

(ii) The negative:

> 只能以围栏形式：「**五个已测采集中无已测得的更易工作点；未测组按在案理由不提供证据**」。**本体形式（「不存在更易数据」）绝不可单独引用。**

Additionally: the legacy value `0.098260` is never cited as a measurement (§11); the 1104 budget is carried as a frozen nominal convention, never as an empirical headroom discovery (audit §2 claim 9: M0's `5×208+64 = 1104` equals the budget by definition); and the derived ratios of audit §2 claim 10 (`2–4×`, `1.6×`, `≈366 sym/s`) appear nowhere in any deliverable.

---

## §3 Frozen formulas

Block length **n = 1024 symbols** per superframe (one joint block = one 1024-symbol superframe). Per-symbol entropies `H` are the Scope-A / Scope-B values of §2.1 from each capture's **own-source** file (never a cross-source average, never the V17 ladder).

1. **Joint leak (Scope A, primary)**: `M_A(f) = ceil(1024·f·H(A|B))` bits per superframe.
2. **Joint leak (Scope B, sensitivity)**: `M_B(f) = ceil(1024·f·H(U2|U1,B))` bits per superframe.
3. **Ceiling**: the `ceil` applies to the redundancy product **after** the backoff multiplier (§4), exactly mirroring Stage 0's backoff semantics. No floor, no rounding, no post-ceil adjustment.
4. **Per-capture disclosure totals**: computed per capture under **both** tag accountings (§3.6): `T_single(f) = M(f) + 64` and `T_recorded(f) = M(f) + 1024`.
5. **Budget**: **1104 bits** per 1024-symbol superframe under the single-tag accounting; **2064 bits** (`1104 + 960`) under the consistent recorded-tag accounting (§3.6). Budget-derivation chain (carried from `STAGE0_PACKET.md` §3 item 5, unchanged): the displayed-nominal convention `f_super = (5m+64)/(1024·H_corr)` (`m2real_runner.py:247–250`) adds one 64-bit tag per superframe, matching the M0/V80 frozen comparison basis (`m2real-accounting-correction/design.md` §0); at the M0 m=208 baseline point `5·208 + 64 = 1040 + 64 = 1104`. The budget is a frozen convention, not a measured headroom.
6. **Joint feasibility**: the allocation is feasible iff `0 < M(f) ≤ 10240` (the full 1024-symbol × 10-bit block). `M(f) ≤ 0` or `M(f) > 10240` is recorded **infeasible with reason**; infeasibility is never clamped or borrowed-against.
7. **Transcription-fidelity check**: per source, the `H(A|B)` and `H(U2|U1,B)` values read from I-1…I-5 must equal the corresponding values recorded in I-6 (`S0_RESULT.json`) **exactly** (float equality — same files, no tolerance), and the `H(U1|B) + H(U2|U1,B) = H(A|B)` chain must hold to within `1e-9`. Else STOP under §9 (input-drift flag — the check gates the decision word, never adjusts an input). Stage 0's `Σh2 − H(A|B)` coherence gaps (0.498–0.533 bit/symbol) are carried as reference context from `S0_SUMMARY.md`, not recomputed or re-decided.
8. **Margin report**: per source, `M_A` at `f = 1.3` nominal and at `+20%` backoff, with headrooms `1104 − T_single` and `2064 − T_recorded`.

### §3.6 Tag accounting under D-1 (both totals carried distinctly; no headline designated)

Decision D-1 (`m2real-accounting-correction/design.md` §13) is **DEFERRED**: "The user will not pick a unit by inference from code. It does not block T0: all tag totals are carried distinctly and D-1 decides only the headline column." This packet therefore:

- carries **Comparison A (single-tag nominal, Stage-0 basis)**: `T_single = M + 64` vs `B_single = 1104` (one 64-bit tag per superframe; design §1 "Displayed unit");
- carries **Comparison B (recorded 16-tag consistent)**: `T_recorded = M + 1024` vs `B_recorded = 2064` (`1104 + 15·64`; sixteen 64-bit tags per superframe as executed bookkeeping, `m2real_runner.py:749–755, 786–801`; design §1 "Recorded unit");
- **designates neither as headline**;
- shows the budget comparison under each, and demonstrates — rather than asserts — the audit's Stage-0 robustness observation for the joint figure: because cost and budget shift by the same 960 bits, the excess `E = (M + 64) − 1104 = (M + 1024) − 2064 = M − 1040` is **identical under both comparisons**, so the §5 fit verdict is tag-accounting-invariant. The script computes and reports both excess columns; the reviewer verifies the identity on ≥1 capture by hand (JP-02).

---

## §4 Frozen `f` grid and backoff columns

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

Applied **mechanically** to the frozen table on the **2M source** (CQ-J21c — the M0 baseline source) in **Scope A**. The `M` table is frozen before comparison with the budget (outcome-independent).

> **§5.1 PASS.** Iff, on CQ-J21c in Scope A, at `f = 1.3` with `+20%` backoff, the allocation is **feasible** (`0 < M ≤ 10240`) **and** fits under **both** tag comparisons (`T_single ≤ 1104` and `T_recorded ≤ 2064` — equivalent by the §3.6 invariance, both shown): the word is **PASS**.
>
> **§5.2 KILL.** Iff, on CQ-J21c in Scope A, at `f = 1.3` **nominal** (no backoff), the allocation is **infeasible** or over budget under either comparison (`T_single > 1104`, equivalently `T_recorded > 2064`): the word is **KILL**. The joint precondition fails even before finite-length margin; **option E is abandoned at zero design cost**; no joint-design work follows; the frozen `M` table is the killing evidence. (The audit's estimate — ≈1319 bits under Stage 0's own +20% backoff, over by ≈215 — anticipates this outcome; a KILL here confirms it mechanically and is a legitimate, first-class result per §15.)
>
> **§5.3 MARGINAL (the middle band — frozen, not left undefined).** Every outcome between §5.1 and §5.2 — in particular (a) fit at `f = 1.3` nominal on 2M but FAIL with `+20%` backoff (the audit's anticipated case: the hypothesis fits ideal arithmetic but not finite-length margin — a ~5-bit nominal margin is not a pass), or (b) the full §5.1 condition met on 2M but failed on one or more of the other four sources: the word is **MARGINAL**. Consequence: **no joint-design work is licensed**; the operator returns to the main thread with the frozen table; any continuation requires a **new proposal + new packet + new grant** — never a relaxed re-reading of this packet. MARGINAL is terminal for this packet, exactly as KILL is.
>
> **§5.4 What PASS does and does not license.** A PASS prices a budget fit under backoff; it licenses **only** the drafting of a joint-design packet. It licenses no decoder run, no construction run, no performance claim of any kind, no FER/efficiency/leakage/`f`/SKR/key figure, no method comparison, and no execution. **Thin-margin flag**: a PASS whose nominal single-tag margin (`1104 − T_single` at `f = 1.3`) is fewer than 64 bits carries a `THIN-MARGIN` flag, and no downstream design packet may be drafted until the user explicitly addresses the margin on record (audit §5 remedy). Bare fit under the decision-driving backoff column is sufficient for PASS — no further margin is required — but a thin nominal margin may not be spent silently.
>
> **§5.5 Scope B never decides.** The Scope-B (`H(U2|U1,B)`) columns are reported and budget-compared arithmetically, but no Scope-B outcome can move the decision word in either direction.

This implements the audit §5 remedy ("只有带回退仍装下才判 PASS … 若失败则在零设计成本下放弃 E") as two distinct terminal words plus the thin-margin discipline: hard KILL where even nominal arithmetic fails on the baseline source, MARGINAL→new-proposal-required everywhere else short of PASS. Nothing that fails the primary rule proceeds under this packet.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/jp_<uuid8>/` (uuid8 recorded in §14 P-6). **No existing root may be written** — not `workspace/cq_15d6f160/`, not `workspace/cq_4af91a87/`, not `workspace/s0_1bbe38ac/`, not any other `workspace/` root, not `results/`, not `comparison_bench/outputs_comparison/`.

| # | File | Content |
|---|---|---|
| D-1 | `workspace/jp_<uuid8>/JP_RESULT.json` | One JSON result. Frozen schema: `inputs` (6 paths + byte sizes + UTC mtimes + `status` echoes), `formulas` (the §3 strings as executed), per-source per-scope `M` table (2 × [`H`, 5 `M` columns, feasibility flags]), per-source per-scope `totals` (`T_single` vs 1104 and `T_recorded` vs 2064 per column, both excess columns), `fidelity` (CQ-vs-S0 `H` equality, chain residual), `margin` (nominal and +20% headrooms both comparisons), `decision` (`PASS`/`MARGINAL`/`KILL` + which §5 clause fired + evidence pointers + `THIN-MARGIN` flag state), `resources` (wall_s, peak RSS, CPU, command, thread-pin env) |
| D-2 | `workspace/jp_<uuid8>/JP_SUMMARY.md` | Short Markdown summary: tables only, the decision word, the §11 ceiling restated verbatim. No ranking sentence beyond sorting sources by disclosure total with the ceiling restated |
| D-3 | `workspace/jp_<uuid8>/JOINT_PRICING_LOG.md` | Single append-only log (EXPLORE contract): attempts, machine-gate results, the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/jp_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against JP-01…JP-08 (§13-analogous §7 here). FAIL blocks promotion of every joint-pricing number; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| JP-01 | Input fidelity: exactly the six §2 paths opened, byte sizes + UTC mtimes match the table, all five CQ `status == OK`, both `H` fields present per CQ file; transcription of §2.1 matches the files exactly; no `.ttbin`/`.npz`/`.parquet`/raw/`(a,b)` path opened (script path-gate + log) | `JP_RESULT.json` `inputs` + `JOINT_PRICING_LOG.md` + script source |
| JP-02 | Formula fidelity: `M`/ceiling/totals/budget/fidelity per §3; backoff multiplies inside the ceil; both tag comparisons carried with the §3.6 invariance holding (reviewer recomputes ≥1 capture by hand under both comparisons and confirms equal excess) | fake test (§10 P-3) + reviewer hand recomputation |
| JP-03 | Column completeness: all five §4 columns × 2 scopes × 5 sources (50 `M` cells), 10 disclosure-total pairs, 5 fidelity rows, 5 margin rows; no extra column, no tuned `f` | `JP_RESULT.json` |
| JP-04 | Decision mechanics: exactly one of PASS/MARGINAL/KILL, with the fired §5 clause cited, Scope A only, and the evidence table frozen before the comparison; `THIN-MARGIN` flag state recorded | `JP_RESULT.json` `decision` + `JP_SUMMARY.md` |
| JP-05 | Budget: wall ≤ 300 s, peak RSS ≤ 1 GiB, 1 CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`), one process, sequential; breach ⇒ INCOMPLETE, retained, never continued | log + resource lines in `JP_RESULT.json` |
| JP-06 | No-overwrite: fresh `workspace/jp_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots (including `workspace/s0_1bbe38ac/`) untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest | filesystem + git state |
| JP-07 | Deliverables + review: D-1…D-4 complete in the fresh root; §11 ceiling respected verbatim; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | review document |
| JP-08 | Claim-ceiling machine check: the strings `0.098260`/`0.09826` return **zero hits**, the symbol `f_eff` returns **zero hits**, and the tokens `366`, `1.6×`/`1.6x` (claim-10 ratios) return **zero hits** in the fresh root (words may occur only inside the quoted §11 ceiling); no numeric FER/efficiency/leakage/`f`/SKR/key claim, no method-ranking sentence, no joint-design existence/constructibility claim, and no headline-tag designation anywhere in D-1…D-4 | `rg` over `workspace/jp_<uuid8>` + reviewer read |

---

## §8 Budget (frozen ceiling)

One process, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`; numpy-only arithmetic), sequential, **no retry, no resume** except the single preregistered infra repair below. Wall **≤ 300 s**, peak RSS **≤ 1 GiB**. Breach ⇒ INCOMPLETE, retained, never continued.

The ceiling is generous by roughly three orders of magnitude on wall (50 `ceil` evaluations plus table writes execute in milliseconds; the 300 s covers interpreter start, JSON parsing, and logging with headroom) and by roughly two orders on memory (six JSONs total ≈ 49 KiB; resident set stays in the tens of MiB). The generosity is deliberate: the ceiling must never be the thing under test.

**Preregistered repair (single, infra-only)**: at most one repair+rerun is permitted, and only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript) with **unchanged** scientific inputs, `f` grid, backoff factors, budget reading, tag accountings, thresholds, data roles, and tested question; the failed attempt is retained in `JOINT_PRICING_LOG.md` in the same root. Any change to a scientific input, threshold, or the §5 rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the six §2 files absent, unreadable, size/mtime drifted from the table, CQ `status != OK`, or an `H` field missing/non-scalar.
2. Transcription-fidelity violation: a CQ `H` value differs from its `S0_RESULT.json` counterpart (exact float equality), or the `H(U1|B) + H(U2|U1,B) = H(A|B)` chain residual exceeds `1e-9` on any source (input-drift flag).
3. A formula ambiguous as written here (do not interpolate — stop).
4. Any attempt, successful or attempted, to open a `.ttbin`, a channel bundle, a `pairs.parquet`, an `(a, b)` array, or any raw data.
5. Any invented `H` value (a number not read from the §2 files), any cross-source averaging, any use of the V17 ladder as input.
6. Budget breach (§8).
7. Output collision (`workspace/jp_<uuid8>` already exists) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
8. Any evidence-label error (a number cited with the wrong source/file/line, a status relabelled, a §2.4 fenced sentence altered, a tag total presented as headline).

On stop: retain all evidence in place, **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before granting)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/joint_pricing.py` + `comparison_bench/tests/test_joint_pricing_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** (decision §10.1) | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_joint_pricing_fake.py -p no:cacheprovider` — must be **all-pass** on a fresh additive `workspace/jp__pytest_<uuid8>` root. **What the fake asserts** (hand-computable constants, zero data contact — the test reads no CQ JSON, no `S0_RESULT.json`, no `.ttbin`, nothing): the ceiling is applied (`ceil(1024·1.3·0.5) = ceil(665.6) = 666`); the backoff multiplier is applied inside the ceil (`ceil(1024·1.3·1.2·0.5) = ceil(798.72) = 799`); a ceil-boundary case worked by hand (`ceil(1024·1.3·1.0) = ceil(1331.2) = 1332`); the budget gate fires on both sides under **both** tag comparisons (hand `M` giving `M+64 = 1104` within vs `1105` over, and `M+1024 = 2064` within vs `2065` over); the §3.6 invariance identity (`(M+64)−1104 == (M+1024)−2064`) on a hand `M`; scope selection (Scope A consumes the hand `H(A\|B)`, Scope B the hand `H(U2\|U1,B)`); the fidelity comparator on both sides (exact match → pass, planted mismatch → flagged); and the input path-gate refusal of planted `.ttbin` **and** `.npz` paths (plus `.parquet`) |
| P-4 | Input size/mtime check | `stat` the six §2 paths: byte sizes + UTC mtimes match the table exactly; CQ `status` fields read as `OK` (values only — drift check, not a re-read of science) |
| P-5 | Output absence | `workspace/jp_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-6 | Exact command frozen | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.joint_pricing --inputs <six frozen paths> --root workspace/jp_<uuid8> --execute --execution-authorized` (refuse without both flags, M0/CQ/Stage-0 precedent). Root uuid8 fixed here at Pre-EXECUTE |
| P-7 | Budgets + stops read back | §8 ceilings and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove the six input files' parent roots are otherwise untouched (no writes); `rg` the T-J01 script for `ttbin\|npz\|parquet\|decode\|ldpc\|construct\|bundle` open/decode-shaped tokens returns only the refusal-gate lines (zero read paths) |

### §10.1 Focused-test decision: new script + new test (justification)

A **new additive script** is required; extending the existing Stage-0 script (`perplane_stage0.py`) is **rejected**. Reasons: (i) that script together with `S0_RESULT.json` is accepted, reviewed evidence — any edit invalidates the provenance link between the frozen Stage-0 table and the code that produced it; (ii) joint pricing needs distinct inputs (two `H` scopes, a scope selector, dual tag comparisons, the §3.7 fidelity check) and a distinct decision rule, so extension would couple two independent evidence lines; (iii) per `AGENTS.md` §5.7, the smallest scientifically correct additive unit is a ~120-line pure-arithmetic script reusing Stage 0's house style (dual `--execute --execution-authorized` flags, frozen-path gate, `main() -> int`), not a generalization of the existing one. New code needs a new fake-only test per the same section's logic (new arithmetic — joint ceil sizing, dual-comparison budget gate, invariance identity, fidelity comparator, `.npz` refusal — covered by no existing test).

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation)

> Joint pricing is budget-fit arithmetic about one joint cost basis, nothing more. This stage establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement; NO key figure; NO method comparison or ranking; NO claim that any method corrects any frame; and NO claim that a joint design exists, is constructible, decodes, or works anywhere. No headline tag ratio is designated: all tag totals are carried distinctly and none is selected. The legacy value 0.098260 is not cited as a measurement in any deliverable in any form. The void HDC and void Layered-Binary figures are not used as a baseline in any form. The symbol f_eff does not appear in any deliverable in any form. A PASS prices a budget fit under backoff; it licenses only the drafting of a design packet, and no performance claim, no decoder claim, and no execution.

---

## §12 What this stage cannot decide (with the cheapest test that would)

1. **It cannot show that any joint code corrects anything.** No frame is decoded here. Cheapest test: a future joint-design packet with construction + decoding on measured-rate synthetic draws (EXPLORE) — which this stage does not license beyond drafting (§5.4).
2. **It cannot show that a joint design is constructible or decodable at the priced allocation.** A fitting `M` is arithmetic headroom, not evidence that a 1024-symbol code at that rate decodes. Cheapest test: same future design packet — construct at the frozen `M` and decode.
3. **It cannot speak to the realisable-rate gap beyond this arithmetic.** The priced `M(f)` is an ideal `f`-scaled entropy product with ceil; finite-length achievability at n=1024 symbols is untested. Cheapest test: the construction/decoding test of (2) at matched disclosure.
4. **It cannot establish that the carried-over backoff columns are adequate for a joint construction.** The +10%/+20% factors are Stage-0 comparability conventions, not validated joint finite-length margins. Cheapest test: same future design packet — measure whether the backoff-priced allocation decodes, and re-freeze the margin only on that evidence.
5. **It cannot resolve the ten-plane versus five-plane scope question** (which alphabet a joint construction would code) **or the bin-width question** (all five captures use the imposed `bin_width_ps = 200` convention; cf. `STAGE0_PACKET.md` §12 item 4). Both are science-input changes requiring their own packets; this stage prices Scope B and fences every citation via §2.4 instead.

---

## §13 Carried notes (binding on this packet)

- **§13.1 Ten planes, not nine.** Per `STAGE0_PACKET.md` §13.1 (`BITS = 10`, 10×10 co-error construction, 10-element vectors). Scope A prices the full ten-plane symbol; nothing here assumes a nine-plane treatment.
- **§13.2 `H(U2|U1,B)` range is 0.7669–0.8008, not 0.774–0.801.** Per `STAGE0_PACKET.md` §13.2 (tasking's range excluded the CQ-20a value 0.76687736). The §2.1 table carries the corrected values.
- **§13.3 The 1104 budget is a nominal-equality convention, not an empirical headroom discovery.** Per the audit's §2 claim 9: M0's `5·208+64 = 1104` equals the budget by definition. This packet carries the budget as the frozen comparison basis and forbids citing any fit margin as a headroom "finding" beyond the §5 decision word.
- **§13.4 Fence-soundness note answered.** The audit's §3 notes Stage 0 decided on the single-tag budget while D-1 defers the headline. This packet answers it for the joint figure: both tag comparisons are carried distinctly per §3.6, the invariance is demonstrated in the table (not asserted), and no headline is designated.

---

## §14 Grant block

- Grant verbatim: 「按这个顺序开」
- Date / granter: 2026-09-28, user — given in a session where the three items were described as: run the E analytic pricing packet; fix the fence violations and NOW.md staleness; file the audit report and a decision-log entry.
- Scope: this grant covers **freezing this packet and executing joint pricing within the §8 ceilings only**. **Stages 1–3 of the per-plane line, the proxy line, the u1 line, and the real-frame route all remain as they stand**; in particular the proxy line's own continuation needs its own packet and grant, and Stage 2's real-frame component remains a DECIDE step requiring its own preregistration, Pre-EXECUTE, and explicit grant before anything runs.

---

## §15 What this packet is for

This packet exists to **price a claim the audit found unsupported, cheaply, before any design spending**: the narrative that a jointly-coded alternative "fits" the disclosure budget with about 5 bits to spare — an ideal multiplication with no ceiling, no backoff, no construction, never executed (audit §5). The remedy the audit prescribes is exactly this packet: the same frozen inputs, `ceil(1024·f·H)` with the backoff columns applied, all tag totals carried distinctly per D-1, and **PASS only if the allocation still fits under backoff**. If the answer is that the joint allocation does not fit under backoff — the audit's estimate (≈1319 bits under +20% backoff, over by ≈215) says it will not — **the correct outcome is that option E is abandoned at zero design cost, and that KILL is a legitimate, first-class result of this packet**, not a failure of it.

---

## §16 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-J01** — Implement `comparison_bench/src/comparison_bench/cli/joint_pricing.py` (new file only): stdlib + numpy pure arithmetic; argv takes exactly the six §2 paths + `--root workspace/jp_<uuid8>` + dual `--execute --execution-authorized` flags (refuse without both); startup path-gate admits only the frozen six and refuses any `.ttbin`/`.npz`/`.parquet` path; computes §3 both scopes with the §4 five-column grid, both §3.6 tag comparisons with both excess columns, the §3.7 fidelity check, and the §5 decision word printed last; writes D-1 + D-2 + appends D-3 log lines into the fresh root only; `main() -> int` + `if __name__ == "__main__"` house style. No touch to `perplane_stage0.py` or any other existing file.
2. **T-J02** — Implement `comparison_bench/tests/test_joint_pricing_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/jp__pytest_<uuid8>` roots; zero scientific/real-data contact — hand constants only, reads no input file).
3. **T-J03** — Pre-EXECUTE measurement (§10 P-1…P-8) by main; fill the execution root uuid8 only on PASS.
4. **T-J04** — Execute the single frozen §10 P-6 command; operator writes D-1…D-3. Any STOP (§9) retains evidence and returns to main; the only permitted rerun is the §8 preregistered infra repair.
5. **T-J05** — Independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against JP-01…JP-08; FAIL ⇒ rework + re-review, never publish-then-patch.

**Size note for orchestrator**: small enough to implement directly — one additive arithmetic script (~120 lines, pure ceil/table/gate logic + frozen-path gate + fidelity check) plus one fake-only test with hand-computable constants. No full pipeline needed. No `/opsx-explore` needed: every primitive (H values, formulas, budget chain, tag accountings, grid, rule) is frozen above.

---

## §17 Correction 2026-09-28 — the joint `M + 64` double-count (append-only; §§1–16 above are preserved as the record of what was frozen and executed)

Authority: the single definition in `docs/research_cycles/PERPLANE-BINARY-LDPC/STAGE0_PACKET.md` §16.1 (identities I-TOTAL / I-LEAK / I-BUDGET / I-GATE / I-SHAPE, anchored at `m0_realframe_runner.py:101-106` and `S2_ACCOUNTING_MAP_20260920.md:16`). Nothing here restates it — this section records what it does to *this* packet.

### §17.1 The error

This packet's §3 items 1–2 label `M(f) = ceil(1024·f·H)` a "**leak**", and §3 item 4 / §3.6 form the budget-compared totals `T_single = M + 64` (vs 1104) and `T_recorded = M + 1024` (vs 2064). By I-SHAPE (single-block shape) the bare ceil **is** the tag-inclusive total, so each comparison adds the tag a second time and overstates every excess by exactly 64 bits. The script (`joint_pricing.py:120-122,135-142,155-162`) and the fake test (`test_joint_pricing_fake.py:42-43,54-56` — fixtures asserting `totals_single(1040) == 1104` and excess `m − 1040`, exercised on the actual production values `m = 1100, 1319`) implemented and asserted the mislabelled form faithfully. The propagation path is on record: the audit this packet remedies used the *correct* form throughout (`SESSION_AUDIT.md:25`: joint needs `≈1319` bits, over by `≈215` — no `+64` added); this packet's §3 prose relabelled the ceil as "leak" and both tag comparisons inherited it. (A further framing correction: the tasking brief described the cross-stage check as confirming "the same mistake twice" — Stage 0 made no mistake (STAGE0 §16.2), so the check compared an honest ten-block total against a miscounted single-block total under one shared word, "total".)

### §17.2 Corrected figures (CQ-J21c, Scope A — the §5 decision scope; recomputed this date, pure arithmetic)

- Nominal (`f = 1.3`, `H = 0.8256785297622026` per the frozen input): `1.3·1024·H = 1099.143258819444`, so `M = 1100`. **Correct total 1100 vs 1104 — fits by 4 bits.** Executed form computed `1100 + 64 = 1164`, excess 60 — overstated by exactly 64. (Truncated-`H` check `0.82567853` gives the identical ceil, 1100 — no precision sensitivity at this cell.)
- Backoff (`f = 1.56`): `1.56·1024·H = 1318.9719105833328`, so `M = 1319`. **Correct total 1319 vs 1104 — excess 215.** Executed form computed `1319 + 64 = 1383`, excess 279 — overstated by exactly 64.
- For the record (sensitivity only, never decides per §5.5): Scope B (`H(U2|U1,B) = 0.8007669657724986`, hand constant already carried in the fake test) gives nominal `M = 1066` (fits by 38; executed excess was 26) and backoff `M = 1280` (excess 176; executed 240).
- Uniform-shift rule (exact, no per-cell work needed elsewhere): **every** joint cell's corrected excess is its executed excess minus 64. Spot-applied to the §2.1 transcribed `H(A|B)` values, all five sources fit nominally under correction (excesses −51…−4) and all five fail backoff (+160…+215) — provisional from 8dp transcriptions (ceil-boundary caveat as in STAGE0 §16.2); authoritative confirmation must use the JSON values.

### §17.3 Decision status and clause survival (no re-decision here)

- The executed **KILL is withdrawn as a decision** and retained as evidence of an executed-but-miscounted stage. The §5.2 KILL clause did **not** fire under corrected arithmetic (nominal Scope-A total 1100 ≤ 1104).
- The corrected numbers sit in the **§5.3(a) MARGINAL band** (nominal fit, `+20%` backoff fail) with a 4-bit nominal margin — the thin-margin concern of §5.4 is acute for any continuation, since any future design packet must confront a margin smaller than the tag itself. **Formal re-evaluation (MARGINAL per §5.3(a)) is required; it is not decided by this section.**
- Survive unchanged: §2 inputs, §4 grid and backoff-inside-ceil semantics, §5.1/§5.3/§5.4 rule text, §5.5 (Scope B never decides), §§6–16 machinery.
- Do not survive: the §3 items 1–2 "**leak**" labels (M is the total; leak is `M − 64`); Comparison A as executed (`M + 64` vs 1104 → corrected: **`M` vs 1104**); Comparison B as executed (`M + 1024` vs 2064 → corrected: **`(M − 64) + 1024 = M + 960` vs 2064**); the §3.6 excess reading (the identity `E = (M+64) − 1104 = (M+1024) − 2064 = M − 1040` survives as *arithmetic* but `M − 1040` is not an excess against any budget under correction — the excess is `M − 1104` identically on both comparisons, so the verdict stays tag-accounting-invariant as §3.6 requires); §5.2's executed firing (the audit-estimate parenthetical inside §5.2 — `≈1319` bits, over by `≈215` — was computed in the correct form and survives verbatim).
- The machine-check specification that would have caught this pre-execution is STAGE0 §16.3 (invariants C-1/C-2, patterns F-1…F-4, three-item wiring, and the stated prohibitions) — adopted by reference, not repeated.
