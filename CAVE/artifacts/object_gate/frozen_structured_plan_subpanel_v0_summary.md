# Frozen Structured Plan Subpanel V0 Summary

Date: 2026-03-31

## Contents

This subpanel freezes the accepted structured-plan search path from:

- `batch20_structured_plan_search`
- `batch21_structured_plan_search`

Artifact:

- `artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl`

## Size

- records: `16`
- pairs: `8`
- domain: `plan` only

Accepted pair ids:

- `plan_structured_search_2101`
- `plan_structured_search_2102`
- `plan_structured_search_2103`
- `plan_structured_search_2201`
- `plan_structured_search_2202`
- `plan_structured_search_2203`
- `plan_structured_search_2204`
- `plan_structured_search_2205`

## Interpretation

- this is the first frozen reviewed subpanel in the new
  `contrastive_locality` line that is stable under validator, judge, and human
  review
- it supports an object-level claim for the structured-plan sub-object only
- it does not by itself establish a new Object `GO` for the whole
  `contrastive_locality` family, because the broader family still includes weak
  code and direct-generation paths
