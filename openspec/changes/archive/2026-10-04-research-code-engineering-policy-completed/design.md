# Design: Research Code Engineering Policy

## Decision: Performance algorithm research is the strict first principle

All project planning and review SHALL use this priority order:

1. formulate a scientifically plausible correction-method hypothesis;
2. implement the smallest algorithm capable of testing it;
3. measure correction success, leakage, runtime/resource cost, and net-key
   implications at the appropriate synthetic/real boundary;
4. retain only the minimum reproducibility and lifecycle evidence needed to
   trust that measurement;
5. improve packaging, generalized infrastructure, verifier depth, or defensive
   robustness only when explicitly requested or required by a concrete
   scientific failure mode.

Reviews SHALL distinguish algorithm/scientific blockers from engineering
improvements. Engineering is non-blocking unless it can change the numerical
result, scientific attribution, execution authorization, or existing data.

## Decision: Placement as §5.7

The policy is placed as a new subsection `### 5.7 Research Code Engineering
Policy` under the existing `## 5. Project-Specific Rules` section.

**Rationale**: The policy describes how code in *this specific repository*
should be engineered — it is inherently a project-specific rule. Placing it
as a subsection of §5 avoids renumbering sections §6 through §10, minimizing
diff surface and eliminating the risk of broken cross-references.

**Rejected**: Inserting as a new top-level §6 would require renumbering
§6→§7, §7→§8, §8→§9, §9→§10, §10→§11, §10.1→§11.1 — touching every
subsequent section header. The policy does not warrant that level of
structural disruption.

## File Modification List

| File | Action | Description |
|------|--------|-------------|
| `AGENTS.md` | Edit | Insert `### 5.7` subsection between existing `### 5.6` and the `---` separator before `## 6` |
| `openspec/project.md` | Edit | Add the strict first-principle objective and priority rule |
| `README.md` | Edit | Surface the algorithm-performance-first identity |
| project decision/memory/roadmap docs | Edit | Record the durable decision and supersession rule |

No algorithm or output files are modified by this policy change.

## Structural Checkpoints

After insertion, verify:

1. `### 5.7` immediately follows `### 5.6 Commands That Must Not Be Run By Default`
2. `## 6. OpenSpec Workflow` remains at the same line offset (+ the new subsection length)
3. `---` horizontal rule separates §5.7 from §6 (consistent with other section separators)
4. No duplicate `5.7` or orphaned numbering
5. All bullet lists within §5.7 use consistent `-` prefix (matching existing style)
6. File encoding is UTF-8 (no BOM corruption)
