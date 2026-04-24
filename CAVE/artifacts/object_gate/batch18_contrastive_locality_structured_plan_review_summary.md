# Batch 18 Structured Plan Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch18_v4_summary.md`

## Accepted

- none

## Rejected

- `plan_contrastive_locality_1901_0`
  - rejected because the revise order is actually valid under the structured
    edges, and its adjacent-swap neighborhood contains two valid repairs rather
    than exactly one
- `plan_contrastive_locality_1902_1`
  - rejected because the revise order is also valid under the structured edges,
    even though the unique adjacent-swap repair equals keep
- `plan_contrastive_locality_2_1903`
  - rejected for the same reason as `1902_1`: the object geometry is almost
    right, but the revise order is not actually invalid

## Outcome

- reviewed pairs: `3`
- accepted pairs: `0`
- rejected pairs: `3`
- acceptance rate: `0.0 percent`

Decision:

`Do not use this batch for family bootstrap.`

Interpretation:

- the structured-plan object is easier to diagnose than the prose-plan object
- the remaining error is now crisp: the model keeps generating revise orders
  that satisfy the structured checker
- this justified moving the same semantic test into generation-time validation
