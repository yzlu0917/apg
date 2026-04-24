# Batch 10 API Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch10_api_harder_candidates.jsonl`

Purpose:

- review a held-out API-generated harder batch for final-slice Audit use
- keep this batch separate from the existing dev slice and dev source bank

## Accepted

- `sym_harder_1101_0`
  - clean late-step arithmetic error with one shared intended answer
  - repair is local and checker-backed
- `sym_1102_harder_1`
  - local misread-plus-addition error remains confined to the final step
  - no format shortcut dominates the action label
- `code_pair_0`
  - classic `or` versus `and` local bug with strong unit-test grounding
  - suitable for same-domain shuffle against the dev source bank
- `code_1102_harder_1`
  - local else-branch copy-paste bug that fails the tests
  - repair is operationally clear despite compact suffix wording
- `plan_0_harder_1101`
  - explicit dependency violation with a concrete corrected continuation
  - checker text is strong enough to certify the violation
- `plan_1102_harder_1`
  - local order swap violating `B before C`
  - corrected suffix restores both order and total-time statement

## Rejected

- none

## Outcome

- reviewed pairs: `6`
- accepted pairs: `6`
- acceptance rate: `100.0 percent`
- viable domains after review: `3`

Decision:

`Freeze this batch as the first held-out final audit slice.`

Interpretation:

- this batch is strong enough to move Audit from dev-slice-only evidence to a
  frozen held-out final slice
- the next step is to build matched shuffles from `audit_dev_v2`, then rerun
  the empirical audit on the frozen final slice
