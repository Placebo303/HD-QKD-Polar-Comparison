# P4 FEAS Construct Runner — Proposal

- Change name: `p4-feas-construct-runner`
- Scope of THIS document: **proposal only** — no `design.md`, no `tasks.md`, no `specs/` delta in this change, no edit to `openspec/specs/`, no code/test/config change, no execution, no commit/push.
- Affected specs: **None** (no spec requirement is added, amended, or retired by this change; `openspec/specs/*` stays untouched).
- Track: **— (no track gate: docs-only behavioral record, no execution)** per `AGENTS.md` §1.2 applicability matrix ("Documentation-only changes" → no track gate). This change authorizes no execution, consumes no budget, and makes no FER/SKR/route/qualification/publication claim.
- Subject file (recorded, NOT modified by this change): `comparison_bench/src/comparison_bench/cli/p4_feas_construct.py` (873 lines, as re-measured after the 22:05 revision; `wc -l`).
- Frozen context: `docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_PACKET.md` (FROZEN, NOT GRANTED; §10(d) authorization block BLANK) + `P4_FEAS_PROMPT.md`. Branch `formal-ir-v72p1-addendum-clean`, baseline `8e9c8526`.

## Why (what this change records)

- Review finding **M4 (MAJOR)**: `p4_feas_construct.py` adds production-execution-entrypoint behavior (a runnable CLI with authorization flags, refusal codes, and output roots) with **no covering OpenSpec change**. `AGENTS.md` §3 requires that a change to behavior/architecture/workflow rules go through an OpenSpec change **first**; the runner was implemented under packet §10(b)'s "implementation itself has no track gate" clause, so the two rules were never reconciled in a durable document. This change is that missing behavior record — retroactive documentation of already-implemented behavior, not a new behavior grant.

## Runner purpose (recorded as implemented)

- **Dual-flag fail-closed**: production construction runs only behind BOTH `--execute-real` AND `--execution-authorized` plus every frozen literal echo (n, m, trials, λ, ρ rate, seed line, both uuid8 roots); bare or partial invocation refuses rc=2 **before** any root, log, or write.
- **F1–F6 implemented literally** (packet §2): exactly two arms in frozen order `P4F-R1`(2026092001) → `P4F-R2`(2026092011), reported separately (cross-instance pooling forbidden); one PEG matrix per arm (n=2048 GF(32), m=416, λ={2:1}, ρ=`make_rho(0.796875)`, trials=20, `family="peg-irregular"` + three-shift-cyclic refusal); fresh-object/no-block-seed semantics; **no channel read path** (zero `.ttbin` / `gamma` import or literal); **zero decode** (no decoder entrypoint imported or reachable; module defines no callable starting with `decode`).
- **Pins gates**: `fc=0` AND full `rank==416` AND twice-identical AND base `rank(rows[0,400))==400` REQUIRED, any miss ⇒ STOP-BLOCKED (rc=2); girth/sockets/parity recorded-not-gated.
- **`decode_calls=0`**: asserted and recorded on every output row/record; any decode-shaped output is out of contract.
- **Output confinement**: writes ONLY under fresh additive `workspace/P4_FEAS/<arm>_<uuid8>/` (uuid8 passed explicitly, frozen Pre-EXECUTE — no generation path in the module) plus the one append-only exploration log; `results/` and `comparison_bench/outputs_comparison/` are refused; existing evidence roots untouched.
- The core `execute()` requires explicit `construct_fn`/`rank_fn` injection — no default production wiring (AGENTS §10.1 clause 8).

## Relationship to P4_FEAS_PACKET §10(b) (both standards preserved)

- **Both documents coexist; neither supersedes the other.**
  - The **packet remains the execution authority**: §10(b) readiness + §10(c) Pre-EXECUTE Q0–Q6 + §10(d) signature are the only path to any construction execution; §10(d) is BLANK ⇒ unauthorized. This change grants no execution, no budget, no branch switch, no commit/push.
  - This **change is the behavior record**: it satisfies `AGENTS.md` §3 ("behavior change ⇒ OpenSpec change first") for the runner's already-implemented CLI/refusal/output behavior, so the behavior is citable at OpenSpec level instead of only from a module docstring.
- **Same-batch dual-standard resolution (同批双标准消解)**: packet §10(b) says "implementation itself has no track gate" (AGENTS §1.2 implementation-only matrix) while AGENTS §3 says behavior changes need an OpenSpec change first. Both hold without conflict: implementation carried **no track gate** (nothing to gate — zero execution at implementation time), and **does** require this OpenSpec **behavior record** (no spec delta, no tasks). Track gate for any actual run stays where the packet put it: the first synthetic execution, after §10(d) grant.

## M2 interface incompatibility — PENDING ADJUDICATION (recorded, not selected)

- Review finding **M2 (MAJOR, unresolved)**: the operator prompt command template and the implemented runner disagree on the invocation interface. **Recorded here verbatim; NO option is chosen, NO runner name is frozen by this change:**
  - Prompt template (`P4_FEAS_PROMPT.md` §1 item 6): **per-arm** form — `--arm P4F-R1 --n 2048 --m 416 --instance 2026092001 --trials 20 --root workspace/P4_FEAS/<R1_uuid8>` (R2 swaps `--arm/--instance/--root`), runner path still the placeholder `<P4FEAS_RUNNER [TO BE FROZEN]>`.
  - Implemented runner (`p4_feas_construct.py` argparse): **dual-arm single-invocation** form — `--seeds` (frozen lineage literal) + `--r1-uuid8` + `--r2-uuid8` + `--root`/`--n`/`--m`/`--trials`/`--lambda-edge`/`--rho-rate`; no `--arm`/`--instance` flags exist.
  - **Runner-name backfill is also pending**: whichever side wins, the `<P4FEAS_RUNNER [TO BE FROZEN]>` placeholder must be backfilled at Pre-EXECUTE freeze time by the main thread — not by this change.
- Adjudication (align prompt, align runner, or accept a documented translation step in the Pre-EXECUTE record) belongs to the **main thread at Pre-EXECUTE / packet amendment time**. This change only makes the incompatibility durable and visible; choosing an interface would be a requirements decision outside a docs-only record (AGENTS §4: coder must not redefine requirements).

## Non-goals

- No edit to `openspec/specs/*`, `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, the P4 packet/prompt, `docs/decision-log.md`, `docs/troubleshooting.md`, or any file under `src/`, `experiments/`, `tools/`, `comparison_bench/`, `results/`, `workspace/`.
- No design, tasks, or spec-delta artifacts in this change directory at this stage (added only if a later scope — e.g. the M2 adjudication — needs them, via an explicit main-thread decision).
- No execution of the runner or of any test beyond what a reviewer already ran; no authorization, budget, FER/SKR, route, or publication claim.

## Affected specs

- None.
