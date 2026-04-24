# Contrastive Locality Judge V3.2 Assessment

Date: 2026-03-31

## Headline

`judge_v3.2` is the first version where schedule-style plan checking materially
improves the pre-screen.

Compared with `v3.1`:

- `batch11` schedule-style plan pair is now recovered as `accept`
- `batch12` schedule-style plan pair is still rejected, but now with explicit
  schedule evidence rather than an order-parser artifact
- total accepts move from `1` to `2`

## Current result shape

- judged pairs: `10`
- accepts: `2`
- rejects: `8`
- auto rejects: `4`
- model with program findings: `6`

Accepted pairs:

- `plan_contrastive_locality_0` from batch11
- `code_1501_0`

## What improved

- schedule-style pairs now carry:
  - parsed task durations
  - inferred start times
  - parsed precedence edges
  - computed minimal makespan
- this lets the pre-screen reject schedule traces that are impossible or
  non-minimal under the written constraints
- it also prevents the old false artifact where long natural-language schedule
  traces were mistaken for simple total-order strings

## Remaining limitations

- code acceptance is still unstable relative to human review
- the judge still rejects `code_contrastive_locality_0` and accepts `code_1501_0`
  whereas prior human review preferred the opposite
- schedule parsing is still narrow and only covers the specific prose patterns
  already present in current batches

## Operational conclusion

`judge_v3.2` is the best pre-screen so far for this branch.

Recommended usage:

- keep it as the default veto pre-screen for new `contrastive_locality` batches
- continue to require human review for every accepted pair
- if this family continues, the next leverage point is stronger execution-backed
  code semantics, not more prompt patching
