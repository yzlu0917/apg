# Structured Locality Audit Dev Slice Contract

Date: 2026-04-01

## Frozen dev slice

The first Audit-gate dev slice for the `structured_locality` branch is:

- `artifacts/audit/audit_dev_v3.jsonl`

Source:

- copied from `artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl`

## Boundary

- this slice belongs to the `structured_locality` spin-out branch, not the old
  mixed `contrastive_locality` branch
- it is frozen before any `structured_locality` baseline comparison
- it may be used for protocol debugging and descriptive audit checks
- it may not be silently edited after baseline runs begin

## Comparability

- results on `audit_dev_v3` are not directly comparable to `audit_dev_v2`
  because the underlying object family is different
- `audit_dev_v3` excludes the old weak free-generation samples on purpose
