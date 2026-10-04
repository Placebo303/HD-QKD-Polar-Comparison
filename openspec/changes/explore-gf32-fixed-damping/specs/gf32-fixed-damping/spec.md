## ADDED Requirements

### Requirement: Explicit fixed-damping comparison
The EXPLORE runner SHALL comparedamping1 and.5 on thesameaccepteddeep
matrix/prior/source/syndrome/schedulemax90,usingexplicitarmdecoders and
192newpaired samples,withoutchangingolddecoder orselectingalpha byoutcome.

#### Scenario: Complete paired result
- WHEN 384 calls complete with frozen admissions
- THEN exact+syndrome/wrongisolatedcounts,iterations,pairedstates,260bits
  perattempt andactualtimingRSS SHALL followthefrozen screen/ceiling.

#### Scenario: STOP or partial result
- WHEN admission/resource/exception gates stop
- THEN attempts SHALL remain, no scientific retry and comparisons unknown.

#### Scenario: Authority
- WHEN independent review PASS and main dispatch occur
- THEN ongoing grant SHALL cover this bounded frozen run only, no realdata
  promotionorimplicititeration/schedulechange.
