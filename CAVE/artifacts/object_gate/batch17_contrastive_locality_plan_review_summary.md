# Batch 17 Contrastive Locality Plan Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch17_v4_summary.md`

## Accepted

- none

## Rejected

- `plan_contrastive_locality_1801_0`
  - rejected because the checker text is still ambiguous about whether
    "frosting step" means making frosting or applying frosting
  - this leaves a nearby non-gold repair plausibly checker-valid, so the pair
    does not realize contrastive locality cleanly
- `plan_contrastive_locality_1802_1`
  - rejected because the checker under-specifies the relation between preparing
    frosting and baking layers
  - multiple valid repairs remain, so the gold repair is not uniquely selected
- `plan_contrastive_locality_1803_2`
  - rejected because the checker again permits multiple nearby valid repairs
  - the pair is cleaner than older plan batches, but still does not make only
    the gold local repair checker-correct

## Outcome

- reviewed pairs: `3`
- accepted pairs: `0`
- rejected pairs: `3`
- acceptance rate: `0.0 percent`

Decision:

`Do not use this batch for family bootstrap.`

Interpretation:

- the new plan-specific prompt override improved formatting and eliminated false
  revise claims in this batch
- but it did not solve the deeper problem: plan checkers are still too weak or
  too ambiguous to enforce gold-only local repair geometry
- this is a cleaner negative result than batch16, not a breakthrough
