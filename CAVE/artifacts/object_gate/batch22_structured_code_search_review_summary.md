# Batch 22 Structured Code Search Review Summary

Date: 2026-04-01

Source:

- `artifacts/object_gate/batch22_structured_code_search_candidates.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch22_v4_summary.md`

## Accepted

- `code_structured_search_3101`
  - accepted because the structured checker leaves exactly one passing local
    repair, namely the keep condition `n > 0 and n % 2 == 0`
- `code_structured_search_3102`
  - accepted as another exact local-repair case with a different arithmetic
    predicate and the same gold-only repair geometry
- `code_structured_search_3103`
  - accepted because the revise condition fails the structured tests while all
    listed non-gold local repairs also fail

## Rejected

- none

## Outcome

- reviewed pairs: `3`
- accepted pairs: `3`
- rejected pairs: `0`
- acceptance rate: `100.0 percent`

Decision:

`Use this batch as the first structured-code reviewed slice.`

Interpretation:

- the matching structured-code path is viable under search construction
- exact execution is strong enough to support deterministic `judge_v4`
  pre-screening for this sub-object
- this batch alone is not yet a panel, but it is enough to justify expansion
