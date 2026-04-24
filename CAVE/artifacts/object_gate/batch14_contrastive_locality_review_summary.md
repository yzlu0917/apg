# Batch 14 Contrastive Locality Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`

## Rejected

- `code_1501_0`
  - rejected because the natural-language spec asks for the maximum product of
    any two odd numbers, but the keep solution only multiplies the two largest
    odd values after descending sort
  - the unit tests do not cover mixed-sign cases such as large-magnitude
    negative odds, so the checker does not rule out nearby wrong algorithms
- `plan_1501_0`
  - rejected because the revise trace `A -> D -> B -> C` actually satisfies the
    stated constraints `A before B; B before C; D after A; D before C`
  - this is a semantic validity failure: the pair claims a local violation that
    does not exist under the checker

## Outcome

- reviewed pairs: `2`
- accepted pairs: `0`
- rejected pairs: `2`
- acceptance rate: `0.0 percent`

Decision:

`Do not use this batch for family bootstrap.`

Interpretation:

- stronger formatting and non-empty repairs are not enough; semantic drift is
  still the main blocker
- current failure modes are checker undercoverage in code and false violation
  claims in plan
