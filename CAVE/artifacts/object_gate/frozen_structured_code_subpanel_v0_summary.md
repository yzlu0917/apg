# Frozen Structured Code Subpanel v0 Summary

Date: 2026-04-01

Source slices:

- `artifacts/object_gate/batch22_structured_code_search_candidates.jsonl`
- `artifacts/object_gate/batch23_structured_code_search_candidates.jsonl`

Frozen panel:

- `artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl`

## Composition

- pairs: `8`
- domain: `code`
- construction path: `search_constructed`
- checker schema: `code_local_repair_v1`

Pair IDs:

- `code_structured_search_3101`
- `code_structured_search_3102`
- `code_structured_search_3103`
- `code_structured_search_3201`
- `code_structured_search_3202`
- `code_structured_search_3203`
- `code_structured_search_3204`
- `code_structured_search_3205`

## Acceptance status

- reviewed pairs: `8`
- accepted pairs: `8`
- rejected pairs: `0`
- reviewed acceptance rate: `100.0 percent`

## Interpretation

- the structured-code sub-object is now panel-viable
- `judge_v4` can pre-screen this sub-object deterministically via `auto_accept`
  because the checker explicitly enumerates nearby repair candidates and the
  execution trace proves gold-only repair uniqueness
- this supports an object-level positive claim for the structured-code
  sub-object only
- this does not imply whole-family `contrastive_locality` Object `GO`
