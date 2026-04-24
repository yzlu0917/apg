# Batch 15 Contrastive Locality Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`

## Rejected

- `code_1601_0`
  - rejected because the checker reference itself is inconsistent with the
    stated task: for `n = 20`, the listed valid numbers are eight values, but
    the asserted target is `9`
  - this breaks the one-intended-answer requirement even though the local bug
    shape looks closer to the intended family
- `plan_1601_harder_contrastive`
  - rejected because the constraints collapse to a unique linear order
    `A -> B -> C -> D`, so the example does not realize the intended
    contrastive-locality geometry
  - verifier content is unlikely to be necessary when the task is effectively a
    single-chain precedence problem

## Outcome

- reviewed pairs: `2`
- accepted pairs: `0`
- rejected pairs: `2`
- acceptance rate: `0.0 percent`

Decision:

`Do not use this batch for family bootstrap.`

Interpretation:

- prompt tightening improved syntactic validity but not semantic reliability
- the current generator still drifts into checker inconsistencies and trivial
  plan structures
