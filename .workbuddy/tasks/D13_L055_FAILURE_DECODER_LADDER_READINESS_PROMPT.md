# Copyable prompt — D13 L055 failure decoder ladder readiness

Work in `D:\Code\HD-QKD_Polar_Comparison` and follow `AGENTS.md` plus
`.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md`.

Accept D12 L055 selection. Implement D1301--D1310 as a thin diagnostic over
exactly the 56 frozen L055 failures: strict RL90 replay, then RL360,
RL360+damping0.7 and flooding360. Reuse existing D12 reconstruction and accepted
D7-X3 decoder binders; do not add decoder implementations or tune arms.

This authorizes OpenSpec/code/docs, focused fake tests and PLAN_ONLY work only.
It does not authorize decoder execution, output-root creation, forward/L2,
D7-H, real data, commit or push. Use independent reviewer-go with actual
artifact access and trust its traceable evidence.

Return only at the ready terminal or first STOP condition with the packet
evidence contract. Execution requires a later explicit user grant.
