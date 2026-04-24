# Audit Dev Slice Contract

Date: 2026-03-31

## Frozen dev slice

The first Audit-gate dev slice is:

- `artifacts/audit/audit_dev_v0.jsonl`

Source:

- copied from `artifacts/object_gate/frozen_reviewed_panel_v0.2.jsonl`

## Boundary

- This slice is frozen before any baseline comparison.
- It may be used for protocol debugging and descriptive audit checks.
- It may not be silently edited after baseline runs begin.

## Expansion rule

If the slice must change, the update must:

- receive a new version id,
- explain why the old slice was insufficient,
- state which conclusions are no longer comparable.
