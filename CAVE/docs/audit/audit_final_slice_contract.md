# Audit Final Slice Contract

Date: 2026-03-31

## Frozen final slice

The first held-out Audit-gate final slice is:

- `artifacts/audit/audit_final_v0.jsonl`

The checker-repaired versioned final slice is:

- `artifacts/audit/audit_final_v1.jsonl`

Source:

- reviewed acceptance from `artifacts/object_gate/batch10_api_harder_candidates.jsonl`
- review record in `artifacts/object_gate/batch10_api_review_summary.md`
- versioned checker note in `artifacts/audit/audit_final_v1_change_note.md`

## Boundary

- This slice is held out from the earlier dev-slice protocol shaping work.
- Its matched shuffles must be sourced from the frozen dev source bank rather
  than from itself.
- `audit_final_v0` is the frozen diagnosis anchor.
- `audit_final_v1` is the first versioned checker-repair slice.
- It may not be silently edited after baseline runs begin.

## Comparability rule

If the final slice must change, the update must:

- receive a new version id,
- explain why `audit_final_v0` was insufficient,
- state which conclusions are no longer directly comparable.
