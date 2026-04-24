# Batch 23 Structured Code Search Review Summary

Date: 2026-04-01

Source:

- `artifacts/object_gate/batch23_structured_code_search_candidates.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch23_v4_summary.md`

## Accepted

- `code_structured_search_3201`
  - accepted as a clean structured local-repair case for counting positive even
    numbers
- `code_structured_search_3202`
  - accepted as a clean structured local-repair case for counting positive
    multiples of three
- `code_structured_search_3203`
  - accepted because the negative-odd counting task still leaves exactly one
    checker-correct local repair
- `code_structured_search_3204`
  - accepted as a slightly richer case where the structured checker needs two
    assertions to eliminate all nearby wrong repairs
- `code_structured_search_3205`
  - accepted because the sum-style task remains exact-checkable and the gold
    condition is the only passing local repair

## Rejected

- none

## Outcome

- reviewed pairs: `5`
- accepted pairs: `5`
- rejected pairs: `0`
- acceptance rate: `100.0 percent`

Decision:

`Use this batch to expand and freeze the structured-code reviewed subpanel.`

Interpretation:

- the structured-code path is no longer a one-off success
- search construction plus exact checker analysis can sustain a small reviewed
  panel
- this is strong enough to freeze a first structured-code subpanel, but still
  not enough to elevate the whole `contrastive_locality` family to Object `GO`
