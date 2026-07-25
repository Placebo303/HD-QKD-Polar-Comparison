# Decision Log

Durable decisions and rejected alternatives for the HD-QKD_Polar_Comparison project.

---

## Template

```
### YYYY-MM-DD: <Title>

**Decision**: <What was decided>

**Context**: <Why this was needed>

**Alternatives considered**:
- Alternative A: <Why rejected>
- Alternative B: <Why rejected>

**Consequences**: <What this means going forward>
```

---

## Decisions

### 2025-06-01: Non-invasive comparison layer architecture

**Decision**: The comparison benchmark is built as an outer wrapper (`comparison_bench/`) that reads the original Polar pipeline outputs without modifying them. The original `src/`, `experiments/`, and `tools/` directories are frozen baselines.

**Context**: We needed to compare multiple IR methods without risking regressions in the proven Polar pipeline.

**Alternatives considered**:
- Fork the repo and modify in-place: rejected because it would create maintenance burden and risk breaking the original workflow.
- Build a separate, fully independent project: rejected because we need to directly import/read Polar results.

**Consequences**: 
- `comparison_bench/` is the only mutable area for new IR comparison work.
- The `polar_existing` bridge in `comparison_bench/src/comparison_bench/io/polar_existing_bridge.py` is the sole interface for reading original Polar outputs.

---

### 2025-06-15: OpenSpec workflow initialization

**Decision**: Adopt OpenSpec as the change management workflow for all substantial feature work.

**Context**: Multi-agent workflow requires clear proposal → design → tasks → implement → review → archive pipeline.

**Alternatives considered**:
- GitHub Issues only: rejected because no structured design/spec/task linkage.
- Ad-hoc task lists: rejected because no durable record of decisions and spec changes.

**Consequences**:
- All substantial changes must go through `openspec/` workflow.
- `AGENTS.md` is authoritative for agent rules.
- `docs/decision-log.md` (this file) records durable decisions.

---

### 2026-06-15: Real IR success before final method selection

**Decision**: Prioritize verified real information reconciliation success on high-dimensional arrival-time QKD frames before final error-correction method selection or efficiency comparison.

**Context**: The existing Polar line has produced results, while most non-Polar comparison methods still need stable real-data verification success. Comparing `beta_eff_empirical`, leakage, or runtime before methods actually reconcile real frames risks optimizing a metric artifact instead of solving the IR problem.

**Alternatives considered**:
- Immediate final method selection: rejected because non-Polar methods have not yet established enough verified real-data success.
- Continue broad parameter sweeps first: rejected because broad sweeps are less useful until success/failure criteria and representative real-frame validation are explicit.
- Treat synthetic success as sufficient: rejected because the first-principles target is real high-dimensional arrival-time QKD reconciliation.

**Consequences**:
- The next active OpenSpec change is `real-ir-success-first`.
- Cascade-lite is treated as the first non-Polar real-success candidate, with simplified-Cascade caveats.
- Layered LDPC is treated as an executable failure-diagnosis target before being considered a final candidate.
- qLDPC remains a reference-grade q-ary feasibility direction until stronger evidence exists.
- Final method selection is deferred until verified real-data success and leakage accounting are established.
