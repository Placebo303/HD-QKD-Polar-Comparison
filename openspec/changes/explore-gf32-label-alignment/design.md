# Design

Use the existing GF32 field, CONTROL PEG builder and row-layered decoder.
One numerical module implements PMF/score/column scaling; one CLI implements
pilot then paired holdout and the compact four-artifact root. Requirements
and acceptance items are frozen in the linked packet; operator must STOP on
ambiguity. Scientific decoder binding is explicit; fake tests inject it.
Keep existing modules unchanged. One batch-end independent review suffices.
