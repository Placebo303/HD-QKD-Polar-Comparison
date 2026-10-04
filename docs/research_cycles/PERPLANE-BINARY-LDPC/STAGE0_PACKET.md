# STAGE0 — Frozen Executable Packet (per-plane binary LDPC, achievable-rate kill gate)

- **Status**: FROZEN — awaits Pre-EXECUTE + grant (§14). This packet authorizes nothing by itself.
- **Track**: **EXPLORE** (analytic; zero data contact — see §0.1).
- **Proposal authority**: `docs/research_cycles/PERPLANE-BINARY-LDPC/PROPOSAL.md` §§1–2, §5 Stage 0, §§6–7. This packet freezes Stage 0; it redesigns nothing. Any conflict between this packet and the proposal is a STOP (§9), not a patch license.
- **Grant**: §14 (verbatim user authorisation, 2026-09-27). Covers freezing this packet + executing Stage 0 within the ceilings of §8. Nothing else.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Answer, with no decoding at all, whether a per-plane rate-adaptive binary LDPC can fit inside the frozen disclosure budget. If it cannot, H1 (`PROPOSAL.md` §1) dies before a single decode is paid for. The work is pure feasibility arithmetic over five already-persisted channel-statistics JSONs (§2): per-plane `h2(p_k)`, required parity bits `m_k` on a frozen `f` grid plus finite-length backoff columns (§§3–4), the disclosure total against the 1104-bit budget, per-plane feasibility, the LSB margin, and a `Σ h2` vs measured `H(A|B)` coherence check — closed by one mechanical decision word: PASS, MARGINAL, or KILL (§5).

### Non-Goals

- No decoder call, no construction call, no `.ttbin` open, no channel-bundle open, no raw-data contact of any kind (§2.3).
- No FER, efficiency, leakage, `f`, SKR, or key figure; no method comparison or ranking; no claim that any method corrects (§11).
- No route closure, qualification, publication number, or acceptance of any method.
- No modification of any runner, construction, decoder, config, existing workspace root, `PROPOSAL.md`, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push.

### Impact Scope

- **Written by Stage 0**: exactly two new files — `comparison_bench/src/comparison_bench/cli/perplane_stage0.py` (additive arithmetic script, T-S01) and `comparison_bench/tests/test_perplane_stage0_fake.py` (fake-only test, T-S02) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/s0_<uuid8>` (§7).
- **Read-only inputs**: the five CQ JSONs of §2. Nothing else is read for content (code cites below were verified by the planner read-only during freezing and are carried as frozen references).
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root, `PROPOSAL.md`, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE — justification against `AGENTS.md` §1.2

Stage 0 is **EXPLORE**, confirmed against the §1.2 applicability matrix ("Synthetic diagnostics → EXPLORE: packet+prompt, machine root, one log, one batch-end review"):

1. **Input character**: the five inputs are already-persisted, non-sensitive channel *statistics* (float vectors and scalars in JSON), produced by the closed CHAN-QUALITY-SURVEY batch. Stage 0 opens no `.ttbin`, no channel bundle, no `(a,b)` array, no raw data of any kind (§2.3). "Real data" in the matrix means contact with real/private/raw data; arithmetic over five frozen numbers is not data contact.
2. **Bounded and reversible**: one process, one CPU, ≤600 s, ≤2 GiB (§8); one fresh additive root, append-only (§7).
3. **No claim**: the §11 ceiling forbids every claim-bearing figure (FER, efficiency, leakage, `f`, SKR, key, ranking, correction). The only output is a feasibility-arithmetic table plus a decision word that licenses downstream *design work only* (§5.4).
4. **Uncertainty default**: no concrete risk named here defaults this to DECIDE. The foreseeable failure modes (misread input, formula drift, evidence-label error) are met by the input size/mtime gate (S0-01), the fake-only test (§10 P-3), and the batch-end review (S0-07/S0-08) — not by escalation.

---

## §1 Hypothesis under test (carried, not re-decided)

H1 per `PROPOSAL.md` §1: ten per-plane rate-adapted binary LDPC codes with a qualified asymmetry-aware decoder achieve strictly lower frame error than the GF(32) nonbinary mainline on the same eval superframes at no larger nominal disclosure. Stage 0 tests only the *necessary arithmetic precondition* of H1: that the required per-plane redundancy fits the frozen budget. A KILL here kills H1's precondition with zero decode cost; a PASS does not confirm any clause of H1 (§12).

---

## §2 Frozen input list (read-only)

Exactly these five files. No other file is opened for content by the execution (code, docs, and configs cited elsewhere in this packet are frozen references carried from planning, not execution inputs).

| # | Path | Bytes | UTC mtime (measured 2026-09-27) | Role |
|---|---|---|---|---|
| I-1 | `workspace/cq_15d6f160/CQ-20a.json` | 8632 | 2026-09-27 09:48:32 UTC | Arm A OK group (500K): `plane_rates_lsb_first` (10, LSB-first), `ser`, `H_U1_given_B`, `H_U2_given_U1B`, `H_A_given_B` |
| I-2 | `workspace/cq_15d6f160/CQ-20b.json` | 8628 | 2026-09-27 09:50:34 UTC | Arm A OK group (1M): same fields |
| I-3 | `workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json` | 4221 | 2026-09-27 09:21:12 UTC | Arm B source 1M: same fields |
| I-4 | `workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json` | 4235 | 2026-09-27 09:24:52 UTC | Arm B source 1p5M: same fields |
| I-5 | `workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json` | 4211 | 2026-09-27 09:28:26 UTC | Arm B source **2M** (the M0 baseline source; drives the §5 decision rule) |

Fields consumed per file: `status` (must be `OK`), `channel.ser`, `channel.plane_rates_lsb_first` (must be a 10-element vector), `channel.H_U1_given_B`, `channel.H_U2_given_U1B`, `channel.H_A_given_B`. Every other key (provenance rows, alignment records, header evidence, stability blocks, command lines) is carried as provenance context only and enters no arithmetic.

### §2.1 Per-plane `p_k` values (transcribed, LSB-first index 0 = LSB plane)

- CQ-20a: `[0.11965904, 0.06193353, 0.03137139, 0.01448533, 0.00736405, 0.00366854, 0.00199612, 0.00107898, 0.00051252, 0.00032369]`
- CQ-20b: `[0.12447303, 0.05997477, 0.03140290, 0.01550912, 0.00740068, 0.00390805, 0.00193864, 0.00090778, 0.00040004, 0.00018463]`
- CQ-J21a: `[0.11992188, 0.05989425, 0.02939691, 0.01467226, 0.00744093, 0.00359184, 0.00201982, 0.00092416, 0.00050495, 0.00020008]`
- CQ-J21b: `[0.12776636, 0.06330303, 0.03196116, 0.01593804, 0.00799965, 0.00392326, 0.00186125, 0.00083365, 0.00051380, 0.00023819]`
- CQ-J21c: `[0.12711631, 0.06325473, 0.03222911, 0.01576779, 0.00784055, 0.00382211, 0.00202707, 0.00097146, 0.00050485, 0.00022438]`

(Full precision lives in the JSONs; the script reads the JSON values, never this transcription. Any mismatch between this transcription and the files is a STOP under §9 — the files govern.)

Measured `H(A|B)` per source (coherence-check targets, §3.5): CQ-20a 0.79089947, CQ-20b 0.81957888, CQ-J21a 0.79837921, CQ-J21b 0.82351165, CQ-J21c 0.82567853.

### §2.2 Path correction (recorded, not silently fixed)

`PROPOSAL.md` §5 cites the Arm B inputs as `workspace/cq_4af91a87/ArmB/CQ-J21a/b/c.json`. The filesystem carries per-source subroots: `workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json` (etc.), measured 2026-09-27. This packet freezes the **actual paths in the table above**; the proposal's shortened paths are superseded for execution.

### §2.3 Zero-decode / no-data-contact statement

The five captures above are the **only** per-plane measurements available, and using them is legitimate because they were measured **without decoding** (zero-decoder batch, `CHAN-QUALITY-SURVEY/RESULT.md` §§1–4). The execution SHALL NOT open any `.ttbin` file, any channel bundle (`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`, `gamma_f03_pb.npz` — named here only to forbid them), any `pairs.parquet`, or any raw data of any kind. The script's allowed-input gate (§10, T-S01) refuses any path outside the five frozen above and any path ending in `.ttbin`, `.npz`, `.parquet`.

### §2.4 Standing citation discipline for the channel-structure premise

`CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` does not exist (the survey's independent review is still outstanding per its `RESULT.md` §6). The standing citation rules are therefore `RESULT.md` §§4/6/7, `PREREG_AND_AUTH.md` Rev 2 §§11/13 (plus the correction note §18 and per-JSON `claim_ceiling` fields). The settled channel-structure premise — "zero observed cross-plane co-error; single-plane-flip structure" — may be cited **only in this fenced form**:

> Across the five captures actually measured, `expected_planes_flipped_per_error` equals 1.0 in every case, co-error off-diagonals are exactly zero, and Gray popcount mass lies only on {0,1} (`CHAN-QUALITY-SURVEY/RESULT.md` §§2–4) — a channel-structure finding, not a method result (ibid. §4). It establishes no FER, efficiency, leakage, `f`, SKR, method comparison, or working method (ibid. §§6–7 and the §11 claim ceiling). Non-observation bounds cross-plane structure only down to the measurement's detection floor (finite-pair resolution); absence of evidence below that floor is not cited.

---

## §3 Frozen formulas (transcribed from the proposal without alteration)

Plane count is **ten** (§13.1). Plane index `k = 0..9`, LSB-first (`plane_rates_lsb_first`; index 0 = LSB plane). Block length `n_plane = 1024` bits per plane (one 1024-symbol superframe yields one 1024-bit block per plane; `PROPOSAL.md` §2.2).

1. **Binary entropy**: `h2(p) = −p·log2(p) − (1−p)·log2(1−p)`, with `h2(0) = h2(1) = 0` by continuity. Log base 2.
2. **Per-plane rate**: `R_k = 1 − f·h2(p_k)` (`PROPOSAL.md` §2.1), with `p_k` that plane's **own-source measured** rate from §2.1 (never the V17 reference ladder, never a cross-source average).
3. **Per-plane parity bits**: `m_k = ceil(1024·(1−R_k))` (`PROPOSAL.md` §2.1), equivalently `m_k(f) = ceil(1024·f·h2(p_k))` (`PROPOSAL.md` §5 Stage 0). The two wordings coincide algebraically by substitution of (2) into (3); the script implements `ceil(1024·f·h2(p_k))` and the result schema records both `R_k` and `m_k`.
4. **Disclosure total**: `Σ_k m_k + 64` bits per 1024-symbol superframe (ten per-plane syndromes plus the single 64-bit tag).
5. **Budget**: **1104 bits** per 1024-symbol superframe. Verified against the frozen basis: the displayed-nominal convention is `f_super = (5m+64)/(1024·H_corr)` (`comparison_bench/src/comparison_bench/cli/m2real_runner.py:247–250`, docstring "this-arm m basis"), adding **one 64-bit tag per superframe** and matching the M0/V80 frozen comparison basis (`openspec/changes/m2real-accounting-correction/design.md` §0, citing `docs/V80_BASELINE_20260921.md` §2; tag-unit finding ibid. §1). At the M0 m=208 baseline point: `5·208 + 64 = 1040 + 64 = 1104`.
6. **Per-plane feasibility**: plane `k` is feasible iff `0 < m_k ≤ 1024`. `m_k ≤ 0` or `m_k > 1024` is recorded **infeasible with reason** (cf. `PROPOSAL.md` §2.1); infeasibility is never clamped, borrowed-against, or levelled away.
7. **Coherence check**: per source, `Σ_k h2(p_k)` against the measured `H(A|B)` (§2.1). Expected: `Σ h2 ≥ H(A|B)` (subadditivity; cf. `PROPOSAL.md` §5). Tolerance: `Σ h2 − H(A|B) ≥ −1e-9`, else STOP under §9 (input-drift flag — the check gates the decision word, never adjusts an input).
8. **LSB margin report**: per source, `m_0` (LSB plane, index 0) at `f = 1.3` nominal and at `+20%` backoff, with headrooms `1024 − m_0` (block) and `1104 − (Σm_k + 64)` (budget).

---

## §4 Frozen `f` grid and backoff columns

Five `m_k` columns per plane per source (5 sources × 10 planes × 5 columns = 250 `m_k` cells, plus 5 disclosure totals, 5 coherence rows, 5 LSB-margin rows):

| Column | Formula | Purpose |
|---|---|---|
| `m_k(1.2)` | `ceil(1024·1.2·h2(p_k))` | Optimistic sensitivity: what the budget looks like one efficiency step below the frozen gate |
| `m_k(1.3)` | `ceil(1024·1.3·h2(p_k))` | **Primary**: matches the frozen `f = 1.3` reference (`nonbinary_v25_gate.py:29` `R_TARGET = 1.3`); feeds the §5 rule |
| `m_k(1.4)` | `ceil(1024·1.4·h2(p_k))` | Pessimistic sensitivity: one step above the gate, no tuning |
| `m_k(1.3,+10%)` | `ceil(1024·1.3·1.10·h2(p_k))` | Moderate finite-length backoff (effective `f = 1.43` pre-ceil); margin observation only |
| `m_k(1.3,+20%)` | `ceil(1024·1.3·1.20·h2(p_k))` | Decision-driving finite-length backoff (effective `f = 1.56` pre-ceil); feeds the §5 rule (`PROPOSAL.md` §2.2: short-block penalty is expected, unquantified, first-order kill risk R1) |

Backoff semantics frozen: the backoff factor multiplies the redundancy product *inside* the ceil (not added to `m_k` after). No other `f`, no other backoff, no interpolation, no refit. The `f` grid is reported, never tuned — sensitivity columns cannot move the decision word.

---

## §5 Frozen decision rule (PASS / MARGINAL / KILL)

Applied **mechanically** to the frozen table on the **2M source** (CQ-J21c — the M0 baseline source carrying the 16/383 FER reference). The `m_k` table is frozen before comparison with the budget (outcome-independent).

> **§5.1 PASS.** Iff, on CQ-J21c, at `f = 1.3` with `+20%` backoff, **every one of the ten planes is feasible** (`0 < m_k ≤ 1024`) **and** `Σ_k m_k + 64 ≤ 1104`: the word is **PASS**.
>
> **§5.2 KILL.** Iff, on CQ-J21c, at `f = 1.3` **nominal** (no backoff), **any plane is infeasible** or `Σ_k m_k + 64 > 1104`: the word is **KILL**. H1's arithmetic precondition fails even before finite-length margin; no Stage-1/2/3 work follows; the frozen `m_k` table is the killing evidence.
>
> **§5.3 MARGINAL (the middle band — frozen, not left undefined).** Every outcome between §5.1 and §5.2 — in particular (a) PASS at `f = 1.3` nominal on 2M but FAIL with `+20%` backoff (the most likely outcome: the hypothesis fits ideal arithmetic but not finite-length margin), or (b) the full §5.1 condition met on 2M but failed on one or more of the other four sources: the word is **MARGINAL**. Consequence: **no Stage-1 work is licensed**; the operator returns to the main thread with the frozen table; any continuation (re-frozen backoff, 2M-only source scope with DECIDE justification for dropping sources, longer blocks as a science-input change) requires a **new proposal + new packet + new grant** — never a relaxed re-reading of this packet. MARGINAL is terminal for this packet, exactly as KILL is.
>
> **§5.4 What PASS does and does not license.** A PASS licenses **only** the drafting of a Stage-1 packet (construction/screening design work). It licenses no decoder run, no construction run, no performance claim of any kind, no FER/efficiency/leakage/`f`/SKR/key figure, no method comparison, and no execution — Stage 1 still needs its own frozen packet, its own authorization boundary, and its own batch-end review.

This implements `PROPOSAL.md` §5's "else KILL H1 … or CHANGE approach only via a new proposal" as two distinct terminal words: hard KILL where even nominal arithmetic fails on the baseline source, MARGINAL→new-proposal-required everywhere else short of PASS. Nothing that fails the primary rule proceeds under this packet.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/s0_<uuid8>/` (uuid8 recorded in §14 P-6). **No existing root may be written** — not `workspace/cq_15d6f160/`, not `workspace/cq_4af91a87/`, not any other `workspace/` root, not `results/`, not `comparison_bench/outputs_comparison/`.

| # | File | Content |
|---|---|---|
| D-1 | `workspace/s0_<uuid8>/S0_RESULT.json` | One JSON result. Frozen schema: `inputs` (5 paths + byte sizes + UTC mtimes + `status` echoes), `formulas` (the §3 strings as executed), per-source `planes` (10 × [`p_k`, `h2`, `R_k(1.3)`, 5 `m_k` columns, feasibility flags]), per-source `totals` (`Σm_k+64` per column vs 1104), `coherence` (`Σh2`, `H(A|B)`, gap), `lsb_margin`, `decision` (`PASS`/`MARGINAL`/`KILL` + which §5 clause fired + evidence pointers), `resources` (wall_s, peak RSS, CPU, command, thread-pin env) |
| D-2 | `workspace/s0_<uuid8>/S0_SUMMARY.md` | Short Markdown summary: tables only, the decision word, the §11 ceiling restated verbatim. No ranking sentence beyond sorting sources by disclosure total with the ceiling restated |
| D-3 | `workspace/s0_<uuid8>/STAGE0_LOG.md` | Single append-only log (EXPLORE contract): attempts, machine-gate results, the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/s0_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against S0-01…S0-08 (§13). FAIL blocks promotion of every Stage-0 number; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| S0-01 | Input fidelity: exactly the five §2 paths opened, byte sizes + UTC mtimes match the table, all five `status == OK`, all five `plane_rates_lsb_first` 10-element; no `.ttbin`/`.npz`/`.parquet`/raw path opened (script path-gate + log) | `S0_RESULT.json` `inputs` + `STAGE0_LOG.md` + script source |
| S0-02 | Formula fidelity: `h2`/`R_k`/`m_k`/total/budget/coherence per §3; both `m_k` wordings coincide; budget 1104 from the §3.5 chain | fake test (§10 P-3) + reviewer recomputation of ≥1 plane by hand |
| S0-03 | Column completeness: all five §4 columns × 10 planes × 5 sources (250 `m_k` cells), 5 disclosure totals, 5 coherence rows, 5 LSB-margin rows; no extra column, no tuned `f` | `S0_RESULT.json` |
| S0-04 | Decision mechanics: exactly one of PASS/MARGINAL/KILL, with the fired §5 clause cited and the evidence table frozen before the comparison | `S0_RESULT.json` `decision` + `S0_SUMMARY.md` |
| S0-05 | Budget: wall ≤ 600 s, peak RSS ≤ 2 GiB, 1 CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`), one process, sequential; breach ⇒ INCOMPLETE, retained, never continued | log + resource lines in `S0_RESULT.json` |
| S0-06 | No-overwrite: fresh `workspace/s0_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest | filesystem + git state |
| S0-07 | Deliverables + review: D-1…D-4 complete in the fresh root; §11 ceiling respected verbatim; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | review document |
| S0-08 | Claim-ceiling machine check: the strings `0.098260`/`0.09826` return **zero hits** and the symbol `f_eff` returns **zero hits** in the fresh root (words may occur only inside the quoted §11 ceiling); no numeric FER/efficiency/leakage/`f`/SKR/key claim and no method-ranking sentence anywhere in D-1…D-4 | `rg` over `workspace/s0_<uuid8>` + reviewer read |

---

## §8 Budget (frozen ceiling)

One process, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`; numpy-only arithmetic), sequential, **no retry, no resume** except the single preregistered infra repair below. Wall **≤ 600 s**, peak RSS **≤ 2 GiB**. Breach ⇒ INCOMPLETE, retained, never continued.

The ceiling is generous by roughly four orders of magnitude on wall (250 `h2` evaluations plus table writes execute in well under a second; the 600 s covers interpreter start, JSON parsing, and logging with headroom) and by roughly two orders on memory (five JSONs total ≈ 30 KiB; resident set stays in the tens of MiB). The generosity is deliberate: the ceiling must never be the thing under test.

**Preregistered repair (single, infra-only)**: at most one repair+rerun is permitted, and only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript) with **unchanged** scientific inputs, `f` grid, backoff factors, budget reading, thresholds, data roles, and tested hypothesis; the failed attempt is retained in `STAGE0_LOG.md` in the same root. Any change to a scientific input, threshold, or the §5 rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the five §2 files absent, unreadable, size/mtime drifted from the table, `status != OK`, or `plane_rates_lsb_first` not 10-element.
2. Coherence violation: `Σ h2 − H(A|B) < −1e-9` on any source (input-drift flag).
3. A formula ambiguous as written here (do not interpolate — stop).
4. Any attempt, successful or attempted, to open a `.ttbin`, a channel bundle, a `pairs.parquet`, or any raw data.
5. Any invented plane value (a number not read from the §2 files), any cross-source averaging, any use of the V17 ladder as input.
6. Budget breach (§8).
7. Output collision (`workspace/s0_<uuid8>` already exists) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
8. Any evidence-label error (a number cited with the wrong source/file/line, a status relabelled, the fenced §2.4 sentence altered).

On stop: retain all evidence in place, **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before granting)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/perplane_stage0.py` + `comparison_bench/tests/test_perplane_stage0_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_perplane_stage0_fake.py -p no:cacheprovider` — must be **all-pass** on a fresh additive `workspace/s0__pytest_<uuid8>` root. **Why new code needs a new test**: T-S01 adds new arithmetic (binary entropy, ceil-boundary parity sizing, budget-gate comparison, coherence check, path refusal) covered by no existing test. **What the fake asserts** (hand-computable constants, zero data contact — the test reads no CQ JSON, no `.ttbin`, nothing): `h2(0.5) == 1.0` exactly; `h2(0.1) ≈ 0.4689955936` to 1e-9; a ceil-boundary `m_k` case worked by hand; infeasibility arms (`m_k ≤ 0` at `p = 0`; `m_k > 1024` at `p = 0.5, f = 1.3` → `ceil(1331.2) = 1332`); the budget gate on both sides of 1104 (synthetic totals 1104 → within, 1105 → over); the coherence comparator on both sides of the −1e-9 tolerance; and the input path-gate refusal of a planted `.ttbin`/`.npz` path |
| P-4 | Input size/mtime check | `stat` the five §2 paths: byte sizes + UTC mtimes match the table exactly; `status` fields read as `OK` (values only, the Planner's read already proved content — this is a drift check, not a re-read of science) |
| P-5 | Output absence | `workspace/s0_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-6 | Exact command frozen | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.perplane_stage0 --inputs <five frozen paths> --root workspace/s0_<uuid8> --execute --execution-authorized` (refuse without both flags, M0/CQ precedent). Root uuid8 fixed here at Pre-EXECUTE |
| P-7 | Budgets + stops read back | §8 ceilings and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove the five input files' parent roots are otherwise untouched (no writes); `rg` the T-S01 script for `ttbin|npz|parquet|decode|ldpc|construct|bundle` open/decode-shaped tokens returns only the refusal-gate lines (zero read paths) |

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation)

> Stage 0 is feasibility arithmetic about whether a per-plane rate allocation fits a disclosure budget, nothing more. This stage establishes NO FER, NO efficiency, NO leakage, NO f, NO SKR, and NO key figure; NO method comparison or ranking; NO claim that any method corrects any frame; and NO baseline for any later comparison. The legacy value 0.098260 is not cited in any Stage-0 deliverable in any form. The void HDC and void Layered-Binary figures are not used as a baseline in any form. The symbol f_eff does not appear in any Stage-0 deliverable in any form. A PASS licenses only the drafting of a Stage-1 packet; it licenses no performance claim, no decoder claim, and no execution.

---

## §12 What Stage 0 cannot decide (with the cheapest test that would)

1. **It cannot show that a per-plane binary LDPC corrects better than the GF(32) mainline.** No frame is decoded here. Cheapest test: the Stage-1 synthetic screening packet (`PROPOSAL.md` §5.1) — rate-targeted PEG per plane at the frozen `m_k` table, decoded with corrected symmetric per-plane priors on measured-rate synthetic draws (EXPLORE, non-decisive by design).
2. **It cannot validate the decoder** (not the corrected symmetric prior (a), not the asymmetry ablation (c), neither's threshold nor throughput). Cheapest test: same Stage-1 packet — (a) first, then (c) at matched disclosure, with the wall/iteration ledger (`PROPOSAL.md` §§2.4, 5.1).
3. **It cannot speak to the short-block risk R1 beyond what an infeasible `m_k` reveals.** A feasible `m_k` is arithmetic headroom, not evidence that a rate-≈0.3 irregular code decodes at n=1024. Cheapest test: the Stage-1 synthetic LSB-only decode at the frozen `m_0` (one plane, 1200 trials, EXPLORE) — if the LSB plane alone fails at matched disclosure while quiet planes pass, H1's binding constraint is identified without real-frame cost (`PROPOSAL.md` §6 R1).
4. **It cannot resolve whether the measured channel's single-plane structure is an artifact of the 200 ps bin width (R3/R4).** All five captures use `bin_width_ps = 200` as an imposed convention. Cheapest test: none within this line — re-binning is a science-input change requiring its own DECIDE packet with alignment re-derivation; this packet instead fences every citation to the measured binning via §2.4 (`PROPOSAL.md` §6 R3).

---

## §13 Carried corrections (from the proposal — binding on this packet)

- **§13.1 Ten Gray planes, not nine.** The tasking text said "nine"; every machine artifact shows ten: `BITS = 10` (`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:28`, verified at freezing), the 10×10 co-error construction (`ibid.:292–299`, `np.zeros((BITS, BITS))` at `:293`, verified at freezing), and 10-element `plane_rates_lsb_first` vectors in all five CQ JSONs (§2.1). This packet uses ten throughout. A future 9-plane treatment must freeze which plane is excluded and why; nothing here assumes it.
- **§13.2 `H(U2|U1,B)` range is 0.7669–0.8008, not 0.774–0.801.** Measured: CQ-20a 0.76687736, CQ-J21a 0.77422846, CQ-20b 0.79518146, CQ-J21b 0.79928241, CQ-J21c 0.80076697 (tasking's range excluded the CQ-20a value). The `H(A|B)` ≈ 0.790–0.826 range matches (0.79090–0.82568) and is carried.

---

## §14 Grant block

- Grant verbatim: 「现在把两条审查待办和T 清单一起收掉，然后Stage 0转成可执行的冻结包，然后执行stage 0」
- Date / granter: 2026-09-27, user.
- Scope: this grant covers **freezing this packet and executing Stage 0 within the §8 ceilings only**. The "two review todos and T list" clause is recorded as context of the user's batch intent, not as an expansion of this packet. **Stages 1–3 remain unauthorised**; in particular Stage 2's real-frame component is a DECIDE step requiring its own preregistration, Pre-EXECUTE, and explicit grant before anything runs.

---

## §15 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-S01** — Implement `comparison_bench/src/comparison_bench/cli/perplane_stage0.py` (new file only): stdlib + numpy pure arithmetic; argv takes exactly the five §2 paths + `--root workspace/s0_<uuid8>` + dual `--execute --execution-authorized` flags (refuse without both); startup path-gate refuses any input outside the frozen five and any `.ttbin`/`.npz`/`.parquet` path; computes §3 per plane with the §4 five-column grid; writes D-1 + D-2 + appends D-3 log lines into the fresh root only; prints the §5 decision word last; `main() -> int` + `if __name__ == "__main__"` house style. No `src/` touch.
2. **T-S02** — Implement `comparison_bench/tests/test_perplane_stage0_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/s0__pytest_<uuid8>` roots; zero scientific/real-data contact — hand constants only, reads no input file).
3. **T-S03** — Pre-EXECUTE measurement (§10 P-1…P-8) by main; fill the execution root uuid8 only on PASS.
4. **T-S04** — Execute the single frozen §10 P-6 command; operator writes D-1…D-3. Any STOP (§9) retains evidence and returns to main; the only permitted rerun is the §8 preregistered infra repair.
5. **T-S05** — Independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against S0-01…S0-08; FAIL ⇒ rework + re-review, never publish-then-patch.

**Size note for orchestrator**: small enough to implement directly — one additive arithmetic script (~150 lines, pure `h2`/ceil/table logic + frozen-path gate) plus one fake-only test with hand-computable constants. No full pipeline needed. No `/opsx-explore` needed: every primitive (plane vectors, `H` targets, formulas, budget chain) is frozen above.

---

## §16 Correction 2026-09-28 — tag-inclusive total vs leak, and the single authoritative definition (append-only; §§1–15 above are preserved as the frozen record)

### §16.1 The definition, stated once, as identities

Authoritative sources (read firsthand for this section):

- **A1.** `comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py:101-106`: `f_super(source, m) = (5*m + 64) / (N * H_CORR[source])` with `N = 1024`, and `f_notag(source, m) = (5*m) / (N * H_CORR[source])`.
- **A2.** `docs/research_cycles/V80-NBLDPC-JAN21/S2_ACCOUNTING_MAP_20260920.md:16`: frozen formula `f_super = (4·(5·(m₂+m₁)) + 64) / (1024·H_full)`, `H_full = 0.83256272` (with the worked numerator `4·245 + 64 = 1044` at `:14`).

Derived identities (implement from these, not from prose):

- **I-TOTAL.** `f = TOTAL / (1024·H)`, so `TOTAL(f,H) = f·1024·H`, integer form `T_int = ceil(f·1024·H)`. **The TOTAL includes the 64-bit tag.**
- **I-LEAK.** `LEAK = TOTAL − 64`. **The LEAK excludes the tag.** (`f_notag·N·H = 5m` is exactly this: parity without tag.)
- **I-BUDGET.** Total budget `B_T = 1104` (at the M0 m=208 point: `5·208 + 64 = 1040 + 64`). Leak budget `B_L = 1104 − 64 = 1040`.
- **I-GATE.** Total form: `T_int ≤ 1104`. Leak form: `T_int − 64 ≤ 1040`. The two gates are equivalent. **The tag is added exactly once between parity and total — never zero times, never twice.**
- **I-SHAPE (the rule prose missed — two shapes, not interchangeable):**
  - *Single-block shape* (one syndrome + one tag: the joint code, the mainline m-basis): the f-derived ceil **is** the total. Compare `ceil(f·N·H)` against 1104 directly. Forming `ceil(f·N·H) + 64` against 1104 double-counts the tag and overstates every excess by exactly 64 bits.
  - *Ten-block shape* (ten per-plane syndromes + ONE shared tag): each `m_k = ceil(1024·f·h2(p_k))` is **pure parity for that plane** — no per-plane tag exists. The frame total is `Σ_k m_k + 64` with the tag added once. This comparison is honest; comparing bare `Σ_k m_k` against 1104 would instead *omit* a really-disclosed tag.
  - A blanket "`M + 64` is forbidden" rule false-positives on the honest ten-block form. Every check below is shape-aware.

### §16.2 What this means for Stage 0 (verdict: NO error — KILL stands)

Stage 0 implements the ten-block shape: the script's per-plane function is named `parity_bits` (`perplane_stage0.py:142-144`, `m_k = ceil(1024·fmult·h)`), and the frame total is `sum(col_ms[c]) + TAG_BITS` (ibid.:279) gated by `total <= 1104` (ibid.:156-158), exactly the packet §3 items 3–4 and §5 rule. Ten pure-parity blocks plus one shared tag, tag counted once. **There is no double-count in Stage 0; the executed KILL stands.**

Independent recomputation from the transcribed `p_k` (CQ-J21c, §2.1), verified this date with `.venv/bin/python` (pure `h2`/ceil arithmetic, no data contact):

- Nominal (`f = 1.3`): `m_k = [732, 453, 274, 156, 89, 49, 29, 15, 9, 5]`, `Σm = 1811`, total `1811 + 64 = 1875`, excess `1875 − 1104 = 771` — **exact match** to the executed figure.
- Backoff (`f = 1.56`): `m_k = [878, 544, 329, 187, 106, 58, 34, 18, 10, 5]`, `Σm = 2169`, total `2233`, excess `1129`.
- Coherence corroboration: `Σh2 = 1.35591693` vs `H(A|B) = 0.82567853`, gap `+0.53024` bit/symbol — inside the packet's carried `+0.498…+0.533` range.
- Caveat: recomputed from 8dp transcribed `p_k`; a ceil-boundary flip against JSON-precision values is possible in principle — the exact nominal match corroborates no flip occurred there.

Disagreement with the tasking brief, recorded as instructed (the brief warned its own statements in this area have been wrong): the brief asserted *both* packets double-count and that Stage 0's excess "changes too" (771 → 707). Verified against A1–A2, that assertion is **declined for Stage 0**: Stage 0's f-derived quantity is per-plane parity, not frame total, so `Σm` against 1104 would understate true disclosure by omitting the tag — contradicting the proposal's own `PROPOSAL.md:99` ("`Σ m_k` plus the tag is the nominal disclosure"), its decision rule (ibid.:206, `Σ m_k + 64 ≤ 1104`), this packet's §3.4/§5, and the M0/V80 tag-counting basis. The probable seed of the misreading is the proposal's loose shorthand at ibid.:204 ("`Σ m_k(f)` vs the 1104-bit nominal budget", no `+64`) — recorded here as the propagation path, not edited (proposal untouched). Likewise the brief's "two stages made the same mistake" framing is corrected: Stage 0 made no mistake, so no cross-stage check could have compared "the same" error — it compared an honest total against a miscounted one under a shared label.

Consequence: **no Stage-0 number changes**, and records quoting `1875`/`771` (`docs/decision-log.md:5130,5136`, `docs/NOW.md:158-159`, `SESSION_AUDIT.md:25,36`, `NEXT-STEP-OPTIONS/PROPOSAL.md:136`) require **no numerical correction**.

### §16.3 The machine check (specification — implement separately; this section authorizes no code change)

Why prose, fake tests, and cross-stage consistency all failed — the mechanism, so the check targets it: the mislabel was baked into frozen spec prose ("Joint leak `M(f) = ceil(1024·f·H)`"); both scripts implemented it faithfully; the joint fake test asserted *self-consistency of the wrong gate* (`test_joint_pricing_fake.py:42-43`: `totals_single(1040) == 1104`; `:54-56`: `excess == m − 1040`, exercised on the actual production values `m = 1100, 1319`); the cross-stage check confirmed two stages shared one label while computing different categories. **No check anchored the total-construction to A1–A2.** The check below does only that.

Executable invariants (hand constants only — `f = 1.3, N = 1024, H = 0.5, TAG = 64, B = 1104` — no scientific input):

- **C-1 (single-block):** `TOTAL(f,H) == ceil(f·N·H)`; `LEAK == TOTAL − 64`; `TOTAL ≤ 1104 ⟺ LEAK ≤ 1040`. Hand: `ceil(1.3·1024·0.5) = ceil(665.6) = 666`; `666 − 64 = 602`; margins `1104 − 666 = 438`, `1040 − 602 = 438`.
- **C-2 (the trap assertion — the case that would have caught the joint stage pre-execution):** let `Q` be the stage's budget-compared quantity on hand inputs; assert `Q − B == ceil(f·N·H) − B`. On the hand constants the joint form computes `Q = 666 + 64 = 730 ≠ 666` and **FAILS**. State it negatively too: `Q == ceil(f·N·H) + TAG` on a single-block stage is a FAIL.
- **C-3 (ten-block):** each `PLANE_PARITY(h) == ceil(f·n·h)`; `FRAME_TOTAL − Σ PLANE_PARITY == 64` exactly (fails on both 0 and 128 — tag omitted and tag doubled both trip).
- Procedural rule: every pricing/arithmetic stage **must expose its budget-compared total as a pure function**, and its fake test **must call the real function on hand inputs and assert the shape-specific identity** declared in its packet §3 (C-1/C-2 for single-block stages; C-3 for per-plane stages). Comparator-only tests on synthetic totals (e.g. `within_budget(1104)`) are necessary but explicitly **not sufficient** — record that sentence in the test file.

Forbidden source patterns (run at Pre-EXECUTE over the stage script, its test, and its packet; reviewer dispositions each hit in writing against the packet-declared shape):

- **F-1 (tag added onto a joint ceil):** `rg -n -U 'ceil\(.*1024.*\)[\s\S]{0,400}\+\s*(64|TAG_SINGLE)\b'` — tripwire. Single-block hits are guilty until proven otherwise; ten-block `sum(...) + TAG` hits are honest iff exactly one addition reaches the budget comparison.
- **F-2 (label fraud):** `rg -ni '(leak|parity)[^:\n]{0,60}=\s*ceil\(1024'` and any `M\(f\) = ceil\(1024…` definition co-occurring with the word `leak` within 3 lines. A bare joint ceil may be named `total`, `M_total`, or `joint_bits` — never `leak` or `parity`.
- **F-3 (fixtures encoding the wrong gate):** `rg -n 'totals_single\(1040\) == 1104|== m - 1040|M \+ 64 = 1104'` — any test asserting (ceil-derived M) + tag == budget as "within", or asserting excess `M − 1040` where `M` is a single-block ceil (correct single-block excess is `M − 1104`; `M − 1040` compares a total against a leak budget — a category error).
- **F-4 (excess-identity laundering):** any test asserting `(M+64)−1104 == (M+1024)−2064` as *correctness evidence* without asserting C-1/C-2 first — the identity holds under both labels, so it proves nothing about the label.

Where it lives — smallest sufficient form (three items, nothing else):

1. One shared fake-only module (~40 lines, stdlib + `math` only, zero imports from science code) asserting C-1/C-2/C-3 on the hand constants above.
2. One added case per stage fake test calling the stage's real total function on hand inputs against the packet-declared shape identity.
3. One added Pre-EXECUTE line: run F-1…F-4 greps; reviewer dispositions each hit against the declared shape in the checklist record.

What the check must **not** do: judge any scientific content (`H` values, ten- vs five-plane scope, backoff adequacy, `f` grid); blanket-ban `+ 64` (honest ten-block totals need it once); require remote/SHA equality or stale-SHA searches; re-run science; grow into schema validation or lint beyond F-1…F-4.

### §16.4 Places needing a correction note (identified here; edited separately — artifacts untouched)

- `comparison_bench/src/comparison_bench/cli/joint_pricing.py:85,120-122,135-142,155-162` (`M` labelled leak; `totals_single = M + 64`; `excess = M − 1040`) and `comparison_bench/tests/test_joint_pricing_fake.py:42-43,54-56` (fixtures encode the wrong gate, including on production `m = 1100, 1319`) — code/test fix is a separate task (not this section; AGENTS.md bans planner code edits).
- `docs/research_cycles/JOINT-PRICING/PREREG_AND_AUTH.md` §§3–5 and the joint result root `workspace/jp_8b6fa2cb/` (root name per main-thread report; **not verified by me — `workspace/` was not read, not even listed**): the packet receives its own dated correction section this date pointing here; the `workspace/` machine artifacts must be retained exactly as produced (executed-but-miscounted evidence).
- `docs/research_cycles/NEXT-STEP-OPTIONS/PROPOSAL.md:92` uses the un-ceiled ideal `≈1099` ("fits marginally"); the correct ceiled total is `1100` (fits by 4, not 5). One-bit proposal-framing difference, no decision rests on it — annotation optional, listed for completeness.
- Stage-0-side numerical quotations (`decision-log.md:5130,5136`, `NOW.md:158-159`, `SESSION_AUDIT.md:25,36`, `NEXT-STEP-OPTIONS/PROPOSAL.md:136`) are verified-standing per §16.2 and need no note. `docs/NOW.md:162` still describes the joint packet as awaiting Pre-EXECUTE; its staleness post-execution is flagged for the normal NOW.md maintenance path, not corrected here.
