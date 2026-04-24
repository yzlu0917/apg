# Batch 12 Contrastive Locality Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`

## Rejected

- `code_contrastive_locality_1301_harder`
  - rejected because the stated alternative `digit % 2 != 0` is behaviorally
    equivalent to the gold fix `digit % 2 == 1` on decimal digits
  - this breaks the family requirement that the checker should disambiguate
    nearby but genuinely wrong local repairs
- `plan_contrastive_locality_0`
  - rejected because it collapses back to a trivial three-step sequential order
    with an unnecessary buffer, not a real contrastive-locality case
  - generic retry can recover it without needing verifier content to choose
    among multiple plausible local fixes

## Outcome

- reviewed pairs: `2`
- accepted pairs: `0`
- rejected pairs: `2`
- acceptance rate: `0.0 percent`

Decision:

`Do not use this batch for family bootstrap.`

Interpretation:

- schema-valid output is still not enough for this family
- the prompt at this stage still allowed semantically equivalent code fixes and
  overly trivial plan cases
- next step is to tighten family instructions rather than freezing any panel
