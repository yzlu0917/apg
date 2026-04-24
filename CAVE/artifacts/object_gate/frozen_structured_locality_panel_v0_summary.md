# Frozen Structured Locality Panel v0 Summary

Date: 2026-04-01

Source panels:

- `artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl`
- `artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl`

Frozen panel:

- `artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl`

## Composition

- records: `32`
- pairs: `16`
- domains: `plan` and `code`
- construction path: `search_constructed` only
- checker schemas:
  - `plan_local_repair_v1`
  - `code_local_repair_v1`

## Reviewed status

- reviewed pairs: `16`
- accepted pairs: `16`
- rejected pairs: `0`
- reviewed acceptance rate: `100.0 percent`

## Interpretation

- `structured_locality` now has a clean cross-domain frozen object panel
- this is enough for a fresh Object-level `GO` on the spin-out branch
- this result should not be merged back into the old `contrastive_locality`
  aggregate as if they were one unchanged family
