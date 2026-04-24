# Batch 16 Contrastive Locality Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch16_v4_summary.md`

## Accepted

- `code_1701_harder_0`
  - accepted because it is the cleanest `contrastive_locality` code pair seen
    since batch11
  - the revise trace has a real local error: it returns the largest distinct
    value instead of the second largest
  - the checker is strong enough to separate the gold fix from the wrong local
    behavior on duplicates, singleton cases, and negative integers
  - the pair remains locally repairable and exact-checkable

## Rejected

- `code_1702_1`
  - rejected because the claimed revise trace already passes the written unit
    tests and matches the synthesized reference behavior on probes
  - this is not a real revise case under the current checker, so it fails the
    one-intended-answer requirement
- `plan_1701_0`
  - rejected because the geometry collapses to a single obvious repair: the
    checker does not disambiguate among nearby local alternatives, and generic
    retry would likely recover the order without verifier-specific content
- `plan_1702_harder_1`
  - rejected because the claimed revise trace is actually valid under the
    written constraints: water is boiled first, so adding pasta after sauteing
    vegetables still satisfies the checker
  - this is another false-violation plan pair rather than a true local repair
    case

## Outcome

- reviewed pairs: `4`
- accepted pairs: `1`
- rejected pairs: `3`
- acceptance rate: `25.0 percent`

Decision:

`Do not use this batch for family bootstrap.`

Interpretation:

- `judge_v4` was useful: its pre-screen accepted exactly the one pair that
  survives human review
- code generation is now capable of producing another acceptable pair under the
  new workflow
- plan generation remains the dominant blocker because it still drifts into
  false violations or trivial geometry
