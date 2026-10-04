# Minimal design and frozen operator packet

A1: Read V64's 24 final records (8/source), checking unique block IDs and the realistic assumptions required for reconstruction: exact decomposition, accepted=syndrome AND full tag, undetected=accepted AND NOT exact, terminal stage/call/leak consistency. Early terminal stages must be accepted. Never equate acceptance with correctness.

A2: The execution script continues to the next stage only after failed full verification. For cap k and observed terminal stage j, spent stage is min(j,k). Verified exact recovery is observable iff j<=k AND accepted_full AND exact_full. Accepted-but-wrong is separate. Unreached final outcomes count as not verified recovered; their earlier exactness and residual error counts are UNKNOWN, not inferred failures of exact decoding.

A3: For each cap overall and per source, report attempted blocks, verified exact, unverified, undetected, calls=2+min(j,k), and disclosed bits=80+5*m_source+40*min(j,k)+64, where m_source=(184,190,192). This is the existing single-tag accounting convention, not a new security proof. Include disclosure spent on rejected blocks. Do not infer runtime from call counts, beta, or secret-key yield. Stage gains are paired policy gains, confounding extra rows with extra decoder attempts; not a pure graph or iteration ablation.

A4: Final observed failures: source/block/frame IDs, errors_u1/errors_u2, syndromes, tags, terminal stage. Report source-specific denominators; do not pool V63, invalid V65 evidence, or other sessions. No causal claim from two failures; no temporal clustering claim without timestamps and predeclared reference distribution.

A5: A stdlib-only script with --self-check uses a small constructed three-stage example including an undetected outcome. It must verify truncation arithmetic and separation of wrong acceptance, then analyze actual inputs without importing project decoder modules. Default input paths resolve relative to repository location; optional --records and --summary permit explicit inputs. No output files are written.

A6: Independent reviewer checks code, numerical output, original stop semantics and claim boundaries. Main thread owns requirements and acceptance. Worker returns complete with A1-A5 evidence or a concrete blocker. Memory triage is read-only and does not update long-term memory without user request.

Next experiments should use fresh CAL development blocks, identical block IDs across arms and fixed budgets; historical V64 blocks cannot become tuning/confirmation data. Choose a single factor before fresh validation. Formal decoder work still requires an accepted packet, exact-SHA Pre-EXECUTE review and explicit authorization under AGENTS.md.

## Occam follow-up priority (proposal only)

1. Do not repeat the channel-table/circulant/parametric comparison. Existing `v70r1_table.csv` records a decoder-free result candidate: M2 versus M1 CE improvements are only about 0.0016-0.0022 bits/symbol, whereas M0 to M1 improves about 0.335-0.364. This supports reusing the simpler model candidate; it does not establish FER, achieved efficiency, or a cause of V64 failures. Source labels across V64 and V70R1 do not imply matched sessions or comparable FER.
2. First fresh decoder ablation candidate: V72 joint local-factor updates versus fixed bit-marginal messages derived from the SAME frozen symbol prior. Freeze mother, blocks, checkpoints, maximum iterations, clipping and verification. In the ablated arm replace factor messages by their zero-incoming-message marginals; do not add a second prior. Measure paired verified exact recovery, undetected outcomes, disclosure, wall time and final residuals. This distinguishes the value of iterative within-symbol dependence handling from an independent-bit approximation. It is a successor change, not permission to alter the currently frozen adapter.
3. Only if a resource question remains after (2), compare warm versus cold checkpoint initialization, keeping prior, mother and budgets fixed. Do not combine this with a prior/model change. Stop after the frozen matrix; choose any successor using CAL only, then separately freeze one fresh VAL confirmation.

No numerical win threshold or real-data execution packet is invented here: those require the chosen baseline's implementation acceptance, matching session registry and measured runtime budget. This turn completes the identifiable retrospective ablation and leaves these decoder experiments unexecuted.
