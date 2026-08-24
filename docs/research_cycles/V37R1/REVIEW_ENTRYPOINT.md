# Review Entrypoint: V37R1 (V37-P1-PLAN)

**Cycle ID**: V37R1  
**Lifecycle State**: PLAN_CANDIDATE  
**Review Kind**: PLAN  
**Repository**: `Placebo303/HD-QKD-Polar-pipeline`  
**Branch**: `formal-ir-mainline`  
**Base SHA**: `a258c5a7549f33f43a32b193b134f1ca0df15aea`  
**Execution Authorization**: NOT_GRANTED  

---

## Documents for Review

1. **Scientific Plan Document**:
   - `docs/nbldpc-v37-p1-plan.md`
2. **OpenSpec Candidate Change**:
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/proposal.md`
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/design.md`
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/tasks.md`
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/specs/formal-ir-v37/spec.md`
3. **P0 Feasibility Analyzer (Accepted Baseline)**:
   - `comparison_bench/src/comparison_bench/formal_ir/v37_degree_feasibility.py`
   - `docs/nbldpc-v37-p0-degree-feasibility.md`

---

## Core Review Items

- [ ] Does the plan enforce the accepted $N_2 \le 183$ finite-length feasibility constraint via exact integer apportionment?
- [ ] Is the candidate grid over degrees $\{2, 3, 4, 5\}$ explicit and pre-registered (259 candidates with $N_2 \le 183, d_{c,\max} \le 20$)?
- [ ] Are DE comparison settings strictly matched (empirical-P law, $N=4000, I=60$, identical 3 seeds/source for baseline, control, and candidates)?
- [ ] Is the primary ranking metric based on non-saturated early-stage trajectories ($\text{AUT}_{30}$) with per-source advance requirements ($\ge 5\%$ on 1M, 1.5M, 2M)?
- [ ] Is the V36 candidate explicitly isolated as an exploratory positive control tagged `finite_inadmissible=True`?
- [ ] Is P1 strictly DE-only (no PEG, Tanner graphs, decoders, or FER runs)?
