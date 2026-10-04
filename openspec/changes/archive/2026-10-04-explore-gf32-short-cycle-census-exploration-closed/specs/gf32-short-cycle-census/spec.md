## ADDED Requirements

### Requirement: Bounded simple-cycle inventory
The EXPLORE runner SHALL enumerate canonical simple degree2 cycles of
variablelength2..6 on fixed accepted supports and record GFproducts/unit
witnesses for both accepted matrices without decoder execution.

#### Scenario: Complete inventory
- WHEN all six inventories complete within frozencaps
- THEN pergraph/perlength counts and exact unit witnesses SHALL establish
  only short-cycle availability,not distance or decoder performance.

#### Scenario: STOP or partial inventory
- WHEN cap/resource/reconstruction gates stop
- THEN partialrows SHALL remain without retry and fullbatch totals unknown.

#### Scenario: Authority
- WHEN predecessoraccepted and independentimplementationPASS/maindispatch
- THEN ongoing user authorization SHALL permit only this frozen decoder-free
  run,with no implicitnextdecoder or rangeextension.
