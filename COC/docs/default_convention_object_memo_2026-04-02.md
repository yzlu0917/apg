# Default-Convention Boundary Object Memo 2026-04-02

## Current Object Claim

The strongest current object claim is no longer the broad `clarify_required` family. The narrower claim is:

> Strong judges can still systematically over-reward direct answers that rely on an unstated but culturally common default convention, even when the missing convention changes the concrete output.

This working object is currently best described as a `default-convention boundary` under the broader `clarify_required` umbrella.

## Best Current Evidence

The most informative slices so far are:

1. `v4 clarify-hardcore`
   - `source_unit_missing + date_convention_missing`
   - balanced `pair-strict = 0.25`
2. `v6 date-convention`
   - compact short-date ISO recipe
   - balanced `pair-strict = 0.0`
3. `v7 source-unit`
   - fresh source-unit-only replication
   - balanced `pair-strict = 0.25`
4. `v8 date-convention-compact`
   - fresh compact date-only replication
   - balanced `pair-strict = 0.0`

Together these show that the object is not resting on one accidental recipe.

## What Is Stable vs Recipe-Sensitive

### Stable

- `source_unit_missing`
  - remains hard in mixed and source-only slices
  - currently the most stable hard subtype

### Recipe-Sensitive But Real

- `date_convention_missing`
  - weaker in `v5` mixed slice
  - strongly hard again in `v6` compact short-date recipe
  - cleanly replicated again in `v8`

This suggests the object is real, and that the date-side recipe should stay narrow and compact.

## Paper-Facing Read

If we need one short paper-facing sentence right now, the safest version is:

> We identify a narrow frontier-hard evaluator boundary in which the judge rewards answers that silently adopt common source-unit or date-format defaults instead of rewarding answers that surface the missing convention.

## Decision

- keep `default-convention boundary` as the current main strong-judge object
- treat `source_unit_missing` as the anchor subtype
- treat compact `date_convention_missing` as a second validated subtype
- do not widen back to broad `clarify_required` language in the main claim
