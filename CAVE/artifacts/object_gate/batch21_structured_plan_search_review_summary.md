# Batch 21 Structured Plan Search Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch21_v4_summary.md`

## Accepted

- `plan_structured_search_2201`
  - accepted because the structured checker is exact, the revise order is
    invalid, and the unique valid adjacent-swap repair is the keep order
- `plan_structured_search_2202`
  - accepted as another clean local-repair instance with a different edge set
    and keep order
- `plan_structured_search_2203`
  - accepted because it preserves the same structured geometry while varying
    both edge pattern and keep order
- `plan_structured_search_2204`
  - accepted as a valid structured local-repair case with a different violated
    adjacent pair
- `plan_structured_search_2205`
  - accepted because it remains exact-checkable and locally repairable with a
    unique gold repair

## Rejected

- none

## Outcome

- reviewed pairs: `5`
- accepted pairs: `5`
- rejected pairs: `0`
- acceptance rate: `100.0 percent`

Decision:

`Use this batch to expand the structured-plan reviewed subpanel.`

Interpretation:

- the search-based structured-plan path is no longer a one-off success
- it can produce multiple accepted pairs with better local diversity than
  `batch20`
- this is enough to freeze a first structured-plan reviewed subpanel, but still
  not enough to elevate the whole `contrastive_locality` family to Object `GO`
